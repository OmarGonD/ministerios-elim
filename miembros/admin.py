from django.contrib import admin
from .models import MemberProfile


class MemberProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'country', 'phone_number', 'iglesia_afiliada', 'is_member')
    list_filter = ('role', 'country', 'estado_civil', 'iglesia_afiliada')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'iglesia_afiliada')
    readonly_fields = ('user',)

    fieldsets = (
        ('Información del Usuario', {
            'fields': ('user', 'role')
        }),
        ('Información de Contacto', {
            'fields': ('country', 'country_code', 'phone_number'),
            'classes': ('collapse',)
        }),
        ('Información de Miembro', {
            'fields': ('iglesia_afiliada', 'fecha_afiliacion', 'estado_civil', 'fecha_nacimiento', 'ocupacion'),
            'classes': ('collapse',)
        }),
        ('Foto de Perfil', {
            'fields': ('foto',),
            'classes': ('collapse',)
        }),
    )

    def is_member(self, obj):
        return obj.is_member
    is_member.boolean = True
    is_member.short_description = 'Es Miembro'


admin.site.register(MemberProfile, MemberProfileAdmin)
