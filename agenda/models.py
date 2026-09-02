from django.conf import settings
from django.db import models
from django_mongodb_backend.fields import ObjectIdAutoField


class Agendamento(models.Model):
    id = ObjectIdAutoField(primary_key=True)
    profissional = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="agendamentos",
        verbose_name="Profissional",
    )
    cliente_nome = models.CharField(max_length=200, verbose_name="Nome do Cliente")
    cliente_telefone = models.CharField(
        max_length=20, verbose_name="Telefone do Cliente", null=True, blank=True
    )
    data_horario = models.DateTimeField(verbose_name="Data e Horário")
    duracao = models.IntegerField(default=60, verbose_name="Duração (min)")
    observacoes = models.TextField(verbose_name="Observações", null=True, blank=True)
    finalizado = models.BooleanField(default=False, verbose_name="Finalizado")
    status = models.CharField(
        max_length=20,
        default="Pendente",
        choices=[
            ("Pendente", "Pendente"),
            ("Aguardando", "Aguardando"),
            ("Em Atendimento", "Em Atendimento"),
        ],
        verbose_name="Status",
    )

    # Nota: o campo `servicos_realizados` é gerenciado diretamente via PyMongo
    # (array de dicts com servico + data_agendamento), sem campo ORM declarado,
    # pois o django_mongodb_backend 6.0.1 tem limitações com EmbeddedModelField.

    google_event_id = models.CharField(
        max_length=255, null=True, blank=True, db_index=True
    )
    google_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"
        ordering = ["data_horario"]
        indexes = [models.Index(fields=["profissional", "data_horario"])]

    def __str__(self):
        return f"{self.cliente_nome} - {self.data_horario}"

    @property
    def cor(self):
        """Gera uma cor HSL única por cliente, baseada no hash do nome. Não salva no banco."""
        nome = self.cliente_nome or ""
        hue = hash(nome) % 360
        return f"hsl({hue}, 65%, 50%)"


class GoogleSyncState(models.Model):
    id = ObjectIdAutoField(primary_key=True)
    profissional = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="google_sync_state",
    )
    sync_token = models.CharField(max_length=500, null=True, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Sync de {self.profissional}"
