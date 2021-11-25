{% load static %}

<link href="{% static 'shared/css/enjoyhint.min.css' %}" rel="stylesheet">
<script src="{% static 'shared/js/enjoyhint.min.js' %}"></script>

<script>
	
	jQuery(function () {
		var enjoyhint_instance = new EnjoyHint({}),
			enjoyhint_script_steps = [
				{'next #step-name': 'A name for your research artifact.<br>Keep it clear, concise, and limited to 255 chars.'},
				{'next #step-abstract': 'A summary of the research. This is displayed on the search list page.<br>Keep it clear, concise, and limited to 255 chars.'},
				{'next #step-description': 'A detailed description of the research.'},
				{'next #step-hypothesis': 'What you expected would happen as a result of this research.'},
				{'next #step-basic-tagging': 'Some basic meta data tagging about this research artifact.'},
				{'next #step-target_audience': 'Description of the users of the tool, app, or user experience <br>for which the research was conducted.<br>For example, personas affected.'},
				{'next #step-research_date': 'Date of the completed research (e.g., survey close date)'},
				{'next #step-study_plan_urls': 'Links to any study plans pertaining to this research.'},
				{'next #step-findings': 'Findings as a result of the research.\nKeep each item clear and concise.'},
				{'next #step-final_report_urls': 'Link(s) to the actual research report(s).'},
				{'next #step-tags': 'Keywords to associate this research with. Helps others easily find it.'},
				{'next #step-related_artifacts': 'Other research items related to this one.'},
				{'next #step-related_projects': 'Select the associated project so that it can be easily located.'},
				{'next #step-access-control' : 'Select the owner (if not you) and any additional editors for this research item.',
					'nextButton': {'text': 'Finish'},
					'showSkip': false,
				},
			];
		
		function runWalkthru () {
			enjoyhint_instance.set(enjoyhint_script_steps);
			jQuery('#id_status_1').prop('checked', true).trigger('change');
			enjoyhint_instance.run();	 
		}
			
		runWalkthru();
	});
		
</script>
