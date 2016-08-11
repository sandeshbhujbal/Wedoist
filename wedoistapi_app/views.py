from django.shortcuts import render

from datetime import datetime
import dateutil.parser
import pytz
import json

from django.http import HttpResponse
from django.template import loader, RequestContext

from wedoistapi_project.settings import PROJECT_ROOT
#from django.http import JsonResponse
from wedoistapi import Wedoist, WedoistHTTPAuth

auth_object = None
MEMBERS_ACTIVE_DAYS = 365

def index(request):
	params = {}

	if request.method == "POST":
		login_status = "Success"
		email_address = request.POST.get('email_address')
		password = request.POST.get('password')
		login_status = authenticate_to_api(email_address, password)
		if login_status == "Success":
			template = loader.get_template("show_projects.html")
			available_projects = [{"project_id":1,"project_name":"Project1"},{"project_id":2,"project_name":"Project2"},{"project_id":3,"project_name":"Project3"}]
			available_projects = get_available_projects()
			params["project_list"] = available_projects
			context = RequestContext(request, params)
			return HttpResponse(template.render(context))
		else:
			template = loader.get_template("login.html")
			params["error_message"] = "sfdsdf"
			context = RequestContext(request, params)
			return HttpResponse(template.render(context))


	template = loader.get_template('login.html')
        context = RequestContext(request, params)
	return HttpResponse(template.render(context))

def authenticate_to_api(email_address, password):
	"""
	Function to authenticate to WedoistAPI api using the credentials provided by user.
	After authenticating a global auth object will be set which will be used through out the program
	"""
	global auth_object
	print "Authenticating to api..."
	try:
		auth = WedoistHTTPAuth(email=email_address, password=password)
		wedoist = Wedoist(auth)
		auth_object = wedoist
		return "Success"
	except Exception as e:
		print str(e)
		return "Failed"

def get_lists(request):
	params = {}

	if request.method == "POST":
		project_id = request.POST.get('project_id')
		project_name = request.POST.get('project_name')
		params["project_id"] = 	project_id
		params["project_name"] = project_name

		lists = {"1":"list1","2":"list2"}	
		lists = get_lists_in_project(project_id)

		params["lists"] = lists

		template = loader.get_template('show_lists.html')
		context = RequestContext(request, params)
		return HttpResponse(template.render(context))

def submit_task(request):
	params = {}
	data = {}
	todo = request.POST.get("Task")	
	members_list = request.POST.getlist("members_list")
	project_id = request.POST.get('project_id')
	project_name = request.POST.get('project_name')
	list_id = request.POST.get('list_id')
	list_name = request.POST.get('list_name')
	new_task_name = request.POST.get('new_task_name')
	exesting_task = request.POST.get('exesting_task')

	if todo == "add_task":
		print "Adding new task....."
		status = add_task(list_id, new_task_name, members_list)
		if status == "success":
			data["status"] = "success"
			data["msg"] = "Task added successfully."
		else:
			data["errors"] = "Error occured while adding task."
	else:
		print "updating the task...."

		status = update_task(exesting_task, new_task_name, members_list)
		if status == "success":
			data["status"] = "success"
			data["msg"] = "Task updated successfully."
		else:
			data["errors"] = "Error occured while updating task."

	tasks_data = {"1":"task1","2":"task2","3":"task3","4":"task4"}
	tasks_data = get_tasks_from_api(list_id)
	data["tasks"] = tasks_data
	return HttpResponse(json.dumps(data), content_type="application/json")

def get_tasks(request):
	params = {}
	if request.method == "POST":
		params["project_id"] = request.POST.get("project_id")
		params["project_name"] = request.POST.get("project_name")
		params["list_id"] = request.POST.get("list_id")
		params["list_name"] = request.POST.get("list_name")

		tasks_data = {"1":"task1","2":"task2","3":"task3"}
		members = {"1":"member1","2":"member2"}

		tasks_data = get_tasks_from_api(params["list_id"])
		members = get_project_members(params["project_id"])
		params["tasks"] = tasks_data
		params["members"] = members

		template = loader.get_template('tasks_page.html')
		context = RequestContext(request, params)
		return HttpResponse(template.render(context))


