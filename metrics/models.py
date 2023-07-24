import math
import numpy
import pandas as pd

from datetime import datetime, timedelta
from functools import reduce
from operator import or_

from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator, ValidationError
from django.db import models, connection
from django.db.models import Count, Value, Sum, Q, Avg, JSONField, F
from django.db.models.functions import Lower
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.crypto import get_random_string

import metrics.helpers as helpers
from research.helpers import sendEmail


# Legacy, needed for migrations. Will error if removed.
def getCurrentYear():
	return timezone.now().year


# Legacy, needed for migrations. Will error if removed.
def current_year():
	return timezone.now().year


def getImportScriptUser():
	user, created = User.objects.get_or_create(username='import_script')
	
	if created:
		user.profile.full_name = 'import_script'
		user.save()
		
	return user

def getUsabillaImportScriptUser():
	user, created = User.objects.get_or_create(username='usabilla_import_script')
	
	if created:
		user.profile.full_name = 'usabilla_import_script'
		user.save()
		
	return user


def estimateCount(modelName, app='metrics'):
	'''
	Postgres really sucks at full table counts, this is a faster version:
	http://wiki.postgresql.org/wiki/Slow_Counting
	Return: {int} Estimated count of # of objects in model.
	'''
	cursor = connection.cursor()
	cursor.execute(f"select reltuples from pg_class where relname='{app}_{modelName.lower()}'")
	row = cursor.fetchone()
	return int(row[0])
	
	
class UserRole(models.Model):
	'''
	Examples:
	Department_Owner_Manager
	Financial_Analyst
	Self
	Manager
	Other
	'''
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	name = models.CharField(max_length=64, unique=True)
	
	class Meta:
		ordering = ['name']
		
	def __str__(self):
		return self.name


class Role(models.Model):
	'''
	Examples:
	Any user
	'''
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	name = models.CharField(max_length=64, unique=True)
	
	class Meta:
		ordering = ['name']
		
	def __str__(self):
		return self.name


class Url(models.Model):
	'''
	Examples:
	https://somesite.com/services/eamtlite/AssetsIManage.wss
	https://idea-1.somedomain.com/ECM/workflowmanagement/requesthome?menu=1
	'''
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	url = models.TextField(max_length=5000)
	
	class Meta:
		ordering = ['url']
		
	def __str__(self):
		return self.url


class GoalCompleted(models.Model):
	'''
	Examples:
	Yes
	No
	Partially
	'''
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	name = models.CharField(max_length=32, unique=True)
	
	class Meta:
		ordering = ['name']
		
	def __str__(self):
		return self.name


class Browser(models.Model):
	'''
	Examples:
	Mobile Safari 12.1.1
	Firefox 67.0
	Edge 18.17763
	'''
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	name = models.CharField(max_length=64, unique=True)
	
	class Meta:
		ordering = ['name']
		
	def __str__(self):
		return self.name


class OperatingSystem(models.Model):
	'''
	Examples:
	Windows 7
	Mac OS X 10.14.5
	Linux
	'''
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	name = models.CharField(max_length=32, unique=True)
	
	class Meta:
		ordering = ['name']
		
	def __str__(self):
		return self.name


class PrimaryGoal(models.Model):
	'''
	Examples:
	View_Update_my_assets
	Search_for_asset
	Modify_request
	Other
	'''
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	name = models.CharField(max_length=128, unique=True)
	
	class Meta:
		ordering = ['name']
		
	def __str__(self):
		return self.name


class DeviceType(models.Model):
	'''
	Examples:
	Desktop
	Mobile
	'''
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	name = models.CharField(max_length=32, unique=True)
	
	class Meta:
		ordering = ['name']
		
	def __str__(self):
		return self.name


class Country(models.Model):
	'''
	Examples:
	United Stated
	Ireland
	Hong Kong
	'''
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	name = models.CharField(max_length=64, unique=True)
	
	class Meta:
		ordering = ['name']
		verbose_name_plural = 'Countries'
		
	def __str__(self):
		return self.name


class State(models.Model):
	'''
	Examples:
	NY
	TX
	NC
	'''
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	name = models.CharField(max_length=64, unique=True)
	
	class Meta:
		ordering = ['name']
		
	def __str__(self):
		return self.name


class City(models.Model):
	'''
	Examples:
	Highland Park
	Austin
	Danbury
	'''
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	name = models.CharField(max_length=64, unique=True)
	
	class Meta:
		ordering = ['name']
		verbose_name_plural = 'Cities'
		
	def __str__(self):
		return self.name


class DataSource(models.Model):
	'''
	Examples:
	Usabilla
	Survey Monkey
	Other
	'''
	created_at = models.DateTimeField(auto_now_add=True)
	created_by = models.ForeignKey(User, related_name='data_source_created_by', on_delete=models.PROTECT)
	updated_at = models.DateTimeField(auto_now=True)
	updated_by = models.ForeignKey(User, related_name='data_source_updated_by', on_delete=models.PROTECT)
	
	name = models.CharField(max_length=64, unique=True)
	
	class Meta:
		ordering = ['name']
		
	def __str__(self):
		return self.name


