import csv
import io
import os
import requests
import sys

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User

from django.db.models import Count, Value, Sum, Q
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils.text import capfirst

from djqscsv import render_to_csv_response

from metrics.models import *
from research.models import *
from info.models import *
from ..forms import *
from metrics.response_data_helpers import createCsvFromData, createCsvAndEmailFile, fetchNewUsabillaResponses, fetchNewBeeHeardResponses
import metrics.helpers as helpers
import metrics.access_helpers as accessHelpers


# OLD leaving until we know this is a good idea to switch to. 
def getAdminBreadcrumbBase():
	return []


def doCommonListView(request, model, listItems):
	thisModel = model
	newItemUrl = reverse(f'metrics:admin_{thisModel._meta.model_name}_add')
	templateName = f'metrics/admin_{thisModel._meta.model_name}_list.html'
	
	context = {
		'listItems': listItems,
		'modelMeta': thisModel._meta,
		'newItemUrl': newItemUrl
	}

	response = render(request, templateName, context)
	helpers.clearPageMessage(request)
	return response


def doCommonAddItemView(request, thisModel):
	thisModelForm = globals()[thisModel._meta.object_name + 'Form']
	thisViewTemplate = 'admin_common_add.html'
	adminTemplate = 'metrics/page_template_admin.html'
	thisModelListUrl = reverse(f'metrics:admin_{thisModel._meta.model_name}_list')
	
	breadcrumbs = getAdminBreadcrumbBase()
	breadcrumbs.append(
		{
			'text': capfirst(thisModel._meta.verbose_name_plural),
			'url': thisModelListUrl
		}
	)

	context = {
		'breadcrumbs': breadcrumbs,
		'form': None,
		'modelMeta': thisModel._meta,
		'newItemName': thisModel._meta.verbose_name,
		'adminTemplate': adminTemplate,
	}

	if request.method == 'GET':
		form = thisModelForm()
		context['form'] = form

		response = render(request, thisViewTemplate, context)
		helpers.clearPageMessage(request)
		
	elif request.method == 'POST':
		form = thisModelForm(request.POST)
		context['form'] = form
		
		if form.is_valid():
			post = form.save(commit=False)
			post.created_by = request.user
			post.updated_by = request.user
			post.save()
			form.save_m2m()
			
			# If it's a success and they want JSON back, return the ID and label as JSON,
			#  otherwise we redirect to the list page with a message.
			if request.POST.get('returntype', None) == 'json':
				response = JsonResponse({
					'id': post.id,
					'name': post.__str__()
				}, status=200)
			else:
				helpers.setPageMessage(request, 'success', f'{capfirst(thisModel._meta.verbose_name)} was added successfully')
				response = redirect(thisModelListUrl)
		else:
			response = render(request, thisViewTemplate, context)
			
	return response
	
	
def doCommonEditItemView(request, thisModel, id, nameField, viewTemplate=None, allowDelete=False):
	thisModelItem = get_object_or_404(thisModel, id=id)
	thisModelForm = globals()[thisModel._meta.object_name + 'Form']
	thisViewTemplate = 'admin_common_edit.html' if not viewTemplate else viewTemplate
	adminTemplate = 'metrics/page_template_admin.html'
	addItemTemplate = 'admin_common_add.html'
	thisModelListUrl = reverse(f'metrics:admin_{thisModel._meta.model_name}_list')
	
	try:
		thisModelDeleteUrl = reverse(f'metrics:admin_{thisModel._meta.model_name}_delete')
	except:
		thisModelDeleteUrl = None
	
	breadcrumbs = getAdminBreadcrumbBase()
	breadcrumbs.append(
		{
			'text': capfirst(thisModel._meta.verbose_name_plural),
			'url': thisModelListUrl
		}
	)

	context = {
		'breadcrumbs': breadcrumbs,
		'form': None,
		'modelMeta': thisModel._meta,
		'thisModelItem': thisModelItem,
		'itemName': getattr(thisModelItem, nameField),
		'adminTemplate': adminTemplate,
		'addItemTemplate': addItemTemplate,
		'thisModelDeleteUrl': thisModelDeleteUrl,
		'allowDelete': allowDelete,
	}

	if request.method == 'GET':
		form = thisModelForm(instance=thisModelItem)
		context['form'] = form

		response = render(request, thisViewTemplate, context)
		helpers.clearPageMessage(request)

	elif request.method == 'POST':
		form = thisModelForm(request.POST, instance=thisModelItem)
		context['form'] = form
		
		if form.is_valid():
			post = form.save(commit=False)
			post.updated_by = request.user
			post.save()
			form.save_m2m()
			
			helpers.setPageMessage(request, 'success', f'{capfirst(thisModel._meta.verbose_name)} was edited successfully')
			response = redirect(thisModelListUrl)
		else:
			response = render(request, thisViewTemplate, context)
			
	return response


def doCommonDeleteView(request, thisModel):
	thisId = request.POST.get('id', None)
	thisItem = get_object_or_404(thisModel, id=thisId)
	thisModelListUrl = reverse(f'metrics:admin_{thisModel._meta.model_name}_list')
	
	try:
		thisItem.delete()
		helpers.setPageMessage(request, 'success', f'{capfirst(thisModel._meta.verbose_name)} was deleted successfully')
	except Exception as ex:
		helpers.setPageMessage(request, 'error', f'{capfirst(thisModel._meta.verbose_name)} was unable to be deleted because there are associated responses.')
	
	response = redirect(thisModelListUrl)
		
	return response


