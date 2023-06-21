import csv
import base64
import json
import time
import pandas as pd
import requests

from datetime import datetime, timedelta
from dateutil.relativedelta import *
from django.conf import settings
from django.db.models import Count, Value, Sum, Q, Avg, F
from django.db.models.functions import Lower
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string

from scheduler import commonScheduler
from research.helpers import setPageMessage, clearPageMessage, sendSlackAlert, sendEmail


def runInBackground(funct, kwargs=None):
	"""
	Shortcut to run any function as a background process on a separate thread.
	Return: Null
	"""
	sched = commonScheduler()
	sched.add_job(funct, kwargs=kwargs)


def getYearMonthAgo(monthsAgo):
	today = timezone.now()
	return ((today - relativedelta(months=monthsAgo)).year, (today - relativedelta(months=monthsAgo)).month)
	
	
def getDaysAgo(n):
	return timezone.now() - timedelta(days=n)


def getFirstDateOfQuarter(date):
	"""
	Return: {Date} The start date of the quarter for the given date.
	"""
	# Bug if first date of the quarter is used, so add 1 if that's the case.
	if date.day == 1:
		date = date + timedelta(days=1)
		
	quarter_start = pd.to_datetime(date - pd.tseries.offsets.QuarterBegin(startingMonth=1)).date()
	
	return quarter_start
	

def getLastDateOfQuarter(date):
	"""
	Return: {Date} The last date of the quarter for the given date.
	"""
	# Bug if last date of the quarter is used, so subtract 1 if that's the case.
	if date.day > 29:
		date = date - timedelta(days=1)
	quarter_end = pd.to_datetime(date + pd.tseries.offsets.QuarterEnd(startingMonth=3)).date()
	return quarter_end
	
	
def createProjectsTableData(projects, showField, startDate, endDate):
	"""
	CURRENTLY DEPRECATED.
	Take the projects and filter to only include ones that have snapshots that are
	within the specified date range and have a value for the given field.
	Return: {obj} List of projects and quarter headings showing given field value.
	"""
	def getFieldValue(snapshots, filters, showField):
		try:
			snapshot = snapshots.get(**filters)
			if showField == 'nps_score' and not snapshot.nps_meaningful_data:
				fieldValue = None
			elif showField == 'umux_score' and snapshot.umux_meaningful_data:
				fieldValue = None
			else:
				fieldValue = getattr(snapshot, showField)	
		except Exception as ex:
			fieldValue = None
		
		return fieldValue
		
	startDate = getFirstDateOfQuarter(startDate)
	endDate = getLastDateOfQuarter(endDate)
	
	# Only get and list projects that have snapshots within the date range (2 yr back from now).
	projects = projects.order_by(Lower('name')).select_related('domain').prefetch_related('project_snapshot_project').distinct()
	
	# Each project is a row. Each quarter is a column. 
	# Start a row and get each quarter's snapshot value for the field we're supposed to show.
	for project in projects:
		project.fieldValuesArr = []
		
		# Only fetch snapshots within the date range (2 yr back from now).
		snapshots = project.project_snapshot_project.filter(Q(date_period='quarter', date__gte=startDate, date__lte=endDate) | Q(date_period='last90')).order_by('date')

		# For each quarter in date range, get the field value or set 
		# to empty value (to lay out table properly).
		pidx = pd.period_range(start=startDate, end=endDate, freq='Q')
		for period in pidx:
			fieldValue = getFieldValue(snapshots, {'date__year':period.year,'date_quarter':period.quarter}, showField)
			project.fieldValuesArr.append(fieldValue)

		# Add last 90 #.
		fieldValue = getFieldValue(snapshots, {'date_period':'last90'}, showField)
		project.fieldValuesArr.append(fieldValue)
				
	headings = []
	pidx = pd.period_range(start=startDate, end=endDate, freq ='Q')
	for period in pidx:
		headings.append(f'{period.quarter}Q{str(period.year)[-2:]}')
	
	headings.append('Current score')
	
	return {
		'headings': headings,
		'projects': projects
	}


def getNpsCategory(npsNum):
	"""
	Return: {string} The user category (detractor/passive/promoter) of the given NPS rating.
	"""
	if npsNum < 7:
		return 'detractor'
	elif npsNum < 9:
		return 'passive'
	else:
		return 'promoter'


