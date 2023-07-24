import random
import pandas as pd

from datetime import datetime
from faker import Faker

from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.crypto import get_random_string

from research.models import Artifact
from metrics.models import getImportScriptUser, Campaign, Project, VoteResponse, GoalCompleted, DataSource, UmuxScoreCategory, NpsScoreCategory, NpsLetterGrade, Target, Domain


fake = Faker()


appNames = ['AIAnalyzer','AIAssistant','AIAutomate','AnalyticX','AnalyzeIt','AppBoost','AppGenius','AppLoader','AppMonitor','AudioEditorX','AudioEditX','AutoBackup','AutoFormat','BackupWizard','BatchProcessor','BugBuster','BugTrackerX','Chartify','ChartMaster','CloudBackup','CloudStorage','CodeExplorer','CodeGenius','CodeOptimizer','CodeReviewer','CodeScribe','CodeValidator','ColorMatcher','ColorPalette','ColorPickerX','ContentAnalyzer','DashboardX','DataCleaner','DataGatherer','DataVisualizer','DataVizify','DebugWizard','DesignPro','ErrorFinder','ErrorLogger','FileEncryptor','FileExplorer','FileOrganizer','FileScanner','FileSyncer','FontAnalyzer','FontFinder','FontManager','IconBuilder','IconCreator','ImageEditorX','ImageFilterX','ImageResize','LayoutBuilder','LayoutOptimizer','LayoutTweaker','LogicAnalyzer','MediaHub','MediaManager','NoteMaker','NoteTakerX','PixelArtX','PixelCraft','PixelMapper','PixelTune','PrintMaster','ScanGuard','SecurityShield','SEOOptimizer','SketchIt','SpeedOptimizer','SpeedTestX','SpeedTweak','TaskMaster','TaskPlanner','TimeTracker','UIEnhancer','UIInspector','UIWizard','VideoEditPro','VideoEditX','VideoMakerX','WebCrawler','WebInspector']

# Uncomment for a shorter run.
#appNames = ['AIAnalyzer','AIAssistant','AIAutomate','AnalyticX','AnalyzeIt','AppBoost','AppGenius','AppLoader','AppMonitor','AudioEditorX','AudioEditX','AutoBackup','AutoFormat','BackupWizard','BatchProcessor','BugBuster','BugTrackerX','Chartify']

appOwnerNames = ['Alex Johnson','Emily Martinez','David Smith','Jessica Brown','Michael Wang','Sarah Lee','Kevin Garcia','Jennifer Lopez','Jason Miller','Olivia Chen','Andrew Kim','Michelle Wilson','Daniel Nguyen','Rachel Patel','Matthew Davis','Sophia Rodriguez','Ethan Taylor','Isabella Hernandez','William Lee','Mia Thomas','James Sanchez','Ava Anderson','Benjamin Martinez','Abigail Johnson','Logan Lee','Elizabeth Jackson','Daniel Lee','Emily Miller','Christopher Wang','Ella Roberts','Alexander Brown','Grace Wilson','Samuel Thompson','Scarlett Nguyen','Aiden Davis','Victoria Kim','Joseph Smith','Sofia Gonzalez']


employeeNames = ['Alex Turner','Emily Parker','David Brooks','Jessica Morgan','Michael Cooper','Sarah Mitchell','Kevin Turner','Jennifer Hayes','Jason Phillips','Olivia Evans','Andrew Foster','Michelle Campbell','Daniel Murphy','Rachel Reed','Matthew Bennett','Sophia Price','Ethan Powell','Isabella Hughes','William Simmons','Mia Russell','James Patterson','Ava Henderson','Benjamin Foster','Abigail Cox','Logan Sanders','Elizabeth Kelly','Daniel Carter']


