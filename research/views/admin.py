import io
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


from ..models import *
from ..helpers import *
from ..forms import *


def getAdminBreadcrumbBase():
	return []


def doCommonListView(request, model, listItems):
	thisModel = model
	newItemUrl = reverse(f'research:admin_{thisModel._meta.model_name}_add')
	templateName = f'research/admin_{thisModel._meta.model_name}_list.html'
	
	context = {
		'listItems': listItems,
		'modelMeta': thisModel._meta,
		'newItemUrl': newItemUrl
	}

	response = render(request, templateName, context)
	clearPageMessage(request)
	return response


def doCommonAddItemView(request, thisModel):
	thisModelForm = globals()[thisModel._meta.object_name + 'Form']
	thisViewTemplate = 'admin_common_add.html'
	adminTemplate = 'research/page_template_admin.html'
	thisModelListUrl = reverse(f'research:admin_{thisModel._meta.model_name}_list')
	
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
		clearPageMessage(request)
		
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
				setPageMessage(request, 'success', f'{capfirst(thisModel._meta.verbose_name)} was added successfully')
				response = redirect(thisModelListUrl)
		else:
			response = render(request, thisViewTemplate, context)
			
	return response
	
	
def doCommonEditItemView(request, thisModel, id, nameField, viewTemplate=None, allowDelete=False):
	thisModelItem = get_object_or_404(thisModel, id=id)
	thisModelForm = globals()[thisModel._meta.object_name + 'Form']
	thisViewTemplate = 'admin_common_edit.html'
	adminTemplate = 'research/page_template_admin.html'
	addItemTemplate = 'admin_common_add.html'
	thisModelListUrl = reverse(f'research:admin_{thisModel._meta.model_name}_list')		
	
	try:
		thisModelDeleteUrl = reverse('research:admin_{}_delete'.format(thisModel._meta.model_name))
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
		clearPageMessage(request)

	elif request.method == 'POST':
		form = thisModelForm(request.POST, instance=thisModelItem)
		context['form'] = form
		
		if form.is_valid():
			post = form.save(commit=False)
			post.updated_by = request.user
			post.save()
			form.save_m2m()
			
			setPageMessage(request, 'success', f'{capfirst(thisModel._meta.verbose_name)} was edited successfully')
			response = redirect(thisModelListUrl)
		else:
			response = render(request, thisViewTemplate, context)
			
	return response


def doCommonDeleteView(request, thisModel):
	thisId = request.POST.get('id', None)
	thisItem = get_object_or_404(thisModel, id=thisId)
	thisModelListUrl = reverse(f'research:admin_{thisModel._meta.model_name}_list')
	
	try:
		thisItem.delete()
		setPageMessage(request, 'success', f'{capfirst(thisModel._meta.verbose_name)} was deleted successfully')
	except Exception as ex:
		setPageMessage(request, 'error', f'{capfirst(thisModel._meta.verbose_name)} was unable to be deleted because there are associated responses.')
	
	response = redirect(thisModelListUrl)
		
	return response


##
##	/researchadmin/
##
##	Admin home page.
##
## This URL now loads consolidate admins from metrics app.

##
##	/research/admin/adminaccess/
##
##	Manage who is in admin group (Admin access control).
##
@user_passes_test(hasAdminAccess_decorator)
def admin_adminaccess(request):
	context = {
		'adminUsers': User.objects.filter(groups__name='admins').order_by('username'),
	}
	
	return render(request, 'research/admin_adminaccess.html', context)


##
##	/research/admin/pageviews/
##
##	Page views.
##
@user_passes_test(hasAdminAccess_decorator)
def admin_pageviews(request):
	context = {
		'pageviews': PageView.objects.all()
	}
	
	return render(request, 'research/admin_pageviews.html', context)


##
##	/research/admin/method/
##
##	Methods list page.
##
@user_passes_test(hasAdminAccess_decorator)
def admin_method_list(request):
	thisModel = Method
	listItems = thisModel.objects.all()
	return doCommonListView(request, thisModel, listItems)

##
##	/research/admin/method/add/
##
##	Add a new Method.
##
@user_passes_test(hasAdminAccess_decorator)
def admin_method_add(request):
	thisModel = Method
	return doCommonAddItemView(request, thisModel)

##
##	/research/admin/method/edit/<id>/
##
##	Edit a Method.
##
@user_passes_test(hasAdminAccess_decorator)
def admin_method_edit(request, id):
	thisModel = Method
	return doCommonEditItemView(request, thisModel, id, 'name')


##
##	/research/admin/source/
##
@user_passes_test(hasAdminAccess_decorator)
def admin_source_list(request):
	thisModel = Source
	listItems = thisModel.objects.all()
	return doCommonListView(request, thisModel, listItems)

##
##	/research/admin/source/add/
##
@user_passes_test(hasAdminAccess_decorator)
def admin_source_add(request):
	thisModel = Source
	return doCommonAddItemView(request, thisModel)

##
##	/research/admin/source/edit/<id>/
##
@user_passes_test(hasAdminAccess_decorator)
def admin_source_edit(request, id):
	thisModel = Source
	return doCommonEditItemView(request, thisModel, id, 'name')


##
##	/research/admin/status/
##
@user_passes_test(hasAdminAccess_decorator)
def admin_status_list(request):
	thisModel = Status
	listItems = thisModel.objects.all()
	return doCommonListView(request, thisModel, listItems)

##
##	/research/admin/status/add/
##
@user_passes_test(hasAdminAccess_decorator)
def admin_status_add(request):
	thisModel = Status
	return doCommonAddItemView(request, thisModel)

