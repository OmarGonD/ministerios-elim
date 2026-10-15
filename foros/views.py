from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.conf import settings
from .models import Forum, Topic, Post, Vote, ForumReport, ForumPreference
from django import forms
from django.db.models import Count


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['title']


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['body']


def _is_moderator(user):
    return user.is_authenticated and (
        user.is_superuser or
        user.groups.filter(name='Moderadores de foros').exists()
    )


def _notify_user(user, subject, message, preference_field):
    if not user or not user.email:
        return
    preference, _ = ForumPreference.objects.get_or_create(user=user)
    if getattr(preference, preference_field):
        send_mail(
            subject, message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'webmaster@localhost'),
            [user.email], fail_silently=True,
        )


def forum_list(request):
    forums = Forum.objects.all()
    preference = None
    if request.user.is_authenticated:
        preference, _ = ForumPreference.objects.get_or_create(user=request.user)
    return render(request, 'foros/forum_list.html', {
        'forums': forums,
        'preference': preference,
        'is_moderator': _is_moderator(request.user),
    })


def forum_detail(request, pk):
    forum = get_object_or_404(Forum, pk=pk)
    # Pinned topics first
    topics_qs = forum.topics.filter(is_published=True).order_by('-is_pinned', '-created_at')
    paginator = Paginator(topics_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'foros/forum_detail.html', {'forum': forum, 'page_obj': page_obj})


