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
