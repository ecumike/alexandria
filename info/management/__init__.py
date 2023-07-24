from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor

# On demand, reusable scheduler.
class _DeferredScheduler:
	def __init__(self):
		self._scheduler = None

	# Create background scheduler that runs up to 30 concurrent jobs.
	# Scheduler will reuse open threads, so never have more than # open at once.
	def scheduler(self):
		try:
			self._scheduler.shutdown()
		except:
			pass
		self._scheduler = BackgroundScheduler(executors={'default':ThreadPoolExecutor(60)})
		self._scheduler.start()
		return self._scheduler

_ondemand_scheduler_common = _DeferredScheduler()
	
# Call this to start and return the class's scheduler which you do .add_job() to.
def commonScheduler():
	return _ondemand_scheduler_common.scheduler()

