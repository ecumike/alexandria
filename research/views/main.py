import io
import requests
import sys
import traceback


from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count, Value, Q, Sum
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.debug import ExceptionReporter

from django.conf import settings
from ..models import *
from ..helpers import *
from ..forms import *
from metrics.helpers import runInBackground

############################################################
#### Redirects
############################################################

##	/research/<ID>/
##
def redirect_artifacts_detail(request, id):
	'''
	Redirect from old detail URL to new one. If invalid, sent to home page.
	'''
	if id.isdigit():
		url = reverse('research:artifacts_detail', kwargs={'id':id})
	else:
		url = '/'
	return redirect(url)

############################################################
##
##	/research/
##
def home(request):
	searchResults = Artifact.getArtifacts(request)
	
	artifacts = searchResults['artifacts']
	resultsCount = artifacts.count()
	selectedMethods = searchResults['selectedMethods']
	selectedSources = searchResults['selectedSources']
	selectedStatuses = searchResults['selectedStatuses']
	selectedTags = searchResults['selectedTags']
	selectedProjects = searchResults['selectedProjects']
	qParam = searchResults['qParam']
	
	# Get unique list of taxonomy items that exist across the found set of artifacts.
	# This HAS to come before pagination else we only get values across the 40 we initially show.
	methods = Method.objects.filter(artifact_methods__in=artifacts).distinct().only('name').annotate(numArtifacts=Count('artifact_methods')).order_by('name')
	sources = Source.objects.filter(artifact_source__in=artifacts).distinct().only('name').annotate(numArtifacts=Count('artifact_source')).order_by('name')
	statuses = Status.objects.filter(artifact_status__in=artifacts).distinct().only('name').annotate(numArtifacts=Count('artifact_status')).order_by('name')
	tags = Tag.objects.filter(artifact_tags__in=artifacts).distinct().only('name').annotate(numArtifacts=Count('artifact_tags')).order_by('name')
	projects = Project.objects.allActive().filter(artifact_projects__in=artifacts).distinct().only('name').annotate(numArtifacts=Count('artifact_projects')).order_by('name')

	# Do pagination. We only show first 40 initial page load, then API is used for "load more".
	page = 1
	artifactPaginator = Paginator(artifacts, 200) # Show 200 artifacts per request.
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
		'selectedMethods': selectedMethods,
		'selectedSources': selectedSources,
		'selectedStatuses': selectedStatuses,
		'selectedTags': selectedTags,
		'selectedProjects': selectedProjects,
		'artifacts': artifactsToShow,
		'hasNextPage': artifactsToShow.has_next(),
		'methods': methods,
		'resultsCount': resultsCount,
		'sources': sources,
		'statuses': statuses,
		'tags': tags,
		'projects': projects,
		'userEditableArtifacts': userEditableArtifacts
	}
	
	# Track search string hit.
	if qParam:
		ArtifactSearch.trackSearch(qParam)
	
	response = render(request, 'research/home.html', context)
	clearPageMessage(request)
	return response



##
##	/research/<id>/detail/
##
def artifacts_detail(request, id):
	try:
		artifact = Artifact.objects.filter(id=id).select_related('owner__profile', 'source', 'status').prefetch_related('tags', 'methods', 'related_artifacts', 'projects')[0]
	except Exception as ex:
		return render(request, '404.html', {}, status=404)
	
	excludestrings = list(SurveyQuestionExclusion.objects.all().values_list('question_text', flat=True))
	surveyQuestions = artifact.alchemer_survey_questions
	surveyQuestionsFiltered = []
	if surveyQuestions:
		surveyQuestionsFiltered = [questionText for questionText in surveyQuestions if
		  all(excludeMatch.lower() not in questionText.lower() for excludeMatch in excludestrings)]
		  
	
	breadcrumbs = [
		{ 
			'text': 'Research',
			'url': reverse('research:home')
		}
	]
	
	try:
		canEdit = request.user.hasEditorAccess(artifact)
	except:
		canEdit = False
		
	context = {
		'breadcrumbs': breadcrumbs,
		'artifact': artifact,
		'canEditArtifact': canEdit,
		'surveyQuestionsFiltered': surveyQuestionsFiltered,
	}

	response = render(request, 'research/artifacts_detail.html', context)
	clearPageMessage(request)

	return response
	
	
