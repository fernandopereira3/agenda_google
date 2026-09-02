from allauth.account.adapter import DefaultAccountAdapter


class NoSignupAccountAdapter(DefaultAccountAdapter):
    """Contas de profissionais são criadas pelo administrador via /admin/, não por cadastro público."""

    def is_open_for_signup(self, request):
        return False
