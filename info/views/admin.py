import io
import requests

from datetime import datetime, timedelta

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.db.models import Count, Value, Q, Avg
from django.db.models.functions import Lower
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils.text import capfirst

from ..models import *
from research.models import Profile
from ..forms import *
import metrics.access_helpers as accessHelpers
import metrics.helpers as helpers


def getAdminBreadcrumbBase():
	return []
	

def doCommonListView(request, model, listItems):
	thisModel = model
	newItemUrl = reverse(f'info:admin_{thisModel._meta.model_name}_add')
	templateName = f'info/admin_{thisModel._meta.model_name}_list.html'
		
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
	adminTemplate = 'info/page_template_admin.html'
	thisModelListUrl = reverse(f'info:admin_{thisModel._meta.model_name}_list')
	
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
				helpers.setPageMessage(request, 'success', '{} was added successfully'.format(capfirst(thisModel._meta.verbose_name)))
				response = redirect(thisModelListUrl)
		else:
			response = render(request, thisViewTemplate, context)
			
	return response
	
	
def doCommonEditItemView(request, thisModel, id, nameField, viewTemplate=None, allowDelete=False):
	thisModelItem = get_object_or_404(thisModel, id=id)
	thisModelForm = globals()[thisModel._meta.object_name + 'Form']
	thisViewTemplate = 'admin_common_edit.html' if not viewTemplate else viewTemplate
	adminTemplate = 'info/page_template_admin.html'
	addItemTemplate = 'admin_common_add.html'
	thisModelListUrl = reverse(f'info:admin_{thisModel._meta.model_name}_list')
	
	try:
		thisModelDeleteUrl = reverse(f'info:admin_{thisModel._meta.model_name}_delete')
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
	thisModelListUrl = reverse('info:admin_{}_list'.format(thisModel._meta.model_name))
	
	try:
		thisItem.delete()
		helpers.setPageMessage(request, 'success', '{} was deleted successfully'.format(capfirst(thisModel._meta.verbose_name)))
	except Exception as ex:
		helpers.setPageMessage(request, 'error', '{} was unable to be deleted because there are associated responses.'.format(capfirst(thisModel._meta.verbose_name)))
	
	response = redirect(thisModelListUrl)
		
	return response




##
##	/info/admin/faqcategory/
##
##	FAQ category list page
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_faqcategory_list(request):
	thisModel = FaqCategory
	listItems = thisModel.objects.prefetch_related('faq_categories').annotate(numFaqs=Count('faq_categories'))
	return doCommonListView(request, thisModel, listItems)


##
##	/info/admin/faqcategory/add/
##
##	Add a FAQ category
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_faqcategory_add(request):
	thisModel = FaqCategory
	return doCommonAddItemView(request, thisModel)


##
##	/info/admin/faqcategory/<id>/
##
##	Edit a FAQ category
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_faqcategory_edit(request, id):
	thisModel = FaqCategory
	return doCommonEditItemView(request, thisModel, id, 'name')



##
##	/info/admin/faq/
##
##	FAQ list page
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_faq_list(request):
	thisModel = Faq
	listItems = thisModel.objects.prefetch_related('categories')
	return doCommonListView(request, thisModel, listItems)


##
##	/info/admin/faq/add/
##
##	Add a FAQ
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_faq_add(request):
	thisModel = Faq
	return doCommonAddItemView(request, thisModel)


##
##	/info/admin/faq/edit/<id>
##
##	Edit a FAQ
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_faq_edit(request, id):
	thisModel = Faq
	return doCommonEditItemView(request, thisModel, id, 'question')


##
##	/info/admin/whatsnew/
##
##	What's new list page
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_whatsnew_list(request):
	thisModel = WhatsNew
	listItems = thisModel.objects.all()
	return doCommonListView(request, thisModel, listItems)


##
##	/info/admin/whatsnew/add/
##
##	Add a What's new
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_whatsnew_add(request):
	breadcrumbs = getAdminBreadcrumbBase()
	breadcrumbs.append(
		{ 
			'text': 'What\'s new',
			'url': reverse('info:admin_whatsnew_list')
		}
	)

	if request.method == 'GET':
		form = WhatsNewForm()
		
		context = {
			'breadcrumbs': breadcrumbs,
			'form': form
		}
	
		response = render(request, 'info/admin_whatsnew_add.html', context)
		helpers.clearPageMessage(request)
	
	elif request.method == 'POST':
		form = WhatsNewForm(request.POST)
		
		context = {
			'breadcrumbs': breadcrumbs,
			'form': form
		}
		
		if form.is_valid():
			post = form.save(commit=False)
			post.created_by = request.user
			post.updated_by = request.user
			post.save()
			
			if post.notify_users:
				Profile.newWhatsNewForAll()
				post.sendEmails()
				post.sendSlackWhatsNewNotification()

			helpers.setPageMessage(request, 'success', 'What\'s new item was added successfully')
			response = redirect(reverse('info:admin_whatsnew_list'))
		
		else:
			response = render(request, 'info/admin_whatsnew_add.html', context)
			 
	return response


##
##	/info/admin/whatsnew/edit/<id>
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_whatsnew_edit(request, id):
	thisModel = WhatsNew
	return doCommonEditItemView(request, thisModel, id, 'heading', viewTemplate='info/admin_whatsnew_edit.html')


##
##	/info/admin/whatsnew/delete/<id>/
##
##	Delete a whats new item.
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_whatsnew_delete(request):
	return doCommonDeleteView(request, WhatsNew)


##
##	/info/admin/releasenote/
##
##	ReleaseNote list page.
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_releasenote_list(request):
	thisModel = ReleaseNote
	listItems = thisModel.objects.all()
	return doCommonListView(request, thisModel, listItems)


##
##	/info/admin/releasenote/add/
##
##	Add a ReleaseNote.
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_releasenote_add(request):
	thisModel = ReleaseNote
	return doCommonAddItemView(request, thisModel)


##
##	/info/admin/releasenote/edit/<id>
##
##	Edit a ReleaseNote.
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_releasenote_edit(request, id):
	thisModel = ReleaseNote
	return doCommonEditItemView(request, thisModel, id, 'release_number', allowDelete=True)


##
##	/info/admin/releasenote/delete/<id>/
##
##	Delete a ReleaseNote.
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def admin_releasenote_delete(request):
	return doCommonDeleteView(request, ReleaseNote)

	