class ProjectKeyword(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	name = models.CharField(max_length=64, unique=True)
	
	class Meta:
		ordering = ['name']
		
	def __str__(self):
		return self.name


class NpsScoreCategory(models.Model):
	'''
	Examples:
	Excellent
	Very good
	Good
	'''
	created_at = models.DateTimeField(auto_now_add=True)
	created_by = models.ForeignKey(User, related_name='nps_score_category_created_by', on_delete=models.PROTECT)
	updated_at = models.DateTimeField(auto_now=True)
	updated_by = models.ForeignKey(User, related_name='nps_score_category_updated_by', on_delete=models.PROTECT)

	name = models.CharField(max_length=32, unique=True)
	min_score_range = models.FloatField(validators=[MinValueValidator(-100), MaxValueValidator(100)])
	max_score_range = models.FloatField(validators=[MinValueValidator(-100), MaxValueValidator(100)])
	color_code = models.CharField(max_length=32, null=True, blank=True)
	text_color_code = models.CharField(max_length=32, null=True, blank=True)
	ux_points = models.PositiveIntegerField(default=0)
	
	class Meta:
		ordering = ['-max_score_range']
		verbose_name = 'NPS category'
		verbose_name_plural = 'NPS categories'
		
	def __str__(self):
		return self.name

	
	@staticmethod
	def getCategory(npsNum):
		'''
		Return: {model instance} The NpsScoreCategory for the given NPS -100 to 100.
		'''
		roundedNum = round(npsNum, 1)
		try:
			return NpsScoreCategory.objects.get(min_score_range__lte=roundedNum, max_score_range__gte=roundedNum)
		except Exception as ex:
			return None

	
	@staticmethod
	def getCategoryCounts(snapshots, includeZeros=True):
		'''
		Return: {queryset} NpsScoreCategory set with annotated counts of snapshots for each across given snapshots.
		'''
		categories = NpsScoreCategory.objects.order_by('-min_score_range').only('name', 'color_code', 'text_color_code')
		
		# If don't need 0s, simple annotation count # of snapshots for each unique found category.
		# Else if do need 0s: Manually loop thru each category and return the count even if 0.
		if not includeZeros:
			return categories.filter(project_snapshot_nps_score_category__in=snapshots, project_snapshot_nps_score_category__nps_meaningful_data=True).annotate(categoryCount=Count('project_snapshot_nps_score_category'))
		else:
			for category in categories:
				num = snapshots.filter(nps_score_category=npsCategory, nps_meaningful_data=True).distinct().count()
				
				if not num:
					num = 0
				
				# Add the category count to the model instance.
				category.categoryCount = num
				
		return categories
	

class Domain(models.Model):
	'''
	Examples:
	CFO
	Design
	Sales and Marketing Systems
	'''
	created_at = models.DateTimeField(auto_now_add=True)
	created_by = models.ForeignKey(User, related_name='domain_created_by', on_delete=models.PROTECT)
	updated_at = models.DateTimeField(auto_now=True)
	updated_by = models.ForeignKey(User, related_name='domain_updated_by', on_delete=models.PROTECT)

	name = models.CharField(max_length=64, unique=True)
	lead = models.ForeignKey(User, related_name='domain_lead', null=True, blank=True, on_delete=models.SET_NULL)
	admins = models.ManyToManyField(User, related_name='domain_admins', blank=True)
	
	class Meta:
		ordering = ['name']
		
	def __str__(self):
		return self.name

	
	def getCampaignCount(self):
		'''
		Return: {int} # of campaigns for this Domain.
		'''
		i = 0
		for project in self.project_domain.all():
			i += project.campaign_project.count()

		return i

	
	def updateDomainYearSnapshot(self, year=None):
		'''
		Get this Domain's projects and update DomainYearSnapshot values for the given year.
		Creates a new yearly instance of DomainSnapshot if not exist.
		Return: null
		'''
		if not year:
			year = timezone.now().year
			
		domainSnapshot, created = DomainYearSnapshot.objects.get_or_create(
			domain = self,
			year = year,
			defaults = {
				'created_by': getImportScriptUser(),
				'updated_by': getImportScriptUser(),				
			}
		)
	
		# Setup domain projects conditions we're measuring on.
		domainProjects = Project.objects.allActive().filter(domain=self).order_by(Lower('name'))
		domainCoreProjects = domainProjects.filter(core_project=True)
		domainCoreProjectsValidSnapshots = []
		domainCoreProjectsCurrentlyReporting = []
		
		# Set domainCoreProjectsValidSnapshots.
		for project in domainCoreProjects:
			#projectSnapshot = project.currently_reporting_snapshot
			projectSnapshot = project.latest_valid_currently_reporting_snapshot
			
			if projectSnapshot:	
				project.currentReportSnapshot = projectSnapshot
				domainCoreProjectsCurrentlyReporting.append(project)
				domainCoreProjectsValidSnapshots.append(project)
		
		## Now calculate and set each domain year metrics.
		
		# Basic counts and %s of project and flags.
		domainSnapshot.all_projects_count = domainProjects.count()
		domainSnapshot.core_projects_count = domainCoreProjects.count()
		domainSnapshot.core_projects_percent = round(domainSnapshot.core_projects_count/domainSnapshot.all_projects_count * 100, 4) if domainSnapshot.all_projects_count else 0
		
		# Core projects that we have CURRENT responses for (within 180 days)
		domainSnapshot.vote_projects_count = domainCoreProjects.filter(currently_reporting_snapshot__isnull=False).distinct().count()
		
		domainSnapshot.vote_projects_percent = round(domainSnapshot.vote_projects_count/domainSnapshot.core_projects_count * 100, 4) if domainSnapshot.core_projects_count else 0


		# Sum of currently reporting projects' NPS points (0-4 scale based on NPS category).
		# Currently reporting projects that have a baseline and have a snapshot with NPS responses.
		# Currently reporting projects that currently have 'excellent' NPS.
		domainNpsScorePoints = 0
		domainNpsScoreProjects = 0
		coreProjectsWithExcellentNps = 0
		coreProjectsMeetingNpsTargetCount = 0
		
		#logComment = f'Domain snapshot was updated: {self.name}'
		
		# NOTE: This loop validates items that have 30+ responses and <15 moe are used in the calc.
		for project in domainCoreProjectsValidSnapshots:
			#if project.currentReportSnapshot.nps_score_category:
			#	logComment += f'\n{project.name} : NPS : {project.currentReportSnapshot.nps_score_category.name}'
			
			# Track domain NPS points and meeting excellent
			if project.currentReportSnapshot.nps_meaningful_data:
				try:
					npsLatestScore = project.currentReportSnapshot.nps_score
					pts = project.currentReportSnapshot.nps_score_category.ux_points
					domainNpsScorePoints += pts
					domainNpsScoreProjects += 1
					if project.currentReportSnapshot.nps_score_category.name == 'Excellent':
						#logComment += ' : 30+ and <15 moe'
						coreProjectsWithExcellentNps += 1
				except Exception as ex:
					pass

				# Track core projects that are meeting their target.
				try:
					pys = project.current_year_settings
					npsLatestScore = project.currentReportSnapshot.nps_score
					npsTargetScore = pys.nps_target
					
					if npsLatestScore > npsTargetScore or npsLatestScore >= 26:
						coreProjectsMeetingNpsTargetCount += 1
				except Exception as ex:
					pass

		domainSnapshot.core_projects_nps_score_points = domainNpsScorePoints
		
		# Set currently reporting count and %.
		domainSnapshot.core_projects_currently_reporting_count = domainNpsScoreProjects
		domainSnapshot.core_projects_currently_reporting_percent = round(domainSnapshot.core_projects_currently_reporting_count/domainSnapshot.core_projects_count * 100, 4) if len(domainCoreProjectsValidSnapshots) else 0
		
		# Set currently reporting apps that have excellent NPS
		domainSnapshot.core_projects_excellent_nps_count = coreProjectsWithExcellentNps
		domainSnapshot.core_projects_excellent_nps_percent = round(coreProjectsWithExcellentNps/len(domainCoreProjectsValidSnapshots) * 100, 4) if len(domainCoreProjectsValidSnapshots) else 0
	
		# Set currently reporting apps that are meeting NPS target.
		oldTargetPercent = domainSnapshot.core_projects_nps_target_achieved_percent
		
		domainSnapshot.core_projects_nps_target_achieved_count = coreProjectsMeetingNpsTargetCount
		domainSnapshot.core_projects_nps_target_achieved_percent = round(coreProjectsMeetingNpsTargetCount/domainSnapshot.core_projects_currently_reporting_count * 100, 4) if domainSnapshot.core_projects_currently_reporting_count else 0
		
		# Set NPS letter grade based on average NPS points above.
		domainSnapshot.core_projects_nps_score_points_average = round(domainNpsScorePoints/domainNpsScoreProjects, 4) if domainNpsScoreProjects != 0 else 0
		
		if domainSnapshot.vote_projects_count > 0:
			domainSnapshot.core_projects_nps_letter_grade = NpsLetterGrade.getLetterGrade(domainSnapshot.core_projects_nps_score_points_average)
		else:
			domainSnapshot.core_projects_nps_letter_grade = None
		
		# Save it. The end.
		domainSnapshot.save()
	
		
	@staticmethod
	def getCombinedMetrics(domain=None, keyword=None):
		'''
		Used on Metrics home dashboard page and domains page for CURRENT YEAR metrics.
		Return: {obj} Aggregated yearly numbers for the given (optional) Domain(s) CURRENT YEAR snapshots.
		Perf: 141q in 196ms
		'''
		data = {
			'core_projects_count': None,
			'core_projects_currently_reporting_count': None,
			'core_projects_currently_reporting_percent': None,
			'core_projects_excellent_nps_count': None,
			'core_projects_excellent_nps_percent': None,
			'core_projects_nps_letter_grade': None,
			'core_projects_nps_score_points_average': None,
			'core_projects_nps_target_achieved_count': None,
			'core_projects_nps_target_achieved_percent': None,
			'vote_projects_count': None,
			'vote_projects_percent': None,
		}
		
		
		# For domain or "all", we auto-filter for core project.
		# For keyword, it's a custom list so don't filter by core projects.
		if domain:
			projects = Project.objects.allActive().filter(domain=domain, core_project=True).only('id')
		elif keyword:
			projects = Project.objects.allActive().filter(keywords=keyword).only('id')
		else:
			projects = Project.objects.allActive().filter(core_project=True).only('id')
		
		currentlyReportingCount = projects.filter(currently_reporting_snapshot__isnull=False).count()
		
		currentlyReportingMeaningfulCount = projects.filter(latest_valid_currently_reporting_snapshot__isnull=False).count()
		
		npsPointsProjectsCount = projects.filter(latest_valid_currently_reporting_snapshot__nps_score_category__isnull=False).count()
		
		npsTotalPoints = projects.aggregate(numTot=Sum(F('latest_valid_currently_reporting_snapshot__nps_score_category__ux_points')))['numTot']
		
		excellentNpsCount = projects.filter(latest_valid_currently_reporting_snapshot__nps_score_category__name='Excellent').count()
		
		npsTargetAchievedCount = projects.filter(Q(latest_valid_currently_reporting_snapshot__nps_score__gte=F('current_year_settings__nps_target')) | Q(latest_valid_currently_reporting_snapshot__nps_score__gte=26)).count()
		
		try:
			npsScorePointsAverage = round(npsTotalPoints/npsPointsProjectsCount,1)
			coreProjectsNpsLetterGrade = NpsLetterGrade.getLetterGrade(npsScorePointsAverage).name
		except Exception as ex:
			npsScorePointsAverage = 0
			coreProjectsNpsLetterGrade = None
		
		# Terms
		# core projects = Have the core_project flag set (priority 1-3)
		# vote_projects = Core with a "current" snapshot
		# core_projects_currently_reporting = Core with a "current" snapshot that's "meaningful"
		
		data['core_projects_count'] = projects.count()
		data['core_projects_currently_reporting_count'] = currentlyReportingMeaningfulCount
		data['core_projects_currently_reporting_percent'] = (data['core_projects_currently_reporting_count']/data['core_projects_count']) * 100 if data['core_projects_count'] else 0
		data['core_projects_excellent_nps_count'] = excellentNpsCount
		data['core_projects_excellent_nps_percent'] = (data['core_projects_excellent_nps_count']/data['core_projects_currently_reporting_count']) * 100 if data['core_projects_currently_reporting_count'] else 0
		data['core_projects_nps_score_points_average'] = npsScorePointsAverage
		data['core_projects_nps_letter_grade'] = coreProjectsNpsLetterGrade
		data['core_projects_nps_target_achieved_count'] = npsTargetAchievedCount
		data['core_projects_nps_target_achieved_percent'] = (data['core_projects_nps_target_achieved_count']/data['core_projects_currently_reporting_count']) * 100 if data['core_projects_currently_reporting_count'] else 0
		data['vote_projects_count'] = currentlyReportingCount
		data['vote_projects_percent'] = (data['vote_projects_count']/data['core_projects_count']) * 100 if data['core_projects_count'] else 0
		
		return data
		
	
	@staticmethod
	def domainsCanAdmin(user):
		'''
		Return: {queryset} Domains the user has admin access to.
		'''
		if user.hasAdminAccess():
			domains = Domain.objects.all()
		else:
			try:
				domains = Domain.objects.filter(Q(admins=user) | Q(lead=user)).distinct()
			except Exception as ex:
				domains = None
		
		return domains


##
## Project preset chainable queries.
##
class ProjectQueryset(models.QuerySet):
	def allActive(self):
		'''
		Get all projects that are active. Basic .fiter() preset.
		Usage: Project.objects.allActive()
		Return: {queryset} Chainable queryset, the same as if you used .filter().
		'''
		return self.filter(inactive=False)

class ProjectManager(models.Manager):
	def get_queryset(self):
		return ProjectQueryset(self.model, using=self._db)	## IMPORTANT KEY ITEM.

	def allActive(self):
		return self.get_queryset().allActive()


class Project(models.Model):
	'''
	Examples:
	Box
	CrashPlan
	Slack
	'''
	created_at = models.DateTimeField(auto_now_add=True)
	created_by = models.ForeignKey(User, related_name='project_created_by', on_delete=models.PROTECT)
	updated_at = models.DateTimeField(auto_now=True)
	updated_by = models.ForeignKey(User, related_name='project_updated_by', on_delete=models.PROTECT)
	
	inactive = models.BooleanField(default=False)
	domain = models.ForeignKey(Domain, related_name='project_domain', null=True, blank=True, on_delete=models.SET_NULL)
	name = models.CharField(max_length=64, unique=True)
	priority = models.IntegerField(choices=[
		(1,'1'),
		(2,'2'),
		(3,'3'),
		(4,'4'),
		(5,'5'),
	], null=True, blank=True)
	private_comments = models.BooleanField(default=False)
	keywords = models.ManyToManyField(ProjectKeyword, related_name='project_keywords', blank=True)
	contact = models.ForeignKey(User, related_name='project_contact', null=True, blank=True, on_delete=models.SET_NULL, help_text='Contact is the owner and has full edit access to the project info, can add other admins and editors, and can see emails in responses')
	admins = models.ManyToManyField(User, related_name='project_admins', blank=True, help_text='Admins have full edit access to the project info, can add other admins and editors, and can see emails in responses')
	editors = models.ManyToManyField(User, related_name='project_editors', blank=True, help_text='Editors can only create/edit manual snapshots and can see emails in responses')
	url = models.URLField(max_length=255, null=True, blank=True)
	estimated_num_users	= models.PositiveIntegerField(null=True, blank=True)
	core_project = models.BooleanField(default=False)
	vendor_app = models.CharField(choices=[
		('no','No'),
		('yes','Yes')
	], max_length=3, default='', blank=True)
	comments = models.TextField(blank=True)
	
	# Hidden fields.
	latest_valid_snapshot = models.ForeignKey('ProjectSnapshot', related_name='project_latest_valid_snapshot', null=True, blank=True, on_delete=models.SET_NULL)
	latest_snapshot_by_date = models.ForeignKey('ProjectSnapshot', related_name='project_latest_snapshot_by_date', null=True, blank=True, on_delete=models.SET_NULL)
	currently_reporting_snapshot = models.ForeignKey('ProjectSnapshot', related_name='project_currently_reporting_snapshot', null=True, blank=True, on_delete=models.SET_NULL)
	latest_valid_currently_reporting_snapshot = models.ForeignKey('ProjectSnapshot', related_name='project_latest_valid_currently_reporting_snapshot', null=True, blank=True, on_delete=models.SET_NULL)
	current_year_settings = models.ForeignKey('ProjectYearSetting', related_name='project_current_year_settings', null=True, blank=True, on_delete=models.SET_NULL)
	
	api_key = models.CharField(max_length=16, null=True, blank=True)

	objects = ProjectManager()
	
		
	class Meta:
		ordering = ['name']
		
	def __str__(self):
		return self.name
		
	
	def save(self, *args, **kwargs):
		'''
		If the project was updated and domains changed, update the new and old domain snapshots 
		to recalculate the rollup metrics based on projects in the domain.
		'''
		# New priority value determines if it's 'core' or not. 1-3 = vore
		if self.priority and self.priority <= 3:
			self.core_project = True
		else:
			self.core_project = False
			
		# Set flag for old domain calcs.
		try:
			oldDomain = Project.objects.get(id=self.id).domain
		except Exception as ex:
			oldDomain = None
			
		try:
			oldPriority = Project.objects.get(id=self.id).priority
		except Exception as ex:
			oldPriority = None
			
		if not self.api_key:
			self.api_key = get_random_string()
		
		# Now save the DB item and then do some calculations with the new saved values.
		super(Project, self).save(*args, **kwargs)
		
		# Cases:
		#   If had old domain, has new domain.
		#   else if had no old domain, now it does (new project example)
		#   else if had old domain, now it does not (removed from a domain)
		updateOldDomain = False
		updateNewDomain = False
		
		# Domain changed.
		if oldDomain and self.domain and oldDomain.id != self.domain.id:
			changeEntry = ActivityLog.objects.create(
				user = self.updated_by,
				content_object = self,
				comments = f'Project domain changed from "{oldDomain.name}" to "{self.domain.name}".'
			)
			eventEntry = ProjectEvent.objects.create(
				created_by = self.updated_by,
				updated_by = self.updated_by,
				name = f'Project domain changed from "{oldDomain.name}" to "{self.domain.name}".',
				project = self,
				date = timezone.now(),
			)
			updateOldDomain = True
			updateNewDomain = True
		# Domain added.
		elif self.domain and not oldDomain:
			updateNewDomain = True
		# Domain removed.
		elif oldDomain and not self.domain:
			updateOldDomain = True
		else:
			pass
			
		# If priority changed, update the current domain stats (changes "core" project stats).
		if self.priority != oldPriority:
			updateNewDomain = True

		# Update domains if flags are set.
		if updateOldDomain:
			try:
				oldDomain.updateDomainYearSnapshot()
			except:
				pass
		if updateNewDomain:
			try:
				self.domain.updateDomainYearSnapshot()
			except:
				pass
		
	
	def getVoteResponses(self):
		'''
		Return: {queryset} All responses for all campaigns for this project.
		'''
		return VoteResponse.objects.filter(campaign__project=self)
		
	
	def getFeedbackResponses(self):
		'''
		Return: {queryset} All responses for all campaigns for this project.
		'''
		return FeedbackResponse.objects.filter(campaign__project=self)
		
	
	def getOtherResponses(self):
		'''
		Return: {queryset} All responses for all campaigns for this project.
		'''
		return OtherResponse.objects.filter(campaign__project=self)
		
	
	def getLatestSnapshot(self, requiredValid=False):
		'''
		Return: {model instance} This project's lastest snapshot (optionally lastest meaningful).
		'''
		snapshot = None
		
		if requiredValid:
			try:
				snapshot = self.project_snapshot_project.get(date_period='last90', nps_meaningful_data=True)
			except Exception as ex:
				try:
					snapshot = self.project_snapshot_project.filter(date_period='quarter', nps_meaningful_data=True).order_by('-date').first()
				except:
					pass
				
		else:
			try:
				snapshot = self.project_snapshot_project.get(date_period='last90')
			except Exception as ex:
				try:
					snapshot = self.project_snapshot_project.filter(date_period='quarter').order_by('-date').first()
				except:
					pass
				
		return snapshot
	
	
	def getCurrentlyReportingSnapshot(self, requiredValid=False):
		'''
		Used to find and store this relationship on the project instance so it's always instantly available.
		Return: {model instance} Get this project's "current" snapshot.
		'''
		today = timezone.now()
		oldestDate = today - timedelta(days=180)
		snapshot = None
		
		if requiredValid:
			try:
				snapshot = self.project_snapshot_project.get(date_period='last90', nps_meaningful_data=True)
			except Exception as ex:
				try:
					snapshot = self.project_snapshot_project.filter(date_period='quarter', nps_meaningful_data=True, nps_score_date__gte=oldestDate).order_by('-date').first()
				except Exception as ex:
					pass
		else:
			try:
				snapshot = self.project_snapshot_project.get(date_period='last90')
			except Exception as ex:
				try:
					snapshot = self.project_snapshot_project.filter(date_period='quarter', nps_score_date__gte=oldestDate).order_by('-date').first()
				except Exception as ex:
					pass
						
		return snapshot
		
	
	def getCreateSnapshot(self, last90=False, year=None, quarter=None, month=None, create=False):
		'''
		Convenience method to get or create a snapshot for this project using the given params.
		Centralizes the logistics and values needed for querying and creating new.
		Return: {model instance} A snapshot (or None) for this project using the given params.
		'''
		
		dataSource = DataSource.objects.get(name='Usabilla')
		
		if (last90):
			filterConditions = {
				'project': self,
				'date_period': 'last90',
				'defaults': {}
			}
		elif year and quarter:
			filterConditions = {
				'project': self,
				'date_period': 'quarter',
				'date__year': year,
				'date_quarter': quarter,
				'defaults': {
					'date': timezone.make_aware(datetime(year, quarter * 3, 1)),
				}
			}
		elif year and month:
			filterConditions = {
				'project': self,
				'date_period': 'month',
				'date__year': year,
				'date__month': month,
				'defaults': {
					'date': timezone.make_aware(datetime(year, month, 1)),
					#'date_month': month,
				}
			}
		else:
			return None
			
		if create:
			filterConditions['defaults'].update({
				'entry_type': 'automatic import',
				'data_source': dataSource,
				'created_by': getImportScriptUser(),
				'updated_by': getImportScriptUser(),
			})
			projectSnapshot, created = ProjectSnapshot.objects.get_or_create(**filterConditions)
		else:
			try:
				del filterConditions['defaults']
				projectSnapshot = ProjectSnapshot.objects.get(**filterConditions)
			except Exception as ex:
				projectSnapshot = None
		
		return projectSnapshot	
	
		
	def updateMonthSnapshot(self, year, month):
		'''
		Get this project's set of responses, do calculations, then store them.
		ONLY used by automated script because it uses responses for calculations.
		Update this project's snapshot for the given month and year.
		Safety: 
			Only sets to 'automatic import' if there are responses for the period.
			Only deletes if there's an existing snapshot and it's set to 'automatic import'
		Return: null
		'''
		# If there are responses, we create or take over the existing snapshot via auto import script.
		# Else, we only delete a snapshot for the period if it was NOT a manual entered one.
		responses = self.getVoteResponses().filter(date__year=year, date__month=month)
		
		if responses.count() > 0:
			projectSnapshot = self.getCreateSnapshot(create=True, year=year, month=month)
			projectSnapshot.entry_type = 'automatic import'
			projectSnapshot.data_source = DataSource.objects.get(name='Usabilla')
			projectSnapshot.response_day_range = 30
			
			scoreDate = responses.order_by('-date').values('date').first()['date']
			
			if projectSnapshot.nps_score:
				projectSnapshot.nps_score_date = scoreDate
	
			if projectSnapshot.umux_score:
				projectSnapshot.umux_score_date = scoreDate
	
			if projectSnapshot.goal_completed_percent:
				projectSnapshot.goal_completed_date = scoreDate
				
			projectSnapshot.calculateStats(responses)
			projectSnapshot.save()
		else:
			# Look for empty snapshot for this month/year for automatic import and delete it.
			projectSnapshot = self.getCreateSnapshot(create=False, year=year, month=month)
			if projectSnapshot and projectSnapshot.entry_type == 'automatic import':
				projectSnapshot.delete()
		
	
	def updateQuarterSnapshot(self, year, quarter):
		'''
		Get this project's set of responses, do calculations, then store them.
		ONLY used by automated script because it uses responses for calculations.
		Update this project's snapshot for the given quarter and year.
		Safety: 
			Only sets to 'automatic import' if there are responses for the period.
			Only deletes if there's an existing snapshot and it's set to 'automatic import'
		Return: null
		'''
		# If there are responses, we create or take over the existing snapshot via auto import script.
		# Else, we only delete a snapshot for the period if it was NOT a manual entered one.
		responses = self.getVoteResponses().filter(date__year=year, date__quarter=quarter)
		
		if responses.count() > 0:
			projectSnapshot = self.getCreateSnapshot(create=True, year=year, quarter=quarter)
			projectSnapshot.entry_type = 'automatic import'
			projectSnapshot.data_source = DataSource.objects.get(name='Usabilla')
			projectSnapshot.response_day_range = 90
			
			scoreDate = responses.order_by('-date').values('date').first()['date']
			
			if projectSnapshot.nps_score:
				projectSnapshot.nps_score_date = scoreDate
	
			if projectSnapshot.umux_score:
				projectSnapshot.umux_score_date = scoreDate
	
			if projectSnapshot.goal_completed_percent:
				projectSnapshot.goal_completed_date = scoreDate
				
			projectSnapshot.calculateStats(responses)
			projectSnapshot.save()
		else:
			# Look for empty snapshot for this month/year for automatic import and delete it.
			projectSnapshot = self.getCreateSnapshot(create=False, year=year, quarter=quarter)
			if projectSnapshot and projectSnapshot.entry_type == 'automatic import':
				projectSnapshot.delete()
		

	def updateLast90Snapshot(self):
		'''
		Get this project's set of responses, do calculations, then store them.
		ONLY used by automated script because it uses responses for calculations.
		Update this project's snapshot for the past 90-180 days from TODAY.
		Safety: 
			Only sets to 'automatic import' if there are responses for the period.
			Only deletes if there's an existing snapshot and it's set to 'automatic import'
		Return: null
		'''
		# Start at 90 days, and go back in increment of 30, up to 180 days until we get 30+ and <15 moe.
		# dayRange var is used so we can later store which one we used.
		# Note at the end, 180 is used no matter what if we reach that point.
		projectResponses = self.getVoteResponses()
		dayRange = 90
		responses = projectResponses.filter(date__gte=helpers.getDaysAgo(dayRange))
		
		if not ProjectSnapshot.hasMeaningfulNps(responses):
			dayRange = 120
			responses = projectResponses.filter(date__gte=helpers.getDaysAgo(dayRange))
			if not ProjectSnapshot.hasMeaningfulNps(responses):
				dayRange = 150
				responses = projectResponses.filter(date__gte=helpers.getDaysAgo(dayRange))
				if not ProjectSnapshot.hasMeaningfulNps(responses):
					dayRange = 180
					responses = projectResponses.filter(date__gte=helpers.getDaysAgo(dayRange))
		
		# If there are responses, we create or take over the existing snapshot via auto import script.
		# Else, we only delete a snapshot for the period if it was NOT a manual entered one.
		if responses.count() > 0:
			projectSnapshot = self.getCreateSnapshot(create=True, last90=True)
			projectSnapshot.entry_type = 'automatic import'
			projectSnapshot.data_source = DataSource.objects.get(name='Usabilla')
			projectSnapshot.response_day_range = dayRange

			scoreDate = responses.order_by('-date').values('date').first()['date']
			
			if projectSnapshot.nps_score:
				projectSnapshot.nps_score_date = scoreDate

			if projectSnapshot.umux_score:
				projectSnapshot.umux_score_date = scoreDate

			if projectSnapshot.goal_completed_percent:
				projectSnapshot.goal_completed_date = scoreDate
				
			projectSnapshot.calculateStats(responses)
			projectSnapshot.save()
		else:
			# Look for empty snapshot for this month/year for automatic import and delete it.
			projectSnapshot = self.getCreateSnapshot(create=False, last90=True)
			if projectSnapshot and projectSnapshot.entry_type == 'automatic import':
				projectSnapshot.delete()

	
	def updateAllSnapshots(self):
		'''
		Get/create/update all Snapshots for this project for every month and quarter it has responses for.
		Return: null
		'''
		projectResponses = self.getVoteResponses()
		
		if projectResponses.count() > 0:
			startDate = projectResponses.order_by('date').values('date').first()['date']
			endDate = projectResponses.order_by('-date').values('date').first()['date']
			
			# Loop thru every quarter from oldest to newest response dates and calculate snapshots.
			pidx = pd.period_range(start = startDate, end = endDate, freq ='Q')
			for period in pidx:
				self.updateQuarterSnapshot(year=period.year, quarter=period.quarter)

			# Loop thru every month from oldest to newest response dates and calculate snapshots.
			pidx = pd.period_range(start = startDate, end = endDate, freq ='M')
			for period in pidx:
				self.updateMonthSnapshot(year=period.year, month=period.month)

			# Update the last 90 days snapshot.
			self.updateLast90Snapshot()
		else:
			# Else there are no responses, so cleanup and delete all automatic import snapshots.
			for snapshot in self.project_snapshot_project.filter(entry_type='automatic import'):
				snapshot.delete()
	
	
	@staticmethod
	def getFilteredSet(filterdata, coreProjectsOnly):
		'''
		Convenience method for project tiles and table (deprecated) pages.
		Return: {queryset} All projects or Domain specific projects, and optional 2nd filter; core projects only.
		'''
		if filterdata['selectedArchived'] == 'y':
			projects = Project.objects.filter(inactive=True)
		else:
			projects = Project.objects.allActive().all()
		
		try:
			projects = projects.filter(domain=filterdata['selectedDomain'])
		except Exception as ex:
			pass
		
		if filterdata['selectedProjectKeywords']:
			try:
				projects = projects.filter(keywords__in=filterdata['selectedProjectKeywords'])
			except Exception as ex:
				pass
		
		if filterdata['selectedPriorities']:
			try:
				projects = projects.filter(priority__in=filterdata['selectedPriorities'])
			except Exception as ex:
				pass
				
		if filterdata['selectedActive']:
			try:
				projects = projects.filter(currently_reporting_snapshot__isnull=False)
			except Exception as ex:
				pass
		
		return projects
		
	
	def storeLatestSnapshots(self):
		'''
		Get this project's key snapshots used for calculations/displays and store relationship for quick reference.
		Return: null
		'''
		try:
			self.latest_valid_snapshot = self.getLatestSnapshot(requiredValid=True)
			self.latest_snapshot_by_date = self.getLatestSnapshot()
			self.currently_reporting_snapshot = self.getCurrentlyReportingSnapshot()
			self.latest_valid_currently_reporting_snapshot = self.getCurrentlyReportingSnapshot(requiredValid=True)
			self.save()
		except Exception as ex:
			pass
	
	
	def setYearBaselinesAndTargets(self, year=timezone.now().year):
		'''
		Try to set an NPS and UMUX baseline score for this project.
		This is called in 3 places:
			1. End of nightly usabilla import from API
			2. In manual script we run: "update field alias and pull data"
			3. When changing a campaign's project.
			
			Based on this logic contained in downstrean functions:
				If it's after July 15, do nothing.
				If there's already a baseline, do nothing.
				If no baseline and we find a "meaningful" snapshot, in this order, use it's values:
					Q4 (year-1), Q1, Q2, last90
		Return: null
		'''
		# Get or create a ProjectYearSetting for the project. 
		# After the initial run on Jan 1, every existing project will have one.
		# This will only create for any new projects added after Jan 1.
		projectYearSettings, created = ProjectYearSetting.objects.get_or_create(
			project = self,
			year = year,
			defaults = {
				'created_by': getImportScriptUser(),
				'updated_by': getImportScriptUser(),
			}
		)
		
		# Cache current year settings relationship to project if not already.
		if not self.current_year_settings and year == timezone.now().year:
			self.current_year_settings = projectYearSettings
			self.save()
			
		projectYearSettings.setNpsBaseline()
		projectYearSettings.setUmuxBaseline()
		projectYearSettings.calculateTargets()
		projectYearSettings.save()

	
	@staticmethod
	def getQuarterlyChangers():
		'''
		If it's the first week of the month, and the end of last quarter happend durning last week,
		For each project, get 3 quarters back of snapshots and see if NPS declined or increased consecutively across 2 quarters.
		Return: {obj} Arrays of projects for decliners and increasers.
		'''
		today = timezone.now()
		
		lastWeekStart = helpers.getDaysAgo(7).replace(hour=0)
		lastWeekEnd = helpers.getDaysAgo(1).replace(hour=23)
		currentQ = math.floor((today.month - 1) / 3 + 1)
		currentQStart = timezone.datetime(today.year, 3 * currentQ - 2, 1, tzinfo=timezone.utc).replace(hour=12)
		currentQMid = currentQStart.replace(month=currentQStart.month+1)
		
		quartersDeclineProjects = []
		quartersIncreaseProjects = []
		
		if today.day <= 7 and today.month == currentQStart.month:
			# Get past 2 quarters' year and quarter #.
			startDate = currentQStart.replace(month=currentQStart.month+1) - timedelta(270)
			endDate = currentQMid - timedelta(90)
			quarters = [] # (start),(end):  [(2020, 4), (2021, 1)]
			pidx = pd.period_range(start = startDate, end = endDate, freq ='Q')
			for i, period in enumerate(pidx):
				quarters.append((period.year, period.quarter))
				
			for p in Project.objects.allActive():
				try:
					q3back = p.project_snapshot_project.filter(date__year=quarters[0][0], date_quarter=quarters[0][1], nps_meaningful_data=True).values('nps_score').first()['nps_score']
					q2back = p.project_snapshot_project.filter(date__year=quarters[1][0], date_quarter=quarters[1][1], nps_meaningful_data=True).values('nps_score').first()['nps_score']
					q1back = p.project_snapshot_project.filter(date__year=quarters[2][0], date_quarter=quarters[2][1], nps_meaningful_data=True).values('nps_score').first()['nps_score']
				
					if q1back < q2back < q3back:
						quartersDeclineProjects.append(p)
					elif q1back > q2back > q3back:
						quartersIncreaseProjects.append(p)
						
				except Exception as ex:
					pass
					
		return {
			'decliners': quartersDeclineProjects,
			'increasers': quartersIncreaseProjects,
		}
	
		
	@staticmethod
	def getMonthlyChangers():
		'''
		If it's the first week of the month, and the end of last month happend durning last week,
		For each project, get 4 months back of snapshots and see if NPS declined or increased consecutively across 3 months.
		Return: {obj} Arrays of projects for decliners and increasers.
		'''
		today = timezone.now()
		
		monthsDeclineProjects = []
		monthsIncreaseProjects = []
		
		if today.day <= 7:
			# (2020, 4)
			monthAgo1 = helpers.getYearMonthAgo(1)
			monthAgo2 = helpers.getYearMonthAgo(2)
			monthAgo3 = helpers.getYearMonthAgo(3)
			monthAgo4 = helpers.getYearMonthAgo(4)
	
			for p in Project.objects.allActive():
				try:
					m1back = p.project_snapshot_project.filter(
							date__year=monthAgo1[0],
							date__month=monthAgo1[1],
							nps_meaningful_data=True
						).values('nps_score').first()['nps_score']
					m2back = p.project_snapshot_project.filter(
							date__year=monthAgo2[0],
							date__month=monthAgo2[1],
							nps_meaningful_data=True
						).values('nps_score').first()['nps_score']
					m3back = p.project_snapshot_project.filter(
							date__year=monthAgo3[0],
							date__month=monthAgo3[1],
							nps_meaningful_data=True
						).values('nps_score').first()['nps_score']
					m4back = p.project_snapshot_project.filter(
						date__year=monthAgo4[0],
						date__month=monthAgo4[1],
						nps_meaningful_data=True
					).values('nps_score').first()['nps_score']
			
				
					if m1back < m2back < m3back < m4back:
						monthsDeclineProjects.append(p)
					elif m1back > m2back > m3back > m4back:
						monthsIncreaseProjects.append(p)
						
				except Exception as ex:
					pass
					
		return {
			'decliners': monthsDeclineProjects,
			'increasers': monthsIncreaseProjects,
		}
		
	
	@staticmethod
	def projectsCanAdmin(user):
		'''
		Return: {queryset} Projects the user can admin.
		'''
		if user.hasAdminAccess():
			projects = Project.objects.all()
		else:
			try:
				projects = Project.objects.filter(Q(admins=user) | Q(contact=user) | Q(domain__admins=user) | Q(domain__lead=user)).distinct()
			except Exception as ex:
				projects = None
		
		return projects
		
		
	@staticmethod
	def projectsCanAdminDomainProjects(user):
		'''
		Get the domain(s) for the project the user is an admins is and return all those projects.
		Return: {queryset} Projects the user can admin's domain's all projects.
		'''
		if user.hasAdminAccess():
			projects = Project.objects.allActive().order_by(Lower('name'))
		else:
			try:
				domains = Domain.objects.filter(Q(lead=user) | Q(admins=user) | Q(project_domain__admins=user) | Q(project_domain__contact=user)).distinct()
				projects = Project.objects.allActive().filter(domain__in=domains).order_by(Lower('name'))
			except Exception as ex:
				projects = None
		
		return projects
		
		
	@staticmethod
	def projectsCanEdit(user):
		'''
		Return: {queryset} Projects the user can edit.
		'''
		if user.hasAdminAccess():
			projects = Project.objects.all()
		else:
			try:
				projects = Project.objects.filter(Q(admins=user) | Q(contact=user) | Q(editors=user) | Q(domain__admins=user) | Q(domain__lead=user)).distinct()
			except Exception as ex:
				projects = None
		
		return projects
		
		
	def recalculateSnapshotsBaselinesAndDomains(self):
		'''
		Convenience bundle function used on campaign_edit when campaign changes projects (very rare).
		Return: null
		'''
		self.updateAllSnapshots()
		self.storeLatestSnapshots()
		self.setYearBaselinesAndTargets()
		if self.domain:
			self.domain.updateDomainYearSnapshot()
	
	
	def createSnapshotForDate(self, startDate=None, endDate=None):
		'''
		Used for special Time machine feature to create a 'last90' snapshot on the fly for any given date.
		'''
		# Start at 90 days, and go back in increment of 30, up to 180 days until we get 30+ and <15 moe.
		# dayRange var is used so we can later store which one we used.
		# Note at the end, 180 is used no matter what if we reach that point.
		projectSnapshot = None
		projectResponses = self.getVoteResponses()
		endDate = timezone.make_aware(endDate)
		
		# If no custom start date was given, do a standard "last90" snapshot.
		# Else use responses from the specificed start/end dates.
		if not startDate:
			dayRange = 90
			startDate = endDate - timedelta(days=dayRange)
			responses = projectResponses.filter(date__gte=startDate, date__lte=endDate)
		
			if not ProjectSnapshot.hasMeaningfulNps(responses):
				dayRange = 120
				responses = projectResponses.filter(date__gte=(endDate-timedelta(days=dayRange)), date__lte=endDate)
				if not ProjectSnapshot.hasMeaningfulNps(responses):
					dayRange = 150
					responses = projectResponses.filter(date__gte=(endDate-timedelta(days=dayRange)), date__lte=endDate)
					if not ProjectSnapshot.hasMeaningfulNps(responses):
						dayRange = 180
						responses = projectResponses.filter(date__gte=(endDate-timedelta(days=dayRange)), date__lte=endDate)
		else:
			startDate = timezone.make_aware(startDate)
			dayRange = (endDate - startDate).days
			responses = projectResponses.filter(date__gte=startDate, date__lte=endDate)
			
		# If there are responses, we create or take over the existing snapshot via auto import script.
		# Else, we only delete a snapshot for the period if it was NOT a manual entered one.
		if responses.count() > 0:
			projectSnapshot = ProjectSnapshot(**{
				'created_by': getImportScriptUser(),
				'updated_by': getImportScriptUser(),
				'project': self,
				'date': endDate,
				'date_period': 'custom',
				'entry_type': '',
				'data_source': DataSource.objects.get(name='Other'),
				'response_day_range': dayRange
			})
			
			projectSnapshot.calculateStats(responses)

			scoreDate = responses.order_by('-date').values('date').first()['date']
			
			if projectSnapshot.nps_score:
				projectSnapshot.nps_score_date = scoreDate
			
			if projectSnapshot.umux_score:
				projectSnapshot.umux_score_date = scoreDate
			
			if projectSnapshot.goal_completed_percent:
				projectSnapshot.goal_completed_date = scoreDate
		
		return projectSnapshot

	
	def getReportPeriodData(self, request):
		'''
		Used by project detail page
		'''
		timeMachineStartDate = None
		timeMachineEndDate = None
		customTimeMachineMessage = None
		reportPeriod = helpers.getReportPeriod(request)
		
		# Figure out what snapshot get.
		# Fallback is last90.	
		try:
			if 'last90' in reportPeriod:
				reportPeriod = 'last90'
				snapshotArgs = {
					'date_period': 'last90'
				}
			elif 'q' in reportPeriod:
				quarterYear = reportPeriod.split('q')
				snapshotArgs = {
					'date_period': 'quarter',
					'date__year': int(quarterYear[1]),
					'date_quarter': int(quarterYear[0])
				}
			elif 'm' in reportPeriod:
				monthYear = reportPeriod.split('m')
				snapshotArgs = {
					'date_period': 'month',
					'date__year': int(monthYear[1]),
					'date__month': int(monthYear[0])
				}
			else:
				timeMachineEndDate = datetime.strptime(reportPeriod,'%Y-%m-%d')
	
				if request.GET.get('startdate', None):
					timeMachineStartDate = datetime.strptime(request.GET.get('startdate'),'%Y-%m-%d')
		except Exception as ex:
			timeMachineEndDate = None
			reportPeriod = 'last90'
			snapshotArgs = {
				'date_period': 'last90'
			}
		
		# Try and get the report_period snapshot and all its responses (last90, Q, M, time machine custom).
		try:
			if not timeMachineEndDate:
				projectSnapshot = self.project_snapshot_project.get(**snapshotArgs)
			else:
				projectSnapshot = self.createSnapshotForDate(startDate=timeMachineStartDate, endDate=timeMachineEndDate)
				
				if timeMachineStartDate:
					messageStartDate = timeMachineStartDate
				else:
					messageStartDate = timeMachineEndDate - timedelta(days=projectSnapshot.response_day_range)
				
				customTimeMachineMessage = f"You are viewing a custom report period via the time machine, from <strong>{messageStartDate.strftime('%b %d, %Y')}</strong> to <strong>{timeMachineEndDate.strftime('%b %d, %Y')}</strong>."
				
			projectSnapshotResponses = projectSnapshot.getVoteResponses()
		except Exception as ex:
			projectSnapshot = None
			projectSnapshotResponses = None
		
		return {
			'usingTimeMachine': True if timeMachineEndDate else False,
			'timeMachineEndDate': timeMachineEndDate,
			'timeMachineStartDate': timeMachineStartDate,
			'customTimeMachineMessage': customTimeMachineMessage,
			'projectSnapshot': projectSnapshot,
			'projectSnapshotResponses': projectSnapshotResponses,
			'reportPeriod': reportPeriod,
		}
	
	
	def responsesRawDataToCsv(self, responses):
		rowsArr = []
		fieldNames = []
		
		for r in responses:
			for fn,v in r.raw_data['data'].items():
				fieldNames.append(fn)				
		fieldNames = list(set(fieldNames))
		
		# For each response, loop thru every field, get the value.
		for r in responses:
			responseArr = []
			responseArr.append(r.date)
			responseArr.append(r.campaign.key)
			responseArr.append(r.uid)
			
			for fn in fieldNames:
				try:
					v = r.raw_data['data'][fn]
				except:
					v = ' '
				responseArr.append(v)
			rowsArr.append(responseArr)
		
		headerRow = ['Date', 'Campaign key', 'Response ID'] + fieldNames
		
		# Add header row and return
		return [headerRow] + rowsArr	
		
		
class ProjectEvent(models.Model):
	'''
	Examples:
	Redesigned home page.
	Reduced survey capture to 15% of traffic.
	Changed checkout process
	'''
	created_at = models.DateTimeField(auto_now_add=True)
	created_by = models.ForeignKey(User, related_name='project_event_created_by', on_delete=models.PROTECT)
	updated_by = models.ForeignKey(User, related_name='project_event_updated_by', on_delete=models.PROTECT)
	updated_at = models.DateTimeField(auto_now=True)
	
	name = models.CharField(max_length=255)
	project = models.ForeignKey(Project, related_name='project_event_project', on_delete=models.CASCADE)
	date = models.DateField()
	
	class Meta:
		ordering = ['project', '-date']
		
	def __str__(self):
		return self.name


##
## Campaign preset chainable queries.
##
class CampaignQueryset(models.QuerySet):
	def allActive(self):
		'''
		Get all Campaigns that are active. Basic .fiter() preset.
		Usage: Campaign.objects.allActive()
		Return: {queryset} Chainable queryset, the same as if you used .filter().
		'''
		return self.filter(inactive=False)

	def fromUsabilla(self):
		'''
		Get all Campaigns that are active. Basic .fiter() preset.
		Usage: Campaign.objects.allActive()
		Return: {queryset} Chainable queryset, the same as if you used .filter().
		'''
		return self.exclude(uid__startswith='b')

class CampaignManager(models.Manager):
	def get_queryset(self):
		return CampaignQueryset(self.model, using=self._db)	## IMPORTANT KEY ITEM.

	def allActive(self):
		return self.get_queryset().allActive()

	def fromUsabilla(self):
		return self.get_queryset().fromUsabilla()


class Campaign(models.Model):
	'''
	Examples:
	Help Advisor Feedback - End user doc
	18_server provisioning feedback
	Vote_Help_eng_FULL
	'''
	created_at = models.DateTimeField(auto_now_add=True)
	created_by = models.ForeignKey(User, related_name='campaign_created_by', on_delete=models.PROTECT)
	updated_at = models.DateTimeField(auto_now=True)
	updated_by = models.ForeignKey(User, related_name='campaign_updated_by', on_delete=models.PROTECT)
	
	inactive = models.BooleanField(default=False)
	project = models.ForeignKey(Project, related_name='campaign_project', null=True, blank=True, on_delete=models.PROTECT)
	# uid from Usabilla. Basically just a FK to reference this in upstream systems.
	# One UID have multiple Campaigns here because we tack on "role" and "version" to make unique "key"
	uid = models.CharField(max_length=128, null=True, blank=True)
	usabilla_button_id = models.CharField(max_length=128, null=True, blank=True)
	# OUR unique key we generate and use
	key = models.CharField(max_length=128, unique=True, null=True, blank=True) # True unique campaign ID: 'campaignID + role + version'
	latest_response_date = models.DateTimeField(null=True, blank=True)
	latest_feedback_response_date = models.DateTimeField(null=True, blank=True)
	latest_other_response_date = models.DateTimeField(null=True, blank=True)
	vote_response_count = models.PositiveIntegerField(default=0)
	feedback_response_count = models.PositiveIntegerField(default=0)
	other_response_count = models.PositiveIntegerField(default=0)
	
	objects = CampaignManager()
	
	class Meta:
		ordering = ['uid']
		
	def __str__(self):
		return self.uid
		
		
	# def save(self, *args, **kwargs):
	# 	if not self.latest_response_date:
	# 		self.latest_response_date = timezone.make_aware(datetime(2015, 1, 1))
	# 	super(Campaign, self).save(*args, **kwargs)
		
		
	def storeResponseCount(self):
		self.vote_response_count = self.response_campaign.count()
		self.feedback_response_count = self.feedback_response_campaign.count()
		self.other_response_count = self.other_response_campaign.count()
		self.save()


class NpsLetterGrade(models.Model):
	'''
	Examples:
	A
	B+
	B
	B-
	'''
	created_at = models.DateTimeField(auto_now_add=True)
	created_by = models.ForeignKey(User, related_name='nps_letter_grade_created_by', on_delete=models.PROTECT)
	updated_at = models.DateTimeField(auto_now=True)
	updated_by = models.ForeignKey(User, related_name='nps_letter_grade_updated_by', on_delete=models.PROTECT)

	name = models.CharField(max_length=32, unique=True)
	min_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(4)])
	color_code = models.CharField(max_length=32, null=True, blank=True)

	class Meta:
		ordering = ['-min_score']
		verbose_name = 'NPS letter grade'
		
	def __str__(self):
		return self.name

	
	@staticmethod
	def getLetterGrade(score):
		'''
		Return: {model instance} NpsLetterGrade match for the given points.
		'''
		try:
			return NpsLetterGrade.objects.filter(min_score__lte=score).order_by('-min_score').first()
		except Exception as ex:
			return None
	

