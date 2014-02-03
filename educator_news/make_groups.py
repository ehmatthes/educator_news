# Creates the groups that Educator News needs in order to run well.
import sys
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from ed_news.models import Comment

# Make group Moderators if it doesn't exist.
try:
    moderators = Group.objects.get(name='Moderators')
    print "Found group Moderators."
except Group.DoesNotExist:
    moderators = Group(name='Moderators')
    moderators.save()
    print "Created group Moderators."

try:
    downvote_permission = Permission.objects.get(codename='can_downvote')
except Permission.DoesNotExist:
    content_type = ContentType.objects.get_for_model(Comment)
    downvote_permission = Permission.objects.create(codename='can_downvote_comment',
                                       name='Can downvote comments',
                                       content_type=content_type)
    downvote_permission.save()

try:
    moderators.permissions.add(downvote_permission)
    print "Moderators can downvote comments."
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

