import base64
import csv
import dateutil.parser
import io
import json
import logging
import operator
import os
import requests
import sys
import time
import traceback
import usabilla as ub
import pandas as pd


from user_agents import parse
from datetime import datetime, timedelta
from io import StringIO
from functools import reduce

from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Count, Value, Q, Avg, F
from django.utils import timezone

from .models import *
from research.helpers import sendEmail


CAMPAIGNS_ID_NAME_MAP = {}
BUTTONS_ID_CAMPAIGNS_ID_MAP = {}

def cleanArray(arr):
	"""
	Simply util that removes empty items from an array and returns cleaned array
	"""
	return list(filter(None, arr))


def setSinceDate(date = None):
	# Get responses since this date. In MILLISECONDS (datetime x 1000)
	inception = datetime(2010, 1, 1)
	
	if not date:
		date = inception
	
	return int(date.timestamp() * 1000)


def setBeeHeardCampaignSinceDate(date=None):
	# Get responses since this date. In MILLISECONDS (datetime x 1000)
	inception = datetime(2020, 1, 1)
	
	if not date:
		date = inception
	
	return int(date.timestamp())


def conectToUsabilla():
	"""
	Create an API client with access key and secret key.
	Parse the list of our campaigns in Usabilla and convert the ID to the name.
	This is the only place where ID/KEY is associated to the name, so we make a map of it
	  for use when we get each response, if we have to add a new campaign, we set the key (usabilla ID) and name.
	"""
	apiClient = ub.APIClient(settings.USABILLA_ACCESS_KEY, settings.USABILLA_SECRET_KEY)
	
	usabillaCampaigns = apiClient.get_resource(apiClient.SCOPE_LIVE, apiClient.PRODUCT_WEBSITES, apiClient.RESOURCE_CAMPAIGN, iterate=True)
	
	campaignsArr = json.loads(json.dumps([item for item in usabillaCampaigns]))
	
	# Get list of campaigns and map their ID to their name so we can use 
	#  the name and generate our 'key'
	for campaign in campaignsArr:
		CAMPAIGNS_ID_NAME_MAP[campaign['id']] = campaign['name']
	
	# Get list of campaigns and map their buttons ID to their name so we can use 
	#  the name and generate our 'key'
	for campaign in campaignsArr:
		if campaign['buttonId']:
			BUTTONS_ID_CAMPAIGNS_ID_MAP[campaign['buttonId']] = campaign['id']
	
	return apiClient


def createLocationObjects(locationString):
	locationArr = locationString.split(',')
	state = None
	city = None
	country = None
	
	if len(locationArr) == 3:
		# City/state/country
		country, created = Country.objects.get_or_create(name = locationArr[2].strip())
		state, created = State.objects.get_or_create(name = locationArr[1].strip())
		city, created = City.objects.get_or_create(name = locationArr[0].strip())
	
	elif len(locationArr) == 2 and locationArr[1] == 'United States':
		# US 2-item array is: state/country
		country, created = Country.objects.get_or_create(name = locationArr[1].strip())
		state, created = State.objects.get_or_create(name = locationArr[0].strip())
	
	elif len(locationArr) == 2:
		# Non-US 2-item array is: city/country
		country, created = Country.objects.get_or_create(name = locationArr[1].strip())
		city, created = City.objects.get_or_create(name = locationArr[0].strip())
	
	elif len(locationArr) == 1:
		# Country only
		country, created = Country.objects.get_or_create(name = locationArr[0].strip())
		
	return {
		'city': city,
		'state': state,
		'country': country
	}


def getCampaignNameFromId(id):
	try:
		return CAMPAIGNS_ID_NAME_MAP[id]
	except Exception as ex:
		return 'CAMPAIGN_NAME_NOT_FOUND'


def getDeviceType(device):
	if device.is_mobile:
		return 'Mobile'
	elif device.is_tablet:
		return 'Tablet'
	elif device.is_pc:
		return 'Desktop'
	else:
		return 'Other'


def createCampaignKey(id, role=None, version='', company=''):
	cn = getCampaignNameFromId(id)
	
	# Role is object, None if nonexistant so has special case for it.
	try:
		if role:
			campaignKey = f'{cn}{role}{version}'
		else:
			campaignKey = f'{cn}{version}'
	except Exception as ex:
		campaignKey = cn

	if company:
		campaignKey += f'_{company}'
		
	return campaignKey


def getCampaign(key, uid):
	try:
		project = Campaign.objects.filter(uid=uid).first().project
	except:
		project = None
	
	campaign, created = Campaign.objects.get_or_create(
		key = key,
		defaults = {
			'uid': uid,
			'project': project,
			'latest_response_date': timezone.make_aware(datetime(2016,1,1)),
			'latest_feedback_response_date': timezone.make_aware(datetime(2016,1,1)),
			'latest_other_response_date': timezone.make_aware(datetime(2016,1,1)),
			'created_by': getImportScriptUser(),
			'updated_by': getImportScriptUser(),
		}
	)
	return campaign


def getNps(v):
	try:
		return int(v)
	except:
		return None


def getRole(v):
	try:
		return UserRole.objects.get_or_create(name = v)[0]
	except:
		return None


def getUrl(v):
	try:
		return Url.objects.get_or_create(url = v)[0]
	except:
		return None


def findAValue(r, fieldnameArr):
	val = ''
	
	for n in fieldnameArr:
		try:
			return r[n]
		except:
			try:
				return r['custom'][n]
			except:
				pass
	
	return val


def getComments(r):
	fieldnameArr = [
		'Final_comments',
		'Comment',
		'comment',
		'comments',
		'Comments',
		'Comments_for_the_team_',
		'missing',
	]
	return findAValue(r['data'], fieldnameArr)
	
	
def getFeedbackType(r):
	fieldnameArr = [
		'please_select_type_o',
		'feedback_type',
		'type_of_feedback_opt',
	]
	return findAValue(r['data'], fieldnameArr)
	
	
def getUmuxCapability(r):
	fieldnameArr = [
		'AwesomeSite_s_capabilities_meet_',
		'GLUI_s_capabilities_meet_',
		'requirements_met',
		'requirements_met_returns',
		'UMUX_LITE_capabilities',
		'w3_Search_capabilities_meet_reqt',
		'w3Search_s_capabilities_meet_my_',
	]
	try:
		return int(findAValue(r['data'], fieldnameArr))
	except:
		return None


def getUmuxEaseUse(r):
	fieldnameArr = [
		'AwesomeSite_is_easy_to_use_',
		'ease_of_use',
		'ease_of_use_returns',
		'UMUX_LITE_ease_of_use',
		'w3_Search_is_easy_to_use_',
		'WWPRT_is_easy_to_use_',
	]
	try:
		return int(findAValue(r['data'], fieldnameArr))
	except:
		return None


def getEmailProvided(r):
	fieldnameArr = [
		'email',
		'Email_optional_',
		'OPTIONAL_Please_provide_an_YES',
		'OPTIONAL_Please_provide_your_ema',
		'Please_provide_your_email_if_you',
		'Email'
	]
	# Slightly different.. if they provided their email, simply set flag.
	if findAValue(r['data'], fieldnameArr) != '':
		return True
	else:
		return False


def getGoalCompleted(r):
	fieldnameArr = [
		'Did_you_find_the_help_you_needed',
		'Goal_complete',
		'goal_completed',
		'Goal_completed',
		'goal_Completed',
		'Goal_Completed',
		'Goal_completed_1',
		'Goal_completed_2',	
	]
	val = findAValue(r['data'], fieldnameArr)

	if val.strip() != '':
		return GoalCompleted.objects.get_or_create(name = val)[0]
	else:
		return None