class UmuxScoreCategory(models.Model):
	'''
	Examples:
	A
	B+
	B
	B-
	'''
	created_at = models.DateTimeField(auto_now_add=True)
	created_by = models.ForeignKey(User, related_name='umux_score_category_created_by', on_delete=models.PROTECT)
	updated_at = models.DateTimeField(auto_now=True)
	updated_by = models.ForeignKey(User, related_name='umux_score_category_updated_by', on_delete=models.PROTECT)

	name = models.CharField(max_length=32, unique=True)
	min_score_range = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
	max_score_range = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
	color_code = models.CharField(max_length=32)
	text_color_code = models.CharField(max_length=32, null=True, blank=True)
	
	class Meta:
		ordering = ['-max_score_range']
		verbose_name = 'UMUX score category'
		verbose_name_plural = 'UMUX score categories'
		
	def __str__(self):
		return self.name

	
	@staticmethod
	def getCategory(score):
		'''
		Return: {model instance} UmuxScoreCategory match for the given score.
		'''
		roundedScore = round(score, 1)
		try:
			return UmuxScoreCategory.objects.get(min_score_range__lte=roundedScore, max_score_range__gte=roundedScore)
		except Exception as ex:
			return None

	
	@staticmethod
	def getCategoryCounts(snapshots, includeZeros=False):
		'''
		Return: {queryset} UmuxScoreCategory set with annotated counts of snapshots for each across given snapshots.
		'''
		categories = UmuxScoreCategory.objects.order_by('-min_score_range').only('name', 'color_code', 'text_color_code')
		
		# If don't need 0s, simple annotation count # of snapshots for each unique found category.
		# Else if do need 0s: Manually loop thru each category and return the count even if 0.
		if not includeZeros:
			return categories.filter(project_snapshot_umux_score_category__in=snapshots, project_snapshot_umux_score_category__umux_meaningful_data=True).annotate(categoryCount=Count('project_snapshot_umux_score_category'))
		else:
			# Loop thru each category and return the counts, even if 0.
			for category in categories:
				num = snapshots.filter(umux_score_category=category, umux_meaningful_data=True).distinct().count()
				
				if not num:
					num = 0
					
				# Add the category count to the model instance.
				category.categoryCount = num
				
		return categories
	

