#wsgi.py
import os, sys
from django.core.wsgi import get_wsgi_application
# Calculate the path based on the location of the WSGI script.
#apache_configuration= os.path.dirname(__file__)
apache_configuration=os.path.dirname(os.path.realpath(__file__))
#apache_configuration= os.getcwd()
project = os.path.dirname(apache_configuration)
workspace = os.path.dirname(project)
sys.path.append(workspace)
sys.path.append(project)

# Add the path to 3rd party django application and to django itself.
sys.path.append('/home/ubuntu')
os.environ['DJANGO_SETTINGS_MODULE'] = 'wedoistapi_project.apache.override'
import django.core.handlers.wsgi
#application = django.core.handlers.wsgi.WSGIHandler()
print sys.path
application = get_wsgi_application()