def topic_detail(request, forum_pk, topic_pk):
    topic = get_object_or_404(Topic, pk=topic_pk, forum__pk=forum_pk)
    if not topic.is_published and not (
        _is_moderator(request.user) or topic.created_by_id == getattr(request.user, 'pk', None)
    ):
        return HttpResponseForbidden('Este tema está pendiente de moderación.')
    
    # Increment views
    # Use session to prevent counting refresh as new view
    session_key = f'viewed_topic_{topic.pk}'
    if not request.session.get(session_key, False):
        topic.views += 1
        topic.save()
        request.session[session_key] = True

    posts_qs = topic.posts.filter(is_public=True).annotate(vote_count=Count('votes')).order_by('created_at')
    paginator = Paginator(posts_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get user votes for these posts if logged in
    user_votes = set()
    if request.user.is_authenticated:
        user_votes = set(Vote.objects.filter(user=request.user, post__in=page_obj.object_list).values_list('post_id', flat=True))

    return render(request, 'foros/topic_detail.html', {
        'topic': topic, 
        'page_obj': page_obj,
        'user_votes': user_votes,
        'is_moderator': _is_moderator(request.user),
    })


@login_required
@require_POST
def vote_post(request, post_pk):
    post = get_object_or_404(Post, pk=post_pk, is_public=True, topic__is_published=True)
    vote, created = Vote.objects.get_or_create(user=request.user, post=post)
    
    if not created:
        # Toggle: if exists, delete (unlike)
        vote.delete()
        is_liked = False
    else:
        is_liked = True

    return JsonResponse({
        'status': 'ok', 
        'is_liked': is_liked, 
        'total_votes': post.votes.count()
    })


@login_required
def create_topic(request, forum_pk):
    forum = get_object_or_404(Forum, pk=forum_pk)
    if request.method == 'POST':
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.forum = forum
            topic.created_by = request.user
            topic.is_published = _is_moderator(request.user)
            topic.save()
            if topic.is_published:
                return redirect('foros:topic_detail', forum_pk=forum.pk, topic_pk=topic.pk)
            return render(request, 'foros/create_submitted.html', {'object': topic, 'type': 'tema'})
    else:
        form = TopicForm()
    return render(request, 'foros/create_topic.html', {'form': form, 'forum': forum})


@login_required
def create_post(request, forum_pk, topic_pk):
    topic = get_object_or_404(Topic, pk=topic_pk, forum__pk=forum_pk, is_published=True)
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.topic = topic
            post.created_by = request.user
            post.is_public = False  # moderation
            post.save()
            return render(request, 'foros/create_submitted.html', {'object': post, 'type': 'post'})
    else:
        form = PostForm()
    return render(request, 'foros/create_post.html', {'form': form, 'topic': topic})


@login_required
@require_POST
def report_post(request, post_pk):
    post = get_object_or_404(Post, pk=post_pk, is_public=True)
    reason = request.POST.get('reason', '').strip()
    if len(reason) < 5:
        messages.error(request, 'Explica brevemente el motivo del reporte.')
    else:
        _, created = ForumReport.objects.get_or_create(
            post=post, reported_by=request.user, defaults={'reason': reason[:500]}
        )
        messages.success(request, 'Reporte enviado a moderación.' if created else 'Ya habías reportado esta publicación.')
    return redirect('foros:topic_detail', forum_pk=post.topic.forum_id, topic_pk=post.topic_id)


@login_required
@require_POST
def update_preferences(request):
    preference, _ = ForumPreference.objects.get_or_create(user=request.user)
    preference.notify_replies = request.POST.get('notify_replies') == 'on'
    preference.notify_moderation = request.POST.get('notify_moderation') == 'on'
    preference.save(update_fields=['notify_replies', 'notify_moderation'])
    messages.success(request, 'Preferencias de notificación actualizadas.')
    return redirect('foros:forum_list')


@login_required
def moderation_dashboard(request):
    if not _is_moderator(request.user):
        return HttpResponseForbidden('No tienes permisos de moderación.')
    return render(request, 'foros/moderation_dashboard.html', {
        'pending_topics': Topic.objects.filter(is_published=False).select_related('forum', 'created_by'),
        'pending_posts': Post.objects.filter(is_public=False).select_related('topic', 'created_by'),
        'reports': ForumReport.objects.filter(status=ForumReport.STATUS_PENDING).select_related('post__topic', 'reported_by'),
    })


@login_required
@require_POST
def moderate(request):
    if not _is_moderator(request.user):
        return HttpResponseForbidden('No tienes permisos de moderación.')
    action = request.POST.get('action')
    object_id = request.POST.get('object_id')
    if action == 'approve_topic':
        topic = Topic.objects.filter(pk=object_id).select_related('created_by').first()
        if topic:
            topic.is_published = True
            topic.save(update_fields=['is_published'])
            _notify_user(topic.created_by, 'Tu tema fue aprobado', topic.title, 'notify_moderation')
    elif action == 'reject_topic':
        topic = Topic.objects.filter(pk=object_id, is_published=False).select_related('created_by').first()
        if topic:
            _notify_user(topic.created_by, 'Tu tema no fue aprobado', topic.title, 'notify_moderation')
            topic.delete()
    elif action == 'approve_post':
        post = Post.objects.filter(pk=object_id).select_related('created_by', 'topic__created_by').first()
        if post:
            post.is_public = True
            post.save(update_fields=['is_public'])
            _notify_user(post.created_by, 'Tu respuesta fue aprobada', post.topic.title, 'notify_moderation')
            if post.topic.created_by_id != post.created_by_id:
                _notify_user(post.topic.created_by, 'Nueva respuesta en tu tema', post.topic.title, 'notify_replies')
    elif action == 'reject_post':
        post = Post.objects.filter(pk=object_id, is_public=False).select_related('created_by', 'topic').first()
        if post:
            _notify_user(post.created_by, 'Tu respuesta no fue aprobada', post.topic.title, 'notify_moderation')
            post.delete()
    elif action == 'hide_post':
        Post.objects.filter(pk=object_id).update(is_public=False)
    elif action == 'resolve_report':
        ForumReport.objects.filter(pk=object_id).update(status=ForumReport.STATUS_REVIEWED)
    elif action == 'hide_reported_post':
        report = ForumReport.objects.filter(pk=object_id).select_related('post').first()
        if report:
            Post.objects.filter(pk=report.post_id).update(is_public=False)
            report.status = ForumReport.STATUS_REVIEWED
            report.save(update_fields=['status'])
    elif action == 'dismiss_report':
        ForumReport.objects.filter(pk=object_id).update(status=ForumReport.STATUS_DISMISSED)
    messages.success(request, 'La cola de moderación fue actualizada.')
    return redirect('foros:moderation_dashboard')


def topics_api(request, forum_pk):
    forum = get_object_or_404(Forum, pk=forum_pk)
    topics = forum.topics.filter(is_published=True).order_by('-created_at')[:100]
    data = [{'id': t.pk, 'title': t.title, 'created_by': str(t.created_by), 'created_at': t.created_at} for t in topics]
    return JsonResponse({'forum': forum.pk, 'topics': data})


def posts_api(request, forum_pk, topic_pk):
    topic = get_object_or_404(Topic, pk=topic_pk, forum__pk=forum_pk, is_published=True)
    posts = topic.posts.filter(is_public=True).order_by('created_at')[:200]
    data = [{'id': p.pk, 'body': p.body, 'created_by': str(p.created_by), 'created_at': p.created_at} for p in posts]
    return JsonResponse({'topic': topic.pk, 'posts': data})
