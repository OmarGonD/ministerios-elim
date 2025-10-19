from django.contrib import admin
from .models import Iglesia


class IglesiaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'owner', 'address', 'telefono', 'created')
    list_filter = ('owner',)
    search_fields = ('nombre', 'address', 'owner__username')

    def save_model(self, request, obj, form, change):
        # Ensure only pastor_elim owners can create iglesias via admin (but admins can override)
        try:
            profile = getattr(obj.owner, 'profile', None)
            owner_role = profile.role if profile is not None else None
        except Exception:
            owner_role = None
        if owner_role != 'pastor_elim' and not request.user.is_staff and not request.user.is_superuser:
            raise PermissionError('Solo pastores Elim pueden crear o administrar su sección de iglesia vía admin.')
        super().save_model(request, obj, form, change)


admin.site.register(Iglesia, IglesiaAdmin)
