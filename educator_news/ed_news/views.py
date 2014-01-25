from datetime import datetime

from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.contrib.auth.views import password_change
from django.contrib.auth.models import User
from django.utils.timezone import utc

from ed_news.forms import UserForm, UserProfileForm
from ed_news.forms import EditUserForm, EditUserProfileForm
from ed_news.forms import ArticleForm

from ed_news.models import Article


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

def profile(request, profile_id):
    # The value of profile_id is the profile to be displayed, which
    #  may not be the current user.
    # The value own_profile is true when user is viewing their own
    #  profile.
    target_user = User.objects.get(id=profile_id)
    if target_user == request.user:
        own_profile = True
    else:
        own_profile = False

    return render_to_response('registration/profile.html',
                              {'target_user': target_user,
                               'own_profile': own_profile,
                               },
                              context_instance = RequestContext(request))

def edit_profile(request):
    user = request.user
    if request.method == 'POST':
        edit_user_form = EditUserForm(data=request.POST, instance=request.user)
        edit_user_profile_form = EditUserProfileForm(data=request.POST, instance=request.user.userprofile)

        if edit_user_form.is_valid():
            user = edit_user_form.save()
            user_profile = edit_user_profile_form.save()

        else:
            # Invalid form/s.
            #  Print errors to console; should log these?
            print 'eue', edit_user_form.errors
            print 'eupe', edit_user_profile_form.errors

    else:
        # Send blank forms.
        edit_user_form = EditUserForm(instance=request.user)
        edit_user_profile_form = EditUserProfileForm(instance=request.user.userprofile)
    return render_to_response('registration/edit_profile.html',
                              {'edit_user_form': edit_user_form,
                               'edit_user_profile_form': edit_user_profile_form,
                               },
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
    """Page to allow users to submit a new article.
    Will also allow users to submit a text post later.
    """

    submission_accepted = False
    if request.method == 'POST':
        article_form = ArticleForm(data=request.POST)

        if article_form.is_valid():
            article = article_form.save(commit=False)
            article.author = request.user
            article.save()
            submission_accepted = True

        else:
            # Invalid form/s.
            #  Print errors to console; should log these?
            print 'ae', article_form.errors

    else:
        # Send blank forms.
        article_form = ArticleForm()

    return render_to_response('ed_news/submit.html',
                              {'article_form': article_form,
                               'submission_accepted': submission_accepted,
                               },
                              context_instance = RequestContext(request))


def new(request):
    """Page to show the newest submissions.
    """

    # Should this be in a settings/config file? Best practice says...
    #  Continue to follow HN example, which is 30 articles per screen.
    MAX_SUBMISSIONS = 30
    
    # Get a list of submissions, sorted by date.
    #  This is where MTI inheritance might be better; query all submissions,
    #  rather than building a list of submissions from separate articles
    #  and posts.
    articles = Article.objects.all().order_by('submission_time').reverse()[:30]
    #article_age = get_submission_age(article)
    article_ages = [get_submission_age(article) for article in articles]
    for article_age in article_ages:
        print article_age

    return render_to_response('ed_news/new.html',
                              {'articles': articles,
                               'article_ages': article_ages,
                               },
                              context_instance = RequestContext(request))


# --- Utility functions ---
def get_submission_age(submission):
    age = datetime.utcnow().replace(tzinfo=utc) - submission.submission_time
    if age.days == 1:
        return "1 day"
    elif age.days > 1:
        return "%d days" % age.days
    elif age.seconds > 3600:
        return "%d hours" % age.seconds/3600
    elif age.seconds > 120:
        return "%d minutes" % age.seconds/60
    elif age.seconds > 60:
        return "1 minute"
    elif age.seconds > 1:
        return "%d seconds" % age.seconds
    else:
        return "1 second"