def getUmuxScore(umuxCap, umuxEase):
	"""
	Return: {int .4} UMUX score (as a %) from Ease of Use and Capability score, based on 12pt scale.
	"""
	try:
		total = (umuxCap + umuxEase) - 2
		return round((total / 12 * 100), 4)
	except:
		return None


def calculateAverageNps(totalNpsCount, promoterCount, detractorCount):
	"""
	Return: {int .4}  the actual NPS based on promoter and detractor counts.
	"""
	try:
		promoterPercent = (promoterCount / totalNpsCount) * 100
		detractorPercent = (detractorCount / totalNpsCount) * 100
		return round(promoterPercent - detractorPercent, 4)
	except:
		return None
	

def getVoteResponsesNpsCounts(responses):
	"""
	Return: {obj} NPS user category counts (detractor/passive/promoter) across given responses.
	"""
	data = {
		'total': 0,
		'promoter': 0,
		'passive': 0,
		'detractor': 0, 
	}
	
	data['promoter'] = responses.filter(nps_category='promoter').count()
	data['passive'] = responses.filter(nps_category='passive').count()
	data['detractor'] = responses.filter(nps_category='detractor').count()
	data['total'] = responses.filter(nps__isnull=False).count()
	
	return data


def getHistoricalNpsChartData(allProjectSnapshots):
	"""
	NPS history line chart on project detail page.
	Takes snapshots and returns quarter dates with NPS and targets for historical line chart.
	Return: {obj} Chart data with xaxis quarters, scores, and targets.
	"""
	endDate = getLastDateOfQuarter(timezone.now() - timedelta(days=95))
	startDate = getFirstDateOfQuarter(endDate - timedelta(days=365*2))
	allProjectSnapshots = allProjectSnapshots.filter(date_period='quarter', nps_meaningful_data=True, date__gte=startDate).order_by('date')
	
	# If there are snapshots, set some vars and continue
	# Else return empty obj.
	if allProjectSnapshots.exists():
		project = allProjectSnapshots.first().project
		startDate = getFirstDateOfQuarter(allProjectSnapshots.first().date)
	else:
		return {}
	
	data = {
		'xaxis': ['x'],
		'actual': ['Actual'],
		'scoreDates': [],
		'target': ['Target'],
		'targetExceed': ['Exceed'],
		'targetYears': [],
	}
	
	# For each quarter in date range, get the field value or set to empty.
	pidx = pd.period_range(start = startDate, end = endDate, freq ='Q')
	for quarterPeriod in pidx:
		data['xaxis'].append(f'{quarterPeriod.quarter}Q{str(quarterPeriod.year)[-2:]}')
		
		# If no snapshot for the quarter, set as empty plot via 'except'.
		try:
			snapshot = allProjectSnapshots.get(date__year=quarterPeriod.year, date_quarter=quarterPeriod.quarter)
			data['actual'].append(round(snapshot.nps_score, 1))
			data['targetYears'].append(quarterPeriod.year)
			
			try:
				data['scoreDates'].append(snapshot.nps_score_date.strftime('%b %d'))
			except:
				data['scoreDates'].append('')
			
			try:
				yearTarget = project.project_year_setting_project.filter(year=quarterPeriod.year).values('nps_target').first()['nps_target']
				data['target'].append(round(yearTarget, 1))
			except Exception as ex:
				data['target'].append('null')
			
			try:
				yearTargetExceed = project.project_year_setting_project.get(year=quarterPeriod.year).nps_target_exceed
				data['targetExceed'].append(round(yearTargetExceed, 1))
			except Exception as ex:
				data['targetExceed'].append('null')
				
		except Exception as ex:
			data['actual'].append('null')
			data['targetYears'].append('null')
			data['scoreDates'].append('null')
			data['target'].append('null')
			data['targetExceed'].append('null')
		
	return data


