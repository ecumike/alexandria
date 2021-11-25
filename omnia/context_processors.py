from django.conf import settings

def app_settings(request):
	# return the value you want as a dictionnary. you may add multiple values in there.
	return {
		'DATABASE_HOST': settings.DATABASES['default']['HOST'],
		'CDN_FILES_URL': settings.CDN_FILES_URL,
		'LATEST_RESPONSE_DATE': '2021-11-20',
	}
