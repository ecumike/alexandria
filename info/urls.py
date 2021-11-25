"""
	info app URL Configuration

"""
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import reverse_lazy
from django.views.generic import RedirectView, TemplateView

from .views import *


## All URLs are namespaced in root URL config with "info"

urlpatterns = [
	## Pages
	url(r'^$', home, name='home'),
	url(r'^faqs/$', faqs_list, name='faqs_list'),
	url(r'^releasenotes/$', release_notes, name='release_notes'),
	url(r'^whatsnew/$', whatsnew_list, name='whatsnew_list'),

	## Admin
	url(r'^admin/faqcategory/$', admin_faqcategory_list, name='admin_faqcategory_list'),
	url(r'^admin/faqcategory/add/$', admin_faqcategory_add, name='admin_faqcategory_add'),
	url(r'^admin/faqcategory/edit/(?P<id>[\w-]+)/$', admin_faqcategory_edit, name='admin_faqcategory_edit'),

	url(r'^admin/faq/$', admin_faq_list, name='admin_faq_list'),
	url(r'^admin/faq/add/$', admin_faq_add, name='admin_faq_add'),
	url(r'^admin/faq/edit/(?P<id>[\w-]+)/$', admin_faq_edit, name='admin_faq_edit'),
	
	url(r'^admin/whatsnew/$', admin_whatsnew_list, name='admin_whatsnew_list'),
	url(r'^admin/whatsnew/add/$', admin_whatsnew_add, name='admin_whatsnew_add'),
	url(r'^admin/whatsnew/edit/(?P<id>[\w-]+)/$', admin_whatsnew_edit, name='admin_whatsnew_edit'),
	url(r'^admin/whatsnew/delete/$', admin_whatsnew_delete, name='admin_whatsnew_delete'),
	
	url(r'^admin/releasenote/$', admin_releasenote_list, name='admin_releasenote_list'),
	url(r'^admin/releasenote/add/$', admin_releasenote_add, name='admin_releasenote_add'),
	url(r'^admin/releasenote/edit/(?P<id>[\w-]+)/$', admin_releasenote_edit, name='admin_releasenote_edit'),
	url(r'^admin/releasenote/delete/$', admin_releasenote_delete, name='admin_releasenote_delete'),

	## APIs.
	url(r'^api/whatsnewforme/$', api_whats_new_for_me, name='api_whats_new_for_me'),
	url(r'^api/whatsnewemail/$', api_whats_new_email_subscription, name='api_whats_new_email_subscription'),
	url(r'^api/whatsnewread/$', api_whats_new_read, name='api_whats_new_read'),
	url(r'^api/whatsnewfeatured/$', api_whats_new_featured, name='api_whats_new_featured'),
	
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

## DEBUG is in root URL file.
