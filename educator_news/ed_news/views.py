from datetime import datetime

from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.contrib.auth.views import password_change
from django.contrib.auth.models import User, Group
from django.utils.timezone import utc
from django.views.decorators.cache import cache_page, patch_cache_control
from django.utils.cache import get_cache_key
from django.core.cache import cache
from django.http import HttpRequest

from ed_news.forms import UserForm, UserProfileForm
from ed_news.forms import EditUserForm, EditUserProfileForm
from ed_news.forms import ArticleForm, TextPostForm, CommentEntryForm

from ed_news.models import Submission, Article, TextPost, Comment


# These should be moved to a settings, config, or .env file.
# Active members level will start at 10, increase as site becomes more active.
#  Should have low level if debug = True?
KARMA_LEVEL_ACTIVE_MEMBERS = 10
#  Continue to follow HN example, which is 30 articles per screen.
MAX_SUBMISSIONS = 30
# Number of flags it takes to make an article disappear.
#  Or maybe one flag from a super-mod?
FLAGS_TO_DISAPPEAR = 1
# How long does a user have to edit a comment?
COMMENT_EDIT_WINDOW = 60*10

@cache_page(60 * 10)
def index(request):
    # Get a list of submissions, sorted by date.

    if request.user.is_authenticated() and request.user.userprofile.show_invisible:
        submissions = Submission.objects.all().order_by('ranking_points', 'submission_time').reverse()[:MAX_SUBMISSIONS].prefetch_related('flags', 'upvotes', 'comment_set')
    else:
        submissions = Submission.objects.filter(visible=True).order_by('ranking_points', 'submission_time').reverse()[:MAX_SUBMISSIONS].prefetch_related('flags', 'upvotes', 'comment_set')
        
    submission_set = get_submission_set(submissions, request.user)

    response = render_to_response('ed_news/index.html',
                              {'submission_set': submission_set,
                               },
                              context_instance = RequestContext(request))
    patch_cache_control(response, no_cache=True, no_store=True, must_revalidate=True, max_age=600)
    return response


def get_submission_set(submissions, user):
    """From a set of submissions, builds a list of submission_dicts for a template.
    """
    # Note which submissions should not get upvotes.
    # Build a list of submissions, and their ages.
    submission_set = []
    for submission in submissions:
        submission_age = get_submission_age(submission)
        comment_count = get_comment_count(submission)
        
        flagged = False
        if user in submission.flags.all():
            flagged = True

        can_flag = False
        if user.is_authenticated() and user != submission.submitter and user.has_perm('ed_news.can_flag_submission'):
            can_flag = True

        upvoted = False
        if user in submission.upvotes.all():
            upvoted = True

        submission_set.append({'submission': submission, 'age': submission_age,
                                'comment_count': comment_count,
                                'flagged': flagged, 'can_flag': can_flag,
                                'upvoted': upvoted,
                                })

    return submission_set


# --- Mostly-static page views ---
def about(request):
    return render_to_response('ed_news/about.html',
                              {},
                              context_instance = RequestContext(request))


def guidelines(request):
    return render_to_response('ed_news/guidelines.html',
                              {},
                              context_instance = RequestContext(request))



# --- Authentication views ---
def logout_view(request):
    logout(request)

    # Invalidate caches: index, new
    #  Probably better to start caching just the stable parts of pages.
    invalidate_caches('ed_news', 'index', 'new')

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

    # If user is active_member, they can choose to set show_invisible = True.
    allow_show_invisible = False
    if is_active_member(user):
        allow_show_invisible = True

    if request.method == 'POST':
        edit_user_form = EditUserForm(data=request.POST, instance=request.user)
        # if user is active member, let them set show_invisible
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
        return password_change(request, post_change_redirect='password_change_successful')
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
def submit_link(request):
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
                    return redirect('ed_news:submit_link')
            article = article_form.save(commit=False)
            article.submitter = request.user
            article.save()
            submission_accepted = True
            # Upvote this article.
            upvote_submission(request, article.id)
            # Invalidate caches: index, 
            invalidate_caches('ed_news', 'index', 'new')
        else:
            # Invalid form/s.
            #  Print errors to console; should log these?
            print 'ae', article_form.errors

    else:
        # Send blank forms.
        article_form = ArticleForm()

    return render_to_response('ed_news/submit_link.html',
                              {'article_form': article_form,
                               'submission_accepted': submission_accepted,
                               },
                              context_instance = RequestContext(request))


