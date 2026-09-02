from functools import wraps

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

User = get_user_model()


def staff_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapper


class ProfissionalCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "email")


@staff_required
def listar_profissionais(request):
    profissionais = User.objects.all().order_by("username")
    return render(request, "profissionais.html", {"profissionais": profissionais})


@staff_required
def criar_profissional(request):
    if request.method == "POST":
        form = ProfissionalCreationForm(request.POST)
        if form.is_valid():
            profissional = form.save(commit=False)
            profissional.is_staff = request.POST.get("is_staff") == "on"
            profissional.save()
            return redirect("profissionais")
    else:
        form = ProfissionalCreationForm()
    return render(request, "criar_profissional.html", {"form": form})


@staff_required
@require_http_methods(["POST"])
def alternar_ativo_profissional(request, id):
    profissional = get_object_or_404(User, id=id)
    if profissional != request.user:
        profissional.is_active = not profissional.is_active
        profissional.save(update_fields=["is_active"])
    return redirect("profissionais")
