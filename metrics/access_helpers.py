from django.core.exceptions import PermissionDenied
from .models import *



# User extension for access control used in decorator functions and templates
#  to easily restrict view access and template functionality.
def hasAdminAccess(user):
	"""
	User is Superuser or member of the admin group.
	Return: {bool}
	"""
	try:
		hasAccess = user.is_superuser or user.groups.filter(name='admins').exists()
	except:
		hasAccess = False
	
	return hasAccess

def hasAdminAccess_decorator(user):
	if not hasAdminAccess(user):
		raise PermissionDenied
	return True
	

def isDomainAdmin(user, domain):
	"""
	User is admin of the domain or higher.
	Return: {bool}
	"""
	try:
		if domain:
			hasAccess = user in domain.admins.all() or domain.lead == user or user.hasAdminAccess()
		else: 
			hasAccess = user.hasAdminAccess()
	except:
		hasAccess = False
	
	return hasAccess

def isDomainAdmin_decorator(user):
	if not isDomainAdmin(user):
		raise PermissionDenied
	return True


def isProjectAdmin(user, project):
	"""
	User is admin of the project or higher.
	Return: {bool}
	"""
	try:
		hasAccess = user in project.admins.all() or project.contact == user or user.isDomainAdmin(project.domain)
	except:
		hasAccess = False
	
	return hasAccess


def isProjectEditor(user, project):
	"""
	User is editor of the project or higher.
	Return: {bool}
	"""
	try:
		hasAccess = user in project.editors.all() or isProjectAdmin(user, project)
	except:
		hasAccess = False
	
	return hasAccess


def isAnyDomainAdmin(user):
	"""
	User is an admin of any domain or higher.
	Return: {bool}
	"""
	try:
		hasAccess = Domain.objects.filter(Q(admins=user) | Q(lead=user)).count() > 0 or user.hasAdminAccess()
	except Exception as ex:
		hasAccess = False
	
	return hasAccess

def isAnyDomainAdmin_decorator(user):
	if not isAnyDomainAdmin(user):
		raise PermissionDenied
	return True


def isAnyProjectAdmin(user):
	"""
	User is an admin of any project or higher.
	Return: {bool}
	"""
	try:
		hasAccess = Project.objects.filter(Q(admins=user) | Q(contact=user)).count() > 0 or user.isAnyDomainAdmin()
	except Exception as ex:
		hasAccess = False
	
	return hasAccess

def isAnyProjectAdmin_decorator(user):
	if not isAnyProjectAdmin(user):
		raise PermissionDenied
	return True
	

def isAnyProjectEditor(user):
	"""
	User is an editor of any project or higher.
	Return: {bool}
	"""
	try:
		hasAccess = Project.objects.filter(editors=user).count() > 0 or user.isAnyProjectAdmin()
	except Exception as ex:
		hasAccess = False
	
	return hasAccess
	
def isAnyProjectEditor_decorator(user):
	if not isAnyProjectEditor(user):
		raise PermissionDenied
	return True


# Add decorator methods to User object so they are automatically available anywhere, even in templates!
# No need to pass this in thru views. 
# Template example usage: {% if request.user.hasAdminAccess %}
# View decorator usage:	 @user_passes_test(accessaccessHelpers.hasAdminAccess_decorator)
User.add_to_class('isAnyDomainAdmin', isAnyDomainAdmin)
User.add_to_class('isAnyProjectAdmin', isAnyProjectAdmin)
User.add_to_class('isAnyProjectEditor', isAnyProjectEditor)
User.add_to_class('hasAdminAccess', hasAdminAccess)
User.add_to_class('isDomainAdmin', isDomainAdmin)
User.add_to_class('isProjectAdmin', isProjectAdmin)
User.add_to_class('isProjectEditor', isProjectEditor)
