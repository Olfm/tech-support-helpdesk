from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.roles import is_operator
from .forms import PostForm, TopicForm
from .models import Post, Topic


def topic_list(request):
    # список тем, смотреть могут все
    topics = Topic.objects.select_related("author").prefetch_related("posts")
    return render(request, "forum/topic_list.html", {"topics": topics})


@login_required
def topic_create(request):
    # новая тема + сразу первое сообщение в ней
    if request.method == "POST":
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.author = request.user
            topic.save()
            Post.objects.create(
                topic=topic, author=request.user, body=form.cleaned_data["body"]
            )
            messages.success(request, "Тема создана.")
            return redirect(topic.get_absolute_url())
    else:
        form = TopicForm()
    return render(request, "forum/topic_form.html", {"form": form})


def topic_detail(request, pk):
    # тема и ответы. Отвечать может только залогиненный
    topic = get_object_or_404(Topic.objects.select_related("author"), pk=pk)
    form = PostForm()

    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        # в закрытую тему писать может только оператор
        if topic.is_closed and not is_operator(request.user):
            messages.error(request, "Тема закрыта для ответов.")
            return redirect(topic.get_absolute_url())
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.topic = topic
            post.author = request.user
            post.save()
            return redirect(topic.get_absolute_url())

    context = {
        "topic": topic,
        "posts": topic.posts.select_related("author"),
        "form": form,
        "can_moderate": is_operator(request.user),
    }
    return render(request, "forum/topic_detail.html", context)


@login_required
def topic_toggle_close(request, pk):
    # оператор может закрыть или снова открыть тему
    topic = get_object_or_404(Topic, pk=pk)
    if is_operator(request.user) and request.method == "POST":
        topic.is_closed = not topic.is_closed
        topic.save(update_fields=["is_closed"])
    return redirect(topic.get_absolute_url())
