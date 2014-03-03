from django import forms
from django.contrib.auth.models import User
from ed_news.models import UserProfile
from ed_news.models import Article, TextPost, Comment

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ('username', 'password')


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ()

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ('title', 'url',)
        widgets = {
            'title': forms.TextInput(attrs={'size': 80}),
            'url': forms.TextInput(attrs={'size': 80}),
            }
        labels = {
            'url': 'url',
            }

class TextPostForm(forms.ModelForm):
    class Meta:
        model = TextPost
        fields = ('title', 'post_body',)
        widgets = {
            'title': forms.TextInput(attrs={'size': 80}),
            'post_body': forms.Textarea(attrs={'cols': 100, 'rows': 10}),
            }
        labels = {
            'post_body': '',
            }


class EditUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email',)

class EditUserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('email_public', 'show_invisible')

class CommentEntryForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('comment_text',)
        widgets = {
            'comment_text': forms.Textarea(attrs={'cols': 80, 'rows': 6}),
            }
        labels = {
            'comment_text': '',
            }
