# Creates the groups that Educator News needs in order to run well.
import sys
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from ed_news.models import Comment, Submission

# Make group Moderators if it doesn't exist.
try:
    moderators = Group.objects.get(name='Moderators')
    print "Found group Moderators."
except Group.DoesNotExist:
    moderators = Group(name='Moderators')
    moderators.save()
    print "Created group Moderators."

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
    moderators.permissions.add(downvote_comment_permission)
    print "Moderators can downvote comments."
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
    moderators.permissions.add(flag_comment_permission)
    print "Moderators can flag comments."
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
    moderators.permissions.add(flag_submission_permission)
    print "Moderators can flag submissions."
except:
    pass




#print Comment.permissions.can_downvote in moderators.permissions
#ehm = User.objects.get(username='ehmatthes')
#print 'ehm can downvote:', ehm.has_perm('ed_news.can_downvote')
#eam = User.objects.get(username='erinm')
#print 'eam can downvote:', eam.has_perm('ed_news.can_downvote')
#mhe = User.objects.get(username='matthese')
#print 'matthese can downvote:', mhe.has_perm('ed_news.can_downvote')
#mhe.groups.add(moderators)
#print 'matthese can downvote:', mhe.has_perm('ed_news.can_downvote')
