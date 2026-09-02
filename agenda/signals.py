from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from . import google_calendar
from .models import Agendamento


@receiver(post_save, sender=Agendamento)
def _push_agendamento_on_save(sender, instance, **kwargs):
    if getattr(instance, "_skip_google_sync", False):
        return
    google_calendar.push_agendamento(instance)


@receiver(pre_delete, sender=Agendamento)
def _delete_agendamento_on_delete(sender, instance, **kwargs):
    if getattr(instance, "_skip_google_sync", False):
        return
    google_calendar.delete_agendamento_event(instance)
