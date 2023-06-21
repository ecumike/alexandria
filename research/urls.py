"""
	research app URL Configuration

"""
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import reverse_lazy
from django.views.generic import RedirectView, TemplateView

from .views import *
import metrics.views.admin as metricsViews


## All URLs are namespaced in root URL config with "research"

urlpatterns = [
	## APIs	
	url(r'^api/artifacts/search/$', api_artifacts_search, name='api_artifacts_search'),
	url(r'^api/users/$', api_users, name='api_users'),
	url(r'^api/users/add/$', api_users_add, name='api_users_add'),
	url(r'^api/users/togglestate/(?P<id>[\w-]+)/$', api_users_toggle_state, name='api_users_toggle_state'),
	url(r'^api/userimage/$', api_save_user_image, name='api_save_user_image'),
	url(r'^api/adminaccess/$', api_adminaccess, name='api_adminaccess'),
	url(r'^api/tag/$', api_get_tag, name='api_get_tag'),
	url(r'^api/pv/$', api_page_view_tracker, name='api_page_view_tracker'),
	url(r'^api/brokenlink/$', api_report_broken_link, name='api_report_broken_link'),
	url(r'^api/file/upload/$', api_upload_file, name='api_upload_file'),
	url(r'^api/file/delete/$', api_delete_file, name='api_delete_file'),
	url(r'^api/file/relate/$', api_relate_file, name='api_relate_file'),
	
	## Pages
	url(r'^$', home, name='home'), 	
	url(r'^myresearch/$', myresearch, name='myresearch'),

	## Public/user-accessed version of adding/editing artifacts.
	url(r'^add/$', artifacts_add, name='artifacts_add'),
	url(r'^(?P<id>[\w-]+)/archive/$', artifacts_archive, name='artifacts_archive'),
	url(r'^(?P<id>[\w-]+)/delete/$', artifacts_delete, name='artifacts_delete'),
	url(r'^(?P<id>[\w-]+)/edit/$', artifacts_edit, name='artifacts_edit'),
	url(r'^(?P<id>[\w-]+)/unarchive/$', artifacts_unarchive, name='artifacts_unarchive'),
	url(r'^(?P<id>[\w-]+)/detail/$', artifacts_detail, name='artifacts_detail'),
	url(r'^file/$', get_file, name='get_file'),
	
	## Start ADMIN URLs:
	url(r'^admin/$', metricsViews.admin_home, name='admin_home'),
	url(r'^admin/adminaccess/$', admin_adminaccess, name='admin_adminaccess'),
	url(r'^admin/artifacts/$', admin_artifacts_list, name='admin_artifacts_list'),
	url(r'^admin/artifacts/notags/$', admin_artifacts_notags, name='admin_artifacts_notags'),
	url(r'^admin/batchchanges/$', admin_batch_changes, name='admin_batch_changes'),
	url(r'^admin/pageviews/$', admin_pageviews, name='admin_pageviews'),
	url(r'^admin/users/$', admin_users, name='admin_users'),
	
	## Taxonomy admin URLs:
	url(r'^admin/method/$', admin_method_list, name='admin_method_list'),
	url(r'^admin/method/add/$', admin_method_add, name='admin_method_add'),
	url(r'^admin/method/edit/(?P<id>[\w-]+)/$', admin_method_edit, name='admin_method_edit'),
	
	url(r'^admin/source/$', admin_source_list, name='admin_source_list'),
	url(r'^admin/source/add/$', admin_source_add, name='admin_source_add'),
	url(r'^admin/source/edit/(?P<id>[\w-]+)/$', admin_source_edit, name='admin_source_edit'),

	url(r'^admin/status/$', admin_status_list, name='admin_status_list'),
	url(r'^admin/status/add/$', admin_status_add, name='admin_status_add'),
	url(r'^admin/status/edit/(?P<id>[\w-]+)/$', admin_status_edit, name='admin_status_edit'),

	url(r'^admin/tag/$', admin_tag_list, name='admin_tag_list'),
	url(r'^admin/tag/add/$', admin_tag_add, name='admin_tag_add'),
	url(r'^admin/tag/edit/(?P<id>[\w-]+)/$', admin_tag_edit, name='admin_tag_edit'),

	url(r'^admin/surveyquestionexclusion/$', admin_surveyquestionexclusion_list, name='admin_surveyquestionexclusion_list'),
	url(r'^admin/surveyquestionexclusion/add/$', admin_surveyquestionexclusion_add, name='admin_surveyquestionexclusion_add'),
	url(r'^admin/surveyquestionexclusion/edit/(?P<id>[\w-]+)/$', admin_surveyquestionexclusion_edit, name='admin_surveyquestionexclusion_edit'),
	url(r'^admin/surveyquestionexclusion/delete/$', admin_surveyquestionexclusion_delete, name='admin_surveyquestionexclusion_delete'),
	
	url(r'^admin/brokenlink/$', admin_brokenlink_list, name='admin_brokenlink_list'),
	url(r'^admin/brokenlink/$', admin_brokenlink_list, name='admin_brokenlink_add'),
	url(r'^admin/brokenlink/delete/$', admin_brokenlink_delete, name='admin_brokenlink_delete'),
	

	## Standard pages to put on all apps.
	url(r'^fnb/$', TemplateView.as_view(template_name="research/fnb.html"), name='fnb'),
	
	## Sign in/out.
	url(r'^signin/$', signin, name='signin'),
	url(r'^signout/$', signout, name='signout'),
	
	# Redirect from old URL to new one. Must come last.
	url(r'^(?P<id>[\w-]+)/$', redirect_artifacts_detail),

	
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

## DEBUG is in root URL file.
