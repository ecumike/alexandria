from django.contrib import admin

from .models import UserRole, Role, Url, GoalCompleted, Browser, OperatingSystem, PrimaryGoal, DeviceType, Country, State, City, DataSource, ProjectKeyword, NpsScoreCategory, Domain, Project, ProjectEvent, Campaign, NpsLetterGrade, UmuxScoreCategory, GoalCompletedCategory, Response, VoteResponse, FeedbackResponseKeyword, FeedbackResponse, OtherResponse, ProjectSnapshot, ImportLog, ProjectYearSetting, DomainYearSnapshot, ActivityLog, Target


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
	list_display = ('id', 'created_at', 'updated_at', 'name')
	list_filter = ('created_at', 'updated_at')
	search_fields = ('name',)
	date_hierarchy = 'created_at'


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
	list_display = ('id', 'created_at', 'updated_at', 'name')
	list_filter = ('created_at', 'updated_at')
	search_fields = ('name',)
	date_hierarchy = 'created_at'


@admin.register(Url)
class UrlAdmin(admin.ModelAdmin):
	list_display = ('id', 'created_at', 'updated_at', 'url')
	list_filter = ('created_at', 'updated_at')
	date_hierarchy = 'created_at'


@admin.register(GoalCompleted)
class GoalCompletedAdmin(admin.ModelAdmin):
	list_display = ('id', 'created_at', 'updated_at', 'name')
	list_filter = ('created_at', 'updated_at')
	search_fields = ('name',)
	date_hierarchy = 'created_at'


@admin.register(Browser)
class BrowserAdmin(admin.ModelAdmin):
	list_display = ('id', 'created_at', 'updated_at', 'name')
	list_filter = ('created_at', 'updated_at')
	search_fields = ('name',)
	date_hierarchy = 'created_at'


@admin.register(OperatingSystem)
class OperatingSystemAdmin(admin.ModelAdmin):
	list_display = ('id', 'created_at', 'updated_at', 'name')
	list_filter = ('created_at', 'updated_at')
	search_fields = ('name',)
	date_hierarchy = 'created_at'


@admin.register(PrimaryGoal)
class PrimaryGoalAdmin(admin.ModelAdmin):
	list_display = ('id', 'created_at', 'updated_at', 'name')
	list_filter = ('created_at', 'updated_at')
	search_fields = ('name',)
	date_hierarchy = 'created_at'


@admin.register(DeviceType)
class DeviceTypeAdmin(admin.ModelAdmin):
	list_display = ('id', 'created_at', 'updated_at', 'name')
	list_filter = ('created_at', 'updated_at')
	search_fields = ('name',)
	date_hierarchy = 'created_at'


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
	list_display = ('id', 'created_at', 'updated_at', 'name')
	list_filter = ('created_at', 'updated_at')
	search_fields = ('name',)
	date_hierarchy = 'created_at'


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
	list_display = ('id', 'created_at', 'updated_at', 'name')
	list_filter = ('created_at', 'updated_at')
	search_fields = ('name',)
	date_hierarchy = 'created_at'


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
	list_display = ('id', 'created_at', 'updated_at', 'name')
	list_filter = ('created_at', 'updated_at')
	search_fields = ('name',)
	date_hierarchy = 'created_at'


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
	list_display = (
		'id',
		'created_at',
		'created_by',
		'updated_at',
		'updated_by',
		'name',
	)
	list_filter = ('created_at', 'created_by', 'updated_at', 'updated_by')
	search_fields = ('name',)
	date_hierarchy = 'created_at'


@admin.register(ProjectKeyword)
class ProjectKeywordAdmin(admin.ModelAdmin):
	list_display = ('id', 'created_at', 'updated_at', 'name')
	list_filter = ('created_at', 'updated_at')
	search_fields = ('name',)
	date_hierarchy = 'created_at'