##
##	/myresearch/
##
@login_required
def myresearch(request):
	'''
	Personalized page of research user has created.
	'''
	breadcrumbs = [
		{ 
			'text': 'Research',
			'url': reverse('research:home')
		}
	]

	context = {
		'breadcrumbs': breadcrumbs,
		'artifacts': Artifact.objects.filter(Q(created_by=request.user) | Q(owner=request.user) | Q(editors=request.user)).distinct()
	}
	
	response = render(request, 'research/myresearch.html', context)
	clearPageMessage(request)

	return response


##
##	/research/add/
##
@login_required
def artifacts_add(request):
	'''
	Add a new Artifact - Public (signed in user) way to do it.
	Admins can use admin center page.
	'''
	breadcrumbs = [
		{ 
			'text': 'Research',
			'url': reverse('research:home')
		}
	]

	statuses = Status.objects.all()
	sources = Source.objects.all()
	methods = Method.objects.all()
	
	if request.method == 'GET':
		form = ArtifactForm()
		form.fields['owner'].initial = request.user
		
		context = {
			'breadcrumbs': breadcrumbs,
			'form': form,
			'statuses': statuses,
			'sources': sources,
			'methods': methods
		}

		response = render(request, 'research/artifacts_add.html', context)
		clearPageMessage(request)

	elif request.method == 'POST':
		# Remove empties from array fields and set field values to cleaned arrays.
		request.POST._mutable = True
		request.POST['study_plan_urls'] = cleanArray(request.POST.getlist('study_plan_urls',[]))
		request.POST['final_report_urls'] = cleanArray(request.POST.getlist('final_report_urls',[]))
		request.POST['external_research_urls'] = cleanArray(request.POST.getlist('external_research_urls',[]))
		request.POST['findings'] = json.dumps(cleanArray(request.POST.getlist('findings',[])))
		
		form = ArtifactForm(request.POST)
		form.fields['owner'].initial = request.user
		
		context = {
			'breadcrumbs': breadcrumbs,
			'form': form,
			'statuses': statuses,
			'sources': sources,
			'methods': methods,
		}
		
		if form.is_valid():
			post = form.save(commit=False)
			post.created_by = request.user
			post.updated_by = request.user

			# Save it.
			post.save()
			form.save_m2m()
			
			post.storeUserResearchCount()
			
			runInBackground(post.getAlchemerSurveyQuestions)
			
			if request.POST.get('notify_owner_new', '') == 'yes':
				runInBackground(post.notifyOwnerNewArtifact)
			
			setPageMessage(request, 'success', 'Artifact was added successfully')

			response = redirect(reverse('research:home'))

			# Send slack notification a new item has been created.
			sendSlackNewArtifactNotification(request.user, post, reverse('research:artifacts_detail', kwargs={'id':post.id}))
		 
		else:
			response = render(request, 'research/artifacts_add.html', context)
			 
	return response


##
##	/research/edit/<id>/
##
@login_required
def artifacts_edit(request, id):
	'''
	Edit an Artifact.
	'''
	artifact = get_object_or_404(Artifact, id=id)
	
	if not hasEditorAccess(request.user, artifact):
		return render(request, '403.html', status=403)
	
	breadcrumbs = [
		{ 
			'text': 'Research',
			'url': reverse('research:home')
		}
	]

	statuses = Status.objects.all()
	sources = Source.objects.all()
	methods = Method.objects.all()
	
	if request.method == 'GET':
		form = ArtifactForm(instance=artifact)
		
		context = {
			'breadcrumbs': breadcrumbs,
			'artifact': artifact,
			'form': form,
			'statuses': statuses,
			'sources': sources,
			'methods': methods
		}
		
		response = render(request, 'research/artifacts_edit.html', context)
		clearPageMessage(request)

	elif request.method == 'POST':
		# Remove empties from array fields and set field values to cleaned arrays.
		request.POST._mutable = True
		request.POST['study_plan_urls'] = cleanArray(request.POST.getlist('study_plan_urls',[]))
		request.POST['final_report_urls'] = cleanArray(request.POST.getlist('final_report_urls',[]))
		request.POST['external_research_urls'] = cleanArray(request.POST.getlist('external_research_urls',[]))
		request.POST['findings'] = json.dumps(cleanArray(request.POST.getlist('findings',[])))
		
		form = ArtifactForm(request.POST, instance=artifact)
		
		context = {
			'breadcrumbs': breadcrumbs,
			'artifact': artifact,
			'form': form,
			'statuses': statuses,
			'sources': sources,
			'methods': methods,
		}
		
		if form.is_valid():
			# Send slack notification if status changed to completed.
			existingStatus = Artifact.objects.get(id=artifact.id).status
			if artifact.status != existingStatus and artifact.status.name == 'Completed':
				sendSlackCompletedArtifactNotification(request.user, artifact, reverse('research:artifacts_detail', kwargs={'id':artifact.id}))
			
			post = form.save(commit=False)
			post.updated_by = request.user			

			# Save it
			post.save()
			form.save_m2m()
			
			post.storeUserResearchCount()
			
			runInBackground(post.getAlchemerSurveyQuestions)
			
			setPageMessage(request, 'success', 'Artifact was updated successfully')
			response = redirect(reverse('research:home'))
		 
		else:
			response = render(request, 'research/artifacts_edit.html', context)
			 
	return response



