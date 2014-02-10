from datetime import datetime

from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.contrib.auth.views import password_change
from django.contrib.auth.models import User, Group
from django.utils.timezone import utc

from ed_news.forms import UserForm, UserProfileForm
from ed_news.forms import EditUserForm, EditUserProfileForm
from ed_news.forms import ArticleForm, CommentEntryForm

from ed_news.models import Submission, Article, TextPost, Comment

# These should be moved to a settings, config, or .env file.
# Moderation level will start at 10, increase as site becomes more active.
#  Should have low level if debug = True?
KARMA_LEVEL_MODERATORS = 2
#  Continue to follow HN example, which is 30 articles per screen.
MAX_SUBMISSIONS = 30
# Number of flags it takes to make an article disappear.
#  Or maybe one flag from a super-mod?
FLAGS_TO_DISAPPEAR = 1

def index(request):
    # Get a list of submissions, sorted by date.

    if request.user.userprofile.show_invisible:
        submissions = Submission.objects.all().order_by('ranking_points', 'submission_time').reverse()[:MAX_SUBMISSIONS]
    else:
        submissions = Submission.objects.filter(visible=True).order_by('ranking_points', 'submission_time').reverse()[:MAX_SUBMISSIONS]
        
    # Note which submissions should not get upvotes.
    # Build a list of submissions, and their ages.
    submission_set = []
    for submission in submissions:
        submission_age = get_submission_age(submission)
        comment_count = get_comment_count(submission)
        
        flagged = False
        if request.user in submission.flags.all():
            flagged = True

        can_flag = False
        if request.user.is_authenticated() and request.user != submission.submitter and request.user.has_perm('ed_news.can_flag_submission'):
            can_flag = True

        upvoted = False
        if request.user in submission.upvotes.all():
            upvoted = True

        submission_set.append({'submission': submission, 'age': submission_age,
                                'comment_count': comment_count,
                                'flagged': flagged, 'can_flag': can_flag,
                                'upvoted': upvoted,
                                })

    return render_to_response('ed_news/index.html',
                              {'submission_set': submission_set,
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

    # If user is moderator, they can choose to set show_invisible = True.
    allow_show_invisible = False
    if is_moderator(user):
        allow_show_invisible = True

    if request.method == 'POST':
        edit_user_form = EditUserForm(data=request.POST, instance=request.user)
        # if user is moderator, let them set show_invisible
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
                               'allow_show_invisible': allow_show_invisible,
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

    # Get a list of submissions, sorted by date.
    #  This is where MTI inheritance might be better; query all submissions,
    #  rather than building a list of submissions from separate articles
    #  and posts.

    if request.user.userprofile.show_invisible:
        articles = Article.objects.all().order_by('ranking_points', 'submission_time').reverse()[:MAX_SUBMISSIONS]
    else:
        articles = Article.objects.filter(visible=True).order_by('ranking_points', 'submission_time').reverse()[:MAX_SUBMISSIONS]
    
    # Note which articles should not get upvotes.
    # Build a list of articles, and their ages.
    articles_ages = []
    user_articles = []
    for article in articles:
        article_age = get_submission_age(article)
        comment_count = get_comment_count(article)

        flagged = False
        if request.user in article.flags.all():
            flagged = True

        can_flag = False
        if request.user.is_authenticated() and request.user != article.submitter and request.user.has_perm('ed_news.can_flag_article'):
            can_flag = True

        articles_ages.append({'article': article, 'age': article_age,
                              'comment_count': comment_count,
                              'flagged': flagged, 'can_flag': can_flag,
                              })
        
        # DEV: this should be an attribute of each article, rather than a separate list.
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
    comment_count = get_comment_count(article)

    # If user logged in, get article set.
    #  Also check if article is flagged by this user.
    user_articles = []
    flagged = False
    can_flag = False
    if request.user.is_authenticated():
        user_articles = request.user.userprofile.articles.all()
        if request.user in article.flags.all() and request.user != article.submitter:
            flagged = True

        if request.user != article.submitter and request.user.has_perm('ed_news.can_flag_article'):
            can_flag = True

    comment_set = []
    get_comment_set(article, request, comment_set)


    if admin:
        template = 'ed_news/discuss_admin.html'
    else:
        template = 'ed_news/discuss.html'

    return render_to_response(template,
                              {'article': article, 'age': age,
                               'comment_count': comment_count,
                               'user_articles': user_articles,
                               'flagged': flagged, 'can_flag': can_flag,
                               'comment_entry_form': comment_entry_form,
                               'comment_set': comment_set,
                               },
                              context_instance = RequestContext(request))

def reply(request, article_id, comment_id):
    article = Article.objects.get(id=article_id)
    article_age = get_submission_age(article)
    comment = Comment.objects.get(id=comment_id)
    comment_age = get_submission_age(comment)
    
    # Redirect unauthenticated users to register/ login.
    if not request.user.is_authenticated():
        return redirect('login')

    if request.method == 'POST':

        reply_entry_form = CommentEntryForm(data=request.POST)

        if reply_entry_form.is_valid():
            reply = reply_entry_form.save(commit=False)
            reply.author = request.user
            reply.parent_comment = comment
            reply.save()
            # Update the ranking points for all comments on 
            #  an article at the same time, to be fair.
            update_comment_ranking_points(article)
            update_ranking_points()
            # Redirect to discussion page.
            return redirect('/discuss/%s/' % article.id)
        else:
            # Invalid form/s.
            #  Print errors to console; should log these?
            print 'ce', reply_entry_form.errors

    # Prepare a blank entry form.
    reply_entry_form = CommentEntryForm()



    # Get comment information after processing form, to include comment
    #  that was just saved.
    comment_count = article.comment_set.count()
    comment_count = get_comment_count(article)

    # If user logged in, get article set.
    #  Also check if article is flagged by this user.
    user_articles = []
    flagged = False
    can_flag = False
    if request.user.is_authenticated():
        user_articles = request.user.userprofile.articles.all()
        if request.user in article.flags.all() and request.user != article.submitter:
            flagged = True
        if request.user != article.submitter and request.user.has_perm('ed_news.can_flag_article'):
            can_flag = True

    upvoted, can_upvote = False, False
    downvoted, can_downvote = False, False
    can_flag_comment = False
    comment_flagged = False
    if request.user.is_authenticated() and request.user != comment.author:
        if request.user in comment.upvotes.all():
            upvoted = True
        else:
            can_upvote = True
        if request.user in comment.downvotes.all():
            downvoted = True
        elif request.user.has_perm('ed_news.can_downvote_comment'):
            can_downvote = True
        if request.user in comment.flags.all():
            comment_flagged = True
        if request.user.has_perm('ed_news.can_flag_comment'):
            can_flag_comment = True

    return render_to_response('ed_news/reply.html',
                              {'article': article, 'article_age': article_age,
                               'comment': comment, 'comment_age': comment_age,
                               'comment_count': comment_count,
                               'user_articles': user_articles,
                               'flagged': flagged, 'can_flag': can_flag,
                               'can_upvote': can_upvote, 'upvoted': upvoted,
                               'can_downvote': can_downvote, 'downvoted': downvoted,
                               'can_flag_comment': can_flag_comment,
                               'comment_flagged': comment_flagged,
                               'reply_entry_form': reply_entry_form,
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
    user_articles = get_user_articles(request.user)
    if article in user_articles:
        # This user already upvoted the article.
        return redirect(next_page)
    else:
        article.upvotes.add(request.user)
        article.save()

        # Increment karma of user who submitted article,
        #  unless this is the user who submitted.
        if request.user != article.submitter:
            increment_karma(article.submitter)

        # Update article ranking points, and redirect back to page.
        update_ranking_points()
        return redirect(next_page)


def get_user_articles(user):
    """ Gets the articles that have been upvoted by this user."""
    # DEV: I'm sure there is an equivalent one-line filtered query for this.
    articles = Article.objects.all()
    user_articles = []
    for article in articles:
        if user in article.upvotes.all():
            user_articles.append(article)
    return user_articles


def upvote_comment(request, comment_id):
    # If not upvoted, upvote and increment author's karma.
    # If upvoted, undo upvote and decrement author's karma.
    # If downvoted, undo downvote and increment author's karma.

    next_page = request.META.get('HTTP_REFERER', None) or '/'
    comment = Comment.objects.get(id=comment_id)

    upvoters = comment.upvotes.all()

    if request.user == comment.author:
        return redirect(next_page)

    if request.user not in upvoters:
        # Upvote article, and increment author's karma.
        comment.upvotes.add(request.user)
        comment.save()
        increment_karma(comment.author)

    if request.user in upvoters:
        # Undo the upvote, and decrement author's karma.
        comment.upvotes.remove(request.user)
        comment.save()
        decrement_karma(comment.author)

    if request.user in comment.downvotes.all():
        # Undo the downvote, and increment author's karma.
        comment.downvotes.remove(request.user)
        comment.save()
        increment_karma(comment.author)

    # Recalculate comment order.
    article = get_parent_article(comment)
    update_comment_ranking_points(article)

    return redirect(next_page)


def downvote_comment(request, comment_id):
    # If not downvoted, downvote and decrement author's karma.
    # If downvoted, undo downvote and increment author's karma.
    # If upvoted, undo upvote and decrement author's karma.

    next_page = request.META.get('HTTP_REFERER', None) or '/'
    comment = Comment.objects.get(id=comment_id)

    downvoters = comment.downvotes.all()

    if request.user == comment.author:
        return redirect(next_page)

    if request.user not in downvoters:
        # Downvote article, and decrement author's karma.
        comment.downvotes.add(request.user)
        comment.save()
        decrement_karma(comment.author)

    if request.user in downvoters:
        # Undo the downvote, and increment author's karma.
        comment.downvotes.remove(request.user)
        comment.save()
        increment_karma(comment.author)

    if request.user in comment.upvotes.all():
        # Undo the upvote, and decrement author's karma.
        comment.upvotes.remove(request.user)
        comment.save()
        decrement_karma(comment.author)

    # Recalculate comment order.
    article = get_parent_article(comment)
    update_comment_ranking_points(article)

    return redirect(next_page)


def flag_comment(request, article_id, comment_id):
    """Flagging a comment drops its visibility more quickly.
    Can also trigger moderators to look at the user, and consider
      taking overall action against the user.
    """
    # If not flagged, flag and decrement author's karma.
    # If flagged, undo flag and increment author's karma.
    # If upvoted, undo upvote and decrement author's karma.
    #   (Can't flag something you've upvoted.)

    next_page = request.META.get('HTTP_REFERER', None) or '/'
    comment = Comment.objects.get(id=comment_id)

    flaggers = comment.flags.all()

    if request.user == comment.author or not request.user.has_perm('ed_news.can_flag_comment'):
        return redirect(next_page)

    if request.user not in flaggers:
        # Flag article, and decrement author's karma.
        comment.flags.add(request.user)
        comment.save()
        decrement_karma(comment.author)

    if request.user in flaggers:
        # Undo the flag, and increment author's karma.
        comment.flags.remove(request.user)
        comment.save()
        increment_karma(comment.author)

    if request.user in comment.upvotes.all():
        # Undo the upvote, and decrement author's karma.
        comment.upvotes.remove(request.user)
        comment.save()
        decrement_karma(comment.author)

    # Recalculate comment order.
    update_comment_ranking_points(Article.objects.get(id=article_id))

    return redirect(next_page)


def flag_article(request, article_id):
    """Flagging an article drops its quickly.
    Can also trigger moderators to look at the submitter and the domain.
    Moderators may consider taking overall action against the user.
    Moderators may consider ignoring the domain.
    """
    # If not flagged, flag and decrement submitter's karma.
    # If flagged, undo flag and increment submitter's karma.
    # If upvoted, undo upvote and decrement submitter's karma.
    #   (Can't flag something you've upvoted.)

    next_page = request.META.get('HTTP_REFERER', None) or '/'
    article = Article.objects.get(id=article_id)

    flaggers = article.flags.all()

    if request.user == article.submitter or not request.user.has_perm('ed_news.can_flag_article'):
        return redirect(next_page)

    if request.user not in flaggers:
        # Flag article, and decrement submitter's karma.
        article.flags.add(request.user)

        # If enough flags, article disappears.
        if article.flags.count() >= FLAGS_TO_DISAPPEAR:
            article.visible = False
        article.save()

        decrement_karma(article.submitter)

    if request.user in flaggers:
        # Undo the flag, and increment submitter's karma.
        article.flags.remove(request.user)

        # If enough flags, article disappears.
        if article.flags.count() < FLAGS_TO_DISAPPEAR:
            article.visible = True
        article.save()

        increment_karma(article.submitter)

    if article in request.user.userprofile.articles.all():
        # Undo the upvote, and decrement submitter's karma.
        article.upvotes -= 1
        article.save()
        request.user.userprofile.articles.remove(article)
        decrement_karma(article.submitter)

    # Recalculate article ranking points.
    update_ranking_points()

    return redirect(next_page)


# --- Utility functions ---
def increment_karma(user):
    new_karma = user.userprofile.karma + 1
    user.userprofile.karma = new_karma
    user.userprofile.save()

    # Add user to moderators group if passed karma level.
    if new_karma > KARMA_LEVEL_MODERATORS:
        moderators = Group.objects.get(name='Moderators')
        user.groups.add(moderators)

def decrement_karma(user):
    new_karma = user.userprofile.karma - 1
    user.userprofile.karma = new_karma
    user.userprofile.save()

    # Remove user from moderators group if below karma level.
    if new_karma < KARMA_LEVEL_MODERATORS:
        moderators = Group.objects.get(name='Moderators')
        user.groups.remove(moderators)

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
        comment_points = 5*get_comment_count(article)
        # Flags affect articles proportionally.
        flag_factor = 0.8**article.flags.count()
        article.ranking_points = flag_factor*(10*article.upvotes.count() + comment_points + newness_points)
        article.save()
        #print 'rp', article, article.ranking_points
        
def update_comment_ranking_points(article):
    # Update the ranking points for an article's comments.
    comments = article.comment_set.all()
    for comment in comments:
        newness_points = get_newness_points(comment)
        voting_points = comment.upvotes.count() - comment.downvotes.count() - 3*comment.flags.count()
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


def get_comment_count(submission):
    # Trace comment threads, and report the number of overall comments.
    total_comments = 0
    total_comments += submission.comment_set.count()
    for comment in submission.comment_set.all():
        total_comments += get_comment_count(comment)
        
    return total_comments
        
def get_comment_set(submission, request, comment_set, nesting_level=0):
    # Get all comments for a submission, in a format that can be
    #  used to render all comments on a page.

    # Get first-order comments, then recursively pull all nested comments.
    comments = submission.comment_set.all().order_by('ranking_points', 'submission_time').reverse()

    for comment in comments:

        age = get_submission_age(comment)

        # Report whether this user has already upvoted the comment.
        # Determine whether user can upvote or has upvoted,
        #  can downvote or has downvoted.
        # DEV: This should be factored out, and stored as a dict.
        upvoted, can_upvote = False, False
        downvoted, can_downvote = False, False
        if request.user.is_authenticated() and request.user != comment.author:
            if request.user in comment.upvotes.all():
                upvoted = True
            else:
                can_upvote = True
            if request.user in comment.downvotes.all():
                downvoted = True
            elif request.user.has_perm('ed_news.can_downvote_comment'):
                can_downvote = True

        # Note whether user has flagged this comment.
        flagged = False
        if request.user in comment.flags.all():
            flagged = True
        can_flag = False
        if request.user.is_authenticated() and request.user != comment.author and request.user.has_perm('ed_news.can_flag_comment'):
            can_flag = True


        # Calculate margin-left, based on nesting level.
        margin_left = nesting_level * 30

        # Comments with net downvotes fade to background color.
        # Steps to fade completely.
        downvote_steps = 10
        # step_value * net downvotes, but not negative and not more than 255.
        text_color_value = min(255, (255/downvote_steps)*max(0,(comment.downvotes.count()-comment.upvotes.count())))
        text_color = "rgb(%d, %d, %d)" % (text_color_value, text_color_value, text_color_value)

        # Comments with net flags fade to background color.
        # Steps to fade completely.
        flag_steps = 3
        # step_value * flags, but not negative and not more than 255.
        text_color_value = min(255, (255/flag_steps)*max(0,(comment.flags.count()-comment.upvotes.count())))
        text_color = "rgb(%d, %d, %d)" % (text_color_value, text_color_value, text_color_value)

        # Append current comment information to comment_set.
        comment_set.append({'comment': comment, 'age': age,
                            'upvoted': upvoted, 'can_upvote': can_upvote,
                            'downvoted': downvoted, 'can_downvote': can_downvote,
                            'flagged': flagged, 'can_flag': can_flag,
                            'nesting_level': nesting_level,
                            'margin_left': margin_left,
                            'text_color': text_color,
                            })

        # Append nested comments, if there are any.
        #  Send nesting_level + 1, but when recursion finishes, 
        #  nesting level in top-level for loop should still be 0.
        if comment.comment_set.count() > 0:
            get_comment_set(comment, request, comment_set, nesting_level + 1)

    #return comment_set

def get_parent_article(comment):
    """Takes in a comment, and searches up the comment chain to find
    the parent article.
    """

    if comment.parent_article:
        parent_object = comment.parent_article
    else:
        parent_object = get_parent_article(comment.parent_comment)

    return parent_object

def is_moderator(user):
    return user.groups.filter(name='Moderators')
