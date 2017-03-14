################################################################
###
###  IMPORTS
###
################################################################

# these are standard python libraries
import os
import urllib
import datetime
import re
import pickle

# these are standard GAE imports
from google.appengine.api import users
from google.appengine.ext import ndb

# these are app.yaml imports
import webapp2
import jinja2

# these are my custom modules
# [example]: from [directory] import [some py file without extension]

# setup jinja environment - we are using jinja for processing templates
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

################################################################
###
###  BEGIN: DATASTORE entities
###
################################################################

# naming convention here is that:
# "ds" just means this is a "datastore" object
# "mr" means this is a "metric reserve" related entity

# this is the user Model.  Not to be confused with the account model
class ds_mr_user(ndb.Model):

	user_id = ndb.StringProperty()
	username = ndb.StringProperty()
	email = ndb.StringProperty()
	
	user_status = ndb.StringProperty()
	
	name_first = ndb.StringProperty()
	name_middle = ndb.StringProperty()
	name_last = ndb.StringProperty()
	name_suffix = ndb.StringProperty()
	
	metric_network_ids = ndb.PickleProperty(default="EMPTY")
	metric_account_ids = ndb.PickleProperty(default="EMPTY")
	
	date_created = ndb.DateTimeProperty(auto_now_add=True)

# this is just an entity solely used to enforce name uniqueness in other objects via transactions
# google's datastore requires a little extra work to enforce a unique constraint
class ds_mr_unique_dummy_entity(ndb.Model):

	unique_name = ndb.StringProperty()
	date_created = ndb.DateTimeProperty(auto_now_add=True)

# network profile: this entity contains information about specific graph
class ds_mr_network_profile(ndb.Model):

	network_name = ndb.StringProperty()
	network_id = ndb.StringProperty()
	network_status = ndb.StringProperty()
	active_user_count = ndb.IntegerProperty()
	orphan_count = ndb.IntegerProperty()
	total_trees = ndb.IntegerProperty()
	last_graph_process = ndb.DateTimeProperty()
	
# network cursor: this entity maintains the index of network accounts
class ds_mr_network_cursor(ndb.Model):

	network_id = ndb.StringProperty()
	current_index = ndb.IntegerProperty()

# metric account: this is the main account information
class ds_mr_metric_account(ndb.Model):

	account_id = ndb.StringProperty()
	network_id = ndb.StringProperty()
	outgoing_connection_requests = ndb.PickleProperty()
	incoming_connection_requests = ndb.PickleProperty()
	incoming_reserve_transfer_requests = ndb.PickleProperty()
	outgoing_reserve_transfer_requests = ndb.PickleProperty()
	suggested_reserve_transfer_requests = ndb.PickleProperty()
	current_connections = ndb.PickleProperty()
	current_reserve_balance = ndb.StringProperty()
	current_network_balance = ndb.StringProperty()	
	last_connections = ndb.PickleProperty()
	last_reserve_balance = ndb.StringProperty()
	last_network_balance = ndb.StringProperty()

################################################################
###
###  END: DATASTORE entities
###
################################################################

################################################################
###
###  BEGIN: Application Classes
###
################################################################

# capitalized variables generally refer to class variables

