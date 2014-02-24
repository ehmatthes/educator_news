# Creates the groups that Educator News needs in order to run well.
import sys
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from ed_news.models import Comment, Submission

"""
Main groups are active_members, moderators, and admins(?)
- active_members
  - can downvote comments, flag articles
  - can also flag comments for now
- moderators
  - can act on flagged comments (later)
- admin
  - ?
"""


# Make group Moderators if it doesn't exist.
try:
    active_members = Group.objects.get(name='Active Members')
    print "Found group Active Members."
except Group.DoesNotExist:
    active_members = Group(name='Active Members')
    active_members.save()
    print "Created group Active Members."

# Permission: can_downvote_comment
try:
    downvote_comment_permission = Permission.objects.get(codename='can_downvote_comment')
except Permission.DoesNotExist:
    content_type = ContentType.objects.get_for_model(Comment)
    downvote_comment_permission = Permission.objects.create(codename='can_downvote_comment',
                                       name='Can downvote comments',
                                       content_type=content_type)
    downvote_comment_permission.save()

try:
    active_members.permissions.add(downvote_comment_permission)
    print "Active Members can downvote comments."
except:
    pass
    

# Permission: can_flag_comment
try:
    flag_comment_permission = Permission.objects.get(codename='can_flag_comment')
except Permission.DoesNotExist:
    content_type = ContentType.objects.get_for_model(Comment)
    flag_comment_permission = Permission.objects.create(codename='can_flag_comment',
                                       name='Can flag comments',
                                       content_type=content_type)
    flag_comment_permission.save()

try:
    active_members.permissions.add(flag_comment_permission)
    print "Active Members can flag comments."
except:
    pass


# Permission: can_flag_submission
try:
    flag_submission_permission = Permission.objects.get(codename='can_flag_submission')
except Permission.DoesNotExist:
    content_type = ContentType.objects.get_for_model(Submission)
    flag_submission_permission = Permission.objects.create(codename='can_flag_submission',
                                       name='Can flag submissions',
                                       content_type=content_type)
    flag_submission_permission.save()

try:
    active_members.permissions.add(flag_submission_permission)
    print "Active Members can flag submissions."
except:
    pass


for user in User.objects.all():
    if user.groups.filter(name='Moderators'):
        user.groups.add(active_members)

#print Comment.permissions.can_downvote in moderators.permissions
#ehm = User.objects.get(username='ehmatthes')
#print 'ehm can downvote:', ehm.has_perm('ed_news.can_downvote')
#eam = User.objects.get(username='erinm')
#print 'eam can downvote:', eam.has_perm('ed_news.can_downvote')
#mhe = User.objects.get(username='matthese')
#print 'matthese can downvote:', mhe.has_perm('ed_news.can_downvote')
#mhe.groups.add(moderators)
#print 'matthese can downvote:', mhe.has_perm('ed_news.can_downvote')
