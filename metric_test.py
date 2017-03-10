################################################################
###
###  IMPORTS
###
################################################################

# these are standard python libraries
import os
import urllib

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

class ds_user(ndb.Model):

	user_id = ndb.StringProperty()
	username = ndb.StringProperty()
	email = ndb.StringProperty()
	
	user_status = ndb.StringProperty()
	
	name_first = ndb.StringProperty()
	name_middle = ndb.StringProperty()
	name_last = ndb.StringProperty()
	name_suffix = ndb.StringProperty()
	
	date_created = ndb.DateTimeProperty(auto_now_add=True)
	
	@classmethod
    	def get_by_google_id(cls, user):
        	return cls.query().filter(cls.user_id == user.user_id()).get()

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
		
		# instantiate a user via class - see 'class user(object)'
		self.user = user(self)
		
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
			pass
		
		elif not fstr_security_req == 'unsecured' and self.user.entity.status == 'VERIFIED':
		
			# They have not yet registered with this application. Force them to the
			# STUB: haven't built the page yet
			pass
		
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
		self.LOG_IN_GAE_HREF = users.create_login_url('/')
		self.LOG_IN_GAE_LINKTEXT = 'Login'
		self.LOG_OUT_GAE_HREF = users.create_logout_url('/')
		self.LOG_OUT_GAE_LINKTEXT = 'Logout'
		
   	def _load_user(self, fobj_google_account):
   
		# this function loads a user entity from a key
		ldata_user = ds_user.get_by_google_id(fobj_google_account)
		
		if ldata_user:

			# query from datastore succeeded, user exists
			self.PARENT.TRACE.append("user._load_user(): user object loaded")
			
		else:
			
			# query from datastore failed, user doesn't exist
			self.PARENT.TRACE.append("user._load_user(): user object not loaded")
			
			# create a new user
			ldata_user = ds_user(
				user_id=fobj_google_account.user_id(),
				user_status='VERIFIED')
				
			ldata_user.put()

		return ldata_user
		
		
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
		        template = JINJA_ENVIRONMENT.get_template('templates/tpl_mob_home.html')
		        self.response.write(template.render(master=lobj_master))
		
		else:
		
			# render desktop homepage
			pass

# page handler class for "/mob_home" 
class ph_mob_menu(webapp2.RequestHandler):

	def get(self):
		
		# Instantiate the master object, do security and other app checks. If
		# there's an interruption return from this function without processing
		# further.
		lobj_master = master(self,"get","unsecured")
		if lobj_master.IS_INTERRUPTED:return
		
		template = JINJA_ENVIRONMENT.get_template('templates/tpl_mob_menu.html')
		self.response.write(template.render(master=lobj_master))
		
# page handler class for "/mob_menu" 
class ph_mob_menu(webapp2.RequestHandler):

	def get(self):
		
		# Instantiate the master object, do security and other app checks. If
		# there's an interruption return from this function without processing
		# further.
		lobj_master = master(self,"get","unsecured")
		if lobj_master.IS_INTERRUPTED:return
		
		template = JINJA_ENVIRONMENT.get_template('templates/tpl_mob_menu.html')
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

# All this function does is tell the module which path to match to which 
# class. It then calls either 'get' or 'post' function on that class depending
# on the request type. The path argument takes a regular expression but I 
# just use static mapping as building logic into path tokenizing and handling 
# gets unnecessarily complex.

application = webapp2.WSGIApplication([
	('/', ph_home),
	('/mob_menu',ph_mob_menu)
	],debug=True)

##########################################################################
# END: Python Entry point.  This function should be permanent.
##########################################################################


