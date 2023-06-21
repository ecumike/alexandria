import requests

from datetime import datetime
from slugify import slugify

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Count, Value, Q, F, JSONField
from django.db.models.functions import Lower
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

import cos as cos
from .helpers import *
from metrics.models import Project


class Method(models.Model):
	'''
	Research methods
	'''
	created_by = models.ForeignKey(User, related_name='method_created_by', on_delete=models.PROTECT)
	created_at = models.DateTimeField(auto_now_add=True, editable=False)
	updated_by = models.ForeignKey(User, related_name='method_updated_by', on_delete=models.PROTECT)
	updated_at = models.DateTimeField(auto_now=True)
	
	uxid = models.PositiveIntegerField(default=0)
	name = models.CharField(max_length=64, unique=True)

	class Meta:
		ordering = ['name']
		
	def __str__(self):
		return self.name


class Source(models.Model):
	'''
	Research sources
	EX: By NNG, by 3rd party
	'''
	created_by = models.ForeignKey(User, related_name='source_created_by', on_delete=models.PROTECT)
	created_at = models.DateTimeField(auto_now_add=True, editable=False)
	updated_by = models.ForeignKey(User, related_name='source_updated_by', on_delete=models.PROTECT)
	updated_at = models.DateTimeField(auto_now=True)
	
	uxid = models.PositiveIntegerField(null=True, blank=True)
	name = models.CharField(max_length=64, unique=True)

	class Meta:
		ordering = ['name']
		
	def __str__(self):
		return self.name


class Status(models.Model):
	'''
	Ex: In progress, completed
	'''
	created_by = models.ForeignKey(User, related_name='status_created_by', on_delete=models.PROTECT)
	created_at = models.DateTimeField(auto_now_add=True, editable=False)
	updated_by = models.ForeignKey(User, related_name='status_updated_by', on_delete=models.PROTECT)
	updated_at = models.DateTimeField(auto_now=True)
	
	uxid = models.PositiveIntegerField(null=True, blank=True)
	name = models.CharField(max_length=64, unique=True)
	color_class = models.CharField(max_length=32, default='bg-black')
	text_color_class = models.CharField(max_length=32, default='white')

	class Meta:
		ordering = ['name']
		verbose_name_plural = 'Statuses'
		
	def __str__(self):
		return self.name


class Tag(models.Model):
	created_by = models.ForeignKey(User, related_name='tag_created_by', on_delete=models.PROTECT)
	created_at = models.DateTimeField(auto_now_add=True, editable=False)
	updated_by = models.ForeignKey(User, related_name='tag_updated_by', on_delete=models.PROTECT)
	updated_at = models.DateTimeField(auto_now=True)
	
	uxid = models.PositiveIntegerField(null=True, blank=True)
	name = models.CharField(max_length=64, unique=True)

	class Meta:
		ordering = ['name']
		
	def __str__(self):
		return self.name


class Attachment(models.Model):
	'''
	File name pointer for COS file so we can make relationships and control via research items.
	'''
	created_by = models.ForeignKey(User, related_name='attachment_created_by', on_delete=models.PROTECT)
	created_at = models.DateTimeField(auto_now_add=True, editable=False)
	updated_by = models.ForeignKey(User, related_name='attachment_updated_by', on_delete=models.PROTECT)
	updated_at = models.DateTimeField(auto_now=True, editable=False)
	
	name = models.CharField(max_length=255, unique=True)

	class Meta:
		ordering = ['name']

	def __str__(self):
		return self.name
		
		
	def storeFile(user, file):
		try:
			timestamp = int(timezone.now().timestamp())
			cosFileName = f'{timestamp}/{file.name.replace("&", "and").replace("+", "_")}'
			
			localPath = file.temporary_file_path()
			cos.uploadFile(localPath, cosFileName)
		
			attachment = Attachment.objects.create(
				name = cosFileName,
				created_by = user,
				updated_by = user
			)
			return attachment
					
		except Exception as ex:
			print(ex)
			return None


	def deleteFile(self):
		try:
			fileName = self.name
			cos.deleteFile(fileName)
			self.delete
			return True
		except Exception as ex:
			return False


	def getFile(self):
		try:
			return cos.getFile(self.name)
		except Exception as ex:
			return None


	def getFileName(self):
		return self.name.split('/')[1]
		
		
