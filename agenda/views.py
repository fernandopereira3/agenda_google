from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from .models import Agendamento
from .forms import AgendamentoForm
from . import google_calendar
from django.db import connections
from datetime import datetime, timedelta
from django.utils import timezone
import calendar


def gerar_calendario(user, data_base=None):
    if data_base is None:
        current_date = timezone.now().date()
    else:
        current_date = data_base

    start_of_week = current_date - timedelta(days=current_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    week_days = []
    for i in range(7):
        day = start_of_week + timedelta(days=i)
        week_days.append(
            {
                "date": day,
                "day_name": ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"][
                    day.weekday()
                ],
                "day_num": day.day,
                "is_today": day == timezone.now().date(),
            }
        )

    start_dt = timezone.make_aware(datetime.combine(start_of_week, datetime.min.time()))
    end_dt = timezone.make_aware(datetime.combine(end_of_week, datetime.max.time()))

    agendamentos = Agendamento.objects.filter(
        data_horario__range=(start_dt, end_dt), profissional=user
    )

    schedule = {}
    for day in week_days:
        day_iso = day["date"].isoformat()
        schedule[day_iso] = {}
        for h in range(1, 24):
            schedule[day_iso][f"{h:02d}:00"] = []

    for appt in agendamentos:
        local_dt = timezone.localtime(appt.data_horario)
        day_key = local_dt.date().isoformat()
        hour_key = local_dt.strftime("%H:00")

        if day_key in schedule and hour_key in schedule[day_key]:
            schedule[day_key][hour_key].append(appt)

    hours_list = [f"{h:02d}:00" for h in range(6, 21)]

    prev_week = start_of_week - timedelta(days=7)
    next_week = start_of_week + timedelta(days=7)

    return {
        "current_date": current_date,
        "week_days": week_days,
        "schedule": schedule,
        "hours_list": hours_list,
        "start_of_week": start_of_week,
        "end_of_week": end_of_week,
        "prev_week": prev_week,
        "next_week": next_week,
    }


def gerar_calendario_dia(user, data_base=None):
    if data_base is None:
        current_date = timezone.now().date()
    else:
        current_date = data_base

    week_days = [
        {
            "date": current_date,
            "day_name": ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"][
                current_date.weekday()
            ],
            "day_num": current_date.day,
            "is_today": current_date == timezone.now().date(),
        }
    ]

    start_dt = timezone.make_aware(datetime.combine(current_date, datetime.min.time()))
    end_dt = timezone.make_aware(datetime.combine(current_date, datetime.max.time()))

    agendamentos = Agendamento.objects.filter(
        data_horario__range=(start_dt, end_dt), profissional=user
    )

    schedule = {}
    day_iso = current_date.isoformat()
    schedule[day_iso] = {}
    for h in range(6, 21):
        schedule[day_iso][f"{h:02d}:00"] = []

    for appt in agendamentos:
        local_dt = timezone.localtime(appt.data_horario)
        day_key = local_dt.date().isoformat()
        hour_key = local_dt.strftime("%H:00")

        if day_key in schedule and hour_key in schedule[day_key]:
            schedule[day_key][hour_key].append(appt)

    hours_list = [f"{h:02d}:00" for h in range(6, 21)]

    prev_week = current_date - timedelta(days=1)
    next_week = current_date + timedelta(days=1)

    return {
        "current_date": current_date,
        "week_days": week_days,
        "schedule": schedule,
        "hours_list": hours_list,
        "start_of_week": current_date,
        "end_of_week": current_date,
        "prev_week": prev_week,
        "next_week": next_week,
    }