def submit_textpost(request):
    """Page to allow users to submit a new article.
    """

    submission_accepted = False
    if request.method == 'POST':
        textpost_form = TextPostForm(data=request.POST)

        if textpost_form.is_valid():
            textpost = textpost_form.save(commit=False)
            textpost.submitter = request.user

            # The url needs the id, so it is saved on a post_save signal.
            textpost.url = ''
            textpost.save()

            submission_accepted = True
            # Upvote this submission.
            upvote_submission(request, textpost.id)
            # Invalidate caches: index, 
            invalidate_caches('ed_news', 'index', 'new')

        else:
            # Invalid form/s.
            #  Print errors to console; should log these?
            print 'ae', textpost_form.errors

    else:
        # Send blank forms.
        textpost_form = TextPostForm()

    return render_to_response('ed_news/submit_textpost.html',
                              {'textpost_form': textpost_form,
                               'submission_accepted': submission_accepted,
                               },
                              context_instance = RequestContext(request))


@cache_page(60 * 10)
def new(request):
    """Page to show the newest submissions.
    """

    # Get a list of submissions, sorted by date.
    #  This is where MTI inheritance might be better; query all submissions,
    #  rather than building a list of submissions from separate articles
    #  and posts.

    if request.user.is_authenticated() and request.user.userprofile.show_invisible:
        submissions = Submission.objects.all().order_by('submission_time').reverse()[:MAX_SUBMISSIONS].prefetch_related('flags', 'upvotes', 'comment_set')
    else:
        submissions = Submission.objects.filter(visible=True).order_by('submission_time').reverse()[:MAX_SUBMISSIONS].prefetch_related('flags', 'upvotes', 'comment_set')

    submission_set = get_submission_set(submissions, request.user)

    response = render_to_response('ed_news/new.html',
                              {'submission_set': submission_set,
                               },
                              context_instance = RequestContext(request))
    patch_cache_control(response, no_cache=True, no_store=True, must_revalidate=True, max_age=600)
    return response


@cache_page(60 * 10)
def discuss(request, submission_id, admin=False):
    submission = Submission.objects.get(id=submission_id)
    age = get_submission_age(submission)
    
    if request.method == 'POST':
        # Redirect unauthenticated users to register/ login.
        if not request.user.is_authenticated():
            return redirect('login')

        comment_entry_form = CommentEntryForm(data=request.POST)

        if comment_entry_form.is_valid():
            comment = comment_entry_form.save(commit=False)
            comment.author = request.user
            comment.parent_submission = submission
            comment.save()
            update_comment_ranking_points(submission)
            update_submission_ranking_points()
            # Invalidate caches: index, 
            invalidate_caches('ed_news', 'index', 'new')
            invalidate_cache('discuss', (submission_id, ), namespace='ed_news')
        else:
            # Invalid form/s.
            #  Print errors to console; should log these?
            print 'ce', comment_entry_form.errors

    # Prepare a blank entry form.
    comment_entry_form = CommentEntryForm()

    # Get comment information after processing form, to include comment
    #  that was just saved.
    comment_count = get_comment_count(submission)

    #  Check if submission is flagged by this user.
    flagged = False
    can_flag = False
    if request.user.is_authenticated():
        if request.user in submission.flags.all() and request.user != submission.submitter:
            flagged = True

        if request.user != submission.submitter and request.user.has_perm('ed_news.can_flag_submission'):
            can_flag = True

    comment_set = []
    get_comment_set(submission, request, comment_set)

    saved_submission = False
    if request.user in submission.upvotes.all():
        saved_submission = True

    # Check if this is a textpost that can be edited.
    textpost_can_edit = False
    try:
        textpost_can_edit = can_edit_textpost(submission.textpost, request)
    except Exception, err:
        pass

    response = render_to_response('ed_news/discuss.html',
                              {'submission': submission, 'age': age,
                               'comment_count': comment_count,
                               'saved_submission': saved_submission,
                               'flagged': flagged, 'can_flag': can_flag,
                               'comment_entry_form': comment_entry_form,
                               'comment_set': comment_set,
                               'textpost_can_edit': textpost_can_edit,
                               },
                              context_instance = RequestContext(request))
    patch_cache_control(response, no_cache=True, no_store=True, must_revalidate=True, max_age=600)
    return response