feedbacks = ["The application's user interface is sleek and modern, making it easy to navigate.","I love how quickly the app loads and responds to my commands.","The range of features offered is impressive, covering all my needs.","Customer support is outstanding, resolving my issues promptly.","The recent updates have brought valuable improvements to the app.","The app's performance is consistent, even during peak usage times.","I appreciate the app's intuitive design, making it easy to use for beginners.","The data synchronization feature is seamless and efficient.","The application's security measures inspire confidence in data protection.","The app's offline capabilities have been a lifesaver in areas with poor internet connection.","The app's user interface is cluttered and confusing, making it difficult to find features.","I've experienced frequent crashes, especially when performing certain actions.","Several essential features seem to be missing from the application.","The customer support team is unresponsive, delaying issue resolution.","The recent updates have introduced bugs and made the app less stable.","The app's performance is slow and laggy, hindering the user experience.","I find the app's design outdated and not visually appealing.","The data synchronization process is unreliable, leading to data loss.","The application lacks proper security measures, making me concerned about data privacy.","The app often freezes, forcing me to restart it multiple times.","I've encountered numerous error messages that disrupt my workflow.","The application's user interface is intuitive and user-friendly.","The app's loading times are lightning-fast, providing a smooth experience.","The wide range of features is impressive, catering to various needs.","Customer support is responsive and helpful, resolving my issues quickly.","The latest updates have improved the app's performance and stability.","The app operates seamlessly even during peak usage periods.","The simple and elegant design makes the app a joy to use.","The data synchronization works flawlessly, ensuring my data is always up-to-date.","The app's security features put my mind at ease about data protection.","Offline mode is highly reliable, allowing me to use the app without internet access.","The app's user interface is confusing and requires improvement.","The app's loading times are frustratingly slow, leading to delays.","Essential features are missing, making the app less functional.","Customer support is unresponsive and lacks proper solutions.","The latest updates have introduced more issues and instability.","The app often lags and freezes, disrupting the user experience.","The app's design is outdated and not visually appealing.","The data synchronization is prone to errors, causing data discrepancies.","The app's security measures raise concerns about data privacy.","Offline mode is unreliable and frequently fails to work as intended.","The app's user interface is user-friendly and intuitive.","The app's loading times are fast, providing a seamless experience.","The app offers a wide range of features to meet diverse needs.","Customer support is responsive and efficiently resolves issues.","The recent updates have enhanced the app's performance and stability.","The app operates smoothly, even during peak usage periods.","The app's design is clean and visually pleasing.","The data synchronization is reliable, keeping my data up-to-date.","The app's security measures ensure data protection and privacy.","Offline mode works flawlessly, enabling smooth usage without internet access.","The app's user interface is cluttered and hard to navigate.","The app's loading times are frustratingly slow, causing delays.","The app lacks essential features, limiting its functionality.","Customer support is unresponsive and fails to resolve issues effectively.","The recent updates have introduced more bugs and instability.","The app frequently lags and freezes, disrupting the user experience.","The app's design is outdated and not visually appealing.","The data synchronization often fails, leading to data inconsistencies.","The app's security measures raise concerns about data privacy.","Offline mode is unreliable and frequently fails to work as intended.","The app's user interface is user-friendly and intuitive.","The app's loading times are fast, providing a seamless experience.","The app offers a wide range of features to meet diverse needs.","Customer support is responsive and efficiently resolves issues.","The recent updates have enhanced the app's performance and stability.","The app operates smoothly, even during peak usage periods.","The app's design is clean and visually pleasing.","The data synchronization is reliable, keeping my data up-to-date.","The app's security measures ensure data protection and privacy.","Offline mode works flawlessly, enabling smooth usage without internet access.","The app's user interface is cluttered and hard to navigate.","The app's loading times are frustratingly slow, causing delays.","The app lacks essential features, limiting its functionality.","Customer support is unresponsive and fails to resolve issues effectively.","The recent updates have introduced more bugs and instability.","The app frequently lags and freezes, disrupting the user experience.","The app's design is outdated and not visually appealing.","The data synchronization often fails, leading to data inconsistencies.","The app's security measures raise concerns about data privacy.","Offline mode is unreliable and frequently fails to work as intended.","The app's user interface is user-friendly and intuitive.","The app's loading times are fast, providing a seamless experience.","The app offers a wide range of features to meet diverse needs.","Customer support is responsive and efficiently resolves issues.","The recent updates have enhanced the app's performance and stability.","The app operates smoothly, even during peak usage periods.","The app's design is clean and visually pleasing.","The data synchronization is reliable, keeping my data up-to-date.","The app's security measures ensure data protection and privacy.","Offline mode works flawlessly, enabling smooth usage without internet access."]