def gerar_calendario_mes(user, data_base=None):
    if data_base is None:
        current_date = timezone.now().date()
    else:
        current_date = data_base

    first_day = current_date.replace(day=1)
    last_day = current_date.replace(
        day=calendar.monthrange(current_date.year, current_date.month)[1]
    )

    start_of_calendar = first_day - timedelta(days=first_day.weekday())
    end_of_calendar = last_day + timedelta(days=(6 - last_day.weekday()))

    week_days = []
    current = start_of_calendar
    while current <= end_of_calendar:
        week_days.append(
            {
                "date": current,
                "day_name": ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"][
                    current.weekday()
                ],
                "day_num": current.day,
                "is_today": current == timezone.now().date(),
                "is_current_month": current.month == current_date.month,
            }
        )
        current += timedelta(days=1)

    start_dt = timezone.make_aware(
        datetime.combine(start_of_calendar, datetime.min.time())
    )
    end_dt = timezone.make_aware(datetime.combine(end_of_calendar, datetime.max.time()))

    agendamentos = Agendamento.objects.filter(
        data_horario__range=(start_dt, end_dt), profissional=user
    )

    schedule = {}
    for day in week_days:
        day_iso = day["date"].isoformat()
        schedule[day_iso] = []

    for appt in agendamentos:
        local_dt = timezone.localtime(appt.data_horario)
        day_key = local_dt.date().isoformat()
        if day_key in schedule:
            schedule[day_key].append(appt)

    if current_date.month == 1:
        prev_month = current_date.replace(year=current_date.year - 1, month=12, day=1)
    else:
        prev_month = current_date.replace(month=current_date.month - 1, day=1)

    if current_date.month == 12:
        next_month = current_date.replace(year=current_date.year + 1, month=1, day=1)
    else:
        next_month = current_date.replace(month=current_date.month + 1, day=1)

    return {
        "current_date": current_date,
        "week_days": week_days,
        "schedule": schedule,
        "hours_list": [],
        "start_of_week": start_of_calendar,
        "end_of_week": end_of_calendar,
        "prev_week": prev_month,
        "next_week": next_month,
    }


@login_required
@never_cache
def agenda(request):
    data_str = request.GET.get("data")
    if data_str:
        try:
            data_base = datetime.strptime(data_str, "%d-%m-%Y").date()
        except ValueError:
            data_base = None
    else:
        data_base = None

    view_type = request.GET.get("view", "semana")

    is_mobile = getattr(request, "is_mobile", False)
    if is_mobile and view_type == "mes":
        view_type = "semana"

    if request.method == "POST":
        form = AgendamentoForm(request.POST)
        if form.is_valid():
            agendamento = form.save(commit=False)
            agendamento.profissional = request.user

            conflito = Agendamento.objects.filter(
                data_horario=agendamento.data_horario, profissional=request.user
            ).exists()

            if not conflito:
                agendamento.save()

            if data_base:
                return redirect(
                    f"/?data={data_base.strftime('%d-%m-%Y')}&view={view_type}"
                )
            else:
                return redirect(f"/?view={view_type}")
    else:
        form = AgendamentoForm()

    if view_type == "dia":
        context = gerar_calendario_dia(request.user, data_base)
    elif view_type == "mes":
        context = gerar_calendario_mes(request.user, data_base)
    else:
        context = gerar_calendario(request.user, data_base)

    context["form"] = form
    context["view_type"] = view_type
    context["formas_pagamento"] = [
        ("pix", "PIX"),
        ("credito", "Crédito"),
        ("debito", "Débito"),
        ("dinheiro", "Dinheiro"),
        ("transferencia", "Transação Bancária"),
        ("outros", "Outros"),
    ]

    import json

    db = connections["default"]
    colecao_estoque = db.get_collection("estoque_produto")
    produtos_estoque_docs = list(
        colecao_estoque.find({"quantidade_estoque": {"$gt": 0}}).sort("nome", 1)
    )

    produtos_estoque_list = []
    for p in produtos_estoque_docs:
        produtos_estoque_list.append(
            {
                "id": str(p.get("_id", "")),
                "nome": p.get("nome") or "",
                "preco": float(str(p.get("preco_venda", 0))),
            }
        )
    context["produtos_json"] = json.dumps(produtos_estoque_list)

    template = "agenda_mobile.html" if is_mobile else "agenda.html"
    return render(request, template, context)