def reply(request, submission_id, comment_id):
    submission = Submission.objects.get(id=submission_id)

    comment = Comment.objects.get(id=comment_id)
    comment_age = get_submission_age(comment)

    parent_submission = get_parent_submission(comment)
    parent_comment = comment.parent_comment
    
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
            #  a submission at the same time, to be fair.
            update_comment_ranking_points(submission)
            update_submission_ranking_points()

            # Invalidate caches: index, 
            invalidate_caches('ed_news', 'index', 'new')
            invalidate_cache('discuss', (submission_id, ), namespace='ed_news')

            # Redirect to discussion page.
            return redirect('/discuss/%s/' % submission.id)

        else:
            # Invalid form/s.
            #  Print errors to console; should log these?
            print 'ce', reply_entry_form.errors

    # Prepare a blank entry form.
    reply_entry_form = CommentEntryForm()

    # Get comment information after processing form, to include comment
    #  that was just saved.
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
                              {'submission': submission,
                               'comment': comment, 'comment_age': comment_age,
                               'parent_comment': parent_comment,
                               'parent_submission': parent_submission,
                               'can_upvote': can_upvote, 'upvoted': upvoted,
                               'can_downvote': can_downvote, 'downvoted': downvoted,
                               'can_flag_comment': can_flag_comment,
                               'comment_flagged': comment_flagged,
                               'reply_entry_form': reply_entry_form,
                               },
                              context_instance = RequestContext(request))


def edit_comment(request, comment_id):
    comment = Comment.objects.get(id=comment_id)
    comment_age = get_submission_age(comment)

    parent_submission = get_parent_submission(comment)
    parent_comment = comment.parent_comment
    
    # Redirect unauthenticated users to register/ login.
    if not request.user.is_authenticated():
        return redirect('login')

    if request.method == 'POST':

        edit_comment_form = CommentEntryForm(data=request.POST, instance=comment)

        if edit_comment_form.is_valid():
            # Make sure user can still edit, 
            #  and window has not passed since form displayed.
            if not can_edit_comment(comment, request):
                return redirect('/discuss/%s/' % parent_submission.id)

            # Really just need to save the new comment text.
            edited_comment = edit_comment_form.save(commit=False)
            comment.comment_text = edited_comment.comment_text
            comment.save()

            # Invalidate caches: This only affects the discussion page for the parent submission. 
            invalidate_cache('discuss', (parent_submission.id, ), namespace='ed_news')

            # Redirect to discussion page.
            return redirect('/discuss/%s/' % parent_submission.id)

        else:
            # Invalid form/s.
            #  Print errors to console; should log these?
            print 'ce', edit_comment_form.errors

    # Prepare a blank entry form.
    edit_comment_form = CommentEntryForm(instance=comment)

    return render_to_response('ed_news/edit_comment.html',
                              {'comment': comment, 'comment_age': comment_age,
                               'parent_comment': parent_comment,
                               'parent_submission': parent_submission,
                               'edit_comment_form': edit_comment_form,
                               },
                              context_instance = RequestContext(request))


