from django.urls import path, include
from agenda.views import (
    agenda,
    editar_agendamento,
    excluir_agendamento,
    get_agendamento,
    finalizar_atendimento,
    finalizar_mobile_page,
    visualizar_atendimento,
    buscar_clientes,
    alterar_status_agendamento,
    sincronizar_google,
)
from agenda.views_admin import (
    listar_profissionais,
    criar_profissional,
    alternar_ativo_profissional,
)

urlpatterns = [
    path("accounts/", include("allauth.urls")),
    path("", agenda, name="agenda"),
    path("agenda/editar/<str:id>/", editar_agendamento, name="editar_agendamento"),
    path("agenda/excluir/<str:id>/", excluir_agendamento, name="excluir_agendamento"),
    path("agenda/get/<str:id>/", get_agendamento, name="get_agendamento"),
    path(
        "agenda/finalizar/<str:id>/",
        finalizar_atendimento,
        name="finalizar_atendimento",
    ),
    path(
        "agenda/finalizar-mobile/<str:id>/",
        finalizar_mobile_page,
        name="finalizar_mobile_page",
    ),
    path(
        "agenda/visualizar/<str:id>/",
        visualizar_atendimento,
        name="visualizar_atendimento",
    ),
    path("agenda/buscar-clientes/", buscar_clientes, name="buscar_clientes"),
    path(
        "agenda/status/<str:id>/",
        alterar_status_agendamento,
        name="alterar_status_agendamento",
    ),
    path("agenda/sincronizar/", sincronizar_google, name="sincronizar_google"),
    path("profissionais/", listar_profissionais, name="profissionais"),
    path("profissionais/novo/", criar_profissional, name="criar_profissional"),
    path(
        "profissionais/<str:id>/alternar-ativo/",
        alternar_ativo_profissional,
        name="alternar_ativo_profissional",
    ),
]
