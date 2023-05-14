from .models import Post, Comment
from taggit.models import Tag

from django.core.mail import send_mail
from django.db.models import QuerySet, Count
from django.shortcuts import get_object_or_404
from django.contrib.postgres.search import (
    SearchVector, SearchQuery, SearchRank
)


def get_all_posts_with_filter(self_f) -> QuerySet:
    posts_queryset = Post.published.all()
    tag_slug = self_f.kwargs.get('tag_slug')
    query = self_f.request.GET.get('query')
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        posts_queryset = posts_queryset.filter(tags__in=[tag])
    if query:
        search_vector = SearchVector('title', weight='A') + \
                        SearchVector('body', weight='B')
        search_query = SearchQuery(query)

        posts_queryset = Post.published.annotate(
            rank=SearchRank(search_vector, search_query)
        ).filter(rank__gte=0.3).order_by('-rank')
    return posts_queryset


def get_context_data_about_post(self_f, context: dict) -> dict:
    post = self_f.get_object()
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids) \
        .exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')) \
        .order_by('-same_tags', '-publish')[:4]

    comments = Comment.objects.filter(post=post, active=True)
    context["similar_posts"] = similar_posts
    context["comments"] = comments
    context["form"] = self_f.get_form()

    return context


def save_comment_to_db(self_f, form) -> None:
    comment = form.save(commit=False)
    comment.post = self_f.get_object()
    comment.save()


def send_email_validation(self_f, form, context: dict) -> dict:
    cd = form.cleaned_data
    post = context['post']
    post_url = self_f.request.build_absolute_uri(
        post.get_absolute_url()
    )
    subject = f"{cd['name']} recommends you read {post.title}"
    message = f"Read {post.title} at {post_url}\n\n" \
              f"{cd['name']}\'s comments: {cd['comments']}"

    send_mail(subject, message, 'admin@myblog.com', [cd['to']])
    context['sent'], context['form'] = True, form

    return context
