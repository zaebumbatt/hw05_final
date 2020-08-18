from django.forms import ModelForm
from .models import Post, Comment
from django import forms


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['group', 'text', 'image']
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
        fields = ['text']
