import random
import pandas as pd

from datetime import datetime
from faker import Faker

from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.crypto import get_random_string

from metrics.models import getImportScriptUser, Project
from research.models import Artifact, Source, Status, Method, Tag

fake = Faker()


employeeNames = ['Alex Turner','Emily Parker','David Brooks','Jessica Morgan','Michael Cooper','Sarah Mitchell','Kevin Turner','Jennifer Hayes','Jason Phillips','Olivia Evans','Andrew Foster','Michelle Campbell','Daniel Murphy','Rachel Reed','Matthew Bennett','Sophia Price','Ethan Powell','Isabella Hughes','William Simmons','Mia Russell','James Patterson','Ava Henderson','Benjamin Foster','Abigail Cox','Logan Sanders','Elizabeth Kelly','Daniel Carter']


def getCreateUser(name):
	email = (name.replace(' ','.') + '@somedomain.com').lower()
	
	user, created = User.objects.get_or_create(
		username = email,
		defaults = {
			'email': email,
			'password': get_random_string()
		}
	)
	if created:
		user.profile.full_name = name
		user.save()
		
	return user
	
	
def chooseRandomDate(startDate='-1y', endDate='now'):
	return timezone.make_aware(fake.date_time_between(startDate, endDate), is_dst=True)


def chooseRandomEmployee():
	return getCreateUser(random.choice(employeeNames))
	
	
def chooseRandomProject():
	return random.choice(Project.objects.all())


def createSources():
	sources = ['My company', '3rd party']
	
	for source in sources:
		Source.objects.create(
			name = source,
			created_by = getImportScriptUser(),
			updated_by = getImportScriptUser()
		)


def getCreateTag(word):
	tagName = word.strip().replace('-',' ').title()
	
	# Group related ones
	if 'Accessibility' in tagName or 'Aria' in tagName:
		tagName = 'Accessibility'
	
	if 'Color' in tagName:
		tagName = 'Color'
		
	if 'Design' in tagName:
		tagName = 'Design'
	
	if 'Content' in tagName or 'Dark' in tagName:
		tagName = 'Content'
		
	if 'commerce' in tagName:
		tagName = 'Commerce'
		
	if 'Emotion' in tagName:
		tagName = 'Emotion'
		
	if 'Eye ' in tagName:
		tagName = 'Eye tracking'
		
	if 'Gesture ' in tagName:
		tagName = 'Gestures'
	
	if 'Inclusive ' in tagName:
		tagName = 'Inclusive'
		
	if 'Mobile ' in tagName:
		tagName = 'Mobile'
	
	if 'Navigation ' in tagName:
		tagName = 'Navigation'
		
	if 'Performance ' in tagName:
		tagName = 'Performance'
		
	if 'Usability ' in tagName:
		tagName = 'Usability'
		
	if 'Virtual R' in tagName:
		tagName = 'Virtual reality'
		
	if 'Visual ' in tagName:
		tagName = 'Design'
		
		
	tag, created = Tag.objects.get_or_create(
		name = tagName,
		defaults = {
			'created_by': getImportScriptUser(),
			'updated_by': getImportScriptUser()
		}
	)
	return tag


def createMethods():
	methods = ['A/B test', 'Focus group', 'Interview', 'Observation', 'Case study', 'Experiment']
	
	for method in methods:
		Method.objects.create(
			name = method,
			created_by = getImportScriptUser(),
			updated_by = getImportScriptUser()
		)
		
	
def createStatuses():
	Status.objects.create(
		name = 'Planned',
		color_class = '#002d9c',
		created_by = getImportScriptUser(),
		updated_by = getImportScriptUser()
	)
	Status.objects.create(
		name = 'In progress',
		color_class = '#ff832b',
		created_by = getImportScriptUser(),
		updated_by = getImportScriptUser()
	)
	Status.objects.create(
		name = 'Completed',
		color_class = '#0e6027',
		created_by = getImportScriptUser(),
		updated_by = getImportScriptUser()
	)
	
	
def createResearchArtifacts(deleteAll=True):
	"""
	Import research items from CSV
	"""
	if deleteAll:
		Artifact.objects.all().delete()
		Source.objects.all().delete()
		Status.objects.all().delete()
		Method.objects.all().delete()
		Tag.objects.all().delete()
		
	createStatuses()	
	createSources()
	createMethods()
	
	df = pd.read_csv('./sample_data/sample_research.csv')
	
	print('>> Creating sample research artifacts and associated meta data.')
	
	for i, csvRow in df.iterrows():
		try:
			artifact = Artifact.objects.create(
				owner = chooseRandomEmployee(),
				name = csvRow[0],
				abstract = csvRow[1],
				description = fake.paragraph(nb_sentences=20),
				status = random.choice(Status.objects.all()),
				research_date = chooseRandomDate(),
				source = random.choice(Source.objects.all()),
				created_by = getImportScriptUser(),
				updated_by = getImportScriptUser(),
				external_research_urls = [fake.image_url()],
			)
			artifact.methods.add(random.choice(Method.objects.all()))
			
			for word in csvRow[2].split(','):
				artifact.tags.add(getCreateTag(word))
			
			projectCountArr = [0,0,0,0,0,0,0,0,1,2]
			projectCount = random.choice(projectCountArr)
			
			for i in range(0, projectCount+1):
				artifact.projects.add(random.choice(Project.objects.all()))
		
		except Exception as ex:
			print(f'Problem processing CSV row # {i}: {ex}')
	