@login_required
def editar_agendamento(request, id):
    agendamento = get_object_or_404(Agendamento, id=id, profissional=request.user)

    if request.method == "GET":
        servicos_realizados = []
        produtos_realizados = []
        if agendamento.finalizado:
            db_local = connections["default"]
            colecao = db_local.get_collection("agenda_agendamento")
            doc = colecao.find_one({"_id": agendamento.id}, {"servicos_realizados": 1})
            if doc and doc.get("servicos_realizados"):
                servicos_realizados = [
                    {"tipo": s.get("tipo", ""), "servico": s.get("servico", "")}
                    for s in doc["servicos_realizados"]
                ]
            colecao_produtos = db_local.get_collection("financeiro_produtos")
            for p in colecao_produtos.find({"agendamento_id": str(agendamento.id)}):
                produtos_realizados.append(
                    {
                        "nome": p.get("produto_nome", ""),
                        "quantidade": p.get("quantidade", 1),
                    }
                )

        local_dt = timezone.localtime(agendamento.data_horario)
        data = {
            "id": str(agendamento.id),
            "cliente_nome": agendamento.cliente_nome or "",
            "cliente_telefone": agendamento.cliente_telefone or "",
            "data_horario": local_dt.strftime("%Y-%m-%dT%H:%M"),
            "data_horario_display": local_dt.strftime("%d/%m/%Y %H:%M"),
            "duracao": agendamento.duracao,
            "observacoes": agendamento.observacoes or "",
            "servicos_realizados": servicos_realizados,
            "produtos_realizados": produtos_realizados,
        }
        return JsonResponse(data)

    elif request.method == "POST":
        form = AgendamentoForm(request.POST, instance=agendamento)
        if form.is_valid():
            form.save()

            data_str = request.POST.get("redirect_data", "")
            view_type = request.POST.get("redirect_view", "semana")

            if data_str:
                return redirect(f"/?data={data_str}&view={view_type}")
            else:
                return redirect(f"/?view={view_type}")
        else:
            return redirect("/")

    return HttpResponseNotAllowed(["GET", "POST"])


@login_required
def excluir_agendamento(request, id):
    if request.method == "POST":
        agendamento = get_object_or_404(Agendamento, id=id, profissional=request.user)
        agendamento.delete()

        data_str = request.POST.get("redirect_data", "")
        view_type = request.POST.get("redirect_view", "semana")

        if data_str:
            return redirect(f"/?data={data_str}&view={view_type}")
        else:
            return redirect(f"/?view={view_type}")

    return HttpResponseNotAllowed(["POST"])


@login_required
@require_http_methods(["GET"])
def get_agendamento(request, id):
    try:
        agendamento = Agendamento.objects.get(id=id, profissional=request.user)

        data = {
            "id": str(agendamento.id),
            "cliente_nome": agendamento.cliente_nome,
            "cliente_telefone": agendamento.cliente_telefone or "",
            "cliente_desde": None,
            "ultima_visita": None,
            "data_horario": agendamento.data_horario.strftime("%d/%m/%Y %H:%M"),
        }
        return JsonResponse(data)
    except Agendamento.DoesNotExist:
        return JsonResponse({"error": "Agendamento não encontrado"}, status=404)


