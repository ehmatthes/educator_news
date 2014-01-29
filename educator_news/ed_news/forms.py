from django import forms
from django.contrib.auth.models import User
from ed_news.models import UserProfile
from ed_news.models import Article, Comment

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

class EditUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email',)

class EditUserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('email_public',)

class CommentEntryForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('comment_text',)
