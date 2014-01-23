from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.contrib.auth.views import password_change

from ed_news.forms import UserForm, UserProfileForm
from ed_news.forms import SubmissionForm, ArticleForm

from ed_news.models import Submission


def index(request):
    # Static index page for now.
    return render_to_response('ed_news/index.html',
                              {},
                              context_instance = RequestContext(request))


# --- Authentication views ---
def logout_view(request):
    logout(request)
    # Redirect to home page.
    return redirect('/')

def profile(request):
    return render_to_response('registration/profile.html',
                              {},
                              context_instance = RequestContext(request))

def password_change_form(request):
    if request.method == 'POST':
        return password_change(request, post_change_redirect='/password_change_successful')
    else:
        return render_to_response('registration/password_change_form.html',
                                  {},
                                  context_instance = RequestContext(request))


def password_change_successful(request):
    return render_to_response('registration/password_change_successful.html',
                              {},
                              context_instance = RequestContext(request))

def register(request):
    # Assume registration won't work.
    registered = False

    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            # Save user's form data.
            user = user_form.save()

            user.set_password(user.password)
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

            # Registration was successful.
            registered = True

        else:
            # Invalid form/s.
            #  Print errors to console; should log these?
            print 'ufe', user_form.errors
            print 'pfe', profile_form.errors

    else:
        # Send blank forms.
        user_form = UserForm()
        profile_form = UserProfileForm()

    return render_to_response('registration/register.html',
                                  {'user_form': user_form,
                                   'profile_form': profile_form,
                                   'registered': registered,
                                   },
                                  context_instance = RequestContext(request))

# --- Educator News views ---
def submit(request):

    if request.method == 'POST':
        submission_form = SubmissionForm(data=request.POST)
        article_form = ArticleForm(data=request.POST)

        if submission_form.is_valid() and article_form.is_valid():
            print 'sf', submission_form
            print 'af', article_form
            print 'sfcd', submission_form.cleaned_data
            print 'afcd', article_form.cleaned_data
            print 'u', request.user
            print 'uid', request.user.id
            print 'utype', type(request.user)
            print article_form.cleaned_data['url']

            submission = submission_form.save(commit=False)
            submission.author = request.user
            submission_type = Submission.ARTICLE
            submission.save()
            
            article = article_form.save()

        else:
            # Invalid form/s.
            #  Print errors to console; should log these?
            print 'se', submission_form.errors
            print 'ae', article_form.errors

    else:
        # Send blank forms.
        submission_form = SubmissionForm()
        article_form = ArticleForm()

    return render_to_response('ed_news/submit.html',
                              {'submission_form': submission_form,
                               'article_form': article_form,
                               },
                              context_instance = RequestContext(request))
