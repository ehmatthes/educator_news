from django.conf.urls import patterns, url

from ed_news import views

urlpatterns = patterns('',
    # My urls

    # --- Educator News home page ---
    url(r'^$', views.index, name='index'),
    url(r'^submit/', views.submit, name='submit'),
)
