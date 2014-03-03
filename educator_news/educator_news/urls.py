from django.conf import settings
from django.conf.urls import patterns, include, url
from django.core.urlresolvers import reverse
    

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # My urls
    url(r'^', include('ed_news.urls', namespace='ed_news')),

    url(r'^admin/', include(admin.site.urls)),

    # Auth urls
    url(r'^login/', 'ed_news.views.login_view', name='login_view'),
    url(r'^logout/', 'ed_news.views.logout_view', name='logout_view'),
    url(r'^profile/(?P<profile_id>\d+)/$', 'ed_news.views.profile', name='profile'),
    url(r'^edit_profile/', 'ed_news.views.edit_profile', name='edit_profile'),
    url(r'^password_change/', 'ed_news.views.password_change_form', name='password_change_form'),
    url(r'^password_change_successful/', 'ed_news.views.password_change_successful', name='password_change_successful'),
    url(r'^register/', 'ed_news.views.register', name='register'),
)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('', url(r'^__debug__/', include(debug_toolbar.urls)),)
