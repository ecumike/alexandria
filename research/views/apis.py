import io
import requests
import sys

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count, Value
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.urls import reverse

from ..models import *
from ..helpers import *
from ..forms import *
from login_required_middleware import login_exempt


##
##	/research/api/artifacts/search/ <getparams>
##
def api_artifacts_search(request):
	'''
	Used on home page "load more" button at bottom.
	Gets 40 more artifacts, with offset/pagination, and returns the HTML
	to inject at the bottom of the page.
	'''
	searchResults = Artifact.getArtifacts(request)
	
	page = request.GET.get('page')
	artifactPaginator = Paginator(searchResults['artifacts'], 200) # Show 40 artifacts per request.
	artifactsToShow = artifactPaginator.get_page(page)
	
	# Admins can edit everything, else get list of artifacts user has auth to edit.
	try:
		if request.user.hasAdminAccess():
			userEditableArtifacts = Artifact.objects.values_list('id', flat=True)
		else:
			userEditableArtifacts = Artifact.objects.filter(Q(owner=request.user) | Q(created_by=request.user) | Q(editors=request.user)).values_list('id', flat=True)
	except:
		userEditableArtifacts = []

	
	context = {
		'artifacts': artifactsToShow,
		'userEditableArtifacts': userEditableArtifacts,
		'request': request
	}
	
	html = render_to_string('research/partials/artifacts_list_items.html', context)
	
	return JsonResponse({
		'pageNum': artifactsToShow.number,
		'hasNextPage': artifactsToShow.has_next(),
		'resultsHtml': html
	})


##
##	/research/api/artifacts/?q=<search string>
##
def api_artifacts_typeahead(request):
	'''
	Takes a given string and returns top 6 search results for it.
	'''
	textString = request.GET.get('q', '')
	
	urlList = []

	if textString != '':
		urlList = list(Artifact.objects.filter(name__icontains=textString)[:10].values('id', 'name'))
	
	response = JsonResponse({
		'results': urlList 
	})
	response["Access-Control-Allow-Origin"] = "*"
	return response


@login_exempt
def api_users(request):
	responseData = {
		'results': list(User.objects.filter(username__contains='@').order_by('username').values_list('username', flat=True))
	}
	return JsonResponse(responseData, status=200)


##
##	/research/api/users/add/<POST DATA>
##
@login_required
def api_users_add(request):
	'''
	Creates a user with the passed email and name. Basic.
	Returns the user object ID and user's name (for optional display).
	'''
	email = request.POST.get('email')
	httpCode = 404
	
	# NOTE: This ensures all usernames/emails to be lowercase. Prevents mismatch
	# for users with mix-case emails.
	try:
		user = createNewUser(email)
		
		httpCode = 200
		responseData = {
			'id': user.id,
			'username': user.username,
			'fullName': user.profile.full_name
		}
	except Exception as ex:
		httpCode = 500
		responseData = {
			'results': {
				'message': repr(ex)
			}
		}
		
	return JsonResponse(responseData, status=httpCode)
	

##
##	/research/api/userimage/ <POST DATA>
##
@login_required
def api_save_user_image(request):
	'''
	Updates existing user, uses request.user for validation
	Called from profile edit page.
	'''
	try:
		user = User.objects.get(username=request.POST.get('email').lower())
		
		# Now update profile record and save.
		user.profile.updateFromPost(request.POST)
		user.save()
	
		httpCode = 200
		responseData = {
			'results': {'message': 'success'}
		}
		
	except Exception as ex:
		httpCode = 500
		responseData = {
			'results': {
				'message': repr(ex)
			}
		}
	
	return JsonResponse(responseData, status=httpCode)


##
##	/research/api/adminaccess/<POST>
##
@user_passes_test(hasAdminAccess_decorator)
def api_adminaccess(request):
	'''
	Add/remove a user from the admin group.
	'''
	email = request.POST.get('email')
	action = request.POST.get('action')
	adminGroup, created = Group.objects.get_or_create(name='admins')
	httpCode = 404
	
	# If user no existy, throw back default 404.
	try:
		user = User.objects.get(username=email)
	except Exception as ex:
		responseData = {
			'results': {
				'message': repr(ex)
			}
		}
		
	if user:
		if action == "add":
			user.groups.add(adminGroup) 
			httpCode = 200
			responseData = {
				'results': {
					'id': user.id,
					'name': user.profile.full_name,
					'username': user.username
				}
			}
		elif action == "remove":
			adminGroup.user_set.remove(user)
			httpCode = 200
			responseData = {
				'results': {
					'message': 'User removed successfully'
				}
			}
		else:
			httpCode = 400
			responseData = {
				'results': {
					'message': 'You forgot to tell me what to do; add or remove the user.'
				}
			}
		
	return JsonResponse(responseData, status=httpCode)
	
	
