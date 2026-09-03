# Resumo das alterações — 02/03-09-2026

## 1. Dependências (`pyproject.toml` / `requirements.txt`)

O `requirements.txt`/`pyproject.toml` não cobriam o projeto inteiro — faltavam pacotes usados no código mas nunca instalados (o `.venv` nem os tinha):

- `django-allauth` — login, `SOCIALACCOUNT_PROVIDERS`, `core/account_adapter.py`
- `google-auth` — `agenda/google_calendar.py` (`Credentials`, `Request`)
- `google-api-python-client` — `agenda/google_calendar.py` (`build`, `HttpError`)

Adicionados ao `pyproject.toml` e `requirements.txt`, rodado `uv sync`.

## 2. Primeiro usuário

Banco não tinha nenhum usuário (cadastro público é desabilitado por
`core/account_adapter.py:NoSignupAccountAdapter`). Criado um superusuário:

- **Usuário:** `admin` / **Senha:** `admin123` (trocar depois do primeiro login)

## 3. Bug: login redirecionava para `/accounts/login/None` (404)

Em `agenda/templates/account/login.html`, o campo oculto `next` renderizava
`{{ redirect_field_value }}` sem tratar `None`. O Django Template Engine
converte `None` no texto literal `"None"`, que ia no POST, o allauth aceitava
como destino "seguro" e o navegador resolvia relativo à página atual →
`/accounts/login/None` (404).

**Fix:** `{{ redirect_field_value|default:'' }}`.

## 4. `.gitignore` e segredos versionados

Não havia `.gitignore`. `.env` (com `DJANGO_SECRET_KEY` e `DB_PASSWORD` reais)
e todos os `__pycache__/*.pyc` estavam commitados no git.

- Criado `.gitignore` (ambiente, Python, venv, static/media gerados, editores/SO)
- Removidos do rastreamento (`git rm --cached`) `.env` e todos os `.pyc` —
  continuam no disco, só saem do versionamento a partir do próximo commit
- **Atenção:** os segredos antigos continuam no *histórico* do git. Se o repo
  for para um remoto/público, trocar `DB_PASSWORD` e gerar nova
  `DJANGO_SECRET_KEY`.

## 5. Google Calendar: só recebe, não envia mais

A pedido, a integração deixou de escrever no Google Calendar — agora só lê.

- **Escopo** trocado de `calendar.events` (leitura/escrita) para
  `calendar.readonly`, em `core/settings.py` (`SOCIALACCOUNT_PROVIDERS`) e
  `agenda/google_calendar.py` (`SCOPES`)
- **Removidas** as funções que escreviam no Google:
  `push_agendamento`, `delete_agendamento_event`, `_event_body`
- **Removido** `agenda/signals.py` (só existia para disparar esse envio em
  `post_save`/`pre_delete` de `Agendamento`) e sua referência em
  `agenda/apps.py`
- Limpa a flag vestigial `_skip_google_sync` em `agenda/google_calendar.py`
- `pull_for_user` (recebe do Google) e o comando `sync_google_calendar`
  continuam intactos

**Importante:** quem já conectou a conta Google antes tem token com o escopo
antigo — precisa desconectar e reconectar para valer o novo escopo (readonly).

O que é importado do Google (`_aplicar_evento`): `summary` → `cliente_nome`,
`start/end.dateTime` → `data_horario`/`duracao`, `description` →
`observacoes`, `id` → `google_event_id`. Eventos de dia inteiro (sem horário)
são ignorados; eventos cancelados no Google apagam o `Agendamento` local
correspondente.

## 6. Página "Conectar Google" sem estilo

`/accounts/google/login/?process=connect` caía no template padrão (cru, sem
CSS) do allauth porque o projeto só tinha override de `account/login.html`,
não de `socialaccount/login.html`. Criado
`agenda/templates/socialaccount/login.html` no mesmo visual (card, logo,
cores do tema) do restante do site.

## 7. CSP bloqueava o redirect para o Google

`CSP_DIRECTIVES["form-action"]` em `core/settings.py` estava só com `'self'`.
Chromium (Chrome/Brave/Edge) aplica `form-action` também ao destino do
redirect que acontece *depois* de um POST de formulário — não só à `action`
do `<form>` em si. Como o login social faz POST local e depois 302 para
`accounts.google.com`, o navegador bloqueava essa navegação silenciosamente
(o servidor respondia 302 normalmente, mas a tela não saía do lugar).

**Fix:** `"form-action": ["'self'", "https://accounts.google.com"]`.

## 8. Pendente do lado do usuário (Google Cloud Console)

Depois do fix da CSP, o Google passou a responder com
**Erro 400: redirect_uri_mismatch** — o `redirect_uri` que a app envia não
está cadastrado no client OAuth. Precisa cadastrar em
**Google Cloud Console → APIs e Serviços → Credenciais → (o OAuth Client
usado)** cada combinação de host/porta usada em desenvolvimento, por exemplo:

```
http://localhost:9500/accounts/google/login/callback/
```

Isso não é algo que dá pra resolver por código — é configuração externa no
Console do Google, e cada host/porta testado precisa da própria entrada.