def getGoalNotCompletedReason(r):
	fieldnameArr = [
		'No_Reason',
		'Reason_not_complete',
		'reason_not_complete',
		'Reason_not_complete_1',
		'Reason_not_complete_2',
		'Which_of_the_fol',
		'Why_were_you_not_able_to_accompl',
	]
	return findAValue(r['data'], fieldnameArr)


def getImprovementSuggestion(r):
	fieldnameArr = [
		'suggestions_to_improve',
		'Suggestions_to_improve',
		'Suggestions_to_improve_1',
		'text',
		'What_changes_could_be_made_to_im',
		'What_changes_to_',
	]
	return findAValue(r['data'], fieldnameArr)


def getPrimaryGoal(r):
	fieldnameArr = [
		'goal',
		'Goal',
		'Goal_radio',
		'Goal_Radio',
		'Goal_select',
		'Goal_Select',
		'Goal_select_1',
		'Goal_Select_1',
		'Goal_select_2',
		'Goal_Select_2',
		'primary_goal',
		'primary_site_goal',
		'What_was_your_primary_goal_on_Co',
		'What_was_your_primary_goal_on_th',
	]
	
	try:
		val = findAValue(r['data'], fieldnameArr).lower()
		return PrimaryGoal.objects.get_or_create(name=val)[0]
	except:
		return None


def getPrimaryGoalOther(r):
	fieldnameArr = [
		'Briefly_describe_Accomplished',
		'Briefly_describe_you_primary_goa',
		'Goal_Other',
		'Goal_test',
		'Goal_text',
		'goal_text',
		'Goal_Text',
		'Goal_text1',
		'Goal_text_1',
		'Goal_text_2',
		'primary_goal_other',
		'Other_goal',
	]
	return findAValue(r['data'], fieldnameArr)


def getDeviceData(ua):
	device = parse(ua)
	
	browser, created = Browser.objects.get_or_create(
		name = f'{device.browser.family} {device.browser.version_string}'
	)
	deviceType, created = DeviceType.objects.get_or_create(
		name = getDeviceType(device)
	)
	opSystem, created = OperatingSystem.objects.get_or_create(
		name = f'{device.os.family} {device.os.version_string}'
	)
	
	return {
		'browser': browser,
		'deviceType': deviceType,
		'opSystem': opSystem 
	}


def getTime(r):
	try:
		return int((r['time'] / 1000))
	except:
		return 0


def convertCsvToData(row):
	"""
	Field indexes reference:
		0 Campaign
		1 Campaign ID
		2 Response ID
		3 Date
		4 NPS
		5 UM UX Lite - Capability
		6 UM UX Lite - Ease of Use
		7 Suggestion to Improve
		8 User Role
		9 Primary Goal
		10 Other (Write-in)
		11 Goal Completed
		12 Not Completed Reason
		13 Final Comments
		14 Email (Yes/No)
		15 URL
		16 Location
		17 Total Time
		18 Device Type
		19 Browser
		20 System
	"""
	
	# Pass if we already have this response imported.
	if VoteResponse.objects.filter(uid = row[2]).exists():
		return
	
	campaign, created = Campaign.objects.get_or_create(
		key = row[0],
		defaults = {
			'uid': row[1],
			'latest_response_date': timezone.make_aware(datetime(2000,1,1)),
			'created_by': getImportScriptUser(),
			'updated_by': getImportScriptUser(),
		}
	)

	userRole, created = UserRole.objects.get_or_create(name = row[8])
	primaryGoal, created = PrimaryGoal.objects.get_or_create(name = row[9])
	goalCompleted, created = GoalCompleted.objects.get_or_create(name = row[11])
	
	#locationData = createLocationObjects(row[16])
						
	if row[14].lower() == 'yes':
		email = True
	else:
		email = False
	
	#try:
	#	url, created = Url.objects.get_or_create(url = row[15])
	#except:
	#	url = None
	
	#deviceType, created = DeviceType.objects.get_or_create(name = row[18])
	#browser, created = Browser.objects.get_or_create(name = row[19])
	#system, created = OperatingSystem.objects.get_or_create(name = row[20])
	
	# Clean up values.
	
	remove_s = str.maketrans(dict.fromkeys('s'))
	#try:
	#	totalTime = int(row[17].translate(remove_s))
	#except:
	#	totalTime = 0
	
	try:
		nps = int(row[4])
	except:
		nps = None
		
	try:
		umuxCapability = int(row[5])
	except:
		umuxCapability = None
		
	try:
		umuxEaseUse = int(row[6])
	except:
		umuxEaseUse = None
		
	# Build Response data object and return to sender.
	responseData = {
		#'browser': browser,
		'campaign': campaign,
		'comments': row[13],
		'date': row[3],
		#'device_type': deviceType,
		'email_provided': email,
		'goal_completed': goalCompleted,
		'goal_not_completed_reason': row[12],
		'improvement_suggestion': row[7],
		#'location': row[16],
		#'country': locationData['country'],
		#'state': locationData['state'], 
		#'city': locationData['city'],
		'nps': nps,
		#'operating_system': system,			
		'primary_goal': primaryGoal,
		'primary_goal_other': row[10],
		#'submitted_url': url,
		#'total_time': totalTime,
		'umux_capability': umuxCapability,
		'umux_ease_of_use': umuxEaseUse,
		'uid': row[2],
		'user_role': userRole
	}
	
	return responseData


def convertDataToCsv(campaigns=None, projects=None, startDate=None, endDate=None, orderBy=None):
	"""
	0 Campaign
	1 Campaign ID
	2 Response ID
	3 Date
	4 NPS
	5 UM UX Lite - Capability
	6 UM UX Lite - Ease of Use
	7 Suggestion to Improve
	8 User Role
	9 Primary Goal
	10 Other (Write-in)
	11 Goal Completed
	12 Not Completed Reason
	13 Final Comments
	14 Email (Yes/No)
	15 URL
	16 Location
	17 Total Time
	18 Device Type
	19 Browser
	20 System
	"""
		
	dataset = VoteResponse.objects
	
	if campaigns:
		dataset = dataset.filter(campaign__in=campaigns)
	if projects:
		dataset = dataset.filter(campaign__project__in=projects)
	if startDate:
		dataset = dataset.filter(date__gte=startDate)
	if endDate:
		dataset = dataset.filter(date__lte=endDate)
	
	if orderBy:
		dataset = dataset.order_by(orderBy)

	#responses = dataset.select_related('user_role', 'primary_goal', 'goal_completed', 'campaign', 'country', 'state', 'city', 'submitted_url', 'device_type', 'browser', 'operating_system')
	
	responses = dataset.select_related('user_role', 'primary_goal', 'goal_completed', 'campaign')
	
	totalCount = dataset.count()	
	responseArr = []
	
	#print(f'DEBUG: Exporting data as CSV rows, {totalCount} total rows')
	
	for i, r in enumerate(responses):
		if settings.DEBUG and i%500 == 0:
			print(f'DEBUG: Just processed response # {i} of {totalCount}')
		
		""""
		# Not parsing these on input anymore to speed up processes.
		if r.city and r.state:
			location = f'{r.city.name}, {r.state.name}, {r.country.name}'
		elif r.city:
			location = f'{r.city.name}, {r.country.name}'
		elif r.state:
			location = f'{r.state.name}, {r.country.name}'
		elif r.country:
			location = r.country.name
		else:
			location = ''
		
		# Add handling for optional items.
		try:
			url = r.submitted_url.url
		except: 
			url = ''
		"""
		
		try:
			role = r.user_role.name
		except: 
			role = ''
			
		try:
			primaryGoal = r.primary_goal.name
		except: 
			primaryGoal = ''
			
		try:
			goalCompleted = r.goal_completed.name
		except: 
			goalCompleted = ''
			
		responseCsv = [
			r.campaign.key,
			r.campaign.uid,
			r.uid,
			r.date,
			r.nps,
			r.umux_capability,
			r.umux_ease_of_use,
			r.improvement_suggestion,
			role,
			primaryGoal,
			r.primary_goal_other,
			goalCompleted,
			r.goal_not_completed_reason,
			r.comments,
			r.email_provided,
			#url,
			#location,
			#r.total_time,
			#r.device_type.name,
			#r.browser.name,
			#r.operating_system.name
		]
		responseArr.append(responseCsv)
	
	return responseArr