@login_required
@require_http_methods(["POST"])
def finalizar_atendimento(request, id):
    try:
        agendamento = Agendamento.objects.get(id=id, profissional=request.user)

        formas_pagamento = request.POST.getlist("forma_pagamento")

        MAPA_LABEL = {
            "pix": "PIX",
            "credito": "Crédito",
            "debito": "Débito",
            "dinheiro": "Dinheiro",
            "transferencia": "Transferência",
            "outros": "Outros",
        }

        SERVICO_TIPO = {
            "Corte": "Corte",
            "Coloração": "Coloração",
            "Coloração Gloss": "Coloração Gloss",
            "Manicure": "Manicure",
            "Pedicure": "Pedicure",
            "Penteado": "Penteado",
            "Escova": "Escova",
            "Tratamento Capilar": "Tratamento Capilar",
            "Pedicure e Manicure": "Pedicure e Manicure",
            "Alisamento": "Alisamento",
            "Maquiagem": "Maquiagem",
            "Sobrancelha": "Sobrancelha",
            "Sobrancelha e Buço": "Sobrancelha e Buço",
            "Outro": "Outro",
            "Camuflagem Gloss": "Camuflagem Gloss",
            "Luzes": "Luzes",
            "Relaxamento": "Relaxamento",
        }

        valor_pago = 0.0
        detalhes_pagamento = []
        forma_modelo = "a_prazo"

        if formas_pagamento:
            MAPA_FORMA_MODELO = {
                "pix": "pix",
                "credito": "cartao_credito",
                "debito": "cartao_debito",
                "dinheiro": "dinheiro",
                "transferencia": "transferencia",
                "outros": "a_prazo",
            }
            forma_modelo = MAPA_FORMA_MODELO.get(formas_pagamento[0], "a_prazo")

            for forma in formas_pagamento:
                val_str = request.POST.get(f"valor_forma_{forma}")
                try:
                    val = float(val_str) if val_str else 0.0
                    if val > 0:
                        valor_pago += val
                        label = MAPA_LABEL.get(forma, forma.capitalize())
                        detalhes_pagamento.append(f"{label} (R$ {val:.2f})")
                except ValueError, TypeError:
                    pass

        forma_pagamento_str = (
            ", ".join(detalhes_pagamento) if detalhes_pagamento else "Não informado"
        )

        data_atendimento = timezone.localtime(agendamento.data_horario).date()
        total_geral = 0.0

        servicos_lista = []
        index = 0
        while True:
            servico_nome = request.POST.get(f"servico_{index}")
            servico_valor = request.POST.get(f"valor_servico_{index}")
            desconto_raw = request.POST.get(f"desconto_servico_{index}", "0")
            servico_tipo_raw = request.POST.get(f"servico_tipo_{index}", "")
            servico_tipo = SERVICO_TIPO.get(
                servico_tipo_raw, servico_tipo_raw or "Não especificado"
            )

            if not servico_nome:
                break

            if servico_nome and servico_valor:
                try:
                    valor_decimal = float(servico_valor)
                    desconto = float(desconto_raw) if desconto_raw else 0.0
                    valor_final = max(0, valor_decimal - desconto)
                    if valor_final > 0:
                        servicos_lista.append((servico_tipo, servico_nome, valor_final))
                        total_geral += valor_final
                except ValueError, TypeError:
                    pass

            index += 1

        produtos_lista = []
        index = 0
        while True:
            produto_nome = request.POST.get(f"produto_{index}")
            produto_qtd = request.POST.get(f"qtd_produto_{index}")
            produto_valor = request.POST.get(f"valor_produto_{index}")
            desconto_raw = request.POST.get(f"desconto_produto_{index}", "0")

            if not produto_nome:
                break

            if produto_nome and produto_qtd and produto_valor:
                try:
                    qtd = int(produto_qtd)
                    valor_unitario = float(produto_valor)
                    desconto = float(desconto_raw) if desconto_raw else 0.0
                    valor_final = max(0, (qtd * valor_unitario) - desconto)
                    if valor_final > 0:
                        produtos_lista.append(
                            (produto_nome, qtd, valor_unitario, valor_final)
                        )
                        total_geral += valor_final
                except ValueError, TypeError:
                    pass

            index += 1

        status = "pago" if valor_pago >= total_geral else "pendente"

        agendamento.finalizado = True
        agendamento.save(update_fields=["finalizado"])

        if servicos_lista:
            import bson

            db_local = connections["default"]
            colecao_agendamento = db_local.get_collection("agenda_agendamento")
            servicos_bson = [
                {
                    "_id": bson.ObjectId(),
                    "tipo": tipo,
                    "servico": nome,
                    "data_agendamento": agendamento.data_horario,
                }
                for tipo, nome, _ in servicos_lista
            ]
            colecao_agendamento.update_one(
                {"_id": agendamento.id},
                {"$set": {"servicos_realizados": servicos_bson}},
            )

        servicos_criados = 0
        colecao_servicos = connections["default"].get_collection("financeiro_servicos")
        for servico_tipo, servico_nome, valor_final in servicos_lista:
            colecao_servicos.insert_one(
                {
                    "cliente_nome": agendamento.cliente_nome,
                    "agendamento_id": str(agendamento.id),
                    "profissional_id": str(request.user.id),
                    "servico_tipo": servico_tipo,
                    "servico_nome": servico_nome,
                    "valor": round(valor_final),
                    "data": datetime.combine(data_atendimento, datetime.min.time()),
                    "forma_pagamento": forma_modelo,
                    "status": status,
                    "observacoes": f"Forma de pagamento: {forma_pagamento_str} | Valor pago pelo serviço: R$ {valor_pago:.2f}",
                    "created_at": datetime.now(),
                }
            )
            servicos_criados += 1

        produtos_criados = 0
        colecao_produtos = connections["default"].get_collection("financeiro_produtos")
        for produto_nome, qtd, valor_unitario, valor_final in produtos_lista:
            desconto_produto = round(max(0.0, (qtd * valor_unitario) - valor_final), 2)
            colecao_produtos.insert_one(
                {
                    "cliente_nome": agendamento.cliente_nome,
                    "agendamento_id": str(agendamento.id),
                    "profissional_id": str(request.user.id),
                    "produto_nome": produto_nome,
                    "quantidade": qtd,
                    "preco_venda": round(valor_unitario, 2),
                    "desconto": desconto_produto,
                    "valor_total": round(valor_final, 2),
                    "data": datetime.combine(data_atendimento, datetime.min.time()),
                    "forma_pagamento": forma_modelo,
                    "status": status,
                    "observacoes": f"Forma de pagamento: {forma_pagamento_str} | Valor pago pelo produto: R$ {valor_pago:.2f}",
                    "created_at": datetime.now(),
                }
            )

            colecao_estoque = connections["default"].get_collection("estoque_produto")
            colecao_estoque.update_one(
                {"nome": {"$regex": f"^{produto_nome}$", "$options": "i"}},
                {"$inc": {"quantidade_venda": -qtd, "quantidade_estoque": -qtd}},
            )
            produtos_criados += 1

        total_itens = servicos_criados + produtos_criados

        reagendar_dias_str = request.POST.get("reagendar_dias", "").strip()
        novo_agendamento_id = None
        if reagendar_dias_str:
            try:
                dias = int(reagendar_dias_str)
                if dias > 0:
                    nova_data = agendamento.data_horario + timedelta(days=dias)
                    novo = Agendamento.objects.create(
                        profissional=agendamento.profissional,
                        cliente_nome=agendamento.cliente_nome,
                        cliente_telefone=agendamento.cliente_telefone,
                        data_horario=nova_data,
                        duracao=agendamento.duracao,
                        observacoes=agendamento.observacoes,
                        finalizado=False,
                        status="Pendente",
                    )
                    novo_agendamento_id = str(novo.id)
            except ValueError, TypeError:
                pass

        response_data = {
            "success": True,
            "servicos_criados": servicos_criados,
            "produtos_criados": produtos_criados,
            "total_itens": total_itens,
            "forma_pagamento": formas_pagamento,
            "valor_pago": valor_pago,
            "total_geral": total_geral,
            "status": status,
        }
        if novo_agendamento_id:
            response_data["reagendado"] = True
            response_data["novo_agendamento_id"] = novo_agendamento_id

        return JsonResponse(response_data)

    except Agendamento.DoesNotExist:
        return JsonResponse({"error": "Agendamento não encontrado"}, status=404)


