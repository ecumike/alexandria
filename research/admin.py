from django.contrib import admin

from .models import Method, Source, Status, Tag, Artifact, ArtifactSearch, Profile, PageView, BannerNotification, SurveyQuestionExclusion, BrokenLink


@admin.register(Method)
class MethodAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created_by',
        'created_at',
        'updated_by',
        'updated_at',
        'uxid',
        'name',
    )
    list_filter = ('created_by', 'created_at', 'updated_by', 'updated_at')
    search_fields = ('name',)
    date_hierarchy = 'created_at'


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created_by',
        'created_at',
        'updated_by',
        'updated_at',
        'uxid',
        'name',
    )
    list_filter = ('created_by', 'created_at', 'updated_by', 'updated_at')
    search_fields = ('name',)
    date_hierarchy = 'created_at'


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created_by',
        'created_at',
        'updated_by',
        'updated_at',
        'uxid',
        'name',
        'color_class',
        'text_color_class',
    )
    list_filter = ('created_by', 'created_at', 'updated_by', 'updated_at')
    search_fields = ('name',)
    date_hierarchy = 'created_at'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created_by',
        'created_at',
        'updated_by',
        'updated_at',
        'uxid',
        'name',
    )
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name',)
    date_hierarchy = 'created_at'


@admin.register(Artifact)
class ArtifactAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created_by',
        'created_at',
        'updated_by',
        'updated_at',
        'uxid',
        'owner',
        'name',
        'abstract',
        'description',
        'hypothesis',
        'target_audience',
        'findings',
        'test_start_date',
        'test_end_date',
        'research_date',
        'sort_date',
        'study_plan_urls',
        'final_report_urls',
        'source',
        'status',
        'archived',
        'alchemer_survey_id',
        'alchemer_survey_questions',
    )
    list_filter = (
        'created_at',
        'updated_at',
        'test_start_date',
        'test_end_date',
        'research_date',
        'sort_date',
        'archived',
    )
    raw_id_fields = ('created_by', 'updated_by', 'owner', 'source', 'status')
    search_fields = ('name',)
    date_hierarchy = 'created_at'


@admin.register(ArtifactSearch)
class ArtifactSearchAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created_at',
        'updated_at',
        'search_text',
        'search_count',
    )
    list_filter = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created_at',
        'user',
        'full_name',
        'image',
        'inactive',
        'whats_new_count',
        'whats_new_seen',
        'whats_new_email',
        'research_count',
    )
    list_filter = (
        'created_at',
        'inactive',
        'whats_new_seen',
        'whats_new_email',
    )
    raw_id_fields = ('user',)
    date_hierarchy = 'created_at'


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'modified', 'user', 'url', 'view_count')
    list_filter = ('created', 'modified')
    raw_id_fields = ('user',)


@admin.register(BannerNotification)
class BannerNotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'active', 'banner_text', 'banner_type')
    list_filter = ('active',)
    search_fields = ('name',)


@admin.register(SurveyQuestionExclusion)
class SurveyQuestionExclusionAdmin(admin.ModelAdmin):
    list_display = ('id', 'question_text')


@admin.register(BrokenLink)
class BrokenLinkAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created',
        'modified',
        'artifact',
        'link_url',
        'report_count',
    )
    list_filter = ('created', 'modified', 'artifact')
    
    