def convertVoteResponseToData(r):
	"""
	Sample row:
		{
			'id': '5cf942a511a7d7030d001927',
			'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0',
			'location': 'Austin, TX, United States',
			'date': '2019-06-06T16:43:35.643Z',
			'campaignId': '5cdb14ec87398043843a118d',
			'customData':{},
			'data': {
				'Goal_select': 'General_site_Information',
				'UMUX_LITE_capabilities': 6,
				'UMUX_LITE_ease_of_use': 7,
				'goal_completed': 'Yes',
				'nps': 9,
				'Role': 'adfafdaf'
			},
			'url': '',
			'time': 362904
		}
	"""
	try:
		rd = r['data']
		if not rd:
			return
	except:
		return
	
	role = getRole(rd.get('Role'))
	version = rd.get('Version', '')
	company = rd.get('Company', '')
	campaignKey = createCampaignKey(r['campaignId'], role=role, version=version, company=company)
	
	campaign = getCampaign(campaignKey, r['campaignId'])
	nps = getNps(rd.get('nps'))
	
	#deviceData = getDeviceData(r['userAgent'])
	#locationData = createLocationObjects(r['location'])
	comments = getComments(r)
	umuxCapability = getUmuxCapability(r)
	umuxEaseUse = getUmuxEaseUse(r)
	emailProvided = getEmailProvided(r)
	goalCompleted = getGoalCompleted(r)
	goalNotCompletedReason = getGoalNotCompletedReason(r)
	improvementSuggestion = getImprovementSuggestion(r)
	primaryGoalOther = getPrimaryGoalOther(r)
	primaryGoal = getPrimaryGoal(r)	
	#url = getUrl(r.get('url', ''))
	#totalTime = getTime(r)
	
	# All data in in raw_data. We just pull out special fields we use to display responses.
	responseData = {
		#'browser': deviceData['browser'],
		'campaign': campaign,
		'comments': comments,
		'date': dateutil.parser.parse(r['date']),
		#'device_type': deviceData['deviceType'],
		'email_provided': emailProvided,
		'goal_completed': goalCompleted,
		'goal_not_completed_reason': goalNotCompletedReason,
		'improvement_suggestion': improvementSuggestion,
		#'location': r.get('location',''),
		#'country': locationData['country'],
		#'state': locationData['state'],
		#'city': locationData['city'],
		'nps': nps,
		#'operating_system': deviceData['opSystem'],
		'primary_goal': primaryGoal,
		'primary_goal_other': primaryGoalOther,
		#'submitted_url': url,
		#'total_time': totalTime,
		'umux_capability': umuxCapability,
		'umux_ease_of_use': umuxEaseUse,
		'uid': r['id'],
		'user_role': role,
		'raw_data': r
	}
	
	return responseData


def convertFeedbackResponseToData(r):
	"""
	Sample row:
	{
		'id': 'IGvL13vYKP75YyyE3TeMByLG',
		'url': 'http://127.0.0.1:8000/survey/display/G5RxJ5uc4J6JMIs3yKQbnYyE/',
		'data': {
			'cc': 'us',
			'email': '',
			'comments': 'khblhjjgh ',
			'feedback_type': 'compliment',
			'rating': '4'
		},
		'date': '2021-11-02T00:40:08.788049+00:00',
		'userAgent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36',
		'surveyType': 'feedback',
		'campaignId': 'G5RxJ5uc4J6JMIs3yKQbnYyE',
		'displayType': 'standalone'
	}
	"""	
	try:
		rd = r['data']
	except:
		return
	
	role = getRole(rd.get('Role'))
	version = rd.get('Version', '')
	company = rd.get('Company', '')
	campaignKey = createCampaignKey(r['campaignId'], role=role, version=version, company=company)
	campaign = getCampaign(campaignKey, r['campaignId'])
	comments = getComments(r)
	feedbackType = getFeedbackType(r)
	emailProvided = getEmailProvided(r)
	
	# All data in in raw_data. We just pull out special fields we use to display responses.
	responseData = {
		'date': dateutil.parser.parse(r['date']),
		'uid': r['id'],
		'campaign': campaign,
		'rating': rd.get('rating', None),
		'feedback_type': feedbackType,
		'comments': comments,
		'email_provided': emailProvided,
		'raw_data': r
	}
	
	return responseData


def convertOtherResponseToData(r):
	"""
	Sample row:
	{
		'date': '2021-11-02T00:40:08.788049+00:00',
		'id': 'IGvL13vYKP75YyyE3TeMByLG',
		'campaignId': 'G5RxJ5uc4J6JMIs3yKQbnYyE',
		'data': {
			...unknown...
		},
		'surveyType': 'other',
		'displayType': 'standalone'
	}
	"""
	try:
		rd = r['data']
	except:
		return
	
	role = getRole(rd.get('Role'))
	version = rd.get('Version', '')
	company = rd.get('Company', '')
	campaignKey = createCampaignKey(r['campaignId'], role=role, version=version, company=company)
	campaign = getCampaign(campaignKey, r['campaignId'])
	
	# All data in in raw_data. We just pull out special fields we use to display responses.
	responseData = {
		'date': dateutil.parser.parse(r['date']),
		'uid': r['id'],
		'campaign': campaign,
		'raw_data': r
	}
	
	return responseData


def convertUsabillaResponseToCsvRow(r):
	"""
	Sample row API SOURCE:
		{
			'id': '5cf942a511a7d7030d001927',
			'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0',
			'location': 'Austin, TX, United States',
			'date': '2019-06-06T16:43:35.643Z',
			'campaignId': '5cdb14ec87398043843a118d',
			'customData':{},
			'data': {
				'Goal_select': 'General_site_Information',
				'UMUX_LITE_capabilities': 6,
				'UMUX_LITE_ease_of_use': 7,
				'goal_completed': 'Yes',
				'nps': 9,
				'Role': 'adfafdaf'
			},
			'url': '',
			'time': 362904
		}
	
	Sample array CONVERT TO:
		0 Campaign
		1 Campaign ID
		2 Response ID
		3 Date
		4 NPS
		5 UM UX Lite - Capability
		6 UM UX Lite - Ease of Use
		7 Suggestion to Improve
		8 User Role
		9 Primary Goal
		10 Other (Write-in)
		11 Goal Completed
		12 Not Completed Reason
		13 Final Comments
		14 Email (Yes/No)
		15 URL
		16 Location
		17 Total Time
		18 Device Type
		19 Browser
		20 System
	"""
	
	# If this response has no data, there's nothing to import, so we just stop.
	try:
		rd = r['data']
	except:
		return
	
	role = getRole(rd.get('Role'))
	version = rd.get('Version', '')
	company = rd.get('Company', '')
	campaignKey = createCampaignKey(r['campaignId'], role=role, version=version, company=company)
	
	campaign = getCampaign(campaignKey, r['campaignId'])
	nps = getNps(rd.get('nps'))
	deviceData = getDeviceData(r['userAgent'])
	comments = getComments(r)
	umuxCapability = getUmuxCapability(r)
	umuxEaseUse = getUmuxEaseUse(r)
	emailProvided = getEmailProvided(r)
	goalCompleted = getGoalCompleted(r)
	goalNotCompletedReason = getGoalNotCompletedReason(r)
	improvementSuggestion = getImprovementSuggestion(r)
	primaryGoalOther = getPrimaryGoalOther(r)
	primaryGoal = getPrimaryGoal(r)	
	url = getUrl(r.get('url', ''))
	totalTime = getTime(r)
	
	# Main gig - Create the new response data object and return to sender
	# Add handling for optional items.
	try:
		url = url.url
	except: 
		url = ''
		
	try:
		role = role.name
	except: 
		role = ''
		
	try:
		primaryGoal = primaryGoal.name
	except: 
		primaryGoal = ''
		
	try:
		primaryGoalOther = primaryGoalOther
	except: 
		primaryGoalOther = ''
		
	try:
		goalCompleted = goalCompleted.name
	except: 
		goalCompleted = ''
		
	
	emailProvided = 'Yes' if emailProvided else ''
		
	rowArr = [
		campaignKey,
		r['campaignId'],
		r['id'],
		r['date'],
		nps,
		umuxCapability,
		umuxEaseUse,
		improvementSuggestion,
		role,
		primaryGoal,
		primaryGoalOther,
		goalCompleted,
		goalNotCompletedReason,
		comments,
		emailProvided,
		url,
		r['location'],
		f'{totalTime}s',
		deviceData['deviceType'],
		deviceData['browser'],
		deviceData['opSystem']
	]

	return rowArr


