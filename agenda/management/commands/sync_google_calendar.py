from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from agenda.google_calendar import pull_for_user

User = get_user_model()


class Command(BaseCommand):
    help = "Sincroniza (Google -> app) a agenda de todo profissional com conta Google conectada."

    def handle(self, *args, **options):
        usuarios = User.objects.filter(socialaccount__provider="google").distinct()
        if not usuarios:
            self.stdout.write("Nenhum profissional com Google Calendar conectado.")
            return

        for usuario in usuarios:
            try:
                resultado = pull_for_user(usuario)
            except Exception as exc:
                self.stderr.write(f"{usuario}: erro inesperado — {exc}")
                continue

            if resultado.get("erro"):
                self.stderr.write(f"{usuario}: falha ao sincronizar")
            else:
                self.stdout.write(
                    f"{usuario}: {resultado['criados']} criado(s), "
                    f"{resultado['atualizados']} atualizado(s), "
                    f"{resultado['removidos']} removido(s)"
                )