##
##	/metrics/admin/
##
##	Admin home page. Anyone who is an editor or higher can access.
##
@user_passes_test(accessHelpers.isAnyProjectEditor_decorator)
def admin_home(request):
	projectsCanEdit = Project.projectsCanEdit(request.user)
	projectSnapshots = ProjectSnapshot.objects.exclude(date_period='month').filter(project__in=projectsCanEdit)
	
	context = {
		'counts': {
			'admins': User.objects.filter(groups__name='admins').count(),
			'artifacts': estimateCount('Artifact', app='research'),
			'browsers': estimateCount('Browser'),
			'brokenLinks': BrokenLink.objects.count(),
			'campaigns': estimateCount('Campaign'),
			'cities': estimateCount('City'),
			'activityLogs': estimateCount('ActivityLog'),
			'countries': estimateCount('Country'),
			'dataSources': estimateCount('DataSource'),
			'domains': Domain.domainsCanAdmin(request.user).count(),
			'domainYearSnapshots': estimateCount('DomainYearSnapshot'),
			'faqs': estimateCount('Faq', app='info'),
			'faqCategories': estimateCount('FaqCategory', app='info'),
			'goalCompletedCategories': estimateCount('GoalCompletedCategory'),
			#'inactiveUsers': User.objects.filter(profile__inactive=True).exclude(artifact_owner=None, project_contact=None, project_admins=None).values('id').distinct().count(),
			'methods': estimateCount('Method', app='research'),
			'npsLetterGrades': estimateCount('NpsLetterGrade'),
			'npsScoreCategories': estimateCount('NpsScoreCategory'),
			'operatingsystems': estimateCount('OperatingSystem'),
			'pageViews': PageView.objects.aggregate(Sum('view_count')),
			'primaryGoals': estimateCount('PrimaryGoal'),
			'projects': Project.projectsCanAdmin(request.user).count(),
			'projectKeywords': estimateCount('ProjectKeyword'),
			'projectSnapshots': projectSnapshots.count(),
			'projectEvents': estimateCount('ProjectEvent'),
			'projectYearSettings': estimateCount('ProjectYearSetting'),
			'sources': estimateCount('Source', app='research'),
			'states': estimateCount('State'),
			'statuses': estimateCount('Status', app='research'),
			'responses': estimateCount('Response'),
			'tags': estimateCount('Tag', app='research'),
			'umuxScoreCategories': estimateCount('UmuxScoreCategory'),
			'userRoles': estimateCount('UserRole'),
			'users': estimateCount('User', app='auth'),
		},
		'lastUsabillaRun': UsabillaImportLog.objects.filter(user__username='usabilla_import_script').order_by('-date').only('date', 'user').first(),
		'lastBeeHeardRun': UsabillaImportLog.objects.filter(user__username='beeheard_import_script').order_by('-date').only('date', 'user').first(),
		'dataAudits': {
			'archivedArtifacts': Artifact.objects.filter(archived=True).count(),
			'artifactSearches': ArtifactSearch.objects.all().values('search_text', 'search_count')[:10],
			'notags': Artifact.objects.filter(tags__isnull=True).count(),
			'methodsUnused': Method.objects.filter(artifact_methods__isnull=True).count(),
			'sourcesUnused': Source.objects.filter(artifact_source__isnull=True).count(),
			'statusesUnused': Status.objects.filter(artifact_status__isnull=True).count(),
			'tagsUnused': Tag.objects.filter(artifact_tags__isnull=True).count(),
			'userArtifacts': User.objects.exclude(artifact_owner=None).distinct().annotate(numarts=Count('artifact_owner')).order_by('-numarts')[:10],
			'usersNoProfile': User.objects.filter(profile__full_name='', username__contains='@', profile__inactive=False).count(),
			'artifactsInactiveOwners': Artifact.objects.filter(owner__profile__inactive=True).count(),
			'campaignsResponsesNoProject': Campaign.objects.filter(project__isnull=True, response_campaign__isnull=False).distinct().count(),
			'projectsInactiveContacts': Project.objects.filter(Q(contact__profile__inactive=True) | Q(admins__profile__inactive=True)).distinct().count(),
			'projects': Project.objects.count(),
			'projectsNoSnapshots': Project.objects.filter(project_snapshot_project__isnull=True).count(),
			'projectsNoContact': Project.objects.filter(contact__isnull=True).count(),
			'projectsNoDomain': Project.objects.filter(domain__isnull=True).count(),
			'projectsInactive': Project.objects.filter(inactive=True).count(),
			'coreProjects': Project.objects.filter(core_project=True).count(),
			'projectsWithDesigners': Project.objects.filter(designer_assigned='yes').count(),
		},
	}
	
	response = render(request, 'metrics/admin_home.html', context)
	
	helpers.clearPageMessage(request)
	
	return response


##
##	/metrics/admin/adminaccess/
##
##	Manage who is in admin group (Admin access control).
##
# @user_passes_test(accessHelpers.hasAdminAccess_decorator)
# def admin_adminaccess(request):
# 	
# 	breadcrumbs = [
# 		{ 
# 			'text': 'Metrics',
# 			'url': reverse('metrics:home')
# 		},
# 		{ 
# 			'text': 'Admin',
# 			'url': reverse('metrics:admin_home')
# 		}
# 	]
# 	
# 	context = {
# 		'breadcrumbs': breadcrumbs,
# 		'adminUsers': User.objects.filter(groups__name='admins').order_by('username'),
# 	}
# 	
# 	return render(request, 'admin_adminaccess.html', context)


##
##	/metrics/admin/imported/<model>/
##
##	Read-only view of imported data
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_import_data_list(request, modelName):
	readonlyModels = { 
		'browser': Browser,
		'operatingsystem': OperatingSystem,
		'devicetype': DeviceType,
		'country': Country,
		'state': State,
		'city': City,
		'userrole': UserRole,
		'primarygoal': PrimaryGoal
	}
	
	try:
		thisModel = readonlyModels[modelName]
	except Exception as ex:
		return render(request, '404.html', {}, status=404)
	
	context = {
		'modelName': thisModel._meta.verbose_name_plural.capitalize(),
		'items': thisModel.objects.order_by(Lower('name')).all()
	}
	
	return render(request, 'metrics/admin_import_data_list.html', context)


##
##	/metrics/admin/domains/
##
@user_passes_test(accessHelpers.isAnyDomainAdmin_decorator)
def admin_domain_list(request):
	thisModel = Domain
	listItems = thisModel.domainsCanAdmin(request.user).prefetch_related('project_domain__campaign_project', 'admins__profile')
	return doCommonListView(request, thisModel, listItems)

##
##	/metrics/admin/domains/add/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_domain_add(request):
	thisModel = Domain
	return doCommonAddItemView(request, thisModel)


##
##	/metrics/admin/domains/edit/<id>/
##
@user_passes_test(accessHelpers.isAnyDomainAdmin_decorator)
def admin_domain_edit(request, id):
	thisModel = Domain
	return doCommonEditItemView(request, thisModel, id, 'name')


##
##	/metrics/admin/domain/delete/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_domain_delete(request):
	return doCommonDeleteView(request, Domain)


##
##	/metrics/admin/projects/
##
@user_passes_test(accessHelpers.isAnyProjectAdmin_decorator)
def admin_project_list(request):
	projects = Project.projectsCanAdmin(request.user).order_by(Lower('name')).prefetch_related(
			'campaign_project', 'admins__profile'
		).annotate(
			numResponses=Count('campaign_project__response_campaign'),
			domainName=F('domain__name'),
			createdbyUsername=F('created_by__username'),
		)
	
	# for project in projects:
	# 	project.numResponses = project.getVoteResponses().count()
	
	context = {
		'projects': projects
	}
	
	response = render(request, 'metrics/admin_project_list.html', context)
	
	helpers.clearPageMessage(request)
	
	return response


