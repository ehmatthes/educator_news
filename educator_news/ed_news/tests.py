from django.test import TestCase
from django.core.urlresolvers import reverse

from ed_news.views import invalidate_cache

from django.contrib.auth.models import User, Group
from ed_news.models import UserProfile
from ed_news.views import KARMA_LEVEL_ACTIVE_MEMBERS
from ed_news.views import increment_karma, decrement_karma, is_active_member

class EdNewsViewTests(TestCase):

    def test_index_cache(self):
        """Request index, then invalidate cache.
        Cache should be invalidated, returning True.
        Then try to invalidate, and should return False.
        """
        response = self.client.get(reverse('ed_news:index'))
        self.assertEqual(response.status_code, 200)

        invalidated = invalidate_cache('index', namespace='ed_news')
        self.assertEqual(invalidated, True)

        invalidated = invalidate_cache('index', namespace='ed_news')
        self.assertEqual(invalidated, False)


    # I am running into namespace issues when trying to generalize these tests.
    def test_new_cache(self):
        """Request new, then invalidate cache.
        Cache should be invalidated, returning True.
        Then try to invalidate, and should return False.
        """
        response = self.client.get(reverse('ed_news:new'))
        self.assertEqual(response.status_code, 200)

        invalidated = invalidate_cache('new', namespace='ed_news')
        self.assertEqual(invalidated, True)

        invalidated = invalidate_cache('new', namespace='ed_news')
        self.assertEqual(invalidated, False)

    def test_join_active_members(self):
        """
        If a member crosses the active_member threshold,
        they should be put in the active_member group automatically.
        """
        # Create a new user and userprofile.
        new_user = User(username='paulo', password='password')
        new_user.save()
        new_user_profile = UserProfile(user=new_user)
        new_user_profile.save()

        # Make active_members group.
        #  This should run the make_groups.py script.
        active_members = Group(name='Active Members')
        active_members.save()

        # Set karma just below critical level.
        #  Test that user is not in active_members.
        new_user_profile.karma = KARMA_LEVEL_ACTIVE_MEMBERS - 1
        self.assertEqual(is_active_member(new_user), False)

        # Increment karma past threshold, not just to threshold.
        #  Test that user is now in active_members.
        increment_karma(new_user)
        increment_karma(new_user)
        self.assertEqual(is_active_member(new_user), True)

        # Decrement karma below threshold.
        #  Test that user is no longer in active_members.
        decrement_karma(new_user)
        decrement_karma(new_user)
        self.assertEqual(is_active_member(new_user), False)
