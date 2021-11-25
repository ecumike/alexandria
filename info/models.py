import datetime
import requests

from slugify import slugify

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.db import models
from django.utils import timezone

from research.helpers import sendEmail


class FaqCategory(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	created_by = models.ForeignKey(User, related_name='faq_category_created_by', on_delete=models.PROTECT)
	updated_at = models.DateTimeField(auto_now=True)
	updated_by = models.ForeignKey(User, related_name='faq_category_updated_by', on_delete=models.PROTECT)
	
	name = models.CharField(max_length=64, unique=True)
	slug = models.SlugField(max_length=100, editable=False)
	
	class Meta:
		ordering = ['name']
		verbose_name_plural = 'FAQ categories'
		
	def __str__(self):
		return self.name

	def save(self, *args, **kwargs):
		"""
		Override save to populate the slug and keep in sync with the org name.
		"""
		self.slug = slugify(self.name)
		
		super(FaqCategory, self).save(*args, **kwargs) 


class Faq(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	created_by = models.ForeignKey(User, related_name='faq_created_by', on_delete=models.PROTECT)
	updated_at = models.DateTimeField(auto_now=True)
	updated_by = models.ForeignKey(User, related_name='faq_updated_by', on_delete=models.PROTECT)
	
	categories = models.ManyToManyField(FaqCategory, related_name='faq_categories')
	question = models.CharField(max_length=255, unique=True)
	answer = models.TextField(verbose_name='Answer (HTML allowed)')
	
	class Meta:
		ordering = ['question']
		verbose_name = 'FAQ'
		
	def __str__(self):
		return self.question


class WhatsNew(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	created_by = models.ForeignKey(User, related_name='whats_new_created_by', on_delete=models.PROTECT)
	updated_at = models.DateTimeField(auto_now=True)
	updated_by = models.ForeignKey(User, related_name='whats_new_updated_by', on_delete=models.PROTECT)
	
	date = models.DateField(default=datetime.date.today)
	heading = models.CharField(max_length=255)
	description = models.TextField(max_length=800, verbose_name='Description (HTML allowed)')
	featured = models.BooleanField(default=False)
	include_in_feed = models.BooleanField(default=True)
	notify_users = models.BooleanField(default=True, verbose_name='Notify users (only on new items)')
	emails_sent_count = models.PositiveIntegerField(default=0, blank=True, null=True)
	
	class Meta:
		ordering = ['-date', 'created_at']
		
	def __str__(self):
		return '{} : {}'.format(self.date, self.heading)

	def sendEmails(self):
		"""
		Sends an email to all users subscribed to "What's new" emails with item that was posted.
		"""
		users = list(User.objects.filter(profile__whats_new_email=True).values_list('username', flat=True))
		
		self.emails_sent_count = len(users)
		self.save()
		
		sendEmail({
			'subject': '[Omnia] A new update was just posted',
			'recipients': users,
			'message': '<div style="font-family:sans-serif;font-size:14px;line-height:20px;"><p>An update was just posted to the “What’s new” section of the Omnia web site.</p><p>{}</p><p>{}</p><br><p>To view all updates, visit the What’s new page.</p><br><p style="font-size:12px;color:#777;">You’re receiving this email because you subscribed to Omnia site What’s new email notifications. If you no longer want to receive these, unsubscribe via the checkbox at the top of the What’s new page.</p></div>'.format(self.heading, self.description)
		})
		
	def sendSlackWhatsNewNotification(self):
		"""
		Sends a notification to the set channel channel that a new "What's new" item was posted.
		"""
		slackUrl = settings.SLACK_OMNIA_NOTIFICATIONS_URL
		
		payload = {
			'username': 'UXRA news',
			'icon_emoji': ':news:',
			'text': 'A new "What\'s new" item was just posted:\n*{}*\nhttps://REPLACE_ME/info/whatsnew/'.format(self.heading),
		}
		
		if slackUrl:
			r = requests.post(slackUrl, json=payload)
	

def incrementReleaseNum():
	return ReleaseNote.objects.order_by('-release_number').first().release_number+1
	
class ReleaseNote(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	created_by = models.ForeignKey(User, related_name='release_note_created_by', on_delete=models.PROTECT)
	updated_at = models.DateTimeField(auto_now=True)
	updated_by = models.ForeignKey(User, related_name='release_note_updated_by', on_delete=models.PROTECT)
	
	release_number = models.PositiveIntegerField(default=incrementReleaseNum, unique=True)
	date = models.DateField(default=datetime.date.today)
	notes = models.TextField(max_length=1000)
	
	class Meta:
		ordering = ['-release_number']
		
	def __str__(self):
		return '{} : {}'.format(self.release_number, self.date)



