from django import forms
from .models import UserProfile


class UserProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If this is for creating a profile from dropdown, make role readonly
        if hasattr(self, 'initial') and 'role' in self.initial:
            self.fields['role'].disabled = True
            self.fields['role'].help_text = 'Este rol fue seleccionado durante el registro'

    class Meta:
        model = UserProfile
        fields = ['role', 'country', 'country_code', 'phone_number', 'foto', 'iglesia_principal', 'titulo_academico', 'experiencia', 'fecha_ordenacion']
        labels = {
            'role': 'Rol',
            'country': 'País',
            'country_code': 'Código de País',
            'phone_number': 'Número de Teléfono',
            'foto': 'Foto de Perfil',
            'iglesia_principal': 'Iglesia Principal',
            'titulo_academico': 'Título Académico',
            'experiencia': 'Experiencia Ministerial',
            'fecha_ordenacion': 'Fecha de Ordenación',
        }
        widgets = {
            'foto': forms.FileInput(attrs={'accept': 'image/*'}),
            'experiencia': forms.Textarea(attrs={'rows': 3}),
            'fecha_ordenacion': forms.DateInput(attrs={'type': 'date'}),
        }
