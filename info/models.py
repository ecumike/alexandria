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


def incrementReleaseNum():
	try:
		return ReleaseNote.objects.order_by('-release_number').first().release_number+1
	except:
		return 1
	
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



