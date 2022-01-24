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
from login_required_middleware import login_exempt
import metrics.helpers as helpers
import metrics.access_helpers as accessHelpers


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
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def api_adminaccess(request):
	'''
	Add/remove a user from the admin group.email = request.POST.get('email')
	'''
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
##	/metrics/api/getnewusabillaresponses/
##
@login_exempt
def api_get_new_usabilla_responses(request):
	'''
	Called by cron app to do pull of latest usabilla responses.
	'''
	helpers.runInBackground(fetchNewUsabillaResponses)
	return JsonResponse({'results': 'started' })


##
##	/metrics/api/getnewbeeheardresponses/
##
@login_exempt
def api_get_new_beeheard_responses(request):
	'''
	Called by cron app to do pull of latest beeheard responses.
	'''
	helpers.runInBackground(fetchNewBeeHeardResponses)
	return JsonResponse({'results': 'started' })


##
##	/metrics/api/setresponsesgoal/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def api_set_responses_goal(request):
	'''
	For each response ID in CSV, change the goal to the one specified.
	'''
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
@login_exempt
def api_deactivate_old_campaigns(request):
	'''
	Deactivates campaigns that don't have responses after X months.
	'''
	oldDate = helpers.getDaysAgo(30*9) # Older than 9 months ago.
	Campaign.objects.allActive().filter(latest_response_date__lt=oldDate).update(inactive=True)
	return JsonResponse({'results': 'done' })


##
##	/metrics/api/setuxspecialistassigned/
##
@login_exempt
def api_set_ux_specialist_assigned(request):
	'''
	Called by cron app to do daily check and set any pre-dated ux specialist assigned flags.
	'''
	Project.updateAllUxSpecialistflags()
	return JsonResponse({'results': 'done' })


##
##	/metrics/api/prunealerthistory/
##
@login_exempt
def api_prune_alert_history(request):
	'''
	Called by cron app to trim alert history to 90 days back.
	'''
	Alert.objects.filter(date__lt=helpers.getDaysAgo(90)).delete()
	return JsonResponse({'results': 'done' })


##
##	/metrics/api/pruneactivitylog/
##
@login_exempt
def api_prune_activity_log(request):
	'''
	Called by cron app to trim activity log to 2000.
	'''
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
@login_exempt
def api_projects_vote_responses(request):
	'''
	Return all responses for the given project.
	'''
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
	'''
	Used for "project links" overlay. Dynamically get this list and display overlay with them.
	'''
	return JsonResponse({
		'results': list(Project.objects.allActive().order_by(Lower('name')).values_list('name', 'id'))
	}, status=200)


##
##	/metrics/api/activeusabillacampaigns/
##
@login_exempt
def api_active_usabilla_campaigns(request):
	'''
	Return a list of active Usabilla campaigns. BeeHeard hits this daily and imports any new ones.
	'''
	campaigns = list(Campaign.objects.fromUsabilla().allActive().filter(project__isnull=False).order_by('project__name').values('uid','project__id', 'project__name', 'project__domain__id', 'project__domain__name').distinct())
		
	return JsonResponse({'campaigns': campaigns })
	

##
##	/metrics/api/survey/submit/rawdata/
##
@login_exempt
@csrf_exempt
def api_survey_submit_raw_data(request):
	'''
	All surveys POST submit to this URL. Take fields and store response.
	'''
	requestJson = json.loads(request.body)
	try:
		# Push campaign ID/key into mapping so "convert response" can find and use it.
		CAMPAIGNS_ID_NAME_MAP[requestJson['campaignId']] = requestJson['campaignKey']
		
		response = convertFeedbackResponseToData(requestJson['data'])
		FeedbackResponse.objects.create(**response)
	except Exception as ex:
		print(f'Error: api_survey_submit_raw_data failed - {ex}')
	
	return JsonResponse({'message': 'done' })
	