# master class object holds all the application and request variables
class master(object):

	# intialization function, called when object is instantiated with or without a function call
	def __init__(self, fobj_request,fstr_request_type,fstr_security_req):
		
		# fobj_request - this is the WSGI object passed in from page handlers
		# fstr_request_type - "get", "post", etc.
		# fstr_security_req - tells what security level the page has
		
		# attach request object to master object
		self.request = fobj_request.request
		self.response = fobj_request.response
		# also, let's get the webapp.RequestHandler reference itself for redirects and errors
		self.request_handler = fobj_request
		
		# store IS_POST variable. not necessary, useful for readability
		if fstr_request_type == 'post':
			self.IS_POST = True		
		else:		
			self.IS_POST = False
		
		# This is used for page debugging, placing helper debug references in page code.
		# Different from the WSGI "debug_mode" which tells app to spit out the call stack.
		self.IS_DEBUG = True
		# For my own "stack" tracing I just append to a delimited list for later output.
		self.TRACE = []
		
		# Start with what time it is:
		self.TRACE.append("current time:%s" % str(datetime.datetime.now()))
		# instantiate a user via class - see 'class user(object)'
		self.user = user(self)
		
		# instantiate the metric object
		self.metric = metric(self)
		
		# sometimes our security or other app checks (like system being offline) 
		# interrupt normal page processing and return other information like errors
		# to the browser. So each page handler class will break out before processing
		# if this variable becomes true.
		self.IS_INTERRUPTED = False
		
		# Security:
		# 
		# Using a very simple security pattern. If they are trying to access any page
		# other than an unsecured page send them to login page and redirect back to 
		# target page after login. 
		#
		# Now we are using Google login so a user can log in without actually registering
		# with the application. So the next check has to see if they have registered
		# with these google credentials. When the user object is initially created in the
		# user class, it sets the user "status" to "VERIFIED", meaning the credentials
		# worked and are verified but user is not yet active. If this is the case we 
		# force them to the registration page to complete the sign up.
		#
		# When we have verified that they are logged in and registered we return them to
		# the page and do any additional special checks (like extra checks for admins 
		# where we send them to error page if they aren't admin users). Any pages set as
		# "unsecured" should fall through all this logic.
		
		# Note that there's no check for 'secured' because it's generic and accounted for
		# in the first 'if' check. 'unsecured' also requires no checks.
		if not fstr_security_req == 'unsecured' and self.user.IS_LOGGED_IN == False:
			
			# This page requires login and they are not.
			# Send back to this page after login.
			self.request_handler.redirect(users.create_login_url(self.request.path))
		
		elif not fstr_security_req == 'unsecured' and self.user.entity.user_status == 'VERIFIED' and not self.request.path == '/mob_s_register':
		
			# They have not yet registered with this application. Force them to the
			# regisration page.
			# STUB need to abstract this later for desktop vs. mobile
			self.request_handler.redirect('/mob_s_register')
		
		elif fstr_security_req == 'admin' and self.user.IS_ADMIN == False:
		
			# Admin page is special case. Send them to error page if they are not admin.
			# STUB: haven't built the error page yet.
			pass		

# this is the user class specifically designed for using google user authentication
class user(object):

	# intialization function, called when object is instantiated with or without a function call
	def __init__(self, fobj_master):
		
		# fobj_master - master object for the request
		
		# give this user object a reference to the master object
		self.PARENT = fobj_master
		
		# assume not logged in/admin/registered to start
		self.IS_LOGGED_IN = False
		self.IS_ADMIN = False
		self.IS_REGISTERED = False
		
		# declare an empty entity for now, will load or create one
		self.entity = None
		
		# see if this requestor is logged in via google
		lgoogle_account = users.get_current_user()
		
		if lgoogle_account:
		
			self.PARENT.TRACE.append("user.init(): google account loaded")
			# set some user info based on google user
			self.IS_LOGGED_IN = True
			# Admin status isn't stored in the datastore because it is changed
			# via app engine settings and not via this application. So we check
			# it every request in case it has been changed.
			if users.is_current_user_admin():
				self.IS_ADMIN = True
			else:
				self.IS_ADMIN = False
			self.entity = self._load_user(lgoogle_account)

		else:
		
			self.PARENT.TRACE.append("user.init(): google account not loaded")
			# No google account retrieved, user is not logged in
			self.entity = None
		
		# GAE Authentication Variables
		self.LOG_IN_GAE_HREF = users.create_login_url('/mob_s_home')
		self.LOG_IN_GAE_LINKTEXT = 'Login'
		self.LOG_OUT_GAE_HREF = users.create_logout_url('/')
		self.LOG_OUT_GAE_LINKTEXT = 'Logout'
		
   	def _load_user(self, fobj_google_account):
   
		# this function loads a user entity from a key
		ldata_user_key = ndb.Key("ds_mr_user",fobj_google_account.user_id())
		ldata_user = ldata_user_key.get()
		
		if ldata_user:

			# query from datastore succeeded, user exists
			self.PARENT.TRACE.append("user._load_user(): user object loaded")
			
		else:
			
			# query from datastore failed, user doesn't exist
			self.PARENT.TRACE.append("user._load_user(): user object not loaded")
			
			# create a new user
			ldata_user = ds_mr_user()
			ldata_user.user_id = fobj_google_account.user_id()
			ldata_user.user_status = 'VERIFIED'
			ldata_user.key = ldata_user_key	
			ldata_user.put()

		return ldata_user
		

