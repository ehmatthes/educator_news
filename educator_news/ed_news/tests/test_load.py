from datetime import datetime, timedelta
import pytz

from django.test import TestCase
from django.contrib.auth.models import User
from django.test.client import Client
from django.core.management import call_command
from django.utils.timezone import utc

from django.contrib.auth.models import User, Group
from django.contrib.auth import login
from ed_news.models import UserProfile
from ed_news.views import KARMA_LEVEL_ACTIVE_MEMBERS
from ed_news.views import increment_karma, decrement_karma, is_active_member
import ed_news.views as views

from ed_news.models import Submission, Article, Comment

import random

from test_utilities import create_user_with_profile


class EdNewsTestLoad(TestCase):

    def test_load(self):
        # Generate a fixture for load testing.
        # Create a number of users.
        # Create a number of link submissions for each user.
        # Create a number of text posts from each user.
        # Create a number of comments on each submission.
        # Create a random number of upvotes and downvotes.

        size = 'small'
        if size == 'tiny':
            num_users = 3
            # Number of links each user submits.
            num_link_submissions = 2
            # Number of text posts each user submits.
            num_textpost_submissions = 2
            # Number of submissions each user comments on.
            num_comments = 3
            # Number of comments each user replies to.
            num_replies = 7
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
            new_user = create_user_with_profile('user_%d' % x, 'user_%d' %x)
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

                # Get an artificial age, from 0 to 2*86400 seconds.
                age = timedelta(seconds=random.randint(0,2*86400))
                submission_time = datetime.utcnow().replace(tzinfo=pytz.utc) - age
                article.submission_time = submission_time
                article.save()

                print 'Made submission %d for %s.' % (x, user.username)

        # Create some comments.
        # Go through all submissions.
        #  Pick num_comments random users to make a comment.
        # Make a unique identifier for every comment, for debugging comment system.
        all_users = User.objects.all()
        comment_number = 0
        for submission in Submission.objects.all():
            for comment_num in range(0, num_comments):
                user = random.choice(all_users)
                comment_text = "I just don't think you'll ever make a magnetic monopole. %d" % comment_number
                comment_number += 1
                new_comment = Comment(comment_text=comment_text, author=user, parent_submission=submission)
                new_comment.save()
                self.randomize_comment_submission_time(new_comment, submission)

        print '%d comments made.' % Comment.objects.count()

        # For each user, pick some random comments to reply to.
        all_comments = Comment.objects.all()
        for user in User.objects.all():
            # Getting comments here results in more nesting of replies,
            #  but slows down test for larger datasets.
            # Comment this line if tests are taking too long.
            all_comments = Comment.objects.all()

            for reply_num in range(0, num_replies):
                # If test running slowly, comment this line out.
                all_comments = Comment.objects.all()

                target_comment = random.choice(all_comments)
                reply_text = "Yeah, I was kind of thinking that. %d" % comment_number
                comment_number += 1
                # A reply has the same parent_submission as the target comment.
                new_reply = Comment(comment_text=reply_text, author=user,
                                    parent_comment=target_comment,
                                    parent_submission=target_comment.parent_submission)
                new_reply.save()
                self.randomize_comment_submission_time(new_reply, target_comment)

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
                parent_submission = target_comment.parent_submission

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


    def randomize_comment_submission_time(self, comment, parent):
        # Make an artificial age for this comment. Random int between 0 and age of parent.
        #  Number generated is time after parent submission time.
        # This needs to happen after initial save, otherwise submission time is auto-generated.
        parent_age = views.get_age_seconds(parent.submission_time)
        comment_interval = random.randint(0, parent_age)
        comment_age = timedelta(seconds=parent_age-comment_interval)
        comment.submission_time = datetime.utcnow().replace(tzinfo=pytz.utc) - comment_age
        comment.save()
        
