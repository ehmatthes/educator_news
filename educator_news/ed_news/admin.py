from django.contrib import admin
from ed_news.models import UserProfile
from ed_news.models import Article, TextPost, Comment

admin.site.register(UserProfile)
admin.site.register(Article)
admin.site.register(TextPost)
admin.site.register(Comment)
