from django import forms
from .models import Iglesia


class IglesiaForm(forms.ModelForm):
    class Meta:
        model = Iglesia
        fields = [
            'nombre', 'address', 'telefono', 'country', 'foto',
            'culto_oracion_dia', 'culto_oracion_hora',
            'estudio_biblico_dia', 'estudio_biblico_hora', 
            'culto_general_dia', 'culto_general_hora',
            'culto_oracion', 'estudio_biblico', 'culto_general'
        ]
        labels = {
            'address': 'Dirección',
            'country': 'País',
            'culto_oracion_dia': 'Día',
            'culto_oracion_hora': 'Hora',
            'estudio_biblico_dia': 'Día',
            'estudio_biblico_hora': 'Hora',
            'culto_general_dia': 'Día',
            'culto_general_hora': 'Hora',
            'culto_oracion': 'Período (a. m./p. m.)',
            'estudio_biblico': 'Período (a. m./p. m.)',
            'culto_general': 'Período (a. m./p. m.)',
        }
        widgets = {
            'culto_oracion_hora': forms.TimeInput(attrs={'type': 'time'}),
            'estudio_biblico_hora': forms.TimeInput(attrs={'type': 'time'}),
            'culto_general_hora': forms.TimeInput(attrs={'type': 'time'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Organizar campos en secciones
        self.fields['culto_oracion_dia'].required = False
        self.fields['culto_oracion_hora'].required = False
        self.fields['estudio_biblico_dia'].required = False
        self.fields['estudio_biblico_hora'].required = False
        self.fields['culto_general_dia'].required = False
        self.fields['culto_general_hora'].required = False
