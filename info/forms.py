from django.forms import ModelForm
from django import forms
from django.contrib.admin.widgets import AdminDateWidget

from .models import *

DATE_PICKER = forms.TextInput(attrs={'type':'date', 'style': 'width: 160px'})


class FaqCategoryForm(ModelForm):
	required_css_class = 'bo-field-required'
	
	class Meta:
		model = FaqCategory
		exclude = ['created_by', 'updated_by']

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)


class FaqForm(ModelForm):
	required_css_class = 'bo-field-required'
	
	class Meta:
		model = Faq
		exclude = ['created_by', 'updated_by']

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)


class ReleaseNoteForm(ModelForm):
	required_css_class = 'bo-field-required'
	
	class Meta:
		model = ReleaseNote
		exclude = ['created_by', 'updated_by']
		widgets = {
			'date': DATE_PICKER,
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)


