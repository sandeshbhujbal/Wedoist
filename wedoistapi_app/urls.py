from django.conf.urls import url

from . import views
urlpatterns = [
	url(r'^$', views.index, name='index'),
	url(r'^get_lists$', views.get_lists, name='get_lists'),
	url(r'^get_tasks$', views.get_tasks, name='get_tasks'),
	url(r'^submit_task$', views.submit_task, name='submit_task'),
]

