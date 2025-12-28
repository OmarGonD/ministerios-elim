from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
import phonenumbers
import unicodedata

User = get_user_model()


class EmailAuthenticationForm(AuthenticationForm):
    """
    Custom authentication form that allows login with email or username
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Correo electrónico o nombre de usuario'
        self.fields['username'].widget.attrs.update({'placeholder': 'Ingresa tu email o nombre de usuario'})

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            return username

        # Try to find user by email first
        try:
            user = User.objects.get(email=username)
            return user.username  # Return the actual username for authentication
        except User.DoesNotExist:
            # If not found by email, check if it's a valid username
            try:
                user = User.objects.get(username=username)
                return username
            except User.DoesNotExist:
                # If neither email nor username exists, let Django handle the error
                return username


class ExtendedUserCreationForm(forms.ModelForm):
    ROLE_PASTOR = 'pastor_elim'
    ROLE_PASTOR_OTRO = 'pastor_otro'
    ROLE_MIEMBRO = 'miembro'
    ROLE_VISITANTE = 'visitante'
    ROLE_CHOICES = [
        (ROLE_PASTOR, 'Soy pastor Elim'),
        (ROLE_PASTOR_OTRO, 'Soy pastor - otro ministerio o independiente'),
        (ROLE_MIEMBRO, 'Soy miembro de una iglesia (Elim u otra iglesia)'),
        (ROLE_VISITANTE, 'Solo soy visitante'),
    ]

    username = forms.CharField(required=False)  # This will be set in clean() method
    role = forms.ChoiceField(label='¿Cuál es tu rol?', choices=ROLE_CHOICES, widget=forms.RadioSelect, initial=ROLE_MIEMBRO)
    first_name = forms.CharField(label='Nombre', required=False)
    last_name = forms.CharField(label='Apellido', required=False)
    username_display = forms.CharField(label='Nombre de usuario (opcional)', required=False, widget=forms.TextInput(attrs={'placeholder': 'Si lo dejas vacío se usará la parte del correo antes de @'}))
    country_code = forms.CharField(label='Código de país', required=False, widget=forms.TextInput(attrs={'readonly': True}))
    phone_number = forms.CharField(label='Número de celular', required=False)
    country = forms.CharField(label='País', required=True)
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repite la contraseña', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        # Note: Other fields (username_display, country, phone_number, etc.) are handled as extra form fields

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        username_display = cleaned_data.get('username_display')
        email = cleaned_data.get('email')

        # Validate passwords match
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Las contraseñas no coinciden.')

        # Set username
        if username_display:
            cleaned_data['username'] = username_display
        elif email:
            cleaned_data['username'] = email.split('@')[0]

        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError('Ya existe un usuario con este correo electrónico.')
        return email

    def clean_username_display(self):
        username_display = self.cleaned_data.get('username_display')
        if username_display and User.objects.filter(username=username_display).exists():
            raise forms.ValidationError('Este nombre de usuario ya está en uso.')
        return username_display

    def clean_country(self):
        country_val = self.cleaned_data.get('country')
        if not country_val:
            raise forms.ValidationError('El país es obligatorio')
        
        country_val = country_val.strip()
        if len(country_val) == 2:
            return country_val.upper()

        def normalize_str(s):
            return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8').lower()

        normalized_input = normalize_str(country_val)

        try:
            from django_countries import countries
            # exact match (accent-insensitive)
            for code, name in countries:
                if normalize_str(name) == normalized_input:
                    from .country_phone_codes import COUNTRY_PHONE_CODES
                    self.cleaned_data['country_code'] = '+' + COUNTRY_PHONE_CODES.get(code, '')
                    return code
            
            # partial match (accent-insensitive)
            for code, name in countries:
                if normalize_str(name).startswith(normalized_input):
                    from .country_phone_codes import COUNTRY_PHONE_CODES
                    self.cleaned_data['country_code'] = '+' + COUNTRY_PHONE_CODES.get(code, '')
                    return code
        except Exception:
            pass
            
        raise forms.ValidationError('No se pudo reconocer el país. Selecciona uno de la lista.')

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        country_code = self.cleaned_data.get('country_code')
        if not phone_number:
            return ''
        if not country_code:
            raise forms.ValidationError('El código de país es requerido para validar el número')

        # Combine country code and phone number for validation
        full_phone = f"{country_code} {phone_number}"
        try:
            region = self.cleaned_data.get('country') or None
            parsed = phonenumbers.parse(full_phone, region)
            if not phonenumbers.is_valid_number(parsed):
                raise forms.ValidationError('Número de teléfono no válido')
            normalized = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            # Return just the number part without country code
            return normalized.replace(country_code, '').strip()
        except phonenumbers.NumberParseException:
            raise forms.ValidationError('Formato de teléfono no reconocido')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        # Username is already set in the clean() method

        if commit:
            user.save()
        return user