def getHistoricalUmuxChartData(allProjectSnapshots):
	"""
	UMUX history line chart on project detail page.
	Loop thru quarters starting at first meaningful quarter 2 years or less ago.
	If a quarter has no (meaningful) snapshot, it gets an empty x-axis tick.
	Return: {obj} Chart data with xaxis quarters, scores, and targets.
	"""
	endDate = getLastDateOfQuarter(timezone.now() - timedelta(days=95))
	startDate = getFirstDateOfQuarter(endDate - timedelta(days=365*2))
	allProjectSnapshots = allProjectSnapshots.filter(date_period='quarter', date__gte=startDate, umux_meaningful_data=True).order_by('date')
	
	# If there are snapshots, set some vars and continue
	# Else return empty obj.
	if allProjectSnapshots.exists():
		project = allProjectSnapshots.first().project
		startDate = getFirstDateOfQuarter(allProjectSnapshots.first().date)
	else:
		return {}
	
	data = {
		'xaxis': ['x'],
		'actual': ['Actual'],
		'scoreDates': [],
		'target': ['Target'],
		'targetExceed': ['Exceed'],
		'targetYears': [],
	}
	
	# For each quarter in date range, get the field value or set to empty.
	pidx = pd.period_range(start = startDate, end = endDate, freq ='Q')
	for quarterPeriod in pidx:
		data['xaxis'].append(f'{quarterPeriod.quarter}Q{str(quarterPeriod.year)[-2:]}')
		
		# If no snapshot for the quarter, set as empty plot via 'except'.
		try:
			snapshot = allProjectSnapshots.get(date__year=quarterPeriod.year, date_quarter=quarterPeriod.quarter)
			data['actual'].append(round(snapshot.umux_score, 1))
			data['targetYears'].append(quarterPeriod.year)
			
			try:
				data['scoreDates'].append(snapshot.umux_score_date.strftime('%b %d'))
			except:
				data['scoreDates'].append('')
			try:
				yearTarget = project.project_year_setting_project.get(year=quarterPeriod.year).umux_target
				data['target'].append(round(yearTarget, 1))
			except Exception as ex:
				data['target'].append('null')
			try:
				yearTargetExceed = project.project_year_setting_project.get(year=quarterPeriod.year).umux_target_exceed
				data['targetExceed'].append(round(yearTargetExceed, 1))
			except Exception as ex:
				data['targetExceed'].append('null')	
					
		except Exception as ex:
			data['actual'].append('null')
			data['targetYears'].append('null')
			data['scoreDates'].append('null')
			data['target'].append('null')
			data['targetExceed'].append('null')
		
	return data


def getHistoricalGoalCompletionChartData(allProjectSnapshots):
	"""
	UMUX history line chart on project detail page.
	Loop thru quarters starting at first meaningful quarter 2 years or less ago.
	If a quarter has no (meaningful) snapshot, it gets an empty x-axis tick.
	Return: {obj} Chart data with xaxis quarters, scores, and targets.
	"""
	endDate = getLastDateOfQuarter(timezone.now() - timedelta(days=95))
	startDate = getFirstDateOfQuarter(endDate - timedelta(days=365*2))
	allProjectSnapshots = allProjectSnapshots.filter(date_period='quarter', date__gte=startDate).order_by('date')
	
	# If there are snapshots, set some vars and continue
	# Else return empty obj.
	if allProjectSnapshots.exists():
		project = allProjectSnapshots.first().project
		startDate = getFirstDateOfQuarter(allProjectSnapshots.first().date)
	else:
		return {}
	
	data = {
		'xaxis': ['x'],
		'actual': ['Actual'],
		'scoreDates': [],
	}
	
	# For each quarter in date range, get the field value or set to empty.
	pidx = pd.period_range(start = startDate, end = endDate, freq ='Q')
	for quarterPeriod in pidx:
		data['xaxis'].append(f'{quarterPeriod.quarter}Q{str(quarterPeriod.year)[-2:]}')
		
		# If no snapshot for the quarter, set as empty plot via 'except'.
		try:
			snapshot = allProjectSnapshots.get(date__year=quarterPeriod.year, date_quarter=quarterPeriod.quarter)
			data['actual'].append(round(snapshot.goal_completed_percent, 1))
			
			try:
				data['scoreDates'].append(snapshot.goal_completed_date.strftime('%b %d'))
			except:
				data['scoreDates'].append('')
				
		except Exception as ex:
			data['actual'].append('null')
			data['scoreDates'].append('null')
	
	return data