##
##	/metrics/admin/projects/add/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_project_add(request):
	breadcrumbs = getAdminBreadcrumbBase()
	breadcrumbs.append(
		{ 
			'text': 'Tools &amp; services',
			'url': reverse('metrics:admin_project_list')
		}
	)

	if request.method == 'GET':
		form = ProjectForm()
		
		context = {
			'breadcrumbs': breadcrumbs,
			'form': form,
		}

		response = render(request, 'metrics/admin_project_add.html', context)
		helpers.clearPageMessage(request)

	elif request.method == 'POST':
		form = ProjectForm(request.POST)
		
		context = {
			'breadcrumbs': breadcrumbs,
			'form': form
		}
		
		if form.is_valid():
			post = form.save(commit=False)
			post.created_by = request.user
			post.updated_by = request.user
			post.save()
			form.save_m2m()
			
			changeEntry = ActivityLog.objects.create(
				user = request.user,
				content_object = post,
				comments = 'Project record created'
			)
			alertEntry = Alert.objects.create(
				project = post,
				type = 'Info',
				comments = f'A new project was just added: "{post.name}"'
			)
			
			helpers.setPageMessage(request, 'success', 'Project was added successfully')
			response = redirect(reverse('metrics:admin_project_list'))
		
		else:
			response = render(request, 'metrics/admin_project_add.html', context)
			 
	return response


##
##	/metrics/admin/projects/edit/<id>/
##
@user_passes_test(accessHelpers.isAnyProjectAdmin_decorator)
def admin_project_edit(request, id):
	project = get_object_or_404(Project, id=id)
	
	if not accessHelpers.isProjectAdmin(request.user, project):
		return render(request, '403.html', {}, status=403)
	
	breadcrumbs = getAdminBreadcrumbBase()
	breadcrumbs.append(
		{ 
			'text': 'Tools &amp; services',
			'url': reverse('metrics:admin_project_list')
		}
	)

	if request.method == 'GET':
		form = ProjectForm(instance=project)
		
		context = {
			'breadcrumbs': breadcrumbs,
			'project': project,
			'form': form,
			'uxSpecialistAssigneds': UxSpecialistAssigned.objects.filter(project=project)
		}

		response = render(request, 'metrics/admin_project_edit.html', context)
		helpers.clearPageMessage(request)

	elif request.method == 'POST':
		form = ProjectForm(request.POST, instance=project)
		
		context = {
			'breadcrumbs': breadcrumbs,
			'project': project,
			'form': form
		}
		
		if form.is_valid():
			post = form.save(commit=False)
			post.updated_by = request.user
			post.save()
			form.save_m2m()
			
			changeEntry = ActivityLog.objects.create(
				user = request.user,
				content_object = project,
				comments = 'Project record updated'
			)
			
			helpers.setPageMessage(request, 'success', 'Project was updated successfully')
			response = redirect(reverse('metrics:admin_project_list'))
		 
		else:
			response = render(request, 'metrics/admin_project_edit.html', context)
			 
	return response


##
##	/metrics/admin/projects/delete/<id>/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_project_delete(request):
	return doCommonDeleteView(request, Project)


##
##	/metrics/admin/campaign/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_campaign_list(request):
	campaigns = Campaign.objects.order_by('key').annotate(numResponses=Count('response_campaign')).annotate(projectName=F('project__name'), vendorApp=F('project__vendor_app'), domainName=F('project__domain__name')).annotate(
			numOthers=Count('response_campaign', filter=(Q(response_campaign__primary_goal__name='Other') | Q(response_campaign__primary_goal__name='')))
		)
	
	context = {
		'campaigns': campaigns
	}
	
	response = render(request, 'metrics/admin_campaign_list.html', context)
	
	helpers.clearPageMessage(request)
	
	return response


##
##	/metrics/admin/campaignnoproject/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_campaign_noproject_list(request):
	campaigns = Campaign.objects.filter(response_campaign__isnull=False, project__isnull=True).order_by('key').annotate(numResponses=Count('response_campaign'))
	
	context = {
		'campaigns': campaigns
	}
	
	response = render(request, 'metrics/admin_campaign_list.html', context)
	
	helpers.clearPageMessage(request)
	
	return response


##
##	/metrics/admin/campaign/add/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_campaign_add(request):
	breadcrumbs = getAdminBreadcrumbBase()
	breadcrumbs.append(
		{ 
			'text': 'Campaigns',
			'url': reverse('metrics:admin_campaign_list')
		}
	)

	if request.method == 'GET':
		form = CampaignForm()
		
		context = {
			'breadcrumbs': breadcrumbs,
			'form': form
		}

		response = render(request, 'metrics/admin_campaign_add.html', context)
		helpers.clearPageMessage(request)

	elif request.method == 'POST':
		form = CampaignForm(request.POST)
		
		context = {
			'breadcrumbs': breadcrumbs,
			'form': form
		}
		
		if form.is_valid():
			post = form.save(commit=False)
			post.created_by = request.user
			post.updated_by = request.user
			post.save()
			
			if post.project:
				alertEntry = Alert.objects.create(
					project = post.project,
					type = 'Info',
					comments = f'A new campaign ({post.key}) campaign was added to "{post.project.name}"'
				)
			
			helpers.setPageMessage(request, 'success', 'Campaign was added successfully')
			response = redirect(reverse('metrics:admin_campaign_list'))
		
		else:
			response = render(request, 'metrics/admin_campaign_add.html', context)
			 
	return response


##
##	/metrics/admin/campaign/edit/<id>/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_campaign_edit(request, id):
	campaign = get_object_or_404(Campaign, id=id)
	
	breadcrumbs = getAdminBreadcrumbBase()
	breadcrumbs.append(
		{ 
			'text': 'Campaigns',
			'url': reverse('metrics:admin_campaign_list')
		}
	)

	campaign.numResponses = campaign.response_campaign.count()
	
	if request.method == 'GET':
		form = CampaignForm(instance=campaign)
		
		context = {
			'breadcrumbs': breadcrumbs,
			'campaign': campaign,
			'form': form
		}

		response = render(request, 'metrics/admin_campaign_edit.html', context)
		helpers.clearPageMessage(request)

	elif request.method == 'POST':
		form = CampaignForm(request.POST, instance=campaign)

		context = {
			'breadcrumbs': breadcrumbs,
			'campaign': campaign,
			'form': form
		}
		
		try:
			oldProject = campaign.project
		except Exception as ex:
			oldProject = None

		if form.is_valid():
			# Save the campaign so the new project relationship is stored, then do the re-calculations.
			post = form.save(commit=False)
			post.updated_by = request.user
			post.save()
			
			try:
				newProject = post.project
			except Exception as ex:
				newProject = None
			
			# Update this campaign's project snapshots and domain if it's project changed.
			# If there was and old and new and they are different, update both.
			if newProject and oldProject and oldProject.id != newProject.id:
				helpers.runInBackground(oldProject.recalculateSnapshotsBaselinesAndDomains)
				helpers.runInBackground(newProject.recalculateSnapshotsBaselinesAndDomains)
				
				alertEntry = Alert.objects.create(
					project = newProject,
					domain = getattr(newProject, 'domain', None),
					type = 'Info',
					comments = f'"{post.key}" campaign was moved from "{oldProject.name}" to "{newProject.name}"'
				)
			elif newProject and not oldProject:
				helpers.runInBackground(newProject.recalculateSnapshotsBaselinesAndDomains)
				
				alertEntry = Alert.objects.create(
					project = newProject,
					domain = getattr(newProject, 'domain', None),
					type = 'Info',
					comments = f'"{post.key}" campaign was added to "{newProject.name}"'
				)
			elif oldProject and not newProject:
				helpers.runInBackground(oldProject.recalculateSnapshotsBaselinesAndDomains)
				
				alertEntry = Alert.objects.create(
					project = newProject,
					domain = getattr(newProject, 'domain', None),
					type = 'Info',
					comments = f'"{post.key}" campaign was removed from "{oldProject.name}"'
				)

			helpers.setPageMessage(request, 'success', 'Campaign was updated successfully')
			response = redirect(reverse('metrics:admin_campaign_list'))
		 
		else:
			response = render(request, 'metrics/admin_campaign_edit.html', context)
			 
	return response


