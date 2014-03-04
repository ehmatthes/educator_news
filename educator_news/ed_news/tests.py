from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.core.management import call_command

from ed_news.views import invalidate_cache

from django.contrib.auth.models import User, Group
from django.contrib.auth import login
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
        new_user = self.create_user_with_profile('paulo', 'password')

        # Make active_members group.
        #  This should run the make_groups.py script.
        active_members = Group(name='Active Members')
        active_members.save()

        # Set karma just below critical level.
        #  Test that user is not in active_members.
        new_user.userprofile.karma = KARMA_LEVEL_ACTIVE_MEMBERS - 1
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



    def test_login_client_user(self):
        c = Client()
        user = self.create_user_with_profile('user_0', 'password')
        print 'user: ', user.username
        print 'password: ', user.password
        login = c.login(username=user.username, password=user.password)
        print 'login successful: ', login
        login = c.login(username=user.username, password='password')
        print 'login successful: ', login

        # Can't rely on status_code==200 to verify /login/ page successful.
        #  Failed login attempt still returns a proper html response.
        #response = c.post('/login/', {'username': user.username, 'password': 'password'})
        #print 'login page successful: ', response

    def test_overall_site(self):
        return 0
        # Create a number of users.
        # Create a number of link submissions for each user.
        # Create a number of text posts from each user.
        # Create a number of comments on each submission.

        num_users = 5
        num_link_submissions = 3
        num_textpost_submissions = 2

        for x in range(0,num_users):
            new_user = self.create_user_with_profile('user_%d' % x, 'password')#'user_%d' %x)
            #print 'new user:', new_user
        
        print 'num users created:', User.objects.count()

        # Create a test client.
        c = Client()
        response = c.get('/new/')
        print 'status code - new: ', response.status_code

        link = 'google.com'
        title = 'my submission'
        print 'new user', new_user
        login = c.login(username=new_user.username, password='password')
        print 'login successful: ', login

        response = c.post('/login/', {'username': new_user.username, 'password': 'password'})
        print 'login page response: ', response.status_code

        # Make sure all users can log in.
        for user in User.objects.all():
            response = c.post('/login/', {'username': user.username, 'password': 'password'})
            self.assertEqual(response.status_code, 200)

        return 0

        response = c.post('/submit_link/', {'url': link, 'title': title})
        print 'status code - submit: ', response.status_code

        # Submit a link from each user.
        

        with open('/home/ehmatthes/Desktop/test_fixture.json', 'w') as f:
            pass#call_command('dumpdata', stdout=f)


    def create_user_with_profile(self, username, password):
        # Create a new user and userprofile.
        new_user = User(username=username)
        new_user.set_password(password)
        new_user = User.objects.create_user(username=username, password=password)
        new_user.save()
        new_user_profile = UserProfile(user=new_user)
        new_user_profile.save()
        return new_user
