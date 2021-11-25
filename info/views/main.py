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

from login_required_middleware import login_exempt

from ..models import *
from research.models import Artifact
from metrics.models import Project


def getBreadcrumbBase():
	return [
		{
			'text': 'Info',
			'url': reverse('info:home')
		}
	]
	

##
##	/info/
##
##
def home(request):
	context = {
		'researchItemsCount': Artifact.objects.count(),
		'projectsCount': Project.objects.allActive().count()
	}
	return render(request, 'info/home.html', context)


##
##	/info/faqs/
##
##
def faqs_list(request):
	# Put Glossary at the end/last.
	faqCategories = []
	for fcat in FaqCategory.objects.exclude(name='Glossary').prefetch_related('faq_categories').order_by('name'):
		faqCategories.append(fcat)
	faqCategories.append(FaqCategory.objects.filter(name='Glossary').prefetch_related('faq_categories').order_by('name').get())
	
	context = {
		'faqCatgories': faqCategories,
		'highlightHeaderLink': 'faqs',
		'highlightLeftnavLink': 'faqs',
	}
	return render(request, 'info/faqs.html', context)


##
##	/info/whatsnew/
##
##
def whatsnew_list(request):
	whatsNews = WhatsNew.objects.all()
		
	context = {
		'whatsNews': whatsNews,
		'featuredItem': whatsNews.filter(featured=True),
		'highlightLeftnavLink': 'whatsnew',
	}
	return render(request, 'info/whatsnew_list.html', context)


##
##	/info/releasenotes/
##
##
def release_notes(request):
	releaseNotes = ReleaseNote.objects.all()
		
	context = {
		'releaseNotes': releaseNotes,
		'highlightLeftnavLink': 'releasenotes',
	}
	return render(request, 'info/release_notes.html', context)

