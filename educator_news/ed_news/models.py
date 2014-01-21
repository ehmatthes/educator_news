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