class GoalCompletedCategory(models.Model):
	'''
	Examples:
	Excellent
	Above average
	Average		
	'''
	created_at = models.DateTimeField(auto_now_add=True)
	created_by = models.ForeignKey(User, related_name='goal_completed_category_created_by', on_delete=models.PROTECT)
	updated_at = models.DateTimeField(auto_now=True)
	updated_by = models.ForeignKey(User, related_name='goal_completed_category_updated_by', on_delete=models.PROTECT)

	name = models.CharField(max_length=32, unique=True)
	min_score_range = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
	max_score_range = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
	color_code = models.CharField(max_length=32)
	text_color_code = models.CharField(max_length=32, null=True, blank=True)

	class Meta:
		ordering = ['-max_score_range']
		verbose_name_plural = 'Goal completed categories'
		
	def __str__(self):
		return self.name

	
	@staticmethod
	def getCategory(score):
		'''
		Return: {model instance} UmuxScoreCategory match for the given score.
		'''
		roundedScore = round(score, 1)
		try:
			return GoalCompletedCategory.objects.get(min_score_range__lte=roundedScore, max_score_range__gte=roundedScore)
		except Exception as ex:
			return None

	
	@staticmethod
	def getCategoryCounts(snapshots, includeZeros=False):
		'''
		Return: {queryset} GoalCompletedCategory set with annotated counts of snapshots for each across given snapshots.
		'''
		categories = GoalCompletedCategory.objects.order_by('-min_score_range').all().only('name', 'color_code', 'text_color_code')
		
		# If don't need 0s, simple annotation count # of snapshots for each unique found category.
		# Else if do need 0s: Manually loop thru each category and return the count even if 0.
		if not includeZeros:
			return categories.filter(project_snapshot_goal_completed_category__in=snapshots).annotate(categoryCount=Count('project_snapshot_goal_completed_category'))
		else:
			# Loop thru each category and return the counts, even if 0.
			for category in categories:
				num = snapshots.filter(goal_completed_category=category).distinct().count()
				
				if not num:
					num = 0
					
				# Add the category count to the model instance.
				category.categoryCount = num
				
		return categories