def getNpsHistogramData(responses):
	"""
	NPS histogram chart on project detail page.
	Return: {obj} Counts and % of each NPS rating across given responses.
	"""
	try:
		responses = responses.filter(nps__isnull=False)
		responsesCount = responses.count()
		
		data = list(responses.values(npsScore=F('nps')).annotate(npsScoreCount=Count('nps')).order_by('nps'))
		
		# Set percents for NPS counts, and add missing NPS (set them to 0%)
		for i in range(0, 11):
			try:
				if data[i]['npsScore'] == i:
					try:
						data[i]['npsScorePercent'] = round((data[i]['npsScoreCount'] / responsesCount) * 100)
					except:
						data[i]['npsScorePercent'] = 0
				else:
					pos = i
					data.insert(pos, {
							'npsScore': i,
							'npsScoreCount': 0,
							'npsScorePercent': 0,
						}
					)
			except:
				pos = i
				data.insert(pos, {
						'npsScore': i,
						'npsScoreCount': 0,
						'npsScorePercent': 0,
					}
				)
	except Exception as ex:
		data = None

	#print(json.dumps(data, indent=2))
	return data


def getUmuxCapHistogramData(responses):
	"""
	UMUX Capabilities histogram chart on project detail page.
	Return: {obj} Counts and % of each UMUX Capability rating across given responses.
	"""
	try:
		responses = responses.filter(umux_capability__isnull=False)
		responsesCount = responses.count()
		
		data = list(responses.values(umuxCapScore=F('umux_capability')).annotate(umuxCapScoreCount=Count('umux_capability')).order_by('umux_capability'))

		for i in range(0,7):
			try:
				if data[i] and data[i]['umuxCapScore'] == i+1:
					#print(f'{i} exists')
					try:
						data[i]['umuxCapScorePercent'] = round((data[i]['umuxCapScoreCount'] / responsesCount) * 100)
					except:
						data[i]['umuxCapScorePercent'] = 0
					#print(f"Rating {i+1}: {data[i]['umuxCapScoreCount']} of {responsesCount}")
				else:
					data.insert(i, {
							'umuxCapScore': i+1,
							'umuxCapScoreCount': 0,
							'umuxCapScorePercent': 0,
						}
					)
			except Exception as ex:
				data.append({
						'umuxCapScore': i+1,
						'umuxCapScoreCount': 0,
						'umuxCapScorePercent': 0,
					}
				)
		data.reverse()
		
	except Exception as ex:
		data = None

	return data


def getUmuxEaseHistogramData(responses):
	"""
	UMUX Ease of use histogram chart on project detail page.
	Return: {obj} Counts and % of each UMUX Ease of Use rating across given responses.
	"""
	try:
		responses = responses.filter(umux_ease_of_use__isnull=False)
		responsesCount = responses.count()
		
		data = list(responses.values(umuxEaseScore=F('umux_ease_of_use')).annotate(umuxEaseScoreCount=Count('umux_ease_of_use')).order_by('umux_ease_of_use'))
		
		for i in range(0,7):
			try:
				if data[i] and data[i]['umuxEaseScore'] == i+1:
					#print(f'{i+1} exists')
					try:
						data[i]['umuxEaseScorePercent'] = round((data[i]['umuxEaseScoreCount'] / responsesCount) * 100)
					except:
						data[i]['umuxEaseScorePercent'] = 0
					#print(f"Rating {i+1}: {data[i]['umuxEaseScoreCount']} of {responsesCount}")
				else:
					#print(f'{i+1} missing')
					data.insert(i, {
							'umuxEaseScore': i+1,
							'umuxEaseScoreCount': 0,
							'umuxEaseScorePercent': 0,
						}
					)
			except Exception as ex:
				#print(f'{i+1} append it')
				data.append({
						'umuxEaseScore': i+1,
						'umuxEaseScoreCount': 0,
						'umuxEaseScorePercent': 0,
					}
				)
		data.reverse()
				
	except Exception as ex:
		data = None
	
	return data