##
##	/research/<id>/archive/
##
@login_required
def artifacts_archive(request, id):
	'''
	Archive an Artifact.
	'''
	artifact = get_object_or_404(Artifact, id=id)
	
	if not hasEditorAccess(request.user, artifact):
		return render(request, '403.html', status=403)
	
	breadcrumbs = [
		{ 
			'text': 'Research',
			'url': reverse('research:home')
		}
	]
	
	context = {
		'breadcrumbs': breadcrumbs,
		'artifact': artifact,
		'childrenArtifacts': Artifact.objects.filter(related_artifacts=artifact.id),
		'pageViews': PageView.objects.filter(url=(reverse('research:artifacts_detail', kwargs={'id':artifact.id}))).aggregate(totalViews=Sum('view_count'))['totalViews']
	}

	if request.method == 'GET':
		response = render(request, 'research/artifacts_archive.html', context)

	elif request.method == 'POST':		
		if request.POST.get('do', '') == 'delete':
			try:
				artifact.archived = True
				artifact.save()
				setPageMessage(request, 'success', 'Artifact was archived successfully')
				response = redirect(reverse('research:home'))
		
			except Exception as ex:
				setPageMessage(request, 'error', 'There was a problem archiving the artifact:<br>{}'.format(strex(ex)))
				response = render(request, 'research/artifacts_archive.html', context)
				clearPageMessage(request)		
		else:
			setPageMessage(request, 'error', 'There was nothing to do')
			response = render(request, 'research/artifacts_archive.html', context)
			clearPageMessage(request)
			 
	return response



##
##	/research/<id>/unarchive/
##
@login_required
def artifacts_unarchive(request, id):
	'''
	Unarchive an Artifact.
	'''
	artifact = get_object_or_404(Artifact, id=id)
	
	if not hasEditorAccess(request.user, artifact):
		return render(request, '403.html', status=403)
	
	breadcrumbs = [
		{ 
			'text': 'Research',
			'url': reverse('research:home')
		}
	]

	context = {
		'breadcrumbs': breadcrumbs,
		'artifact': artifact,
		'childrenArtifacts': Artifact.objects.filter(related_artifacts=artifact.id),
		'pageViews': PageView.objects.filter(url=(reverse('research:artifacts_detail', kwargs={'id':artifact.id}))).aggregate(totalViews=Sum('view_count'))['totalViews']
	}

	if request.method == 'GET':
		response = render(request, 'research/artifacts_unarchive.html', context)

	elif request.method == 'POST':		
		if request.POST.get('do', '') == 'delete':
			try:
				artifact.archived = False
				artifact.save()
				setPageMessage(request, 'success', 'Artifact was republished successfully')
				response = redirect(reverse('research:home'))
		
			except Exception as ex:
				setPageMessage(request, 'error', 'There was a problem republishing the artifact:<br>{}'.format(strex(ex)))
				response = render(request, 'research/artifacts_unarchive.html', context)
				clearPageMessage(request)		
		else:
			setPageMessage(request, 'error', 'There was nothing to do')
			response = render(request, 'research/artifacts_unarchive.html', context)
			clearPageMessage(request)
			 
	return response



##
##	/research/<id>/delete/
##
@user_passes_test(hasAdminAccess_decorator)
def artifacts_delete(request, id):
	'''
	Delete an Artifact.
	'''
	artifact = get_object_or_404(Artifact, id=id)
	
	breadcrumbs = [
		{ 
			'text': 'Research',
			'url': reverse('research:home')
		}
	]

	context = {
		'breadcrumbs': breadcrumbs,
		'artifact': artifact,
		'childrenArtifacts': Artifact.objects.filter(related_artifacts=artifact.id),
		'pageViews': PageView.objects.filter(url=(reverse('research:artifacts_detail', kwargs={'id':artifact.id}))).aggregate(totalViews=Sum('view_count'))['totalViews']
	}

	if request.method == 'GET':
		response = render(request, 'research/artifacts_delete.html', context)

	elif request.method == 'POST':		
		if request.POST.get('do', '') == 'delete':
			try:
				artifact.delete()
				setPageMessage(request, 'success', 'Artifact was deleted successfully')
				response = redirect(reverse('research:home'))
		
			except Exception as ex:
				setPageMessage(request, 'error', 'There was a problem deleting the artifact:<br>{}'.format(strex(ex)))
				response = render(request, 'research/artifacts_delete.html', context)
				clearPageMessage(request)		
		else:
			setPageMessage(request, 'error', 'There was nothing to do')
			response = render(request, 'research/artifacts_delete.html', context)
			clearPageMessage(request)
			 
	return response