def edit_textpost(request, textpost_id):
    """Page to allow users to edit a textpost.
    """

    textpost = TextPost.objects.get(id=textpost_id)
    textpost_age = get_submission_age(textpost)

    # Redirect unauthenticated users to register/ login.
    if not request.user.is_authenticated():
        return redirect('login')

    if request.method == 'POST':

        edit_textpost_form = TextPostForm(data=request.POST, instance=textpost)

        if edit_textpost_form.is_valid():
            # Make sure user can still edit,
            #  and window has not passed since form displayed.
            if not can_edit_textpost(textpost, request):
                return redirect('/discuss/%s/' % textpost.id)

            edited_textpost = edit_textpost_form.save(commit=False)
            textpost.post_body = edited_textpost.post_body
            textpost.title = edited_textpost.title
            textpost.save()

            # Invalidate caches: This affects the discussion page for the textpost.
            #  If title changed, also affects /index and /new caches.
            invalidate_caches('ed_news', 'index', 'new')
            invalidate_cache('discuss', (textpost.id, ), namespace='ed_news')

            # Redirect to discussion page.
            return redirect('/discuss/%s/' % textpost.id)

        else:
            # Invalid form/s.
            #  Print errors to console; should log these?
            print 'ae', edit_textpost_form.errors

    else:
        # Send blank forms.
        edit_textpost_form = TextPostForm(instance=textpost)

    return render_to_response('ed_news/edit_textpost.html',
                              {'edit_textpost_form': edit_textpost_form,
                               'textpost_id': textpost.id,
                               },
                              context_instance = RequestContext(request))



def discuss_admin(request, article_id):
    if request.user == User.objects.get(username='ehmatthes'):
        response = discuss(request, article_id, True)
        return response
    else:
        return redirect('/discuss/%s/' % article_id)

def upvote_submission(request, submission_id):
    # Check if user has upvoted this submission.
    #  If not, increment submission points.
    #  Save submission for this user.
    next_page = request.META.get('HTTP_REFERER', None) or '/'
    submission = Submission.objects.get(id=submission_id)
    if request.user in submission.upvotes.all():
        # This user already upvoted the submission.
        return redirect(next_page)
    else:
        submission.upvotes.add(request.user)
        submission.save()

        # Increment karma of user who submitted submission,
        #  unless this is the user who submitted.
        if request.user != submission.submitter:
            increment_karma(submission.submitter)

        # Update submission ranking points, and redirect back to page.
        update_submission_ranking_points()
        # Invalidate caches: index, 
        invalidate_caches('ed_news', 'index', 'new')
        invalidate_cache('discuss', (submission_id, ), namespace='ed_news')
        return redirect(next_page)


def get_saved_submissions(user):
    """ Gets the submissions that have been upvoted by this user."""
    # DEV: I'm sure there is an equivalent one-line filtered query for this.
    submissions = Submission.objects.all()
    saved_submissions = []
    for submission in submissions:
        if user in submission.upvotes.all():
            saved_submissions.append(submission)
    return saved_submissions


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

    if request.user in comment.flags.all():
        # Undo the flag, and increment author's karma.
        comment.flags.remove(request.user)
        comment.save()
        increment_karma(comment.author)

    # Recalculate comment order.
    submission = get_parent_submission(comment)
    update_comment_ranking_points(submission)

    # Invalidate caches: index, 
    invalidate_caches('ed_news', 'index', 'new')
    invalidate_cache('discuss', (str(submission.id), ), namespace='ed_news')

    return redirect(next_page)


def downvote_comment(request, comment_id):
    # If not downvoted, downvote and decrement author's karma.
    # If downvoted, undo downvote and increment author's karma.
    # If upvoted, undo upvote and decrement author's karma.

    next_page = request.META.get('HTTP_REFERER', None) or '/'
    comment = Comment.objects.get(id=comment_id)

    downvoters = comment.downvotes.all()

    # Can't downvote and flag a comment.
    if request.user == comment.author or request.user in comment.flags.all():
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
    submission = get_parent_submission(comment)
    update_comment_ranking_points(submission)

    # Invalidate caches: index, 
    invalidate_caches('ed_news', 'index', 'new')
    invalidate_cache('discuss', (str(submission.id), ), namespace='ed_news')

    return redirect(next_page)


