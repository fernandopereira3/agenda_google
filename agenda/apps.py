from django.apps import AppConfig


class AgendaConfig(AppConfig):
    default_auto_field = "django_mongodb_backend.fields.ObjectIdAutoField"
    name = "agenda"