##
##	/metrics/admin/campaign/delete/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_campaign_delete(request):
	return doCommonDeleteView(request, Campaign)


##
##	/metrics/admin/campaign/deleteallresponses/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_campaign_delete_all_responses(request):
	campaign = get_object_or_404(Campaign, id=request.POST.get('id', None))
	
	# Delete all response
	# Set the date way back
	# Update all this project's snapshots so they recalc with removed responses.
	# Update this project's domain to update the rollup scores metrics.
	try:
		campaign.response_campaign.all().delete()
		campaign.feedback_response_campaign.all().delete()
		campaign.other_response_campaign.all().delete()
		campaign.latest_response_date = timezone.make_aware(datetime(2015, 1, 1))
		campaign.save()
		campaign.project.updateAllSnapshots()
		campaign.project.storeLatestSnapshots()
		campaign.project.domain.updateDomainYearSnapshot()
		
		helpers.setPageMessage(request, 'success', 'All campaign responses were deleted successfully')
	except Exception as ex:
		helpers.setPageMessage(request, 'error', 'Campaign responses were unable to be deleted. Contact Michael Santelia')
	
	return redirect(reverse('metrics:admin_campaign_list'))	


##
##	/metrics/admin/projectyearsetting/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_projectyearsetting_list(request):
	thisModel = ProjectYearSetting
	listItems = thisModel.objects.prefetch_related('project', 'updated_by').all()
	return doCommonListView(request, thisModel, listItems)


##
##	/metrics/admin/projectyearsetting/add/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_projectyearsetting_add(request):
	breadcrumbs = getAdminBreadcrumbBase()
	breadcrumbs.append(
		{ 
			'text': 'Project year settings',
			'url': reverse('metrics:admin_projectyearsetting_list')
		}
	)

	if request.method == 'GET':
		form = ProjectYearSettingForm()
		
		context = {
			'breadcrumbs': breadcrumbs,
			'form': form
		}

		response = render(request, 'metrics/admin_projectyearsetting_add.html', context)
		helpers.clearPageMessage(request)

	elif request.method == 'POST':
		form = ProjectYearSettingForm(request.POST)
		
		context = {
			'breadcrumbs': breadcrumbs,
			'form': form
		}
		
		if form.is_valid():
			post = form.save(commit=False)
			post.created_by = request.user
			post.updated_by = request.user
			post.nps_baseline_entry_type = 'manual'
			post.calculateTargets()
			post.save()
			
			helpers.setPageMessage(request, 'success', 'Project year setting was added successfully')
			response = redirect(reverse('metrics:admin_projectyearsetting_list'))
		
		else:
			response = render(request, 'metrics/admin_projectyearsetting_add.html', context)
			 
	return response


##
##	/metrics/admin/projectyearsetting/edit/<id>/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_projectyearsetting_edit(request, id):
	projectyearsetting = get_object_or_404(ProjectYearSetting, id=id)
	
	breadcrumbs = getAdminBreadcrumbBase()
	breadcrumbs.append(
		{ 
			'text': 'Project year settings',
			'url': reverse('metrics:admin_projectyearsetting_list')
		}
	)

	if request.method == 'GET':
		form = ProjectYearSettingForm(instance=projectyearsetting)
		
		context = {
			'breadcrumbs': breadcrumbs,
			'projectyearsetting': projectyearsetting,
			'form': form
		}

		response = render(request, 'metrics/admin_projectyearsetting_edit.html', context)
		helpers.clearPageMessage(request)

	elif request.method == 'POST':
		form = ProjectYearSettingForm(request.POST, instance=projectyearsetting)

		context = {
			'breadcrumbs': breadcrumbs,
			'projectyearsetting': projectyearsetting,
			'form': form
		}
		
		if form.is_valid():
			post = form.save(commit=False)
			post.updated_by = request.user
			post.nps_baseline_entry_type = 'manual'
			post.calculateTargets()
			post.save()
			
			helpers.setPageMessage(request, 'success', 'Project year setting was updated successfully')
			response = redirect(reverse('metrics:admin_projectyearsetting_list'))
		 
		else:
			response = render(request, 'metrics/admin_projectyearsetting_edit.html', context)
			 
	return response


##
##	/metrics/admin/datasource/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_datasource_list(request):
	thisModel = DataSource
	listItems = thisModel.objects.all()
	return doCommonListView(request, thisModel, listItems)


##
##	/metrics/admin/datasource/add/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_datasource_add(request):
	thisModel = DataSource
	return doCommonAddItemView(request, thisModel)


##
##	/metrics/admin/datasource/edit/<id>
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_datasource_edit(request, id):
	thisModel = DataSource
	return doCommonEditItemView(request, thisModel, id, 'name')


##
##	/metrics/admin/npslettergrade/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_npslettergrade_list(request):
	thisModel = NpsLetterGrade
	listItems = thisModel.objects.all()
	return doCommonListView(request, thisModel, listItems)


##
##	/metrics/admin/npslettergrade/add/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_npslettergrade_add(request):
	thisModel = NpsLetterGrade
	return doCommonAddItemView(request, thisModel)


##
##	/metrics/admin/npslettergrade/edit/<id>
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_npslettergrade_edit(request, id):
	thisModel = NpsLetterGrade
	return doCommonEditItemView(request, thisModel, id, 'name')


##
##	/metrics/admin/npsscorecategory/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_npsscorecategory_list(request):
	thisModel = NpsScoreCategory
	listItems = thisModel.objects.all()
	return doCommonListView(request, thisModel, listItems)