##
##	/research/admin/status/edit/<id>/
##
@user_passes_test(hasAdminAccess_decorator)
def admin_status_edit(request, id):
	thisModel = Status
	return doCommonEditItemView(request, thisModel, id, 'name')


##
##	/research/admin/tags/
##
@user_passes_test(hasAdminAccess_decorator)
def admin_tag_list(request):
	thisModel = Tag
	listItems = thisModel.objects.all()
	return doCommonListView(request, thisModel, listItems)


##
##	/research/admin/tags/add/
##
@user_passes_test(hasAdminAccess_decorator)
def admin_tag_add(request):
	thisModel = Tag
	return doCommonAddItemView(request, thisModel)


##
##	/research/admin/tags/edit/<id>/
##
@user_passes_test(hasAdminAccess_decorator)
def admin_tag_edit(request, id):
	thisModel = Tag
	return doCommonEditItemView(request, thisModel, id, 'name')


##
##	/research/admin/artifacts/
##
##	Main Artifacts list page.
##
@user_passes_test(hasAdminAccess_decorator)
def admin_artifacts_list(request):
	context = {
		'artifacts': Artifact.objects.all().select_related('owner', 'status')
	}
	
	response = render(request, 'research/admin_artifacts_list.html', context)
	
	clearPageMessage(request)
	
	return response


##
##	/research/admin/artifacts/notags/
##
##	Artifacts without tags.
##
@user_passes_test(hasAdminAccess_decorator)
def admin_artifacts_notags(request):
	context = {
		'artifacts': Artifact.objects.filter(tags__isnull=True).prefetch_related('owner')
	}
	
	response = render(request, 'research/admin_artifacts_notags.html', context)
	
	clearPageMessage(request)
	
	return response


##
##	/research/admin/users/
##
##	Manage who is in admin group (Admin access control).
##
@user_passes_test(hasAdminAccess_decorator)
def admin_users(request):
	context = {
		'users': User.objects.order_by('username').prefetch_related('profile').annotate(numarts=Count('artifact_owner')),
		'usersByPageviews': PageView.objects.filter(user__isnull=False).values('user__username').annotate(views = Sum('view_count')).order_by('-views')
	}
	
	return render(request, 'research/admin_users.html', context)


##
##	/research/admin/users/noprofile/
##
##	Users without a profile
##
@user_passes_test(hasAdminAccess_decorator)
def admin_users_noprofile(request):
	context = {
		'users': User.objects.filter(Q(profile__full_name = '') | Q(profile__image__isnull=True), profile__inactive=False).order_by('username')
	}
	
	response = render(request, 'research/admin_users_noprofile.html', context)
	
	clearPageMessage(request)
	
	return response


##
##	/research/admin/batchchange/
##
##	Batch changes across all artifacts
##
@user_passes_test(hasAdminAccess_decorator)
def admin_batch_changes(request):
	context = {
		'artifactOwners': User.objects.exclude(artifact_owner=None).distinct().order_by('username'),
		'activeUsers': User.objects.filter(profile__inactive=False).order_by('username')
	}
	
	if request.method == 'GET':
		response = render(request, 'research/admin_batch_changes.html', context)
		clearPageMessage(request)

	elif request.method == 'POST':
		existingOwner = request.POST.get('existing_owner', None)
		newOwner = request.POST.get('new_owner', None)
			
		if existingOwner and newOwner:
			artifactsUpdated = Artifact.objects.filter(owner=existingOwner).update(owner=newOwner)
			
		setPageMessage(request, 'success', f'{artifactsUpdated} research artifacts were updated.')
		response = render(request, 'research/admin_batch_changes.html', context)
			 
	return response



##
##	/research/admin/surveyquestionexclusion/
##
@user_passes_test(hasAdminAccess_decorator)
def admin_surveyquestionexclusion_list(request):
	thisModel = SurveyQuestionExclusion
	listItems = thisModel.objects.all()
	return doCommonListView(request, thisModel, listItems)


##
##	/metrics/admin/surveyquestionexclusion/add/
##
@user_passes_test(hasAdminAccess_decorator)
def admin_surveyquestionexclusion_add(request):
	thisModel = SurveyQuestionExclusion
	return doCommonAddItemView(request, thisModel)


##
##	/metrics/admin/surveyquestionexclusion/edit/<id>/
##
@user_passes_test(hasAdminAccess_decorator)
def admin_surveyquestionexclusion_edit(request, id):
	thisModel = SurveyQuestionExclusion
	return doCommonEditItemView(request, thisModel, id, 'question_text', allowDelete=True)


##
##	/metrics/admin/surveyquestionexclusion/delete/ <POST: id>
##
##	Delete a Survey question exclusion.
##
@user_passes_test(hasAdminAccess_decorator)
def admin_surveyquestionexclusion_delete(request):
	return doCommonDeleteView(request, SurveyQuestionExclusion)


##
##	/research/admin/brokenlink/
##
##	List of artifact broken URLs
##
@user_passes_test(hasAdminAccess_decorator)
def admin_brokenlink_list(request):
	thisModel = BrokenLink
	listItems = thisModel.objects.all()
	return doCommonListView(request, thisModel, listItems)


##
##	/research/admin/brokenlink/delete/ <POST: id>
##
##	Delete a broken link item.
##
@user_passes_test(hasAdminAccess_decorator)
def admin_brokenlink_delete(request):
	return doCommonDeleteView(request, BrokenLink)

