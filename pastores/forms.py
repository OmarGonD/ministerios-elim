from django import forms
from .models import UserProfile


class UserProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Handle hierarchical titles in the role field
        if self.instance and self.instance.pk:
            if self.instance.is_apostle:
                self.fields['role'].choices = [(self.instance.role, "Apóstol Elim")]
                self.fields['role'].disabled = True
            elif self.instance.is_superpastor:
                self.fields['role'].choices = [(self.instance.role, "Pastor de Pastores")]
                self.fields['role'].disabled = True
        
        # If this is for creating a profile from dropdown, make role readonly
        elif hasattr(self, 'initial') and 'role' in self.initial:
            self.fields['role'].disabled = True
            self.fields['role'].help_text = 'Este rol fue seleccionado durante el registro'

    class Meta:
        model = UserProfile
        fields = ['role', 'country', 'country_code', 'phone_number', 'foto', 'iglesia_principal', 'titulo_academico', 'experiencia', 'fecha_ordenacion', 'biography']
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
            'biography': 'Biografía / Historia',
        }
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'country_code': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'foto': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'iglesia_principal': forms.TextInput(attrs={'class': 'form-control'}),
            'titulo_academico': forms.TextInput(attrs={'class': 'form-control'}),
            'experiencia': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fecha_ordenacion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'biography': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }
