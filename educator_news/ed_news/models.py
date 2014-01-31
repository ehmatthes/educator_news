from django.db import models
from django.contrib.auth.models import User

# --- Educator News models ---

class Submission(models.Model):
    """An abstract class for the two types of submission,
    which are an article and a text submission. Text submissions
    can be questions, ie Ask EN, or posts such as Show EN.
    """

    # Stick with programming 80-char limit for now.
    #  It's what HN uses, which fits nicely on mobile.
    title = models.CharField(max_length=80)
    submitter = models.ForeignKey(User)
    upvotes = models.IntegerField(default=0)
    ranking_points = models.IntegerField(default=0)
    submission_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.title

class Article(Submission):
    url = models.URLField()

class UserProfile(models.Model):
    # Link UserProfile to a User instance.
    user = models.OneToOneField(User)
    email_public = models.BooleanField(default=False)
    articles = models.ManyToManyField(Article, blank=True, null=True)

    # Custom user fields, not in User model.

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

    # Will need to kill some comments.
    alive = models.BooleanField(default=True)

    # If it's a reply, there is a parent comment.
    parent_comment = models.ForeignKey('self', blank=True, null=True)

    # If it's a first-level reply, there is a parent article.
    parent_article = models.ForeignKey(Article, blank=True, null=True)

    def __unicode__(self):
        return self.comment_text[:50] + '...'
