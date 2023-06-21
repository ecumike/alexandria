from django.forms import ModelForm
from django import forms
from django.contrib.admin.widgets import AdminDateWidget

from .models import *
from research.models import Profile

DATE_PICKER = forms.TextInput(attrs={'type':'date', 'style': 'width: 160px'})
requiredCssClass = 'bo-field-required'


class CampaignForm(ModelForm):
	required_css_class = requiredCssClass
	
	class Meta:
		model = Campaign
		readonly_fields = []
		exclude = ['created_by', 'updated_by']
		widgets = {
			'key': forms.TextInput(attrs={'readonly':'readonly'})
		}
		

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		

class DataSourceForm(ModelForm):
	required_css_class = requiredCssClass
	
	class Meta:
		model = DataSource
		exclude = ['created_by', 'updated_by']

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)


class DomainForm(ModelForm):
	required_css_class = requiredCssClass
	
	class Meta:
		model = Domain
		exclude = ['created_by', 'updated_by']
		widgets = {
			'lead': forms.Select(attrs={'data-widget':'addnewuser'}),
		}

	def __init__(self, *args, **kwargs):
		self.base_fields['lead'].choices = Profile.usersByFullnameWithEmpty()
		self.base_fields['admins'].choices = Profile.usersByFullname()
		super().__init__(*args, **kwargs)


class DomainYearSnapshotForm(ModelForm):
	required_css_class = requiredCssClass
	
	class Meta:
		model = DomainYearSnapshot
		exclude = ['created_by', 'updated_by']

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)


class FeedbackResponseForm(ModelForm):
	required_css_class = requiredCssClass
	
	class Meta:
		model = FeedbackResponse
		exclude = ['created_at', 'updated_at']
		widgets = {
			'assignees': forms.SelectMultiple(attrs={'data-widget':'addnewuser'}),
			'keywords': forms.SelectMultiple(attrs={'data-tags': 'true'}),
		}
	
	def __init__(self, *args, **kwargs):
		self.base_fields['assignees'].choices = Profile.usersByFullname()
		super().__init__(*args, **kwargs)


class GoalCompletedCategoryForm(ModelForm):
	required_css_class = requiredCssClass
	
	class Meta:
		model = GoalCompletedCategory
		exclude = ['created_by', 'updated_by']

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)


class NpsLetterGradeForm(ModelForm):
	required_css_class = requiredCssClass
	
	class Meta:
		model = NpsLetterGrade
		exclude = ['created_by', 'updated_by']

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)


class NpsScoreCategoryForm(ModelForm):
	required_css_class = requiredCssClass
	
	class Meta:
		model = NpsScoreCategory
		exclude = ['created_by', 'updated_by']

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)


class ProjectForm(ModelForm):
	required_css_class = requiredCssClass
	
	class Meta:
		model = Project
		exclude = ['created_by', 'updated_by']
		widgets = {
			'admins': forms.SelectMultiple(attrs={'data-widget':'addnewuser'}),
			'api_key': forms.TextInput(attrs={'style':'width: 160px'}),
			'comments': forms.Textarea(attrs={'class': 'bo-common-autotextarea', 'rows': '3'}),
			'contact': forms.Select(attrs={'data-widget':'addnewuser'}),
			'core_project': forms.TextInput(attrs={'type':'hidden'}),
			'current_year_settings': forms.TextInput(attrs={'type':'hidden'}),
			'currently_reporting_snapshot': forms.TextInput(attrs={'type':'hidden'}),
			'editors': forms.SelectMultiple(attrs={'data-widget':'addnewuser'}),
			'estimated_num_users': forms.TextInput(attrs={'class':'mw4'}),
			'latest_snapshot_by_date': forms.TextInput(attrs={'type':'hidden'}),
			'latest_valid_currently_reporting_snapshot': forms.TextInput(attrs={'type':'hidden'}),
			'latest_valid_snapshot': forms.TextInput(attrs={'type':'hidden'}),
			'priority': forms.Select(attrs={'data-width':'resolve','class':'w4'}),
			'vendor_app': forms.Select(attrs={'data-width':'resolve','class':'w4'}),
		}

	def __init__(self, *args, **kwargs):
		self.base_fields['contact'].choices = Profile.usersByFullnameWithEmpty()
		self.base_fields['admins'].choices = Profile.usersByFullname()
		self.base_fields['editors'].choices = Profile.usersByFullname()
		super().__init__(*args, **kwargs)