# this is metric reserve class, containing the P2P network related functionality
class metric(object):

	# intialization function, called when object is instantiated with or without a function call
	def __init__(self, fobj_master):
	
		# give this object a reference to the master object
		self.PARENT = fobj_master
	
	@ndb.transactional(xg=True)
	def _initialize_network(self):
	
		# redo the existence check now that we're in a transaction
		network_key = ndb.Key("ds_mr_network_profile", "1000001")
		primary_network_profile = network_key.get()
		if primary_network_profile is not None:
			# it exists already, nevermind
			return primary_network_profile
		else:
			# not created yet
			primary_network_profile = ds_mr_network_profile()
			primary_network_profile.network_name = "Primary"
			primary_network_profile.network_id = "1000001"
			primary_network_profile.network_status = "ACTIVE"
			primary_network_profile.active_user_count = 0
			primary_network_profile.orphan_count = 0
			primary_network_profile.total_trees = 0
			# use the proper key from above
			primary_network_profile.key = network_key
			primary_network_profile.put()
			
			# also make the cursor for the network when making the network
			cursor_key = ndb.Key("ds_mr_network_cursor", "1000001")
			new_cursor = ds_mr_network_cursor()
			new_cursor.current_index = 0
			new_cursor.network_id = "1000001"
			new_cursor.key = cursor_key
			new_cursor.put()
			
			return primary_network_profile
			
	def _get_network_summary(self):
	
		# get the primary network
		# arbitrarily, I start network ids at one million and one
		# ..and that number is always the primary network.
		network_key = ndb.Key("ds_mr_network_profile", "1000001")
		primary_network_profile = network_key.get()
		if primary_network_profile is not None:
			self.PARENT.TRACE.append("metric._get_network_summary():primary network exists")
			return primary_network_profile
		else:
			# not created yet
			# initialize it in a transaction
			return self._initialize_network()
			
	@ndb.transactional(xg=True)
	def _join_network(self,fstr_user_id,fstr_network_id):
	
		# first make sure the user isn't already joined to this network
		# if not, join them at the proper index and create their metric account
		user_key = ndb.Key("ds_mr_user",fstr_user_id)
		lds_user = user_key.get()
		if not lds_user.metric_network_ids == "EMPTY":
			# user is already joined to the network
			return "error_already_joined"
		
		cursor_key = ndb.Key("ds_mr_network_cursor",fstr_network_id)
		
		# increment the network cursor
		lds_cursor = cursor_key.get()
		lds_cursor.current_index += 1
		
		# create a new metric account with key equal to current cursor/index for this network
		metric_account_key = ndb.Key("ds_mr_metric_account","%s%s" % (fstr_network_id,str(lds_cursor.current_index).zfill(12)))
		lds_metric_account = ds_mr_metric_account()
		lds_metric_account.network_id = fstr_network_id
		lds_metric_account.account_id = str(lds_cursor.current_index).zfill(12)
		lds_metric_account.key = metric_account_key
		
		# put the metric account id into the user object so we know this user is joined
		lds_user.metric_network_ids = "%s" % fstr_network_id
		lds_user.metric_account_ids = "%s" % str(lds_cursor.current_index).zfill(12)
		
		# save the transaction
		lds_user.put()
		lds_metric_account.put()
		lds_cursor.put()
		
		return "success"
		
################################################################
###
###  END: Application Classes
###
################################################################


################################################################
###
###  BEGIN: Page Handler Classes
###
################################################################