@login_required
@require_http_methods(["GET"])
def visualizar_atendimento(request, id):
    try:
        agendamento = Agendamento.objects.get(id=id, profissional=request.user)

        db = connections["default"]

        servicos_lista = list(
            db.get_collection("financeiro_servicos").find({"agendamento_id": str(id)})
        )
        servicos = []
        for s in servicos_lista:
            servicos.append(
                {
                    "nome": s.get("servico_nome", ""),
                    "valor": s.get("valor", 0),
                }
            )

        produtos_lista = list(
            db.get_collection("financeiro_produtos").find({"agendamento_id": str(id)})
        )
        produtos = []
        for p in produtos_lista:
            produtos.append(
                {
                    "nome": p.get("produto_nome", ""),
                    "quantidade": p.get("quantidade", 1),
                    "valor_total": p.get("valor_total", 0),
                }
            )

        total_servicos = sum(s["valor"] for s in servicos)
        total_produtos = sum(p["valor_total"] for p in produtos)
        total_geral = total_servicos + total_produtos

        forma_pagamento = "Não informado"
        if servicos_lista and servicos_lista[0].get("observacoes"):
            obs = servicos_lista[0].get("observacoes")
            if "Forma de pagamento:" in obs:
                forma_pagamento = obs.split(" | ")[0].replace(
                    "Forma de pagamento: ", ""
                )
        elif produtos_lista and produtos_lista[0].get("observacoes"):
            obs = produtos_lista[0].get("observacoes")
            if "Forma de pagamento:" in obs:
                forma_pagamento = obs.split(" | ")[0].replace(
                    "Forma de pagamento: ", ""
                )

        data = {
            "success": True,
            "cliente_nome": agendamento.cliente_nome or "Desconhecido",
            "data_horario": agendamento.data_horario.strftime("%d/%m/%Y às %H:%M"),
            "servicos": servicos,
            "produtos": produtos,
            "total_geral": total_geral,
            "forma_pagamento": forma_pagamento,
        }
        return JsonResponse(data)
    except Agendamento.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Agendamento não encontrado"}, status=404
        )


