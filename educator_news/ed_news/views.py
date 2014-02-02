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
from ed_news.forms import ArticleForm, CommentEntryForm

from ed_news.models import Article, Comment


def index(request):
    # Should this be in a settings/config file? Best practice says...
    #  Continue to follow HN example, which is 30 articles per screen.
    MAX_SUBMISSIONS = 30
    
    # Get a list of submissions, sorted by date.
    #  This is where MTI inheritance might be better; query all submissions,
    #  rather than building a list of submissions from separate articles
    #  and posts.
    articles = Article.objects.all().order_by('ranking_points', 'submission_time').reverse()[:MAX_SUBMISSIONS]
    
    # Note which articles should not get upvotes.
    # Build a list of articles, and their ages.
    articles_ages = []
    user_articles = []
    for article in articles:
        article_age = get_submission_age(article)
        comment_count = article.comment_set.count()
        articles_ages.append({'article': article, 'age': article_age, 'comment_count': comment_count})
        if request.user.is_authenticated() and article in request.user.userprofile.articles.all():
            user_articles.append(article)

    return render_to_response('ed_news/index.html',
                              {'articles_ages': articles_ages,
                               'user_articles': user_articles,
                               },
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
            # Check that this article has not already been submitted.
            articles = Article.objects.all()
            for article in articles:
                if article_form.cleaned_data['url'] == article.url:
                    # This should return the discussion page for this article.
                    return redirect('ed_news:submit')
            article = article_form.save(commit=False)
            article.submitter = request.user
            article.save()
            submission_accepted = True
            # Upvote this article.
            upvote_article(request, article.id)
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
    articles = Article.objects.all().order_by('submission_time').reverse()[:MAX_SUBMISSIONS]
    
    # Note which articles should not get upvotes.
    # Build a list of articles, and their ages.
    articles_ages = []
    user_articles = []
    for article in articles:
        article_age = get_submission_age(article)
        comment_count = article.comment_set.count()
        articles_ages.append({'article': article, 'age': article_age, 'comment_count': comment_count})
        if request.user.is_authenticated() and article in request.user.userprofile.articles.all():
            user_articles.append(article)

    return render_to_response('ed_news/new.html',
                              {'articles_ages': articles_ages,
                               'user_articles': user_articles,
                               },
                              context_instance = RequestContext(request))

def discuss(request, article_id, admin=False):
    article = Article.objects.get(id=article_id)
    age = get_submission_age(article)
    
    if request.method == 'POST':
        # Redirect unauthenticated users to register/ login.
        if not request.user.is_authenticated():
            return redirect('login')

        comment_entry_form = CommentEntryForm(data=request.POST)

        if comment_entry_form.is_valid():
            comment = comment_entry_form.save(commit=False)
            comment.author = request.user
            comment.parent_article = article
            comment.save()
            update_comment_ranking_points(article)
            update_ranking_points()
        else:
            # Invalid form/s.
            #  Print errors to console; should log these?
            print 'ce', comment_entry_form.errors

    # Prepare a blank entry form.
    comment_entry_form = CommentEntryForm()

    # Get comment information after processing form, to include comment
    #  that was just saved.
    comment_count = article.comment_set.count()
    # If user logged in, get article set.
    user_articles = []
    if request.user.is_authenticated():
        user_articles = request.user.userprofile.articles.all()
    # These are just the first-order comments?
    #  No, not at this point.
    comments = article.comment_set.all().order_by('ranking_points', 'submission_time').reverse()
    comment_set = []
    for comment in comments:
        age = get_submission_age(comment)
        # Report whether this user has already upvoted the comment.
        upvoted = False
        if request.user in comment.upvotes.all():
            upvoted = True
        comment_set.append({'comment': comment, 'age': age, 'upvoted': upvoted})

    if admin:
        template = 'ed_news/discuss_admin.html'
    else:
        template = 'ed_news/discuss.html'

    return render_to_response(template,
                              {'article': article, 'age': age,
                               'comment_count': comment_count,
                               'user_articles': user_articles,
                               'comment_entry_form': comment_entry_form,
                               'comment_set': comment_set,
                               },
                              context_instance = RequestContext(request))

def discuss_admin(request, article_id):
    if request.user == User.objects.get(username='ehmatthes'):
        response = discuss(request, article_id, True)
        return response
    else:
        return redirect('/discuss/%s/' % article_id)

def upvote_article(request, article_id):
    # Check if user has upvoted this article.
    #  If not, increment article points.
    #  Save article for this user.
    next_page = request.META.get('HTTP_REFERER', None) or '/'
    article = Article.objects.get(id=article_id)
    # Add this to user's articles, if not already there.
    user_articles = request.user.userprofile.articles.all()
    if article in user_articles:
        # This user already upvoted the article.
        return redirect(next_page)
    else:
        request.user.userprofile.articles.add(article)
        article.upvotes += 1
        article.save()

        # Increment karma of user who submitted article,
        #  unless this is the user who submitted.
        if request.user != article.submitter:
            increment_karma(article.submitter)

        # Update article ranking points, and redirect back to page.
        update_ranking_points()
        return redirect(next_page)

def upvote_comment(request, comment_id):
    next_page = request.META.get('HTTP_REFERER', None) or '/'
    comment = Comment.objects.get(id=comment_id)
    # Add this to user's upvoted comments, if not already there.
    upvoters = comment.upvotes.all()
    if request.user in upvoters or request.user == comment.author:
        return redirect(next_page)
    else:
        comment.upvotes.add(request.user)
        comment.save()
        increment_karma(comment.author)

    return redirect(next_page)

# --- Utility functions ---
def increment_karma(user):
    new_karma = user.userprofile.karma + 1
    user.userprofile.karma = new_karma
    user.userprofile.save()

def get_submission_age(submission):
    """Returns a formatted string stating how old the article is.
    """
    age = datetime.utcnow().replace(tzinfo=utc) - submission.submission_time
    if age.days == 1:
        return "1 day"
    elif age.days > 1:
        return "%d days" % age.days
    elif int(age.seconds) > 3600:
        return "%d hours" % (age.seconds/3600)
    elif age.seconds > 120:
        return "%d minutes" % (age.seconds/60)
    elif age.seconds > 60:
        return "1 minute"
    elif age.seconds > 1:
        return "%d seconds" % age.seconds
    else:
        return "1 second"

def update_ranking_points():
    # How many articles really need this?
    #  Only articles submitted over last x days?
    articles = Article.objects.all()
    for article in articles:
        newness_points = get_newness_points(article)
        comment_points = 5*article.comment_set.count()
        article.ranking_points = 10*article.upvotes + comment_points + newness_points
        article.save()
        
def update_comment_ranking_points(article):
    # Update the ranking points for an article's comments.
    comments = article.comment_set.all()
    for comment in comments:
        newness_points = get_newness_points(comment)
        voting_points = comment.upvotes.count() - comment.downvotes.count()
        # For now, 5*voting_points.
        comment.ranking_points = 5*voting_points + newness_points
        comment.save()
    

def get_newness_points(submission):
    # From 0 to 30 points, depending on newness. Linear function.
    #  This should probably be a rapidly-decaying function,
    #  rather than a linear function.
    age = (datetime.utcnow().replace(tzinfo=utc) - submission.submission_time).seconds
    newness_points = int(max((((86400.0-age)/86400)*30),0))
    return newness_points
