from django import forms
from django.contrib.auth.models import User
from ed_news.models import UserProfile
from ed_news.models import Submission, Article

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ('username', 'password')

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ()

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ('title',)

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ('url',)