# page handler class for "/" (web root/home page)
class ph_home(webapp2.RequestHandler):

	# There is a mobile and desktop version of this site. We direct them to
	# the corresponding site based on CGI user agent variable. This only
	# applies to the root domain as all internal pages are named and rendered
	# separately so any bookmarking will always terminate on correct template.
	
	def get(self):
		
		# Instantiate the master object, do security and other app checks. If
		# there's an interruption return from this function without processing
		# further.
		lobj_master = master(self,"get","unsecured")
		if lobj_master.IS_INTERRUPTED:return
		
		# STUB - need user agent check after site complete, now just targeting mobile
		# by using "True" in decision logic.
		if True:
		
			# render mobile homepage
		        template = JINJA_ENVIRONMENT.get_template('templates/tpl_mob_u_home.html')
		        self.response.write(template.render(master=lobj_master))
		
		else:
		
			# render desktop homepage
			pass

# page handler class for "/mob_u_home" 
class ph_mob_u_home(webapp2.RequestHandler):

	def get(self):
		
		# Instantiate the master object, do security and other app checks. If
		# there's an interruption return from this function without processing
		# further.
		lobj_master = master(self,"get","unsecured")
		if lobj_master.IS_INTERRUPTED:return
		
		template = JINJA_ENVIRONMENT.get_template('templates/tpl_mob_u_home.html')
		self.response.write(template.render(master=lobj_master))

# page handler class for "/mob_u_menu" 
class ph_mob_u_menu(webapp2.RequestHandler):

	def get(self):
		
		# Instantiate the master object, do security and other app checks. If
		# there's an interruption return from this function without processing
		# further.
		lobj_master = master(self,"get","unsecured")
		if lobj_master.IS_INTERRUPTED:return
		
		template = JINJA_ENVIRONMENT.get_template('templates/tpl_mob_u_menu.html')
		self.response.write(template.render(master=lobj_master))

# page handler class for "/mob_s_home"
class ph_mob_s_home(webapp2.RequestHandler):

	def get(self):
		
		# Instantiate the master object, do security and other app checks. If
		# there's an interruption return from this function without processing
		# further.
		lobj_master = master(self,"get","secured")
		if lobj_master.IS_INTERRUPTED:return
		
		template = JINJA_ENVIRONMENT.get_template('templates/tpl_mob_s_home.html')
		self.response.write(template.render(master=lobj_master))
		
# page handler class for "/mob_s_menu" 
class ph_mob_s_menu(webapp2.RequestHandler):

	def get(self):
		
		# Instantiate the master object, do security and other app checks. If
		# there's an interruption return from this function without processing
		# further.
		lobj_master = master(self,"get","secured")
		if lobj_master.IS_INTERRUPTED:return
		
		template = JINJA_ENVIRONMENT.get_template('templates/tpl_mob_s_menu.html')
		self.response.write(template.render(master=lobj_master))

# page handler class for "/mob_s_scaffold1"
class ph_mob_s_scaffold1(webapp2.RequestHandler):

	def get(self):
		
		# Instantiate the master object, do security and other app checks. If
		# there's an interruption return from this function without processing
		# further.
		lobj_master = master(self,"get","secured")
		if lobj_master.IS_INTERRUPTED:return
		
		template = JINJA_ENVIRONMENT.get_template('templates/tpl_mob_s_scaffold1.html')
		self.response.write(template.render(master=lobj_master))
		
# page handler class for "/mob_s_test_form1"
class ph_mob_s_test_form1(webapp2.RequestHandler):

	def get(self):
		
		# Instantiate the master object, do security and other app checks. If
		# there's an interruption return from this function without processing
		# further.
		lobj_master = master(self,"get","secured")
		if lobj_master.IS_INTERRUPTED:return
		
		template = JINJA_ENVIRONMENT.get_template('templates/tpl_mob_s_test_form1.html')
		self.response.write(template.render(master=lobj_master))
		
