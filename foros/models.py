from django.db import models
from django.conf import settings
from django.utils import timezone


class Forum(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title


class Topic(models.Model):
    forum = models.ForeignKey(Forum, related_name='topics', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    is_published = models.BooleanField(default=False)  # moderation
    is_pinned = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title


class Post(models.Model):
    topic = models.ForeignKey(Topic, related_name='posts', on_delete=models.CASCADE)
    body = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(default=timezone.now)
    is_public = models.BooleanField(default=True)  # moderation flag

    def __str__(self):
        return f"Post by {self.created_by} on {self.topic}"


class Comment(models.Model):
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    body = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(default=timezone.now)
    is_public = models.BooleanField(default=True)

    def __str__(self):
        return f"Comment by {self.created_by}"


class Vote(models.Model):
    post = models.ForeignKey(Post, related_name='votes', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='forum_votes', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')

    def __str__(self):
        return f"{self.user} likes {self.post}"


class ForumReport(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_REVIEWED = 'reviewed'
    STATUS_DISMISSED = 'dismissed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendiente'),
        (STATUS_REVIEWED, 'Atendido'),
        (STATUS_DISMISSED, 'Descartado'),
    ]

    post = models.ForeignKey(Post, related_name='reports', on_delete=models.CASCADE)
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='forum_reports',
        on_delete=models.CASCADE,
    )
    reason = models.CharField(max_length=500)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['post', 'reported_by'], name='unique_post_report_per_user')
        ]
        ordering = ['-created_at']


class ForumPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name='forum_preference',
        on_delete=models.CASCADE,
    )
    notify_replies = models.BooleanField(default=False)
    notify_moderation = models.BooleanField(default=True)

    def __str__(self):
        return f'Preferencias de foro de {self.user}'
