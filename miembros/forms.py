from django import forms
from .models import MemberProfile


class MemberProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If this is for creating a profile from dropdown, make role readonly
        if hasattr(self, 'initial') and 'role' in self.initial:
            self.fields['role'].disabled = True
            self.fields['role'].help_text = 'Este rol fue seleccionado durante el registro'

    class Meta:
        model = MemberProfile
        fields = [
            'role', 'country', 'country_code', 'phone_number', 'foto',
            'iglesia_afiliada', 'fecha_afiliacion', 'estado_civil',
            'fecha_nacimiento', 'ocupacion'
        ]
        labels = {
            'role': 'Rol',
            'country': 'País',
            'country_code': 'Código de País',
            'phone_number': 'Número de Teléfono',
            'foto': 'Foto de Perfil',
            'iglesia_afiliada': 'Iglesia Afiliada',
            'fecha_afiliacion': 'Fecha de Afiliación',
            'estado_civil': 'Estado Civil',
            'fecha_nacimiento': 'Fecha de Nacimiento',
            'ocupacion': 'Ocupación',
        }
        widgets = {
            'foto': forms.FileInput(attrs={'accept': 'image/*'}),
            'fecha_afiliacion': forms.DateInput(attrs={'type': 'date'}),
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
        }