##
##	/metrics/admin/npsscorecategory/add/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_npsscorecategory_add(request):
	thisModel = NpsScoreCategory
	return doCommonAddItemView(request, thisModel)


##
##	/metrics/admin/npsscorecategory/edit/<id>
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_npsscorecategory_edit(request, id):
	thisModel = NpsScoreCategory
	return doCommonEditItemView(request, thisModel, id, 'name')


##
##	/metrics/admin/goalcompletedcategory/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_goalcompletedcategory_list(request):
	thisModel = GoalCompletedCategory
	listItems = thisModel.objects.all()
	return doCommonListView(request, thisModel, listItems)


##
##	/metrics/admin/goalcompletedcategory/add/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_goalcompletedcategory_add(request):
	thisModel = GoalCompletedCategory
	return doCommonAddItemView(request, thisModel)


##
##	/metrics/admin/goalcompletedcategory/edit/<id>
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_goalcompletedcategory_edit(request, id):
	thisModel = GoalCompletedCategory
	return doCommonEditItemView(request, thisModel, id, 'name')


##
##	/metrics/admin/domainyearsnapshot/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_domainyearsnapshot_list(request):
	thisModel = DomainYearSnapshot
	listItems = thisModel.objects.all()
	return doCommonListView(request, thisModel, listItems)


##
##	/metrics/admin/domainyearsnapshot/add/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_domainyearsnapshot_add(request):
	thisModel = DomainYearSnapshot
	return doCommonAddItemView(request, thisModel)


##
##	/metrics/admin/domainyearsnapshot/edit/<id>
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_domainyearsnapshot_edit(request, id):
	thisModel = DomainYearSnapshot
	return doCommonEditItemView(request, thisModel, id, 'domain')


##
##	/metrics/admin/umuxscorecategory/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_umuxscorecategory_list(request):
	thisModel = UmuxScoreCategory
	listItems = thisModel.objects.all()
	return doCommonListView(request, thisModel, listItems)


##
##	/metrics/admin/umuxscorecategory/add/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_umuxscorecategory_add(request):
	thisModel = UmuxScoreCategory
	return doCommonAddItemView(request, thisModel)


##
##	/metrics/admin/umuxscorecategory/edit/<id>
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_umuxscorecategory_edit(request, id):
	thisModel = UmuxScoreCategory
	return doCommonEditItemView(request, thisModel, id, 'name')


##
##	/metrics/admin/projectevents/
##
@user_passes_test(accessHelpers.isAnyProjectEditor_decorator)
def admin_projectevent_list(request):
	thisModel = ProjectEvent
	listItems = thisModel.objects.select_related('project', 'created_by')
	return doCommonListView(request, thisModel, listItems)


##
##	/metrics/admin/projectevents/add/
##
def admin_projectevent_add(request):
	thisModel = ProjectEvent
	thisModelForm = globals()[thisModel._meta.object_name + 'Form']
	thisViewTemplate = f'metrics/admin_{thisModel._meta.model_name}_add.html'
	thisModelListUrl = reverse(f'metrics:admin_{thisModel._meta.model_name}_list')
	
	breadcrumbs = getAdminBreadcrumbBase()
	breadcrumbs.append(
		{
			'text': capfirst(thisModel._meta.verbose_name_plural),
			'url': thisModelListUrl
		}
	)

	context = {
		'breadcrumbs': breadcrumbs,
		'form': None,
		'modelMeta': thisModel._meta,
		'newItemName': thisModel._meta.verbose_name,
	}

	if request.method == 'GET':
		form = thisModelForm()
		
		try:
			form.fields['project'].initial = Project.objects.get(id=request.GET.get('project', None))
		except:
			pass
		
		context['form'] = form

		response = render(request, thisViewTemplate, context)
		helpers.clearPageMessage(request)
		
	elif request.method == 'POST':
		form = thisModelForm(request.POST)

		try:
			form.fields['project'].initial = Project.objects.get(id=request.GET.get('project', None))
		except:
			pass
		
		context['form'] = form
		
		if form.is_valid():
			post = form.save(commit=False)
			post.created_by = request.user
			post.updated_by = request.user
			post.save()
			form.save_m2m()
			
			# If it's a success and they want JSON back, return the ID and label as JSON,
			#  otherwise we redirect to the list page with a message.
			if request.POST.get('returntype', None) == 'json':
				response = JsonResponse({
					'id': post.id,
					'name': post.__str__()
				}, status=200)
			else:
				helpers.setPageMessage(request, 'success', f'{capfirst(thisModel._meta.verbose_name)} was added successfully')
				response = redirect(thisModelListUrl)
		else:
			response = render(request, thisViewTemplate, context)
			
	return response


##
##	/metrics/admin/projectevents/edit/<id>/
##
def admin_projectevent_edit(request, id):
	thisModel = ProjectEvent
	thisModelItem = get_object_or_404(thisModel, id=id)
	thisModelForm = globals()[thisModel._meta.object_name + 'Form']
	thisViewTemplate = f'metrics/admin_{thisModel._meta.model_name}_edit.html'
	thisModelListUrl = reverse(f'metrics:admin_{thisModel._meta.model_name}_list')
	
	breadcrumbs = getAdminBreadcrumbBase()
	breadcrumbs.append(
		{
			'text': capfirst(thisModel._meta.verbose_name_plural),
			'url': thisModelListUrl
		}
	)

	context = {
		'breadcrumbs': breadcrumbs,
		'form': None,
		'modelMeta': thisModel._meta,
		'thisModelItem': thisModelItem,
	}

	if request.method == 'GET':
		form = thisModelForm(instance=thisModelItem)

		context['form'] = form

		response = render(request, thisViewTemplate, context)
		helpers.clearPageMessage(request)

	elif request.method == 'POST':
		form = thisModelForm(request.POST, instance=thisModelItem)

		context['form'] = form
		
		if form.is_valid():
			post = form.save(commit=False)
			post.updated_by = request.user
			post.save()
			form.save_m2m()
			
			# If it's a success and they want JSON back, return the ID and label as JSON,
			#  otherwise we redirect to the list page with a message.
			if request.POST.get('returntype', None) == 'json':
				response = JsonResponse({
					'id': post.id,
					'name': post.__str__()
				}, status=200)
			else:
				helpers.setPageMessage(request, 'success', f'{capfirst(thisModel._meta.verbose_name)} was edited successfully')
				response = redirect(thisModelListUrl)
		else:
			response = render(request, thisViewTemplate, context)
			
	return response
	
	
