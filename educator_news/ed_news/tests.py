from datetime import datetime, timedelta

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.core.management import call_command
from django.utils.timezone import utc

from ed_news.views import invalidate_cache

from django.contrib.auth.models import User, Group
from django.contrib.auth import login
from ed_news.models import UserProfile
from ed_news.views import KARMA_LEVEL_ACTIVE_MEMBERS
from ed_news.views import increment_karma, decrement_karma, is_active_member
from ed_news.views import get_parent_submission
import ed_news.views as views

from ed_news.models import Submission, Article, Comment

import random


class EdNewsViewTests(TestCase):

    def test_index_cache(self):
        return 0
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
        return 0
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


    def test_undo_upvote_submission(self):
        # Create a user, make a submission.
        # Create a user. Upvote submission.
        #  Verify user 2 in submission.upvotes.
        #  Verify user 1 karma increases.
        # Undo upvote (resubmit upvote request.)
        #  Verify user 2 not in submission.upvotes.
        #  Verify user 1 karma back to original.

        # DEV: unfinished

        # Create 2 users.
        user_0 = self.create_user_with_profile('user_0', 'user_0')
        user_1 = self.create_user_with_profile('user_1', 'user_1')
        # Log user_0 in, and make a submission.
        c = Client()
        #response = c.post('/login/', {'username': user_0.username, 'password': 'user_0'})
        #self.assertEqual(response.status_code, 200)
        login = c.login(username=user_0.username, password='user_0')
        self.assertEqual(login, True)

        response = c.post('/submit_link/', {'url': 'http://google.com', 'title': 'google'})
        self.assertEqual(response.status_code, 200)

        original_karma = user_0.userprofile.karma
        
        login = c.login(username=user_1.username, password='user_1')
        self.assertEqual(login, True)

        #print Submission.objects.all()[0].id
        return 0
        response = c.get('/upvote_submission/', {'submission_id': 5})
        self.assertEqual(response.status_code, 200)


    def test_login_client_user(self):
        # Prove that I know how to log in a user using the test client.
        c = Client()
        user = self.create_user_with_profile('user_0', 'password')
        login = c.login(username=user.username, password='password')
        self.assertEqual(login, True)


    def test_login_page(self):
        pass
        # Can't rely on status_code==200 to verify /login/ page successful.
        #  Failed login attempt still returns a proper html response.
        #response = c.post('/login/', {'username': user.username, 'password': 'password'})
        #print 'login page successful: ', response
        # Make sure all users can log in.
        num_users = 5
        for x in range(0,num_users):
            # Each user's password is their username.
            new_user = self.create_user_with_profile('user_%d' % x, 'user_%d' %x)

        c = Client()
        for user in User.objects.all():
            response = c.post('/login/', {'username': user.username, 'password': 'password'})
            self.assertEqual(response.status_code, 200)


    def test_load(self):
        # Generate a fixture for load testing.
        # Create a number of users.
        # Create a number of link submissions for each user.
        # Create a number of text posts from each user.
        # Create a number of comments on each submission.
        # Create a random number of upvotes and downvotes.

        size = 'small'
        if size == 'tiny':
            num_users = 2
            # Number of links each user submits.
            num_link_submissions = 2
            # Number of text posts each user submits.
            num_textpost_submissions = 2
            # Number of submissions each user comments on.
            num_comments = 3
            # Number of comments each user replies to.
            num_replies = 2
            # Number of items each user will vote/ flag.
            num_submission_upvotes = 2
            num_comment_upvotes = 2
            num_comment_downvotes = 1
        elif size == 'small':
            num_users = 7
            # Number of links each user submits.
            num_link_submissions = 3
            # Number of text posts each user submits.
            num_textpost_submissions = 2
            # Number of submissions each user comments on.
            num_comments = 5
            # Number of comments each user replies to.
            num_replies = 15
            # Number of items each user will vote/ flag.
            num_submission_upvotes = 3
            num_comment_upvotes = 3
            num_comment_downvotes = 1
        elif size == 'medium':
            num_users = 50
            # Number of links each user submits.
            num_link_submissions = 3
            # Number of text posts each user submits.
            num_textpost_submissions = 2
            # Number of submissions each user comments on.
            num_comments = 5
            # Number of comments each user replies to.
            num_replies = 3
            # Number of items each user will vote/ flag.
            num_submission_upvotes = 10
            num_comment_upvotes = 10
            num_comment_downvotes = 1
        elif size == 'largish':
            num_users = 100
            # Number of links each user submits.
            num_link_submissions = 10
            # Number of text posts each user submits.
            num_textpost_submissions = 2
            # Number of submissions each user comments on.
            num_comments = 25
            # Number of comments each user replies to.
            num_replies = 50
            # Number of items each user will vote/ flag.
            num_submission_upvotes = 50
            num_comment_upvotes = 50
            num_comment_downvotes = 10

        for x in range(0,num_users):
            # Each user's password is their username.
            new_user = self.create_user_with_profile('user_%d' % x, 'user_%d' %x)
        print 'num users created:', User.objects.count()

        # Create a test client.
        #  Prove that each user can be logged in, and make link submissions.
        #  DEV: should upvote own article automatically.
        c = Client()
        for user in User.objects.all():
            password = user.username
            login = c.login(username=user.username, password=password)
            self.assertEqual(login, True)
            
            for x in range(0, num_link_submissions):
                # Need many unique urls; google your username.
                url = 'http://google.com/#q=%s-%d' % (user.username, x)
                title = 'I googled my username: %s-%d' % (user.username, x)
                article = Article(title=title, url=url, submitter=user)
                article.save()

                # Make sure most recently submitted link matches current title.
                latest_submission = Submission.objects.latest('submission_time')
                self.assertEqual(latest_submission.url, url)
                self.assertEqual(latest_submission.title, title)

                # Get an artificial age, from 0 to 86400 seconds.
                age = timedelta(seconds=random.randint(0,86400))
                submission_time = datetime.utcnow() - age
                article.submission_time = submission_time
                article.save()

                print 'Made submission %d for %s.' % (x, user.username)

        # Create some comments.
        # Go through all submissions.
        #  Pick num_comments random users to make a comment.
        all_users = User.objects.all()
        for submission in Submission.objects.all():
            for comment_num in range(0, num_comments):
                user = random.choice(all_users)
                comment_text = "I just don't think you'll ever make a magnetic monopole."
                new_comment = Comment(comment_text=comment_text, author=user, parent_submission=submission)
                new_comment.save()
                print 'Made comment %d for %s.' % (comment_num, user.username)
        print '%d comments made.' % Comment.objects.count()

        # For each user, pick some random comments to reply to.
        all_comments = Comment.objects.all()
        for user in User.objects.all():
            for reply_num in range(0, num_replies):
                target_comment = random.choice(all_comments)
                reply_text = "Yeah, I was kind of thinking that."
                # A reply has the same parent_submission as the target comment.
                new_reply = Comment(comment_text=reply_text, author=user,
                                    parent_comment=target_comment,
                                    parent_submission=target_comment.parent_submission)
                new_reply.save()
                print 'Made reply %d for %s.' % (reply_num, user.username)
        print 'finished replying.'

        # For each user, upvote/downvote submissions, comments.
        #  Fine if have same user upvoting same submission; should toggle.

        # Need to make permissions before downvoting.
        #  make_groups should be a function or class that I can import and then call.
        execfile('make_groups.py')
        all_submissions = Submission.objects.all()
        all_comments = Comment.objects.all()
        for user in User.objects.all():
            for upvote_num in range(0, num_submission_upvotes):
                target_submission = random.choice(all_submissions)
                if user in target_submission.upvotes.all():
                    # User already upvoted this submission,
                    #  can't un-upvote submissions yet.
                    continue
                else:
                    target_submission.upvotes.add(user)
                    target_submission.save()

                    if user != target_submission.submitter:
                        views.increment_karma(target_submission.submitter)

                print '%s upvoted %s.' % (user.username, target_submission)

            for upvote_num in range(0, num_comment_upvotes):
                target_comment = random.choice(all_comments)
                if user == target_comment.author:
                    continue
                if user not in target_comment.upvotes.all():
                    target_comment.upvotes.add(user)
                    target_comment.save()
                    views.increment_karma(target_comment.author)
                if user in target_comment.upvotes.all():
                    target_comment.upvotes.remove(user)
                    target_comment.save()
                    views.decrement_karma(target_comment.author)
                if user in target_comment.downvotes.all():
                    # Undo the downvote, and increment author's karma.
                    target_comment.downvotes.remove(user)
                    target_comment.save()
                    views.increment_karma(target_comment.author)
                if user in target_comment.flags.all():
                    # Deal with flags.
                    pass
                parent_submission = views.get_parent_submission(target_comment)

                print '%s upvoted %s.' % (user.username, target_comment)

            continue

            for downvote_num in range(0, num_comment_downvotes):
                c.login(username=user.username, password=user.username)
                target_comment = random.choice(Comment.objects.all())
                response = c.post('/downvote_comment/%d/' % target_comment.id)
                self.assertEqual(response.status_code, 302)
                print '%s downvoted %s.' % (user.username, target_comment)

        views.update_submission_ranking_points()
        # This only needs to be run once for each submission.
        for submission in Submission.objects.all():
            views.update_comment_ranking_points(submission)
        
        # Show karma for all users.
        print "All users' karma:"
        for user in User.objects.all():
            print "%s: %d" % (user.username, user.userprofile.karma)

        # Make a fixture from this data.
        #with open('/home/ehmatthes/Desktop/test_fixture.json', 'w') as f:
        # Assumes being run from same directory as manage.py.
        with open('ed_news/fixtures/test_fixture.json', 'w') as f:
            call_command('dumpdata', stdout=f)


    def test_overall_site(self):
        # This approach is appropriate for testing user experience.
        #  Working through requests is too slow for generating large
        #  amounts of data for load testing.
        return 0
        # Create a number of users.
        # Create a number of link submissions for each user.
        # Create a number of text posts from each user.
        # Create a number of comments on each submission.
        # Create a random number of upvotes and downvotes.

        size = 'medium'
        if size == 'tiny':
            num_users = 2
            # Number of links each user submits.
            num_link_submissions = 2
            # Number of text posts each user submits.
            num_textpost_submissions = 2
            # Number of submissions each user comments on.
            num_comments = 3
            # Number of comments each user replies to.
            num_replies = 2
            # Number of items each user will vote/ flag.
            num_submission_upvotes = 2
            num_comment_upvotes = 2
            num_comment_downvotes = 1
        elif size == 'medium':
            num_users = 50
            # Number of links each user submits.
            num_link_submissions = 3
            # Number of text posts each user submits.
            num_textpost_submissions = 2
            # Number of submissions each user comments on.
            num_comments = 5
            # Number of comments each user replies to.
            num_replies = 3
            # Number of items each user will vote/ flag.
            num_submission_upvotes = 10
            num_comment_upvotes = 10
            num_comment_downvotes = 1

        for x in range(0,num_users):
            # Each user's password is their username.
            new_user = self.create_user_with_profile('user_%d' % x, 'user_%d' %x)
        print 'num users created:', User.objects.count()

        # Create a test client.
        #  Prove that each user can be log in, and make 5 link submissions.
        c = Client()
        for user in User.objects.all():
            password = user.username
            login = c.login(username=user.username, password=password)
            self.assertEqual(login, True)
            
            for x in range(0, num_link_submissions):
                # Need many unique urls; google your username.
                url = 'http://google.com/#q=%s%d' % (user.username, x)
                title = 'I googled my username: %s%d' % (user.username, x)
                response = c.post('/submit_link/', {'url': url, 'title': title})
                self.assertEqual(response.status_code, 200)
                # Make sure most recently submitted link matches current title.
                latest_submission = Submission.objects.latest('submission_time')
                self.assertEqual(latest_submission.url, url)
                self.assertEqual(latest_submission.title, title)
                print 'Made submission %d for %s.' % (x, user.username)

        # Create some comments.
        # Go through all submissions.
        #  Pick num_comments random users to make a comment.
        for submission in Submission.objects.all():
            for comment_num in range(0, num_comments):
                user = random.choice(User.objects.all())
                c.login(username=user.username, password=user.username)
                comment_text = "I just don't think you'll ever make a magnetic monopole."
                response = c.post('/discuss/%d/' % submission.id, {'comment_text': comment_text})
                self.assertEqual(response.status_code, 200)
                print 'Made comment %d for %s.' % (comment_num, user.username)
        print '%d comments made.' % Comment.objects.count()

        # For each user, pick some random comments to reply to.
        for user in User.objects.all():
            for reply_num in range(0, num_replies):
                c.login(username=user.username, password=user.username)
                target_comment = random.choice(Comment.objects.all())
                parent_submission = get_parent_submission(target_comment)
                reply_text = "Yeah, I was kind of thinking that."
                print 'parent_submission, target_comment', parent_submission.id, target_comment.id
                print Submission.objects.get(id=parent_submission.id)
                print Comment.objects.get(id=target_comment.id)
                response = c.post('/reply/%d/%d/' % (parent_submission.id, target_comment.id), {'comment_text': reply_text})
                #self.assertEqual(response.status_code, 200)
                print 'Made reply %d for %s.' % (reply_num, user.username)
        print 'finished replying.'


        # For each user, upvote/downvote submissions, comments.
        #  Fine if have same user upvoting same submission; should toggle.

        # Need to make permissions before downvoting.
        #  make_groups should be a function or class that I can import and then call.
        execfile('make_groups.py')
        for user in User.objects.all():
            for upvote_num in range(0, num_submission_upvotes):
                c.login(username=user.username, password=user.username)
                target_submission = random.choice(Submission.objects.all())
                response = c.post('/upvote_submission/%d/' % target_submission.id)
                self.assertEqual(response.status_code, 302)
                print '%s upvoted %s.' % (user.username, target_submission)

            for upvote_num in range(0, num_comment_upvotes):
                c.login(username=user.username, password=user.username)
                target_comment = random.choice(Comment.objects.all())
                response = c.post('/upvote_comment/%d/' % target_comment.id)
                self.assertEqual(response.status_code, 302)
                print '%s upvoted %s.' % (user.username, target_comment)

            for downvote_num in range(0, num_comment_downvotes):
                c.login(username=user.username, password=user.username)
                target_comment = random.choice(Comment.objects.all())
                response = c.post('/downvote_comment/%d/' % target_comment.id)
                self.assertEqual(response.status_code, 302)
                print '%s downvoted %s.' % (user.username, target_comment)


        # Show karma for all users.
        print "All users' karma:"
        for user in User.objects.all():
            print "%s: %d" % (user.username, user.userprofile.karma)



        # Make a fixture from this data.
        #with open('/home/ehmatthes/Desktop/test_fixture.json', 'w') as f:
        # Assumes being run from same directory as manage.py.
        with open('ed_news/fixtures/test_fixture.json', 'w') as f:
            call_command('dumpdata', stdout=f)


    def create_user_with_profile(self, username, password):
        # Create a new user and userprofile.
        # Either this, or new_user = User(username=un); new_user.set_password(pw)
        new_user = User.objects.create_user(username=username, password=password)
        new_user.save()
        new_user_profile = UserProfile(user=new_user)
        new_user_profile.save()
        return new_user
