from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth import logout, login, authenticate
from django.core.urlresolvers import reverse
from django.contrib.auth.views import password_change
from ed_news.forms import UserForm, UserProfileForm
from ed_news.models import UserProfile

def index(request):
    # Static index page for now.
    return render_to_response('ed_news/index.html',
                              {},
                              context_instance = RequestContext(request))


# Authentication views
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
            print 'un', user.username

            user.set_password(user.password)
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

            # Registration was successful.
            registered = True

            # Not requiring email validation yet, so log user in.
            #user = authenticate(username=user.username, password=user.password)
            #login(request, user)
            print 'un, pw', user.username,  user.password

        else:
            # Invalid form/s.
            print 'uf', user_form
            print 'ufe', user_form.errors
            print 'pf', profile_form
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
