import calendar
import json
import re
import math

from django import template
from django.db.models import Count, Q
from math import log, floor

from research.models import Artifact, BannerNotification
from research.helpers import hasEditorAccess

register = template.Library()


@register.inclusion_tag("partials/banner_notification.html")
def bannerNotification():
	"""
	Gets all active banners and displays them at page top, 
	using the 'banner_notification.html' template.
	"""
	return {"banners": BannerNotification.objects.filter(active=True)}


@register.filter
def noprotocol(fullUrl):
	"""
	Strips protocol off URL for nice display/hotlink text.
	Example: https://www.someDomain.com/some/path/here/
	Return: {string} URL with no protocol (ex: www.someDomain.com/some/path/here/)
	"""
	returnData = re.sub(r"https?://", "", fullUrl)
	returnData = re.sub(r"/$", "", returnData)

	return returnData


@register.filter
def replace_underscore(string):
	"""
	Replaces an underscore with a space.
	Return: {string}
	"""
	return string.replace('_', ' ')
	
	
@register.filter
def split(string, sep=','):
	"""
	Template usage of split()
	Example usage: {{ value|split:',' }}
	Return: {array} Array of strings separated by the given separator.
	"""
	return string.split(sep)
	

@register.filter
def toJson(jsonString):
	"""
	Takes json or array as a string and returns it as json so it can be parsed in loop.
	Example usage: {{ value|toJson }}
	Return: {json} 
	"""
	return json.loads(jsonString)


@register.filter()
def formatMinutes(m):
	s = math.floor(m * 60)
	mins = math.floor(s / 60);
	secs = math.floor(s - (mins * 60)); 
	return "%d:%02d" % (mins, secs);

