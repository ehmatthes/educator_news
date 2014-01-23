from django.db import models
from django.contrib.auth.models import User

# --- Educator News models ---

class UserProfile(models.Model):
    # Link UserProfile to a User instance.
    user = models.OneToOneField(User)

    # Custom user fields, not in User model.

    # Use username to refer to user.
    def __unicode__(self):
        return self.user.username

class Submission(models.Model):
    """An abstract class for the two types of submission,
    which are an article and a text submission. Text submissions
    can be questions, ie Ask EN, or posts such as Show EN.
    """

    # Stick with programming 80-char limit for now.
    #  It's what HN uses, which fits nicely on mobile.
    title = models.CharField(max_length=80)
    author = models.ForeignKey(User)
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    submission_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.title

class Article(Submission):
    url = models.URLField()