class Artifact(models.Model):
	'''
	Research item
	'''
	created_by = models.ForeignKey(User, related_name='artifact_created_by', on_delete=models.PROTECT)
	created_at = models.DateTimeField(auto_now_add=True, editable=False)
	updated_by = models.ForeignKey(User, related_name='artifact_updated_by', on_delete=models.PROTECT)
	updated_at = models.DateTimeField(auto_now=True, editable=False)
	
	uxid = models.PositiveIntegerField(null=True, blank=True)
	owner = models.ForeignKey(User, related_name='artifact_owner', on_delete=models.PROTECT)
	editors = models.ManyToManyField(User, related_name='artifact_editors', verbose_name='Additional editors', blank=True)
	
	name = models.CharField(db_index=True, max_length=255, unique=True, help_text='Keep it clear, concise, and easy to read.')
	abstract = models.TextField(db_index=True, max_length=255, verbose_name='Short description', help_text='A summary of the research. This is displayed on the search list page.')
	description = models.TextField(db_index=True, verbose_name='Full description', help_text='A detailed description of the research')
	hypothesis = models.TextField(db_index=True, blank=True, null=True, help_text='What you expected would happen as a result of this research')
	target_audience = models.CharField(db_index=True, max_length=255, verbose_name='User group(s)', blank=True, null=True, help_text='Description of the users of the tool, app, or user experience for which the research was conducted. For example, personas affected.')
	
	findings = JSONField(default=list, blank=True, null=True)
	
	test_start_date = models.DateField(blank=True, null=True)
	test_end_date = models.DateField(blank=True, null=True)
	research_date = models.DateField(blank=True, null=True, help_text='The date of the completed or posted research')
	sort_date = models.DateField(blank=True, null=True)
	
	study_plan_urls = ArrayField(models.URLField(max_length=255, blank=True), blank=True, null=True, verbose_name='Study plan URL(s)', help_text='Links to any study plans pertaining to this research')
	final_report_urls = ArrayField(models.URLField(max_length=255, blank=True), blank=True, null=True, verbose_name='Final report URL(s)', help_text='Link(s) to the actual research report(s)')
	
	external_research_urls = ArrayField(models.URLField(max_length=255, blank=True), blank=True, null=True, verbose_name='External research/third party URL(s)', help_text='Link(s) to the external research')
	study_plan_files = models.ManyToManyField(Attachment, related_name='artifact_study_plan_files', blank=True)
	final_report_files = models.ManyToManyField(Attachment, related_name='artifact_final_report_files', blank=True)
	
	# Taxonomy/tagging.
	projects = models.ManyToManyField(Project, related_name='artifact_projects', blank=True)
	related_artifacts = models.ManyToManyField('self', related_name='artifact_related_artifacts', verbose_name='Related research', blank=True, help_text='Other research items related to this one')
	methods = models.ManyToManyField(Method, related_name='artifact_methods', blank=True)
	source = models.ForeignKey(Source, related_name='artifact_source', null=True, on_delete=models.PROTECT)
	status = models.ForeignKey(Status, related_name='artifact_status', null=True, on_delete=models.PROTECT)
	tags = models.ManyToManyField(Tag, related_name='artifact_tags', blank=True, verbose_name='keywords', help_text='Keywords to associate this research with. Helps others easily find it.')

	archived = models.BooleanField(default=False)
	alchemer_survey_id = models.PositiveIntegerField(blank=True, null=True, help_text='The Alchemer survey ID used for this research. EX: 7968827')
	alchemer_survey_questions = JSONField(blank=True, null=True)
	

	class Meta:
		ordering = ['name']
		
	def __str__(self):
		return self.name

	
	def save(self, *args, **kwargs):
		"""
		Choose which date to use for sorting field
		"""
		if self.research_date:
			self.sort_date = self.research_date
		elif self.created_at: 
			self.sort_date = self.created_at
		else: 
			self.sort_date = timezone.now()
			
		super(Artifact, self).save(*args, **kwargs) 
		
	
	def storeUserResearchCount(self):
		'''
		Store the user's research count so we don't have to count and check on every view (for "my research" link)
		'''
		for user in list(set([self.created_by, self.updated_by, self.owner] + list(self.editors.all()))):
			user.profile.research_count = Artifact.objects.filter(Q(created_by=user) | Q(owner=user) | Q(editors=user)).count()
			user.save()
			
			
	def getArtifacts(request):
		'''
		Main gig on search page. Takes request params and returns research items and selected filters.
		'''
		# Start with all artifacts and no selected filters.
		artifacts = Artifact.objects.exclude(archived=True).all()
		qParam = request.GET.get('q'.strip(), None)
			
		# Selected taxonomy items are used as display tags also, so we can't just use 'values_list' of IDs.
		try:
			selectedMethods = Method.objects.filter(id__in=request.GET.getlist('method'))
		except: 
			selectedMethods = []
		
		try:
			selectedSources = Source.objects.filter(id__in=request.GET.getlist('source'))
		except:
			selectedSources = []
		
		try:
			selectedStatuses = Status.objects.filter(id__in=request.GET.getlist('status'))
		except:
			selectedStatuses = []
		
		try:
			selectedTags = Tag.objects.filter(id__in=request.GET.getlist('tag'))
		except:
			selectedTags = []
		
		try:
			selectedProjects = Project.objects.filter(id__in=request.GET.getlist('project'))
		except:
			selectedProjects = []
			
		if qParam:
			# CURRENT SPEED: 'cloud' search: 22 queries in 120ms.
			artifacts = artifacts.filter(
				Q(name__icontains=qParam) |
				Q(owner__username__icontains=qParam) |
				Q(owner__profile__full_name__icontains=qParam) |
				Q(abstract__icontains=qParam) |
				Q(hypothesis__icontains=qParam) |
				Q(description__icontains=qParam) |
				Q(target_audience__icontains=qParam) |
				Q(findings__icontains=qParam)
			)
			
		artifacts = filterObjectsContaining(artifacts, 'methods', selectedMethods)
		artifacts = filterObjectsContaining(artifacts, 'source', selectedSources)
		artifacts = filterObjectsContaining(artifacts, 'status', selectedStatuses)
		artifacts = filterObjectsContaining(artifacts, 'tags', selectedTags)
		artifacts = filterObjectsContaining(artifacts, 'projects', selectedProjects)
			
		# Sort and prefetch.
		# Default sort is '-sort_date'. It gets set on save() (look above): research date, or created date.
		sortParam = request.GET.get('sort', None)
		sortOrder = '-sort_date'
		if sortParam:
			if sortParam == 'date':
				sortOrder = 'sort_date'	
			elif sortParam == 'updateddatedesc':
				sortOrder = '-updated_at'	
			elif sortParam == 'updateddate':
				sortOrder = 'updated_at'	
		
		# Set secondary sort by name no matter what primary sort is.
		sortOrder = [sortOrder, 'name']
		
		artifacts = artifacts.order_by(*sortOrder).select_related('status').prefetch_related('methods').annotate(ownerEmail=F('owner__username')).annotate(ownerName=F('owner__profile__full_name'))
		
		return {
			'artifacts': artifacts,
			'qParam': qParam,
			'selectedMethods': selectedMethods,
			'selectedSources': selectedSources,
			'selectedStatuses': selectedStatuses,
			'selectedTags': selectedTags,
			'selectedProjects': selectedProjects,
		}
		
	
	def getAlchemerSurveyQuestions(self):
		'''
		On save of research item, try to get and save alchemer questions if alchemer survey ID exists.
		'''
		if self.alchemer_survey_id and settings.ALCHEMER_API_TOKEN and settings.ALCHEMER_API_TOKEN_SECRET:
			try:
				url = f'https://api.alchemer.com/v5/survey/{self.alchemer_survey_id}/question/?api_token={settings.ALCHEMER_API_TOKEN}&api_token_secret={settings.ALCHEMER_API_TOKEN_SECRET}'
				
				data = requests.get(url)
				
				questions = []
				for item in data.json()['data']:
					if item['base_type'] == 'Question':
						questions.append(item['title']['English'])
				
				self.alchemer_survey_questions = questions
					
			except Exception as ex:
				print(f'Error: Couldn\'t get Alchemer survey questions for ID: {self.alchemer_survey_id}')
		elif not self.alchemer_survey_id:
			self.alchemer_survey_questions = None
			
		self.save()
	
	
	def notifyOwnerNewArtifact(self):
		try:
			sendEmail({
				'subject': f'[Alexandria Research] New research item entered for you',
				'recipients': [self.owner.username],
				'message': f'<div style="font-family:sans-serif;font-size:14px;line-height:20px;"><p>{self.created_by.profile.full_name} ({self.created_by.username}) just added a new research item "{self.name}" and marked you as the owner.<p><p>The research item detail page is here: <a href="https://REPLACE_ME/research/{self.id}/edit/">https://REPLACE_ME/research/{self.id}/edit/</a></p>',
			})
		except Exception as ex:
			pass
			
			
	def notifyBrokenLink(self, brokenUrl):
		try:
			sendEmail({
				'subject': f'[Alexandria Research] Broken link reported on your research item',
				'recipients': [self.owner.username],
				'message': f'<div style="font-family:sans-serif;font-size:14px;line-height:20px;"><p>A broken link was just reported on your research item: <strong>{self.name}</strong>.<p><p>The URL that was reported as broken: {brokenUrl}.</p><p>The research item detail page is here: <a href="https://REPLACE_ME/research/{self.id}/edit/">https://REPLACE_ME/research/{self.id}/edit/</a></p>',
			})
		except Exception as ex:
			pass
	