##
##	/research/api/tag/? id=## or name=abc
##
def api_get_tag(request):
	'''
	Find tag by name, return the ID. Used to dynamically select tags on "add research" entry template.
	'''
	responseData = {}
	tagName = request.GET.get('name', '')
	tagId = request.GET.get('id', '')
	
	if tagName:
		tag = Tag.objects.filter(name__iexact=tagName)
	elif tagId: 
		tag = Tag.objects.filter(id=tagId)
	
	if tag.exists():
		responseData = {
			'id': tag.get().id
		}
	
	return JsonResponse(responseData, status=200)
	
	
##
##	/research/api/users/togglestate/<id>/ POST: inactive='y|n'
##
def api_users_toggle_state(request, id):
	'''
	Takes a given user and sets their state to inactive or not, based on posted data.
	'''
	user = get_object_or_404(User, id=id)
	setInactive = request.GET.get('inactive', '')
	
	if setInactive == 'y':
		user.profile.inactive = True
	elif setInactive == 'n':
		user.profile.inactive = False
	user.save()

	return JsonResponse({
		'results': user.profile.inactive 
	})



##
##	/research/api/pv/
##
def api_page_view_tracker(request):
	'''
	Increment the hit count to the URL for the user, or creates it as 1.
	'''
	try:
		try:
			page = request.POST['page']
		except:
			page = request.META.get('HTTP_REFERER', 'None').split('.REPLACE_ME.com')[1]
		
		if request.user.username:	
			pv, created = PageView.objects.get_or_create(
				url = page,
				user = request.user
			)
			pv.view_count = pv.view_count + 1
			pv.save()
	except Exception as ex:
		pass
	
	return JsonResponse({})


##
##	/research/api/brokenlink/
##
def api_report_broken_link(request):
	'''
	Used next to links for users to report them as broken.
	'''
	try:
		artifact = Artifact.objects.get(id=request.POST.get('artifact'))
		linkUrl = request.POST.get('link_url', '')
		
		brokenLink, created = BrokenLink.objects.get_or_create(
			artifact = artifact,
			link_url = linkUrl,			
		)
		brokenLink.report_count = brokenLink.report_count + 1
		brokenLink.save()
	except Exception as ex:
		pass
		
	artifact.notifyBrokenLink(linkUrl)
	
	return JsonResponse({'message': 'Success'})


##
##	/research/api/file/upload/<POST DATA>
##
def api_upload_file(request):
	'''
	Takes a file, uploads to COS, creates Attachment obj and returns it.
	'''
	httpCode = 404
	if request.method == 'POST':
		attachment = Attachment.storeFile(request.user, request.FILES['file'])
		
		if attachment:
			httpCode = 200
			responseData = {
				'id': attachment.id,
				'fileName': attachment.name,
				'displayName': attachment.getFileName()
			}
		else:
			responseData = {
				'message': 'There was a problem uploading and saving the file.'
			}
	else:
		httpCode = 405
		responseData = {}
		
	return JsonResponse(responseData, status=httpCode)


##
##	/research/api/file/delete/<POST DATA>
##
def api_delete_file(request):
	'''
	Takes a file, deleted from COS and Attachment obj and returns it.
	'''
	httpCode = 200
	
	responseData = {
		'id': '',
		'fileName': '',
		'displayName': ''
	}
	
	# If we can't delete the attachment or file because it doesn't exist, it doesn't matter.
	# Therefore we just always return a success (if POST) so the UI always removes it.
	if request.method == 'POST':
		try:
			fileName = request.POST.get('filename', None)
			if Attachment.objects.get(name=fileName).deleteFile():
				Attachment.objects.get(name=fileName).delete()
		except Exception as ex:
			pass

	return JsonResponse(responseData, status=httpCode)


##
##	/research/api/file/relate/<POST DATA>
##
def api_relate_file(request):
	'''
	Takes an Attachment obj and related it to the research item.
	'''
	httpCode = 200
	
	if request.method == 'POST':
		try:
			artifact = Artifact.objects.get(id=request.POST.get('artifactId',None))
			getattr(artifact, request.POST.get('fieldName',None)).add(request.POST.get('attachmentId',None))
		except Exception as ex:
			print(ex)

	return JsonResponse({'message':'done'}, status=httpCode)