####
##  4 main actions from data source triangle: 
##  [Usabilla API] -- [CSV to import] -- [Omnia Data models]
####


def importUsabillaFromApi(campaignsArr):
	"""
	Uses Usabilla API (https://developers.usabilla.com/#get-campaigns) to get campaign
	responses, and inserts them into OM.
	
	:param campaigns: An array of objects to fetch: 
		id: <campaignid>,
		date: <datetime object>
	"""
	t0 = time.time()
	
	apiClient = conectToUsabilla()
	
	try:
		newActivity = ActivityLog.objects.create(
			user = getUsabillaImportScriptUser(),
			comments = f'Import timer: Connecting to Usabilla: {round(time.time()-t0,1)}s'
		)
	except Exception as ex:
		print(f'Error: Import timer: Usabilla connection logging ERROR: {str(ex)}')
		
	
	# For each campaign object passed in, fetch the campaign results
	# using the campaign object ID and the campaign object "since" date.
	
	projectsTouched = []
	projectsTouchedData = {}
	campaignUidsTouched = []
	buttonIdsTouched = []
	campaignsProcessed = []
	campaignButtonsProcessed = []
	processedCount = 0
	insertedCount = 0
	t0 = time.time()
	
	if settings.DEBUG:
		print(f'>> {campaignsArr}')
	
	for campaign in campaignsArr:
		
		# Get feedback responses.
		if campaign['usabilla_button_id'] and campaign['usabilla_button_id'] not in campaignButtonsProcessed:
			try:
				# Get the earliest latest response date.
				sinceDate = setSinceDate(campaign['latest_feedback_response_date'])
				apiClient.set_query_parameters({'since': sinceDate})
				campaignResponses = apiClient.get_resource(apiClient.SCOPE_LIVE, apiClient.PRODUCT_WEBSITES, apiClient.RESOURCE_FEEDBACK, campaign['usabilla_button_id'], iterate=True)
			
				if settings.DEBUG:
					print(f">> Button id: {campaign['usabilla_button_id']}, since date: {sinceDate}")
				
				for cr in campaignResponses:
					processedCount += 1
					
					if settings.DEBUG:
						print(f'>> Processing response #{processedCount}')
					
					if FeedbackResponse.objects.filter(uid=cr['id']).exists():
						if settings.DEBUG:
							print(f'>> Have it already')
						continue
					
					# It's expecting object with some fields and survey data in 'data'
					responseData = {
						'id': cr['id'],
						'date': cr['date'],
						'campaignId': BUTTONS_ID_CAMPAIGNS_ID_MAP[campaign['usabilla_button_id']],
						'data': cr,
					}
					
					# Insert record if there's data.
					responseDataArgs = convertFeedbackResponseToData(responseData)
					if responseDataArgs:
						try:
							savedResponse = FeedbackResponse.objects.create(**responseDataArgs)
							insertedCount += 1
							buttonIdsTouched.append(campaign['usabilla_button_id'])
							
							if not savedResponse.campaign.usabilla_button_id:
								savedResponse.campaign.usabilla_button_id = campaign['usabilla_button_id']
								savedResponse.campaign.save()
							if settings.DEBUG:
								print(f'Inserted feedback #{insertedCount}')
						except Exception as ex:
							if settings.DEBUG:
								print(f">> Error: Button id: {campaign['usabilla_button_id']}, since date: {sinceDate}")
								print(f'Error importing response: {ex}')
							continue
						
			except Exception as ex:
				if settings.DEBUG:
					print(f'{ex}')
					
				newActivity = ActivityLog.objects.create(
					user = getUsabillaImportScriptUser(),
					comments = f"Error trying Usabilla feedback button: {campaign['usabilla_button_id']}: {ex}"
				)
					
			campaignButtonsProcessed.append(campaign['usabilla_button_id'])
			
		# Get VOTE responses.	
		if campaign['uid'] and campaign['uid'] not in campaignsProcessed:
			try:
				# Get the earliest latest response date.
				sinceDate = setSinceDate(campaign['latest_response_date'])
				apiClient.set_query_parameters({'since': sinceDate})
				campaignResponses = apiClient.get_resource(apiClient.SCOPE_LIVE, apiClient.PRODUCT_WEBSITES, apiClient.RESOURCE_CAMPAIGN_RESULT, campaign['uid'], iterate=True)
				
				if settings.DEBUG:
					print(f">> Intercept id: {campaign['uid']}, since date: {sinceDate}")
				
				# For each user response/feedback item, convert data and add to DB.
				for cr in campaignResponses:
					processedCount += 1
					
					if settings.DEBUG:
						print(f'>> Processing response #{processedCount}')
					
					if VoteResponse.objects.filter(uid=cr['id']).exists():
						if settings.DEBUG:
							print(f'>> Have it already')
						continue
					
					# Insert record if there's data.
					# No need to check if we have response already (via uid), just fail silently,
					#   because 99.99% it's new response and if we have if just continue to next one anyway.
					responseDataArgs = convertVoteResponseToData(cr)
					if responseDataArgs:
						try:
							savedResponse = VoteResponse.objects.create(**responseDataArgs)	
							insertedCount += 1
							campaignUidsTouched.append(campaign['uid'])
							if settings.DEBUG:
								print(f'Inserted vote #{insertedCount}')
						except Exception as ex:
							if settings.DEBUG:
								print(f">> Intercept id: {campaign['uid']}, since date: {sinceDate}")
								print(f'{ex}')
							continue
						
						# Flag this campaign so we set the latest response date for it (usabilla ID + role)
						project = savedResponse.campaign.project
						responseYearQuarter = (pd.Timestamp(savedResponse.date).year,pd.Timestamp(savedResponse.date).quarter)
						responseYearMonth = (pd.Timestamp(savedResponse.date).year,pd.Timestamp(savedResponse.date).month)
					
						if project:
							# If it's not in the array already, add it.
							# Else, check if the month or quarter is there already and add that.
							if project.id not in projectsTouched:
								projectsTouched.append(project.id)
								projectsTouchedData[project.id] = {
									'quarters': [responseYearQuarter],
									'months': [responseYearMonth],
								}
							else:
								if responseYearQuarter not in projectsTouchedData[project.id]['quarters']:
									projectsTouchedData[project.id]['quarters'].append(responseYearQuarter)
								
								if responseYearMonth not in projectsTouchedData[project.id]['months']:
									projectsTouchedData[project.id]['months'].append(responseYearMonth)
									
			except Exception as ex:
				if settings.DEBUG:
					print(f'{ex}')
				
				newActivity = ActivityLog.objects.create(
					user = getUsabillaImportScriptUser(),
					comments = f"Error trying Usabilla vote campaign: {campaign['uid']}, using date: {ex}"
				)
				
			campaignsProcessed.append(campaign['uid'])
			
	newActivity = ActivityLog.objects.create(
		user = getUsabillaImportScriptUser(),
		comments = f'Import timer: Importing Usabilla responses: {round(time.time()-t0,1)}'
	)
		
	if settings.DEBUG:
		print(f'>> {campaignUidsTouched}')
		
	setLatestResponseDate(campaignUidsTouched, getUsabillaImportScriptUser())
	setLatestButtonResponseDate(buttonIdsTouched, getUsabillaImportScriptUser())
	
	setCampaignsResponseCount()
	
	# We only need to update snapshots and baseline/targets for projects 
	#  touched that got VOTE responses.
	if len(projectsTouched) > 0:
		updateProjectSnapshots(projectsTouched, projectsTouchedData)
		updateDomainSnapshots(projectsTouched)
		setProjectYearBaselinesAndTargets()

	# Cleanup and remove new Campaign placeholders we already fetched results for.
	# If we don't have a real Campaign for it yet (usabillaID + role), then it stays as placeholder.
	for campaignPlaceholder in Campaign.objects.filter(key__isnull=True):
		if Campaign.objects.filter(uid=campaignPlaceholder.uid, key__isnull=False).exists():
			campaignPlaceholder.delete()
	
	if settings.DEBUG:
		print(f'Processed: {processedCount}, Inserted {insertedCount}')
	
	return {
		'processedCount': processedCount,
		'insertedCount': insertedCount,
		'projectsTouchedCount': len(projectsTouched) 
	}
	

