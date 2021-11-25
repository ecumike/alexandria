{% load static %}

<link href="{% static 'shared/css/enjoyhint.min.css' %}" rel="stylesheet">
<script src="{% static 'shared/js/enjoyhint.min.js' %}"></script>

<script>
	
	jQuery(function () {
		var enjoyhint_instance = new EnjoyHint({}),
			enjoyhint_script_steps = [
				{'next #step-domain-selector': 'View priority 1-3 tools &amp; services metrics for all domains, or scope to a specific domain'},
				{'next #step-meeting-target': '% of "currently reporting" that are achieving their NPS targets'},
				{'next #step-excellent-range': '% of "currently reporting" that are in NPS excellent range'},
				{'next #step-active': 'Priority 1-3 tools &amp; services with data in the past 180 days'},
				{'next #step-nps-grade': 'Letter grade based on current NPS'},
				{'next #step-list-most-improved': 'Priority 1-3 tools/services with the largest increase over their baseline NPS'},
				{'next #step-list-worst-nps': 'Priority 1-3 tools/services with the lowest NPS'},
				{'next #step-list-best-goal': 'Priority 1-3 tools/services with the highest goal completion rates'},
				{'next #step-list-piecharts': 'Distribution of priority 1-3 tools/services for all three dimensions: &nbsp; <br>NPS, ease &amp; capabilities, goal completion',
					'nextButton': {'text': 'Finish'},
					'showSkip': false,
				},
			];
		
		function runWalkthru () {
			enjoyhint_instance.set(enjoyhint_script_steps);
			//jQuery('#id_status_1').prop('checked', true).trigger('change');
			enjoyhint_instance.run();	 
		}
			
		runWalkthru();
	});
		
</script>