##
##	/metrics/admin/projectevents/delete/<id>/
##
def admin_projectevent_delete(request, id):
	thisModel = ProjectEvent
	thisModelItem = get_object_or_404(thisModel, id=id)
	thisModelListUrl = reverse(f'metrics:admin_{thisModel._meta.model_name}_list')

	if not accessHelpers.isProjectAdmin(request.user, thisModelItem.project):
		return render(request, '404.html', {}, status=404)

	thisModelItem.delete()
	
	if request.POST.get('returntype', None) == 'json':
		response = JsonResponse({
			'msg': "Deleted successfully."
		}, status=200)
	else:
		helpers.setPageMessage(request, 'success', f'{capfirst(thisModel._meta.verbose_name)} was deleted successfully')
		response = redirect(thisModelListUrl)
	
	return response


##
##	/metrics/admin/projectsnapshots/
##
@user_passes_test(accessHelpers.isAnyProjectEditor_decorator)
def admin_projectsnapshot_list(request):
	projectsCanEdit = Project.projectsCanEdit(request.user)
	
	if not projectsCanEdit or projectsCanEdit.count() == 0:
		return render(request, '403.html', {}, status=403)

	projectSnapshots = ProjectSnapshot.objects.filter(Q(date_period='quarter') | Q(date_period='last90')).filter(project__in=projectsCanEdit).prefetch_related('project', 'updated_by', 'data_source')
	
	context = {
		'projectSnapshots': projectSnapshots
	}
	
	response = render(request, 'metrics/admin_projectsnapshot_list.html', context)
	
	helpers.clearPageMessage(request)
	
	return response


##
##	/metrics/admin/projectsnapshots/add/
##
@user_passes_test(accessHelpers.isAnyProjectEditor_decorator)
def admin_projectsnapshot_add(request):
	projectsCanEdit = Project.projectsCanEdit(request.user)
	
	if not projectsCanEdit or projectsCanEdit.count() == 0:
		return render(request, '403.html', {}, status=403)

	breadcrumbs = getAdminBreadcrumbBase()
	breadcrumbs.append(
		{ 
			'text': 'Project snapshots',
			'url': reverse('metrics:admin_projectsnapshot_list')
		}
	)

	if request.method == 'GET':
		form = ProjectSnapshotForm()
		form.fields['project'].queryset = projectsCanEdit
		form.fields['data_source'].initial = DataSource.objects.get(name='Other')
		
		context = {
			'breadcrumbs': breadcrumbs,
			'form': form
		}

		response = render(request, 'metrics/admin_projectsnapshot_add.html', context)
		helpers.clearPageMessage(request)

	elif request.method == 'POST':
		form = ProjectSnapshotForm(request.POST)
		form.fields['project'].queryset = projectsCanEdit
		
		context = {
			'breadcrumbs': breadcrumbs,
			'form': form
		}
		
		if form.is_valid():
			post = form.save(commit=False)
			post.created_by = request.user
			post.updated_by = request.user
			post.response_day_range = 90
			try:
				errorMsg = post.save()
				if errorMsg:
					context['form'].add_error(field='date', error=errorMsg)
					raise ValidationError(errorMsg)
					
				post.manualEntryCalculateAndSave()
				post.project.storeLatestSnapshots()
				post.project.setYearBaselinesAndTargets()
				if post.project.domain:
					post.project.domain.updateDomainYearSnapshot()
				
				helpers.setPageMessage(request, 'success', 'Projectsnapshot was added successfully')
				response = redirect(reverse('metrics:admin_projectsnapshot_list'))
			except Exception as ex:
				response = render(request, 'metrics/admin_projectsnapshot_add.html', context)	
		else:
			response = render(request, 'metrics/admin_projectsnapshot_add.html', context)
			 
	return response


##
##	/metrics/admin/projectsnapshots/edit/<id>/
##
@user_passes_test(accessHelpers.isAnyProjectEditor_decorator)
def admin_projectsnapshot_edit(request, id):
	projectsnapshot = get_object_or_404(ProjectSnapshot, id=id)
	
	projectsCanEdit = Project.projectsCanEdit(request.user)
	
	if not projectsnapshot.project in projectsCanEdit:
		return render(request, '403.html', {}, status=403)

	breadcrumbs = getAdminBreadcrumbBase()
	breadcrumbs.append(
		{ 
			'text': 'Project snapshots',
			'url': reverse('metrics:admin_projectsnapshot_list')
		}
	)


	if request.method == 'GET':
		form = ProjectSnapshotForm(instance=projectsnapshot)
		form.fields['project'].queryset = projectsCanEdit
		form.fields['data_source'].initial = DataSource.objects.get(name='Other')
		
		context = {
			'breadcrumbs': breadcrumbs,
			'projectSnapshot': projectsnapshot,
			'form': form
		}

		response = render(request, 'metrics/admin_projectsnapshot_edit.html', context)
		helpers.clearPageMessage(request)

	elif request.method == 'POST':
		form = ProjectSnapshotForm(request.POST, instance=projectsnapshot)
		form.fields['project'].queryset = projectsCanEdit

		context = {
			'breadcrumbs': breadcrumbs,
			'projectsnapshot': projectsnapshot,
			'form': form
		}
		
		if form.is_valid():
			post = form.save(commit=False)
			post.updated_by = request.user
			try:
				errorMsg = post.save()
				if errorMsg:
					context['form'].add_error(field='date', error=errorMsg)
					raise ValidationError(errorMsg)
					
				post.manualEntryCalculateAndSave()
				post.project.storeLatestSnapshots()
				post.project.setYearBaselinesAndTargets()
				if post.project.domain:
					post.project.domain.updateDomainYearSnapshot()
				
				helpers.setPageMessage(request, 'success', 'Project snapshot was updated successfully')
				response = redirect(reverse('metrics:admin_projectsnapshot_list'))
			except Exception as ex:
				response = render(request, 'metrics/admin_projectsnapshot_edit.html', context)	
		else:
			response = render(request, 'metrics/admin_projectsnapshot_edit.html', context)
			 
	return response


##
##	/metrics/admin/emailallresponsesascsv/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_email_all_responses_as_csv(request):
	helpers.runInBackground(createCsvAndEmailFile, {'user':request.user})
	helpers.setPageMessage(request, 'success', 'Your CSV request is processing. You will recieve an email with the file in a few minutes.')
	response = redirect(reverse('metrics:admin_home'))	
	return response


##
##	/metrics/admin/getnewusabillaresponses/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_get_new_usabilla_responses(request):
	helpers.runInBackground(fetchNewUsabillaResponses, {'user':request.user})
	helpers.setPageMessage(request, 'success', 'Omnia is fetching all the latest Usabilla responses since the last fetch.<br>All reports will be updated with the latest data in a few minutes.')
	response = redirect(reverse('metrics:admin_home'))	
	return response


