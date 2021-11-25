# For Openshift and Cirrus, see: https://docs.openshift.com/container-platform/3.4/using_images/s2i_images/python.html
# For gunicorn: see:

# This is configured for a cluster that is intended to only serve the site without background jobs running

# these two settings are incompatible with each other
# either 1 is true and the other false or both are false
import os

preload_app = True
reload = False
timeout = int(os.environ.get("GUNICORN_TIMEOUT", 120))
graceful_timeout = int(os.environ.get("GUNICORN_GRACEFUL_TIMEOUT", 120))

# example settings
# bind = "0.0.0.0:8080"
# loglevel = "DEBUG"
# workers = 8

try:
	from gunicorn_conf_local import *
except ImportError:
	print("No local gunicorn config")
