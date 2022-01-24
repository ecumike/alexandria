import io
import requests

from datetime import datetime, timedelta

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core import serializers
from django.db.models import Count, Value, Q, Avg
from django.db.models.functions import Lower
from django.forms.models import model_to_dict
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse


from ..models import *
import metrics.access_helpers as accessHelpers
import metrics.helpers as helpers

##
##	/info/api/whatsnewforme
##
def api_whats_new_for_me(request):
	'''
	Returns what's new items the user hasn't seen, up to 3, to populate
	to populate the toast and overlay
	'''
	try:
		whatsNewCount = request.user.profile.whats_new_count
	
		if whatsNewCount > 3:
			whatsNewCount = 3
		
		latestWhatsNewItems = list(WhatsNew.objects.order_by('-date').values('date', 'heading', 'description')[:whatsNewCount])
		
		httpCode = 200
		responseData = {
			'whatsNewItems': latestWhatsNewItems,
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
##	/info/api/whatsnewemail/
##
def api_whats_new_email_subscription(request):
	'''
	Toggle user's flag if they want what's new in an email or not.
	'''
	profile = request.user.profile
	
	if profile.whats_new_email:
		profile.whats_new_email = False
		profile.save()
	else:
		profile.whats_new_email = True
		profile.save()
	
	responseData = {
		'results': {
			'message': 'Done'
		}
	}
		
	return JsonResponse(responseData, status=200)
	

##
##	/info/api/whatsnewread/
##
def api_whats_new_read(request):
	'''
	Set user's flag that they've read the latest updates.
	'''
	request.user.profile.seenWhatsNew()
	
	responseData = {
		'results': {
			'message': 'Done'
		}
	}
		
	return JsonResponse(responseData, status=200)
	

##
##	/info/api/whatsnewfeatured/
##
@user_passes_test(accessHelpers.hasAdminAccess_decorator)
def api_whats_new_featured(request):
	'''
	Set a whats new item as the featured item.
	'''
	id = request.POST.get('id', None)
	whatsNewItem = get_object_or_404(WhatsNew, id=id)
	
	WhatsNew.objects.update(featured=False)
	whatsNewItem.featured=True
	whatsNewItem.save()
	
	helpers.setPageMessage(request, 'success', 'Featured item changed successfully.')
		
	responseData = {
		'results': {
			'message': 'Featured item changed successfully.'
		}
	}
		
	return JsonResponse(responseData, status=200)
	
