"""
	Metrics app URL Configuration

"""
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import reverse_lazy
from django.views.generic import RedirectView, TemplateView

from .views import *


## All URLs are namespaced in root URL config with "metrics"

urlpatterns = [
	# APIs.
	url(r'^api/activeusabillacampaigns/$', api_active_usabilla_campaigns, name='api_active_usabilla_campaigns'),
	url(r'^api/projects/links/$', api_projects_links, name='api_projects_links'),
	url(r'^api/projects/voteresponses/download/$', api_projects_vote_responses, name='api_projects_vote_responses'),
	url(r'^api/survey/submit/rawdata/$', api_survey_submit_raw_data, name='api_survey_submit_raw_data'),
	
	# Admin only APIs:
	url(r'^api/deleteprojectresponses/$', api_delete_project_responses, name='api_delete_project_responses'),
	url(r'^api/deleteresponse/$', api_delete_response, name='api_delete_response'),
	url(r'^api/recalculatesnapshot/$', api_recalculate_snapshot, name='api_recalculate_snapshot'),
	url(r'^api/setresponsesgoal/$', api_set_responses_goal, name='api_set_responses_goal'),
			
	
	# API Crons: run daily or weekly.
	url(r'^api/addbeeheardcampaign/$', api_add_beeheard_campaign, name='api_add_beeheard_campaign'),
	url(r'^api/deactivateoldcampaigns/$', api_deactivate_old_campaigns, name='api_deactivate_old_campaigns'),
	url(r'^api/getnewbeeheardresponses/$', api_get_new_beeheard_responses, name='api_get_new_beeheard_responses'),
	url(r'^api/getnewusabillaresponses/$', api_get_new_usabilla_responses, name='api_get_new_usabilla_responses'),
	url(r'^api/pruneactivitylog/$', api_prune_activity_log, name='api_prune_activity_log'),
	url(r'^api/prunealerthistory/$', api_prune_alert_history, name='api_prune_alert_history'),
	url(r'^api/removeoldemails/$', api_remove_old_emails, name='api_remove_old_emails'),
	url(r'^api/scheduledalerts/$', api_do_scheduled_alerts, name='api_do_scheduled_alerts'),
	url(r'^api/setuxspecialistassigned/$', api_set_ux_specialist_assigned, name='api_set_ux_specialist_assigned'),

	# Redirects.
	url(r'^domains/$', tiles_table_router, name='domains_home'),
	url(r'^domains/tiles/$', domains_tiles, name='domains_tiles'),
	url(r'^domains/table/$', domains_table, name='domains_table'), # Hidden, no longer linked.
	url(r'^tilestableview/$', tiles_table_router, name='tiles_table_router'),
	url(r'^projectdetail/$', redirect_project_detail),
	url(r'^responsescomments/$', redirect_project_comments, name='redirect_project_comments'),
	url(r'^projects/responses/$', redirect_project_comments, name='redirect_project_comments'),
	
	## Pages
	url(r'^$', metrics_home, name='home'),
	url(r'^projects/$', projects_home, name='projects_home'),
	url(r'^projects/detail/$', projects_detail, name='projects_detail'),
	url(r'^projects/responses/vote/$', projects_vote_responses, name='projects_vote_responses'),
	url(r'^projects/responses/feedback/$', projects_feedback_responses, name='projects_feedback_responses'),
	url(r'^projects/responses/feedback/detail/(?P<uid>[\w-]+)/$', projects_feedback_responses_detail, name='projects_feedback_responses_detail'),
	url(r'^projects/responses/feedback/csvdump/$', project_feedback_responses_csv_dump, name='project_feedback_responses_csv_dump'),
	url(r'^projects/responses/vote/csvdump/$', project_vote_responses_csv_dump, name='project_vote_responses_csv_dump'),
	url(r'^projects/responses/vote/timeperiodcsvdump/$', project_vote_responses_timeperiod_csv_dump, name='project_vote_responses_timeperiod_csv_dump'),
	url(r'^alerts/$', alerts, name='alerts'),
	url(r'^responsecounts/$', response_counts, name='response_counts'),
	url(r'^tasks/$', tasks_home, name='tasks_home'),
	url(r'^tasks/detail/(?P<id>[\w-]+)/$', tasks_detail, name='tasks_detail'),
	
	
	
	
	## Admin pages:
	url(r'^admin/$', admin_home, name='admin_home'),
	
	url(r'^admin/importdata/(?P<modelName>[\w-]+)/$', admin_import_data_list, name='admin_import_data_list'),
	url(r'^admin/emailallresponsesascsv/$', admin_email_all_responses_as_csv, name='admin_email_all_responses_as_csv'),
	url(r'^admin/getnewbeeheardresponses/$', admin_get_new_beeheard_responses, name='admin_get_new_beeheard_responses'),
	url(r'^admin/getnewusabillaresponses/$', admin_get_new_usabilla_responses, name='admin_get_new_usabilla_responses'),
	url(r'^admin/importlog/$', admin_import_log, name='admin_import_log'),
	url(r'^admin/pageviews/$', admin_page_views, name='admin_page_views'),
	url(r'^admin/pageviews/download/$', admin_page_views_download, name='admin_page_views_download'),
	
	url(r'^admin/activitylog/$', admin_activity_log, name='admin_activity_log'),
	url(r'^admin/inactiveusers/$', admin_inactive_users, name='admin_inactive_users'),
	
	url(r'^admin/domain/$', admin_domain_list, name='admin_domain_list'),
	url(r'^admin/domain/add/$', admin_domain_add, name='admin_domain_add'),
	url(r'^admin/domain/edit/(?P<id>[\w-]+)/$', admin_domain_edit, name='admin_domain_edit'),
	url(r'^admin/domain/delete/$', admin_domain_delete, name='admin_domain_delete'),

	url(r'^admin/project/$', admin_project_list, name='admin_project_list'),
	url(r'^admin/project/add/$', admin_project_add, name='admin_project_add'),
	url(r'^admin/project/edit/(?P<id>[\w-]+)/$', admin_project_edit, name='admin_project_edit'),
	url(r'^admin/project/delete/$', admin_project_delete, name='admin_project_delete'),
	
	url(r'^admin/projectsnapshots/$', admin_projectsnapshot_list, name='admin_projectsnapshot_list'),
	url(r'^admin/projectsnapshots/add/$', admin_projectsnapshot_add, name='admin_projectsnapshot_add'),
	url(r'^admin/projectsnapshots/edit/(?P<id>[\w-]+)/$', admin_projectsnapshot_edit, name='admin_projectsnapshot_edit'),

	url(r'^admin/campaign/$', admin_campaign_list, name='admin_campaign_list'),
	url(r'^admin/campaign/add/$', admin_campaign_add, name='admin_campaign_add'),
	url(r'^admin/campaign/edit/(?P<id>[\w-]+)/$', admin_campaign_edit, name='admin_campaign_edit'),
	url(r'^admin/campaign/delete/$', admin_campaign_delete, name='admin_campaign_delete'),
	url(r'^admin/campaign/deleteallresponses/$', admin_campaign_delete_all_responses, name='admin_campaign_delete_all_responses'),

	url(r'^admin/campaignnoproject/$', admin_campaign_noproject_list, name='admin_campaign_noproject_list'),
	
	url(r'^admin/goalcompletedcategory/$', admin_goalcompletedcategory_list, name='admin_goalcompletedcategory_list'),
	url(r'^admin/goalcompletedcategory/add/$', admin_goalcompletedcategory_add, name='admin_goalcompletedcategory_add'),
	url(r'^admin/goalcompletedcategory/edit/(?P<id>[\w-]+)/$', admin_goalcompletedcategory_edit, name='admin_goalcompletedcategory_edit'),

	url(r'^admin/npslettergrade/$', admin_npslettergrade_list, name='admin_npslettergrade_list'),
	url(r'^admin/npslettergrade/add/$', admin_npslettergrade_add, name='admin_npslettergrade_add'),
	url(r'^admin/npslettergrade/edit/(?P<id>[\w-]+)/$', admin_npslettergrade_edit, name='admin_npslettergrade_edit'),

	url(r'^admin/npsscorecategory/$', admin_npsscorecategory_list, name='admin_npsscorecategory_list'),
	url(r'^admin/npsscorecategory/add/$', admin_npsscorecategory_add, name='admin_npsscorecategory_add'),
	url(r'^admin/npsscorecategory/edit/(?P<id>[\w-]+)/$', admin_npsscorecategory_edit, name='admin_npsscorecategory_edit'),

	url(r'^admin/projectevent/$', admin_projectevent_list, name='admin_projectevent_list'),
	url(r'^admin/projectevent/add/$', admin_projectevent_add, name='admin_projectevent_add'),
	url(r'^admin/projectevent/edit/(?P<id>[\w-]+)/$', admin_projectevent_edit, name='admin_projectevent_edit'),
	url(r'^admin/projectevent/delete/(?P<id>[\w-]+)/$', admin_projectevent_delete, name='admin_projectevent_delete'),
	
	url(r'^admin/projectyearsetting/$', admin_projectyearsetting_list, name='admin_projectyearsetting_list'),
	url(r'^admin/projectyearsetting/add/$', admin_projectyearsetting_add, name='admin_projectyearsetting_add'),
	url(r'^admin/projectyearsetting/edit/(?P<id>[\w-]+)/$', admin_projectyearsetting_edit, name='admin_projectyearsetting_edit'),
	
	url(r'^admin/domainyearsnapshot/$', admin_domainyearsnapshot_list, name='admin_domainyearsnapshot_list'),
	url(r'^admin/domainyearsnapshot/add/$', admin_domainyearsnapshot_add, name='admin_domainyearsnapshot_add'),
	url(r'^admin/domainyearsnapshot/edit/(?P<id>[\w-]+)/$', admin_domainyearsnapshot_edit, name='admin_domainyearsnapshot_edit'),
	
	url(r'^admin/datasource/$', admin_datasource_list, name='admin_datasource_list'),
	url(r'^admin/datasource/add/$', admin_datasource_add, name='admin_datasource_add'),
	url(r'^admin/datasource/edit/(?P<id>[\w-]+)/$', admin_datasource_edit, name='admin_datasource_edit'),
	
	url(r'^admin/umuxscorecategory/$', admin_umuxscorecategory_list, name='admin_umuxscorecategory_list'),
	url(r'^admin/umuxscorecategory/add/$', admin_umuxscorecategory_add, name='admin_umuxscorecategory_add'),
	url(r'^admin/umuxscorecategory/edit/(?P<id>[\w-]+)/$', admin_umuxscorecategory_edit, name='admin_umuxscorecategory_edit'),

	url(r'^admin/responsesexport/$', admin_responses_export, name='admin_responses_export'),
	url(r'^admin/responsesascsv/$', admin_responses_as_csv, name='admin_responses_as_csv'),
	url(r'^admin/responsesimportgoal/$', admin_responses_import_goal, name='admin_responses_import_goal'),

	url(r'^admin/target/$', admin_target_list, name='admin_target_list'),
	url(r'^admin/target/add/$', admin_target_add, name='admin_target_add'),
	url(r'^admin/target/edit/(?P<id>[\w-]+)/$', admin_target_edit, name='admin_target_edit'),
	url(r'^admin/target/delete/$', admin_target_delete, name='admin_target_delete'),

	url(r'^admin/projectkeyword/$', admin_projectkeyword_list, name='admin_projectkeyword_list'),
	url(r'^admin/projectkeyword/add/$', admin_projectkeyword_add, name='admin_projectkeyword_add'),
	url(r'^admin/projectkeyword/edit/(?P<id>[\w-]+)/$', admin_projectkeyword_edit, name='admin_projectkeyword_edit'),
	url(r'^admin/projectkeyword/delete/$', admin_projectkeyword_delete, name='admin_projectkeyword_delete'),

	url(r'^admin/uxspecialistassigned/add/$', admin_uxspecialistassigned_add, name='admin_uxspecialistassigned_add'),
	url(r'^admin/uxspecialistassigned/delete/$', admin_uxspecialistassigned_delete, name='admin_uxspecialistassigned_delete'),
	
	url(r'^admin/emailadmins/$', admin_email_admins, name='admin_email_admins'),
	
	url(r'^admin/onlineusers/$', admin_online_users, name='admin_online_users'),
	
	url(r'^admin/projectkeywordtagging/$', admin_project_keyword_tagging, name='admin_project_keyword_tagging'),
	url(r'^admin/projectkeywordtagging/remove/$', admin_project_keyword_tagging_remove, name='admin_project_keyword_tagging_remove'),
	url(r'^admin/projectkeywordtagging/add/$', admin_project_keyword_tagging_add, name='admin_project_keyword_tagging_add'),
	
	url(r'^admin/role/$', admin_role_list, name='admin_role_list'),
	url(r'^admin/role/add/$', admin_role_add, name='admin_role_add'),
	url(r'^admin/role/edit/(?P<id>[\w-]+)/$', admin_role_edit, name='admin_role_edit'),
	url(r'^admin/role/delete/$', admin_role_delete, name='admin_role_delete'),
	
	url(r'^admin/task/$', admin_task_list, name='admin_task_list'),
	url(r'^admin/task/add/$', admin_task_add, name='admin_task_add'),
	url(r'^admin/task/edit/(?P<id>[\w-]+)/$', admin_task_edit, name='admin_task_edit'),
	url(r'^admin/task/delete/$', admin_task_delete, name='admin_task_delete'),
	
	url(r'^admin/projectsnapshots/export/csv/$', admin_projectsnapshots_to_csv, name='admin_projectsnapshots_to_csv'),
	
	
	# Misc
	#url(r'^feedback.js$', feedback_js, name='feedback_js'),
	url(r'^claudeistheman/$', claude_temp, name='claude_temp'),
	url(r'^claudeistheman/dabby1/$', claude_temp_dabby1, name='claude_temp_dabby1'),
	url(r'^claudeistheman/dabby2/$', claude_temp_dabby2, name='claude_temp_dabby2'),
	
	
	
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

## DEBUG is in root URL file.
