import logging
from datetime import timedelta

from allauth.socialaccount.models import SocialAccount, SocialToken
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def get_credentials(user):
    """Monta as credenciais do Google para o usuário, renovando o token se preciso.

    Retorna None se o usuário não tiver conectado a conta Google.
    """
    try:
        account = SocialAccount.objects.get(user=user, provider="google")
        token = SocialToken.objects.get(account=account)
    except SocialAccount.DoesNotExist, SocialToken.DoesNotExist:
        return None

    app = settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"]
    credentials = Credentials(
        token=token.token,
        refresh_token=token.token_secret or None,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=app["client_id"],
        client_secret=app["secret"],
        scopes=SCOPES,
    )
    credentials.expiry = token.expires_at

    if credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
        except Exception:
            logger.exception("Falha ao renovar token do Google para %s", user)
            return None
        token.token = credentials.token
        token.expires_at = credentials.expiry
        token.save(update_fields=["token", "expires_at"])

    return credentials


def _service_for(user):
    credentials = get_credentials(user)
    if credentials is None:
        return None
    return build("calendar", "v3", credentials=credentials, cache_discovery=False)


def _event_body(agendamento):
    inicio = agendamento.data_horario
    fim = inicio + timedelta(minutes=agendamento.duracao or 60)
    return {
        "summary": agendamento.cliente_nome,
        "description": agendamento.observacoes or "",
        "start": {"dateTime": inicio.isoformat()},
        "end": {"dateTime": fim.isoformat()},
    }


def push_agendamento(agendamento):
    """Cria/atualiza o evento no Google Calendar do profissional dono do agendamento."""
    service = _service_for(agendamento.profissional)
    if service is None:
        return

    body = _event_body(agendamento)
    try:
        if agendamento.google_event_id:
            event = (
                service.events()
                .update(
                    calendarId="primary", eventId=agendamento.google_event_id, body=body
                )
                .execute()
            )
        else:
            event = service.events().insert(calendarId="primary", body=body).execute()
    except HttpError as exc:
        if exc.resp.status == 404 and agendamento.google_event_id:
            agendamento.google_event_id = None
            push_agendamento(agendamento)
            return
        logger.warning(
            "Falha ao sincronizar agendamento %s com o Google: %s", agendamento.id, exc
        )
        return
    except Exception:
        logger.exception(
            "Erro inesperado sincronizando agendamento %s com o Google", agendamento.id
        )
        return

    agendamento.google_event_id = event["id"]
    agendamento.google_synced_at = timezone.now()
    agendamento._skip_google_sync = True
    agendamento.save(update_fields=["google_event_id", "google_synced_at"])


def delete_agendamento_event(agendamento):
    """Remove o evento correspondente no Google Calendar, se existir."""
    if not agendamento.google_event_id:
        return
    service = _service_for(agendamento.profissional)
    if service is None:
        return
    try:
        service.events().delete(
            calendarId="primary", eventId=agendamento.google_event_id
        ).execute()
    except HttpError as exc:
        if exc.resp.status not in (404, 410):
            logger.warning(
                "Falha ao apagar evento do Google do agendamento %s: %s",
                agendamento.id,
                exc,
            )
    except Exception:
        logger.exception(
            "Erro inesperado apagando evento do Google do agendamento %s",
            agendamento.id,
        )


def pull_for_user(user):
    """Traz pro app o que mudou direto no Google Calendar do profissional.

    Usa o `syncToken` incremental quando existe; faz uma sincronização completa
    (últimos 90 dias) quando é a primeira vez ou quando o token expirou (HTTP 410).
    """
    from .models import GoogleSyncState

    service = _service_for(user)
    if service is None:
        return {"conectado": False}

    state, _ = GoogleSyncState.objects.get_or_create(profissional=user)
    resultado = {
        "conectado": True,
        "criados": 0,
        "atualizados": 0,
        "removidos": 0,
        "erro": False,
    }

    def aplicar_pagina(items):
        for event in items:
            _aplicar_evento(user, event, resultado)

    full_resync = not state.sync_token

    if not full_resync:
        try:
            page_token = None
            while True:
                resp = (
                    service.events()
                    .list(
                        calendarId="primary",
                        syncToken=state.sync_token,
                        pageToken=page_token,
                    )
                    .execute()
                )
                aplicar_pagina(resp.get("items", []))
                page_token = resp.get("nextPageToken")
                if not page_token:
                    state.sync_token = resp.get("nextSyncToken", state.sync_token)
                    break
        except HttpError as exc:
            if exc.resp.status == 410:
                full_resync = True
                state.sync_token = None
            else:
                logger.warning("Falha ao sincronizar (pull) para %s: %s", user, exc)
                resultado["erro"] = True
                return resultado

    if full_resync:
        try:
            page_token = None
            time_min = (timezone.now() - timedelta(days=90)).isoformat()
            while True:
                resp = (
                    service.events()
                    .list(
                        calendarId="primary",
                        singleEvents=True,
                        timeMin=time_min,
                        pageToken=page_token,
                    )
                    .execute()
                )
                aplicar_pagina(resp.get("items", []))
                page_token = resp.get("nextPageToken")
                if not page_token:
                    state.sync_token = resp.get("nextSyncToken")
                    break
        except HttpError as exc:
            logger.warning("Falha no resync completo do Google para %s: %s", user, exc)
            resultado["erro"] = True
            return resultado

    state.last_synced_at = timezone.now()
    state.save(update_fields=["sync_token", "last_synced_at"])
    return resultado


def _aplicar_evento(user, event, resultado):
    from .models import Agendamento

    if event.get("status") == "cancelled":
        for agendamento in Agendamento.objects.filter(
            profissional=user, google_event_id=event["id"]
        ):
            agendamento._skip_google_sync = True
            agendamento.delete()
            resultado["removidos"] += 1
        return

    start = event.get("start", {}).get("dateTime")
    if not start:
        return  # evento de dia inteiro (sem horário) — fora do escopo da agenda

    inicio = parse_datetime(start)
    duracao = 60
    end = event.get("end", {}).get("dateTime")
    if end:
        fim = parse_datetime(end)
        duracao = max(1, int((fim - inicio).total_seconds() // 60))

    campos = {
        "cliente_nome": event.get("summary") or "(sem título)",
        "data_horario": inicio,
        "duracao": duracao,
        "observacoes": event.get("description") or "",
        "google_synced_at": timezone.now(),
    }

    try:
        agendamento = Agendamento.objects.get(
            profissional=user, google_event_id=event["id"]
        )
        criado = False
    except Agendamento.DoesNotExist:
        agendamento = Agendamento(profissional=user, google_event_id=event["id"])
        criado = True

    for campo, valor in campos.items():
        setattr(agendamento, campo, valor)
    # Marca antes de salvar: o sinal post_save lê essa flag na própria instância,
    # então precisa estar setada já na criação, não depois.
    agendamento._skip_google_sync = True
    agendamento.save()

    resultado["criados" if criado else "atualizados"] += 1
