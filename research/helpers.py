import base64
import io
import json
import os
import requests

from copy import copy

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.forms.models import model_to_dict
from django.utils.crypto import get_random_string
from django.core.mail import EmailMultiAlternatives

from .models import *


# User extension for access control used in decorator functions and templates
#  to easily restrict view access and template functionality.
def hasAdminAccess(user):
	"""
	User is Superuser or member of the admin group.
	Return: {bool}
	"""
	try:
		hasAccess = user.is_superuser or user.groups.filter(name='admins').exists()
	except:
		hasAccess = False
	
	return hasAccess

def hasAdminAccess_decorator(user):
	if not hasAdminAccess(user):
		raise PermissionDenied
	return True
	

## Is editor or greater access.
def hasEditorAccess(user, artifact):
	try:
		hasAccess = hasAdminAccess(user) or artifact.created_by == user or artifact.owner == user or user in artifact.editors.all()
	except Exception as ex:
		hasAccess = False
	
	return hasAccess
		

# Add decorator methods to User object so they are automatically available anywhere, even in templates!
# No need to pass this in thru views. 
# Template example usage: {% if request.user.hasAdminAccess %}
# View decorator usage:	 @user_passes_test(hasAdminAccess_decorator)
User.add_to_class('hasAdminAccess', hasAdminAccess)
User.add_to_class('hasEditorAccess', hasEditorAccess)



def cleanArray(arr):
	"""
	Simply util that removes empty items from an array and returns cleaned array
	"""
	return list(filter(None, arr))


def filterObjectsContaining(queryset=None, fieldname=None, objects=None):
	"""
	Generic 'and' filter to use on any queryset, any field, with any object to fiter on.
	"""
	for obj in objects:
		filterset = { fieldname: obj }
		queryset = queryset.filter(**filterset)
	
	return queryset


def setPageMessage(request, msgType, msgText):
	"""
	Sets the session page message
	"""
	msgClass = "green" if msgType == "success" else "dark-red"
	
	request.session['pageMessage'] = {
		'class': msgClass,
		'text': msgText,
	}

	
def clearPageMessage(request):
	"""
	Clears the session page message
	"""
	request.session['pageMessage'] = None

	
def sendSlackAlert(errorCode, msg):
	"""
	Takes the HTTP error code passed and the message and pushes a message to the Slack web hook URL for our room.
	"""
	slackUrl = settings.SLACK_ALERT_URL
	icon = ':error:' if errorCode > 499 else ':warning:'
	
	payload = {
		'username': 'Omnia',
		'icon_emoji': icon,
		'text': f'*A {errorCode} error just happened*\n{msg}',
	}
	
	if slackUrl:
		r = requests.post(slackUrl, json=payload)


def sendSlackNewArtifactNotification(user, artifact, url):
	"""
	Sends a notification to the "notifications" channel that a new research has been posted.
	"""
	slackUrl = settings.SLACK_OMNIA_NOTIFICATIONS_URL
	
	payload = {
		'username': 'OMNIA research',
		'icon_emoji': ':new:',
		'text': f'*{user.profile.full_name}* just posted a new research item:\n*Title*: {artifact.name}\n*Status*: {artifact.status.name}\nhttps://REPLACE_ME{url}',
	}
	
	if slackUrl:
		r = requests.post(slackUrl, json=payload)


def sendSlackCompletedArtifactNotification(user, artifact, url):
	"""
	Sends a notification to the "notifications" channel that a research item is now in 'completed' status.
	"""
	slackUrl = settings.SLACK_OMNIA_NOTIFICATIONS_URL
	
	payload = {
		'username': 'OMNIA research',
		'icon_emoji': ':white_check_mark:',
		'text': f'*{user.profile.full_name}* just marked a research item complete:\n*Title*: {artifact.name}\nhttps://REPLACE_ME{url}',
	}
	
	if slackUrl:
		r = requests.post(slackUrl, json=payload)


def sendEmail(emailData):
	try:
		fromEmail = emailData['fromEmail']
	except:
		fromEmail = 'do-not-reply@REPLACE_ME.com'
	
	try:
		email = EmailMultiAlternatives(
			subject = emailData['subject'],
			body = emailData['message'],
			from_email = fromEmail,
			bcc = emailData['recipients'],
		)
		email.attach_alternative(emailData['message'], "text/html")
		email.send()
		return ('Email sent', True)
	except Exception as ex:
		print(f"Error: {emailData['subject']} failed to send. Error message: {ex}")
		return (f"Error: {emailData['subject']} failed to send. Error message: {ex}", False)
		

def updateUserProfile(user):
	"""
	User profile is created on user.create, so we know user.profile exists when this is called.
	Fetches full name of user when the sign in. If user has name-change, 
	just have them sign out and sign in and it'll get updated.
	Since we keep persistent sign-in state we can keep this set on every sign in.
	"""
	user.profile.full_name = user.username
	
	user.save()


def createNewUser(email):
	emailLower = email.lower()

	user, created = User.objects.get_or_create(
		username = emailLower,
		defaults = {
			'email': emailLower,
			'password': get_random_string()
		}
	)
	
	# Profile is automatically created via user.save() signal.
	# Now create their profile via bluemix bluepages APIs.
	updateUserProfile(user)
	
	return user
	
	