# page handler class for "/mob_s_register"
class ph_mob_s_register(webapp2.RequestHandler):

	def get(self):
		
		# Instantiate the master object, do security and other app checks. If
		# there's an interruption return from this function without processing
		# further.
		lobj_master = master(self,"get","secured")
		if lobj_master.IS_INTERRUPTED:return
		
		lobj_master.TRACE.append("ph_mob_s_register.get(): in registration GET function")
		
		template = JINJA_ENVIRONMENT.get_template('templates/tpl_mob_s_register.html')
		self.response.write(template.render(master=lobj_master))
		
	def post(self):
	
		# Instantiate the master object, do security and other app checks. If
		# there's an interruption return from this function without processing
		# further.
		lobj_master = master(self,"post","secured")
		if lobj_master.IS_INTERRUPTED:return
		
		lobj_master.TRACE.append("ph_mob_s_register.post(): in registration POST function")
		
		# Do registration processing
		# Here's transaction we need to register the username
		@ndb.transactional(xg=True)
		def save_unique_username(fstr_name):

			maybe_new_key = ndb.Key("ds_mr_unique_dummy_entity", fstr_name)
			maybe_dummy_entity = maybe_new_key.get()
			if maybe_dummy_entity is not None:
				lobj_master.TRACE.append("metric._save_unique_name():entity was returned")
				return False # False meaning "not created"
			lobj_master.TRACE.append("metric._save_unique_name():entity was NOT returned")
			new_entity = ds_mr_unique_dummy_entity()
			new_entity.unique_name = fstr_name
			new_entity.key = maybe_new_key
			new_entity.put()
			lobj_master.user.entity.user_status = "ACTIVE"
			lobj_master.user.entity.username = fstr_name
			lobj_master.user.entity.put()
			return True # True meaning "created"
		
		# STEP 1 (VALIDATE FORMAT)
		# make sure the username format is entered correctly, only a-z, 0-9, and underscore allowed
		if not re.match(r'^[a-z0-9_]+$',lobj_master.request.POST['form_username']):
		
			# bad username format
			# kick them back to registration page with an error
			# error messages are contained in the HTML template and activated by URL query string
			lobj_master.request_handler.redirect('/mob_s_register?user_error=bad_username_format')
		
		# STEP 2 (VALIDATE UNIQUENESS AND PROCESS REQUEST)
		# make sure the chosen username isn't already taken
		elif not save_unique_username(lobj_master.request.POST['form_username']):
		
			# username is not unique
			# kick them back to registration page with an error
			# error messages are contained in the HTML template and activated by URL query string
			lobj_master.request_handler.redirect('/mob_s_register?user_error=username_not_unique')
		
		
		# SETP 3 (REDIRECT ON SUCCESS)
		# Redirect to non-POST page
		else:
			
			lobj_master.request_handler.redirect('/mob_s_register?form_success=username_successfully_assigned')

# page handler class for "/mob_s_network_summary"
class ph_mob_s_network_summary(webapp2.RequestHandler):

	def get(self):
		
		# Instantiate the master object, do security and other app checks. If
		# there's an interruption return from this function without processing
		# further.
		lobj_master = master(self,"get","secured")
		if lobj_master.IS_INTERRUPTED:return
		
		lobj_master.TRACE.append("ph_mob_s_network_summary.get(): in network_summary GET function")
		
		# Show network summary with join links
		lobj_master.network_summary_entity = lobj_master.metric._get_network_summary()
		
		# STUB TEMP get all users to show connect/disconnect links
		all_users = ds_mr_user.query().fetch()
		lobj_master.all_users = all_users
		
		template = JINJA_ENVIRONMENT.get_template('templates/tpl_mob_s_network_summary.html')
		self.response.write(template.render(master=lobj_master))
		
