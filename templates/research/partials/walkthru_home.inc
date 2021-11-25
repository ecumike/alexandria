{% load static %}

<link href="{% static 'shared/css/enjoyhint.min.css' %}" rel="stylesheet">
<script src="{% static 'shared/js/enjoyhint.min.js' %}"></script>

<script>
	
	jQuery(function () {
		var enjoyhint_instance = new EnjoyHint({}),
			enjoyhint_script_steps = [
				{'next #step-filter-tag': 'Keywords tagged by the owner of each research artifact.'},
				{'next #step-filter-method': 'The type of research method used.'},
				{'next #step-filter-status': 'Pretty self-explanatory here.'},
				{'next #step-filter-source': 'Who\'s research is it.'},
				{
					'next .custom-artifact-item' : 'A research artifact with high level summary,<br> hotlinked to the detail page containing the full set of info.',
					'nextButton': {'text': 'Finish'},
					'showSkip': false,
				},
			];
		
		function runWalkthru () {
			enjoyhint_instance.set(enjoyhint_script_steps);
			enjoyhint_instance.run();	 
		}
			
		runWalkthru();
	});
		
</script>
