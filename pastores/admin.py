from django.contrib import admin
from .models import UserProfile


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'country', 'phone_number')
    list_filter = ('role', 'country')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('user',)

    fieldsets = (
        ('Información del Usuario', {
            'fields': ('user', 'role')
        }),
        ('Información de Contacto', {
            'fields': ('country', 'country_code', 'phone_number'),
            'classes': ('collapse',)
        }),
        ('Foto de Perfil', {
            'fields': ('foto',),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        # If changing an existing profile, prevent non-staff users from promoting someone to pastor_elim
        if change:
            try:
                old = UserProfile.objects.get(pk=obj.pk)
            except UserProfile.DoesNotExist:
                old = None
            if old and old.role == 'pastor_otro' and obj.role == 'pastor_elim':
                # Only allow staff/superusers to make this change
                if not request.user.is_staff and not request.user.is_superuser:
                    raise PermissionError('Solo administradores pueden promover a pastor Elim.')
        super().save_model(request, obj, form, change)


admin.site.register(UserProfile, UserProfileAdmin)
