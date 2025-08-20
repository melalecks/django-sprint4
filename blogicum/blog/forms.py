from django import forms

from .models import Comment, Post, User


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ('author',)
        # fields = [
        #     'is_published',
        #     'title', 'text',
        #     'pub_date',
        #     'image',
        #     'location',
        #     'category'
        # ]
        widgets = {'pub_date': forms.DateInput(attrs={'type': 'date'})}

    # def __init__(self, *args, **kwargs):
    #     self.user = kwargs.pop('user', None)
    #     super().__init__(*args, **kwargs)

    # def save(self, commit=True):
    #     instance = super().save(commit=False)
    #     if self.user:
    #         instance.author = self.user
    #     if commit:
    #         instance.save()
    #     return instance


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)

    # def __init__(self, *args, **kwargs):
    #     self.user = kwargs.pop('user', None)
    #     self.post = kwargs.pop('post_id', None)
    #     super().__init__(*args, **kwargs)

    # def save(self, commit=True):
    #     instance = super().save(commit=False)
    #     if self.user:
    #         instance.author = self.user
    #     if self.post:
    #         instance.post = self.post
    #     if commit:
    #         instance.save()
    #     return instance