@admin.register(NpsScoreCategory)
class NpsScoreCategoryAdmin(admin.ModelAdmin):
	list_display = (
		'id',
		'created_at',
		'created_by',
		'updated_at',
		'updated_by',
		'name',
		'min_score_range',
		'max_score_range',
		'color_code',
		'text_color_code',
		'ux_points',
	)
	list_filter = ('created_at', 'created_by', 'updated_at', 'updated_by')
	search_fields = ('name',)
	date_hierarchy = 'created_at'


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
	list_display = (
		'id',
		'created_at',
		'created_by',
		'updated_at',
		'updated_by',
		'name',
		'lead',
	)
	list_filter = (
		'created_at',
		'created_by',
		'updated_at',
		'updated_by',
		'lead',
	)
	raw_id_fields = ('admins',)
	search_fields = ('name',)
	date_hierarchy = 'created_at'


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
	list_display = (
		'id',
		'created_at',
		'created_by',
		'updated_at',
		'updated_by',
		'inactive',
		'domain',
		'name',
		'priority',
		'private_comments',
		'contact',
		'url',
		'estimated_num_users',
		'core_project',
		'vendor_app',
		'comments',
		'latest_valid_snapshot',
		'latest_snapshot_by_date',
		'currently_reporting_snapshot',
		'latest_valid_currently_reporting_snapshot',
		'current_year_settings',
		'api_key',
	)
	list_filter = (
		'created_at',
		'updated_at',
		'inactive',
		'private_comments',
		'core_project',
	)
	raw_id_fields = (
		'created_by',
		'updated_by',
		'domain',
		'contact',
		'latest_valid_snapshot',
		'latest_snapshot_by_date',
		'currently_reporting_snapshot',
		'latest_valid_currently_reporting_snapshot',
		'current_year_settings',
	)
	search_fields = ('name',)
	date_hierarchy = 'created_at'


@admin.register(ProjectEvent)
class ProjectEventAdmin(admin.ModelAdmin):
	list_display = (
		'id',
		'created_at',
		'created_by',
		'updated_by',
		'updated_at',
		'name',
		'project',
		'date',
	)
	list_filter = ('created_at', 'updated_at', 'date')
	raw_id_fields = ('created_by', 'updated_by', 'project')
	search_fields = ('name',)
	date_hierarchy = 'created_at'


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
	list_display = (
		'id',
		'created_at',
		'created_by',
		'updated_at',
		'updated_by',
		'inactive',
		'project',
		'uid',
		'usabilla_button_id',
		'key',
		'latest_response_date',
		'vote_response_count',
		'feedback_response_count',
		'other_response_count',
	)
	list_filter = (
		'created_at',
		'updated_at',
		'inactive',
		'latest_response_date',
	)
	raw_id_fields = ('created_by', 'updated_by', 'project')
	date_hierarchy = 'created_at'


@admin.register(NpsLetterGrade)
class NpsLetterGradeAdmin(admin.ModelAdmin):
	list_display = (
		'id',
		'created_at',
		'created_by',
		'updated_at',
		'updated_by',
		'name',
		'min_score',
		'color_code',
	)
	list_filter = ('created_at', 'created_by', 'updated_at', 'updated_by')
	search_fields = ('name',)
	date_hierarchy = 'created_at'


@admin.register(UmuxScoreCategory)
class UmuxScoreCategoryAdmin(admin.ModelAdmin):
	list_display = (
		'id',
		'created_at',
		'created_by',
		'updated_at',
		'updated_by',
		'name',
		'min_score_range',
		'max_score_range',
		'color_code',
		'text_color_code',
	)
	list_filter = ('created_at', 'created_by', 'updated_at', 'updated_by')
	search_fields = ('name',)
	date_hierarchy = 'created_at'


