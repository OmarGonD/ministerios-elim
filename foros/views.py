from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.core.paginator import Paginator
from .models import Forum, Topic, Post, Vote
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


def forum_list(request):
    forums = Forum.objects.all()
    return render(request, 'foros/forum_list.html', {'forums': forums})


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
        'user_votes': user_votes
    })


@login_required
def vote_post(request, post_pk):
    post = get_object_or_404(Post, pk=post_pk)
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
            topic.is_published = True  # Verified: auto-publish for now
            topic.save()
            return redirect('foros:topic_detail', forum_pk=forum.pk, topic_pk=topic.pk)
    else:
        form = TopicForm()
    return render(request, 'foros/create_topic.html', {'form': form, 'forum': forum})


@login_required
def create_post(request, forum_pk, topic_pk):
    topic = get_object_or_404(Topic, pk=topic_pk, forum__pk=forum_pk)
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


def topics_api(request, forum_pk):
    forum = get_object_or_404(Forum, pk=forum_pk)
    topics = forum.topics.filter(is_published=True).order_by('-created_at')[:100]
    data = [{'id': t.pk, 'title': t.title, 'created_by': str(t.created_by), 'created_at': t.created_at} for t in topics]
    return JsonResponse({'forum': forum.pk, 'topics': data})


def posts_api(request, forum_pk, topic_pk):
    topic = get_object_or_404(Topic, pk=topic_pk, forum__pk=forum_pk)
    posts = topic.posts.filter(is_public=True).order_by('created_at')[:200]
    data = [{'id': p.pk, 'body': p.body, 'created_by': str(p.created_by), 'created_at': p.created_at} for p in posts]
    return JsonResponse({'topic': topic.pk, 'posts': data})