class ProjectEventForm(ModelForm):
	required_css_class = requiredCssClass
	
	class Meta:
		model = ProjectEvent
		exclude = ['created_by', 'updated_by']
		widgets = {
			'date': DATE_PICKER,
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)


class ProjectSnapshotForm(ModelForm):
	"""
	Fields that are hidden are calculated in view using snapshot 'calculateStats' method.
	"""
	required_css_class = requiredCssClass
	
	class Meta:
		model = ProjectSnapshot
		exclude = ['created_by', 'updated_by']
		widgets = {
			'date': DATE_PICKER,
			'date_period': forms.TextInput(attrs={'type':'hidden'}),
			'entry_type': forms.TextInput(attrs={'type':'hidden'}),
			'date_quarter': forms.TextInput(attrs={'type':'hidden'}),
			'date_month': forms.TextInput(attrs={'type':'hidden'}),
			'nps_meaningful_data': forms.TextInput(attrs={'type':'hidden'}),
			'nps_score_date': forms.TextInput(attrs={'type':'hidden'}),
			'nps_score_category': forms.TextInput(attrs={'type':'hidden'}),
			'nps_margin_error_lower': forms.TextInput(attrs={'type':'hidden'}),
			'nps_margin_error_upper': forms.TextInput(attrs={'type':'hidden'}),
			'umux_score_date': forms.TextInput(attrs={'type':'hidden'}),
			'umux_score_category': forms.TextInput(attrs={'type':'hidden'}),
			'umux_scores_sum': forms.TextInput(attrs={'type':'hidden'}),
			'umux_margin_error_lower': forms.TextInput(attrs={'type':'hidden'}),
			'umux_margin_error_upper': forms.TextInput(attrs={'type':'hidden'}),
			'umux_meaningful_data': forms.TextInput(attrs={'type':'hidden'}),
			'goal_completed_date': forms.TextInput(attrs={'type':'hidden'}),
			'goal_completed_category': forms.TextInput(attrs={'type':'hidden'}),
			'response_day_range': forms.TextInput(attrs={'type':'hidden'}),
			'meaningful_response_count': forms.TextInput(attrs={'type':'hidden'}),
		}
		
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)


class ProjectYearSettingForm(ModelForm):
	required_css_class = requiredCssClass
	
	class Meta:
		model = ProjectYearSetting
		exclude = ['created_by', 'updated_by']
		widgets = {
			'nps_baseline_entry_type': forms.TextInput(attrs={'type':'hidden'}),
			'updated_by': forms.TextInput(attrs={'readonly':'readonly'}),
			'nps_target': forms.TextInput(attrs={'readonly':'readonly'}),
			'nps_baseline_created_at': forms.TextInput(attrs={'readonly':'readonly'}),
			
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)


class UmuxScoreCategoryForm(ModelForm):
	required_css_class = requiredCssClass
	
	class Meta:
		model = UmuxScoreCategory
		exclude = ['created_by', 'updated_by']

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)


class TargetForm(ModelForm):
	required_css_class = requiredCssClass
	
	class Meta:
		model = Target
		exclude = ['created_by', 'updated_by']

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)


class EmailAdminsForm(forms.Form):
	required_css_class = requiredCssClass
	
	msg = forms.CharField(
		label = 'Email message',
		required = True,
		widget = forms.Textarea(attrs={'class': 'bo-common-autotextarea', 'rows': '5'})
	)


class ProjectKeywordForm(ModelForm):
	required_css_class = requiredCssClass
	
	class Meta:
		model =  ProjectKeyword
		exclude = ['created_by', 'updated_by']

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)



class RoleForm(ModelForm):
	required_css_class = requiredCssClass
	
	class Meta:
		model = Role
		exclude = ['created_by', 'updated_by']

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