class Response(models.Model):
	'''
	Automated imported data from usabilla. A user's response to a survey.
	This should never be created or updated in admin. 100% auto-imported raw_data, parsed and created.
	'''
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	campaign = models.ForeignKey(Campaign, related_name='response_campaign', on_delete=models.PROTECT)
	uid = models.CharField(max_length=128, unique=True)
	date = models.DateTimeField(db_index=True)
	nps = models.SmallIntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(10)])
	nps_category = models.CharField(db_index=True, choices=[
		('promoter','Promoter'),
		('passive','Passive'),
		('detractor','Detractor'),
	], max_length=12, blank=True)
	umux_capability = models.SmallIntegerField(db_index=True, null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(7)])
	umux_ease_of_use = models.SmallIntegerField(db_index=True, null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(7)])
	umux_score = models.FloatField(null=True, blank=True)
	improvement_suggestion = models.TextField(blank=True)
	user_role = models.ForeignKey(UserRole, related_name='response_user_role', null=True, blank=True, on_delete=models.SET_NULL)
	primary_goal = models.ForeignKey(PrimaryGoal, related_name='response_primary_goal', null=True, blank=True, on_delete=models.SET_NULL)
	primary_goal_other = models.TextField(blank=True)
	goal_completed = models.ForeignKey(GoalCompleted, related_name='response_goal_completed', null=True, blank=True, on_delete=models.SET_NULL)
	goal_not_completed_reason = models.TextField(blank=True)
	comments = models.TextField(blank=True)
	email_provided = models.BooleanField(default=False)
	submitted_url = models.ForeignKey(Url, related_name='response_submitted_url', null=True, blank=True, on_delete=models.PROTECT)
	location = models.CharField(max_length=128, blank=True)
	country = models.ForeignKey(Country, related_name='response_country', null=True, blank=True, on_delete=models.SET_NULL)
	state = models.ForeignKey(State, related_name='response_state', null=True, blank=True, on_delete=models.SET_NULL)
	city = models.ForeignKey(City, related_name='response_city', null=True, blank=True, on_delete=models.SET_NULL)
	total_time = models.PositiveIntegerField(default=0)
	device_type = models.ForeignKey(DeviceType, related_name='response_device_type', null=True, blank=True, on_delete=models.PROTECT)
	browser = models.ForeignKey(Browser, related_name='response_browser', null=True, blank=True, on_delete=models.PROTECT)
	operating_system = models.ForeignKey(OperatingSystem, related_name='response_operating_system', null=True, blank=True, on_delete=models.PROTECT)
	raw_data = JSONField()
	
	class Meta:
		ordering = ['campaign', '-date']
		
	def __str__(self):
		return f'{self.campaign} : {self.uid}'
		

	def save(self, *args, **kwargs):
		# Set NPS category if NPS exists.
		if self.nps is not None:
			self.nps_category = helpers.getNpsCategory(self.nps)
		
		# Calculate UMUX score.
		if self.umux_capability and self.umux_ease_of_use:
			self.umux_score = helpers.getUmuxScore(self.umux_capability, self.umux_ease_of_use)
		
		super(Response, self).save(*args, **kwargs)
		
	
	@staticmethod	
	def getVoteResponsesCountsHistory(projects=None, startDate=None, endDate=None):
		'''
		Used on metrics home page.
		For each quarter in the given date range, sum NPS/UMUX/Goal completion response counts across given projects.
		Return: {obj} Labels and data to generate historical line chart with total quarterly response counts.
		'''
		if not projects or not startDate or not endDate:
			return []
		
		responsesHistoryChartData = []
		pidx = pd.period_range(start=startDate, end=endDate, freq='Q')
		
		for period in pidx:
			periodSnapshots = ProjectSnapshot.objects.filter(project__in=projects, date_period='quarter', date__year=period.year, date_quarter=period.quarter).only('nps_count', 'umux_count', 'goal_completed_count')
			npsCount = periodSnapshots.aggregate(Sum('nps_count'))['nps_count__sum']
			umuxCount = periodSnapshots.aggregate(Sum('umux_count'))['umux_count__sum']
			goalCompletedCount = periodSnapshots.aggregate(Sum('goal_completed_count'))['goal_completed_count__sum']	
			
			if npsCount is None:
				npsCount = 0
			if umuxCount is None:
				umuxCount = 0
			if goalCompletedCount is None:
				goalCompletedCount = 0

			responsesHistoryChartData.append({
				'label': f'{period.quarter}Q{str(period.year)[-2:]}',
				'NPS': npsCount,
				'Ease & Capabilities': umuxCount,
				'Goal completion': goalCompletedCount,
			})
		
		return responsesHistoryChartData
	
	
	@staticmethod	
	def createGoalImportPreviewData(attachment):
		'''
		Used for goal update import to preview changed CSV to verify sample of changes before submitting.
		Take first 100 rows of CSV file and list existing goal from DB, and new goal from attachment.
		Return: {array} List of responses with existing and new goal.
		'''
		df = pd.read_csv(attachment, dtype='string')
		df = df.head(100)
		
		dataArr = []
		
		for i in df.itertuples():
			try:
				existingGoal = VoteResponse.objects.get(uid=i[3]).primary_goal.name
			except Exception as ex:
				existingGoal = 'entry not found'
			
			if pd.isnull(i[10]):
				newGoal = ''
			else: 
				newGoal = i[10]
				
			dataArr.append({
				'id': i[3],
				'existingGoal': existingGoal,
				'newGoal': newGoal,
			})
			
		return dataArr
	
	
	@staticmethod
	def processGoalImportUpdateFile(attachment):
		'''
		Take uploaded CSV file and for each response, update the PrimaryGoal.
		Return: null
		'''
		df = pd.read_csv(attachment, dtype='string')
		
		for i in df.itertuples():
			try:
				response = VoteResponse.objects.get(uid=i[3])
				goal, created = PrimaryGoal.objects.get_or_create(name=i[10])
				response.primary_goal = goal
				response.save()
			except Exception as ex:
				pass
				
	
	@staticmethod
	def removeOldEmailValues():
		'''
		Called by weekly cron, deletes email values on responses older than 3 years ago.
		'''
		for r in VoteResponse.objects.filter(date__lte=helpers.getDaysAgo(365*2.99), raw_data__data__email__isnull=False):
			if r.raw_data['data'].get('email'):
				r.raw_data['data']['email'] = ''
				r.save()

class VoteResponse(Response):
	class Meta:
		proxy = True
		

