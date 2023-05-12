from django.shortcuts import get_object_or_404
from django.db.models import QuerySet

from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormMixin, FormView

from .models import Post
from .forms import CommentForm, EmailPostForm
from .services_blog import (
    get_all_posts_with_filter, get_context_data_about_post,
    save_comment_to_db, send_email_validation
)


class PostListView(ListView):
    paginate_by = 10
    template_name = 'blog/post-list.html'

    def get_queryset(self, **kwargs) -> QuerySet:
        return get_all_posts_with_filter(self)  # QuerySet

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context["tag"] = self.kwargs.get('tag_slug')
        context["query"] = self.request.GET.get('query')
        return context


class PostDetailView(FormMixin, DetailView):
    template_name = 'blog/post-detail.html'
    form_class = CommentForm

    def get_object(self):
        return get_object_or_404(Post, status='published',
                                 slug=self.kwargs.get('slug'),
                                 publish__year=self.kwargs.get('year'),
                                 publish__month=self.kwargs.get('month'),
                                 publish__day=self.kwargs.get('day')
                                 )

    def get_success_url(self):
        return self.get_object().get_absolute_url()

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        return get_context_data_about_post(self, context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()

        if form.is_valid():
            save_comment_to_db(self, form)
            return self.form_valid(form)
        else:
            print("Invalid form")
            return self.form_invalid(form)


class PostShareView(FormView):
    form_class = EmailPostForm
    template_name = 'blog/post-share.html'

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context["post"] = get_object_or_404(
            Post, id=self.kwargs.get('post_id'))
        context["sent"] = False
        return context

    def form_valid(self, form):
        context_raw = self.get_context_data()
        context = send_email_validation(self, form, context_raw)
        return self.render_to_response(context)