# page handler class for "/mob_s_join_network"
class ph_mob_s_join_network(webapp2.RequestHandler):

	def get(self):
		
		# Instantiate the master object, do security and other app checks. If
		# there's an interruption return from this function without processing
		# further.
		lobj_master = master(self,"get","secured")
		if lobj_master.IS_INTERRUPTED:return
		
		lobj_master.TRACE.append("ph_mob_s_join_network.get(): in join_network GET function")
		
		# Show join verification
		# In future we could have multiple networks and would query on passed in URL variable
		# but for now, we're ignoring that and just loading the primary network
		lobj_master.network_joining = lobj_master.metric._get_network_summary()
		
		template = JINJA_ENVIRONMENT.get_template('templates/tpl_mob_s_join_network.html')
		self.response.write(template.render(master=lobj_master))
		
	def post(self):
		
		# Instantiate the master object, do security and other app checks. If
		# there's an interruption return from this function without processing
		# further.
		lobj_master = master(self,"post","secured")
		if lobj_master.IS_INTERRUPTED:return
		
		lobj_master.TRACE.append("ph_mob_s_join_network.post(): in join_network POST function")
		
		
		# joining a network does 3 things primarily
		# 1. Update your user object to reference the metric account
		# 2. Create the metric account at cursor position
		# 3. Update the network cursor
		
		# Show join verification
		# In future we could have multiple networks and would query on passed in URL variable
		# but for now, we're ignoring that and just loading the primary network
		lobj_master.network_joining = lobj_master.metric._get_network_summary()
		lstr_result = lobj_master.metric._join_network(lobj_master.user.entity.user_id,lobj_master.network_joining.network_id)
		
		lobj_master.request_handler.redirect('/mob_s_network_summary?form_result=%s' % lstr_result)	

# page handler class for "/mob_s_connect"
class ph_mob_s_connect(webapp2.RequestHandler):

	def get(self):
		
		# Instantiate the master object, do security and other app checks. If
		# there's an interruption return from this function without processing
		# further.
		lobj_master = master(self,"get","secured")
		if lobj_master.IS_INTERRUPTED:return
		
		lobj_master.TRACE.append("ph_mob_s_connect.get(): in connect GET function")
		
		# Connect Page
		lobj_master.network_connecting = lobj_master.metric._get_network_summary()
		
		template = JINJA_ENVIRONMENT.get_template('templates/tpl_mob_s_connect.html')
		self.response.write(template.render(master=lobj_master))
		
	def post(self):
		
		# Instantiate the master object, do security and other app checks. If
		# there's an interruption return from this function without processing
		# further.
		lobj_master = master(self,"post","secured")
		if lobj_master.IS_INTERRUPTED:return
		
		lobj_master.TRACE.append("ph_mob_s_connect.get(): in connect POST function")
		
		
		# Connect Page
		
		template = JINJA_ENVIRONMENT.get_template('templates/tpl_mob_s_connect.html')
		self.response.write(template.render(master=lobj_master))	
		
		
		
################################################################
###
###  END: Page Handler Classes
###
################################################################


##########################################################################
# BEGIN: Python Entry point.  This function should be permanent.
##########################################################################

# Defining all pages here for simplicity
# 'ph' prefix means "page handler"
# 'mob' means "mobile version" (example: ph_mob_home)
# 'full' means "full browser version" (example: ph_full_home)
# 's' and 'u' refer to 'unsecured' vs. 'secured'
#
# so ph_mob_u_menu for instance means:
# "this class is a page handler for the mobile version of an unsecured menu page."

# All this function does is tell the module which path to match to which 
# class. It then calls either 'get' or 'post' function on that class depending
# on the request type. The path argument takes a regular expression but I 
# just use static mapping as building logic into path tokenizing and handling 
# gets unnecessarily complex.

# steps to add a new page
# 1. Create the template you want to use
# 2. Add it to the tuple-ey/arrayish thingy below
# 3. Create the class you designate below up above like the others with a get/post

application = webapp2.WSGIApplication([
	('/', ph_home),
	('/mob_u_home', ph_mob_u_home),
	('/mob_u_menu', ph_mob_u_menu),
	('/mob_s_home', ph_mob_s_home),
	('/mob_s_menu', ph_mob_s_menu),
	('/mob_s_register', ph_mob_s_register),
	('/mob_s_network_summary', ph_mob_s_network_summary),
	('/mob_s_join_network', ph_mob_s_join_network),
	('/mob_s_connect', ph_mob_s_connect),
	('/mobile_scaffold1', ph_mob_s_scaffold1),
	('/mobile_test_form1', ph_mob_s_test_form1)
	],debug=True)

##########################################################################
# END: Python Entry point.  This function should be permanent.
##########################################################################