class FeedbackResponseKeyword(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	name = models.CharField(max_length=64)
	
	class Meta:
		ordering = ['name']
		
	def __str__(self):
		return self.name
	
	
class FeedbackResponse(models.Model):
	'''
	Automated imported data. Only survey with type==feedback
	This should never be created or updated in admin. 100% auto-imported raw_data, parsed and created.
	'''
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	date = models.DateTimeField(db_index=True)
	uid = models.CharField(max_length=128, unique=True)
	campaign = models.ForeignKey(Campaign, related_name='feedback_response_campaign', on_delete=models.PROTECT)
	rating = models.SmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
	feedback_type = models.CharField(max_length=128, blank=True)
	comments = models.TextField(blank=True)
	email_provided = models.BooleanField(default=False)
	assignees = models.ManyToManyField(User, related_name='feedback_response_assignees', blank=True)
	keywords = models.ManyToManyField(FeedbackResponseKeyword, related_name='feedback_response_keywords', blank=True)
	notes = models.TextField(max_length=3000, blank=True)
	raw_data = JSONField()
	
	class Meta:
		ordering = ['campaign', '-date']
		
	def __str__(self):
		return f'{self.campaign} : {self.uid}'

	
	@staticmethod
	def removeOldEmailValues():
		'''
		Called by weekly cron, deletes email values on responses older than 3 years ago.
		'''
		for r in FeedbackResponse.objects.filter(date__lte=helpers.getDaysAgo(365*2.99), raw_data__data__email__isnull=False):
			if r.raw_data['data'].get('email'):
				r.raw_data['data']['email'] = ''
				r.save()
		

class OtherResponse(models.Model):
	'''
	Automated imported data. Only survey with type==other
	This should never be created or updated in admin. 100% auto-imported raw_data, parsed and created.
	'''
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	date = models.DateTimeField(db_index=True)
	uid = models.CharField(max_length=128, unique=True)
	campaign = models.ForeignKey(Campaign, related_name='other_response_campaign', on_delete=models.PROTECT)
	raw_data = JSONField()
	
	class Meta:
		ordering = ['campaign', '-date']
		
	def __str__(self):
		return f'{self.campaign} : {self.uid}'
	
	
	@staticmethod
	def removeOldEmailValues():
		'''
		Called by weekly cron, deletes email values on responses older than 3 years ago.
		'''
		for r in OtherResponse.objects.filter(date__lte=helpers.getDaysAgo(365*2.99), raw_data__data__email__isnull=False):
			if r.raw_data['data'].get('email'):
				r.raw_data['data']['email'] = ''
				r.save()
		
	
class ProjectSnapshot(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	created_by = models.ForeignKey(User, related_name='project_snapshot_created_by', on_delete=models.PROTECT)
	updated_at = models.DateTimeField(auto_now=True)
	updated_by = models.ForeignKey(User, related_name='project_snapshot_updated_by', on_delete=models.PROTECT)
	
	data_source = models.ForeignKey(DataSource, related_name='project_snapshot_data_source', null=True, blank=True, on_delete=models.SET_NULL)
	entry_type = models.CharField(choices=[
		('manual','Manual'),
		('automatic import','Automatic import')
	], max_length=20, default='manual', blank=True)
	project = models.ForeignKey(Project, related_name='project_snapshot_project', on_delete=models.CASCADE)
	date = models.DateField(null=True, blank=True)
	date_period = models.CharField(choices=[
		('month','Month'),
		('quarter','Quarter'),
		('last90','Last 90 days')
	], max_length=12, default='quarter', blank=True)
	# date__quarter only works on DB query. Store and use date_quarter always, for consistency.
	date_quarter = models.PositiveIntegerField(null=True, blank=True)
	# Unused and never set (for now). date__month and date.month both exist.
	date_month = models.PositiveIntegerField(null=True, blank=True)
	
	nps_score = models.FloatField(null=True, blank=True, validators=[MinValueValidator(-100), MaxValueValidator(100)])
	nps_score_category = models.ForeignKey(NpsScoreCategory, related_name='project_snapshot_nps_score_category', null=True, blank=True, on_delete=models.SET_NULL)
	nps_score_date = models.DateTimeField(null=True, blank=True)
	nps_count = models.PositiveIntegerField(null=True, blank=True)
	nps_promoter_count = models.PositiveIntegerField(null=True, blank=True)
	nps_passive_count = models.PositiveIntegerField(null=True, blank=True)
	nps_detractor_count = models.PositiveIntegerField(null=True, blank=True)
	nps_margin_error = models.FloatField(null=True, blank=True)
	nps_margin_error_lower = models.FloatField(null=True, blank=True, validators=[MinValueValidator(-100), MaxValueValidator(100)])
	nps_margin_error_upper = models.FloatField(null=True, blank=True, validators=[MinValueValidator(-100), MaxValueValidator(100)])
	nps_meaningful_data = models.BooleanField(default=False)
	
	umux_score = models.FloatField(null=True, blank=True)
	umux_score_category = models.ForeignKey(UmuxScoreCategory, related_name='project_snapshot_umux_score_category', null=True, blank=True, on_delete=models.SET_NULL)
	umux_score_date = models.DateTimeField(null=True, blank=True)
	umux_count = models.PositiveIntegerField(null=True, blank=True)
	umux_scores_sum = models.FloatField(null=True, blank=True)
	umux_capability_avg = models.FloatField(null=True, blank=True)
	umux_ease_of_use_avg = models.FloatField(null=True, blank=True)
	umux_margin_error = models.FloatField(null=True, blank=True)
	umux_margin_error_lower = models.FloatField(null=True, blank=True)
	umux_margin_error_upper = models.FloatField(null=True, blank=True)
	umux_meaningful_data = models.BooleanField(default=False)
	
	goal_completed_percent = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
	goal_completed_category = models.ForeignKey(GoalCompletedCategory, related_name='project_snapshot_goal_completed_category', null=True, blank=True, on_delete=models.SET_NULL)
	goal_completed_date = models.DateTimeField(null=True, blank=True)
	goal_completed_count = models.PositiveIntegerField(null=True, blank=True)
	response_day_range = models.PositiveIntegerField(null=True, blank=True)
	meaningful_response_count = models.PositiveIntegerField(null=True, blank=True)
	
	class Meta:
		ordering = ['project', '-date']
		
	def __str__(self):
		if self.date:
			showDate = self.date
		else:
			showDate = 'Last 90'
		
		return f'{self.project.name} : {showDate}'
		
		
	def save(self, *args, **kwargs):
		# If it's a new snapshot, check if one already exists for the project time period.
		if not self.id:
			# Checks for 90day one. Special because there's no date.
			# Then check for quarter.
			# Then check for month.
			if self.date_period == 'last90' and ProjectSnapshot.objects.filter(project=self.project, date_period='last90').exists():
				return 'A "last 90 days" snapshot already exists for this project. Edit it from the list of snapshots.'
			elif self.date_period == 'quarter' and self.date and ProjectSnapshot.objects.filter(project=self.project, date_period='quarter', date__year=self.date.year, date_quarter=pd.Timestamp(self.date).quarter).exists():
				return 'A snapshot already exists for this quarter. Edit it from the list of snapshots.'
			elif self.date_period == 'month' and self.date and ProjectSnapshot.objects.filter(project=self.project, date_period='month', date__year=self.date.year, date__month=pd.Timestamp(self.date).month).exists():
				return 'A snapshot already exists for this month. Edit it from the list of snapshots.'
		
		super(ProjectSnapshot, self).save(*args, **kwargs)
	
	
	def setNpsMeaningfulDataFlag(self):
		'''
		Centralized function with logic to determine if Snapshot has enough responses to be "meaningful".
		Return: null
		'''
		try:
			if self.nps_count >= 30 and self.nps_margin_error <= 16:
				self.nps_meaningful_data = True
			else:
				self.nps_meaningful_data = False
		except Exception as ex:
			pass
		
	
	def setUmuxMeaningfulDataFlag(self):
		'''
		Centralized function with logic to determine if Snapshot has enough responses to be "meaningful".
		Return: null
		'''
		try:
			if self.umux_count >= 30 and self.umux_margin_error <= 7:
				self.umux_meaningful_data = True
			else:
				self.umux_meaningful_data = False
		except Exception as ex:
			pass
	
		
	def setMeaningfulDataFlags(self):
		'''
		Convenience function grouping. Called from calculateStats and manualEntryCalculateAndSave.
		Return: null
		'''
		self.setNpsMeaningfulDataFlag()
		self.setUmuxMeaningfulDataFlag()
		
		
	def calculateStats(self, responses):
		'''
		Do some calculations and counts and store them.
		ONLY used by "updateQuarter/Month/last90" which is only used by automated script
		because it requires responses to do calculations.
		Return: null
		'''
		# Get counts of NPS promoters, passive, detractors and total NPS respnoses.
		npsCounts = helpers.getVoteResponsesNpsCounts(responses)
		
		self.nps_promoter_count = npsCounts['promoter']
		self.nps_passive_count = npsCounts['passive']
		self.nps_detractor_count = npsCounts['detractor']
		
		try:
			self.nps_count = npsCounts['total']
		except Exception as ex:
			self.nps_count = None
			
		# Now calculate actual NPS.
		try:
			self.nps_score = round(helpers.calculateAverageNps(self.nps_count, self.nps_promoter_count, self.nps_detractor_count), 4)
		except Exception as ex:
			self.nps_score = None
		
		# Count UMUX scores, total and Average UMUX score (each response already has 'score' (%), so just straight avg them)
		try:
			self.umux_count = responses.filter(umux_score__isnull=False).count()
		except Exception as ex:
			self.umux_count = None
		
		try:
			self.umux_scores_sum = round(responses.filter(umux_score__isnull=False).all().values('umux_score').aggregate(Sum('umux_score'))['umux_score__sum'], 4)
		except Exception as ex:
			self.umux_scores_sum = None
		
		try:
			# Faster instead of new query using Avg()
			self.umux_score = round(responses.filter(umux_score__isnull=False).all().values('umux_score').aggregate(Avg('umux_score'))['umux_score__avg'], 4)
		except Exception as ex:
			self.umux_score = None
			
		try:
			self.umux_capability_avg = round(responses.filter(umux_capability__isnull=False).all().values('umux_capability').aggregate(Avg('umux_capability'))['umux_capability__avg'], 4)
		except Exception as ex:
			self.umux_capability_avg = None
		
		try:
			self.umux_ease_of_use_avg = round(responses.filter(umux_ease_of_use__isnull=False).all().values('umux_ease_of_use').aggregate(Avg('umux_ease_of_use'))['umux_ease_of_use__avg'], 4)
		except Exception as ex:
			self.umux_capability_avg = None
		
		# Average goal completed %.
		try:
			self.goal_completed_count = responses.filter(goal_completed__isnull=False).count()
		except Exception as ex:
			self.goal_completed_count = None
			
		try:
			self.goal_completed_percent = round(((responses.filter(goal_completed__name__iexact='yes').count()) / responses.exclude(goal_completed=None).count()) * 100, 4)
			
			# Store the category so we don't have to look it up on every page view.
			roundedGoal = round(self.goal_completed_percent, 0)
			self.goal_completed_category = GoalCompletedCategory.objects.get(min_score_range__lte=roundedGoal, max_score_range__gte=roundedGoal)	
		except Exception as ex:
			self.goal_completed_percent = None
		
		# NPS margin of error
		if self.nps_score:
			npsMargins = self.calculateNpsErrorMargin()
			if npsMargins:
				self.nps_margin_error = round(npsMargins['errorMargin'], 4)
				self.nps_margin_error_lower = round(npsMargins['errorMarginLower'], 4)
				self.nps_margin_error_upper = round(npsMargins['errorMarginUpper'], 4)	

			# Store the category of NPS so we don't have to look it up on every page view.
			self.nps_score_category = NpsScoreCategory.getCategory(self.nps_score)
			
		# UMUX margin of error
		if self.umux_score:
			umuxMargins = self.calculateUmuxErrorMargin(responses)
			if umuxMargins:
				try:
					self.umux_margin_error = round(umuxMargins['errorMargin'], 4)
					self.umux_margin_error_lower = round(umuxMargins['errorMarginLower'], 4)
					self.umux_margin_error_upper = round(umuxMargins['errorMarginUpper'], 4)
				except:
					pass

			# Store the category UMUX score so we don't have to look it up on every page view.
			roundedUmux = round(self.umux_score, 1)
			self.umux_score_category = UmuxScoreCategory.objects.get(min_score_range__lte=roundedUmux, max_score_range__gte=roundedUmux)
	
		self.setMeaningfulDataFlags()
		
		# Count responses that are meaningful (have a score/response for something.)
		self.meaningful_response_count = responses.filter(Q(goal_completed__isnull=False) | Q(umux_ease_of_use__isnull=False) | Q(nps__isnull=False)).count()
		
		# Save this snapshot
		self.updated_by = getImportScriptUser()


	def manualEntryCalculateAndSave(self):
		'''
		Do some calculations and counts and store them.
		ONLY used by manual editing of snapshot.
		Return: null
		'''
		# NPS margin of error
		if self.nps_score and self.nps_margin_error:
			self.nps_margin_error_upper = self.nps_score + self.nps_margin_error
			self.nps_margin_error_lower = self.nps_score - self.nps_margin_error

			if self.nps_margin_error_upper >= 100:
				self.nps_margin_error_upper = 100
			
			if self.nps_margin_error_lower <= -100:
				self.nps_margin_error_lower = -100

			# Store the category of NPS so we don't have to look it up on every page view.
			self.nps_score_category = NpsScoreCategory.getCategory(self.nps_score)
			
		# UMUX margin of error
		if self.umux_score and self.umux_margin_error:
			self.umux_margin_error_upper = self.umux_score + self.umux_margin_error
			self.umux_margin_error_lower = self.umux_score - self.umux_margin_error

			# Store the category UMUX score so we don't have to look it up on every page view.
			roundedUmux = round(self.umux_score, 1)
			self.umux_score_category = UmuxScoreCategory.objects.get(min_score_range__lte=roundedUmux, max_score_range__gte=roundedUmux)
	
		# Goal completed category.
		if self.goal_completed_percent:
			roundedGoal = round(self.goal_completed_percent, 0)
			self.goal_completed_category = GoalCompletedCategory.objects.get(min_score_range__lte=roundedGoal, max_score_range__gte=roundedGoal)
			
		# Set the quarter based on the date they chose.
		if self.date:
			self.date_quarter = pd.Timestamp(self.date).quarter
			
		if self.date:
			scoreDate = timezone.make_aware(datetime(self.date.year, self.date.month, self.date.day))
			if self.nps_score:
				self.nps_score_date = scoreDate
	
			if self.umux_score:
				self.umux_score_date = scoreDate
	
			if self.goal_completed_percent:
				self.goal_completed_date = scoreDate
				
		self.setMeaningfulDataFlags()
		
		# Save this snapshot
		self.save()


	def calculateNpsErrorMargin(self):
		'''
		Calculate and return NPS MOE numbers for this snapshot.
		Formula from spreadsheet:
			MOE: ((((1-npsScore/100)^2*(promoterPercent)+(0-npsScore/100)^2*(passivePercent)+(-1-npsScore/100)^2*(detractorPercent))^0.5)/((totalNpsCount)^0.5))*100*1.64
			Upper:
				100 if (I11+E16)>=100 else I11+E16
			Lower:
				-100 if (I11-E16)<=-100 else I11-E16
		Return: {obj} NPS MOE data for this snapshot.
		'''
		# Legend for above XLS cells:
		#   I5:  Total NPS count
		#   I11: NPS
		#   I2:  Promoters %
		#   I3:  Detractors %
		#   I4:  Passive %
		totalNpsCount = self.nps_count
		
		try:
			promoterPercentDecimal = self.nps_promoter_count / totalNpsCount
			detractorPercentDecimal = self.nps_detractor_count / totalNpsCount
			passivePercentDecimal = self.nps_passive_count / totalNpsCount
			npsScore = (promoterPercentDecimal * 100) - (detractorPercentDecimal * 100)
			
			errorMargin = ((((1-npsScore/100)**2*(promoterPercentDecimal)+(0-npsScore/100)**2*(passivePercentDecimal)+(-1-npsScore/100)**2*(detractorPercentDecimal))**0.5)/((totalNpsCount)**0.5))*100*1.64
			rangeUpper = 100 if (npsScore + errorMargin)>=100 else npsScore + errorMargin
			rangeLower = -100 if (npsScore - errorMargin)<=-100 else npsScore - errorMargin
			
			return {
				'npsScore': npsScore,
				'errorMargin': errorMargin,
				'errorMarginUpper': rangeUpper,
				'errorMarginLower': rangeLower
			}
		except Exception as ex:
			return None


	def calculateUmuxErrorMargin(self, responses):
		'''
		Calculate and return UMUX MOE numbers for this snapshot.
		Formula from spreadsheet:
			MOE: ((STDEV.S(F:F))*1.64)/(SQRT(UMUXListResponses))
			Upper: Just add margin
			Lower: Just subtract margin
		Return: {obj} UMUX MOE data for this snapshot.
		'''
		umuxScoresArray = responses.filter(umux_score__isnull=False).values_list('umux_score', flat=True)
		
		try:
			errorMargin = ((numpy.std(umuxScoresArray, ddof=1))*1.64)/(numpy.sqrt(self.umux_count))
			rangeUpper = self.umux_score + errorMargin
			rangeLower = self.umux_score - errorMargin
			
			return {
				'umuxScore': self.umux_score,
				'errorMargin': errorMargin,
				'errorMarginUpper': rangeUpper,
				'errorMarginLower': rangeLower
			}
		except Exception as ex:
			return None

	
	def getVoteResponses(self):
		'''
		Return: {queryset} Responses for to this snapshot quarter/month/last90 days ago.
		'''
		try:
			responses = self.project.getVoteResponses()
			
			if self.date_period == 'quarter':
				return responses.filter(date__year=self.date.year, date__quarter=self.date_quarter)
			elif self.date_period == 'month':
				return responses.filter(date__year=self.date.year, date__month=self.date.month)
			elif self.date_period == 'last90':
				return responses.filter(date__gte=helpers.getDaysAgo(self.response_day_range))
			elif self.date_period == 'custom':
				return responses.filter(date__gte=self.date-timedelta(days=self.response_day_range), date__lte=self.date)
		except Exception as ex:
			return None
	
	
	@staticmethod
	def getCoreCurrentlyReportingProjectSnapshots(domain=None, keyword=None):
		'''
		Used for metrics home dashboard.
		Return: {queryset} Core projects currently reporting's snapshots, optionally domain filtered.
		'''
		conditions = {
			'project_latest_valid_currently_reporting_snapshot__isnull': False,
			'project__inactive': False,
		}
		
		# For domain, we auto-filter for core project.
		# For keyword, it's a custom list so don't filter by core projects.
		if domain:
			conditions['project__domain'] = domain
			conditions['project__core_project']: True
		elif keyword:
			conditions['project__keywords'] = keyword
		
		try:
			projectSnapshots = ProjectSnapshot.objects.filter(**conditions)
		except Exception as ex:
			projectSnapshots = None
			
		return projectSnapshots
	
	
	@staticmethod
	def getFilteredSet(tileFiltersData, projects):
		'''
		Convenience method for project tiles page.
		Return: {queryset} Snapshots for given projects, using given filter data.
		'''
		def addYearSettings(snapshots):
			for snapshot in snapshots:
				if 'q' in timePeriod:
					timePeriodYear = timePeriod.split('q')[1]
					try:
						snapshot.project.timePeriodSettings = ProjectYearSetting.objects.get(project=snapshot.project, year=timePeriodYear)
					except Exception as ex:
						snapshot.project.timePeriodSettings = None
				else:
					snapshot.project.timePeriodSettings = snapshot.project.current_year_settings
					
			return snapshots
	
	
		def onlyMeetingNpsTarget(snapshots):
			snapshots = addYearSettings(projectSnapshots)
			
			for snapshot in snapshots:
				try:
					npsTarget = snapshot.project.timePeriodSettings.nps_target
				except:
					npsTarget = None
			
				if not(npsTarget and (snapshot.nps_score > npsTarget or snapshot.nps_score >= 26)):
					snapshots = snapshots.exclude(id=snapshot.id)
					
			return snapshots
	
	
		def onlyMeetingUmuxTarget(snapshots):
			snapshots = addYearSettings(projectSnapshots)
			
			for snapshot in snapshots:
				try:
					umuxTarget = snapshot.project.timePeriodSettings.umux_target
				except:
					umuxTarget = None
			
				if not(umuxTarget and (snapshot.umux_score > umuxTarget or snapshot.umux_score >= 74)):
					snapshots = snapshots.exclude(id=snapshot.id)
					
			return snapshots
		
		
		def onlyExceedingNpsTarget(snapshots):
			snapshots = addYearSettings(projectSnapshots)
			
			for snapshot in snapshots:
				try:
					npsTarget = snapshot.project.timePeriodSettings.nps_target_exceed
				except:
					npsTarget = None
			
				if not(npsTarget and (snapshot.nps_score > npsTarget or snapshot.nps_score >= 41)):
					snapshots = snapshots.exclude(id=snapshot.id)
					
			return snapshots
	
	
		def onlyExceedingUmuxTarget(snapshots):
			snapshots = addYearSettings(projectSnapshots)
			
			for snapshot in snapshots:
				try:
					umuxTarget = snapshot.project.timePeriodSettings.umux_target_exceed
				except:
					umuxTarget = None
			
				if not(umuxTarget and (snapshot.umux_score > umuxTarget or snapshot.umux_score >= 84)):
					snapshots = snapshots.exclude(id=snapshot.id)
					
			return snapshots
		
		
		timePeriod = tileFiltersData['selectedReportPeriod']
		showField = tileFiltersData['selectedShowData']
		
		# Get current reporting snapshots that have requested value.
		# Fall back to last90 if none available or bad URL param value.	
		snapshotArgsLast90 = {
			'project_currently_reporting_snapshot__isnull': False,
			'{}__isnull'.format(showField): False,
			'project__in': projects
		}
		
		try:
			if timePeriod == 'last90':
				snapshotArgs = snapshotArgsLast90
			else:
				quarterYear = timePeriod.split('q')
				snapshotArgs = {
					'date_period': 'quarter',
					'date__year': int(quarterYear[1]),
					'date_quarter': int(quarterYear[0]),
					'{}__isnull'.format(showField): False,
					'project__in': projects
				}
		except Exception as ex:
			timePeriod = 'last90'
			snapshotArgs = snapshotArgsLast90
			
		
		# If they filtered by any of the score categories, setup queries for those ('or's).
		npsCategoryQueries = Q()
		if tileFiltersData['selectedNpsCats']:
			snapshotArgs['nps_meaningful_data'] = True
			npsCategoryQueries = reduce(or_, (Q(nps_score_category=x) for x in tileFiltersData['selectedNpsCats']))
		
		umuxCategoryQueries = Q()
		if tileFiltersData['selectedUmuxCats']:
			snapshotArgs['umux_meaningful_data'] = True
			umuxCategoryQueries = reduce(or_, (Q(umux_score_category=x) for x in tileFiltersData['selectedUmuxCats']))
		
		goalCategoryQueries = Q()
		if tileFiltersData['selectedGoalCats']:
			goalCategoryQueries = reduce(or_, (Q(goal_completed_category=x) for x in tileFiltersData['selectedGoalCats']))
		
		
		# If they filtered by achieving/exceeing NPS or umux target, add queries required for those.
		if tileFiltersData['selectedMeetingNpsTarget'] == 'y' or tileFiltersData['selectedExceedingNpsTarget'] == 'y':
			snapshotArgs['nps_meaningful_data'] = True
			snapshotArgs['nps_score__isnull'] = False
			
		if tileFiltersData['selectedMeetingUmuxTarget'] == 'y' or tileFiltersData['selectedExceedingUmuxTarget'] == 'y':
			snapshotArgs['umux_meaningful_data'] = True
			snapshotArgs['umux_score__isnull'] = False
			
		
		# Get all snapshots based on filter criteria above except the 'OR'
		try:
			projectSnapshots = ProjectSnapshot.objects.filter(npsCategoryQueries, umuxCategoryQueries, goalCategoryQueries, **snapshotArgs).order_by(Lower('project__name')).select_related('project', 'project__current_year_settings', 'project__domain', 'project__contact__profile', 'nps_score_category', 'umux_score_category', 'goal_completed_category')
		except:
			projectSnapshots = None
		
		
		# We need to manually filter snapshots if they used this filter.
		# Because we need to first get the proper timeperiod setting to compare to.
		# Ya this f'ing sucks, but it's fast and it's the only way, so it's OK.
		if tileFiltersData['selectedMeetingNpsTarget'] == 'y':
			projectSnapshots = onlyMeetingNpsTarget(projectSnapshots)	
		
		if tileFiltersData['selectedMeetingUmuxTarget'] == 'y':
			projectSnapshots = onlyMeetingUmuxTarget(projectSnapshots)	
		
		if tileFiltersData['selectedExceedingNpsTarget'] == 'y':
			projectSnapshots = onlyExceedingNpsTarget(projectSnapshots)	
		
		if tileFiltersData['selectedExceedingUmuxTarget'] == 'y':
			projectSnapshots = onlyExceedingUmuxTarget(projectSnapshots)	
		
		# Add the year settings to the objects so we can display targets and if they are above/below.
		projectSnapshots = addYearSettings(projectSnapshots)
		
		# Add high MOE warning messages.
		for projectSnapshot in projectSnapshots:
			if projectSnapshot.nps_margin_error and projectSnapshot.nps_margin_error >= 13 and projectSnapshot.nps_margin_error <= 17:
				projectSnapshot.npsMoeWarning = 'It is recommended that you increase your sample size to try and reduce your margin of error to below 13'
			
			if projectSnapshot.umux_margin_error and projectSnapshot.umux_margin_error >= 5 and projectSnapshot.umux_margin_error <= 7:
				projectSnapshot.umuxMoeWarning = 'It is recommended that you increase your sample size to try and reduce your margin of error to below 5'
				
		return projectSnapshots
		
		
	@staticmethod
	def hasMeaningfulNps(responses):
		'''
		Return: {bool} Does NPS calc and determines if given responses generate a meaningful NPS.
		'''
		npsCounts = helpers.getVoteResponsesNpsCounts(responses)
		tempSnapshot = ProjectSnapshot()
		tempSnapshot.nps_promoter_count = npsCounts['promoter']
		tempSnapshot.nps_detractor_count = npsCounts['detractor']
		tempSnapshot.nps_passive_count = npsCounts['passive']
		tempSnapshot.nps_count = npsCounts['total']
		moe = tempSnapshot.calculateNpsErrorMargin()
		
		tempSnapshot = None
		
		if npsCounts['total'] >= 30 and moe['errorMargin'] <= 16:
			return True
		else:
			return False
			
		
	@staticmethod	
	def getExcellentNpsHistoricalChartData():
		'''
		Used on metrics home page.
		For each quarter in the given date range, sum NPS/UMUX/Goal completion response counts across given projects.
		Return: {obj} Labels and data to generate historical line chart with total quarterly response counts.
		'''
		npsHistoryChartData = {}
		
		startdate = timezone.now() - timedelta(days=365)
		pidx = pd.date_range(start=startdate, end=timezone.now(), freq='M')
		
		for period in pidx:
			periodSnapshots = ProjectSnapshot.objects.filter(date_period='month', date__year=period.year, date__month=period.month, nps_meaningful_data=True).filter(Q(nps_score_category__name='Excellent') | Q(nps_score_category__name='Very good')).select_related('project')
			npsExcellentCount = periodSnapshots.count()
			npsCoreExcellentCount = periodSnapshots.filter(project__core_project=True).count()
			
			npsHistoryChartData[f'{period.month}M{str(period.year)[-2:]}'] = [
				npsCoreExcellentCount, npsExcellentCount
			]
			
			# .append({
			# 	'label': f'{period.month}M{str(period.year)[-2:]}',
			# 	'All projects': npsExcellentCount,
			# 	'Priority 1-3 projects': npsCoreExcellentCount,
			# })
		
		manualProjectsPastYear = Project.objects.filter(
			project_snapshot_project__date_period='quarter',
			project_snapshot_project__entry_type='manual',
			project_snapshot_project__date__gte=startdate).order_by('name').only('core_project').distinct()
			
		snapshots = ProjectSnapshot.objects.filter(
			date__gte=(startdate-timedelta(days=365)),
			entry_type='manual',
			nps_meaningful_data=True,
			project__in=manualProjectsPastYear).only('nps_score_category')
			
		npsCategoriesIds = list(NpsScoreCategory.objects.filter(Q(name='Excellent') | Q(name='Very good')).values_list('id', flat=True))
		
		# Loop thru quarters
		# For each project if there's a snapshot, use it for the quarter's three months.
		# Else traverse back a quarter to see if one exists, up to 3 quarters back.
		pidx = pd.date_range(start=startdate, end=timezone.now()+timedelta(days=92), freq='Q')

		for period in pidx:
			for project in manualProjectsPastYear:
				# Try and find a valid quarter snapshot for this quarter, 
				#  then traversing up to 3 quarters back (1 yr total)
				# 583q, 450ms, 17s
				quarterSnapshot = None
				
				try:
					quarterSnapshot = snapshots.filter(project=project, date__lte=period).first()
				except:
					pass
				
				#print(f'{period.quarter}Q{period.year} - {project} - {quarterSnapshot}')
				
				if quarterSnapshot:
					if quarterSnapshot.nps_score_category_id in npsCategoriesIds:
						month1 = (period.quarter * 3) - 2
						try:
							dataItemM1 = npsHistoryChartData[f'{month1}M{str(period.year)[-2:]}']
							if project.core_project:
								dataItemM1[0] = dataItemM1[0]+1
							dataItemM1[1] = dataItemM1[1]+1
						except:
							pass
						try:
							dataItemM2 = npsHistoryChartData[f'{month1+1}M{str(period.year)[-2:]}']
							if project.core_project:
								dataItemM2[0] = dataItemM2[0]+1
							dataItemM2[1] = dataItemM2[1]+1
						except:
							pass
						try:
							dataItemM3 = npsHistoryChartData[f'{month1+2}M{str(period.year)[-2:]}']
							if project.core_project:
								dataItemM3[0] = dataItemM3[0]+1
							dataItemM3[1] = dataItemM3[1]+1
						except:
							pass
							
		npsDataAsArray = []
		
		for key in npsHistoryChartData:
			npsDataAsArray.append({
				'label': key,
				'All projects': npsHistoryChartData[key][1], 
				'Priority 1-3 projects': npsHistoryChartData[key][0]
			})
			
		return npsDataAsArray
		
		
	@staticmethod
	def getHistoricalNpsCatCountChartData():
		'''
		Used on metrics home page at bottom. 2-yr history of NPS catrgories response counts by quarter.
		'''
		npsCatData = []
		npsCategories = list(NpsScoreCategory.objects.all().values('id', 'name'))
		allMeaninfulQuarterSnapshots = ProjectSnapshot.objects.filter(date_period='quarter', nps_meaningful_data=True, project__inactive=False)
		
		startdate = timezone.now() - timedelta(days=731)
		pidx = pd.date_range(start=startdate, end=timezone.now(), freq='Q')
		for period in pidx:
			yr = f'{period.year}'[2:]
			
			quarterData = {'label': f'{period.quarter}Q{yr}',}
			
			quarterSnapshots = allMeaninfulQuarterSnapshots.filter(date__year=period.year, date__quarter=period.quarter)
			
			quarterSnapshotsCount = quarterSnapshots.count()
			
			for cat in npsCategories:
				try:
					quarterData[cat['name']] = round(quarterSnapshots.filter(nps_score_category=cat['id']).count() / quarterSnapshotsCount * 100)
				except:
					quarterData[cat['name']] = 0
				
			npsCatData.append(quarterData)
			
		return npsCatData
			

class ImportLog(models.Model):
	date = models.DateTimeField(db_index=True, auto_now_add=True)
	responses_imported_count = models.PositiveIntegerField(null=True, blank=True)
	projects_affected_count = models.PositiveIntegerField(null=True, blank=True)
	run_time_seconds = models.FloatField()
	import_type = models.CharField(choices=[
			('usabilla','Usabilla'),
		], max_length=12)
	user = models.ForeignKey(User, related_name='usabilla_import_log_user', null=True, blank=True, on_delete=models.SET_NULL)
	
	class Meta:
		ordering = ['-date']
		
	def __str__(self):
		return f'{self.date} : {self.responses_imported_count}'
		

class ProjectYearSetting(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	created_by = models.ForeignKey(User, related_name='project_year_setting_created_by', on_delete=models.PROTECT)
	updated_at = models.DateTimeField(auto_now=True)
	updated_by = models.ForeignKey(User, related_name='project_year_setting_updated_by', on_delete=models.PROTECT)
	project = models.ForeignKey(Project, related_name='project_year_setting_project', on_delete=models.CASCADE)
	year = models.PositiveIntegerField(default=timezone.now().year)
	# NPS fields
	nps_target = models.FloatField(null=True, blank=True, validators=[MinValueValidator(-100), MaxValueValidator(100)])
	nps_target_exceed = models.FloatField(null=True, blank=True, validators=[MinValueValidator(-100), MaxValueValidator(100)])
	nps_baseline = models.FloatField(verbose_name='NPS baseline', null=True, blank=True, validators=[MinValueValidator(-100), MaxValueValidator(100)])
	nps_baseline_created_at = models.DateTimeField(verbose_name='NPS baseline created at', null=True, blank=True)
	nps_baseline_response_count = models.PositiveIntegerField(verbose_name='NPS baseline reponse count', null=True, blank=True)
	nps_baseline_margin_error = models.FloatField(verbose_name='NPS baseline MOE', null=True, blank=True)
	nps_baseline_entry_type = models.CharField(choices=[
		('automatic','Automatic'),
		('manual','Manual'),
	], max_length=12, blank=True)
	nps_baseline_score_category = models.ForeignKey(NpsScoreCategory, related_name='project_year_setting_nps_baseline_score_category', null=True, blank=True, on_delete=models.SET_NULL)
	nps_baseline_from = models.CharField(verbose_name='NPS baseline from', max_length=64, blank=True)
	nps_baseline_last_response_at = models.DateTimeField(verbose_name='NPS baseline last response', null=True, blank=True)
	nps_baseline_response_day_range = models.PositiveIntegerField(null=True, blank=True)
	nps_baseline_notes = models.TextField(verbose_name='NPS baseline notes', blank=True)
	# UMUX fields
	umux_target = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
	umux_target_exceed = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
	umux_baseline = models.FloatField(verbose_name='UMUX baseline', null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
	umux_baseline_created_at = models.DateTimeField(verbose_name='UMUX baseline created at', null=True, blank=True)
	umux_baseline_response_count = models.PositiveIntegerField(verbose_name='UMUX baseline reponse count', null=True, blank=True)
	umux_baseline_margin_error = models.FloatField(verbose_name='UMUX baseline MOE', null=True, blank=True)
	umux_baseline_entry_type = models.CharField(choices=[
		('automatic','Automatic'),
		('manual','Manual'),
	], max_length=12, blank=True)
	umux_baseline_score_category = models.ForeignKey(UmuxScoreCategory, related_name='project_year_setting_umux_baseline_score_category', null=True, blank=True, on_delete=models.SET_NULL)
	umux_baseline_from = models.CharField(verbose_name='UMUX baseline from', max_length=64, blank=True)
	umux_baseline_last_response_at = models.DateTimeField(verbose_name='UMUX baseline last response', null=True, blank=True)
	umux_baseline_response_day_range = models.PositiveIntegerField(null=True, blank=True)
	umux_baseline_notes = models.TextField(verbose_name='UMUX baseline notes', blank=True)
		
	class Meta:
		ordering = ['-year', 'project',]
		
	def __str__(self):
		return f'{str(self.year)} - {self.project.name}'


	def save(self, *args, **kwargs):
		'''
		Logging. 
		Check if baselines we're about to save are different. If so, set baseline date and log.
		'''
		# Need to check if NPS and UMUX baselines changed, and grab old value before we save the new one.
		try:
			oldNpsBaseline = ProjectYearSetting.objects.get(id=self.id).nps_baseline
			if oldNpsBaseline != self.nps_baseline:
				self.nps_baseline_created_at = timezone.now()
			else:				
				oldNpsBaseline = None 
		except Exception as ex:
			oldNpsBaseline = None 
		
		try:
			oldUmuxBaseline = ProjectYearSetting.objects.get(id=self.id).umux_baseline
			if oldUmuxBaseline != self.umux_baseline:
				self.umux_baseline_created_at = timezone.now()
			else:
				oldUmuxBaseline = None 
		except Exception as ex:
			oldUmuxBaseline = None 
		
		# Save so we can get the user who updated it for the logs below.
		super(ProjectYearSetting, self).save(*args, **kwargs)
		
		# IF BASELINE CHANGED, LOG IT.
		# These are done on Save because it could be set by daily import, 
		#   or manual admin editing of doc in Admin Center, so we can't do 
		#   the log in the 'set___baseline' method.
		newSelf = self
		if oldNpsBaseline:
			try:
				changeEntry = ActivityLog.objects.create(
					user = newSelf.updated_by,
					content_object = newSelf,
					comments = f'NPS baseline changed from {oldNpsBaseline} to {newSelf.nps_baseline}'
				)
			except Exception as ex:
				print(str(ex))
				
		if oldUmuxBaseline:
			try:
				changeEntry = ActivityLog.objects.create(
					user = newSelf.updated_by,
					content_object = newSelf,
					comments = f'UMUX baseline changed from {oldUmuxBaseline} to {newSelf.umux_baseline}'
				)
			except Exception as ex:
				print(str(ex))
				
		
	def calculateTargets(self, *args, **kwargs):
		'''
		Calculate NPS targets, set baseline category.
		Calculate UMUX targets, set baseline category.
		Return: null
		'''
		# NPS target calc.
		if self.nps_baseline:
			self.nps_target = self.calculateNpsTarget()
			self.nps_target_exceed = self.calculateNpsTargetExceed()
			self.nps_baseline_score_category = NpsScoreCategory.getCategory(self.nps_baseline)
			
		# UMUX target calc.
		if self.umux_baseline:
			self.umux_target = self.calculateUmuxTarget()
			self.umux_target_exceed = self.calculateUmuxTargetExceed()
			self.umux_baseline_score_category = UmuxScoreCategory.getCategory(self.umux_baseline)

	def calculateNpsTarget(self):
		'''
		Force the baseline to have decimal and find the closest INT entry below the baseline.
		Else, get the lowest one because it's too low and there's nothing below it.
		We round it to normalize to display value first, to prevent case:
		  baseline = 26.98. Displays as 27, target would be 26 (int of 26.98)
		Return: {int} 'Achieve' Target for this project year setting's NPS baseline.
		'''
		target = None
		
		if self.nps_baseline:
			adjustedBase = round(self.nps_baseline, 1) + .00001
			
			try:
				target = Target.objects.filter(nps_score__isnull=False, nps_score__lte=adjustedBase).order_by('-nps_score').values('achieve_target').first()['achieve_target']
			except Exception as ex:
				target = Target.objects.filter(nps_score__isnull=False).order_by('nps_score').values('achieve_target').first()['achieve_target']
		
		return target
		
		
	def calculateNpsTargetExceed(self):
		'''
		Force the baseline to have decimal and find the closest INT entry below the baseline.
		Else, get the lowest one because it's too low and there's nothing below it.
		We round it to normalize to display value first, to prevent case:
		  baseline = 26.98. Displays as 27, target would be 26 (int of 26.98)
		Return: {int} 'Exceed' Target for this project year setting's NPS baseline.
		'''
		target = None
		
		if self.nps_baseline:
			adjustedBase = round(self.nps_baseline, 1) + .00001
			
			try:
				target = Target.objects.filter(nps_score__isnull=False, nps_score__lte=adjustedBase).order_by('-nps_score').values('exceed_target').first()['exceed_target']
			except Exception as ex:
				target = Target.objects.filter(nps_score__isnull=False).order_by('nps_score').values('exceed_target').first()['exceed_target']
		
		return target
		
		
	def calculateUmuxTarget(self):
		'''
		Force the baseline to have decimal and find the closest INT entry below the baseline.
		Else, get the lowest one because it's too low and there's nothing below it.
		We round it to normalize to display value first, to prevent case:
		  baseline = 26.98. Displays as 27, target would be 26 (int of 26.98)
		Return: {int} 'Achieve' Target for this project year setting's UMUX baseline.
		'''
		target = None
		
		if self.umux_baseline:
			adjustedBase = round(self.umux_baseline, 1) + .00001
			
			try:
				target = Target.objects.filter(umux_score__isnull=False, umux_score__lte=adjustedBase).order_by('-umux_score').values('achieve_target').first()['achieve_target']
			except Exception as ex:
				target = Target.objects.filter(umux_score__isnull=False).order_by('umux_score').values('achieve_target').first()['achieve_target']
		
		return target

	
	def calculateUmuxTargetExceed(self):
		'''
		Force the baseline to have decimal and find the closest INT entry below the baseline.
		Else, get the lowest one because it's too low and there's nothing below it.
		We round it to normalize to display value first, to prevent case:
		  baseline = 26.98. Displays as 27, target would be 26 (int of 26.98)
		Return: {int} 'Exceed' Target for this project year setting's UMUX baseline.
		'''
		target = None
		
		if self.umux_baseline:
			adjustedBase = round(self.umux_baseline, 1) + .00001
			
			try:
				target = Target.objects.filter(umux_score__isnull=False, umux_score__lte=self.umux_baseline).order_by('-umux_score').values('exceed_target').first()['exceed_target']
			except Exception as ex:
				target = Target.objects.filter(umux_score__isnull=False).order_by('umux_score').values('exceed_target').first()['exceed_target']
		
		return target


	def setNpsBaseline(self):
		'''
		Set NPS baseline #s for this project year setting if suitable snapshot is found.
		Admins can manually set a baseline so this is not done on Save. This is only for automated import.
		Only the target is done on Save because that contains a formula that is used to calc the target.
		Return: null
		'''
		# If the baseline is already set, or it's after July 15: Stop and do nothing.
		# Rule: No baseline allowed to be set after July 15.
		#if self.nps_baseline or timezone.now() > timezone.make_aware(datetime(timezone.now().year,7,15)):
		#	return
		
		# Fetch oldest to newest snapshots: Q4 $lastyear, Q1 & Q2 $thisyear, then last90.
		# If there's snapshots found, use the oldest one found from criteria.
		# Then set the snapshot's NPS baseline.
		baselineSnapshot = ProjectSnapshot.objects.filter(
			((Q(date__year=self.year-1, date_quarter=4) | Q(date__year=self.year)) & Q(date_period='quarter')) | Q(date_period='last90'), 
			nps_meaningful_data=True,
			project=self.project,
		).order_by('date').first()
		
		if baselineSnapshot:
			if baselineSnapshot.date_period == 'quarter':
				baselineFrom = f'{baselineSnapshot.date.year} Q{baselineSnapshot.date_quarter}'
			elif baselineSnapshot.date_period == 'last90':
				baselineFrom = 'last90'
			
			self.nps_baseline = baselineSnapshot.nps_score
			self.nps_baseline_created_at = timezone.now()
			self.nps_baseline_response_count = baselineSnapshot.nps_count
			self.nps_baseline_margin_error = baselineSnapshot.nps_margin_error
			self.nps_baseline_from = baselineFrom
			self.nps_baseline_entry_type = 'automatic'
			self.nps_baseline_response_day_range =  baselineSnapshot.response_day_range
			self.nps_baseline_last_response_at = baselineSnapshot.nps_score_date
			
				
	def setUmuxBaseline(self):
		'''
		Set UMUX baseline #s for this project year setting if suitable snapshot is found.
		Admins can manually set a baseline so this is not done on Save. This is only for automated import.
		Only the target is done on Save because that contains a formula that is used to calc the target.
		Return: null
		'''
		# If the baseline is already set, or it's after July 15: Stop and do nothing.
		# Rule: No baseline allowed to be set after July 15.
		if self.umux_baseline or timezone.now() > timezone.make_aware(datetime(timezone.now().year,7,15)):
			return
		
		# Fetch oldest to newest snapshots: Q4 $lastyear, Q1 & Q2 $thisyear, then last90.
		# If there's snapshots found, use the oldest one found from criteria.
		# Then set the snapshot's NPS baseline.
		baselineSnapshot = ProjectSnapshot.objects.filter(
			((Q(date__year=self.year-1, date_quarter=4) | Q(date__year=self.year)) & Q(date_period='quarter')) | Q(date_period='last90'), 
			umux_meaningful_data=True,
			project=self.project,
		).order_by('date').first()
		
		if baselineSnapshot:
			if baselineSnapshot.date_period == 'quarter':
				baselineFrom = f'{baselineSnapshot.date.year} Q{baselineSnapshot.date_quarter}'
			elif baselineSnapshot.date_period == 'last90':
				baselineFrom = 'last90'
			
			self.umux_baseline = baselineSnapshot.umux_score
			self.umux_baseline_created_at = timezone.now()
			self.umux_baseline_response_count = baselineSnapshot.umux_count
			self.umux_baseline_margin_error = baselineSnapshot.umux_margin_error
			self.umux_baseline_from = baselineFrom
			self.umux_baseline_entry_type = 'automatic'
			self.umux_baseline_response_day_range =  baselineSnapshot.response_day_range
			self.umux_baseline_last_response_at = baselineSnapshot.umux_score_date
			
	
class DomainYearSnapshot(models.Model):
	'''
	Terms:
	core projects = Have the core_project flag set (priority 1-3)
	vote_projects = Core with a "current" snapshot
	core_projects_currently_reporting = Core with a "current" snapshot that's "meaningful"
	'''
	created_at = models.DateTimeField(auto_now_add=True)
	created_by = models.ForeignKey(User, related_name='domain_year_snapshot_created_by', on_delete=models.PROTECT)
	updated_at = models.DateTimeField(auto_now=True)
	updated_by = models.ForeignKey(User, related_name='domain_year_snapshot_updated_by', on_delete=models.PROTECT)
	
	domain = models.ForeignKey(Domain, related_name='domain_year_snapshot_domain', on_delete=models.CASCADE)
	year = models.PositiveIntegerField(default=timezone.now().year)
	
	all_projects_count = models.PositiveIntegerField(default=0)
	core_projects_count = models.PositiveIntegerField(default=0)
	core_projects_percent = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
	vote_projects_count = models.PositiveIntegerField(default=0)
	vote_projects_percent = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
	core_projects_currently_reporting_count = models.PositiveIntegerField(default=0)
	core_projects_currently_reporting_percent = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
	core_projects_excellent_nps_count = models.PositiveIntegerField(default=0)
	core_projects_excellent_nps_percent = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
	core_projects_nps_target_achieved_count = models.PositiveIntegerField(default=0)
	core_projects_nps_target_achieved_percent = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
	core_projects_nps_score_points = models.PositiveIntegerField(default=0)
	core_projects_nps_score_points_average = models.FloatField(default=0)
	core_projects_nps_letter_grade = models.ForeignKey(NpsLetterGrade, related_name='domain_year_snapshot_core_projects_nps_letter_grade', null=True, blank=True, on_delete=models.SET_NULL)
	
	class Meta:
		ordering = ['-year', 'domain',]
		
	def __str__(self):
		return f'{str(self.year)} - {self.domain.name}'


class ActivityLog(models.Model):
	timestamp = models.DateTimeField(db_index=True, default=timezone.now)
	user = models.ForeignKey(User, related_name='instance_change_user', null=True, blank=True, on_delete=models.SET_NULL)
	content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE)
	object_id = models.PositiveIntegerField(null=True, blank=True)
	content_object = GenericForeignKey('content_type', 'object_id')
	comments = models.TextField(max_length=3000)
		
	class Meta:
		ordering = ['-timestamp']
		
	def __str__(self):
		return f'{self.timestamp} - {self.comments}'


class Target(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	nps_score = models.FloatField(null=True, blank=True, validators=[MinValueValidator(-100), MaxValueValidator(100)])
	umux_score = models.FloatField(null=True, blank=True)
	achieve_target = models.FloatField(null=True, blank=True)
	exceed_target = models.FloatField(null=True, blank=True)
	
	class Meta:
		ordering = ['-nps_score', '-umux_score']
		
	def __str__(self):
		return f'{self.timestamp} - {self.user}'


class Alert(models.Model):
	date = models.DateTimeField(default=timezone.now)
	project = models.ForeignKey(Project, related_name='alert_project', null=True, blank=True, on_delete=models.CASCADE)
	domain = models.ForeignKey(Domain, related_name='alert_domain', null=True, blank=True, on_delete=models.CASCADE)
	type = models.CharField(choices=[
		('Great', 'Great'),
		('Good', 'Good'),
		('Info', 'Info'),
		('Warning', 'Warning'),
		('Bad', 'Bad'),
		('Poop', 'Poop'),
	], max_length=8)
	comments = models.TextField(max_length=3000)
	
	class Meta:
		ordering = ['-date', 'domain', 'project',]
		
	def __str__(self):
		return f'{self.date} - {self.domain} - {self.project}'


	def doScheduledAlerts():
		'''
		Look for monthly and quarterly trends and log/email alerts found.
		Runs at 2am on the 1st of every month, via cron.
		'''
		quarterlyChangers = Project.getQuarterlyChangers()
		monthlyChangers = Project.getMonthlyChangers()
		
		for p in quarterlyChangers['decliners']:
			Alert.objects.create(
				project = p,
				domain = p.domain,
				type = 'Poop',
				comments = f'The NPS for ({p.name}) has declined the past two consecutive quarters.'
			)
			
			try:
				sendEmail({
					'subject': f'[Alexandria Metrics] NPS decline warning for {p.name}',
					'recipients': [p.contact.username],
					'message': f'<div style="font-family:sans-serif;font-size:14px;line-height:20px;"><p>The NPS for {p.name} has declined the past two consecutive quarters.',
				})
			except Exception as ex:
				pass
				
		for p in quarterlyChangers['increasers']:
			Alert.objects.create(
				project = p,
				domain = p.domain,
				type = 'Great',
				comments = f'The NPS for ({p.name}) has increased the past two consecutive quarters.'
			)
			
			try:
				sendEmail({
					'subject': f'[Alexandria Metrics] NPS increase for {p.name}',
					'recipients': [p.contact.username],
					'message': f'<div style="font-family:sans-serif;font-size:14px;line-height:20px;"><p>The NPS for {p.name} has increased the past two consecutive quarters.',
				})
			except Exception as ex:
				pass
	
		for p in monthlyChangers['decliners']:
			Alert.objects.create(
				project = p,
				domain = p.domain,
				type = 'Bad',
				comments = f'The NPS for ({p.name}) has declined the past three consecutive months.'
			)
			
			try:
				sendEmail({
					'subject': f'[Alexandria Metrics] NPS decline warning for {p.name}',
					'recipients': [p.contact.username],
					'message': f'<div style="font-family:sans-serif;font-size:14px;line-height:20px;"><p>The NPS for {p.name} has declined the past three consecutive months.</p>',
				})
			except Exception as ex:
				pass
				
		for p in monthlyChangers['increasers']:
			Alert.objects.create(
				project = p,
				domain = p.domain,
				type = 'Good',
				comments = f'The NPS for ({p.name}) has increased the past three consecutive months.'
			)
			
			try:
				sendEmail({
					'subject': f'[Alexandria Metrics] NPS increase for {p.name}',
					'recipients': [p.contact.username],
					'message': f'<div style="font-family:sans-serif;font-size:14px;line-height:20px;"><p>The NPS for {p.name} has increased the past three consecutive months.</p>',
				})
			except Exception as ex:
				pass

	
