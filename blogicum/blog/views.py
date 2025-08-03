from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView
)

from blog.forms import CommentForm, PostForm, UserForm
from blog.models import Category, Comment, Post, User


def posts_filter(posts=Post.objects.all()):
    return posts.select_related('author', 'category', 'location').filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    ).annotate(comment_count=Count('comments')).order_by('-pub_date')


class IndexListView(ListView):
    paginate_by = 10
    template_name = 'blog/index.html'

    def get_queryset(self):
        return posts_filter()


class PostDetailView(DetailView):
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_object(self):
        get_object_or_404(Post.objects, pk=self.kwargs['post_id'])
        self.post = Post.objects.select_related(
            'author',
            'location',
            'category'
        ).get(pk=self.kwargs['post_id'])
        if self.post.author != self.request.user and (
            self.post.is_published is False
            or self.post.category.is_published is False
            or self.post.pub_date > timezone.now()
        ):
            raise Http404
        return self.post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.post.comments.all()
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    template_name = 'blog/create.html'
    form_class = PostForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'blog/create.html'
    form_class = PostForm

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != request.user:
            return redirect(
                'blog:post_detail',
                post_id=self.kwargs['post_id']
            )
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return get_object_or_404(Post, pk=self.kwargs['post_id'])

    def get_success_url(self):
        return reverse_lazy('blog:post_detail',
                            kwargs={'post_id': self.object.id})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    template_name = 'blog/create.html'
    model = Post

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != request.user:
            return redirect(
                'blog:post_detail',
                post_id=self.kwargs['post_id']
            )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context

    def get_object(self):
        return get_object_or_404(Post, pk=self.kwargs['post_id'])

    def get_success_url(self):
        return reverse('blog:profile',
                       kwargs={'username': self.request.user.username})


class CommentCreateView(LoginRequiredMixin, CreateView):
    template_name = 'includes/comments.html'
    form_class = CommentForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['post_id'] = get_object_or_404(Post, pk=self.kwargs['post_id'])
        return kwargs

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post_id = self.kwargs['post_id']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail',
                            kwargs={'post_id': self.kwargs['post_id']})


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    template_name = 'blog/comment.html'
    model = Comment

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != request.user:
            return redirect(
                'blog:post_detail',
                post_id=self.kwargs['post_id']
            )
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return get_object_or_404(Comment, pk=self.kwargs['comment_id'])

    def get_success_url(self):
        return reverse_lazy('blog:post_detail',
                            kwargs={'post_id': self.kwargs['post_id']})


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'blog/comment.html'
    form_class = CommentForm

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != request.user:
            return redirect(
                'blog:post_detail',
                post_id=self.kwargs['post_id']
            )
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return get_object_or_404(Comment, pk=self.kwargs['comment_id'])

    def get_success_url(self):
        return reverse_lazy('blog:post_detail',
                            kwargs={'post_id': self.kwargs['post_id']})


class ProfileListView(ListView):
    template_name = 'blog/profile.html'
    paginate_by = 10

    def get_queryset(self):
        self.author = get_object_or_404(
            User, username=self.kwargs['username']
        )
        if self.request.user != self.author:
            return posts_filter(self.author.posts.all())
        return self.author.posts.all().annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.author
        return context


class CategoryListView(ListView):
    paginate_by = 10
    template_name = 'blog/category.html'

    def get_queryset(self):
        self.category = get_object_or_404(
            Category, is_published=True, slug=self.kwargs['category_slug']
        )
        return posts_filter(self.category.posts.all())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class UserUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'blog/user.html'
    model = User
    form_class = UserForm

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )

    def get_object(self):
        return self.request.user