def getCreateUser():
	name = random.choice(appOwnerNames)
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
	return random.choice(employeeNames)
	
	
def chooseRandomApp():
	return random.choice(appNames)


def chooseRandomUmuxPair():
	return (
		min(int(str(datetime.now().microsecond)[0]), 5) + min(int(str(datetime.now().microsecond)[0]), 2),
		min(int(str(datetime.now().microsecond)[0]), 5) + min(int(str(datetime.now().microsecond)[0]), 2)
	)


def chooseGoalCompleted():
	return GoalCompleted.objects.get_or_create(name = random.choice(['no', 'yes', 'partial']))[0]
	
	
def chooseRandomNps():
	return min(int(str(datetime.now().microsecond)[0]), 8) + min(int(str(datetime.now().microsecond)[0]), 2)
	

def addResearchArtifacts():
	"""
	Import research items from CSV
	"""
	df = pd.read_csv('./sample_data/sample_research.csv')
	
	for i, csvRow in df.iterrows():
		try:
			# Get/Create employee.
			# Create new artifact
			pass
		except Exception as ex:
			print(f'Problem processing CSV row # {i}: {ex}')
	

def createUmuxCategories():
	UmuxScoreCategory.objects.create(
		name = 'F',
		min_score_range = 0,
		max_score_range = '59.99',
		color_code = '#a2191f',
		text_color_code = '#fff',
		created_by = getImportScriptUser(),
		updated_by = getImportScriptUser()
	)
	UmuxScoreCategory.objects.create(
		name = 'D',
		min_score_range = 60,
		max_score_range = '69.99',
		color_code = '#ff832b',
		text_color_code = '#000',
		created_by = getImportScriptUser(),
		updated_by = getImportScriptUser()
	)
	UmuxScoreCategory.objects.create(
		name = 'C',
		min_score_range = 70,
		max_score_range = '79.99',
		color_code = '#ffb700',
		text_color_code = '#000',
		created_by = getImportScriptUser(),
		updated_by = getImportScriptUser()
	)
	UmuxScoreCategory.objects.create(
		name = 'B',
		min_score_range = 80,
		max_score_range = '89.99',
		color_code = '#198038',
		text_color_code = '#fff',
		created_by = getImportScriptUser(),
		updated_by = getImportScriptUser()
	)
	UmuxScoreCategory.objects.create(
		name = 'A',
		min_score_range = 90,
		max_score_range = 100,
		color_code = '#0e6027',
		text_color_code = '#fff',
		created_by = getImportScriptUser(),
		updated_by = getImportScriptUser()
	)
	
def createNpsScoreCategories():
	NpsScoreCategory.objects.create(
		name = 'Excellent',
		min_score_range = 40.1,
		max_score_range = 100,
		color_code = '#0e6027',
		text_color_code = '#fff',
		ux_points = 4,
		created_by = getImportScriptUser(),
		updated_by = getImportScriptUser()
	)
	NpsScoreCategory.objects.create(
		name = 'Very good',
		min_score_range = 25.1,
		max_score_range = 40,
		color_code = '#198038',
		text_color_code = '#fff',
		ux_points = 3,
		created_by = getImportScriptUser(),
		updated_by = getImportScriptUser()
	)
	NpsScoreCategory.objects.create(
		name = 'Good',
		min_score_range = 8.1,
		max_score_range = 25,
		color_code = '#ffb700',
		text_color_code = '#000',
		ux_points = 2,
		created_by = getImportScriptUser(),
		updated_by = getImportScriptUser()
	)
	NpsScoreCategory.objects.create(
		name = 'Average',
		min_score_range = -26.9,
		max_score_range = 8,
		color_code = '#ff832b',
		text_color_code = '#000',
		ux_points = 1,
		created_by = getImportScriptUser(),
		updated_by = getImportScriptUser()
	)
	NpsScoreCategory.objects.create(
		name = 'Poor',
		min_score_range = -100,
		max_score_range = -27,
		color_code = '#a2191f',
		text_color_code = '#fff',
		ux_points = 0,
		created_by = getImportScriptUser(),
		updated_by = getImportScriptUser()
	)