##
##	/research/file/<file>
##
def get_file(request):
	'''
	Gets the requested file from COS and echos it back
	'''
	attachment = get_object_or_404(Attachment, name=request.GET.get('filename', None))
	
	file = attachment.getFile()
	
	if file:
		fileHeaders = file['ResponseMetadata']['HTTPHeaders']
		response = HttpResponse(file['Body'].read())
		response['content-length'] = fileHeaders['content-length']
		
		if attachment.name.endswith('.xlsx'):
			response['content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
			response['content-disposition'] = 'filename="{}"'.format(attachment.getFileName())
		elif attachment.name.endswith('.pptx'):
			response['content-type'] = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
			response['content-disposition'] = 'filename="{}"'.format(attachment.getFileName())
		else:
			response['content-type'] = fileHeaders['content-type']	
	else:
		response = render(request, '404.html', {}, status=404)
	
	return response


########################################################
########################################################
##
## Standards views in each app, direct copy/paste.
##
########################################################
########################################################

##
##	/research/signin/
##
def signin(request):
	'''
	Sign in page
	'''
	response = render(request, 'signin.html', {
		'form': AuthenticationForm,
	})
	
	## If user is already signed in they don't need to be here, so redirect them to home page.
	if request.user.is_authenticated:
		response = redirect(request.GET.get('next', reverse('research:home')))
	
	elif request.method == 'GET':
		response = render(request, 'signin.html', {
			'form': AuthenticationForm,
		})
		
	elif request.method == 'POST':
		username = request.POST['username']
		password = request.POST['password']
		
		# NOTE: This ensures all usernames/emails to be lowercase. Prevents mismatch
		# for users with mix-case emails.
		try:
			user = authenticate(request, username=username.lower(), password=password)
		except Exception as ex:
			context = {
				'form': AuthenticationForm,
				'error': 'Uh oh, we were unable to authenticate you. Check your ID/PW and try again.',
			}
			
			return render(request, 'signin.html', context)
		
		## Success
		if user is not None:
			login(request, user)
			
			# Hit some company profile API to create/update their profile.
			updateUserProfile(user)
			
			# Send them back to the page they originally went to before they had to sign in.
			response = redirect(request.POST.get('next', reverse('info:home')))
			
		## Fail
		else:
			context = {
				'form': AuthenticationForm,
				'error': 'DOH! It seems your ID/PW combination wasn\'t quite right.<br>Please try again.',
			}
			response = render(request, 'signin.html', context)
	
	return response
	

##
##	/research/signout/
##
def signout(request):
	'''
	Signs the user out.
	'''
	logout(request)
	return render(request, "signout.html", {})


##
##	404
##
def custom_404(request, exception):
	'''
	This is only needed if you want to do custom processing when a 404 happens.
	'''
	referer = request.META.get('HTTP_REFERER', 'None')

	try:
		userCaused = '\n*User:* {}'.format(request.user.username)
	except: 
		userCaused = ''	

	if request.get_host() in referer:
		sendSlackAlert(404, '*Requested path:*  {}\n*Referring page:* {}{}'.format(request.get_full_path(), referer, userCaused))
		
	return render(request, '404.html', {}, status=404)
	

##
##	500
##
def custom_500(request):
	'''
	This is only needed if you want to do custom processing when a 500 happens.
	'''
	exc_info = sys.exc_info()
	errorTitle = exc_info[:2]
	
	errMsg = errorTitle or '(No error provided)'
	errMsg = str(errMsg)

	referer = request.META.get('HTTP_REFERER', 'None')

	try:
		userCaused = '\n*User:* {}'.format(request.user.username)
	except: 
		userCaused = ''	

	# Send slack alert
	sendSlackAlert(500, '*Requested path:* {}\n*Referring page:* {}{}\n*Error msg:* {}\nCheck email for full debug.'.format(request.get_full_path(), referer, userCaused, errMsg))
		
	return render(request, '500.html', {}, status=500)
	
