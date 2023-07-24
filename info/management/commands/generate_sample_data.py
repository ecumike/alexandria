from django.core.management.base import BaseCommand, CommandError

from sample_data.sample_research_lib import createResearchArtifacts
from sample_data.sample_metrics_lib import createProjects


class Command(BaseCommand):
	help = "Deletes all data and creates sample projects, survey responses, metrics, and research artifacts."

	def handle(self, *args, **options):
		createProjects(deleteAll=True)
		createResearchArtifacts(deleteAll=True)
		self.stdout.write(
			self.style.SUCCESS('Successfully created all sample data.')
		)