# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Submission'
        db.create_table(u'ed_news_submission', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('submitter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('ranking_points', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('submission_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('visible', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'ed_news', ['Submission'])

        # Adding M2M table for field upvotes on 'Submission'
        m2m_table_name = db.shorten_name(u'ed_news_submission_upvotes')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('submission', models.ForeignKey(orm[u'ed_news.submission'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['submission_id', 'user_id'])

        # Adding M2M table for field flags on 'Submission'
        m2m_table_name = db.shorten_name(u'ed_news_submission_flags')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('submission', models.ForeignKey(orm[u'ed_news.submission'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['submission_id', 'user_id'])

        # Adding model 'Article'
        db.create_table(u'ed_news_article', (
            (u'submission_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['ed_news.Submission'], unique=True, primary_key=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
        ))
        db.send_create_signal(u'ed_news', ['Article'])

        # Adding model 'TextPost'
        db.create_table(u'ed_news_textpost', (
            (u'submission_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['ed_news.Submission'], unique=True, primary_key=True)),
            ('post_body', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'ed_news', ['TextPost'])

        # Adding model 'UserProfile'
        db.create_table(u'ed_news_userprofile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('email_public', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('karma', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('show_invisible', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'ed_news', ['UserProfile'])

        # Adding model 'Comment'
        db.create_table(u'ed_news_comment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('comment_text', self.gf('django.db.models.fields.TextField')()),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(related_name='comments', to=orm['auth.User'])),
            ('ranking_points', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('submission_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('visible', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('parent_submission', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ed_news.Submission'], null=True, blank=True)),
            ('parent_comment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ed_news.Comment'], null=True, blank=True)),
        ))
        db.send_create_signal(u'ed_news', ['Comment'])

        # Adding M2M table for field upvotes on 'Comment'
        m2m_table_name = db.shorten_name(u'ed_news_comment_upvotes')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('comment', models.ForeignKey(orm[u'ed_news.comment'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['comment_id', 'user_id'])

        # Adding M2M table for field downvotes on 'Comment'
        m2m_table_name = db.shorten_name(u'ed_news_comment_downvotes')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('comment', models.ForeignKey(orm[u'ed_news.comment'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['comment_id', 'user_id'])

        # Adding M2M table for field flags on 'Comment'
        m2m_table_name = db.shorten_name(u'ed_news_comment_flags')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('comment', models.ForeignKey(orm[u'ed_news.comment'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['comment_id', 'user_id'])


    def backwards(self, orm):
        # Deleting model 'Submission'
        db.delete_table(u'ed_news_submission')

        # Removing M2M table for field upvotes on 'Submission'
        db.delete_table(db.shorten_name(u'ed_news_submission_upvotes'))

        # Removing M2M table for field flags on 'Submission'
        db.delete_table(db.shorten_name(u'ed_news_submission_flags'))

        # Deleting model 'Article'
        db.delete_table(u'ed_news_article')

        # Deleting model 'TextPost'
        db.delete_table(u'ed_news_textpost')

        # Deleting model 'UserProfile'
        db.delete_table(u'ed_news_userprofile')

        # Deleting model 'Comment'
        db.delete_table(u'ed_news_comment')

        # Removing M2M table for field upvotes on 'Comment'
        db.delete_table(db.shorten_name(u'ed_news_comment_upvotes'))

        # Removing M2M table for field downvotes on 'Comment'
        db.delete_table(db.shorten_name(u'ed_news_comment_downvotes'))

        # Removing M2M table for field flags on 'Comment'
        db.delete_table(db.shorten_name(u'ed_news_comment_flags'))


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'ed_news.article': {
            'Meta': {'object_name': 'Article', '_ormbases': [u'ed_news.Submission']},
            u'submission_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['ed_news.Submission']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'ed_news.comment': {
            'Meta': {'object_name': 'Comment'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'comments'", 'to': u"orm['auth.User']"}),
            'comment_text': ('django.db.models.fields.TextField', [], {}),
            'downvotes': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'downvoted_comments'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'flags': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'flagged_comments'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent_comment': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ed_news.Comment']", 'null': 'True', 'blank': 'True'}),
            'parent_submission': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ed_news.Submission']", 'null': 'True', 'blank': 'True'}),
            'ranking_points': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'submission_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'upvotes': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'upvoted_comments'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'ed_news.submission': {
            'Meta': {'object_name': 'Submission'},
            'flags': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'flagged_submissions'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ranking_points': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'submission_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'submitter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'upvotes': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'upvoted_submissions'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'ed_news.textpost': {
            'Meta': {'object_name': 'TextPost', '_ormbases': [u'ed_news.Submission']},
            'post_body': ('django.db.models.fields.TextField', [], {}),
            u'submission_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['ed_news.Submission']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'ed_news.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'email_public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'karma': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'show_invisible': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['ed_news']