def getGoalHistogramData(responses):
	"""
	Goal Completion histogram chart on project detail page.
	Return: {obj} Counts and % of each Goal Completion rating across given responses.
	"""
	try:
		snapshotResponses = responses.exclude(Q(primary_goal__isnull=True) | Q(primary_goal__name=''))
		respsnapshotResponsesCount = snapshotResponses.count()
		
		# Get unique list of primary goals and count each primary goal occurance.
		# Then clean up names and change counts to percents
		goals = list(snapshotResponses.values(goalName=F('primary_goal__name')).annotate(goalTotal=Count('primary_goal')).order_by('-goalTotal'))
		
		# For each unique goal and count found:
		for goal in goals:
			goalResponses = snapshotResponses.filter(primary_goal__name=goal['goalName']).select_related('goal_completed')
			responseYesCount = goalResponses.filter(goal_completed__name__iexact='yes').count()
			responsePartiallyCount = goalResponses.filter(goal_completed__name__iexact='yartially').count()
			responseNoCount = goalResponses.filter(goal_completed__name__iexact='no').count()
			
			goal['Yes'] = responseYesCount
			goal['Partially'] = responsePartiallyCount
			goal['No'] = responseNoCount
			goal['YesPercent'] = round((responseYesCount/goal['goalTotal'])*100)
			goal['NoPercent'] = round((responseNoCount/goal['goalTotal'])*100)
			goal['PartiallyPercent'] = round((responsePartiallyCount/goal['goalTotal'])*100)
			goal['goalName'] = goal['goalName'].replace('_',' ').capitalize()
			goal['goalPercent'] = round((goal['goalTotal']/respsnapshotResponsesCount)*100)
	except Exception as ex:
		goals = None
	
	#print(json.dumps(data, indent=2))	
	return goals


def createReportPeriodChoices(startDate, endDate):
	"""
	Used for project tiles report_period select list.
	Return: {array} List of value/label tuples of quarters for given date range.
	"""
	reportPeriodChoices = [
		('last90','Current score'),
	]
	
	# For each quarter in date range, get the field value or set to empty.
	pidx = reversed(pd.period_range(start=startDate, end=endDate, freq ='Q'))
	for period in pidx:
		reportPeriodChoices.append((f'{period.quarter}q{period.year}', f'{period.quarter}Q{period.year}'))
	
	return reportPeriodChoices

	
def getPriorities(request):
	"""
	Return: {string} 'priority' param value based on hierarchy: URL param value -> session (last used) -> none.
	"""
	filterVal = request.GET.getlist('priority', None)
	filterValLastUsed = request.session.get('filterPriorities', None)
	if not filterVal and filterValLastUsed:
		filterVal = filterValLastUsed
	return filterVal
	
	
def getFilterDomain(request):
	"""
	Return: {string} 'domain' param value based on hierarchy: URL param value -> session (last used) -> none.
	"""
	filterVal = request.GET.get('domain', None)
	filterByLastUsed = request.session.get('filterDomain', 'alldomains')
	if not filterVal and filterByLastUsed:
		filterVal = filterByLastUsed

	return filterVal
	
	
def getDomainsDisplay(request):
	"""
	Return: {string} 'displayDomainsAs' param value based on hierarchy: URL param value -> session (last used) -> none.
	"""
	lastUsed = request.session.get('displayDomainsAs', 'tiles')
	return lastUsed
	
	
def getReportPeriod(request):
	"""
	Return: {string} 'filterReportPeriod' param value based on hierarchy: URL param value -> session (last used) -> none.
	"""
	filterVal = request.GET.get('reportperiod', None)
	filterByLastUsed = request.session.get('filterReportPeriod', 'last90')
	if not filterVal and filterByLastUsed:
		filterVal = filterByLastUsed
	
	return filterVal

	
def getShowData(request, allowedFieldsArr):
	"""
	Return: {string} 'showdata' param value based on hierarchy: URL param value -> session (last used) -> none.
	"""
	fieldToShow = request.GET.get('showdata', None)
	fieldToShowLastUsed = request.session.get('filterShowData', 'nps_score')
	if fieldToShow not in allowedFieldsArr and fieldToShowLastUsed in allowedFieldsArr:
		fieldToShow = fieldToShowLastUsed

	return fieldToShow
	
	
