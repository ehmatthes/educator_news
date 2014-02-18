from django.db import models
from django.contrib.auth.models import User

# --- Educator News models ---

class Submission(models.Model):
    """A base class for the two types of submission,
    which are an article and a text submission. Text submissions
    can be questions, ie Ask EN, or posts such as Show EN.
    """

    # Stick with programming 80-char limit for now.
    #  It's what HN uses, which fits nicely on mobile.
    title = models.CharField(max_length=80)
    url = models.URLField()
    submitter = models.ForeignKey(User)
    upvotes = models.ManyToManyField(User, blank=True, null=True, related_name='upvoted_submissions')
    flags = models.ManyToManyField(User, blank=True, null=True, related_name='flagged_submissions')
    ranking_points = models.IntegerField(default=0)
    submission_time = models.DateTimeField(auto_now_add=True)

    # Will need to ignore some submissions, by making them invisible.
    #  But assume visible.
    visible = models.BooleanField(default=True)

    def __unicode__(self):
        return self.title


class Article(Submission):
    # Now that TextPosts have urls, not sure there is anything special about an article.
    pass


class TextPost(Submission):
    post_body = models.TextField()


class UserProfile(models.Model):
    # Custom user fields, not in User model.

    # Link UserProfile to a User instance.
    user = models.OneToOneField(User)
    email_public = models.BooleanField(default=False)
    karma = models.IntegerField(default=0)

    # Only moderators can choose show_all.
    show_invisible = models.BooleanField(default=False)

    # Use username to refer to user.
    def __unicode__(self):
        return self.user.username


class Comment(models.Model):
    # Allow essay-length comments.
    comment_text = models.TextField()
    author = models.ForeignKey(User, related_name='comments')
    # For these fields, need to track who's given the up/downvote, 
    #  flag. Accountability, and prevent double-voting/ flagging.
    upvotes = models.ManyToManyField(User, blank=True, null=True, related_name='upvoted_comments')
    downvotes = models.ManyToManyField(User, blank=True, null=True, related_name='downvoted_comments')
    flags = models.ManyToManyField(User, blank=True, null=True, related_name='flagged_comments')
    ranking_points = models.IntegerField(default=0)

    submission_time = models.DateTimeField(auto_now_add=True)

    # Will need to ignore some comments, by making them invisible.
    #  But assume visible.
    visible = models.BooleanField(default=True)

    # If it's a first-level reply, there is a parent submission.
    parent_submission = models.ForeignKey(Submission, blank=True, null=True)

    # If it's a reply, there is a parent comment.
    parent_comment = models.ForeignKey('self', blank=True, null=True)

    def __unicode__(self):
        return self.comment_text[:50] + '...'


# Save a textpost's url based on its id, once the id has been identified.
def create_textpost_url(sender, instance, created, **kwargs):
    if created:
        instance.url = "/discuss/%s/" % instance.id
        instance.save()

models.signals.post_save.connect(create_textpost_url, sender=TextPost, dispatch_uid='create_textpost_url')


# Any time a submission, article, textpost, or comment is saved, invalidate the cache.

def invalidate_caches(sender, instance, **kwargs):
    if sender in [Submission, Article, TextPost, Comment]:
        invalidate_cache('index', namespace='ed_news')

#models.signals.post_save.connect(invalidate_caches)

from django.core.urlresolvers import reverse
from django.utils.cache import get_cache_key
from django.core.cache import cache
from django.http import HttpRequest

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
    header_key = ''
 
    if page_key:
        # Need to clear page and header cache. Get the header key
        #  from the page key.
        # Typical page key: :1:views.decorators.cache.cache_page..GET.6666cd76f96956469e7be39d750cc7d9.d41d8cd98f00b204e9800998ecf8427e.en-us.UTC
        # Typical header key: :1:views.decorators.cache.cache_header..6666cd76f96956469e7be39d750cc7d9.en-us.UTC
        #  Change _page..GET. to _header..
        #  then lose the second hash.
        import re
        p = re.compile("(.*)_page\.\.GET\.([a-z0-9]*)\.[a-z0-9]*(.*en-us.UTC)")
        m = p.search(page_key)
        header_key = m.groups()[0] + '_header..' + m.groups()[1] + m.groups()[2]

        print '\n\nmodels.invalidate_cache'
        print 'page_key:', page_key
        print 'header_key:', header_key

       # If the page/ header have been cached, destroy them.
        if cache.get(page_key):
            # Delete the page and header caches.
            cache.delete(page_key)
            cache.delete(header_key)

            print 'invalidated cache'
            return True

    print "couldn't invalidate cache"
    return False