##
##	/metrics/admin/getnewbeeheardresponses/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_get_new_beeheard_responses(request):
	helpers.runInBackground(fetchNewBeeHeardResponses, {'user':request.user})
	helpers.setPageMessage(request, 'success', 'Omnia is fetching all the latest BeeHeard responses since the last fetch.<br>All reports will be updated with the latest data in a few minutes.')
	response = redirect(reverse('metrics:admin_home'))	
	return response


##
##	/metrics/admin/usabillaimportlog/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_usabilla_import_log(request):
	context = {
		'runs': UsabillaImportLog.objects.prefetch_related('user', 'user__profile')[:200]
	}
	
	return render(request, 'metrics/admin_usabilla_import_log.html', context)
	

##
##	/metrics/admin/activitylog/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_activity_log(request):
	context = {
		'activityLogs': ActivityLog.objects.all().annotate(userName=F('user__profile__full_name')).select_related('content_type').prefetch_related('content_object')[:2000]
	}
	
	return render(request, 'metrics/admin_activity_log.html', context)
	

##
##	/metrics/admin/pageviews/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_page_views(request):
	pageViewsValidUsers = PageView.objects.filter(user__isnull=False, user__username__contains='@')
	
	context = {
		'pageViews': list(PageView.objects.filter(user__isnull=False).values('url').annotate(views=Sum('view_count')).values_list('views', 'url').order_by('-views')[:25]),
		'totalPageViews': PageView.objects.aggregate(Sum('view_count')),
		'usersByPageviews': list(pageViewsValidUsers.values('user__username').annotate(views=Sum('view_count')).values_list('views', 'user__username').order_by('-views')[:25]),
		'usersByMetricsPageviews': list(pageViewsValidUsers.filter(url__contains='/metrics').values('user__username').annotate(views=Sum('view_count')).values_list('views', 'user__username').order_by('-views')[:25]),
		'usersByResearchPageviews': list(pageViewsValidUsers.filter(url__contains='/research').values('user__username').annotate(views=Sum('view_count')).values_list('views', 'user__username').order_by('-views')[:25]),
	}
	
	return render(request, 'metrics/admin_page_views.html', context)
	

##
##	/metrics/admin/inactiveusers/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_inactive_users(request):
	inactiveUsers = User.objects.filter(profile__inactive=True).prefetch_related('artifact_owner', 'project_contact', 'project_admins')
	
	context = {
		'inactiveUsers': inactiveUsers
	}
	
	return render(request, 'metrics/admin_inactive_users.html', context)
	

##
##	/metrics/admin/responseexport/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_responses_export(request):
	campaigns = Campaign.objects.filter(response_campaign__isnull=False).order_by('key').annotate(numResponses=Count('response_campaign')).select_related('project')
	
	try:
		for c in campaigns:
			c.numOthers = c.response_campaign.filter(Q(primary_goal__name='Other') | Q(primary_goal__name='')).count()
	except Exception as ex:
		pass
	
	context = {
		'campaigns': campaigns
	}
	
	response = render(request, 'metrics/admin_responses_export.html', context)
	
	helpers.clearPageMessage(request)
	
	return response

	
##
##	/metrics/admin/responsesascsv/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_responses_as_csv(request):
	try:
		campaigns = request.POST.getlist('campaigns')
		
		if len(campaigns) > 0:
			fileName = createCsvFromData(campaigns=campaigns, orderBy='primary_goal')
			f = open(fileName, 'r')
			file_content = f.read()
			f.close()
			response = HttpResponse(file_content, content_type='application/vnd.ms-excel')
			response['Content-Disposition'] = f'attachment;filename="{fileName}"'
			
			# Delete file.
			os.remove(fileName)
			
			# Return it
			return response
		else:
			raise Exception()
	except Exception as ex:
		return render(request, '404.html', {}, status=404)


##
##	/metrics/admin/responsesimportgoal/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_responses_import_goal(request):
	context = {
		
	}
	
	response = render(request, 'metrics/admin_responses_import_goal.html', context)
	
	helpers.clearPageMessage(request)
	
	return response

	
##
##	/metrics/admin/target/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_target_list(request):
	thisModel = Target
	listItems = thisModel.objects.all()
	return doCommonListView(request, thisModel, listItems)


##
##	/metrics/admin/target/add/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_target_add(request):
	thisModel = Target
	return doCommonAddItemView(request, thisModel)


##
##	/metrics/admin/target/edit/<id>
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_target_edit(request, id):
	thisModel = Target
	return doCommonEditItemView(request, thisModel, id, 'nps_score', viewTemplate='metrics/admin_target_edit.html')


##
##	/metrics/admin/target/delete/<id>/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_target_delete(request):
	return doCommonDeleteView(request, Target)

	
##
##	/metrics/admin/api/uxspecialistassigned/add/
##
@user_passes_test(accessHelpers.isAnyProjectAdmin_decorator)
def admin_uxspecialistassigned_add(request):
	try:
		project = Project.objects.get(id=request.POST.get('project'))
		
		if not accessHelpers.isProjectAdmin(request.user, project):
			return JsonResponse({'msg': 'Not authorized'}, status=403)
	
		UxSpecialistAssigned.objects.create(
			created_by = request.user,
			project = project,
			date = request.POST.get('date'),
			assigned = request.POST.get('assigned'),
		)
		
		existingDA = project.designer_assigned
		
		# Now set this project's flag that it has one assigned or not.
		project.setUxSpecialistFlag()

		# Log the change.
		changeEntry = ActivityLog.objects.create(
			user = request.user,
			content_object = project,
			comments = f'Project UX specialist assigned changed from "{existingDA}" to "{project.designer_assigned}"'
		)
		
		# Return the new list to display.
		response = JsonResponse({
			'uxSpecialistAssigneds': list(UxSpecialistAssigned.objects.filter(project=project).values_list('date', 'assigned', 'created_by__username', 'id')),
		}, status=200)
		
	except Exception as ex:
		response = JsonResponse({
			'msg': str(ex)
		}, status=404)
	
	return response
	
	
##
##	/metrics/admin/api/uxspecialistassigned/delete/<POST $ID>
##
@user_passes_test(accessHelpers.isAnyProjectAdmin_decorator)
def admin_uxspecialistassigned_delete(request):
	try:
		project = Project.objects.get(id=request.POST.get('project'))	
		uxSpecialist = UxSpecialistAssigned.objects.get(id=request.POST.get('id'))
		
		if not accessHelpers.isProjectAdmin(request.user, project):
			return JsonResponse({'msg': 'Not authorized'}, status=403)
		
		uxSpecialist.delete()
		
		# Return the new list to display.
		response = JsonResponse({
			'uxSpecialistAssigneds': list(UxSpecialistAssigned.objects.filter(project=project).values_list('date', 'assigned', 'created_by__username', 'id')),
		}, status=200)
		
	except Exception as ex:
		response = JsonResponse({
			'msg': str(ex)
		}, status=404)
	
	return response	
	
	