##
##	/metrics/api/addbeeheardcampaign
##
@login_exempt
@csrf_exempt
def api_add_beeheard_campaign(request):
	'''
	When BeeHeard saves a campaign, if the "feed to lux" box is checked, it hits this so we can create 
	the campaign in LUX (if it doesn't exist already)
	'''
	requestJson = json.loads(request.body)
	
	scriptUser = getBeeHeardImportScriptUser()
	
	if not Campaign.objects.filter(uid=requestJson['uid']).exists():
		try:
			project = Project.objects.get(beeheard_id=requestJson['project']['id'])
		except:
			project, created = Project.objects.get_or_create(name = requestJson['project']['name'],
				defaults = {
					'created_by': scriptUser,
					'updated_by': scriptUser,
					'domain': None,
				}
			)
			project.beeheard_id = requestJson['project']['id']
			project.save()
			
		try:
			campaign = Campaign.objects.create(
				created_by = scriptUser,
				updated_by = scriptUser,
				uid=requestJson['uid'],
				project = project,
			)
			newActivity = ActivityLog.objects.create(
				user = scriptUser,
				comments = f'Added campaign {campaign.uid} from BeeHeard because it was saved with "feed to lux" flag'
			)
		except Exception as ex:
			print(f"Error: api_add_beeheard_campaign couldn't create campaign {requestJson['uid']}: {ex}")
		
	return JsonResponse({'results': 'done'}, status=200)


##
##	/metrics/api/deleteresponse/
##
@user_passes_test(accessHelpers.hasAdminAccess)
def api_delete_response(request):
	'''
	Admins only: Project responses list - "delete this response" trashcan link hits this.
	'''
	if request.POST.get('type', False) == 'vote':
		responseModelToUse = VoteResponse
	elif request.POST.get('type', False) == 'feedback':
		responseModelToUse = FeedbackResponse
	elif request.POST.get('type', False) == 'other':		
		responseModelToUse = OtherResponse
	else:
		return JsonResponse({'results': {'message': f'{ex}'}}, status=400)
		
	try:
		response = responseModelToUse.objects.get(id=request.POST.get('id'))
		response.delete()
	except Exception as ex:
		return JsonResponse({'results': {'message': f'{ex}'}}, status=400)
	
	return JsonResponse({'results': {'message': 'Success.'}}, status=200)
	
	
##
##	/metrics/api/deleteprojectresponses/
##
@user_passes_test(accessHelpers.hasAdminAccess)
def api_delete_project_responses(request):
	'''
	Admin only - Project's response list page "delete all responses" hits this.
	'''
	if request.POST.get('type', False) == 'vote':
		responseModelToUse = VoteResponse
	elif request.POST.get('type', False) == 'feedback':
		responseModelToUse = FeedbackResponse
	elif request.POST.get('type', False) == 'other':		
		responseModelToUse = OtherResponse
	else:
		return JsonResponse({'results': {'message': f'{ex}'}}, status=400)
	
	try:
		project = Project.objects.get(id=request.POST.get('id'))
	except Exception as ex:
		return JsonResponse({'results': {'message': f'{ex}'}}, status=400)
	
	try:
		responseModelToUse.objects.filter(campaign__project=project).delete()
	except Exception as ex:
		return JsonResponse({'results': {'message': f'{ex}'}}, status=400)
	
	return JsonResponse({'results': {'message': 'Success.'}}, status=200)
	
	
##
##	/metrics/api/recalculatesnapshot/
##
@user_passes_test(accessHelpers.hasAdminAccess)
def api_recalculate_snapshot(request):
	'''
	Admin only - Link on vote response list pages for projects. 
	'''
	try:
		project = Project.objects.get(id=request.POST.get('project'))
		reportPeriod = request.POST.get('reportperiod')
		
		try:
			if 'last90' in reportPeriod:
				project.updateLast90Snapshot()
			elif 'q' in reportPeriod:
				quarterYear = reportPeriod.split('q')
				project.updateQuarterSnapshot(year=quarterYear[1], quarter=quarterYear[0])
		except Exception as ex:
			return JsonResponse({'results': {'message': f'{ex}'}}, status=400)
		
		try:
			project.domain.updateDomainYearSnapshot(year=quarterYear[1])
		except:
			pass
	except Exception as ex:
		return JsonResponse({'results': {'message': f'{ex}'}}, status=400)
		
	return JsonResponse({'results': {'message': 'Success.'}}, status=200)
	