def get_all_members():
	global auth_object
	#find all the members information available in the given account.
	print "Getting all members information...."
	all_members = auth_object.Dashboard.getAllPeople()
	members_list = []
	#create a list of members which will hold the full name of member.
	for key, value in all_members.iteritems():
		temp = {}
		temp["member_id"]=value['full_name']
		temp["member_name"]=value['full_name']
		members_list.append(temp)
	return members_list

def get_project_members(project_id):
	global auth_object
	print "Getting members information for project....."
	all_members = auth_object.Projects.getUsers(project_id=project_id)
	members_list = []
	temp = {}
        for member in all_members:
		last_login_date = member["last_login"]
		if check_member_status(last_login_date):
			temp[member['full_name']]=member['full_name']
        return temp


def check_member_status(last_login_date):
	global MEMBERS_ACTIVE_DAYS
	if last_login_date == None:
		return False
	last_login_date = dateutil.parser.parse(last_login_date)
	current_date = datetime.now(pytz.utc)
	date_difference = current_date - last_login_date
	if date_difference.days > MEMBERS_ACTIVE_DAYS:
		return False
	return True


def add_task(list_id, content, member_name):
	global auth_object
	#Add a new task in the given list
	#and assign it to the selected member in member_name list
	#if add task with the format "@<member_name> task" it will automatically create the task and assign it to member_name
	"""
	if member_name == "-1":
		auth_object.Items.add(content=content,list_id=list_id)
	else:
		auth_object.Items.add(content="@"+member_name+" "+content,list_id=list_id)
	"""
	if not member_name:
		print "no members selected"
		print content
		auth_object.Items.add(content=content,list_id=list_id)
	else:
		members_string = ""
		for member in member_name:
			members_string = members_string + "@"+member+" "
		content = members_string+content
		print content
		auth_object.Items.add(content=content,list_id=list_id)
	
	return "success"


def update_task(task_id, content, member_name):
	global auth_object
	#Update the given task and assign it to the members in member_name list
	#to assign the task to a particular member just add @<member name> before the task name
	#auth_object.Items.update(item_id=task_id,content="@"+member_name+" "+content)
	print "inside update task....."
	print task_id, content, member_name

	if not member_name:
		print "No members selected"
		print content
		auth_object.Items.update(item_id=task_id,content=content)
	else:
		members_string = ""
		for member in member_name:
			if "@"+member not in content:
				members_string = members_string + "@"+member+" "

		content = members_string+content
		print content
		auth_object.Items.update(item_id=task_id,content=content)
		
	return "success"

	"""
	if member_name == "-1":
		auth_object.Items.update(item_id=task_id,content=content)
	elif "@"+member_name not in content:
		auth_object.Items.update(item_id=task_id,content="@"+member_name+" "+content)
	else:
		auth_object.Items.update(item_id=task_id,content=content)
	"""

def get_tasks_from_api(list_id):
	global auth_object
	print "Getting all tasks for the list....."
	tasks_list = auth_object.Items.getActive(list_id=list_id)
	temp = {}
	#Get the list of tasks for the selected list_id
	for task in tasks_list:
		#task name will contain the aleready assigned members name also
		temp[task["id"]] = task["content"]
	return temp


def get_available_projects():
	"""
	Find the all available projects from the given account using the global auth object.
	"""
	global auth_object
	print "Getting list of projects available..."
	all_projects = auth_object.Projects.getAll(only_active="true")
	projects_dict = []
	#Create a list of dictionaries which will store the project id and its name.
	for project in all_projects:
		temp = {}
		temp["project_id"]=project["id"]
		temp["project_name"] = project["name"]
		projects_dict.append(temp)
	return projects_dict

def get_lists_in_project(project_id):
	global auth_object
	#Find all the lists available in the project.
	print "Getting the lists available in the project..."
	print auth_object
	all_lists = auth_object.Lists.getAll(project_id=str(project_id))
	temp = {}
	#Create a dictionary with the list id and its name.
	for list1 in all_lists:
		temp[list1["id"]] = list1["name"]
	return temp