def importUsabillaFromCsv(file = './campaign-mark.csv'):
	t0 = time.time()
	
	with open(file,'r') as csvf:
		rows = csv.reader(csvf)
		totalRows = sum(1 for row in rows)

	with open(file,'r') as csvf:
		rows = csv.reader(csvf)
		
		for row in rows:
			# Create the data object and insert response.
			responseData = convertCsvToData(row)
			if responseData:
				VoteResponse.objects.create(**responseData)
	
	#print(f'>> Finished importing {totalRows} rows, took {round(time.time()-t0,1)}.')


def createCsvFromUsabillaApi(campaignsArr):
	"""
	Uses Usabilla API (https://developers.usabilla.com/#get-campaigns) to get campaign
	responses, and inserts them into OM.
	
	:param campaigns: An array of objects to fetch: 
		id: <campaignid>,
		date: <datetime object>
	"""
	
	t0 = time.time()
	
	apiClient = conectToUsabilla()
	
	# For each campaign object passed in, fetch the campaign results
	# using the campaign object ID and the campaign object "since" date.
	rowsArr = []

	for campaign in campaignsArr:
		sinceDate = setSinceDate(campaign['latest_response_date'])
		apiClient.set_query_parameters({'since': sinceDate})
		campaignResponses = apiClient.get_resource(apiClient.SCOPE_LIVE, apiClient.PRODUCT_WEBSITES, apiClient.RESOURCE_CAMPAIGN_RESULT, campaign['uid'], iterate=True)
		
		for cr in campaignResponses:
			# Convert the API result to a CSV row and add to our array.
			csvRow = convertUsabillaResponseToCsvRow(cr)
			if csvRow:
				rowsArr.append(csvRow)
	
	# Send CSV to browser.