##
##	/metrics/admin/pageviews/download/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_page_views_download(request):
	
	if request.GET.get('list', None) == 'allpages':
		listResult = list(PageView.objects.filter(user__isnull=False).values('url').annotate(views=Sum('view_count')).values_list('views', 'url').order_by('-views'))
	
	elif request.GET.get('list', None) == 'usersallpages':
		listResult = list(PageView.objects.filter(user__isnull=False).values('user__username').annotate(views=Sum('view_count')).values_list('views', 'user__username').order_by('-views'))
	
	elif request.GET.get('list', None) == 'usersmetricspages':
		listResult = list(PageView.objects.filter(user__isnull=False, url__contains='/metrics').values('user__username').annotate(views=Sum('view_count')).values_list('views', 'user__username').order_by('-views'))
	elif request.GET.get('list', None) == 'usersresearchpages':
		listResult = list(PageView.objects.filter(user__isnull=False, url__contains='/research').values('user__username').annotate(views=Sum('view_count')).values_list('views', 'user__username').order_by('-views'))
	else:
		return render(request, '404.html', {}, status=404)
		
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment;filename="page views.csv"'
	
	writer = csv.writer(response)
	for item in listResult:
		writer.writerow(item)
	
	return response		
	
	
##
##	/metrics/admin/emailadmins/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_email_admins(request):
	context = {
		'form': None,
		'admins': list(Group.objects.get(name='admins').user_set.all().values_list('profile__full_name', flat=True))
	}
	
	if request.method == 'GET':
		form = EmailAdminsForm()
		context['form'] = form
		response = render(request, 'metrics/admin_email_admins.html', context)
		helpers.clearPageMessage(request)
	elif request.method == 'POST':
		form = EmailAdminsForm(request.POST)
		context['form'] = form
		
		if form.is_valid():	
			returnMessage, emailSent = helpers.emailAdmins({
				'msg': request.POST.get('msg', ''),
				'sender': request.user.profile.full_name,
				'fromEmail': f'{request.user.profile.full_name}<{request.user.username}>',
			})
			
			if emailSent:
				helpers.setPageMessage(request, 'success', 'Your message was emailed to all admins.')
				response = redirect(reverse('metrics:admin_home'))
			else:
				helpers.setPageMessage(request, 'error', returnMessage)
				response = render(request, 'metrics/admin_email_admins.html', context)
		else:
			response = render(request, 'metrics/admin_email_admins.html', context)
			helpers.clearPageMessage(request)
	
	return response	
	
	
##
##	/metrics/admin/onlineusers/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_online_users(request):
	context = {
		
	}	

	response = render(request, 'metrics/admin_online_users.html', context)

	return response
	
	
##
##	/metrics/admin/projectkeyword/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_projectkeyword_list(request):
	thisModel = ProjectKeyword
	listItems = thisModel.objects.all()
	return doCommonListView(request, thisModel, listItems)


##
##	/metrics/admin/projectkeyword/add/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_projectkeyword_add(request):
	return doCommonAddItemView(request, ProjectKeyword)


##
##	/metrics/admin/projectkeyword/edit/<id>
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_projectkeyword_edit(request, id):
	return doCommonEditItemView(request, ProjectKeyword, id, 'name', allowDelete=True)


##
##	/metrics/admin/projectkeyword/delete/<id>/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_projectkeyword_delete(request):
	return doCommonDeleteView(request, ProjectKeyword)
	
	
##
##	/metrics/admin/projectkeywordtagging/
##
@user_passes_test(accessHelpers.isAnyProjectAdmin_decorator)
def admin_project_keyword_tagging(request):
	context = {
		'keywords': ProjectKeyword.objects.all(),
		'projects': Project.projectsCanAdminDomainProjects(request.user).prefetch_related('keywords'),
	}
	
	response = render(request, 'metrics/admin_project_keyword_tagging.html', context)
	
	helpers.clearPageMessage(request)
	
	return response


##
##	/metrics/admin/projectkeywordtagging/add/
##
##	Add keyword to projects
##
@user_passes_test(accessHelpers.isAnyProjectAdmin_decorator)
def admin_project_keyword_tagging_add(request):
	try:
		projects = Project.objects.filter(id__in=request.POST.getlist('project'))
		
		if request.POST.get('keyword_new', None):
			keyword = ProjectKeyword.objects.create(name=request.POST['keyword_new'])
		else:
			keyword = ProjectKeyword.objects.get(id=request.POST.get('keyword'))
		for p in projects:
			p.keywords.add(keyword)
	except:
		pass
	
	helpers.setPageMessage(request, 'success', f'"{keyword.name}" was added to {projects.count()} tools successfully.')
	
	return redirect(reverse('metrics:admin_project_keyword_tagging'))
	

##
##	/metrics/admin/projectkeywordtagging/delete/
##
@user_passes_test(accessHelpers.isAnyProjectAdmin_decorator)
def admin_project_keyword_tagging_remove(request):
	try:
		project = Project.objects.get(id=request.POST.get('project'))
		keyword = ProjectKeyword.objects.get(id=request.POST.get('keyword'))
		project.keywords.remove(keyword)
	except:
		pass
	
	return JsonResponse({
			'msg': "Deleted successfully."
		}, status=200)
	

##
##	/metrics/admin/role/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_role_list(request):
	thisModel = Role
	listItems = thisModel.objects.all()
	return doCommonListView(request, thisModel, listItems)


##
##	/metrics/admin/role/add/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_role_add(request):
	thisModel = Role
	return doCommonAddItemView(request, thisModel)


##
##	/metrics/admin/role/edit/<id>
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_role_edit(request, id):
	thisModel = Role
	return doCommonEditItemView(request, thisModel, id, 'name', allowDelete=True)


##
##	/metrics/admin/role/delete/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_role_delete(request):
	return doCommonDeleteView(request, Role)


##
##	/metrics/admin/task/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_task_list(request):
	thisModel = Task
	listItems = thisModel.objects.all().select_related('parent_task').prefetch_related('projects', 'task_parent_task')
	return doCommonListView(request, thisModel, listItems)


##
##	/metrics/admin/task/add/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_task_add(request):
	thisModel = Task
	return doCommonAddItemView(request, thisModel)


##
##	/metrics/admin/task/edit/<id>
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_task_edit(request, id):
	thisModel = Task
	return doCommonEditItemView(request, thisModel, id, 'name', allowDelete=True)


##
##	/metrics/admin/task/delete/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_task_delete(request):
	return doCommonDeleteView(request, Task)



##
##	/metrics/admin/projectsnapshots/export/csv/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_projectsnapshots_to_csv(request):
	return render_to_csv_response(ProjectSnapshot.objects.all())
	
	
	
