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
from django.views.decorators.csrf import csrf_exempt

from djqscsv import render_to_csv_response

from ..models import *
from ..response_data_helpers import *
from ..forms import *
from ..response_data_helpers import fetchNewUsabillaResponses, fetchNewBeeHeardResponses, convertFeedbackResponseToData
from login_required_middleware import login_exempt
import metrics.helpers as helpers
import metrics.access_helpers as accessHelpers


##
##	/research/api/artifacts/?q=<search string>
##
##
def api_artifacts_typeahead(request):
	"""
	Takes a given string and returns top 6 search results for it.
	"""
	
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
##	/research/api/userimage/ <POST DATA>
##
##	Updates existing user, uses request.user for validation
##	Called from profile edit page.
##
##
@login_required
def api_save_user_image(request):
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
##	Add/remove a user from the admin group.
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def api_adminaccess(request):
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
##	/research/api/users/togglestate/<id>/ POST: inactive='y|n'
##
##
def api_users_toggle_state(request, id):
	"""
	Takes a given user and sets their state to inactive or not, based on posted data.
	"""
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
##	/metrics/api/getnewusabillaresponses/
##
##	Called by cron app to do pull of latest usabilla responses.
##
@login_exempt
def api_get_new_usabilla_responses(request):
	helpers.runInBackground(fetchNewUsabillaResponses)
	return JsonResponse({'results': 'started' })


##
##	/metrics/api/getnewbeeheardresponses/
##
##	Called by cron app to do pull of latest beeheard responses.
##
@login_exempt
def api_get_new_beeheard_responses(request):
	helpers.runInBackground(fetchNewBeeHeardResponses)
	return JsonResponse({'results': 'started' })


##
##	/metrics/api/setresponsesgoal/
##
##	For each response ID in CSV, change the goal to the one specified.
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def api_set_responses_goal(request):
	try:
		attachment = request.FILES['file']
	except Exception as ex:
		return JsonResponse({
			'message': 'There was no file uploaded.'
		}, status=500)
	
	# We have a file, try and parse it.
	previewOnly = request.POST.get('preview', 'no')
	
	# If preview, run preview function and return JSON to display.
	# Else, run function to actually change each response's primary goal.		
	try:
		if previewOnly == 'yes':
			jsonData = VoteResponse.createGoalImportPreviewData(attachment)
			response = JsonResponse({
				'message': 'A sample preview of the response current goal and new goal is below. If it looks correct, submit it for processing.',
				'data': jsonData
			}, status=200)	
		else:
			VoteResponse.processGoalImportUpdateFile(attachment)
			response = JsonResponse({
				'message': 'Goals for your responses have been updated successfully.'
			}, status=200)	
	except Exception as ex:
		response = JsonResponse({
			'message': 'There was an error parsing the file. Maybe wrong file? Nothing happened.'
		}, status=500)

	return response


##
##	/metrics/api/deactivateoldcampaigns/
##
##	Deactivates campaigns that don't have responses after X months.
##
@login_exempt
def api_deactivate_old_campaigns(request):
	oldDate = helpers.getDaysAgo(30*9) # Older than 9 months ago.
	Campaign.objects.allActive().filter(latest_response_date__lt=oldDate).update(inactive=True)
	return JsonResponse({'results': 'done' })


##
##	/metrics/api/setuxspecialistassigned/
##
##	Called by cron app to do daily check and set any pre-dated ux specialist assigned flags.
##
@login_exempt
def api_set_ux_specialist_assigned(request):
	Project.updateAllUxSpecialistflags()
	return JsonResponse({'results': 'done' })


##
##	/metrics/api/prunealerthistory/
##
##	Called by cron app to trim alert history to 90 days back.
##
@login_exempt
def api_prune_alert_history(request):
	Alert.objects.filter(date__lt=helpers.getDaysAgo(90)).delete()
	return JsonResponse({'results': 'done' })


