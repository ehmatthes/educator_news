# A library of utility functions for testing.
from django.contrib.auth.models import User
from ed_news.models import UserProfile

def create_user_with_profile(username, password):
    # Create a new user and userprofile.
    # Either this, or new_user = User(username=un); new_user.set_password(pw)
    new_user = User.objects.create_user(username=username, password=password)
    new_user.save()
    new_user_profile = UserProfile(user=new_user)
    new_user_profile.save()
    return new_user