def createProjectTilesFiltersData(request):
	"""
	Return: {object} Data to create filters on project tile list page, including what to show as selected.
	"""
	showDataChoices = [
		('nps_score', 'Net Promoter Score'),
		('umux_score', ' Ease & capabilities'),
		('goal_completed_percent', 'Goal completion %'),
	]
	
	allowedShowDataChoices = []
	for v in showDataChoices:
		allowedShowDataChoices.append(v[0])

	# These three we store in session data so "last use" works for these.
	domain = getFilterDomain(request)
	showData = getShowData(request, allowedShowDataChoices)
	reportPeriod = getReportPeriod(request)

	return {
		'selectedDomain': domain,
		'selectedShowData': showData,
		'selectedReportPeriod': reportPeriod,
		'selectedActive': request.GET.get('active', None),
		'selectedArchived': request.GET.get('archived', None),		
		'selectedPriorities': request.GET.getlist('priority', None),
		'selectedProjectKeywords': request.GET.getlist('keyword', None),
		'selectedNpsCats': request.GET.getlist('npscat', None),
		'selectedUmuxCats': request.GET.getlist('umuxcat', None),
		'selectedGoalCats': request.GET.getlist('goalcat', None),
		'selectedMeetingNpsTarget': request.GET.get('meetingnpstarget', None),
		'selectedMeetingUmuxTarget': request.GET.get('meetingumuxtarget', None),
		'selectedExceedingNpsTarget': request.GET.get('exceedingnpstarget', None),
		'selectedExceedingUmuxTarget': request.GET.get('exceedingumuxtarget', None),
		'showDataChoices': showDataChoices,
		'allowedShowDataChoices': allowedShowDataChoices,
		'reportPeriodChoices': createReportPeriodChoices((timezone.now() - timedelta(days=365*2)), timezone.now()),
	}