@login_required
def finalizar_mobile_page(request, id):
    try:
        agendamento = Agendamento.objects.get(id=id, profissional=request.user)
    except Agendamento.DoesNotExist:
        return redirect("agenda")

    FORMAS_PAGAMENTO = [
        ("pix", "PIX"),
        ("credito", "Crédito"),
        ("debito", "Débito"),
        ("dinheiro", "Dinheiro"),
        ("transferencia", "Transação Bancária"),
        ("outros", "Outros"),
    ]

    SERVICO_TIPO = {
        "Corte": "Corte",
        "Coloração": "Coloração",
        "Coloração Gloss": "Coloração Gloss",
        "Manicure": "Manicure",
        "Pedicure": "Pedicure",
        "Penteado": "Penteado",
        "Escova": "Escova",
        "Tratamento Capilar": "Tratamento Capilar",
        "Pedicure e Manicure": "Pedicure e Manicure",
        "Alisamento": "Alisamento",
        "Maquiagem": "Maquiagem",
        "Sobrancelha": "Sobrancelha",
        "Sobrancelha e Buço": "Sobrancelha e Buço",
        "Outro": "Outro",
        "Camuflagem Gloss": "Camuflagem Gloss",
        "Luzes": "Luzes",
        "Relaxamento": "Relaxamento",
    }

    if request.method == "GET":
        db = connections["default"]
        produtos_estoque_docs = list(
            db.get_collection("estoque_produto")
            .find({"quantidade_estoque": {"$gt": 0}})
            .sort("nome", 1)
        )
        import json as _json

        produtos_estoque_list = [
            {"nome": p["nome"], "preco": str(p.get("preco_venda", 0))}
            for p in produtos_estoque_docs
        ]

        return render(
            request,
            "finalizar_mobile.html",
            {
                "agendamento": agendamento,
                "formas_pagamento": FORMAS_PAGAMENTO,
                "produtos_estoque_json": _json.dumps(produtos_estoque_list),
            },
        )

    # POST
    formas_pagamento_post = request.POST.getlist("forma_pagamento")

    MAPA_LABEL = {
        "pix": "PIX",
        "credito": "Crédito",
        "debito": "Débito",
        "dinheiro": "Dinheiro",
        "transferencia": "Transferência",
        "outros": "Outros",
    }
    MAPA_FORMA_MODELO = {
        "pix": "pix",
        "credito": "cartao_credito",
        "debito": "cartao_debito",
        "dinheiro": "dinheiro",
        "transferencia": "transferencia",
        "outros": "a_prazo",
    }

    valor_pago = 0.0
    detalhes_pagamento = []
    forma_modelo = "a_prazo"

    if formas_pagamento_post:
        forma_modelo = MAPA_FORMA_MODELO.get(formas_pagamento_post[0], "a_prazo")
        for forma in formas_pagamento_post:
            val_str = request.POST.get(f"valor_forma_{forma}")
            try:
                val = float(val_str) if val_str else 0.0
                if val > 0:
                    valor_pago += val
                    detalhes_pagamento.append(
                        f"{MAPA_LABEL.get(forma, forma.capitalize())} (R$ {val:.2f})"
                    )
            except ValueError, TypeError:
                pass

    forma_pagamento_str = (
        ", ".join(detalhes_pagamento) if detalhes_pagamento else "Não informado"
    )
    data_atendimento = timezone.localtime(agendamento.data_horario).date()
    total_geral = 0.0

    servicos_lista = []
    index = 0
    while True:
        servico_nome = request.POST.get(f"servico_{index}")
        servico_valor = request.POST.get(f"valor_servico_{index}")
        desconto_raw = request.POST.get(f"desconto_servico_{index}", "0")
        servico_tipo_raw = request.POST.get(f"servico_tipo_{index}", "")
        servico_tipo = SERVICO_TIPO.get(
            servico_tipo_raw, servico_tipo_raw or "Não especificado"
        )
        if not servico_nome:
            break
        if servico_nome and servico_valor:
            try:
                valor_decimal = float(servico_valor)
                desconto = float(desconto_raw) if desconto_raw else 0.0
                valor_final = max(0, valor_decimal - desconto)
                if valor_final > 0:
                    servicos_lista.append((servico_tipo, servico_nome, valor_final))
                    total_geral += valor_final
            except ValueError, TypeError:
                pass
        index += 1

    produtos_lista = []
    index = 0
    while True:
        produto_nome = request.POST.get(f"produto_{index}")
        produto_qtd = request.POST.get(f"qtd_produto_{index}")
        produto_valor = request.POST.get(f"valor_produto_{index}")
        desconto_raw = request.POST.get(f"desconto_produto_{index}", "0")
        if not produto_nome:
            break
        if produto_nome and produto_qtd and produto_valor:
            try:
                qtd = int(produto_qtd)
                valor_unitario = float(produto_valor)
                desconto = float(desconto_raw) if desconto_raw else 0.0
                valor_final = max(0, (qtd * valor_unitario) - desconto)
                if valor_final > 0:
                    produtos_lista.append(
                        (produto_nome, qtd, valor_unitario, valor_final)
                    )
                    total_geral += valor_final
            except ValueError, TypeError:
                pass
        index += 1

    if not servicos_lista and not produtos_lista:
        return redirect("finalizar_mobile_page", id=id)

    status = "pago" if valor_pago >= total_geral else "pendente"

    agendamento.finalizado = True
    agendamento.save(update_fields=["finalizado"])

    if servicos_lista:
        import bson

        db_local = connections["default"]
        colecao_agendamento = db_local.get_collection("agenda_agendamento")
        servicos_bson = [
            {
                "_id": bson.ObjectId(),
                "tipo": tipo,
                "servico": nome,
                "data_agendamento": agendamento.data_horario,
            }
            for tipo, nome, _ in servicos_lista
        ]
        colecao_agendamento.update_one(
            {"_id": agendamento.id},
            {"$set": {"servicos_realizados": servicos_bson}},
        )

    servicos_criados = 0
    colecao_servicos = connections["default"].get_collection("financeiro_servicos")
    for servico_tipo, servico_nome, valor_final in servicos_lista:
        colecao_servicos.insert_one(
            {
                "cliente_nome": agendamento.cliente_nome,
                "agendamento_id": str(agendamento.id),
                "profissional_id": str(request.user.id),
                "servico_tipo": servico_tipo,
                "servico_nome": servico_nome,
                "valor": round(valor_final),
                "data": datetime.combine(data_atendimento, datetime.min.time()),
                "forma_pagamento": forma_modelo,
                "status": status,
                "observacoes": f"Forma de pagamento: {forma_pagamento_str} | Valor pago pelo serviço: R$ {valor_pago:.2f}",
                "created_at": datetime.now(),
            }
        )
        servicos_criados += 1

    produtos_criados = 0
    colecao_produtos = connections["default"].get_collection("financeiro_produtos")
    colecao_estoque = connections["default"].get_collection("estoque_produto")
    for produto_nome, qtd, valor_unitario, valor_final in produtos_lista:
        desconto_produto = round(max(0.0, (qtd * valor_unitario) - valor_final), 2)
        colecao_produtos.insert_one(
            {
                "cliente_nome": agendamento.cliente_nome,
                "agendamento_id": str(agendamento.id),
                "profissional_id": str(request.user.id),
                "produto_nome": produto_nome,
                "quantidade": qtd,
                "preco_venda": round(valor_unitario, 2),
                "desconto": desconto_produto,
                "valor_total": round(valor_final, 2),
                "data": datetime.combine(data_atendimento, datetime.min.time()),
                "forma_pagamento": forma_modelo,
                "status": status,
                "observacoes": f"Forma de pagamento: {forma_pagamento_str} | Valor pago pelo produto: R$ {valor_pago:.2f}",
                "created_at": datetime.now(),
            }
        )
        colecao_estoque.update_one(
            {"nome": {"$regex": f"^{produto_nome}$", "$options": "i"}},
            {"$inc": {"quantidade_venda": -qtd, "quantidade_estoque": -qtd}},
        )
        produtos_criados += 1

    reagendar_dias_str = request.POST.get("reagendar_dias", "").strip()
    if reagendar_dias_str:
        try:
            dias = int(reagendar_dias_str)
            if dias > 0:
                nova_data = agendamento.data_horario + timedelta(days=dias)
                Agendamento.objects.create(
                    profissional=agendamento.profissional,
                    cliente_nome=agendamento.cliente_nome,
                    cliente_telefone=agendamento.cliente_telefone,
                    data_horario=nova_data,
                    duracao=agendamento.duracao,
                    observacoes=agendamento.observacoes,
                    finalizado=False,
                    status="Pendente",
                )
        except ValueError, TypeError:
            pass

    return redirect("agenda")