class ArtifactSearch(models.Model):
	'''
	Store search terms, for kicks to see top searches.
	'''
	created_at = models.DateTimeField(default=datetime.now, editable=False)
	updated_at = models.DateTimeField(default=datetime.now, editable=False)
	
	search_text = models.CharField(max_length=255, unique=True)
	search_count = models.PositiveIntegerField(default=0)
	
	class Meta:
		ordering = ['-search_count', 'search_text']
		
	def __str__(self):
		return self.search_text


	def trackSearch(searchString):
		searchObj, created = ArtifactSearch.objects.get_or_create(search_text=searchString)
		
		searchObj.search_count = searchObj.search_count + 1
		searchObj.save()
		
		return ''
		
	


########################################################
########################################################
##
## Standards models in each app, direct copy/paste (trim Profile as needed).
##
########################################################
########################################################

class Profile(models.Model):
	"""
	Extension of user object. Receives signal from User obj and 
	creates/saves the user's profile.
	"""
	created_at = models.DateTimeField(auto_now_add=True, editable=False)
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	full_name = models.CharField(max_length=255, blank=True)
	image = models.TextField(null=True, blank=True)
	inactive = models.BooleanField(default=False)
	research_count = models.PositiveIntegerField(default=0)
	
	class Meta:
		ordering = ['full_name']
		
	def __str__(self):
		return f'{self.user} : {self.full_name}'
	
	
	def updateFromPost(self, post):
		updatableFields = [
			'full_name',
			'image'
		]
		
		for field in updatableFields:
			postedValue = post.get(field, None)
			if postedValue:	
				setattr(self, field, postedValue)
	
	
	@staticmethod
	def usersByFullname():
		users = Profile.objects.filter(user__username__contains='@').exclude(Q(full_name__isnull=True) | Q(inactive=True)).order_by('full_name').values_list('user_id','full_name')
		return tuple(list(users))
		
		
	@staticmethod
	def usersByFullnameWithEmpty():
		users = Profile.objects.filter(user__username__contains='@').exclude(Q(full_name__isnull=True) | Q(inactive=True)).order_by('full_name').values_list('user_id','full_name')
		return tuple([('', '---------')] + list(users))
		

