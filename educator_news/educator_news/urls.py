from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # My urls
    url(r'^', include('ed_news.urls', namespace='ed_news')),

    url(r'^admin/', include(admin.site.urls)),
)