def createNpsLetterGrades():
	grades = [
		['A', 41, '#0e6027'],
		['B', 26, '#198038'],
		['C', 9, '#ffb700'],
		['D', -26, '#ff832b'],
		['F', -100, '#a2191f'],
	]
	for grade in grades:
		
		NpsLetterGrade.objects.create(
			name = grade[0],
			min_score = grade[1],
			color_code = grade[2],
			created_by = getImportScriptUser(),
			updated_by = getImportScriptUser()
		)
	
	
def createDataSources():
	dataSource = DataSource.objects.get_or_create(
		name='Usabilla',
		created_by = getImportScriptUser(),
		updated_by = getImportScriptUser()
	)
	dataSource = DataSource.objects.get_or_create(
		name='Other',
		created_by = getImportScriptUser(),
		updated_by = getImportScriptUser()
	)


def createTargets():
	bump = 9
	for target in range(-100,101):
		try:
			if target % bump == 0:
				bump = bump - 1
		except Exception as ex:
			pass
			
		Target.objects.create(
			nps_score = target,
			#umux_score = models.FloatField(null=True, blank=True)
			achieve_target = target + (bump/2),
			exceed_target = target + bump,
		)
	
	
def createDomains():
	domains = ['CFO', 'Design', 'HR']
	for domain in domains:
		Domain.objects.create(
			name = domain,
			created_by = getImportScriptUser(),
			updated_by = getImportScriptUser(),	
		)
		
	
def createProjects(deleteAll=True):
	"""
	Generate fake projects, with owners, scores, and feedback.
	"""
	if deleteAll:
		Domain.objects.all().delete()
		DataSource.objects.all().delete()
		Target.objects.all().delete()
		NpsScoreCategory.objects.all().delete()
		NpsLetterGrade.objects.all().delete()
		UmuxScoreCategory.objects.all().delete()
		VoteResponse.objects.all().delete()
		Campaign.objects.all().delete()
		Project.objects.all().delete()
		
	# Create supporting score objects.
	createDomains()
	createDataSources()
	createNpsLetterGrades()
	createNpsScoreCategories()
	createUmuxCategories()
	createTargets()
	
	# Create projects and add responses, then calculate snapshots.
	print('>> Creating projects with responses and metrics.')
	
	for i, appName in enumerate(appNames, 1):
		project = Project.objects.create(
			name = appName,
			domain = random.choice(Domain.objects.all()),
			contact = getCreateUser(),
			priority = random.randrange(1,6),
			created_by = getImportScriptUser(),
			updated_by = getImportScriptUser(),
		)
		
		campaign = Campaign.objects.create(
			project = project,
			uid = get_random_string(),
			created_by = getImportScriptUser(),
			updated_by = getImportScriptUser(),
		)
		
		# Choose random #, create that many responses with random date, feedback, scores.
		numResponses = random.randrange(300, 2000)
		
		appCount = len(appNames)
		print(f'{i} of {appCount} : Creating {numResponses} responses for {project}')
		
		for n in range(1, random.randrange(400, 4000)):
			umuxPair = chooseRandomUmuxPair()
			VoteResponse.objects.create(
				campaign = campaign,
				uid = get_random_string(),
				date = chooseRandomDate(),
				nps = chooseRandomNps(),
				umux_capability = umuxPair[0],
				umux_ease_of_use = umuxPair[1],
				goal_completed = chooseGoalCompleted(),
				improvement_suggestion = random.choice(feedbacks),
				raw_data = {'someKey':'somevalue'}
			)
			
		project.updateAllSnapshots()
		project.storeLatestSnapshots()
		project.setYearBaselinesAndTargets()
		project.updateAllSnapshots()
	
	print('>> Calculating domain metrics.')
	
	for domain in Domain.objects.all():
		domain.updateDomainYearSnapshot()
	