# 	response = HttpResponse(rowsArr, content_type='text/csv')
# 	response['Content-Disposition'] = 'attachment; filename="Usabilla response export.csv"'
#	return response

	# Save CSV as local file.
	with open('api_to_csv.csv', mode='w', encoding='utf-8') as csvFile:
		writer = csv.writer(csvFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		writer.writerows(rowsArr)
		
	#print(f'>> Finished creating CSV from API, took {round(time.time()-t0,1)}.')	


def createCsvFromData(campaigns=None, projects=None, startDate=None, endDate=None, orderBy=None):
	"""
	Create a CSV file using data from the Response object
	"""
	t0 = time.time()
	
	rowsArr = convertDataToCsv(campaigns=campaigns, projects=projects, startDate=startDate, endDate=endDate, orderBy=orderBy)
	
	if settings.DEBUG:
		print(f'>> Query took: {round(time.time()-t0,1)}')
	
	headerRow = ['Campaign', 'Campaign ID', 'Response ID', 'Date', 'NPS', 'UM UX Lite - Capability', 'UM UX Lite - Ease of Use', 'Suggestion to Improve', 'User Role', 'Primary Goal', 'Other (Write-in)', 'Goal Completed', 'Not Completed Reason', 'Final Comments', 'Email (Yes/No)',] # 'URL', 'Location', 'Total Time', 'Device Type', 'Browser', 'System']
	
	# Add header row.
	rowsArr = [headerRow] + rowsArr
	
	# Send CSV to browser.
# 	response = HttpResponse(rowsArr, content_type='text/csv')
# 	response['Content-Disposition'] = 'attachment; filename="Usabilla response export.csv"'
#	return response

	# Save CSV as local file.
	filename = f'responses_to_csv_{int(timezone.now().timestamp())}.csv'
	
	t0 = time.time()
	with open(filename, mode='w', encoding='utf-8') as csvFile:
		writer = csv.writer(csvFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		writer.writerows(rowsArr)
	
	if settings.DEBUG:
		print(f'>> File write took: {round(time.time()-t0,1)}')
	
	return filename
	
	
def fetchNewUsabillaResponses(user=None):
	"""
	Gets all campaigns and latest response dates and fetches new responses for each campaign
	since that date.
	"""
	t0 = time.time()
	
	campaignCountBefore = Campaign.objects.fromUsabilla().count()
	
	# Get list of active usabilla campaigns.
	campaigns = Campaign.objects.fromUsabilla().only('uid', 'usabilla_button_id', 'latest_response_date', 'latest_feedback_response_date', 'latest_other_response_date').order_by('uid')
	
	# Build smal array of campaign data to use for imports.
	campaignDataArr = []
	for campaign in campaigns:
		campaignDataArr.append({
			'uid': campaign.uid,
			'usabilla_button_id': campaign.usabilla_button_id,
			'latest_response_date': campaign.latest_response_date,
			'latest_feedback_response_date': campaign.latest_feedback_response_date,
			'latest_other_response_date': campaign.latest_other_response_date,
		})
	
	try:
		newActivity = ActivityLog.objects.create(
			user = getUsabillaImportScriptUser(),
			comments = f'Import timer: Got list of {len(campaignDataArr)} Usabilla campaigns: {round(time.time()-t0,1)}s'
		)
	except Exception as ex:
		print(f'Error: Import timer: Usabilla campaign list count logging ERROR: {str(ex)}')
	
	importStats = importUsabillaFromApi(campaignDataArr)
	
	if settings.DEBUG:
		print(f'{importStats}')
		
	runTime = round(time.time()-t0,1)
	
	if not user:
		user = getUsabillaImportScriptUser()
		
	# Now log this API import.
	logData = {
		'responses_imported_count': importStats['insertedCount'],
		'projects_affected_count': importStats['projectsTouchedCount'], 
		'run_time_seconds': runTime,
		'import_type': 'usabilla',
		'user': user
	}
	logEntry = ImportLog.objects.create(**logData)
	
	newCampaignsCount = Campaign.objects.fromUsabilla().count() - campaignCountBefore
	if newCampaignsCount > 0:
		newCampaigns = Campaign.objects.allActive().fromUsabilla().order_by('-created_at')[:newCampaignsCount]
		campaignList = '<br>- '.join(map(str, (list(newCampaigns.values_list('key', flat=True)))))
		admins = list(Group.objects.get(name='admins').user_set.all().values_list('username', flat=True))
		
		sendEmail({
			'subject': '[Omnia] Omniabot detected new Usabilla campaigns created',
			'recipients': admins,
			'message': f'<div style="font-family:sans-serif;font-size:14px;line-height:20px;"><p><strong>{newCampaignsCount}</strong> new campaigns were just created from the Usabilla import and are not associated with a project:<br>- {campaignList}</p><p>All campaigns without a project association can be seen in the the Omnia Admin Center data audits, for campaigns: https://REPLACE_ME/metrics/admin/campaignnoproject/</p><br><br><p style="font-size:12px;color:#777;">You\'re receiving this email because you\'re a Omnia admin. If you don\'t want to receive these, tough luck.</p></div>'
		})
	
	if settings.DEBUG:
		print('>> Usabilla import done.')
	
	
def createCsvAndEmailFile(user=None, campaigns=None, projects=None, startDate=None, endDate=None):
	if not user:
		print('Error: User not provied to createCsvAndEmailFile')
		return 
			
	t0 = time.time()
	fileName = createCsvFromData(campaigns, projects, startDate, endDate)

	activityEntry = ActivityLog.objects.create(
		user = user,
		comments = f'Created CSV export of all responses, took {round(time.time()-t0,1)}.'
	)
	
	email = EmailMessage(
		'[Omnia] Usabilla response CSV dump',
		'Attached is a CSV with the Usabilla response dump you requested.',
		'do-not-reply@domain.com',
		[user.username],
		[],
	)
	
	try:
		email.attach_file(fileName)
		email.send()
		activityEntry = ActivityLog.objects.create(
			user = user,
			comments = 'Responses export email sent successfully'
		)
		
	except Exception as ex:
		print(f'Error: Responses export email failed to send. Error message: {str(ex)}')
		activityEntry = ActivityLog.objects.create(
			user = user,
			comments = f'Error: Responses export email failed to send. Error message: {str(ex)}'
		)
	
	os.remove(fileName)


def updateResponseFieldValues(dataObjects):
	"""
	Manual script to run whenever Mark sends new variants of fields.
	This will look for the variants in existing raw data we have and set the individual field
	name it's a variant of to whatever the value is of that variant.
	NOTE: Ensure to add the variant field names to the import script so we pick them up from now on.
	
	Example usage of param:
		dataObjects = [
			{
				'newFields': [
					'requirements_met', 'requirements_met_returns'
				],
				'functionName': 'getUmuxCapability',
				'modelFieldName': 'umux_capability',
			},
			{
				'newFields': [
					'ease_of_use', 'ease_of_use_returns'
				],
				'functionName': 'getUmuxEaseUse',
				'modelFieldName': 'umux_ease_of_use',
			},
			{
				'newFields': [
					'Please_provide_your_email_if_you',
				],
				'functionName': 'getEmailProvided',
				'modelFieldName': 'email_provided',
			},
		]
	"""
	projectsTouched = []
	projectsTouchedData = {}
	updatedCount = 0
	
	for data in dataObjects:
		filterArr = []

		for field in data['newFields']:
			filterArr.append(Q(**{'raw_data__data__'+field+'__isnull':False}))

		responses = VoteResponse.objects.filter(reduce(operator.or_, filterArr))
		
		print(f">> Found: {responses.count()} for {data['newFields']}")

		for r in responses:
			newVal = globals()[data['functionName']](r.raw_data)
			setattr(r, data['modelFieldName'], newVal)
			r.save()
			updatedCount += 1

			# Get project and response year & quarter and track for updating project quarter snapshots and domain year snapshots.
			project = r.campaign.project
			responseYearQuarter = (pd.Timestamp(r.date).year,pd.Timestamp(r.date).quarter)
			responseYearMonth = (pd.Timestamp(r.date).year,pd.Timestamp(r.date).month)
			
			if project:
				# If it's not in the array already, add it.
				# Else, check if the month or quarter is there already and add that.
				if project.id not in projectsTouched:
					projectsTouched.append(project.id)
					projectsTouchedData[project.id] = {
						'quarters': [responseYearQuarter],
						'months': [responseYearMonth],
					}
				else:
					if responseYearQuarter not in projectsTouchedData[project.id]['quarters']:
						projectsTouchedData[project.id]['quarters'].append(responseYearQuarter)
						
					if responseYearMonth not in projectsTouchedData[project.id]['months']:
						projectsTouchedData[project.id]['months'].append(responseYearMonth)

		print(f">> After update found: {responses.filter(**{data['modelFieldName']+'__isnull': True}).count()}")

	"""
	Sample of what we store in projectsTouchedData as a result of the imports:
	projectsTouched = [45,3,41,55]
	projectsTouchedData = {
		41 = {
			quarters: [
				(2019,2),
				(2018,3)
			],
			momths: [
				(2019,3),
				(2018,7),
			]
		}
	}
	"""
	projectsTouched = cleanArray(projectsTouched)

	# This only works when the campaign is associated to a project. 
	# Update the quarterly and 'last 90 day' snapshots for each project we just added responses for.
	for projectId in projectsTouched:
		thisProject = Project.objects.get(id=projectId)
		
		for yearQuarter in projectsTouchedData[projectId]['quarters']:
			thisProject.updateQuarterSnapshot(year=yearQuarter[0], quarter=yearQuarter[1])
			
		for yeaMonth in projectsTouchedData[projectId]['months']:
			thisProject.updateMonthSnapshot(year=yearMonth[0], month=yearMonth[1])
		
		print(f">> Update project {thisProject.name} snapshot for Q: {projectsTouchedData[projectId]['quarters']}")
		print(f">> Update project {thisProject.name} snapshot for M: {projectsTouchedData[projectId]['months']}")
		
	# Update the last 90 days snapshot for EVERY non-inactive project 
	#  because it's a daily rolling time frame and responses drop off.
	# Then update the stored snapshots (current reporting, valid, latest, etc)
	t0 = time.time()
	for project in Project.objects.allActive():
		project.updateLast90Snapshot()
		project.storeLatestSnapshots()

	# Set baseline and targets.
	setProjectYearBaselinesAndTargets()
		
	# Update the DomainYearSnapshot for projects touched's domains.
	# This will use updated snapshots, and updated year settings (if any) to calculate % active,
	#  excellent NPS, etc. 
	t0 = time.time()
	for domain in Domain.objects.filter(project_domain__in=projectsTouched).distinct().order_by('name'):
		domain.updateDomainYearSnapshot()

	# Return stats.
	print(json.dumps({
		'Responses': updatedCount,
		'Projects': len(projectsTouched),
		'Domains': Domain.objects.filter(project_domain__in=projectsTouched).distinct().count()
	}, indent=2))


def setProjectYearBaselinesAndTargets():
	"""
	Run on projects that don't have a baseline for THIS year for NPS OR UMUX.
	Same 'if' logic is built in to "setNpsBaseline" and "setUmuxBaseline" so we can call individual
	  project method, but this prevents unnecessary processing loop here.
	We don't set baselines after July 15.
	"""
	if timezone.now() < timezone.make_aware(datetime(timezone.now().year,7,15)):
		for project in Project.objects.allActive().filter(
			Q(project_year_setting_project__nps_baseline__isnull=True) | Q(project_year_setting_project__umux_baseline__isnull=True),
			project_year_setting_project__year=timezone.now().year,
		):
			project.setYearBaselinesAndTargets()


def importBeeHeardFromApi(campaignsArr):
	"""
	Uses BeeHeard API to get campaign responses, and inserts them into Omnia.
	
	<campaignsArr>: An array of objects to fetch: 
		id: <campaignid>,
		date: <datetime object>
	"""
	t0 = time.time()
	
	try:
		newActivity = ActivityLog.objects.create(
			user = getBeeHeardImportScriptUser(),
			comments = f'Import timer: Connecting to BeeHeard: {round(time.time()-t0,1)}s'
		)
	except Exception as ex:
		print(f'Error: Import timer: BeeHeard connection logging ERROR: {str(ex)}')
		
	
	# For each campaign object passed in, fetch the campaign results
	# using the campaign object ID and the campaign object "since" date.
	projectsTouched = []
	voteProjectsTouched = []
	voteProjectsTouchedData = {}
	campaignIdsTouched = []
	processedCount = 0
	insertedCount = 0
	t0 = time.time()
	
	if settings.DEBUG:
		print(f'>> {campaignsArr}')
	
	# We don't skip duplicate instances of UIDs because each one has a different date, 
	#  And it's a fast skip anyway when we already have a response.
	for campaign in campaignsArr:
		try:
			sinceDate = setBeeHeardCampaignSinceDate(campaign['latest_response_date'])
			
			campaignResponses = requests.get(f"https://REPLACE_ME/survey/api/responses/?campaign={campaign['uid']}&since={sinceDate}", timeout=4).json()['responses']
			i
			#print(f">> Campaign UID: {campaign['uid']} - Using date: {sinceDate}")
			
			# For each user response/feedback item, convert data and add to DB.
			for response in campaignResponses:
				processedCount += 1
				
				if settings.DEBUG:
					print(f'>> Processing response #{processedCount}')
				
				# Process and insert response based on the type of respose it is. 3 types.
				responseType = response.get('surveyType', None)
				try:
					if responseType == 'vote':
						if VoteResponse.objects.filter(uid=response['id']).exists():
							if settings.DEBUG:
								print(f'>> Have it already')
							continue
						responseData = convertVoteResponseToData(response)
						savedResponse = VoteResponse.objects.create(**responseData)
					elif responseType == 'feedback':
						if FeedbackResponse.objects.filter(uid=response['id']).exists():
							if settings.DEBUG:
								print(f'>> Have it already')
							continue
						responseData = convertFeedbackResponseToData(response)
						savedResponse = FeedbackResponse.objects.create(**responseData)
					else:
						if OtherResponse.objects.filter(uid=response['id']).exists():
							if settings.DEBUG:
								print(f'>> Have it already')
							continue
						responseData = convertOtherResponseToData(response)
						savedResponse = OtherResponse.objects.create(**responseData)
						
				except Exception as ex:
					if settings.DEBUG:
						print(f'{ex}')
					continue
				
				# If we made it here, we inserted one of the three types of responses.
				insertedCount += 1
				
				if settings.DEBUG:
					print(f'Inserted feedback #{insertedCount}')
				
				# Store the actual DB ID to make it easy.
				campaignIdsTouched.append(savedResponse.campaign.id)
				
				project = responseData['campaign'].project
				if project and project.id not in projectsTouched:
					projectsTouched.append(project.id)
				
				# If it's vote response add touched campaign and project to arrays
				#  so we can set the latest response date and recalculate project snapshots.
				if responseType == 'vote':
					project = responseData['campaign'].project
					responseYearQuarter = (pd.Timestamp(responseData['date']).year,pd.Timestamp(responseData['date']).quarter)
					responseYearMonth = (pd.Timestamp(responseData['date']).year,pd.Timestamp(responseData['date']).month)
				
					if project:
						# If it's not in the array already, add it.
						# Else, check if the month or quarter is there already and add that.
						if project.id not in voteProjectsTouched:
							voteProjectsTouched.append(project.id)
							voteProjectsTouchedData[project.id] = {
								'quarters': [responseYearQuarter],
								'months': [responseYearMonth],
							}
						else:
							if responseYearQuarter not in voteProjectsTouchedData[project.id]['quarters']:
								voteProjectsTouchedData[project.id]['quarters'].append(responseYearQuarter)
							
							if responseYearMonth not in voteProjectsTouchedData[project.id]['months']:
								voteProjectsTouchedData[project.id]['months'].append(responseYearMonth)
								
		except Exception as ex:
			if settings.DEBUG:
				print(f'{ex}')
				
			newActivity = ActivityLog.objects.create(
				user = getUsabillaImportScriptUser(),
				comments = f"Error trying BeeHeard campaign: {campaign['uid']}, using date: {ex}"
			)
			
	try:
		newActivity = ActivityLog.objects.create(
			user = getBeeHeardImportScriptUser(),
			comments = f'Import timer: Importing responses: {round(time.time()-t0,1)}'
		)
	except Exception as ex:
		print(f'Error: Import timer: VoteResponse importing logging ERROR: {str(ex)}')
	
	setLatestBeeHeardResponseDate(campaignIdsTouched, getBeeHeardImportScriptUser())
	setCampaignsResponseCount()
	
	# We only need to update snapshots and baseline/targets for projects 
	#  touched that got VOTE responses.
	if len(voteProjectsTouched) > 0:
		updateProjectSnapshots(voteProjectsTouched, voteProjectsTouchedData)
		updateDomainSnapshots(voteProjectsTouched)
		setProjectYearBaselinesAndTargets()

	# Cleanup and remove new Campaign placeholders we already fetched results for.
	# If we don't have a real Campaign for it yet (usabillaID + role), then it stays as placeholder.
	for campaignPlaceholder in Campaign.objects.filter(key__isnull=True):
		if Campaign.objects.filter(uid=campaignPlaceholder.uid, key__isnull=False).exists():
			campaignPlaceholder.delete()
	
	return {
		'processedCount': processedCount,
		'insertedCount': insertedCount,
		'projectsTouchedCount': len(projectsTouched) 
	}


def fetchNewBeeHeardResponses(user=None):
	"""
	Gets all campaigns and latest response dates and fetches new responses for each campaign
	since that date.
	"""
	t0 = time.time()
	
	campaignCountBefore = Campaign.objects.fromBeeHeard().count()
	
	uniqueIds = list(Campaign.objects.allActive().fromBeeHeard().values_list('uid', flat=True).order_by('uid').distinct())
	
	try:
		beeHeardCampaigns = requests.get('https://REPLACE_ME/survey/api/campaigns/', timeout=4).json()['campaigns']
		
		for campaign in beeHeardCampaigns:
			CAMPAIGNS_ID_NAME_MAP[campaign['uid']] = campaign['key']
	except Exception as ex:
		print(f'Error: {ex}')
	
	campaignDataArr = []
	for uniqueId in uniqueIds:
		try:
			latestOne = Campaign.objects.filter(uid=uniqueId).order_by('-latest_response_date').first()
			latestDate = latestOne.latest_response_date
		except Exception as ex:
			latestDate = ''
		
		campaignDataArr.append({
			'uid': uniqueId,
			'latest_response_date': latestDate,
		})
	
	importStats = importBeeHeardFromApi(campaignDataArr)
	
	runTime = round(time.time()-t0,1)
	
	if not user:
		user = getBeeHeardImportScriptUser()
		
	# Now log this API import.
	logData = {
		'responses_imported_count': importStats['insertedCount'],
		'projects_affected_count': importStats['projectsTouchedCount'], 
		'run_time_seconds': runTime,
		'import_type': 'beeheard',
		'user': user
	}
	logEntry = ImportLog.objects.create(**logData)
	
	newCampaignsCount = Campaign.objects.fromBeeHeard().count() - campaignCountBefore
	if newCampaignsCount > 0:
		newCampaigns = Campaign.objects.fromBeeHeard().order_by('-created_at')[:newCampaignsCount]
		campaignList = '<br>- '.join(map(str, (list(newCampaigns.values_list('key', flat=True)))))
		admins = list(Group.objects.get(name='admins').user_set.all().values_list('username', flat=True))
		
		sendEmail({
			'subject': '[Omnia] Omniabot detected new BeeHeard campaigns created',
			'recipients': admins,
			'message': f'<div style="font-family:sans-serif;font-size:14px;line-height:20px;"><p><strong>{newCampaignsCount}</strong> new campaigns were just created from the BeeHeard import and are not associated with a project:<br>- {campaignList}</p><p>All campaigns without a project association can be seen in the the Omnia Admin Center data audits, for campaigns: https://REPLACE_ME/metrics/admin/campaignnoproject/</p><br><br><p style="font-size:12px;color:#777;">You\'re receiving this email because you\'re a Omnia admin. If you don\'t want to receive these, tough luck.</p></div>'
		})
		
	if settings.DEBUG:
		print('>> BeeHeard import done.')
	

def setLatestResponseDate(campaignUidsTouched, user):
	# Loop thru unique campaigns touched and set the latest response date.
	t0 = time.time()
	
	uniqueUids = list(set(campaignUidsTouched))
	
	for uid in uniqueUids:
		if not uid:
			continue
			
		# Get all campaigns that have this UID and set the date on ACTIVE ones.
		campaigns = Campaign.objects.filter(uid=uid).prefetch_related('response_campaign', 'feedback_response_campaign', 'other_response_campaign')
		
		if Response.objects.filter(campaign__in=campaigns).exists():
			latestDate = Response.objects.filter(campaign__in=campaigns).order_by('-date').values('date')[0]['date']
			campaigns.allActive().update(latest_response_date=latestDate)

		if FeedbackResponse.objects.filter(campaign__in=campaigns).exists():
			latestDate = FeedbackResponse.objects.filter(campaign__in=campaigns).order_by('-date').values('date')[0]['date']
			campaigns.allActive().update(latest_feedback_response_date=latestDate)
		
		if OtherResponse.objects.filter(campaign__in=campaigns).exists():
			latestDate = OtherResponse.objects.filter(campaign__in=campaigns).order_by('-date').values('date')[0]['date']
			campaigns.allActive().update(latest_other_response_date=latestDate)
			
	try:
		newActivity = ActivityLog.objects.create(
			user = user,
			comments = f'Import timer: Set campaign latest date for {len(uniqueUids)} UIDs: {round(time.time()-t0,1)}s'
		)
	except Exception as ex:
		print(f'Error: Import timer: Campaign latest date logging ERROR: {str(ex)}')
		

def setLatestButtonResponseDate(buttonIdsTouched, user):
	# Loop thru unique campaigns touched and set the latest response date.
	t0 = time.time()
	
	uniqueButtonIds = list(set(buttonIdsTouched))
	
	for usabilla_button_id in uniqueButtonIds:
		if not usabilla_button_id:
			continue
		
		# Get all campaigns that have this UID and set the date on ACTIVE ones.
		campaigns = Campaign.objects.filter(usabilla_button_id=usabilla_button_id).prefetch_related('feedback_response_campaign')

		if FeedbackResponse.objects.filter(campaign__in=campaigns).exists():
			latestDate = FeedbackResponse.objects.filter(campaign__in=campaigns).order_by('-date').values('date')[0]['date']
			campaigns.allActive().update(latest_feedback_response_date=latestDate)
		
	try:
		newActivity = ActivityLog.objects.create(
			user = user,
			comments = f'Import timer: Set campaign latest date for {len(uniqueButtonIds)} button IDs: {round(time.time()-t0,1)}s'
		)
	except Exception as ex:
		print(f'Error: Import timer: Campaign latest date logging ERROR: {str(ex)}')


def setLatestBeeHeardResponseDate(campaignIdsTouched, user):
	# Loop thru unique campaigns touched and set the latest response date.
	t0 = time.time()
	
	for campaignId in campaignIdsTouched:
		# Each BeeHeard campaign can only have 1 type of response because each is unique,
		#   so we use only the latest_response_date field for them.
		# Just concat counts from each of the three because we don't know what type of 
		#   responses the campaign has.
		noDateDate = timezone.make_aware(datetime(2020,1,1))
		latestDate = noDateDate
		
		try:
			lastRespDate = Response.objects.filter(campaign=campaignId).order_by('-date').values('date')[0]['date']
			if lastRespDate > latestDate:
				latestDate = lastRespDate 
		except Exception as ex:
			pass
		
		try:
			lastRespDate = FeedbackResponse.objects.filter(campaign=campaignId).order_by('-date').values('date')[0]['date']
			if lastRespDate > latestDate:
				latestDate = lastRespDate 
		except Exception as ex:
			pass
		
		try:
			lastRespDate = OtherResponse.objects.filter(campaign=campaignId).order_by('-date').values('date')[0]['date']
			if lastRespDate > latestDate:
				latestDate = lastRespDate 
		except Exception as ex:
			pass
		
		if latestDate != noDateDate:
			Campaign.objects.filter(id=campaignId).update(latest_response_date=latestDate)
		
	try:
		newActivity = ActivityLog.objects.create(
			user = user,
			comments = f'Import timer: Set campaign latest date for {len(campaignIdsTouched)} UIDs: {round(time.time()-t0,1)}s'
		)
	except Exception as ex:
		print(f'Error: Import timer: Campaign latest date logging ERROR: {str(ex)}')
		

def setCampaignsResponseCount():
	for campaign in Campaign.objects.all():
		campaign.storeResponseCount()
		

def updateProjectSnapshots(projectsTouched, projectsTouchedData):
	'''
	Sample of what we store in projectsTouchedData as a result of the imports:
	projectsTouched = [45,3,41,55]
	projectsTouchedData = {
		41 = {
			quarters: [
				(2019,2),
				(2018,3),
			],
			momths: [
				(2019,3),
				(2018,7),
			]
		}
	}
	'''
	projectsTouched = cleanArray(projectsTouched)
	
	# This only works when the campaign is associated to a project. 
	# Update the quarterly and 'last 90 day' snapshots for each project we just added responses for.
	for projectId in projectsTouched:
		thisProject = Project.objects.get(id=projectId)
		
		for yearQuarter in projectsTouchedData[projectId]['quarters']:
			thisProject.updateQuarterSnapshot(year=yearQuarter[0], quarter=yearQuarter[1])
		
		for yearMonth in projectsTouchedData[projectId]['months']:
			thisProject.updateMonthSnapshot(year=yearMonth[0], month=yearMonth[1])
	
	# Update the last 90 days snapshot for EVERY non-inactive project 
	#  because it's a daily rolling time frame and responses drop off.
	# Then update the stored snapshots (current reporting, valid, latest, etc)
	t0 = time.time()
	for project in Project.objects.allActive():
		project.updateLast90Snapshot()
		project.storeLatestSnapshots()
	
	try:
		newActivity = ActivityLog.objects.create(
			user = getImportScriptUser(),
			comments = f'Import timer: Update all last90: {round(time.time()-t0,1)}s'
		)
	except Exception as ex:
		print(f'Error: Import timer: Update all last90 logging ERROR: {str(ex)}')
	

def updateDomainSnapshots(projectsTouched):
	# Update the DomainYearSnapshot for projects touched's domains.
	# This will use updated snapshots, and updated year settings (if any) to calculate % active,
	#  excellent NPS, etc. 
	t0 = time.time()
	for domain in Domain.objects.filter(project_domain__in=projectsTouched).distinct().order_by('name'):
		domain.updateDomainYearSnapshot()
	
	try:
		newActivity = ActivityLog.objects.create(
			user = getImportScriptUser(),
			comments = f'Import timer: Update touched domains ({Domain.objects.filter(project_domain__in=projectsTouched).distinct().count()}): {round(time.time()-t0,1)}s'
		)
	except Exception as ex:
		print(f'Error: Import timer: Update touched domains logging ERROR: {str(ex)}')


