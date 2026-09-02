from django import forms
from .models import Agendamento


class AgendamentoForm(forms.ModelForm):
    class Meta:
        model = Agendamento
        fields = [
            "cliente_nome",
            "cliente_telefone",
            "data_horario",
            "duracao",
            "observacoes",
        ]
        widgets = {
            "cliente_nome": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nome do cliente",
                    "autocomplete": "off",
                }
            ),
            "cliente_telefone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "(00) 00000-0000"}
            ),
            "data_horario": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "duracao": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Minutos"}
            ),
            "observacoes": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "maxlength": 70}
            ),
        }
