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
    """ A parent class for the two types of submission,
    which are an article and a text submission. Text submissions
    can be questions, ie Ask EN, or posts such as Show EN.

    Using multi-table inheritance rather than abstract base class,
    because I want to be able to query back to a general submission,
    and then deal with the specific type.
    """

    ARTICLE = 'ART'
    TEXT = 'TXT'
    SUBMISSION_TYPE_CHOICES = (
        (ARTICLE, 'Article'),
        (TEXT, 'Text'),
        )

    # Stick with programming 80-char limit for now.
    #  It's what HN uses, which fits nicely on mobile.
    title = models.CharField(max_length=80)
    author = models.OneToOneField(UserProfile)
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    submission_time = models.DateTimeField(auto_now_add=True)
    submission_type = models.CharField(max_length=3,
                                       choices=SUBMISSION_TYPE_CHOICES,
                                       default=ARTICLE)

class Article(Submission):
    url = URLField()

    Using multi-table inheritance rather than abstract base class,
    because I want to be able to query back to a general submission,
    and then deal with the specific type.
    """

    ARTICLE = 'ART'
    TEXT = 'TXT'
    SUBMISSION_TYPE_CHOICES = (
        (ARTICLE, 'Article'),
        (TEXT, 'Text'),
        )

    # Stick with programming 80-char limit for now.
    #  It's what HN uses, which fits nicely on mobile.
    title = models.CharField(max_length=80)
    author = models.OneToOneField(UserProfile)
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    submission_time = models.DateTimeField(auto_now_add=True)
    submission_type = models.CharField(max_length=3,
                                       choices=SUBMISSION_TYPE_CHOICES,
                                       default=ARTICLE)

class Article(Submission):
    url = URLField()

    Using multi-table inheritance rather than abstract base class,
    because I want to be able to query back to a general submission,
    and then deal with the specific type.
    """

    ARTICLE = 'ART'
    TEXT = 'TXT'
    SUBMISSION_TYPE_CHOICES = (
        (ARTICLE, 'Article'),
        (TEXT, 'Text'),
        )

    # Stick with programming 80-char limit for now.
    #  It's what HN uses, which fits nicely on mobile.
    title = models.CharField(max_length=80)
    author = models.OneToOneField(UserProfile)
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    submission_time = models.DateTimeField(auto_now_add=True)
    submission_type = models.CharField(max_length=3,
                                       choices=SUBMISSION_TYPE_CHOICES,
                                       default=ARTICLE)

class Article(Submission):
    url = URLField()
