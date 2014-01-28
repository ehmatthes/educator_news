from django.contrib import admin
from ed_news.models import UserProfile
from ed_news.models import Article, Comment

admin.site.register(UserProfile)
admin.site.register(Article)
admin.site.register(Comment)