def flag_comment(request, submission_id, comment_id):
    """Flagging a comment drops its visibility more quickly.
    Can also trigger moderators to look at the user, and consider
      taking overall action against the user.
    """
    # If not flagged, flag and decrement author's karma.
    # If flagged, undo flag and increment author's karma.
    # If upvoted, undo upvote and decrement author's karma.
    # If downvoted, undo upvote and increment author's karma.
    #  No need to downvote and flag.
    #   (Can't flag something you've upvoted.)

    next_page = request.META.get('HTTP_REFERER', None) or '/'
    comment = Comment.objects.get(id=comment_id)

    flaggers = comment.flags.all()

    if request.user == comment.author or not request.user.has_perm('ed_news.can_flag_comment'):
        return redirect(next_page)

    if request.user not in flaggers:
        # Flag comment, and decrement author's karma.
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

    if request.user in comment.downvotes.all():
        # Undo the downvote, and increment author's karma.
        comment.downvotes.remove(request.user)
        comment.save()
        increment_karma(comment.author)

    # Recalculate comment order.
    update_comment_ranking_points(Submission.objects.get(id=submission_id))

    # Invalidate caches: index, 
    invalidate_caches('ed_news', 'index', 'new')
    invalidate_cache('discuss', (submission_id, ), namespace='ed_news')

    return redirect(next_page)


def flag_submission(request, submission_id):
    """Flagging a submission drops its quickly.
    Can also trigger moderators to look at the submitter and the domain.
    Moderators may consider taking overall action against the user.
    Moderators may consider ignoring the domain.
    """
    # If not flagged, flag and decrement submitter's karma.
    # If flagged, undo flag and increment submitter's karma.
    # If upvoted, undo upvote and decrement submitter's karma.
    #   (Can't flag something you've upvoted.)

    next_page = request.META.get('HTTP_REFERER', None) or '/'
    submission = Submission.objects.get(id=submission_id)

    flaggers = submission.flags.all()

    if request.user == submission.submitter or not request.user.has_perm('ed_news.can_flag_submission'):
        return redirect(next_page)

    if request.user not in flaggers:
        # Flag submission, and decrement submitter's karma.
        submission.flags.add(request.user)

        # If enough flags, submission disappears.
        if submission.flags.count() >= FLAGS_TO_DISAPPEAR:
            submission.visible = False
        submission.save()

        decrement_karma(submission.submitter)

    if request.user in flaggers:
        # Undo the flag, and increment submitter's karma.
        submission.flags.remove(request.user)

        # If enough flags, submission reappears.
        if submission.flags.count() < FLAGS_TO_DISAPPEAR:
            submission.visible = True
        submission.save()

        increment_karma(submission.submitter)

    if request.user in submission.upvotes.all():
        # Undo the upvote, and decrement submitter's karma.
        submission.upvotes.remove(request.user)
        submission.save()
        decrement_karma(submission.submitter)

    # Recalculate submission ranking points.
    update_submission_ranking_points()

    # Invalidate caches: index, 
    invalidate_caches('ed_news', 'index', 'new')
    invalidate_cache('discuss', (submission_id, ), namespace='ed_news')

    return redirect(next_page)


# --- Utility functions ---
def increment_karma(user):
    new_karma = user.userprofile.karma + 1
    user.userprofile.karma = new_karma
    user.userprofile.save()

    # Add user to active_members group if passed karma level.
    if new_karma > KARMA_LEVEL_ACTIVE_MEMBERS:
        active_members = Group.objects.get(name='Active Members')
        user.groups.add(active_members)

def decrement_karma(user):
    new_karma = user.userprofile.karma - 1
    user.userprofile.karma = new_karma
    user.userprofile.save()

    # Remove user from active_members group if below karma level.
    if new_karma < KARMA_LEVEL_ACTIVE_MEMBERS:
        active_members  = Group.objects.get(name='Active Members')
        user.groups.remove(active_members)

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

