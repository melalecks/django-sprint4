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


PAGINATE = 10


def posts_filter(queryset=Post.objects.all(),
                 filter_published=True,
                 select_related=True,
                 annotate_comments=True):
    qs = queryset

    if filter_published:
        qs = qs.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        )

    if select_related:
        qs = qs.select_related('author', 'category', 'location')

    if annotate_comments:
        qs = qs.annotate(comment_count=Count('comments'))

    return qs.order_by(*Post._meta.ordering)


class IndexListView(ListView):
    paginate_by = PAGINATE
    template_name = 'blog/index.html'
    queryset = posts_filter()


class PostDetailView(DetailView):
    template_name = 'blog/detail.html'
    model = Post
    pk_url_kwarg = 'post_id'

    def get_object(self):
        post = super().get_object()
        if post.author == self.request.user:
            return post
        published_posts = Post.objects.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        )
        try:
            return published_posts.get(pk=self.kwargs['post_id'])
        except Post.DoesNotExist:
            raise Http404

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs,
                                        form=CommentForm(),
                                        comments=self.object.comments.all)


class PostCreateView(LoginRequiredMixin, CreateView):
    template_name = 'blog/create.html'
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile', args=[self.request.user.username])


class PostMixin():
    template_name = 'blog/create.html'
    model = Post
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != request.user:
            return redirect(
                'blog:post_detail',
                post_id=self.kwargs['post_id']
            )
        return super().dispatch(request, *args, **kwargs)


class PostUpdateView(PostMixin, LoginRequiredMixin, UpdateView):
    form_class = PostForm

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'post_id': self.kwargs['post_id']})


class PostDeleteView(PostMixin, LoginRequiredMixin, DeleteView):
    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs,
                                        form=PostForm(instance=self.object))

    def get_success_url(self):
        return reverse('blog:profile', args=[self.request.user.username])


class CommentCreateView(LoginRequiredMixin, CreateView):
    template_name = 'includes/comments.html'
    form_class = CommentForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'post_id': self.kwargs['post_id']})


class CommentMixin():
    template_name = 'blog/comment.html'
    model = Comment
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != request.user:
            return redirect(
                'blog:post_detail',
                post_id=self.kwargs['post_id']
            )
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'post_id': self.kwargs['post_id']})


class CommentDeleteView(CommentMixin, LoginRequiredMixin, DeleteView):
    pass


class CommentUpdateView(CommentMixin, LoginRequiredMixin, UpdateView):
    form_class = CommentForm


class ProfileListView(ListView):
    template_name = 'blog/profile.html'
    paginate_by = PAGINATE

    def get_author(self):
        return get_object_or_404(User, username=self.kwargs['username'])

    def get_queryset(self):
        author = self.get_author()
        if self.request.user != author:
            return posts_filter(author.posts.all())
        return posts_filter(author.posts.all(), filter_published=False)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs, profile=self.get_author())


class CategoryListView(ListView):
    paginate_by = PAGINATE
    template_name = 'blog/category.html'

    def get_category(self):
        return get_object_or_404(
            Category, is_published=True, slug=self.kwargs['category_slug']
        )

    def get_queryset(self):
        return posts_filter(self.get_category().posts.all())

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs, category=self.get_category())


class UserUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'blog/user.html'
    model = User
    form_class = UserForm

    def get_success_url(self):
        return reverse(
            'blog:profile', args=[self.request.user.username])

    def get_object(self):
        return self.request.user
