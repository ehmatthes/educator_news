from django.db import models
from django.contrib.auth.models import User

# --- Educator News models ---

class UserProfile(models.Model):
    user = models.OneToOneField(User)