##
##	/metrics/api/pruneactivitylog/
##
##	Called by cron app to trim activity log to 2000.
##
@login_exempt
def api_prune_activity_log(request):
	try:
		afterDate = ActivityLog.objects.all()[2000:2001].first().timestamp
		ActivityLog.objects.filter(timestamp__lt=afterDate).delete()
	except:
		pass
	return JsonResponse({'results': 'done' })


##
##	/metrics/api/scheduledalerts/
##
@login_exempt
def api_do_scheduled_alerts(request):
	helpers.runInBackground(Alert.doScheduledAlerts)
	return JsonResponse({'results': 'started' })


##
##	/metrics/api/projects/responses/download/
##
##	Return all responses for the given project.
##
##
@login_exempt
def api_projects_vote_responses(request):
	key = request.GET.get('key', 'xxx')
	#project = request.GET.get('project', None)
	
	project = get_object_or_404(Project, api_key=key)
	
	# if request.user.isProjectAdmin(project):
	# 	response = JsonResponse({
	# 		'responses': list(project.getVoteResponses().values_list('raw_data', flat=True))
	# 	}, status=200)
	# else:
	# 	response = JsonResponse({
	# 		'error': 'Not authorized. Only project admins can perform this operation.'
	# 	}, status=403)
	if request.user.is_authenticated:
		apiUser = request.user
		apiUserName = request.user.username
	else:
		apiUser = None
		apiUserName = 'Anonymous user'
	
	newActivity = ActivityLog.objects.create(
		user = apiUser,
		comments = f'Response API view: The download API URL for {project.name} was hit by: {apiUserName}'
	)
		
	response = JsonResponse({
		'responses': list(project.getVoteResponses().values_list('raw_data', flat=True))
	}, status=200)
	
	response["Access-Control-Allow-Origin"] = "*"
	return response


##
##	/metrics/api/removeoldemails/
##
@login_exempt
def api_remove_old_emails(request):
	VoteResponse.removeOldEmailValues()
	FeedbackResponse.removeOldEmailValues()
	OtherResponse.removeOldEmailValues()
	return JsonResponse({'results': 'done' })


##
##	/metrics/api/projects/links/
##
def api_projects_links(request):
	return JsonResponse({
		'results': list(Project.objects.allActive().order_by(Lower('name')).values_list('name', 'id'))
	}, status=200)



##
##	/metrics/api/projects/responses/vote/export/csv/
##
def api_project_vote_responses_to_csv(request):
	try:
		project = get_object_or_404(Project, id=request.GET.get('project'))
	except Exception as ex:
		return render(request, '404.html', {}, status=404)
	
	# Get proper report period, snapshot, and responses based on the project and report period selected.
	reportPeriodData = project.getReportPeriodData(request)
	projectSnapshotResponses = reportPeriodData['projectSnapshotResponses']
	
	return render_to_csv_response(projectSnapshotResponses.values('date', 'improvement_suggestion', 'goal_not_completed_reason', 'comments', 'nps', 'umux_capability', 'umux_ease_of_use', goal=F('primary_goal__name')))


##
##	/metrics/api/projects/responses/feedback/export/csv/
##
def api_project_feedback_responses_to_csv(request):
	try:
		project = get_object_or_404(Project, id=request.GET.get('project'))
	except Exception as ex:
		return render(request, '404.html', {}, status=404)
	
	isProjectEditor = accessHelpers.isProjectEditor(request.user, project)
	
	if not isProjectEditor:
		return render(request, '403.html', {}, status=403)
	
	responses = project.getFeedbackResponses()
	
	return render_to_csv_response(responses.values('date', 'rating', 'feedback_type', 'comments', country=F('raw_data__data__email'), email=F('raw_data__data__cc')))


##
##	/metrics/api/activeusabillacampaigns/
##
@login_exempt
def api_active_usabilla_campaigns(request):
	campaigns = list(Campaign.objects.fromUsabilla().allActive().filter(project__isnull=False).order_by('project__name').values('uid','project__id', 'project__name', 'project__domain__id', 'project__domain__name').distinct())
		
	return JsonResponse({'campaigns': campaigns })
	