def update_submission_ranking_points():
    # How many submissions really need this?
    #  Only submissions submitted over last x days?
    submissions = Submission.objects.all()
    for submission in submissions:
        newness_points = get_newness_points(submission)
        comment_points = 5*get_comment_count(submission)
        # Flags affect submissions proportionally.
        flag_factor = 0.8**submission.flags.count()
        submission.ranking_points = flag_factor*(10*submission.upvotes.count() + comment_points + newness_points)
        submission.save()
        #print 'rp', submission, submission.ranking_points

        
def update_comment_ranking_points(article):
    # Update the ranking points for an article's comments.
    comments = article.comment_set.all().prefetch_related('upvotes', 'downvotes', 'flags')
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
    # DEV: Should call get_age_seconds()
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
    comments = submission.comment_set.all().order_by('ranking_points', 'submission_time').reverse().prefetch_related('upvotes', 'downvotes', 'flags', 'comment_set', 'author')

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
        can_edit = can_edit_comment(comment, request)

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
                            'can_edit': can_edit,
                            })

        # Append nested comments, if there are any.
        #  Send nesting_level + 1, but when recursion finishes, 
        #  nesting level in top-level for loop should still be 0.
        if comment.comment_set.count() > 0:
            get_comment_set(comment, request, comment_set, nesting_level + 1)


def can_edit_comment(comment, request):
    # Find out if this comment can be edited.
    #  User needs to be author, and comment needs to be less than 
    #   COMMENT_EDIT_WINDOW seconds old.
    user_is_author = (request.user == comment.author)
    recent_comment = (get_age_seconds(comment.submission_time) < COMMENT_EDIT_WINDOW)

    if user_is_author and recent_comment:
        return True
    else:
        return False


def can_edit_textpost(textpost, request):
    # Find out if this textpost can be edited.
    #  User needs to be author, and textpost needs to be less than 
    #   COMMENT_EDIT_WINDOW seconds old.
    user_is_author = (request.user == textpost.submitter)
    recent_textpost = (get_age_seconds(textpost.submission_time) < COMMENT_EDIT_WINDOW)
    print user_is_author, recent_textpost
    if user_is_author and recent_textpost:
        return True
    else:
        return False


def get_age_seconds(timestamp_in):
    age = (datetime.utcnow().replace(tzinfo=utc) - timestamp_in).seconds
    return age

def get_parent_submission(comment):
    """Takes in a comment, and searches up the comment chain to find
    the parent submission.
    """

    if comment.parent_submission:
        parent_object = comment.parent_submission
    else:
        parent_object = get_parent_submission(comment.parent_comment)

    return parent_object


def is_active_member(user):
    if user.groups.filter(name='Active Members'):
        return True
    else:
        return False


def invalidate_caches(namespace=None, *pages):
    for page in pages:
        invalidate_cache(page, namespace=namespace)

def invalidate_cache(view_path, args=[], namespace=None, key_prefix=None):
    """Function to allow invalidating a view-level cache.
    Adapted from: http://stackoverflow.com/questions/2268417/expire-a-view-cache-in-django
    """
    # Usage: invalidate_cache('index', namespace='ed_news', key_prefix=':1:')

    # Create a fake request.
    request = HttpRequest()
    # Get the request path.
    if namespace:
        view_path = namespace + ":" + view_path

    request.path = reverse(view_path, args=args)
    #print 'request:', request

    # Get cache key, expire if the cached item exists.
    # Using the key_prefix did not work on first testing.
    #key = get_cache_key(request, key_prefix=key_prefix)
    page_key = get_cache_key(request)

    if page_key:
        #print '\n\nviews.invalidate_cache'
        #print 'page_key:', page_key
    
        # If the page has been cached, destroy them.
        if cache.get(page_key):
            # Delete the page cache.
            cache.delete(page_key)

            #print 'invalidated cache'
            return True

    #print "couldn't invalidate cache"
    return False