@admin.register(GoalCompletedCategory)
class GoalCompletedCategoryAdmin(admin.ModelAdmin):
	list_display = (
		'id',
		'created_at',
		'created_by',
		'updated_at',
		'updated_by',
		'name',
		'min_score_range',
		'max_score_range',
		'color_code',
		'text_color_code',
	)
	list_filter = ('created_at', 'created_by', 'updated_at', 'updated_by')
	search_fields = ('name',)
	date_hierarchy = 'created_at'


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
	list_display = (
		'id',
		'created_at',
		'updated_at',
		'campaign',
		'uid',
		'date',
		'nps',
		'nps_category',
		'umux_capability',
		'umux_ease_of_use',
		'umux_score',
		'improvement_suggestion',
		'user_role',
		'primary_goal',
		'primary_goal_other',
		'goal_completed',
		'goal_not_completed_reason',
		'comments',
		'email_provided',
		'submitted_url',
		'location',
		'country',
		'state',
		'city',
		'total_time',
		'device_type',
		'browser',
		'operating_system',
		'raw_data',
	)
	list_filter = ('created_at', 'updated_at', 'date', 'email_provided')
	raw_id_fields = (
		'campaign',
		'user_role',
		'primary_goal',
		'goal_completed',
		'submitted_url',
		'country',
		'state',
		'city',
		'device_type',
		'browser',
		'operating_system',
	)
	date_hierarchy = 'created_at'


@admin.register(VoteResponse)
class VoteResponseAdmin(admin.ModelAdmin):
	list_display = (
		'id',
		'created_at',
		'updated_at',
		'campaign',
		'uid',
		'date',
		'nps',
		'nps_category',
		'umux_capability',
		'umux_ease_of_use',
		'umux_score',
		'improvement_suggestion',
		'user_role',
		'primary_goal',
		'primary_goal_other',
		'goal_completed',
		'goal_not_completed_reason',
		'comments',
		'email_provided',
		'submitted_url',
		'location',
		'country',
		'state',
		'city',
		'total_time',
		'device_type',
		'browser',
		'operating_system',
		'raw_data',
	)
	list_filter = ('created_at', 'updated_at', 'date', 'email_provided')
	raw_id_fields = (
		'campaign',
		'user_role',
		'primary_goal',
		'goal_completed',
		'submitted_url',
		'country',
		'state',
		'city',
		'device_type',
		'browser',
		'operating_system',
	)
	date_hierarchy = 'created_at'


@admin.register(FeedbackResponseKeyword)
class FeedbackResponseKeywordAdmin(admin.ModelAdmin):
	list_display = ('id', 'created_at', 'updated_at', 'name')
	list_filter = ('created_at', 'updated_at')
	search_fields = ('name',)
	date_hierarchy = 'created_at'


@admin.register(FeedbackResponse)
class FeedbackResponseAdmin(admin.ModelAdmin):
	list_display = (
		'id',
		'created_at',
		'updated_at',
		'date',
		'uid',
		'campaign',
		'rating',
		'feedback_type',
		'comments',
		'email_provided',
		'notes',
		'raw_data',
	)
	list_filter = ('created_at', 'updated_at', 'date', 'email_provided')
	raw_id_fields = ('campaign',)
	date_hierarchy = 'created_at'


@admin.register(OtherResponse)
class OtherResponseAdmin(admin.ModelAdmin):
	list_display = (
		'id',
		'created_at',
		'updated_at',
		'date',
		'uid',
		'campaign',
		'raw_data',
	)
	list_filter = ('created_at', 'updated_at', 'date', 'campaign')
	date_hierarchy = 'created_at'


@admin.register(ProjectSnapshot)
class ProjectSnapshotAdmin(admin.ModelAdmin):
	list_display = (
		'id',
		'created_at',
		'created_by',
		'updated_at',
		'updated_by',
		'data_source',
		'entry_type',
		'project',
		'date',
		'date_period',
		'date_quarter',
		'date_month',
		'nps_score',
		'nps_score_category',
		'nps_score_date',
		'nps_count',
		'nps_promoter_count',
		'nps_passive_count',
		'nps_detractor_count',
		'nps_margin_error',
		'nps_margin_error_lower',
		'nps_margin_error_upper',
		'nps_meaningful_data',
		'umux_score',
		'umux_score_category',
		'umux_score_date',
		'umux_count',
		'umux_scores_sum',
		'umux_capability_avg',
		'umux_ease_of_use_avg',
		'umux_margin_error',
		'umux_margin_error_lower',
		'umux_margin_error_upper',
		'umux_meaningful_data',
		'goal_completed_percent',
		'goal_completed_category',
		'goal_completed_date',
		'goal_completed_count',
		'response_day_range',
		'meaningful_response_count',
	)
	list_filter = (
		'created_at',
		'updated_at',
		'date',
		'nps_score_date',
		'nps_meaningful_data',
		'umux_score_date',
		'umux_meaningful_data',
		'goal_completed_date',
	)
	raw_id_fields = (
		'created_by',
		'updated_by',
		'data_source',
		'project',
		'nps_score_category',
		'umux_score_category',
		'goal_completed_category',
	)
	date_hierarchy = 'created_at'


