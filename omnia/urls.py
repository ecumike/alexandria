"""omnia URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
	https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
	1. Add an import:  from my_app import views
	2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
	1. Add an import:  from other_app.views import Home
	2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
	1. Import the include() function: from django.urls import include, path
	2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import path, reverse_lazy
from django.views.generic import RedirectView, TemplateView



#  This is only needed to do custom processing when a 404/500 happens, 
#	otherwise, just make 404|500.html template file.
handler404 = 'research.views.custom_404'
handler500 = 'research.views.custom_500'


def test403(request):
	return render(request, '403.html', {}, status=403)
	
def test404(request):
	return render(request, '404.html', {}, status=404)
	
def test500(request):
	return render(request, '500.html', {}, status=500)


urlpatterns = [
	path('djangoadmin/doc/', include('django.contrib.admindocs.urls')),
	path('djangoadmin/', admin.site.urls),
	
	## Root home page to new web site home page.
	url(r'^$', RedirectView.as_view(pattern_name='info:home', permanent=False)),
    
	## Map default favicon URL to static file location.
	url(r'^favicon.ico$', RedirectView.as_view(
		url=staticfiles_storage.url('shared/img/favicon.ico'),
		permanent=False),
		name="favicon"
	),

	## Research app URLs namespace.
	url(r'^research/', include(('research.urls', 'research'))),
	
	## Report app URLs namespace.
	url(r'^metrics/', include(('metrics.urls', 'metrics'))),
	
	## Web site app URLs namespace.
	url(r'^info/', include(('info.urls', 'info'))),
	
	## Hijack module URLs namespace.
	url(r'^hijack/', include('hijack.urls', namespace='hijack')),
	
		
	# Testing error handling
	url(r'^500/$', test500),
	url(r'^403/$', test403),
	url(r'^404/$', test404),
	

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)



if settings.DEBUG:
	from django.conf.urls.static import static
	from django.contrib.staticfiles.urls import staticfiles_urlpatterns
	import debug_toolbar

	# Serve static and media files from development server
	urlpatterns += staticfiles_urlpatterns()
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
	urlpatterns = [
		url(r'^__debug__/', include(debug_toolbar.urls)),
	] + urlpatterns