# Django signals: Tells Django to automatically save the User's Profile record when User is saved.
# You should never save Profile directly. Update profile fields and do "user.save()".
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
	if created:
		Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
	instance.profile.save()
	

class PageView(models.Model):
	"""
	Tracks #s of which pages viewed, and by user if exists.
	"""
	created = models.DateTimeField(auto_now_add=True, editable=False)
	modified = models.DateTimeField(auto_now=True, editable=False)
	user = models.ForeignKey(User, related_name='pageview_user', null=True, on_delete=models.SET_NULL)
	url = models.CharField(max_length=2000)
	view_count = models.PositiveIntegerField(default=0)

	class Meta:
		ordering = ['-view_count']	

	def __str__(self):
		return '%s : %s' % (self.view_count, self.url)


class BannerNotification(models.Model):
	"""
	Allows you to create a site-wide banner at the top of the page for site-wide 
	notifications, i.e. site maintenance, problems, important updates, etc.
	"""
	name = models.CharField(max_length=255)
	active = models.BooleanField(default=False)
	banner_text = models.CharField(max_length=255)
	banner_type = models.CharField(default='info', choices=[
		('info','info'),
		('warn','warn'),
		('alert','alert'),
	], max_length=20)


	class Meta:
		ordering = ['active','name']

	def __str__(self):
		return '%s - %s - %s' % (self.name, self.banner_type, self.active)


class SurveyQuestionExclusion(models.Model):
	'''
	Alchemer survey questions to exclude on display because unimportant, like: "what org are you in"
	'''
	question_text = models.CharField(max_length=255)

	class Meta:
		ordering = ['question_text']
		
	def __str__(self):
		return self.question_text


class BrokenLink(models.Model):
	"""
	Tracks reports of research broken links.
	"""
	created = models.DateTimeField(auto_now_add=True, editable=False)
	modified = models.DateTimeField(auto_now=True, editable=False)
	artifact = models.ForeignKey(Artifact, related_name='broken_link_artifact', on_delete=models.CASCADE)
	link_url = models.CharField(max_length=400)
	report_count = models.PositiveIntegerField(default=0)

	class Meta:
		ordering = ['-report_count']	

	def __str__(self):
		return '%s : %s' % (self.report_count, self.link_url)
		