##
## Global template HTML helpers for site consistency and easy redesigns.
##
@register.simple_tag(takes_context=True)
def getTemplateHelpers(context):
	horizontalSpace = 'ph3 ph4-ns'
	rounded = 'br2'
	
	commonButton = 'bw0 dib pointer ph3 pv2 custom-animate-all border-box lh-copy custom-standard-button ' + rounded
	smallButton = 'bw0 dib pointer ph3 pv2 custom-animate-all border-box ' + rounded
	
	tab = rounded + ' custom-tab relative w-auto bg-animate db pointer ph4 pv3 mb0 bw0 fw5 bg-near-white hover-bg-light-gray'
	
	# Icons from Carbon repo.
	icons = {
		'add': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="6 6 21 21" class="icon add"><defs><style>.cls-1{fill:none;}</style></defs><polygon points="17 15 17 7 15 7 15 15 7 15 7 17 15 17 15 25 17 25 17 17 25 17 25 15 17 15"/><rect class="cls-1" width="32" height="32"/></svg>',
		'archive': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" class="icon archive"><defs><style>.cls-1{fill:none;}</style></defs><rect x="14" y="19" width="4" height="2"/><path d="M6,2V28a2,2,0,0,0,2,2H24a2,2,0,0,0,2-2V2ZM24,28H8V16H24Zm0-14H8V10H24ZM8,8V4H24V8Z"/><rect class="cls-1" width="32" height="32"/></svg>',
		'arrowDown': '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32" class="icon"><defs><style>.cls-1 {fill: none;}</style></defs><polygon points="24.59 16.59 17 24.17 17 4 15 4 15 24.17 7.41 16.59 6 18 16 28 26 18 24.59 16.59"/><rect class="cls-1" width="32" height="32"/></svg>',
		'chat': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><defs><style>.cls-1{fill:none;}</style></defs><title>chat</title><path d="M17.74,30,16,29l4-7h6a2,2,0,0,0,2-2V8a2,2,0,0,0-2-2H6A2,2,0,0,0,4,8V20a2,2,0,0,0,2,2h9v2H6a4,4,0,0,1-4-4V8A4,4,0,0,1,6,4H26a4,4,0,0,1,4,4V20a4,4,0,0,1-4,4H21.16Z" transform="translate(0 0)"/><rect x="8" y="10" width="16" height="2"/><rect x="8" y="16" width="10" height="2"/><rect class="cls-1" width="32" height="32"/></svg>',
		'checkmark': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" class="icon checkmark"><defs><style>.cls-1{fill:none;}</style></defs><path d="M16,2A14,14,0,1,0,30,16,14,14,0,0,0,16,2Zm0,26A12,12,0,1,1,28,16,12,12,0,0,1,16,28Z"/><polygon points="14 21.5 9 16.54 10.59 14.97 14 18.35 21.41 11 23 12.58 14 21.5"/><rect class="cls-1" width="32" height="32"/></svg>',
		'chevronForward': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="8 0 18 24" class="icon chevron-forward"><g data-name="Layer 2"><g data-name="arrow-ios-forward"><rect width="24" height="24" transform="rotate(-90 12 12)" opacity="0"/><path d="M10 19a1 1 0 0 1-.64-.23 1 1 0 0 1-.13-1.41L13.71 12 9.39 6.63a1 1 0 0 1 .15-1.41 1 1 0 0 1 1.46.15l4.83 6a1 1 0 0 1 0 1.27l-5 6A1 1 0 0 1 10 19z"/></g></g></svg>',
		'close': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="2 2 20 20" class="icon close"><g data-name="Layer 2"><g data-name="close"><rect width="24" height="24" transform="rotate(180 12 12)" opacity="0"/><path d="M13.41 12l4.3-4.29a1 1 0 1 0-1.42-1.42L12 10.59l-4.29-4.3a1 1 0 0 0-1.42 1.42l4.3 4.29-4.3 4.29a1 1 0 0 0 0 1.42 1 1 0 0 0 1.42 0l4.29-4.3 4.29 4.3a1 1 0 0 0 1.42 0 1 1 0 0 0 0-1.42z"/></g></g></svg>',
		'copy': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" class="icon copy"><defs><style>.cls-1{fill:none;}</style></defs><path d="M28,10V28H10V10H28m0-2H10a2,2,0,0,0-2,2V28a2,2,0,0,0,2,2H28a2,2,0,0,0,2-2V10a2,2,0,0,0-2-2Z" /><path d="M4,18H2V4A2,2,0,0,1,4,2H18V4H4Z" /><rect class="cls-1" width="32" height="32"/></svg>',
		'csv': '<svg version="1.1" xmlns="http://www.w3.org/2000/svg" class="icon csv" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px" viewBox="0 0 512 512" style="enable-background:new 0 0 512 512;" xml:space="preserve"><g><g><g><path d="M443.536,141.584L312.208,4.912C309.184,1.776,305.024,0,300.672,0H80c-8.848,0-16,7.168-16,16v480c0,8.832,7.152,16,16,16h352c8.848,0,16-7.168,16-16V152.672C448,148.544,446.4,144.56,443.536,141.584z M304,42.56L401.488,144H304V42.56z M416,480H96V32h176v128c0,8.832,7.152,16,16,16h128V480z"/><path d="M158.208,333.2c2.96-3.136,6.224-5.328,10.016-6.736c6.48-2.4,13.376-2.784,20.944-1.536c2.784,0.464,6.304,1.44,10.4,2.928c2.656,0.928,5.584,0.432,7.76-1.328c2.176-1.776,3.248-4.56,2.864-7.328c-0.272-1.776-0.416-3.456-0.48-5.072c-0.16-3.6-2.688-6.656-6.208-7.456c-2.944-0.672-5.296-1.168-7.04-1.456c-1.776-0.304-4.096-0.576-6.896-0.832c-11.456-1.008-20.224,0.048-28.992,3.296c-6.896,2.544-12.896,6.512-17.856,11.792c-4.912,5.248-8.656,11.84-11.12,19.568c-2.4,7.36-3.6,15.12-3.6,23.04c0,7.184,1.04,14.128,3.104,20.64c2.176,6.896,5.664,12.96,10.336,18c4.688,5.072,10.384,8.96,16.944,11.536c6.368,2.48,13.152,3.744,20.176,3.744c3.216,0,6.88-0.24,10.96-0.736c4.064-0.496,8.384-1.36,13.008-2.608c3.216-0.864,5.584-3.648,5.888-6.976c0.176-1.792,0.368-3.328,0.656-4.672c0.624-2.832-0.336-5.76-2.512-7.68c-2.176-1.92-5.216-2.496-7.936-1.568c-13.36,4.656-24.08,5.232-32.688,1.68c-3.632-1.488-6.656-3.616-9.28-6.496c-2.592-2.832-4.496-6.368-5.84-10.784c-1.424-4.784-2.16-9.872-2.16-15.136c0-5.408,0.88-10.72,2.608-15.808C152.928,340.352,155.184,336.416,158.208,333.2z"/><path d="M277.12,372.768c-1.072-2.08-2.432-4.144-4.16-6.272c-1.536-1.904-3.136-3.664-5.552-5.984l-6.944-6.656c-3.504-3.344-6.32-6.096-8.4-8.224c-2.096-2.112-3.888-4-5.392-5.632c-1.248-1.36-2.256-2.608-3.008-3.728c-0.496-0.752-0.848-1.44-1.072-2.224c-0.176-0.544-0.256-1.136-0.256-1.856c0-1.328,0.336-2.528,1.072-3.776c0.736-1.248,1.728-2.192,3.152-2.992c2.416-1.344,7.104-1.552,12.08-0.656c2.24,0.4,5.008,1.2,8.336,2.336c2.656,0.928,5.584,0.368,7.744-1.424c2.16-1.808,3.2-4.608,2.768-7.376c-0.272-1.68-0.432-3.232-0.464-4.64c-0.064-3.744-2.72-6.944-6.384-7.68c-16.736-3.456-26.016-2.352-33.76,1.68c-4.992,2.576-8.832,6.176-11.424,10.704c-2.512,4.384-3.792,9.184-3.792,14.288c0,2.096,0.208,4.128,0.592,6.112c0.416,2.064,0.992,3.872,1.728,5.632c0.688,1.568,1.664,3.36,3.072,5.44c1.216,1.744,2.704,3.648,4.544,5.712c1.712,1.92,3.488,3.76,5.488,5.68l4.944,4.512c5.424,4.976,9.216,8.624,11.344,10.992c2.016,2.256,3.552,4.096,4.608,5.504c0.672,0.928,1.152,1.776,1.408,2.496c0.24,0.672,0.336,1.376,0.336,2.16c0,1.84-0.4,3.376-1.232,4.704c-0.8,1.248-1.872,2.144-3.424,2.832c-5.888,2.592-14.608,1.264-24.576-3.936c-2.592-1.36-5.744-1.2-8.192,0.464c-2.432,1.648-3.76,4.496-3.472,7.424c0.208,2.016,0.32,3.792,0.32,5.344c0,3.36,2.112,6.368,5.28,7.52c5.344,1.936,9.6,3.168,13.024,3.792c3.408,0.656,6.848,0.96,10.384,0.96c5.824,0,11.248-1.056,16.112-3.152c5.376-2.336,9.52-5.872,12.336-10.512c2.752-4.512,4.144-9.696,4.144-15.424c0-2.368-0.272-4.784-0.816-7.312C279.072,377.248,278.24,374.944,277.12,372.768z"/><path d="M287.952,315.952l23.024,69.76l6.96,23.04c1.008,3.52,4.304,5.84,7.92,5.808l3.328-0.064l3.264,0.064c0.08,0,0.144,0,0.224,0c3.216,0,6.144-1.936,7.376-4.912c3.392-8.08,7.504-17.248,12.304-27.456l16.304-34.896c5.968-12.848,10.8-22.944,14.496-30.24c1.28-2.528,1.12-5.552-0.4-7.936c-1.52-2.384-4.128-3.792-7.024-3.68l-2.64,0.048l-2.624-0.048c-3.392-0.256-6.416,1.856-7.68,4.944c-1.472,3.552-2.656,6.368-3.616,8.496l-28.336,61.616l-18.336-56.656l-3.632-12.624c-1.008-3.52-4.48-6.24-7.984-5.776l-2.496,0.048l-2.528-0.048c-2.624-0.336-5.104,1.088-6.672,3.184C287.584,310.72,287.12,313.456,287.952,315.952z"/></g></g></g></svg>',
		'edit': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" class="icon edit"><defs><style>.cls-1{fill:none;}</style></defs><rect x="2" y="27" width="28" height="2"/><path d="M25.41,9a2,2,0,0,0,0-2.83L21.83,2.59a2,2,0,0,0-2.83,0l-15,15V24h6.41Zm-5-5L24,7.59l-3,3L17.41,7ZM6,22V18.41l10-10L19.59,12l-10,10Z"/><rect class="cls-1" width="32" height="32"/></svg>',
		'flag': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" class="icon"><defs><style>.cls-1{fill:none;}</style></defs><path d="M6,30H4V2H28l-5.8,9L28,20H6ZM6,18H24.33L19.8,11l4.53-7H6Z"/><rect class="cls-1" width="32" height="32"/></svg>',
		'email': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="icon email"><g data-name="Layer 2"><g data-name="email"><rect width="24" height="24" opacity="0"/><path d="M19 4H5a3 3 0 0 0-3 3v10a3 3 0 0 0 3 3h14a3 3 0 0 0 3-3V7a3 3 0 0 0-3-3zm-.67 2L12 10.75 5.67 6zM19 18H5a1 1 0 0 1-1-1V7.25l7.4 5.55a1 1 0 0 0 .6.2 1 1 0 0 0 .6-.2L20 7.25V17a1 1 0 0 1-1 1z"/></g></g></svg>',
		'sad': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" class="icon sad"><defs><style>.cls-1{fill:none;}</style></defs><path d="M16,2A14,14,0,1,0,30,16,14,14,0,0,0,16,2Zm0,26A12,12,0,1,1,28,16,12,12,0,0,1,16,28Z" transform="translate(0)"/><path d="M11.5,11A2.5,2.5,0,1,0,14,13.5,2.5,2.5,0,0,0,11.5,11Z" transform="translate(0)"/><path d="M20.5,11A2.5,2.5,0,1,0,23,13.5,2.5,2.5,0,0,0,20.5,11Z" transform="translate(0)"/><path d="M16,19a8,8,0,0,0-6.85,3.89l1.71,1a6,6,0,0,1,10.28,0l1.71-1A8,8,0,0,0,16,19Z" transform="translate(0)"/><rect class="cls-1" width="32" height="32"/></svg>',
		'grid': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="2 -3 30 30" class="icon"><g data-name="Layer 2"><g data-name="grid"><rect width="24" height="24" opacity="0"/><path d="M9 3H5a2 2 0 0 0-2 2v4a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2zM5 9V5h4v4z"/><path d="M19 3h-4a2 2 0 0 0-2 2v4a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2zm-4 6V5h4v4z"/><path d="M9 13H5a2 2 0 0 0-2 2v4a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2v-4a2 2 0 0 0-2-2zm-4 6v-4h4v4z"/><path d="M19 13h-4a2 2 0 0 0-2 2v4a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2v-4a2 2 0 0 0-2-2zm-4 6v-4h4v4z"/></g></g></svg>',
		'help': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" class="icon help"><defs><style>.cls-1{fill:none;}</style></defs><path d="M16,2A14,14,0,1,0,30,16,14,14,0,0,0,16,2Zm0,26A12,12,0,1,1,28,16,12,12,0,0,1,16,28Z"/><circle cx="16" cy="23.5" r="1.5"/><path d="M17,8H15.5A4.49,4.49,0,0,0,11,12.5V13h2v-.5A2.5,2.5,0,0,1,15.5,10H17a2.5,2.5,0,0,1,0,5H15v4.5h2V17a4.5,4.5,0,0,0,0-9Z"/><rect class="cls-1" width="32" height="32"/></svg>',
		'idea': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" class="icon idea"><defs><style>.cls-1{fill:none;}</style></defs><rect x="11" y="24" width="10" height="2"/><rect x="13" y="28" width="6" height="2"/><path d="M16,2A10,10,0,0,0,6,12a9.19,9.19,0,0,0,3.46,7.62c1,.93,1.54,1.46,1.54,2.38h2c0-1.84-1.11-2.87-2.19-3.86A7.2,7.2,0,0,1,8,12a8,8,0,0,1,16,0,7.2,7.2,0,0,1-2.82,6.14c-1.07,1-2.18,2-2.18,3.86h2c0-.92.53-1.45,1.54-2.39A9.18,9.18,0,0,0,26,12,10,10,0,0,0,16,2Z" transform="translate(0 0)"/><rect class="cls-1" width="32" height="32"/></svg>',
		'info': '<svg id="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" class="icon info"><defs><style>.cls-1{fill:none;}</style></defs><polygon points="17 22 17 13 13 13 13 15 15 15 15 22 12 22 12 24 20 24 20 22 17 22"/><path d="M16,7a1.5,1.5,0,1,0,1.5,1.5A1.5,1.5,0,0,0,16,7Z"/><path d="M16,30A14,14,0,1,1,30,16,14,14,0,0,1,16,30ZM16,4A12,12,0,1,0,28,16,12,12,0,0,0,16,4Z"/><rect id="_Transparent_Rectangle_" data-name="&lt;Transparent Rectangle&gt;" class="cls-1" width="32" height="32"/></svg>',
		'list': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="icon"><g data-name="Layer 2"><g data-name="list"><rect width="24" height="24" transform="rotate(180 12 12)" opacity="0"/><circle cx="4" cy="7" r="1"/><circle cx="4" cy="12" r="1"/><circle cx="4" cy="17" r="1"/><rect x="7" y="11" width="14" height="2" rx=".94" ry=".94"/><rect x="7" y="16" width="14" height="2" rx=".94" ry=".94"/><rect x="7" y="6" width="14" height="2" rx=".94" ry=".94"/></g></g></svg>',
		'modal': '<svg xmlns="http://www.w3.org/2000/svg" class="icon modal" width="32" height="32" viewBox="0 0 32 32"><defs><style>.cls-1{fill:none;}</style></defs><path d="M28,4H10A2.0059,2.0059,0,0,0,8,6V20a2.0059,2.0059,0,0,0,2,2H28a2.0059,2.0059,0,0,0,2-2V6A2.0059,2.0059,0,0,0,28,4Zm0,16H10V6H28Z"/><path d="M18,26H4V16H6V14H4a2.0059,2.0059,0,0,0-2,2V26a2.0059,2.0059,0,0,0,2,2H18a2.0059,2.0059,0,0,0,2-2V24H18Z"/><rect class="cls-1" width="32" height="32"/></svg>',
		'newWindow': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="icon new-window"><g data-name="Layer 2"><g data-name="external-link"><rect width="24" height="24" opacity="0"/><path d="M20 11a1 1 0 0 0-1 1v6a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h6a1 1 0 0 0 0-2H6a3 3 0 0 0-3 3v12a3 3 0 0 0 3 3h12a3 3 0 0 0 3-3v-6a1 1 0 0 0-1-1z"/><path d="M16 5h1.58l-6.29 6.28a1 1 0 0 0 0 1.42 1 1 0 0 0 1.42 0L19 6.42V8a1 1 0 0 0 1 1 1 1 0 0 0 1-1V4a1 1 0 0 0-1-1h-4a1 1 0 0 0 0 2z"/></g></g></svg>',
		'poop': '<svg viewBox="0 0 24 24" class="icon" width="24" xmlns="http://www.w3.org/2000/svg"><path d="m19.581 24h-15.162c-2.437 0-4.419-1.982-4.419-4.419 0-1.88 1.201-3.508 2.896-4.131-.295-.568-.451-1.202-.451-1.86 0-2.101 1.606-3.833 3.656-4.032-.116-.295-.18-.613-.185-.937-.015-.975.355-1.894 1.039-2.589s1.599-1.077 2.574-1.077c1.166 0 2.114-.948 2.114-2.114v-2.091c0-.27.145-.519.38-.652.233-.133.522-.13.754.008l3.669 2.186c1.3.971 2.052 2.386 2.129 3.926.061 1.203-.296 2.37-.995 3.322 2.198.041 3.975 1.843 3.975 4.051 0 .658-.156 1.292-.451 1.86 1.695.622 2.896 2.25 2.896 4.13 0 2.437-1.982 4.419-4.419 4.419zm-13.084-12.962c-1.407 0-2.552 1.145-2.552 2.552 0 .686.27 1.33.761 1.813.21.208.278.52.176.796-.104.276-.359.467-.654.486-1.53.102-2.728 1.374-2.728 2.896 0 1.609 1.31 2.919 2.919 2.919h15.162c1.609 0 2.919-1.31 2.919-2.919 0-1.522-1.198-2.794-2.728-2.896-.295-.02-.551-.21-.654-.486s-.034-.588.176-.796c.491-.483.761-1.128.761-1.813 0-1.407-1.145-2.552-2.552-2.552h-1.968c-.355 0-.663-.25-.734-.599-.072-.349.111-.699.438-.84.255-.109.476-.25.657-.417.806-.742 1.236-1.796 1.182-2.891-.056-1.094-.589-2.099-1.465-2.757l-2.469-1.467v.772c0 1.993-1.621 3.614-3.614 3.614-.57 0-1.105.224-1.506.63s-.617.946-.608 1.517c.006.432.24.818.627 1.034.298.166.445.514.359.844s-.384.561-.726.561h-1.179z"/><path d="m8 15.485c-.827 0-1.5-.673-1.5-1.5s.673-1.5 1.5-1.5 1.5.673 1.5 1.5-.673 1.5-1.5 1.5zm0-1.501v.002l.75-.001z"/><path d="m16 15.485c-.827 0-1.5-.673-1.5-1.5s.673-1.5 1.5-1.5 1.5.673 1.5 1.5-.673 1.5-1.5 1.5zm0-1.501v.002l.75-.001z"/><path d="m12 22.006c-2.521 0-4.718-1.621-5.467-4.033-.07-.228-.028-.476.113-.668s.366-.305.604-.305h9.5c.238 0 .463.113.604.305.142.192.184.44.113.668-.749 2.412-2.946 4.033-5.467 4.033zm-3.594-3.506c.755 1.23 2.097 2.006 3.594 2.006s2.839-.775 3.594-2.006z"/></svg>',
		'sortup': '<svg xmlns="http://www.w3.org/2000/svg" x="0px" y="0px" class="icon" width="32px" height="32px" viewBox="0 0 32 32" style="enable-background:new 0 0 32 32;" xml:space="preserve"><style type="text/css">.st0{fill:none;}</style><polygon points="8,8 16,0 24,8 "/><rect id="_Transparent_Rectangle_" class="st0" width="32" height="32"/></svg>',
		'star': '<svg xmlns="http://www.w3.org/2000/svg" id="icon" viewBox="0 0 32 32" class="icon star"><defs><style>.cls-1{fill:none;}</style></defs><path d="M16,6.52l2.76,5.58.46,1,1,.15,6.16.89L22,18.44l-.75.73.18,1,1.05,6.13-5.51-2.89L16,23l-.93.49L9.56,26.34l1-6.13.18-1L10,18.44,5.58,14.09l6.16-.89,1-.15.46-1L16,6.52M16,2l-4.55,9.22L1.28,12.69l7.36,7.18L6.9,30,16,25.22,25.1,30,23.36,19.87l7.36-7.17L20.55,11.22Z"/><rect class="cls-1" width="32" height="32"/></svg>',
		'subtract': '<svg version="1.1" xmlns="http://www.w3.org/2000/svg" x="0px" y="0px" width="32px" height="32px" class="icon" viewBox="0 0 32 32" style="enable-background:new 0 0 32 32;" xml:space="preserve"><style type="text/css">	.st0{fill:none;}</style><rect x="8" y="15" width="16" height="2"/><rect class="st0" width="32" height="32"/></svg>',
		'table': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" class="icon table"><defs><style>.cls-1{fill:none;}</style></defs><path d="M27,3H5A2,2,0,0,0,3,5V27a2,2,0,0,0,2,2H27a2,2,0,0,0,2-2V5A2,2,0,0,0,27,3Zm0,2V9H5V5ZM17,11H27v7H17Zm-2,7H5V11H15ZM5,20H15v7H5Zm12,7V20H27v7Z"/><rect class="cls-1" width="32" height="32"/></svg>',
		'time': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" class="icon time"><defs><style>.cls-1{fill:none;}</style></defs><path d="M16,30A14,14,0,1,1,30,16,14,14,0,0,1,16,30ZM16,4A12,12,0,1,0,28,16,12,12,0,0,0,16,4Z"/><polygon points="20.59 22 15 16.41 15 7 17 7 17 15.58 22 20.59 20.59 22"/><rect class="cls-1" width="32" height="32"/></svg>',
		'trash': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" class="icon trash"><defs><style>.cls-1{fill:none;}</style></defs><rect x="12" y="12" width="2" height="12"/><rect x="18" y="12" width="2" height="12"/><path d="M4,6V8H6V28a2,2,0,0,0,2,2H24a2,2,0,0,0,2-2V8h2V6ZM8,28V8H24V28Z"/><rect x="12" y="2" width="8" height="2"/><rect class="cls-1" width="32" height="32"/></svg>',
		'unarchive': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" class="icon unarchive"><defs><style>.cls-1{fill:none;}</style></defs><path d="M25.7,9.3l-7-7A.91.91,0,0,0,18,2H8A2,2,0,0,0,6,4V28a2,2,0,0,0,2,2H24a2,2,0,0,0,2-2V10A.91.91,0,0,0,25.7,9.3ZM18,4.4,23.6,10H18ZM24,28H8V4h8v6a2,2,0,0,0,2,2h6Z"/><polygon points="14 22.18 11.41 19.59 10 21 14 25 22 17 20.59 15.59 14 22.18"/><rect class="cls-1" width="32" height="32"/></svg>',
		'userRole': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" class="icon userrole"><defs><style>.cls-1{fill:none;}</style></defs><polygon points="28.07 21 22 15 28.07 9 29.5 10.41 24.86 15 29.5 19.59 28.07 21"/><path d="M22,30H20V25a5,5,0,0,0-5-5H9a5,5,0,0,0-5,5v5H2V25a7,7,0,0,1,7-7h6a7,7,0,0,1,7,7Z"/><path d="M12,4A5,5,0,1,1,7,9a5,5,0,0,1,5-5m0-2a7,7,0,1,0,7,7A7,7,0,0,0,12,2Z"/><rect id="_Transparent_Rectangle_" class="cls-1" width="32" height="32"/></svg>',
		'warn': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" class="icon warn"><defs><style>.cls-1{fill: none;}</style></defs><path d="M16,23a1.5,1.5,0,1,0,1.5,1.5A1.5,1.5,0,0,0,16,23Z"/> <rect x="15" y="12" width="2" height="9"/><path d="M29,30H3a1,1,0,0,1-.8872-1.4614l13-25a1,1,0,0,1,1.7744,0l13,25A1,1,0,0,1,29,30ZM4.6507,28H27.3493l.002-.0033L16.002,6.1714h-.004L4.6487,27.9967Z"/><rect class="cls-1" width="32" height="32"/></svg>'
	}
			
			
	return {
		'classes': {
			'button': commonButton,
			'smallButton': smallButton,
			'bluePriButton': 'bg-blue hover-bg-dark-blue white hover-white',
			'blueSecButton': 'bg-near-white hover-bg-dark-blue dark-blue hover-white',
			'blueTertiaryButton': 'bg-white hover-bg-dark-blue blue hover-white nounderline',
			'greenPriButton': 'bg-green hover-bg-dark-green white hover-white',
			'redPriButton': 'bg-red hover-bg-dark-red white hover-white',
			'redSecButton': 'bg-near-white hover-bg-red dark-red hover-white',
			'disabledButton': 'bg-black-10 black-40',
			'bulletlist': 'bl-bullet-list',
			'grid': horizontalSpace,
			'horizontalSpace': horizontalSpace,
			'hasIconFlexCenter': 'inline-flex items-center underline-hover',
			'imageBorder': 'ba b--black-20',
			'leftnavItem': 'custom-animate-all custom-leftnav-item db hover-bg-near-white pa2 pl3 relative underline-hover textcolor f6 fw5',
			'leftnavSubnavItem': 'custom-animate-all custom-leftnav-item db hover-bg-near-white pa2 pl4 relative underline-hover textcolor f6',
			'link': 'custom-animate-all link linkcolor',
			'menunavLink': 'custom-animate-all underline-hover custom-menunav-item db ph3 white hover-light-yellow',
			'menunavText': 'custom-menunav-item db ph3 white',
			'navItem': 'custom-animate-all underline-hover pa3 link f6 f5-ns db relative hover-dark-blue textcolor',
			'overlayContent': 'w-90 bg-white pa4 br2',
			'overlayClose': 'mt2 bl-modal-close pointer h2 ba br2 ph2 border-box b--blue blue bg-white hover-bg-dark-blue hover-white custom-animate-all',
			'pageTitleSecondary': 'fw4',
			'rounded': rounded,
			'spinner': 'bl-spinner ba br-100',
			'tab': tab,
			'tableListCell': 'pv3 pr3 bb b--black-20',
			'tableListCellSmall': 'pv2 pr2 bb b--black-20 f6',
			'tableListCell_bt': 'pv2 bt b--black-20',
			'tag': 'common-tag inline-flex items-center ba br2 custom-border-color hover-b--dark-blue hover-bg-dark-blue textcolor hover-white pv1 ph2 mr2 mb2 f6 lh-title bg-near-white',
			'textTag': f'dib f6 {rounded} pv1 ph2',
			'tooltipCue': 'bb b--black-20 b--dashed pointer normal bt-0 br-0 bl-0',
			'yellowMessage': 'ph2 bg-light-yellow bl-fadeout br2',
			'websiteHeading': 'f3 fw4 mb3',
		},
		'html': {
			'hr': '<div class="' + horizontalSpace + ' w-100 mv5"><div class="bb b--silver"></div></div>',
			'icons': icons,
			'tableWidget': {
				'sortOnly': 'data-widget="datatable" data-fixed-header="true" data-paging="false" data-searching="false" data-info="false" class="w-100 hover stripe collapse display" width="100%"',
				'fullFeatures': 'data-widget="datatable" data-fixed-header="true" data-length-change="false" data-page-length="100" class="w-100 hover stripe collapse display" width="100%" data-buttons=\'["excel"]\' data-dom="lBifrtip"',
			},
		}
	}



@register.filter
def alertTypeIcon(type):
	"""
	Takes alert type and returns span with icon to represent it.
	"""
	th = getTemplateHelpers({})
	html = ''
	
	if type == 'Great':
		html = '<span class="yellow hasiconNoTop">{}</span>'.format(th['html']['icons']['star'])
	elif type == 'Good':
		html = '<span class="green hasiconNoTop">{}</span>'.format(th['html']['icons']['checkmark'])
	elif type == 'Warning':
		html = '<span class="orange hasiconNoTop">{}</span>'.format(th['html']['icons']['warn'])
	elif type == 'Bad':
		html = '<span class="red hasiconNoTop">{}</span>'.format(th['html']['icons']['sad'])
	elif type == 'Poop':
		html = '<span class="brown hasiconNoTop">{}</span>'.format(th['html']['icons']['poop'])
	elif type == 'Info':
		html = '<span class="blue hasiconNoTop">{}</span>'.format(th['html']['icons']['info'])

	return html

