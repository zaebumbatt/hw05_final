from django import forms
from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        labels = {
            'group': 'Группа',
            'text': 'Текст'
        }
        help_texts = {
            'group': 'Выберите группу',
            'text': 'Введите текст ваше поста',
            'image': 'Вставьте изображение'
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
