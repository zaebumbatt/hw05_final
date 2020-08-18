from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm

import datetime


def index(request):
    post_list = Post.objects.order_by('-pub_date').all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'page': page,
        'paginator': paginator
    }
    return render(request, 'index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'group': group,
        'page': page,
        'paginator': paginator
    }
    return render(request, 'group.html', context)


@login_required
def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST or None, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('index')
    else:
        form = PostForm()
    return render(request, 'new.html', {'form': form})


def profile(request, username):
    user = get_object_or_404(User, username=username)
    fullname = user.get_full_name()
    posts_count = user.posts.filter(author=user).count()
    post_list = user.posts.filter(author=user)
    paginator = Paginator(post_list, 3)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    following = False
    if request.user.is_authenticated:
        if len(Follow.objects.filter(user=request.user, author=user)):
            following = True
        else:
            following = False

    context = {
        'username': user,
        'fullname': fullname,
        'posts_count': posts_count,
        'page': page,
        'paginator': paginator,
        'following': following,
    }
    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    user = get_object_or_404(User, username=username)
    fullname = user.get_full_name()
    post = get_object_or_404(Post, id=post_id)
    posts_count = user.posts.filter(author=user).count()
    items = post.comments.order_by('-created').filter(post=post)
    form = CommentForm()
    context = {
        'username': user,
        'fullname': fullname,
        'posts_count': posts_count,
        'post': post,
        'form': form,
        'items': items,
    }
    return render(request, 'post.html', context)


@login_required
def post_edit(request, username, post_id):
    user = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, id=post_id)
    if post.author == request.user:
        if request.method == 'POST':
            form = PostForm(request.POST or None, files=request.FILES or None)
            if form.is_valid():
                post = form.save(commit=False)
                post.author = user
                post.id = post_id
                post.pub_date = datetime.datetime.now()
                post.save()
                return redirect('post', username=user, post_id=post_id)
        else:
            form = PostForm(initial={'text': post.text, 'group': post.group})
    else:
        return redirect('index')
    return render(request, 'new.html', {'form': form, 'post': post})


@login_required
def add_comment(request, username, post_id):
    user = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, id=post_id)

    if request.method == 'POST':
        form = CommentForm(request.POST or None)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = get_object_or_404(User, username=request.user)
            comment.save()
            return redirect('post', username=user, post_id=post_id)

    return redirect('post', username=user, post_id=post_id)


@login_required
def follow_index(request):
    authors = []
    for author in Follow.objects.filter(user=request.user):
        authors.append(author.author)

    post_list = Post.objects.filter(author__in=authors).order_by('-pub_date')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'page': page,
        'paginator': paginator
    }
    return render(request, 'follow.html', context)


@login_required
def profile_follow(request, username):
    user = get_object_or_404(User, username=username)
    if user != request.user:
        Follow.objects.get_or_create(user=request.user, author=user)
    return redirect('profile', username=user)


@login_required
def profile_unfollow(request, username):
    user = get_object_or_404(User, username=username)
    unfollow, created = Follow.objects.get_or_create(user=request.user, author=user)
    unfollow.delete()

    return redirect('profile', username=user)


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)