def doWeeklyDigestAndEmail():
	"""
	Runs every Sunday via cron. Gathers stats from previous week and emails them to all Alexandria admins.
	Return: null
	"""
	from metrics.models import ActivityLog, User, Group, VoteResponse, Campaign, Project
	from research.models import Artifact, Profile
	
	scriptUser, created = User.objects.get_or_create(
		username = 'user_audit_script',
		defaults = {
			'password': get_random_string()
		}
	)
	
	# Gether some stats.
	lastWeek = getDaysAgo(7)
	responsesReceived = VoteResponse.objects.filter(date__gte=lastWeek).count()
	campaignsAdded = Campaign.objects.filter(created_at__gte=lastWeek).count()
	researchAdded = Artifact.objects.filter(created_at__gte=lastWeek).count()
	researchCompleted = Artifact.objects.filter(research_date__gte=lastWeek).count()
	campaignsWithoutProject = Campaign.objects.allActive().filter(project__isnull=True, response_campaign__isnull=False).distinct().count()
	projectsWithoutDomains = Project.objects.allActive().filter(domain__isnull=True, campaign_project__response_campaign__isnull=False).order_by('name').distinct().count()
	projectsExcellent = Project.objects.allActive().filter(latest_valid_currently_reporting_snapshot__nps_score_category__name='Excellent').count()
	projectsWithResponsesNoBaseline = Project.objects.filter(
			project_year_setting_project__year=timezone.now().year,
			campaign_project__response_campaign__isnull=False,
			campaign_project__response_campaign__date__year=timezone.now().year,
			project_year_setting_project__nps_baseline__isnull=True,
		).distinct().count()
	
	cellerDwellers = 0
	for p in Project.objects.allActive().filter(latest_valid_currently_reporting_snapshot__nps_score__lt=F('current_year_settings__nps_baseline')):
		if abs(p.latest_valid_currently_reporting_snapshot.nps_score - p.current_year_settings.nps_baseline) > 10:
			cellerDwellers += 1
		
	msg = """
		<style>td{padding:3px 4px;}td:first-child{text-align:right;width: 40px;font-weight:bold;}tr:nth-child(odd){background-color:#efefef;}</style>
		<p><b>What happened last week</b></p>
		<table cellpadding="0" cellspacing="0" border="0" style="font-size: 14px;"><tbody>
		"""
		
	if responsesReceived > 0:
		msg += f'<tr><td>{responsesReceived:,}</td><td>Responses received</td></tr>'
	
	if campaignsAdded > 0:
		msg += f'<tr><td>{campaignsAdded}</td><td>Campaigns added</td></tr>'
	
	if researchAdded > 0:
		msg += f'<tr><td>{researchAdded}</td><td>Research added</td></tr>'
	
	if researchCompleted > 0:
		msg += f'<tr><td>{researchCompleted}</td><td>Research completed</td></tr>'
	
	msg += '</table>'
	
	# Current standings
	
	msg += """
		<br><p><b>Some current standings</b></p>
		<table cellpadding="0" cellspacing="0" border="0" style="margin-top: 12px;font-size: 14px;"><tbody>
		"""
		
	if campaignsWithoutProject > 0:
		msg += f'<tr><td>{campaignsWithoutProject}</td><td>Active campaigns with responses, currently not associated to a project</td></tr>'
	
	if projectsWithoutDomains > 0:
		msg += f'<tr><td>{projectsWithoutDomains}</td><td>Active projects with responses, currently not associated to a domain</td></tr>'
	
	if projectsWithResponsesNoBaseline > 0:
		msg += f'<tr><td>{projectsWithResponsesNoBaseline}</td><td>Active projects with responses this year but no NPS baseline yet</td></tr>'
	
	msg += f"""
		<tr><td>{projectsExcellent}</td><td>Projects with excellent NPS</td></tr>
		<tr><td>{cellerDwellers}</td><td>Celler dwellers: NPS currently 10+ below their baseline</td></tr>
		</table>"""
	
	quarterlyChangers = Project.getQuarterlyChangers()
	monthlyChangers = Project.getMonthlyChangers()
	
	# Increasers
	if len(monthlyChangers['increasers']) > 0:
		pNames = ''
		for p in monthlyChangers['increasers']:
			pNames += f'<li>{p.name}</li>'
			
		msg += f'<p style="margin-top:32px;"><strong>Consecutive monthly increasers</strong></p><p>The NPS for these projects has increased the past three consecutive months:<ul>{pNames}</ul></p>'
		
	if len(quarterlyChangers['increasers']) > 0:
		pNames = ''
		for p in quarterlyChangers['increasers']:
			pNames += f'<li>{p.name}</li>'
			
		msg += f'<p style="margin-top:32px;"><strong>Consecutive quarterly increasers</strong></p><p>The NPS for these projects has increased the past two consecutive quarters:<ul>{pNames}</ul></p>'
		
	# Decliners
	if len(monthlyChangers['decliners']) > 0:
		pNames = ''
		for p in monthlyChangers['decliners']:
			pNames += f'<li>{p.name}</li>'
			
		msg += f'<p style="margin-top:32px;"><strong>Consecutive monthly decliners</strong></p><p>The NPS for these projects has declined the past three consecutive months:<ul>{pNames}</ul></p>'
		
	if len(quarterlyChangers['decliners']) > 0:
		pNames = ''
		for p in quarterlyChangers['decliners']:
			pNames += f'<li>{p.name}</li>'
			
		msg += f'<p style="margin-top:32px;"><strong>Consecutive quarterly decliners</strong></p><p>The NPS for these projects has declined the past two consecutive quarters:<ul>{pNames}</ul></p>'
	
	try:
		admins = list(Group.objects.get(name='admins').user_set.all().values_list('username', flat=True))
		sendEmail({
			'subject': '[Alexandria] Alexandriabot weekly digest',
			'recipients': admins,
			'message': f'<div style="font-family:sans-serif;font-size:14px;line-height:20px;">{msg}<br><p style="font-size:12px;color:#777;">You\'re receiving this email because you\'re a Alexandria admin. If you don\'t want to receive these, tough luck.</p></div>'
		})
	except Exception as ex:
		print(str(ex))

	if settings.DEBUG:
		print('Done')


def emailAdmins(msgData):
	"""
	Emails all admins with given message. States which admin created/is sending the message to everyone.
	Return: {bool}
	"""
	from metrics.models import Group
	
	try:
		if not msgData['msg']:
			print('No message was provided to send.')
			return False
		
		admins = list(Group.objects.get(name='admins').user_set.all().values_list('username', flat=True))
		
		returnMessage, emailSent = sendEmail({
			'subject': '[Alexandria] Admins communication',
			'recipients': admins,
			'fromEmail': msgData['fromEmail'],
			'message': f'<div style="font-family:sans-serif;font-size:14px;line-height:20px;"><p>Message from {msgData["sender"]} to all {len(admins)} Alexandria admins:</p><p>{msgData["msg"]}</p></div>'
		})
		
		return (returnMessage, emailSent)
	except Exception as ex:
		return (f"Error: Admin email failed to send. Error message: {returnMessage}", False)
	