@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
	list_display = (
		'id',
		'date',
		'responses_imported_count',
		'projects_affected_count',
		'run_time_seconds',
		'import_type',
		'user',
	)
	list_filter = ('date',)
	raw_id_fields = ('user',)


@admin.register(ProjectYearSetting)
class ProjectYearSettingAdmin(admin.ModelAdmin):
	list_display = (
		'id',
		'created_at',
		'created_by',
		'updated_at',
		'updated_by',
		'project',
		'year',
		'nps_target',
		'nps_target_exceed',
		'nps_baseline',
		'nps_baseline_created_at',
		'nps_baseline_response_count',
		'nps_baseline_margin_error',
		'nps_baseline_entry_type',
		'nps_baseline_score_category',
		'nps_baseline_from',
		'nps_baseline_last_response_at',
		'nps_baseline_response_day_range',
		'nps_baseline_notes',
		'umux_target',
		'umux_target_exceed',
		'umux_baseline',
		'umux_baseline_created_at',
		'umux_baseline_response_count',
		'umux_baseline_margin_error',
		'umux_baseline_entry_type',
		'umux_baseline_score_category',
		'umux_baseline_from',
		'umux_baseline_last_response_at',
		'umux_baseline_response_day_range',
		'umux_baseline_notes',
	)
	list_filter = (
		'created_at',
		'updated_at',
		'nps_baseline_created_at',
		'nps_baseline_last_response_at',
		'umux_baseline_created_at',
		'umux_baseline_last_response_at',
	)
	raw_id_fields = (
		'created_by',
		'updated_by',
		'project',
		'nps_baseline_score_category',
		'umux_baseline_score_category',
	)
	date_hierarchy = 'created_at'


@admin.register(DomainYearSnapshot)
class DomainYearSnapshotAdmin(admin.ModelAdmin):
	list_display = (
		'id',
		'created_at',
		'created_by',
		'updated_at',
		'updated_by',
		'domain',
		'year',
		'all_projects_count',
		'core_projects_count',
		'core_projects_percent',
		'vote_projects_count',
		'vote_projects_percent',
		'core_projects_currently_reporting_count',
		'core_projects_currently_reporting_percent',
		'core_projects_excellent_nps_count',
		'core_projects_excellent_nps_percent',
		'core_projects_nps_target_achieved_count',
		'core_projects_nps_target_achieved_percent',
		'core_projects_nps_score_points',
		'core_projects_nps_score_points_average',
		'core_projects_nps_letter_grade',
	)
	list_filter = (
		'created_at',
		'created_by',
		'updated_at',
		'updated_by',
		'domain',
		'core_projects_nps_letter_grade',
	)
	date_hierarchy = 'created_at'


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
	list_display = (
		'id',
		'timestamp',
		'user',
		'content_type',
		'object_id',
		'comments',
	)
	list_filter = ('timestamp',)
	raw_id_fields = ('user', 'content_type')


@admin.register(Target)
class TargetAdmin(admin.ModelAdmin):
	list_display = (
		'id',
		'created_at',
		'updated_at',
		'nps_score',
		'umux_score',
		'achieve_target',
		'exceed_target',
	)
	list_filter = ('created_at', 'updated_at')
	date_hierarchy = 'created_at'

