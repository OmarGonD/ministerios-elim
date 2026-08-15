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
