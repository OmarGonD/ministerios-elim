from django.contrib import admin
from .models import Forum, Topic, Post, Comment, ForumReport, ForumPreference


@admin.register(Forum)
class ForumAdmin(admin.ModelAdmin):
    list_display = ('title', 'description')


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'forum', 'created_by', 'created_at', 'is_published')
    list_filter = ('forum', 'is_published')
    search_fields = ('title', 'created_by__username')
    actions = ['make_published']

    def make_published(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f"{updated} temas publicados.")
    make_published.short_description = 'Marcar temas como publicados'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('topic', 'created_by', 'created_at', 'is_public')
    list_filter = ('is_public', 'created_at')
    search_fields = ('body', 'created_by__username')
    actions = ['make_public']

    def make_public(self, request, queryset):
        updated = queryset.update(is_public=True)
        self.message_user(request, f"{updated} posts publicados.")
    make_public.short_description = 'Marcar posts como públicos'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'created_by', 'created_at', 'is_public')
    list_filter = ('is_public', 'created_at')
    search_fields = ('body', 'created_by__username')


@admin.register(ForumReport)
class ForumReportAdmin(admin.ModelAdmin):
    list_display = ('post', 'reported_by', 'reason', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    actions = ['mark_reviewed']

    @admin.action(description='Marcar reportes como atendidos')
    def mark_reviewed(self, request, queryset):
        queryset.update(status=ForumReport.STATUS_REVIEWED)


admin.site.register(ForumPreference)
