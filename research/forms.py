from django.forms import ModelForm
from django import forms
from django.contrib.admin.widgets import AdminDateWidget

from .models import *

DATE_PICKER = forms.TextInput(attrs={'type':'date', 'style': 'width: 160px'})

class BasicTaxonomyForm(ModelForm):
	required_css_class = 'bl-field-required'
	
	class Meta:
		model = None
		exclude = ['created_by', 'updated_by', 'uxid']

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
class MethodForm(BasicTaxonomyForm):
	class Meta(BasicTaxonomyForm.Meta):
		model = Method
		
class SourceForm(BasicTaxonomyForm):
	class Meta(BasicTaxonomyForm.Meta):
		model = Source
		
class StatusForm(BasicTaxonomyForm):
	class Meta(BasicTaxonomyForm.Meta):
		model = Status
		
class SurveyQuestionExclusionForm(BasicTaxonomyForm):
	class Meta(BasicTaxonomyForm.Meta):
		model = SurveyQuestionExclusion
		
class TagForm(BasicTaxonomyForm):
	class Meta(BasicTaxonomyForm.Meta):
		model = Tag
		

class ArtifactForm(ModelForm):
	required_css_class = 'bl-field-required'
	
	class Meta:
		model = Artifact
		exclude = ['created_by', 'updated_by', 'uxid', 'sort_date']
		widgets = {
			'research_date': forms.TextInput(attrs={'type':'date'}),
			'abstract': forms.Textarea(attrs={'rows':3, 'class':'bl-common-autotextarea'}),
			'description': forms.Textarea(attrs={'rows':3, 'class':'bl-common-autotextarea'}),
			'hypothesis': forms.Textarea(attrs={'rows':3, 'class':'bl-common-autotextarea'}),
			'owner': forms.Select(attrs={'data-placeholder':'Select one', 'data-widget':'addnewuser'}),
			'editors': forms.SelectMultiple(attrs={'data-widget':'addnewuser'}),
			
		}

	def __init__(self, *args, **kwargs):
		self.base_fields['owner'].choices = Profile.usersByFullnameWithEmpty()
		self.base_fields['editors'].choices = Profile.usersByFullname()
		self.base_fields['projects'].queryset = Project.objects.allActive()
		super().__init__(*args, **kwargs)
		
		
		
		