@login_required
@require_http_methods(["GET"])
def buscar_clientes(request):
    """Autocomplete: busca nomes já usados em agendamentos anteriores."""
    q = request.GET.get("q", "").strip()
    if len(q) < 2:
        return JsonResponse({"clientes": []})

    # Busca nomes únicos de agendamentos existentes
    vistos = set()
    resultado = []
    agendamentos = (
        Agendamento.objects.filter(cliente_nome__icontains=q, profissional=request.user)
        .values("cliente_nome", "cliente_telefone")
        .order_by("cliente_nome")[:30]
    )
    for a in agendamentos:
        nome = a["cliente_nome"]
        if nome not in vistos:
            vistos.add(nome)
            resultado.append(
                {
                    "id": nome,
                    "nome": nome,
                    "telefone": a["cliente_telefone"] or "",
                }
            )
        if len(resultado) >= 10:
            break

    return JsonResponse({"clientes": resultado})


@login_required
@require_http_methods(["POST"])
def alterar_status_agendamento(request, id):
    agendamento = get_object_or_404(Agendamento, id=id, profissional=request.user)

    STATUSES_VALIDOS = ["Pendente", "Aguardando", "Em Atendimento"]
    import json

    body = json.loads(request.body)
    novo_status = body.get("status", "Pendente")

    if novo_status not in STATUSES_VALIDOS:
        return JsonResponse({"success": False, "error": "Status inválido."}, status=400)

    agendamento.status = novo_status
    agendamento.save(update_fields=["status"])

    return JsonResponse({"success": True, "status": novo_status})


@login_required
@require_http_methods(["POST"])
def sincronizar_google(request):
    resultado = google_calendar.pull_for_user(request.user)
    if not resultado.get("conectado"):
        return JsonResponse(
            {"success": False, "error": "Google Calendar não está conectado."},
            status=400,
        )
    if resultado.get("erro"):
        return JsonResponse(
            {"success": False, "error": "Falha ao sincronizar com o Google."},
            status=502,
        )
    return JsonResponse({"success": True, **resultado})
