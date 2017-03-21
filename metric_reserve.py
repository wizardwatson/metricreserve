############################################################################79
###
###  IMPORTS
###
##############################################################################




# These are standard python libraries.
import os
import urllib
import datetime
import re
import pickle
import random
import bisect
from operator import itemgetter
# for debugging on dev_appserver.py only
import pdb
# how to invoke: Just put this on any line: "pdb.set_trace()"
# read about pdb: https://cloud.google.com/appengine/docs/standard/python/tools/using-local-server#Python_Debugging_with_PDB

# these are standard GAE imports
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import ndb

# These are app.yaml imports.
import webapp2
import jinja2

# These are my custom modules.
# [example]: from [directory] import [some py file without extension]

# Setup jinja environment: we are using jinja for processing templates
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

##############################################################################
###
###  SETTINGS
###
##############################################################################

# Number of shard counters application creates.
# You can increase these, but decreasing will break it.
NUM_BALANCE_POSITIVE_SHARDS = 20
NUM_BALANCE_NEGATIVE_SHARDS = 20
NUM_RESERVE_POSITIVE_SHARDS = 20
NUM_RESERVE_NEGATIVE_SHARDS = 20

IS_DEBUG = True
REDO_FINISHED_GRAPH_PROCESS = True

# How often do you want the application to process the graph?
GRAPH_FREQUENCY_MINUTES = 15
GRAPH_ITERATION_DURATION_SECONDS = 30
GRAPH_ITERATION_WIGGLE_ROOM_SECONDS = 15
GRAPH_ITERATION_HIJACK_DURATION_SECONDS = 10

# $1 of value = 100,000
MAX_RESERVE_MODIFY = 100000000
MAX_PAYMENT = 100000000

# Arbitrary time from which the application calculates cutoff time for graph 
# process.
T_EPOCH = datetime.datetime(2017, 3, 13, 8, 0, 0, 0)

##############################################################################
###
###  BEGIN: DATASTORE entities
###
##############################################################################

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
	
	metric_network_ids = ndb.PickleProperty(default=[])
	metric_account_ids = ndb.PickleProperty(default=[])
	
	date_created = ndb.DateTimeProperty(auto_now_add=True)

# this is just an entity solely used to enforce name uniqueness in other
# objects via transactions google's datastore requires a little extra work
# to enforce a unique constraint
class ds_mr_unique_dummy_entity(ndb.Model):

	unique_name = ndb.StringProperty()
	date_created = ndb.DateTimeProperty(auto_now_add=True)

# network profile: this entity contains information about specific graph
class ds_mr_network_profile(ndb.Model):

	network_name = ndb.StringProperty()
	network_id = ndb.IntegerProperty()
	network_status = ndb.StringProperty()
	network_type = ndb.StringProperty()
	active_user_count = ndb.IntegerProperty()
	orphan_count = ndb.IntegerProperty()
	total_trees = ndb.IntegerProperty()
	last_graph_process = ndb.DateTimeProperty()
	date_created = ndb.DateTimeProperty(auto_now_add=True)
	
# network cursor: this entity maintains the index of network accounts
class ds_mr_network_cursor(ndb.Model):

	network_id = ndb.StringProperty()
	current_index = ndb.IntegerProperty()

# metric account: this is the main account information
class ds_mr_metric_account(ndb.Model):

	account_id = ndb.IntegerProperty()
	network_id = ndb.IntegerProperty()
	user_id = ndb.StringProperty()
	tx_index = ndb.IntegerProperty()
	account_status = ndb.StringProperty()
	outgoing_connection_requests = ndb.PickleProperty(default="EMPTY")
	incoming_connection_requests = ndb.PickleProperty(default="EMPTY")
	incoming_reserve_transfer_requests = ndb.PickleProperty()
	outgoing_reserve_transfer_requests = ndb.PickleProperty()
	suggested_inactive_incoming_reserve_transfer_requests = ndb.PickleProperty()
	suggested_inactive_outgoing_reserve_transfer_requests = ndb.PickleProperty()
	suggested_active_incoming_reserve_transfer_requests = ndb.PickleProperty()
	suggested_active_outgoing_reserve_transfer_requests = ndb.PickleProperty()
	current_timestamp = ndb.DateTimeProperty(auto_now_add=True)
	current_connections = ndb.PickleProperty(default="EMPTY")
	current_reserve_balance = ndb.IntegerProperty()
	current_network_balance = ndb.IntegerProperty()	
	last_connections = ndb.PickleProperty(default="EMPTY")
	last_reserve_balance = ndb.IntegerProperty()
	last_network_balance = ndb.IntegerProperty()
	date_created = ndb.DateTimeProperty(auto_now_add=True)

# transaction log:  think "bank statements"
class ds_mr_tx_log(ndb.Model):

	category = ndb.StringProperty()
	tx_index = ndb.IntegerProperty()
	tx_type = ndb.StringProperty()
	amount = ndb.IntegerProperty()
	access = ndb.StringProperty()
	description = ndb.StringProperty()
	memo = ndb.StringProperty()
	date_created = ndb.DateTimeProperty(auto_now_add=True)
	user_id_created = ndb.StringProperty()
	network_id = ndb.IntegerProperty()
	account_id = ndb.IntegerProperty()
	source_account = ndb.IntegerProperty()
	target_account = ndb.IntegerProperty()
	
# counter shards to track global balances and reserves
# on the fly creation is done where they are used/incremented
# positive balance counter shard
class ds_mr_positive_balance_shard(ndb.Model):
	count = ndb.IntegerProperty(default=0)
	
	def get_count():
	    total = 0
	    for counter in ds_mr_positive_balance_shard.query():
		total += counter.count
	    return total
# negative balance counter shard
class ds_mr_negative_balance_shard(ndb.Model):
	count = ndb.IntegerProperty(default=0)
	
	def get_count():
	    total = 0
	    for counter in ds_mr_negative_balance_shard.query():
		total += counter.count
	    return total
# positive reserve counter shard
class ds_mr_positive_reserve_shard(ndb.Model):
	count = ndb.IntegerProperty(default=0)
	
	def get_count():
	    total = 0
	    for counter in ds_mr_positive_reserve_shard.query():
		total += counter.count
	    return total
# negative reserve counter shard
class ds_mr_negative_reserve_shard(ndb.Model):
	count = ndb.IntegerProperty(default=0)
	
	def get_count():
	    total = 0
	    for counter in ds_mr_negative_reserve_shard.query():
		total += counter.count
	    return total



##############################################################################
###
###  DATASTORE entities related to GRAPH PROCESSING
###  
##############################################################################

# Labeling Conventions:
#
# ds = datastore class
# mrgp = metric reserve graph processing related
	
# *** the profile entity ***
#
# This entity controls a specific networks specific graph process and 
# also is what generates the report after it's finished.  If a process
# gets paused, this is the entity that keeps track of where it stopped
# at and where it needs to continue from.  It holds all the important
# information about how many chunks there are for this process, etc.

class ds_mrgp_profile(ndb.Model):

	status = ndb.StringProperty()
	deadline = ndb.DateTimeProperty()
	max_account = ndb.IntegerProperty()
	phase_cursor = ndb.IntegerProperty()
	tree_cursor = ndb.IntegerProperty()
	count_cursor = ndb.IntegerProperty()
	tree_chunks = ndb.IntegerProperty()
	tree_in_process = ndb.BooleanProperty()
	index_chunks = ndb.IntegerProperty()
	parent_pointer = ndb.IntegerProperty()
	child_pointer = ndb.IntegerProperty()
	report = ndb.PickleProperty()

# *** the staging chunk ***
class ds_mrgp_staging_chunk(ndb.Model):
	stuff = ndb.PickleProperty()
# *** the index chunk ***
class ds_mrgp_index_chunk(ndb.Model):
	stuff = ndb.PickleProperty()
# *** the tree chunk ***
class ds_mrgp_tree_chunk(ndb.Model):
	stuff = ndb.PickleProperty()
# *** the report chunk ***
class ds_mrgp_report_chunk(ndb.Model):
	stuff = ndb.PickleProperty()
	
##############################################################################
###
###  DATASTORE entities related to DEBUGGING
###  
##############################################################################

# the big pickle
class ds_mrgp_big_pickle(ndb.Model):

	stuff = ndb.PickleProperty()

##############################################################################
###
###  END: DATASTORE entities
###
##############################################################################

##############################################################################
###
###  BEGIN: Application Classes
###
##############################################################################

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
		self.IS_DEBUG = IS_DEBUG
		# For my own "stack" tracing I just append to a delimited list for later output.
		self.TRACE = []
		
		# Start with what time it is:
		self.TRACE.append("current time:%s" % str(datetime.datetime.now()))
		"""
		tree_index_test = ds_mrgp_big_pickle()
		tree_index_test.stuff = []
		for i in range(1,800001):
			if random.randint(1,2) == 1:
				lbool_value = True
			else:
				lbool_value = False
			tree_index_test.stuff.append(lbool_value)
		self.TRACE.append("tree_index_test length at 100,000:%s" % str(len(tree_index_test._to_pb().Encode())))
		self.TRACE.append("current time:%s" % str(datetime.datetime.now()))		
		
		# staging chunk size testing
		staging_test = ds_mrgp_staging_chunk()
		staging_test.stuff = {}
		for i in range(1,2501):
			st_account_id = random.randint(10000000000,20000000000)
			staging_test.stuff[st_account_id] = {}
			# tree id
			staging_test.stuff[st_account_id][1] = random.randint(10000000000,20000000000)
			# connections * 20 
			
			staging_test.stuff[st_account_id][2] = []
			
			for x in range(1,21):
				staging_test.stuff[st_account_id][2].append(random.randint(10000000000,20000000000))
				
			# suggestions * 20
			staging_test.stuff[st_account_id][3] = []
			for x in range(1,21):
				# staging_test.stuff[st_account_id][3].append(0)
				staging_test.stuff[st_account_id][3].append(random.randint(10000000000,20000000000))
			# network balance
			staging_test.stuff[st_account_id][4] = random.randint(10000000000,20000000000)
			# reserves
			staging_test.stuff[st_account_id][5] = random.randint(10000000000,20000000000)	
			
		self.TRACE.append("staging_test length at 1000:%s" % str(len(staging_test._to_pb().Encode())))
		self.TRACE.append("current time:%s" % str(datetime.datetime.now()))
		"""
		#DEBUG STUFF BEGIN
		
		some_obj = ds_mrgp_big_pickle()
		
		some_obj.stuff = (1,2,3)
		self.TRACE.append("object length:%s" % str(len(some_obj._to_pb().Encode())))
		self.TRACE.append(str(int(-10222)).zfill(12))
		some_obj.put()
		
		str(int(-10222)).zfill(12)
		self.TRACE.append(str(int(str(int(-10222)).zfill(12)) + 30000))
		
		self.TRACE.append(str((int(str(int(-10222)).zfill(12)) + 30000)*-1))
		
		self.TRACE.append("key chunk sample test: %s" % str((50000 - (50000 % 20000))/20000))
		
		
		
		
		
		
		
		# Calculate the graph process cutoff time for this request
		t_now = datetime.datetime.now()
		#pdb.set_trace()
		d_since = t_now - T_EPOCH
		# this requests cutoff time
		t_cutoff = t_now - datetime.timedelta(seconds=(d_since.total_seconds() % (GRAPH_FREQUENCY_MINUTES * 60)))
		self.TRACE.append("request cutoff time:%s" % str(t_cutoff))
		self.TRACE.append("request cutoff time:YEAR-%s-" % str(t_cutoff.year))
		self.TRACE.append("request cutoff time:MONTH-%s-" % str(t_cutoff.month))
		self.TRACE.append("request cutoff time:DAY-%s-" % str(t_cutoff.day))
		self.TRACE.append("request cutoff time:HOUR-%s-" % str(t_cutoff.hour))
		self.TRACE.append("request cutoff time:MINUTES-%s-" % str(t_cutoff.minute))
		
		
		
		
		
		#DEBUG STUFF END
		
		
		
		
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
			
			# transaction log:  think "bank statements"
			lds_tx_log = ds_mr_tx_log()
			lds_tx_log.category = "MRTX" # GENERAL TRANSACTION GROUPING
			# tx_index should be based on incremented metric_account value
			lds_tx_log.tx_index = 0
			lds_tx_log.tx_type = "USER CREATED" # SHORT WORD(S) FOR WHAT TRANSACTION DID
			lds_tx_log.amount = 0
			lds_tx_log.access = "PUBLIC" # "PUBLIC" OR "PRIVATE"
			lds_tx_log.description = "A new user object was created." 
			lds_tx_log.memo = ""
			lds_tx_log.user_id_created = fobj_google_account.user_id()
			lds_tx_log.network_id = ""
			lds_tx_log.account_id = ""
			lds_tx_log.source_account = "" 
			lds_tx_log.target_account = ""
			lds_tx_log.put()			

		return ldata_user
		
	@ndb.transactional(xg=True)
	def _save_unique_username(self,fstr_name):

		# new name check
		maybe_new_key = ndb.Key("ds_mr_unique_dummy_entity", fstr_name)
		maybe_dummy_entity = maybe_new_key.get()
		if maybe_dummy_entity is not None:
			self.PARENT.TRACE.append("metric._save_unique_name():entity was returned")
			return False # False meaning "not created"
		self.PARENT.TRACE.append("metric._save_unique_name():entity was NOT returned")
		new_entity = ds_mr_unique_dummy_entity()
		new_entity.unique_name = fstr_name
		new_entity.key = maybe_new_key
		new_entity.put()
		# assign new username to user
		self.PARENT.user.entity.user_status = "ACTIVE"
		self.PARENT.user.entity.username = fstr_name
		self.PARENT.user.entity.put()
		
		# transaction log:  think "bank statements"
		lds_tx_log = ds_mr_tx_log()
		lds_tx_log.category = "MRTX" # GENERAL TRANSACTION GROUPING
		# tx_index should be based on incremented metric_account value
		lds_tx_log.tx_index = 0
		lds_tx_log.tx_type = "NEW USERNAME CREATED" # SHORT WORD(S) FOR WHAT TRANSACTION DID
		lds_tx_log.amount = 0
		lds_tx_log.access = "PUBLIC" # "PUBLIC" OR "PRIVATE"
		lds_tx_log.description = "A new username was chosen by a user." 
		lds_tx_log.memo = fstr_name
		lds_tx_log.user_id_created = self.PARENT.user.user_id
		lds_tx_log.network_id = ""
		lds_tx_log.account_id = ""
		lds_tx_log.source_account = "" 
		lds_tx_log.target_account = ""
		lds_tx_log.put()
		
		return True # True meaning "created"
		
	@ndb.transactional(xg=True)
	def _change_unique_username(self,fstr_name):

		# new name check
		maybe_new_key = ndb.Key("ds_mr_unique_dummy_entity", fstr_name)
		maybe_dummy_entity = maybe_new_key.get()
		if maybe_dummy_entity is not None:
			self.PARENT.TRACE.append("metric._save_unique_name():entity was returned")
			return False # False meaning "not created"
		self.PARENT.TRACE.append("metric._change_unique_username():entity was NOT returned")
		new_entity = ds_mr_unique_dummy_entity()
		new_entity.unique_name = fstr_name
		new_entity.key = maybe_new_key
		new_entity.put()
		# delete old name making available for others to now use
		old_key = ndb.Key("ds_mr_unique_dummy_entity", self.PARENT.user.entity.username)
		old_key.delete()
		# assign new username to user
		self.PARENT.user.entity.user_status = "ACTIVE"
		self.PARENT.user.entity.username = fstr_name
		self.PARENT.user.entity.put()
		
		# transaction log:  think "bank statements"
		lds_tx_log = ds_mr_tx_log()
		lds_tx_log.category = "MRTX" # GENERAL TRANSACTION GROUPING
		# tx_index should be based on incremented metric_account value
		lds_tx_log.tx_index = 0
		lds_tx_log.tx_type = "USERNAME CHANGED" # SHORT WORD(S) FOR WHAT TRANSACTION DID
		lds_tx_log.amount = 0
		lds_tx_log.access = "PUBLIC" # "PUBLIC" OR "PRIVATE"
		lds_tx_log.description = "A user changed their username." 
		lds_tx_log.memo = fstr_name
		lds_tx_log.user_id_created = self.PARENT.user.user_id
		lds_tx_log.network_id = ""
		lds_tx_log.account_id = ""
		lds_tx_log.source_account = "" 
		lds_tx_log.target_account = ""
		lds_tx_log.put()
		
		return True # True meaning "created"
			
# this is metric reserve class, containing the P2P network/accounting related functionality
class metric(object):

	# intialization function, called when object is instantiated with or without a function call
	def __init__(self, fobj_master):
	
		# give this object a reference to the master object
		self.PARENT = fobj_master
	
	@ndb.transactional(xg=True)
	def _initialize_network(self, fint_network_id, fstr_network_name="Primary", fstr_network_type="PUBLIC_LIVE"):
	
		# redo the existence check now that we're in a transaction
		network_key = ndb.Key("ds_mr_network_profile", "%s" % str(fint_network_id).zfill(8))
		new_network_profile = network_key.get()
		if new_network_profile is not None:
			# it exists already, nevermind
			return new_network_profile
		else:
			# not created yet
			new_network_profile = ds_mr_network_profile()
			new_network_profile.network_name = fstr_network_name
			new_network_profile.network_id = fint_network_id
			new_network_profile.network_status = "ACTIVE"
			new_network_profile.network_type = fstr_network_type
			new_network_profile.active_user_count = 0
			new_network_profile.orphan_count = 0
			new_network_profile.total_trees = 0
			# use the proper key from above
			new_network_profile.key = network_key
			new_network_profile.put()
			
			# also make the cursor for the network when making the network
			cursor_key = ndb.Key("ds_mr_network_cursor", "%s" % str(fint_network_id).zfill(8))
			new_cursor = ds_mr_network_cursor()
			new_cursor.current_index = 0
			new_cursor.network_id = fint_network_id
			new_cursor.key = cursor_key
			new_cursor.put()

			# transaction log
			lds_tx_log = ds_mr_tx_log()
			lds_tx_log.category = "MRTX" # GENERAL TRANSACTION GROUPING
			# tx_index should be based on incremented metric_account value
			lds_tx_log.tx_index = 0
			lds_tx_log.tx_type = "NETWORK INITIALIZED" # SHORT WORD(S) FOR WHAT TRANSACTION DID
			lds_tx_log.amount = 0
			lds_tx_log.access = "PUBLIC" # "PUBLIC" OR "PRIVATE"
			lds_tx_log.description = "A new network was created." 
			lds_tx_log.memo = "%s %s" % (fstr_network_name, str(fint_network_id))
			lds_tx_log.user_id_created = self.PARENT.user.user_id
			lds_tx_log.network_id = fint_network_id
			lds_tx_log.account_id = ""
			lds_tx_log.source_account = "" 
			lds_tx_log.target_account = ""
			lds_tx_log.put()

			return new_network_profile
			
	def _get_network_summary(self, fint_network_id=1):
	
		# get the primary network
		# default is 1
		network_key = ndb.Key("ds_mr_network_profile", "%s" % str(fint_network_id).zfill(8))
		network_profile = network_key.get()
		if network_profile is not None:
			self.PARENT.TRACE.append("metric._get_network_summary():network exists")
			return network_profile
		else:
			# not created yet
			# ONLY AUTO-INITIALIZE THE PRIMARY NETWORK!!!
			if fstr_network_id == 1: return self._initialize_network(fint_network_id)
			
	@ndb.transactional(xg=True)
	def _join_network(self,fstr_user_id,fint_network_id):
	
		# first make sure the user isn't already joined to this 
		# network if not, join them at the proper index and create
		# their metric account user_key = ndb.Key("ds_mr_user",
		# fstr_user_id)
		lds_user = user_key.get()
		if not lds_user.metric_network_ids == "EMPTY":
			# user is already joined to the network
			return "error_already_joined"
		
		# increment the network cursor and update the key chunk(s)
		cursor_key = ndb.Key("ds_mr_network_cursor", "%s" % str(fint_network_id).zfill(8))		
		lds_cursor = cursor_key.get()
		lds_cursor.current_index += 1
		
		# create a new metric account with key equal to current cursor/index for this network
		metric_account_key = ndb.Key("ds_mr_metric_account","%s%s" % (str(fint_network_id).zfill(8),str(lds_cursor.current_index).zfill(12)))
		lds_metric_account = ds_mr_metric_account()
		lds_metric_account.network_id = fint_network_id
		lds_metric_account.account_id = lds_cursor.current_index
		lds_metric_account.user_id = lds_user.user_id
		lds_metric_account.tx_index = 1
		lds_metric_account.account_status = "ACTIVE"
		lds_metric_account.outgoing_connection_requests = []
		lds_metric_account.incoming_connection_requests = []
		lds_metric_account.incoming_reserve_transfer_requests = {}
		lds_metric_account.outgoing_reserve_transfer_requests = {}
		lds_metric_account.suggested_inactive_incoming_reserve_transfer_requests = {}
		lds_metric_account.suggested_inactive_outgoing_reserve_transfer_requests = {}
		lds_metric_account.suggested_active_incoming_reserve_transfer_requests = {}
		lds_metric_account.suggested_active_outgoing_reserve_transfer_requests = {}
		lds_metric_account.current_connections = []
		lds_metric_account.current_reserve_balance = 0
		lds_metric_account.current_network_balance = 0	
		lds_metric_account.last_connections = []
		lds_metric_account.last_reserve_balance = 0
		lds_metric_account.last_network_balance = 0
		lds_metric_account.key = metric_account_key
		
		# put the metric account id into the user object so we know this user is joined
		lds_user.metric_network_ids = fint_network_id
		lds_user.metric_account_ids = lds_cursor.current_index
		
		# transaction log
		tx_log_key = ndb.Key("MRTX%s%s%s", (fstr_network_id,fstr_user_id,str(1).zfill(12)))
		lds_tx_log = ds_mr_tx_log()
		lds_tx_log.key = tx_log_key
		lds_tx_log.category = "MRTX" # GENERAL TRANSACTION GROUPING
		# tx_index should be based on incremented metric_account value
		lds_tx_log.tx_index = 1
		lds_tx_log.tx_type = "JOINED NETWORK" # SHORT WORD(S) FOR WHAT TRANSACTION DID
		lds_tx_log.amount = 0
		lds_tx_log.access = "PUBLIC" # "PUBLIC" OR "PRIVATE"
		lds_tx_log.description = "A user joined a network." 
		lds_tx_log.memo = ""
		lds_tx_log.user_id_created = lds_user.user_id
		lds_tx_log.network_id = fstr_network_id
		lds_tx_log.account_id = fstr_user_id
		lds_tx_log.source_account = fstr_user_id 
		lds_tx_log.target_account = ""
		lds_tx_log.put()
		
		# save the transaction
		lds_user.put()
		lds_metric_account.put()
		lds_cursor.put()
		
		return "success"

	@ndb.transactional(xg=True)
	def _leave_network(self, fint_account_id, fint_network_id):
	
		# must have zero connections in order to leave the network
		# graph process cannot be going on when we delete
		
		# BEGIN THOUGHT
		# OK, so I just thought of something.  For the graph process, I felt
		# it was necessary to use integer based keys to make the algorithm more
		# simplistic.  I knew that if we had each "chunk" hold say 2000 accounts
		# that first chunk would be 1-2000.  The whole point being that we can 
		# query by keys.  Originally, I envisioned-when someone leaves the network-
		# that we'd have to swap out their index with the account at last index.
		#
		# But I don't think this is necessary, and we can avoid I think having
		# to transactionally swap all the connections for the last account we're
		# moving into the vacant spot.  What we need to store is the "chunk ranges".
		# Starting is: chunk#1 = 1-2000, chunk#2 = 2001-4000, etc.  If you delete
		# an account you just need to adjust the chunk ranges.  It makes it a little
		# more complex when running the graph process, but no deleting will occur
		# during the process, so the chunk range structure can stay in memory without
		# worry of it being modified.
		# 
		# This lets us also avoid ever having to change a network account id for a 
		# user on a specific network.
		# END THOUGHT
		
		# first retrieve and check the metric account
		key_part1 = str(fint_network_id).zfill(8)
		key_part2 = str(fint_account_id).zfill(12)
		metric_account_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part2))
		lds_metric_account = metric_account_key.get()
		
		# error if source doesn't exist
		if lds_metric_account is None: return "error_account_id_invalid"
		
		# error if account still has connections
		if len(lds_metric_account.current_connections) > 0: return "error_account_still_has_connections"		

		# the only two values in a metric account that really matter during a deletion
		# will be the network and reserve remaining balances.  We do one finally transaction
		# on this account that works like a "modify_reserve", "normal_subtract" only we ignore
		# any checks and we remove entire balance even if it exceeds the reserve amount.  All
		# reserves and balances are forfeit, essentially.
		
		# increment negative balance shard
		if lds_metric_account.current_network_balance > 0:
			lint_shard_string_index = str(random.randint(0, NUM_BALANCE_NEGATIVE_SHARDS - 1))
			lds_counter1 = ds_mr_negative_balance_shard.get_by_id(lint_shard_string_index)
			if lds_counter1 is None:
				lds_counter1 = ds_mr_negative_balance_shard(id=lint_shard_string_index)
			lds_counter1.count += lds_metric_account.current_network_balance
			lds_counter1.put()

		# increment negative reserve shard
		if lds_metric_account.current_reserve_balance > 0:
			lint_shard_string_index = str(random.randint(0, NUM_RESERVE_NEGATIVE_SHARDS - 1))
			lds_counter2 = ds_mr_negative_reserve_shard.get_by_id(lint_shard_string_index)
			if lds_counter2 is None:
				lds_counter2 = ds_mr_negative_reserve_shard(id=lint_shard_string_index)
			lds_counter2.count += lds_metric_account.current_reserve_balance
			lds_counter2.put()

		lstr_return_message = "success_reserve_normal_subtract"
		
		lds_chunk_catalog.put()
		
		lds_metric_account.tx_index += 1
		# transaction log
		key_part3 = str(lds_metric_account.tx_index).zfill(12)
		tx_log_key = ndb.Key("MRTX%s%s%s", (key_part1,key_part2,key_part3))
		lds_tx_log = ds_mr_tx_log()
		lds_tx_log.key = tx_log_key
		lds_tx_log.category = "MRTX" # GENERAL TRANSACTION GROUPING
		# tx_index should be based on incremented metric_account value
		lds_tx_log.tx_index = lds_metric_account.tx_index
		lds_tx_log.tx_type = "LEFT NETWORK" # SHORT WORD(S) FOR WHAT TRANSACTION DID
		lds_tx_log.amount = 0
		lds_tx_log.access = "PUBLIC" # "PUBLIC" OR "PRIVATE"
		lds_tx_log.description = "A user left a network." 
		lds_tx_log.memo = ""
		lds_tx_log.user_id_created = lds_metric_account.user_id
		lds_tx_log.network_id = fint_network_id
		lds_tx_log.account_id = fint_account_id
		lds_tx_log.source_account = fint_account_id 
		lds_tx_log.target_account = ""
		lds_tx_log.put()
		
		# don't delete an account, just set it's status to "deleted", and delete it along with
		# it's transactions when however much time passes where we no longer want to keep them
		lds_metric_account.current_network_balance = 0
		lds_metric_account.current_reserve_balance = 0
		lds_metric_account.account_status = "DELETED"
		lds_metric_account.current_timestamp = datetime.datetime.now()
		lds_metric_account.put()
		
	@ndb.transactional(xg=True)
	def _connect(self, fint_network_id, fint_source_account_id, fint_target_account_id):
	
		# connect() corresponds to a "friending" to use a Facebook
		# term.  Basically reserves pass through your connections and
		# the network is literally defined by these bilateral connections.
		# If you are not connected to anyone you are an orphan.  Upper
		# limit on connections needs to be set to mitigate chunking size
		# issues in the graph/tree processing phase.
		#
		# Just like friending, both parties must agree to connect.  So 
		# when one person tries to connect to the other, it's semantically
		# a "connection request".  When the other party connects to the same
		# person after they've already done a connection request, it's semantically a 
		# "connection request authorized" and then the two parties are 
		# connected.
		#
		# Just like with other functions that affect the graph state and are
		# processed in the tree process phase, we have to pay attention to the
		# timestamp to determine whether to only change the current state, or
		# move the current to the last state before updating the current.
		#
		# got all that? lol
		
		# get the source and target metric accounts
		key_part1 = str(fint_network_id).zfill(8)
		key_part2 = str(fint_source_account_id).zfill(12)
		source_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part2))
		lds_source = source_key.get()
		
		# error if source doesn't exist
		if lds_source is None: return "error_source_id_not_valid"
		# error if trying to connect to self
		if fint_source_account_id == fint_target_account_id: return "error_cant_connect_to_self"
		
		key_part3 = str(fint_target_account_id).zfill(12)
		target_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part3))
		lds_target = target_key.get()
		
		# error if target doesn't exist
		if lds_target is None: return "error_target_id_not_valid"

		# Five situations where we don't even try to connect
		# 1. Source and target are already connected.
		if fint_target_account_id in lds_source.current_connections: return "error_already_connected"
		# 2. Source already has outgoing connection request to target
		if fint_target_account_id in lds_source.outgoing_connection_requests: return "error_connection_already_requested"
		# 3. Target incoming connection requests is maxed out
		if len(lds_target.incoming_connection_requests) > 19: return "error_target_incoming_requests_maxed"
		# 4. Source outgoing connection requests is maxed out
		if len(lds_source.outgoing_connection_requests) > 19: return "error_target_incoming_requests_maxed"
		# 5. Target or source has reached their maximum number of connections
		if len(lds_source.current_connections) > 19: return "error_source_connections_maxed"
		if len(lds_target.current_connections) > 19: return "error_target_connections_maxed"
		
		# should be ok to connect
		# check if the target has the source in it's outgoing connection requests
		if fint_source_account_id in lds_target.outgoing_connection_requests:
			
			# target already connected, this is a connection request authorization
			
			# First thing we need to do-and probably should abstract this later STUB
			# since we will need in other places-is we need to figure out our cutoff
			# time for "current_timestamp" based on graph processing frequency.
			#
			# My basic idea is to subtract the frequencies modulus since epoch time
			# (which I'm arbitralily making 8am UTC March 13th, 2017) from the current
			# datetime.  We'll set frequency in minutes but convert to seconds since
			# that's what timedelta uses in python.
			
			t_now = datetime.datetime.now()
			d_since = t_now - T_EPOCH
			# this requests cutoff time
			t_cutoff = t_now - datetime.timedelta(seconds=(d_since.total_seconds() % (GRAPH_FREQUENCY_MINUTES * 60)))
			
			# Worthy to note here, perhaps, is that we are evaluating the "old" 
			# current_timestamps for the two parties involved independently, even though the 
			# "new" current_timestamp will be the same.
			
			# update the source account
			if lds_source.current_timestamp > t_cutoff:
				
				# last transaction was in current time window, no need to swap
				# a.k.a. overwrite current
				lds_source.current_connections.append(fint_target_account_id)
				lds_source.incoming_connection_requests.remove(fint_target_account_id)
				
			else:
			
				# last transaction was in previous time window, swap
				# a.k.a. move "old" current into "last" before overwriting
				lds_source.last_connections = lds_source.current_connections
				lds_source.last_reserve_balance = lds_source.current_reserve_balance
				lds_source.last_network_balance = lds_source.current_network_balance
				lds_source.current_connections.append(fint_target_account_id)
				lds_source.incoming_connection_requests.remove(fint_target_account_id)
				
	
			# update the target account
			if lds_target.current_timestamp > t_cutoff:
				
				# last transaction was in current time window, no need to swap
				# a.k.a. overwrite current
				lds_target.current_connections.append(fint_source_account_id)
				lds_target.outgoing_connection_requests.remove(fint_source_account_id)
				
			else:
			
				# last transaction was in previous time window, swap
				# a.k.a. move "old" current into "last" before overwriting
				lds_target.last_connections = lds_target.current_connections
				lds_target.last_reserve_balance = lds_target.current_reserve_balance
				lds_target.last_network_balance = lds_target.current_network_balance
				lds_target.current_connections.append(fint_source_account_id)
				lds_target.outgoing_connection_requests.remove(fint_source_account_id)
			
			# only update current_timestamp for graph dependent transactions??? STUB
			lstr_source_tx_type = "INCOMING CONNECTION AUTHORIZED"
			lstr_source_tx_description = "INCOMING CONNECTION AUTHORIZED"
			lstr_target_tx_type = "OUTGOING CONNECTION AUTHORIZED"
			lstr_target_tx_description = "OUTGOING CONNECTION AUTHORIZED"
			lds_source.current_timestamp = datetime.datetime.now()
			lds_target.current_timestamp = datetime.datetime.now()			
			lstr_return_message = "success_connection_request_authorized"
			
			
		else:
			# target not yet connected, this is a connection request
			lstr_source_tx_type = "OUTGOING CONNECTION REQUEST"
			lstr_source_tx_description = "OUTGOING CONNECTION REQUEST"
			lstr_target_tx_type = "INCOMING CONNECTION REQUEST"
			lstr_target_tx_description = "INCOMING CONNECTION REQUEST"
			lds_source.outgoing_connection_requests.append(fint_target_account_id)
			lds_target.incoming_connection_requests.append(fint_source_account_id)
			lstr_return_message = "success_connection_request_completed"
		
		
		lds_source.tx_index += 1
		# source transaction log
		source_tx_log_key = ndb.Key("MRTX%s%s%s", (key_part1,key_part2,str(lds_source.tx_index).zfill(12)))
		source_lds_tx_log = ds_mr_tx_log()
		source_lds_tx_log.key = source_tx_log_key
		source_lds_tx_log.category = "MRTX" # GENERAL TRANSACTION GROUPING
		# tx_index should be based on incremented metric_account value
		source_lds_tx_log.tx_index = lds_source.tx_index
		source_lds_tx_log.tx_type = lstr_source_tx_type # SHORT WORD(S) FOR WHAT TRANSACTION DID
		source_lds_tx_log.amount = 0
		source_lds_tx_log.access = "PUBLIC" # "PUBLIC" OR "PRIVATE"
		source_lds_tx_log.description = lstr_source_tx_description 
		source_lds_tx_log.memo = ""
		source_lds_tx_log.user_id_created = lds_source.user_id
		source_lds_tx_log.network_id = fint_network_id
		source_lds_tx_log.account_id = fint_source_account_id
		source_lds_tx_log.source_account = fint_source_account_id 
		source_lds_tx_log.target_account = fint_target_account_id
		source_lds_tx_log.put()

		lds_target.tx_index += 1
		# target transaction log
		target_tx_log_key = ndb.Key("MRTX%s%s%s", (key_part1,key_part3,str(lds_target.tx_index).zfill(12)))
		target_lds_tx_log = ds_mr_tx_log()
		target_lds_tx_log.key = target_tx_log_key
		target_lds_tx_log.category = "MRTX" # GENERAL TRANSACTION GROUPING
		# tx_index should be based on incremented metric_account value
		target_lds_tx_log.tx_index = lds_target.tx_index
		target_lds_tx_log.tx_type = lstr_target_tx_type # SHORT WORD(S) FOR WHAT TRANSACTION DID
		target_lds_tx_log.amount = 0
		# typically we'll make target private for bilateral transactions so that
		# when looking at a system view, we don't see duplicates.
		target_lds_tx_log.access = "PRIVATE" # "PUBLIC" OR "PRIVATE"
		target_lds_tx_log.description = lstr_target_tx_description 
		target_lds_tx_log.memo = ""
		target_lds_tx_log.user_id_created = lds_source.user_id
		target_lds_tx_log.network_id = fint_network_id
		target_lds_tx_log.account_id = fint_target_account_id
		target_lds_tx_log.source_account = fint_source_account_id 
		target_lds_tx_log.target_account = fint_target_account_id
		target_lds_tx_log.put()
		
		lds_source.put()
		lds_target.put()
		return lstr_return_message
			
	@ndb.transactional(xg=True)
	def _disconnect(self, fint_network_id, fint_source_account_id, fint_target_account_id):
	
	
		# STUB we need to remove any reserve transfer requests when disconnecting
		
		key_part1 = str(fint_network_id).zfill(8)
		key_part2 = str(fint_source_account_id).zfill(12)
		key_part3 = str(fint_target_account_id).zfill(12)
		source_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part2))
		lds_source = source_key.get()
		
		# error if source doesn't exist
		if lds_source is None: return "error_source_id_not_valid"
		# error if trying to disconnect from self
		if fint_source_account_id == fint_target_account_id: return "error_cant_disconnect_from_self"
		
		target_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part3))
		lds_target = target_key.get()
		
		# error if target doesn't exist
		if lds_target is None: return "error_target_id_not_valid"
		
		# Disconnect() can do one of three things:
		#
		# 1. Cancel an incoming connection request
		# 2. Cancel an outgoing connection request
		# 3. Cancel an existing connection
		#
		# None of these three situations can exist simultaneously.  And if none of
		# the three cases apply, then the request to disconnect is invalid.
		#
		# 1 & 2 are benign changes and don't effect the graph, but cancelling an
		# existing connection will require a graph process time window check.
		
		if fint_target_account_id in lds_source.incoming_connection_requests:
		
			# benign change with respect to graph
			lds_source.incoming_connection_requests.remove(fint_target_account_id)
			lds_target.outgoing_connection_requests.remove(fint_source_account_id)
			lstr_source_tx_type = "INCOMING CONNECTION REQUEST DENIED"
			lstr_source_tx_description = "INCOMING CONNECTION REQUEST DENIED"
			lstr_target_tx_type = "OUTGOING CONNECTION REQUEST DENIED"
			lstr_target_tx_description = "OUTGOING CONNECTION REQUEST DENIED"
			
			lstr_return_message = "success_denied_target_connection_request"
		
		elif fstr_target_account_id in lds_source.outgoing_connection_requests:
		
			# benign change with respect to graph
			lds_target.incoming_connection_requests.remove(fint_source_account_id)
			lds_source.outgoing_connection_requests.remove(fint_target_account_id)
			lstr_source_tx_type = "OUTGOING CONNECTION REQUEST WITHDRAWN"
			lstr_source_tx_description = "OUTGOING CONNECTION REQUEST WITHDRAWN"
			lstr_target_tx_type = "INCOMING CONNECTION REQUEST WITHDRAWN"
			lstr_target_tx_description = "INCOMING CONNECTION REQUEST WITHDRAWN"
			lstr_return_message = "success_withdrew_connection_request"
		
		elif fint_target_account_id in lds_source.current_connections:
		
			# First thing we need to do-and probably should abstract this later STUB
			# since we will need in other places-is we need to figure out our cutoff
			# time for "current_timestamp" based on graph processing frequency.
			#
			# My basic idea is to subtract the frequencies modulus since epoch time
			# (which I'm arbitralily making 8am UTC March 13th, 2017) from the current
			# datetime.  We'll set frequency in minutes but convert to seconds since
			# that's what timedelta uses in python.
			
			t_now = datetime.datetime.now()
			d_since = t_now - T_EPOCH
			# this requests cutoff time
			t_cutoff = t_now - datetime.timedelta(seconds=(d_since.total_seconds() % (GRAPH_FREQUENCY_MINUTES * 60)))
		
			# update the source account
			if lds_source.current_timestamp > t_cutoff:
				
				# last transaction was in current time window, no need to swap
				# a.k.a. overwrite current
				lds_source.current_connections.remove(fint_target_account_id)
				
			else:
			
				# last transaction was in previous time window, swap
				# a.k.a. move "old" current into "last" before overwriting
				lds_source.last_connections = lds_source.current_connections
				lds_source.last_reserve_balance = lds_source.current_reserve_balance
				lds_source.last_network_balance = lds_source.current_network_balance
				lds_source.current_connections.remove(fint_target_account_id)				
	
			# update the target account
			if lds_target.current_timestamp > t_cutoff:
				
				# last transaction was in current time window, no need to swap
				# a.k.a. overwrite current
				lds_target.current_connections.remove(fint_source_account_id)
				
			else:
			
				# last transaction was in previous time window, swap
				# a.k.a. move "old" current into "last" before overwriting
				lds_target.last_connections = lds_target.current_connections
				lds_target.last_reserve_balance = lds_target.current_reserve_balance
				lds_target.last_network_balance = lds_target.current_network_balance
				lds_target.current_connections.remove(fint_source_account_id)
				
			# only update current_timestamp for graph dependent transactions??? STUB
			lds_source.current_timestamp = datetime.datetime.now()
			lds_target.current_timestamp = datetime.datetime.now()
			lstr_source_tx_type = "DISCONNECTION BY THIS ACCOUNT"
			lstr_source_tx_description = "DISCONNECTION BY THIS ACCOUNT"
			lstr_target_tx_type = "DISCONNECTION BY OTHER ACCOUNT"
			lstr_target_tx_description = "DISCONNECTION BY OTHER ACCOUNT"
			lstr_return_message = "success_cancelled_connection"
			
		else: return "error_nothing_to_disconnect"

		# ADD TWO TRANSACTIONS LIKE CONNECT()
		lds_source.tx_index += 1
		# source transaction log
		source_tx_log_key = ndb.Key("MRTX%s%s%s", (key_part1, key_part2,str(lds_source.tx_index).zfill(12)))
		source_lds_tx_log = ds_mr_tx_log()
		source_lds_tx_log.key = source_tx_log_key
		source_lds_tx_log.category = "MRTX" # GENERAL TRANSACTION GROUPING
		# tx_index should be based on incremented metric_account value
		source_lds_tx_log.tx_index = lds_source.tx_index
		source_lds_tx_log.tx_type = lstr_source_tx_type # SHORT WORD(S) FOR WHAT TRANSACTION DID
		source_lds_tx_log.amount = 0
		source_lds_tx_log.access = "PUBLIC" # "PUBLIC" OR "PRIVATE"
		source_lds_tx_log.description = lstr_source_tx_description 
		source_lds_tx_log.memo = ""
		source_lds_tx_log.user_id_created = lds_source.user_id
		source_lds_tx_log.network_id = fint_network_id
		source_lds_tx_log.account_id = fint_source_account_id
		source_lds_tx_log.source_account = fint_source_account_id 
		source_lds_tx_log.target_account = fint_target_account_id
		source_lds_tx_log.put()

		lds_target.tx_index += 1
		# target transaction log
		target_tx_log_key = ndb.Key("MRTX%s%s%s", (key_part1, key_part3,str(lds_target.tx_index).zfill(12)))
		target_lds_tx_log = ds_mr_tx_log()
		target_lds_tx_log.key = target_tx_log_key
		target_lds_tx_log.category = "MRTX" # GENERAL TRANSACTION GROUPING
		# tx_index should be based on incremented metric_account value
		target_lds_tx_log.tx_index = lds_target.tx_index
		target_lds_tx_log.tx_type = lstr_target_tx_type # SHORT WORD(S) FOR WHAT TRANSACTION DID
		target_lds_tx_log.amount = 0
		# typically we'll make target private for bilateral transactions so that
		# when looking at a system view, we don't see duplicates.
		target_lds_tx_log.access = "PRIVATE" # "PUBLIC" OR "PRIVATE"
		target_lds_tx_log.description = lstr_target_tx_description 
		target_lds_tx_log.memo = ""
		target_lds_tx_log.user_id_created = lds_source.user_id
		target_lds_tx_log.network_id = fint_network_id
		target_lds_tx_log.account_id = fint_target_account_id
		target_lds_tx_log.source_account = fint_source_account_id 
		target_lds_tx_log.target_account = fint_target_account_id
		target_lds_tx_log.put()

		lds_source.put()
		lds_target.put()
		return lstr_return_message

	@ndb.transactional(xg=True)
	def _modify_reserve(self, fint_network_id, fint_source_account_id, fstr_type, fstr_amount):

		# First, get the source account.
		key_part1 = str(fint_network_id).zfill(8)
		key_part2 = str(fint_source_account_id).zfill(12)
		source_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part2))
		lds_source = source_key.get()
		
		# error if source doesn't exist
		if lds_source is None: return "error_source_id_not_valid"
		
		# Second, let's make sure the number passed is valid.
		#
		# Keep in mind, we're passing it in as a string.
		# Also, we use integers to represent decimals.  The integer 100000 equals $1 of value.
		# This hopefully will provide ample room to represent large and small values.  At the 
		# time of this writing the smallest amount Bitcoin could represent given a price of 
		# $1254.97 per BTC would be around 1/100,000th of a dollar.
		# a 64 bit integer stored in the NDB datastore can be up to 9,223,372,036,854,775,807
		# so our upper limit (without making minor changes to fix it that is) would be 
		# 92,233,720,368,547.75807...92 trillion.  Unlike Bitcoin, this is a per account balance.
		# And as I will be discussing, this amount of liquidity is really ludicrous to begin with
		# so we should be fine.
		try:
			lint_amount = int(float(fstr_amount)*100000)
		except ValueError, ex:
			return "error_invalid_amount_passed"
		
		# make sure amount isn't over the maximum
		if lint_amount > MAX_RESERVE_MODIFY: return "error_amount_exceeds_maximum_allowed"
		
		# if we don't modify one or the other, "new" will be previous
		lint_new_balance = lds_source.current_network_balance
		lint_new_reserve = lds_source.current_reserve_balance		
		
		# 4 types of reserve modifications are possible
		if fstr_type == "normal_add":		
		
			# 1.  Normal Add
			# User is essentially depositing money.  This will add to their reserve
			# amount, also adding to reserve total(shard), also adds to network balance and
			# network total(shard).
			lint_new_balance = lds_source.current_network_balance + lint_amount
			lint_new_reserve = lds_source.current_reserve_balance + lint_amount
			
			# increment positive balance shard
			lint_shard_string_index = str(random.randint(0, NUM_BALANCE_POSITIVE_SHARDS - 1))
			lds_counter1 = ds_mr_positive_balance_shard.get_by_id(lint_shard_string_index)
			if lds_counter1 is None:
				lds_counter1 = ds_mr_positive_balance_shard(id=lint_shard_string_index)
			lds_counter1.count += lint_amount
			lds_counter1.put()
			
			# increment positive reserve shard
			lint_shard_string_index = str(random.randint(0, NUM_RESERVE_POSITIVE_SHARDS - 1))
			lds_counter2 = ds_mr_positive_reserve_shard.get_by_id(lint_shard_string_index)
			if lds_counter2 is None:
				lds_counter2 = ds_mr_positive_reserve_shard(id=lint_shard_string_index)
			lds_counter2.count += lint_amount
			lds_counter2.put()
			
			lstr_source_tx_type = "RESERVE MODIFIED NORMAL ADD"
			lstr_source_tx_description = "RESERVE MODIFIED NORMAL ADD"
			lstr_return_message = "success_reserve_normal_add"

		elif fstr_type == "normal_subtract":
		
			# 2.  Normal Subtract
			# User is withdrawing money via reserves.  Opposite of Normal Add with respect
			# to individual and system totals.  User cannot take reserve balance below zero
			# and cannot withdraw more reserves than they have network balance.
			if lint_amount > lds_source.current_network_balance:
				return "error_cannot_withdraw_reserves_exceeding_balance"
			if lint_amount > lds_source.current_reserve_balance:
				return "error_cannot withdraw_more_reserves_than_exist"
			lint_new_balance = lds_source.current_network_balance - lint_amount
			lint_new_reserve = lds_source.current_reserve_balance - lint_amount
			
			# increment negative balance shard
			lint_shard_string_index = str(random.randint(0, NUM_BALANCE_NEGATIVE_SHARDS - 1))
			lds_counter3 = ds_mr_negative_balance_shard.get_by_id(lint_shard_string_index)
			if lds_counter3 is None:
				lds_counter3 = ds_mr_negative_balance_shard(id=lint_shard_string_index)
			lds_counter3.count += lint_amount
			lds_counter3.put()
			
			# increment negative reserve shard
			lint_shard_string_index = str(random.randint(0, NUM_RESERVE_NEGATIVE_SHARDS - 1))
			lds_counter4 = ds_mr_negative_reserve_shard.get_by_id(lint_shard_string_index)
			if lds_counter4 is None:
				lds_counter4 = ds_mr_negative_reserve_shard(id=lint_shard_string_index)
			lds_counter4.count += lint_amount
			lds_counter4.put()
			
			lstr_source_tx_type = "RESERVE MODIFIED NORMAL SUBTRACT"
			lstr_source_tx_description = "RESERVE MODIFIED NORMAL SUBTRACT"
			lstr_return_message = "success_reserve_normal_subtract"
			
		elif fstr_type == "override_add":

			# 3.  Override Add
			# Found money, donation, etc.  Adds to reserves for this user without adding to
			# their network balance or the system balance.  Only adds to reserve balance.
			lint_new_reserve = lds_source.current_reserve_balance + lint_amount
			# increment positive reserve shard
			lint_shard_string_index = str(random.randint(0, NUM_RESERVE_POSITIVE_SHARDS - 1))
			lds_counter5 = ds_mr_positive_reserve_shard.get_by_id(lint_shard_string_index)
			if lds_counter5 is None:
				lds_counter5 = ds_mr_positive_reserve_shard(id=lint_shard_string_index)
			lds_counter5.count += lint_amount
			lds_counter5.put()
			
			lstr_source_tx_type = "RESERVE MODIFIED OVERRIDE ADD"
			lstr_source_tx_description = "RESERVE MODIFIED OVERRIDE ADD"
			lstr_return_message = "success_reserve_override_add"
			
		elif fstr_type == "override_subtract":
		
			# 4.  Override Subtract
			# Lost money, etc.  User cannot subtract more reserves than they had.  Does not
			# update network individual or system balance.
			lint_new_reserve = lds_source.current_reserve_balance - lint_amount
			# increment negative reserve shard
			lint_shard_string_index = str(random.randint(0, NUM_RESERVE_NEGATIVE_SHARDS - 1))
			lds_counter6 = ds_mr_negative_reserve_shard.get_by_id(lint_shard_string_index)
			if lds_counter6 is None:
				lds_counter6 = ds_mr_negative_reserve_shard(id=lint_shard_string_index)
			lds_counter6.count += lint_amount
			lds_counter6.put()
			
			lstr_source_tx_type = "RESERVE MODIFIED OVERRIDE SUBTRACT"
			lstr_source_tx_description = "RESERVE MODIFIED OVERRIDE SUBTRACT"
			lstr_return_message = "success_reserve_override_subtract"
			
		else: return "error_invalid_transaction_type"
		
		# If we're here, then we modified something, so need to do 
		# graph process time window check before saving data. Reserve
		# modification always effects the graph state.
		
		# First thing we need to do-and probably should abstract this later STUB
		# since we will need in other places-is we need to figure out our cutoff
		# time for "current_timestamp" based on graph processing frequency.
		#
		# My basic idea is to subtract the frequencies modulus since epoch time
		# (which I'm arbitralily making 8am UTC March 13th, 2017) from the current
		# datetime.  We'll set frequency in minutes but convert to seconds since
		# that's what timedelta uses in python.

		t_now = datetime.datetime.now()
		d_since = t_now - T_EPOCH
		# this requests cutoff time
		t_cutoff = t_now - datetime.timedelta(seconds=(d_since.total_seconds() % (GRAPH_FREQUENCY_MINUTES * 60)))
		
		# update the source account
		if lds_source.current_timestamp > t_cutoff:

			# last transaction was in current time window, no need to swap
			# a.k.a. overwrite current
			lds_source.current_network_balance = lint_new_balance
			lds_source.current_reserve_balance = lint_new_reserve

		else:

			# last transaction was in previous time window, swap
			# a.k.a. move "old" current into "last" before overwriting
			lds_source.last_connections = lds_source.current_connections
			lds_source.last_reserve_balance = lds_source.current_reserve_balance
			lds_source.last_network_balance = lds_source.current_network_balance
			lds_source.current_network_balance = lint_new_balance
			lds_source.current_reserve_balance = lint_new_reserve

		lds_source.tx_index += 1
		# source transaction log
		tx_log_key = ndb.Key("MRTX%s%s%s", (key_part1, key_part2,str(lds_source.tx_index).zfill(12)))
		lds_tx_log = ds_mr_tx_log()
		lds_tx_log.key = tx_log_key
		lds_tx_log.category = "MRTX" # GENERAL TRANSACTION GROUPING
		# tx_index should be based on incremented metric_account value
		lds_tx_log.tx_index = lds_source.tx_index
		lds_tx_log.tx_type = lstr_source_tx_type # SHORT WORD(S) FOR WHAT TRANSACTION DID
		lds_tx_log.amount = lint_amount
		lds_tx_log.access = "PUBLIC" # "PUBLIC" OR "PRIVATE"
		lds_tx_log.description = lstr_source_tx_description 
		lds_tx_log.memo = ""
		lds_tx_log.user_id_created = lds_source.user_id
		lds_tx_log.network_id = fint_network_id
		lds_tx_log.account_id = fint_source_account_id
		lds_tx_log.source_account = fint_source_account_id 
		lds_tx_log.target_account = ""
		lds_tx_log.put()
		
		# only update current_timestamp for graph dependent transactions??? STUB
		lds_source.current_timestamp = datetime.datetime.now()
		lds_source.put()
		return lstr_return_message

	@ndb.transactional(xg=True)
	def _make_payment(self, fint_network_id, fint_source_account_id, fint_target_account_id, fstr_amount):
	
		# make a payment
		# transfer network balance from one user to another
		# this does not affect our global balance counters
				
		# get the source and target metric accounts
		
		key_part1 = str(fint_network_id).zfill(8)
		key_part2 = str(fint_source_account_id).zfill(12)
		key_part3 = str(fint_target_account_id).zfill(12)
		source_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part2))
		lds_source = source_key.get()
		
		# error if source doesn't exist
		if lds_source is None: return "error_source_id_not_valid"
		# error if trying to connect to self
		if fint_source_account_id == fint_target_account_id: return "error_cant_pay_self"
		
		target_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part3))
		lds_target = target_key.get()
		
		# error if target doesn't exist
		if lds_target is None: return "error_target_id_not_valid"
		# make sure fstr_amount actually is an integer
		try:
			lint_amount = int(float(fstr_amount)*100000)
		except ValueError, ex:
			return "error_invalid_amount_passed"
		# STUB make sure all lint_amount inputs are greater than 0
		# can't pay if you don't have that much
		if lds_source.current_network_balance < lint_amount: return "error_not_enough_balance_to_make_payment"
		# can't exceed maximum allowed payment
		if lint_amount > MAX_PAYMENT: return "error_amount_exceeds_maximum_allowed"
		
		# So everything checks out, payments are probably simplest things to do.
		# We do count network balances as "graph affecting" even though the algorithms
		# don't deal with balances (yet).  It's still an important summarized statistic
		# so we will check the cutoff time as with other graph affecting functions.
		
		# calculate cutoff time
		t_now = datetime.datetime.now()
		d_since = t_now - T_EPOCH
		# this requests cutoff time
		t_cutoff = t_now - datetime.timedelta(seconds=(d_since.total_seconds() % (GRAPH_FREQUENCY_MINUTES * 60)))
		
		# update the source account
		if lds_source.current_timestamp > t_cutoff:

			# last transaction was in current time window, no need to swap
			# a.k.a. overwrite current
			lds_source.current_network_balance -= lint_amount

		else:

			# last transaction was in previous time window, swap
			# a.k.a. move "old" current into "last" before overwriting
			lds_source.last_connections = lds_source.current_connections
			lds_source.last_reserve_balance = lds_source.current_reserve_balance
			lds_source.last_network_balance = lds_source.current_network_balance
			lds_source.current_network_balance -= lint_amount				

		# update the target account
		if lds_target.current_timestamp > t_cutoff:

			# last transaction was in current time window, no need to swap
			# a.k.a. overwrite current
			lds_target.current_network_balance += lint_amount

		else:

			# last transaction was in previous time window, swap
			# a.k.a. move "old" current into "last" before overwriting
			lds_target.last_connections = lds_target.current_connections
			lds_target.last_reserve_balance = lds_target.current_reserve_balance
			lds_target.last_network_balance = lds_target.current_network_balance
			lds_target.current_network_balance += lint_amount

		# only update current_timestamp for graph dependent transactions??? STUB
		lds_source.current_timestamp = datetime.datetime.now()
		lds_target.current_timestamp = datetime.datetime.now()
		
		# ADD TWO TRANSACTIONS LIKE CONNECT()
		lds_source.tx_index += 1
		# source transaction log
		source_tx_log_key = ndb.Key("MRTX%s%s%s", (key_part1, key_part2,str(lds_source.tx_index).zfill(12)))
		source_lds_tx_log = ds_mr_tx_log()
		source_lds_tx_log.key = source_tx_log_key
		source_lds_tx_log.category = "MRTX" # GENERAL TRANSACTION GROUPING
		# tx_index should be based on incremented metric_account value
		source_lds_tx_log.tx_index = lds_source.tx_index
		source_lds_tx_log.tx_type = "PAYMENT MADE" # SHORT WORD(S) FOR WHAT TRANSACTION DID
		source_lds_tx_log.amount = lint_amount
		source_lds_tx_log.access = "PUBLIC" # "PUBLIC" OR "PRIVATE"
		source_lds_tx_log.description = "PAYMENT MADE" 
		source_lds_tx_log.memo = ""
		source_lds_tx_log.user_id_created = lds_source.user_id
		source_lds_tx_log.network_id = fint_network_id
		source_lds_tx_log.account_id = fint_source_account_id
		source_lds_tx_log.source_account = fint_source_account_id 
		source_lds_tx_log.target_account = fint_target_account_id
		source_lds_tx_log.put()

		lds_target.tx_index += 1
		# target transaction log
		target_tx_log_key = ndb.Key("MRTX%s%s%s", (key_part1, key_part3,str(lds_target.tx_index).zfill(12)))
		target_lds_tx_log = ds_mr_tx_log()
		target_lds_tx_log.key = target_tx_log_key
		target_lds_tx_log.category = "MRTX" # GENERAL TRANSACTION GROUPING
		# tx_index should be based on incremented metric_account value
		target_lds_tx_log.tx_index = lds_target.tx_index
		target_lds_tx_log.tx_type = "PAYMENT RECEIVED" # SHORT WORD(S) FOR WHAT TRANSACTION DID
		target_lds_tx_log.amount = lint_amount
		# typically we'll make target private for bilateral transactions so that
		# when looking at a system view, we don't see duplicates.
		target_lds_tx_log.access = "PRIVATE" # "PUBLIC" OR "PRIVATE"
		target_lds_tx_log.description = "PAYMENT RECEIVED" 
		target_lds_tx_log.memo = ""
		target_lds_tx_log.user_id_created = lds_source.user_id
		target_lds_tx_log.network_id = fint_network_id
		target_lds_tx_log.account_id = fint_target_account_id
		target_lds_tx_log.source_account = fint_source_account_id 
		target_lds_tx_log.target_account = fint_target_account_id
		target_lds_tx_log.put()
		
		lds_source.put()
		lds_target.put()
		return "success_payment_succeeded"

	@ndb.transactional(xg=True)
	def _process_reserve_transfer(self, fint_network_id, fint_source_account_id, fint_target_account_id, fstr_amount, fstr_type):
	
		# A "reserve transfer" is just what I'm calling a bilateral agreement to move
		# some amount of reserve balance from an account with a positive amount equal
		# to or greater than the reserve transfer amount, to some other account.
		#
		# It functions very similar to a connection in that one account will "request" the
		# reserve transfer, basically requesting that the transfer take place, but the transfer
		# will not be finalized, by actually updating the balances in each account until the
		# corresponding account "authorizes" the reserve transfer. Once the reserve transfer is authorized
		# both accounts will be updated.  
		#
		# Only one reserve transfer can exist per connection.  If a user requests a new one when an
		# old one already exists, the old one is cancelled automatically.  "Suggested" reserve transfers
		# that are created by the system do not get cancelled.  Ideally, user created reserve transfers
		# will be at a minimum overall, since the graph process is designed to suggest reserve transfers
		# that balance out the network as a whole.		
		
		key_part1 = str(fint_network_id).zfill(8)
		key_part2 = str(fint_source_account_id).zfill(12)
		key_part3 = str(fint_target_account_id).zfill(12)
		source_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part2))
		lds_source = source_key.get()
		
		# error if source doesn't exist
		if lds_source is None: return "error_source_id_not_valid"
		# error if trying to write check to self
		if fint_source_account_id == fint_target_account_id: return "error_source_and_target_ids_cannot_be_the_same"
		
		target_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part3))
		lds_target = target_key.get()
		
		# error if target doesn't exist
		if lds_target is None: return "error_target_id_not_valid"

		# make sure fstr_amount actually is an integer
		try:
			lint_amount = int(float(fstr_amount)*100000)
		except ValueError, ex:
			return "error_invalid_amount_passed"
			
		if not fint_target_account_id in lds_source.current_connections: return "error_source_and_target_not_connected"
		
		# We don't do a lot of checks on the requesting a transfer side, because graph state changes, and users may
		# be writing transfer requests in anticipation of balance updates.  So we only do the main checks when we
		# actually try to authorize a reserve transfer.
		
		if fstr_type == "storing_suggested":		
			
			# This is a new suggestion from the graph process.  If any previous exist 
			# that are in the inactive queue, delete them.
			lds_source.suggested_inactive_incoming_reserve_transfer_requests.pop(fint_target_account_id,None)
			lds_source.suggested_inactive_outgoing_reserve_transfer_requests.pop(fint_target_account_id,None)
			lds_target.suggested_inactive_incoming_reserve_transfer_requests.pop(fint_source_account_id,None)
			lds_target.suggested_inactive_outgoing_reserve_transfer_requests.pop(fint_source_account_id,None)
			# create new request
			lds_source.suggested_inactive_outgoing_reserve_transfer_requests[fint_target_account_id] = lint_amount
			lds_target.suggested_inactive_incoming_reserve_transfer_requests[fint_source_account_id] = lint_amount
			
			lstr_source_tx_type = "SUGGESTED OUTGOING RESERVE TRANSFER STORED"
			lstr_source_tx_description = "SUGGESTED OUTGOING RESERVE TRANSFER STORED"
			lstr_target_tx_type = "SUGGESTED INCOMING RESERVE TRANSFER STORED"
			lstr_target_tx_description = "SUGGESTED INCOMING RESERVE TRANSFER STORED"
			lstr_return_message = "success_suggested_reserve_transfer_stored"

		elif fstr_type == "activating_suggested":
			
			# We're "activating" a suggested one.  So we move it to active queue.  This let's
			# the other party know that they can authorize it.  But it's the web, so need to
			# make sure that inactive request still exists
			if not fint_target_account_id in lds_source.suggested_inactive_outgoing_reserve_transfer_requests:
				return "error_activation_request_has_no_inactive_match_on_id"
			# ...and has the same amount
			if not lint_amount == lds_source.suggested_inactive_outgoing_reserve_transfer_requests[fint_target_account_id]:
				return "error_activation_request_has_no_inactive_match_on_amount"
			# before inactive can be moved to active, any old activated, suggested transfers must be
			# either cancelled or completed.  We don't automatically cancel an active one since it may
			# be in process.
			if fint_target_account_id in lds_source.suggested_active_incoming_reserve_transfer_requests:
				return "error_active_must_be_completed_or_cancelled_before_new_activation"
			if fint_target_account_id in lds_source.suggested_active_outgoing_reserve_transfer_requests:
				return "error_active_must_be_completed_or_cancelled_before_new_activation"
				
			# request is valid
			# move inactive to active, leaving inactive empty
			lds_source.suggested_inactive_incoming_reserve_transfer_requests.pop(fint_target_account_id,None)
			lds_source.suggested_inactive_outgoing_reserve_transfer_requests.pop(fint_target_account_id,None)
			lds_target.suggested_inactive_incoming_reserve_transfer_requests.pop(fint_source_account_id,None)
			lds_target.suggested_inactive_outgoing_reserve_transfer_requests.pop(fint_source_account_id,None)
			# create new request
			lds_source.suggested_active_outgoing_reserve_transfer_requests[fint_target_account_id] = lint_amount
			lds_target.suggested_active_incoming_reserve_transfer_requests[fint_source_account_id] = lint_amount
			
			lstr_source_tx_type = "SUGGESTED OUTGOING RESERVE TRANSFER ACTIVATED"
			lstr_source_tx_description = "SUGGESTED OUTGOING RESERVE TRANSFER ACTIVATED"
			lstr_target_tx_type = "SUGGESTED INCOMING RESERVE TRANSFER ACTIVATED"
			lstr_target_tx_description = "SUGGESTED INCOMING RESERVE TRANSFER ACTIVATED"
			lstr_return_message = "success_suggested_reserve_transfer_activated"
			
		elif fstr_type == "deactivating_suggested":
		
			# This is similar to a "disconnect()".  Once a suggested transfer is active, either
			# party to it, can deny/withdraw it.  The special case here, is that if the inactive
			# suggested slot is empty, we move this one back to it.  If not, we simply delete it
			# as the system has already suggested a new one.
			
			# source is always the one doing the action, let's see which situation we're in first
			if fint_target_account_id in lds_source.suggested_active_outgoing_reserve_transfer_requests:
				
				# we are deactiving our own activation
				# verify amount
				if not lint_amount == lds_source.suggested_active_outgoing_reserve_transfer_requests[fint_target_account_id]:
					return "error_deactivation_request_has_no_active_match_on_amount"
				# if inactive slot is empty, we move before deleting otherwise just delete
				if not fint_target_account_id in lds_source.suggested_inactive_outgoing_reserve_transfer_requests:
					if not fint_target_account_id in lds_source.suggested_inactive_incoming_reserve_transfer_requests:
						# ok to copy back to inactive
						lds_source.suggested_inactive_outgoing_reserve_transfer_requests[fint_target_account_id] = lint_amount
						lds_target.suggested_inactive_incoming_reserve_transfer_requests[fint_source_account_id] = lint_amount
				# delete the suggested active entries
				lds_source.suggested_active_outgoing_reserve_transfer_requests.pop(fint_target_account_id,None)
				lds_target.suggested_active_incoming_reserve_transfer_requests.pop(fint_source_account_id,None)
				
				lstr_source_tx_type = "SUGGESTED OUTGOING RESERVE TRANSFER DEACTIVATED"
				lstr_source_tx_description = "SUGGESTED OUTGOING RESERVE TRANSFER DEACTIVATED"
				lstr_target_tx_type = "SUGGESTED INCOMING RESERVE TRANSFER DEACTIVATED"
				lstr_target_tx_description = "SUGGESTED INCOMING RESERVE TRANSFER DEACTIVATED"
				lstr_return_message = "success_suggested_reserve_transfer_deactivated"
			
			elif fint_target_account_id in lds_source.suggested_active_incoming_reserve_transfer_requests:
			
				# we are denying the targets activation
				# verify amount
				if not lint_amount == lds_source.suggested_active_incoming_reserve_transfer_requests[fint_target_account_id]:
					return "error_denial_request_has_no_active_match_on_amount"
				# if inactive slot is empty, we move before deleting otherwise just delete
				if not fint_target_account_id in lds_source.suggested_inactive_outgoing_reserve_transfer_requests:
					if not fint_target_account_id in lds_source.suggested_inactive_incoming_reserve_transfer_requests:
						# ok to copy back to inactive
						lds_source.suggested_inactive_incoming_reserve_transfer_requests[fint_target_account_id] = lint_amount
						lds_target.suggested_inactive_outgoing_reserve_transfer_requests[fint_source_account_id] = lint_amount
				# delete the suggested active entries
				lds_source.suggested_active_incoming_reserve_transfer_requests.pop(fint_target_account_id,None)
				lds_target.suggested_active_outgoing_reserve_transfer_requests.pop(fint_source_account_id,None)
				
				lstr_source_tx_type = "SUGGESTED INCOMING RESERVE TRANSFER DENIED"
				lstr_source_tx_description = "SUGGESTED INCOMING RESERVE TRANSFER DENIED"
				lstr_target_tx_type = "SUGGESTED OUTGOING RESERVE TRANSFER DENIED"
				lstr_target_tx_description = "SUGGESTED OUTGOING RESERVE TRANSFER DENIED"
				lstr_return_message = "success_suggested_reserve_transfer_denied"
			
			else: return "error_no_suggested_active_request_between_source_and_target"		
		
		elif fstr_type == "requesting_user":
		
			# new outgoing transfer request from source
			# must complete or cancel old ones before making a new one
			if fint_target_account_id in lds_source.incoming_reserve_transfer_requests:
				return "error_existing_transfer_requests_must_be_completed_or_cancelled_before_creating_new_one"
			if fstr_target_account_id in lds_source.outgoing_reserve_transfer_requests:
				return "error_existing_transfer_requests_must_be_completed_or_cancelled_before_creating_new_one"
			# create new request
			lds_source.outgoing_reserve_transfer_requests[fint_target_account_id] = lint_amount
			lds_target.incoming_reserve_transfer_requests[fint_source_account_id] = lint_amount
			
			lstr_source_tx_type = "USER OUTGOING RESERVE TRANSFER REQUESTED"
			lstr_source_tx_description = "USER OUTGOING RESERVE TRANSFER REQUESTED"
			lstr_target_tx_type = "USER INCOMING RESERVE TRANSFER REQUESTED"
			lstr_target_tx_description = "USER INCOMING RESERVE TRANSFER REQUESTED"
			lstr_return_message = "success_user_reserve_transfer_requested"
			
		elif fstr_type == "cancelling_user":
			
			# creator of a transfer request is cancelling
			# verify source actually has an outgoing for correct amount and if so delete it
			if fint_target_account_id in lds_source.outgoing_reserve_transfer_requests:
				if not lint_amount == lds_source.outgoing_reserve_transfer_requests[fint_target_account_id]:
					return "error_cancellation_request_does_not_match_outgoing_amount"
			else: return "error_cancel_request_does_not_have_match_in_outgoing_requests_for_source"
			# delete the transfer request in question
			lds_source.outgoing_reserve_transfer_requests.pop(fint_target_account_id,None)
			lds_target.incoming_reserve_transfer_requests.pop(fint_source_account_id,None)
			
			lstr_source_tx_type = "USER OUTGOING RESERVE TRANSFER WITHDRAWN"
			lstr_source_tx_description = "USER OUTGOING RESERVE TRANSFER WITHDRAWN"
			lstr_target_tx_type = "USER INCOMING RESERVE TRANSFER WITHDRAWN"
			lstr_target_tx_description = "USER INCOMING RESERVE TRANSFER WITHDRAWN"
			lstr_return_message = "success_user_reserve_transfer_cancelled"

		elif fstr_type == "denying_user":
			
			# source is denying targets requested transfer
			# verify source actually has an incoming request for correct amount and if so delete it
			if fint_target_account_id in lds_source.incoming_reserve_transfer_requests:
				if not lint_amount == lds_source.incoming_reserve_transfer_requests[fint_target_account_id]:
					return "error_cancellation_request_does_not_match_incoming_amount"
			else: return "error_cancel_request_does_not_have_match_in_incoming_requests_for_source"
			# delete the transfer request in question
			lds_source.incoming_reserve_transfer_requests.pop(fint_target_account_id,None)
			lds_target.outgoing_reserve_transfer_requests.pop(fint_source_account_id,None)
			
			lstr_source_tx_type = "USER INCOMING RESERVE TRANSFER DENIED"
			lstr_source_tx_description = "USER INCOMING RESERVE TRANSFER DENIED"
			lstr_target_tx_type = "USER OUTGOING RESERVE TRANSFER DENIED"
			lstr_target_tx_description = "USER OUTGOING RESERVE TRANSFER DENIED"
			lstr_return_message = "success_user_reserve_transfer_denied"
		
		elif fstr_type == "authorizing_suggested":

			# This transaction type is one which affects the graph.
			# "authorizing_suggested" pretty much works exactly like "authorizing_user" except that we will
			# put this request back in the suggested_inactive slot if it is blank just like we did for 
			# deactivate and deny.
			
			# Again, authorization is always an incoming request with respect to the source account.

			# From the initial checks in this function we already know:
			# 1. source and target accounts are valid
			# 2. source id and target id are different
			# 3. amount is valid
			# 4. source and target are connected
			
			# make sure still an incoming suggested request from the target
			if not fint_target_account_id in lds_source.suggested_active_incoming_reserve_transfer_requests:
				return "error_no_request_in_active_suggested_incoming_for_target"
			# make sure it's the same amount
			if not lds_source.suggested_active_incoming_reserve_transfer_requests[fint_target_account_id] == lint_amount:
				return "error_authorization_amount_does_not_match_incoming_request"
			# make sure target still has enough to pay
			if not lds_target.current_reserve_balance > lint_amount: return "error_target_has_insufficient_reserves_for_transfer"			
			
			# calculate cutoff time
			t_now = datetime.datetime.now()
			d_since = t_now - T_EPOCH
			# this requests cutoff time
			t_cutoff = t_now - datetime.timedelta(seconds=(d_since.total_seconds() % (GRAPH_FREQUENCY_MINUTES * 60)))
			
			# update the source account last/current
			if not lds_source.current_timestamp > t_cutoff:
			
				# last transaction was in previous time window, swap
				# a.k.a. move "old" current into "last" before overwriting
				lds_source.last_connections = lds_source.current_connections
				lds_source.last_reserve_balance = lds_source.current_reserve_balance
				lds_source.last_network_balance = lds_source.current_network_balance
			
			# update the source account
			# delete the incoming request and add to reserve balance
			lds_source.suggested_active_incoming_reserve_transfer_requests.pop(fint_target_account_id,None)
			lds_source.current_reserve_balance += lint_amount
			lds_source.current_timestamp = datetime.datetime.now()

			# update the target account last/current
			if not lds_target.current_timestamp > t_cutoff:
				
				# last transaction was in previous time window, swap
				# a.k.a. move "old" current into "last" before overwriting
				lds_target.last_connections = lds_target.current_connections
				lds_target.last_reserve_balance = lds_target.current_reserve_balance
				lds_target.last_network_balance = lds_target.current_network_balance

			# if inactive slot is empty, we move before deleting otherwise just delete
			# one check is sufficient for both parties
			if not fint_target_account_id in lds_source.suggested_inactive_outgoing_reserve_transfer_requests:
				if not fint_target_account_id in lds_source.suggested_inactive_incoming_reserve_transfer_requests:
					# ok to copy back to inactive
					lds_source.suggested_inactive_incoming_reserve_transfer_requests[fint_target_account_id] = lint_amount
					lds_target.suggested_inactive_outgoing_reserve_transfer_requests[fint_source_account_id] = lint_amount
				
			# update the target account
			lds_target.suggested_active_outgoing_reserve_transfer_requests.pop(fint_source_account_id,None)
			lds_target.current_reserve_balance -= lint_amount
			lds_target.current_timestamp = datetime.datetime.now()

			lstr_source_tx_type = "SUGGESTED INCOMING RESERVE TRANSFER AUTHORIZED"
			lstr_source_tx_description = "SUGGESTED INCOMING RESERVE TRANSFER AUTHORIZED"
			lstr_target_tx_type = "SUGGESTED OUTGOING RESERVE TRANSFER AUTHORIZED"
			lstr_target_tx_description = "SUGGESTED OUTGOING RESERVE TRANSFER AUTHORIZED"
			lstr_return_message = "success_suggested_reserve_transfer_authorized"
			
		elif fstr_type == "authorizing_user":
		
			# This transaction type is one which affects the graph.
			
			# When a reserve transfer is "authorized" is essentially means that whatever reserves the two accounts
			# intended to transfer have been transferred and they have both agreed to adjust their reserve amounts
			# accordingly.  Just like any balance we need to do all the necessary checks to make sure they have
			# the amount available to move.  
			
			# From the initial checks in this function we already know:
			# 1. source and target accounts are valid
			# 2. source isn't trying to transfer to themselves
			# 3. amount is valid
			# 4. source and target are connected
			
			# "authorizing" means the source in this request is authorizing an incoming request.  Therefore we need
			# to validate it is still active and also need to make sure the target still has funds to pay.
			if not fint_target_account_id in lds_source.incoming_reserve_transfer_requests:
				return "error_no_request_in_incoming_for_target"
			if not lds_source.incoming_reserve_transfer_requests[fint_target_account_id] == lint_amount:
				return "error_authorization_amount_does_not_match_incoming_request"
			if not lds_target.current_reserve_balance > lint_amount: return "error_target_has_insufficient_reserves_for_transfer"			
			
			# ok to update now
			
			# calculate cutoff time
			t_now = datetime.datetime.now()
			d_since = t_now - T_EPOCH
			# this requests cutoff time
			t_cutoff = t_now - datetime.timedelta(seconds=(d_since.total_seconds() % (GRAPH_FREQUENCY_MINUTES * 60)))

			# update the source account last/current
			if not lds_source.current_timestamp > t_cutoff:
			
				# last transaction was in previous time window, swap
				# a.k.a. move "old" current into "last" before overwriting
				lds_source.last_connections = lds_source.current_connections
				lds_source.last_reserve_balance = lds_source.current_reserve_balance
				lds_source.last_network_balance = lds_source.current_network_balance
			
			# update the source account
			# delete the incoming request and add to reserve balance
			lds_source.incoming_reserve_transfer_requests.pop(fint_target_account_id,None)
			lds_source.current_reserve_balance += lint_amount
			lds_source.current_timestamp = datetime.datetime.now()
			
			# update the target account last/current
			if not lds_target.current_timestamp > t_cutoff:
				
				# last transaction was in previous time window, swap
				# a.k.a. move "old" current into "last" before overwriting
				lds_target.last_connections = lds_target.current_connections
				lds_target.last_reserve_balance = lds_target.current_reserve_balance
				lds_target.last_network_balance = lds_target.current_network_balance
				
			# update the target account
			lds_target.outgoing_reserve_transfer_requests.pop(fint_source_account_id,None)
			lds_target.current_reserve_balance -= lint_amount
			lds_target.current_timestamp = datetime.datetime.now()

			lstr_source_tx_type = "USER INCOMING RESERVE TRANSFER AUTHORIZED"
			lstr_source_tx_description = "USER INCOMING RESERVE TRANSFER AUTHORIZED"
			lstr_target_tx_type = "USER OUTGOING RESERVE TRANSFER AUTHORIZED"
			lstr_target_tx_description = "USER OUTGOING RESERVE TRANSFER AUTHORIZED"
			lstr_return_message = "success_user_reserve_transfer_authorized"

		else: return "error_transaction_type_invalid"			
		
		# ADD TWO TRANSACTIONS LIKE CONNECT()
		lds_source.tx_index += 1
		# source transaction log
		source_tx_log_key = ndb.Key("MRTX%s%s%s", (key_part1, key_part2,str(lds_source.tx_index).zfill(12)))
		source_lds_tx_log = ds_mr_tx_log()
		source_lds_tx_log.key = source_tx_log_key
		source_lds_tx_log.category = "MRTX" # GENERAL TRANSACTION GROUPING
		# tx_index should be based on incremented metric_account value
		source_lds_tx_log.tx_index = lds_source.tx_index
		source_lds_tx_log.tx_type = lstr_source_tx_type # SHORT WORD(S) FOR WHAT TRANSACTION DID
		source_lds_tx_log.amount = lint_amount
		source_lds_tx_log.access = "PUBLIC" # "PUBLIC" OR "PRIVATE"
		source_lds_tx_log.description = lstr_source_tx_description 
		source_lds_tx_log.memo = ""
		source_lds_tx_log.user_id_created = lds_source.user_id
		source_lds_tx_log.network_id = fstr_network_id
		source_lds_tx_log.account_id = fint_source_account_id
		source_lds_tx_log.source_account = fint_source_account_id 
		source_lds_tx_log.target_account = fint_target_account_id
		source_lds_tx_log.put()

		lds_target.tx_index += 1
		# target transaction log
		target_tx_log_key = ndb.Key("MRTX%s%s%s", (key_part1, key_part3,str(lds_target.tx_index).zfill(12)))
		target_lds_tx_log = ds_mr_tx_log()
		target_lds_tx_log.key = target_tx_log_key
		target_lds_tx_log.category = "MRTX" # GENERAL TRANSACTION GROUPING
		# tx_index should be based on incremented metric_account value
		target_lds_tx_log.tx_index = lds_target.tx_index
		target_lds_tx_log.tx_type = lstr_target_tx_type # SHORT WORD(S) FOR WHAT TRANSACTION DID
		target_lds_tx_log.amount = lint_amount
		# typically we'll make target private for bilateral transactions so that
		# when looking at a system view, we don't see duplicates.
		target_lds_tx_log.access = "PRIVATE" # "PUBLIC" OR "PRIVATE"
		target_lds_tx_log.description = lstr_target_tx_description 
		target_lds_tx_log.memo = ""
		target_lds_tx_log.user_id_created = lds_source.user_id
		target_lds_tx_log.network_id = fstr_network_id
		target_lds_tx_log.account_id = fint_target_account_id
		target_lds_tx_log.source_account = fint_source_account_id 
		target_lds_tx_log.target_account = fint_target_account_id
		target_lds_tx_log.put()
		
		lds_source.put()
		lds_target.put()
		return lstr_return_message

	def _process_graph(self, fint_network_id):
	
		# So...we meet again.
		
		# Each NETWORK!!! has a process lock. Network, not application
		# ..so if you and 50 of your buddies are playing around on the
		# same application running graph processing on 50 different
		# networks, might explain any slowness.
				
		# first get the cutoff time
		# It is from the cutoff time that we derive the entity key/id
		# for the profile.  
		t_now = datetime.datetime.now()
		d_since = t_now - T_EPOCH
		t_cutoff = t_now - datetime.timedelta(seconds=(d_since.total_seconds() % (GRAPH_FREQUENCY_MINUTES * 60)))
		# make a nice string to serve as our key "YYYYMMDDHHMM"
		profile_key_time_part = "%s%s%s%s%s" % (str(t_cutoff.year),
			str(t_cutoff.month).zfill(2),
			str(t_cutoff.day).zfill(2),
			str(t_cutoff.hour).zfill(2),
			str(t_cutoff.minute).zfill(2))
			
		# We use a transactional timelock mechanism to make sure one
		# and only one process is processing each specific window
		# of time, for each specific network id.
		
		profile_key_network_part = str(fint_network_id).zfill(8)
		
		@ndb.transactional()
		def process_lock():
		
			# get or create this networks master process entity
			profile_key = ndb.Key("ds_mrgp_master", "%s%s" % (profile_key_network_part, profile_key_time_part))
			profile = profile_key.get()
			if profile is None:
			
				# This process is creating the profile. We can
				# start a fresh process.
				what_to_do = "NEW"
				profile = ds_mrgp_master()
				profile.key = profile_key
				
			else:
			
				# profile loaded
				if profile.status == "IN PROCESS":
				
					# if the deadline has passed reboot
					# the process, otherwise exit.
					if t_now > profile.deadline:
						what_to_do = "NEW"
					else: return ("PROCESS LOCKED",None)
						
				if profile.status == "FINISHED":
				
					if not REDO_FINISHED_GRAPH_PROCESS:
						return ("PROCESS FINISHED FOR CURRENT TIMEFRAME",None)
					else: what_to_do = "NEW"
					
				if profile.status == "PAUSED":
					
					# We set status to "IN PROCESS" and
					# set our new deadline but we leave
					# all the cursors where they are and
					# pick up where we left off.
					what_to_do = "CONTINUE"
			
			if what_to_do == "NEW":
			
				profile.max_account = 0
				profile.phase_cursor = 1
				profile.tree_cursor = 0
				profile.count_cursor = 0
				profile.tree_chunks = 0
				profile.tree_in_process = False
				profile.index_chunks = 0
				profile.parent_pointer = 0
				profile.child_pointer = 0
				profile.report = {}
				profile.report['LAST_TREE_LEVEL'] = {}
				# LAST PARENT ON LEVEL ABOVE LAST LEVEL TREE CHUNK POINTER PER TREE
				profile.report['LP_WITH_KIDS'] = {}
				profile.report['LP_WITH_KIDS_IDX'] = {}
				profile.report['TREE_RESERVE_AMT_TOTAL'] = {}
				profile.report['TREE_RESERVE_AMT_AVERAGE'] = {}
				profile.report['TREE_NETWORK_AMT_TOTAL'] = {}
				profile.report['TREE_MEMBER_TOTAL'] = {}
				profile.report['ORPHAN_RESERVE_AMT_TOTAL'] = 0
				profile.report['ORPHAN_NETWORK_AMT_TOTAL'] = 0
				profile.report['ORPHAN_MEMBER_TOTAL'] = 0
				profile.report['SUGGESTED_TREE_COUNT_TOTAL'] = {}
				profile.report['SUGGESTED_TREE_MEMBER_TOTAL'] = {}
				profile.report['SUGGESTED_TREE_TX_COUNT_TOTAL'] = {}
				profile.report['SUGGESTED_TREE_AMT_TOTAL'] = {}
				profile.report['SUGGESTED_COUNT_TOTAL'] = 0
				profile.report['SUGGESTED_MEMBER_TOTAL'] = 0
				profile.report['SUGGESTED_TX_COUNT_TOTAL'] = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
				profile.report['SUGGESTED_AMT_TOTAL'] = 0
				profile.report['RESERVE_AMT_TOTAL'] = 0
				profile.report['NETWORK_AMT_TOTAL'] = 0
				profile.report['PARENT_LEVEL'] = 1 # Level Parent
				profile.report['PARENT_LEVEL_IDX'] = 0 # Level Parent Index
				profile.report['CHILD_LEVEL_IDX'] = 0 # Level Parent Index
		
			profile.status = "IN PROCESS"
			deadline_seconds_away = (GRAPH_ITERATION_DURATION_SECONDS + 
						GRAPH_ITERATION_WIGGLE_ROOM_SECONDS)
			profile.deadline = t_now + datetime.timedelta(seconds=deadline_seconds_away)
			profile.put()
			return ("GOT THE LOCK",profile)
						
		process_lock_result = process_lock()
		
		# If we didn't get the lock, we're done.
		if not process_lock_result[0] == "GOT THE LOCK": return process_lock_result[0]
		
		# now the clock starts.  If we don't finish before the
		# deadline, then we pause and wait for a different 
		# request
		
		# First we create the graph "juggler". Along with all it's
		# supporting functions.  The juggler is just a dictionary
		# that holds references to graph related objects.  It tells
		# us what's in memory, what needs to be written, etc.  As
		# for most small graphs we won't need to write but a few 
		# times, and for large graphs we want to minimize our writes
		# to the datastore.
		
		profile = process_lock_result[1]
		juggler = {}
		juggler_to_put = {}
		
		def get_chunk_from_juggler(fstr_type,fint_index):
		
			if fstr_type == "staging":
			
				# first see if it's already in the juggler
				juggler_key = ("%s_%s" % (fstr_type, str(fint_index)))
				if juggler_key in juggler: return juggler[juggler_key]
				# not there, get or create
				key_part1 = profile_key_network_part
				key_part2 = profile_key_time_part
				key_part3 = str(fint_index).zfill(12)
				staging_chunk_key = ndb.Key("ds_mrgp_staging_chunk","%s%s%s" % (key_part1,key_part2,key_part3))
				staging_chunk_member = staging_chunk_key.get()
				if staging_chunk_member is None:
					staging_chunk_member = ds_mrgp_staging_chunk()
					staging_chunk_member.key = staging_chunk_key
					# Staging chunks are modified upon creation by the
					# calling function.  No need to have juggler do the
					# save for an initial creation.
				# create a reference in the juggler
				juggler[juggler_key] = staging_chunk_member
				return staging_chunk_member
		
			if fstr_type == "index":
			
				# first see if it's already in the juggler
				juggler_key = ("%s_%s" % (fstr_type, str(fint_index)))
				if juggler_key in juggler: return juggler[juggler_key]
				# not there, get or create
				key_part1 = profile_key_network_part
				key_part2 = profile_key_time_part
				key_part3 = str(fint_index).zfill(12)
				index_chunk_key = ndb.Key("ds_mrgp_index_chunk","%s%s%s" % (key_part1, key_part2, key_part3))
				index_chunk_member = index_chunk_key.get()
				if index_chunk_member is None:
					index_chunk_member = ds_mrgp_index_chunk()
					index_chunk_member.key = chunk_key
					# Load our generic chunk or create so
					# that we don't have to wait for a 100,000
					# list loop to happen. If this is first time
					# ever, create the generic index.
					generic_index_key = ndb.Key("ds_mrgp_index_chunk","GENERIC_500_THOUSAND_FALSES_LIST")
					generic_index_chunk = generic_index_key.get()
					if generic_index_chunk is None:
						t_list = []
						for i in range(1,500001):
							t_list.append(False)
						generic_index_chunk = ds_mrgp_index_chunk()
						generic_index_chunk.stuff = t_list
						generic_index_chunk.key = generic_index_key
						generic_index_chunk.put()					
					index_chunk_member.stuff = generic_index_chunk.stuff
					# we had to create this index chunk
					# make sure juggler knows it needs to save it later
					juggler_to_put[juggler_key] = True
				# create a reference in the juggler
				juggler[juggler_key] = index_chunk_member
				return index_chunk_member		

			if fstr_type == "tree":
			
				# first see if it's already in the juggler
				juggler_key = ("%s_%s" % (fstr_type, str(fint_index)))
				if juggler_key in juggler: return juggler[juggler_key]
				# not there, get or create
				key_part1 = profile_key_network_part
				key_part2 = profile_key_time_part
				key_part3 = str(fint_index).zfill(12)
				tree_chunk_key = ndb.Key("ds_mrgp_tree_chunk","%s%s%s" % (key_part1, key_part2, key_part3))
				tree_chunk_member = tree_chunk_key.get()
				# if the chunk we're trying to get doesn't exist, create it
				if tree_chunk_member is None:
					tree_chunk_member = ds_mrgp_tree_chunk()
					tree_chunk_member.key = tree_chunk_key
					tree_chunk_member.stuff = {}
					tree_chunk_member.stuff[1] = []
					# we had to create this tree chunk
					# make sure juggler knows it needs to save it later
					juggler_to_put[juggler_key] = True
				# create a reference in the juggler
				juggler[juggler_key] = tree_chunk_member
				return tree_chunk_member

		def tell_juggler_modified(fstr_type,fint_index):
			
			juggler_key = ("%s_%s" % (fstr_type, str(fint_index)))
			if not juggler_key in juggler_to_put:
				juggler_to_put[juggler_key] = True
			return None
			
		# FOR FINISH AND PAUSE
		# put() index chunks
		# put() child chunk
		# put() profile
		def process_stop():
			#STUB	
			pass		
		
		lint_deadline_compute_factor = 0
		def deadline_reached(fbool_use_compute_factor=False):
			#STUB
			pass
			
		# PHASE 1
		#
		# phase 1 is loading the staging chunks with the entities that
		# we get by doing a "get_multi"
		if profile.phase_cursor == 1:		
			# figure out how many accounts there are
			# if we haven't already
			if profile.total_accounts == 0:			
				network_cursor_key = ndb.Key("ds_mr_network_cursor",profile_key_network_part)		
				lds_network_cursor = network_cursor_key.get()
				profile.max_account = lds_network_cursor.current_index
				################################################
				################################################
				################################################
				# STUB if total accounts = zero, just finish
				################################################
				################################################
				################################################				
			while True:			
				list_of_keys = []
				# staging chunk object
				chunk_stuff = {}
				# the chunks id is the starting account id
				# 1, 2501, 5001, etc.
				chunk_id = profile.count_cursor + 1				
				for i in range(1,2501):
					account_id = profile.count_cursor + i
					a_key = ndb.Key("ds_mr_metric_account","%s%s" % (profile_key_network_part,str(account_id).zfill(12)))
					list_of_keys.append(a_key)
					# when account id == the max account we are done
					# with this phase.
					if account_id == profile.max_account:
						break
					# if i == 2500 and we didn't reach max account
					# then add 2500 to our count cursor
					if i == 2500: profile.count_cursor += 2500
				list_of_metric_accounts = ndb.get_multi(list_of_keys)
				something_in_chunk = False
				for metric_account in list_of_metric_accounts:
					if metric_account is None: continue
					if metric_account.account_status == "DELETED": continue
					something_in_chunk = True
					# add account data to staging dictionary
					t_id = metric_account.account_id
					chunk_stuff[t_id] = {}
					# key 1 is tree
					# ...value 1 is always orphan
					# ...tree values then start 2, 3, 4, n...
					# key 2 is connections 
					# key 3 is suggestions [] in same order as connections
					# key 4 is network balance
					# key 5 is reserve balance
					chunk_stuff[t_id][1] = 1
					# default suggestions to 0
					chunk_stuff[t_id][3] = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
					if metric_account.current_timestamp <= t_cutoff:
						# use current
						chunk_stuff[t_id][2] = metric_account.current_connections
						chunk_stuff[t_id][4] = metric_account.last_network_balance
						chunk_stuff[t_id][5] = metric_account.last_reserve_balance
					else:
						# use last
						chunk_stuff[t_id][2] = metric_account.last_connections
						chunk_stuff[t_id][4] = metric_account.last_network_balance
						chunk_stuff[t_id][5] = metric_account.last_reserve_balance						
				if something_in_chunk:
					# put the chunk in the datastore
					# if this chunk already exists because perhaps
					# we're re-running this graph process overwrite it
					this_staging_chunk = get_chunk_from_juggler("staging",chunk_id)
					this_staging_chunk = chunk_stuff
					this_staging_chunk.put()				
				if account_id == profile.max_account:
					profile.phase_cursor = 2
					profile.tree_cursor = 0
					profile.count_cursor = 0
					if deadline_reached():
						return process_stop()
					else:
						# break into Phase 2 if there's more time
						break				
				if deadline_reached():
					return process_stop()
				else:
					# more time continue the tree process
					pass
		
		# PHASE 2
		#
		# we have queried all the accounts in the network and they
		# now reside in staging chunks of 2500 accounts each. In
		# Phase 2 we build the tree hierarchy which creates a proof
		# as to which sets of accounts have a "path" between them.
		#
		# I call each set a "tree".  The most populated tree is 
		# assumed to me the main network.  The other trees are 
		# considered off the main network.  An account with no 
		# connections is called an "orphan".  
		#
		# key 1 in the staging chunk for each account is reserved
		# for the "tree" value.  1 = orphan.  While building the 
		# tree chunks we start with 2 and increment.
		#
		# Really, this is going to be the slowest part of the algorithm.
		# This phase specifically, as we're accessing essne
		# It's my hope that with 1,000,000 nodes, perhaps the use of 
		# memcache and devoting sufficient RAM in GAE deployments will
		# suffice and still allow the app to exist as a web application
		# without using backends.		
		
		if profile.phase_cursor == 2:
		
			# PHASE 2 PART 1
			#
			# load the index chunk(s)
			# each handles indexing for 500,000
			# load all of them, they are small
			
			# how many indexes to query/create?
			# if we haven't figured it out yet in a previous
			# iteration then calculate it
			if profile.index_chunks == 0:				
				t_num = profile.max_account
				# one for every 500,000 accounts
				profile.index_chunks = ((t_num - (t_num % 500000)) / 500000) + 1
			
			# load index chunks
			index_chunk = {}
			for i in range(1,profile.index_chunks + 1):
				index_chunk[i] = get_chunk_from_juggler("index",i)
						
			# PHASE 2 PART 2
			# 
			# Now for the complicated part.  Building the representation
			# of the graph on GAE datastore.  The data of a graph is 
			# hierarchal, but the way we need to process it requires some
			# redundancy in information.
			#
			# Each "tree" has a seed account.  That account is "level 1".
			# All it's children are "level 2" and their children "level 3"
			# etc.  The tree chunk stores this information in a dictionary
			# of dictionaries.  Top level key is "tree number", next key
			# is level.  Orphans are all added to tree number 1 in whatever
			# tree chunk they happened to get processed in.  Reminder: an
			# orphan is an account with no connections that is still active.
			#
			# Now the problem is that we can't represent the tree in one big object
			# because we can't save it.  So just like with the staging chunks
			# we have to have 1MB tree chunks.  But it's a little more tricky
			# here.  We can traverse the tree pretty straightfoward, but we
			# need to reference the level above the level we're currently 
			# processing.  In PHASE 2 we're only reading the level above
			# but in the evening PHASE we're writing to two different levels.
			# And the level we're reading might be in a different tree
			# chunk than the one we're writing.  There's no way to really 
			# know where they will be either, because we can't know the shape
			# of the graph beforehand.
			#
			# This is why we have a "read pointer" and a "write pointer".  
			# These variable are pointers to the correct tree chunk.
			
			# Let's start by getting our parent and child tree chunks.
			# Parent and Child pointer values tell us the index of the 
			# tree chunks.
			if profile.parent_pointer == 0:
				# this is our first iteration in PHASE 2
				# we could do initialization stuff here
				profile.parent_pointer = 1
				profile.child_pointer = 1
			
			# First, get the tree chunk the parent_pointer is using
			parent_chunk = get_tree_chunk(profile.parent_pointer)
			# For small networks, they will always be the same
			# For a large tree they may diverge in which tree 
			# chunk they are pointing at
			if profile.parent_pointer == profile.child_pointer:
				child_chunk = get_chunk_from_juggler("tree",profile.child_pointer)
			else:
				child_chunk = parent_chunk
				
			# Our tree_cursor tracks which tree we are on
			if profile.tree_cursor == 0:
				profile.tree_cursor = 1
			# Our count_cursor tracks which account_id we start new trees on
			if profile.count_cursor == 0:
				profile.count_cursor = 1
			
			# PHASE 2 PART 3
			# our staging chunk(s) is/are ready
			# our index chunk(s) is/are ready
			# our tree chunk(s) is/are ready
			# 
			# we are ready to enter our main tree process loop
			# let's define the functions it uses first
			
			# tree process function helper #1
			# get account info from the staging chunk
			def phz2_get_acct_fsc(fint_account_id):			
				# We use memcache here, because we don't want to clog
				# the RAM of the machine accessing the graph randomly.
				# Especially if there are millions of accounts.
				#
				# Staging chunks in phase 2 are read only entities.
				staging_chunk_id = (fint_account_id - (fint_account_id % 2500)) + 1
				key_part1 = profile_key_network_part
				key_part2 = profile_key_time_part
				key_part3 = str(staging_chunk_id).zfill(12)
				memcache_key = key_part1 + key_part2 + key_part3
				data = memcache.get(memcache_key)				
				if data is None:
					staging_chunk_key = ndb.Key("ds_mrgp_staging_chunk","%s%s%s" % (key_part1,key_part2,key_part3))
					staging_chunk_entity = staging_chunk_key.get()
					data = staging_chunk_entity.stuff
					memcache.add(memcache_key, data, 60)				
				if data.get(fint_account_id) is None:
					return None
				else:
					return data[fint_account_id]			
			# tree process function helper #2
			# check if account is in the tree index already
			def phz2_acct_in_idx(fint_acc_id):		
				lint_index_chunk_id = ((fint_acc_id - (fint_acc_id % 500000)) / 500000) + 1
				lint_index_we_want_in_chunk = fint_acc_id - ((fint_acc_id -1) * 500000)
		 		if index_chunk[lint_index_chunk_id].stuff[lint_index_we_want_in_chunk - 1]:
		 			return True
		 		else:
		 			index_chunk[lint_index_chunk_id].stuff[lint_index_we_want_in_chunk - 1] = True
		 			# Let the juggler know we need to save this index chunk since 
		 			# we've modified it.
		 			tell_juggler_modified("index",lint_index_chunk_id)
		 			return False		 			
		 	# tree process function helper #3
		 	# see if our tree chunk is too big and we need to spawn another
		 	lint_tree_chunk_size_factor = 0
			def phz2_chk_chnk_sz(fbool_use_size_factor=False):			
				if fbool_use_size_factor:
					# This is a setting that makes it more flexible
					# how often we waste resources redundantly encoding
					# the tree chunk to check its size.
					if lint_tree_chunk_size_factor < 1000:
						return None
				lint_tree_chunk_size_factor = 0
				# if the size of the child chunk is too big 
				# create the next one
				if len(child_chunk._to_pb().Encode()) > 900000:
					# We're going to need to save the one that's full
					# Let the juggler know.
					tell_juggler_modified("tree",profile.child_pointer)
					ldict_stats = child_chunk['STATS']
					profile.child_pointer += 1
					if profile.tree_in_process:
						# Before we abandon the previous tree chunk, we need to leave
						# a breadcrumb, so the parent knows when to leap to the next
						# tree chunk.  Place an 'X' where the next entity info would
						# have been.
						child_chunk.stuff[profile.tree_cursor][temp_LP + 1].append('X')
						# Now change reference for "child" to new chunk.
						child_chunk = get_chunk_from_juggler("tree",profile.child_pointer)
						# Overwrite the default header info with current tree info.
						child_chunk.stuff[profile.tree_cursor] = {}
					else:
						# We must have filled up from orphans
						# Defaults will suffice, since not working on a tree at the moment.
						child_chunk = get_chunk_from_juggler("tree",profile.child_pointer)
					return None
				return None
					

			# MAIN PHASE 2 TREE PROCESS LOOP
			while True:

				if deadline_reached(True): return process_stop()
				phz2_chk_chnk_sz(True)

				if profile.tree_in_process:
					# finish the tree we're on
					# do one full group at a time
					key1 = profile.tree_cursor # the tree number
					key2 = profile.report['PARENT_LEVEL'] # the tree level parent
					idx1 = profile.report['PARENT_LEVEL_IDX'] # the parent index on that level
					key3 = 2 # that accounts connections sequence					
					# Large trees cause the parent and child chunk references
					# to possibly separate, but whenever we start a new tree
					# the parent and child both should be referencing the same
					# chunk.
					if key2 == 1 and idx1 == 0: 					
						parent_chunk = child_chunk
						# Also, level one is the only level where we need to get tree
						# statistics from the parent level too, all other times, we get
						# them by only looking at child.
						# get parents reserve total
						lint_temp = parent_chunk.stuff[key1][key2][idx1][5]
						profile.report['TREE_RESERVE_AMT_TOTAL'][key1] = lint_temp
						profile.report['TREE_NETWORK_AMT_TOTAL'][key1] = lint_temp
						profile.report['TREE_MEMBER_TOTAL'][key1] = 1
						profile.report['RESERVE_AMT_TOTAL'] += lint_temp
						profile.report['NETWORK_AMT_TOTAL'] += lint_temp
					# The child_chunk creates new tree chunks as it runs out of
					# space and keeps all the important variables.  The parent_chunk
					# just follows along.  Every time a child_chunk goes to a
					# new chunk, it places a static 'X' where an account dict
					# would have been in the previous chunk before it leaves
					# So before trying to access the account info you think is at:
					# ***chunk[tree_key][level_key][index_of_account_dict]***
					# ...you need to make sure there isn't a big fat 'X' in that
					# spot.  If there is, we need to transition to the next tree
					# chunk before continuing.
					if parent_chunk.stuff[key1][key2][idx1] == 'X':					
						profile.parent_pointer += 1
						parent_chunk = get_tree_chunk(profile.parent_pointer)
						# Parent index on whatever level they are in the new
						# chunk will always be zero. The start of the sequence.
						profile.report['PARENT_LEVEL_IDX'] = 0
					for connection in parent_chunk.stuff[key1][key2][idx1][key3]:
						# only do something with this account if we haven't already processed
						if not phz2_acct_in_idx(connection):
							# lets put this connection on the level below
							# after getting it from the staging chunk
							laccount = get_acct_fsc(connection)
							# Get tree statistics from this account
							# get childs reserve total
							profile.report['TREE_RESERVE_AMT_TOTAL'][key1] += laccount[5]
							profile.report['TREE_NETWORK_AMT_TOTAL'][key1] += laccount[4]
							profile.report['TREE_MEMBER_TOTAL'] += 1
							profile.report['RESERVE_AMT_TOTAL'] += laccount[5]
							profile.report['NETWORK_AMT_TOTAL'] += laccount[4]
							# Make this parent_chunk id the LP_WITH_KIDS
							profile.report['LP_WITH_KIDS'][key1] = profile.parent_pointer
							profile.report['LP_WITH_KIDS_IDX'][key1] = idx1
							if child_chunk.stuff[key1].get(key2 + 1) is None:
								# create the level
								profile.report['LAST_TREE_LEVEL'][key1] = key2 + 1
								child_chunk.stuff[key1][key2 + 1] = []
								child_chunk.stuff[key1][(key2 + 1) * -1] = []
								child_chunk.stuff[key1][(key2 + 1) * -1].append(-1)
							# lets store the parent reference in key 6 of child
							# chunk.stuff[tree][-level array][account ids]
							laccount[6] = parent_chunk.stuff[key1][key2 * -1][idx1]
							child_chunk.stuff[key1][key2 + 1].append(laccount)
							child_chunk.stuff[key1][(key2 + 1) * -1].append(connection)
							lint_tree_chunk_size_factor += 10
					# if we haven't reached the end of this level we aren't done
					this_id = parent_chunk.stuff[key1][key2 * -1][idx1]
					final_id = parent_chunk.stuff[key1][key2 * -1][-1]
					if this_id == final_id:
						# Ok, we've reached the end of this level.
						# But is there a level below this?  Check the child stats
						if profile.report['LAST_TREE_LEVEL'][key1] == profile.report['PARENT_LEVEL']:
							# no level below this, this tree is done
							profile.report['PARENT_LEVEL'] = 1
							profile.report['PARENT_LEVEL_IDX'] = 0
							profile.report['CHILD_LEVEL_IDX'][key1] = idx1
							# While we're ending the tree, lets take care of some reporting variables.
							profile.report['SUGGESTED_TREE_COUNT_TOTAL'][key1] = 0
							profile.report['SUGGESTED_TREE_MEMBER_TOTAL'][key1] = 0
							profile.report['SUGGESTED_TREE_TX_COUNT_TOTAL'][key1] = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
							profile.report['SUGGESTED_TREE_AMT_TOTAL'][key1] = 0
							lint_amt = profile.report['TREE_RESERVE_AMT_TOTAL'][key1]
							lint_accounts = profile.report['TREE_MEMBER_TOTAL'][key1]
							# drop the scintillions and also divide this way so that complies with 
							# python 3? division if ever migrated.
							lint_average = ((lint_amount - (lint_amount % lint_accounts)) / lint_accounts)
							profile.report['TREE_RESERVE_AMT_AVERAGE'][key1] = lint_average
							profile.tree_in_process = False
						else:
							# more levels, keep going
							profile.report['PARENT_LEVEL'] += 1
							profile.report['PARENT_LEVEL_IDX'] = 0
							lint_tree_chunk_size_factor += 1
					else:
						# more account(s) in this level, keep going
						profile.report['PARENT_LEVEL_IDX'] += 1
						lint_tree_chunk_size_factor += 1
							
							
				else:
					# try to start a new tree
					if phz2_acct_in_idx(profile.count_cursor):
						# already processed this account
						pass						
					else:
						# account not yet processed
						# try to get it from staging chunk
						lresult = get_acct_fsc(profile.count_cursor)
						if lresult is None:
							# nothing to do
							# let process fall through and 
							# incrmement count_cursor
							pass
						elif lresult[2] == []:
							# no connections, so it's an orphan
							child_chunk.stuff[1].append(profile.count_cursor)
							lint_tree_chunk_size_factor += 1
							profile.report['ORPHAN_RESERVE_AMT_TOTAL'] += lresult[5]
							profile.report['ORPHAN_NETWORK_AMT_TOTAL'] += lresult[4]
							profile.report['ORPHAN_MEMBER_TOTAL'] += 1
					
						else:
							# has connections
							# add seed to dict and start tree
							profile.tree_cursor += 1
							child_chunk.stuff[profile.tree_cursor] = {}
							# make level one this new seed
							child_chunk.stuff[profile.tree_cursor][1] = []
							child_chunk.stuff[profile.tree_cursor][-1] = []
							# put the new account seed in level 1 sequence
							child_chunk.stuff[profile.tree_cursor][1].append(lresult)
							child_chunk.stuff[profile.tree_cursor][-1].append(profile.count_cursor)
							profile.tree_in_process = True
							lint_tree_chunk_size_factor += 10						
					if profile.count_cursor == profile.max_account:
						# we're done with phase 2
						profile.phase_cursor = 3
						if deadline_reached(): return None
						break
					else:
						profile.count_cursor += 1
						lint_deadline_compute_factor += 1
						continue
						
		if profile.phase_cursor == 3:
		
			# PHASE 3
			#
			# Phase 3 is the reserve evening process.  This is where the system suggests how
			# accounts should move money between accounts in order that network liquidity is
			# normalized.  
			# 
			# To do this we run backwards through the tree.  Whereas when we created it we
			# started from the seed and proceeded downward in each tree, level by level, for
			# the evening process we will start at the lowest level and move upward.  
			#
			# We still have a parent and child chunk reference but now, since we're going
			# backwards, it's the parent that moves ahead of the child.  There is no need 
			# to access any staging chunks, or any index chunks.
			# 
			# Instead we will have one report_chunk that we will write to whenever the
			# child_chunk moves to the lower-indexed tree chunk, because once that occurs all
			# the data in that chunk has been finalized.
			# 
			# So reporting when a chunk is finalized will be for any orphans in that chunk
			# and for any trees that had there seeds in that chunk.  If we haven't reached
			# the beginning of the tree, then we're still creating data, and we just save
			# the reporting stuff for that tree in the "header" of the new child_chunk.

			# So let's get started.
			
			# Still using the parent/child pointers.  The child_pointer should still be 
			# pointing at the last tree chunk.  May or may not have any trees in that chunk.
			# The parent pointer should still be pointed at the lowest level of that last
			# tree completed.  There's no logic that would have modified it.  Don't really
			# need to reference the parent unless we're evening a tree though.

			child_chunk = get_chunk_from_juggler("tree",profile.child_pointer)
			
			# Main Loop
			while True:
			
				if deadline_reached(True): return process_stop()
				
				if profile.tree_in_process:
				
					# If there's a tree in process there must
					# be another group to process.  Because when
					# we process a group, we cue up the next group
					# and if the group we processed had the seed
					# as the parent, then we would have finished
					# the tree.
					
					# get references to tree
					lint_tree = profile.tree_cursor
					
					# get parent level/index/id/reserves					
					lint_p_lvl = profile.report['PARENT_LEVEL']
					lint_p_idx = profile.report['PARENT_LEVEL_IDX']
					lint_p_id = parent_chunk.stuff[lint_tree][lint_p_lvl * -1][lint_p_idx]
					ldict_p_account = parent_chunk.stuff[lint_tree][lint_p_lvl][lint_p_idx]
					lint_p_rsrv = ldict_p_account[5]
					
					# The only complicated part of this particular evening algorithm
					# is deciding how a parent should spread out his reserves to the
					# deficient children.  If he has no reserves, or none of the children
					# are deficient, we don't do this part.
					if lint_p_rsrv > 19:
						parent_has_reserves = True
					else:
						parent_has_reserves = False
					# make list of tuples for children
					list_tpl_kids = []
					
					# loop initialization variables
					lint_c_lvl = lint_p_lvl + 1
					lint_child_idx = profile.report['CHILD_LEVEL_IDX']
					lint_c_id = parent_chunk.stuff[lint_tree][(lint_p_lvl + 1) * -1][lint_child_idx]
					ldict_c_account = child_chunk.stuff[lint_tree][lint_p_lvl + 1][lint_child_idx]
					child_has_deficiency = False
					# We run this loop even if parent has no reserves in order
					# to complete any child suggestions to parent.
					while True:						
						if not ldict_c_account[6] == lint_p_id:
							# We're done, this child belongs to next parent
							break						
						if ldict_c_account[5] < profile.report['TREE_RESERVE_AMT_AVERAGE'][lint_tree]:
							# This child belongs to our parent, and it has a 
							# reserve deficiency from average.  Add it to list of
							# candidates for parent-to-child reserve transfer.
							list_tpl_kids.append((lint_c_idx, lint_c_id, ldict_c_account[5]))
							child_has_deficiency = True						
						if ldict_c_account[5] > profile.report['TREE_RESERVE_AMT_AVERAGE'][lint_tree]:
							# Most of the complexity in this algorithm is deciding how
							# parent should distribute its reserves to deficient children.
							# Deciding what the child should do with excess reserves, 
							# however, is easy.  It should give all the excess to the parent.
							#
							# We can take care of this right here in this logic branch. If
							# we're here it means this child has more than the average for 
							# this tree.
							# 1. Create - suggestion for parent slot in this account = to overage
							# 2. Create + suggestion for child slot in parent account = to overage
							lint_overage = ldict_c_account[5] - profile.report['TREE_RESERVE_AMT_AVERAGE'][lint_tree]
							# do the childs suggestion
							lint_target_sugg_idx = ldict_c_account[2].index(lint_p_id)
							ldict_c_account[3][lint_target_sugg_idx] = (lint_overage * -1)
							# do the parents suggestion
							lint_target_sugg_idx = ldict_p_account[2].index(lint_c_id)
							ldict_p_account[3][lint_target_sugg_idx] = (lint_overage)
							# increment/modify reporting variables
							# We store an indication in key 7 that we had a suggestion
							# outgoing as a parent to children.  So at this point, when we're 
							# processing it as part of a child group, we know how many
							# transactions to include and where.
							if ldict_c_account.get(7) is None:
								# Not defined.  This account only has this
								# one suggestion.
								# global report variables
								profile.report['SUGGESTED_COUNT_TOTAL'] += 1
								profile.report['SUGGESTED_MEMBER_TOTAL'] += 1
								profile.report['SUGGESTED_TX_COUNT_TOTAL'][0] += 1 
								profile.report['SUGGESTED_AMT_TOTAL'] += lint_overage
								# tree report variables
								profile.report['SUGGESTED_TREE_COUNT_TOTAL'][lint_tree] += 1
								profile.report['SUGGESTED_TREE_MEMBER_TOTAL'][lint_tree] += 1
								profile.report['SUGGESTED_TREE_TX_COUNT_TOTAL'][lint_tree][0] += 1 
								profile.report['SUGGESTED_TREE_AMT_TOTAL'][lint_tree] += lint_overage
							else:
								# Defined.  This account has (key 7) + 1 suggestions.
								lint_total_suggestions = ldict_c_account[7] + 1
								# global report variables
								profile.report['SUGGESTED_COUNT_TOTAL'] += 1
								# already included in SUGGESTED_MEMBER_TOTAL in processing as parent
								profile.report['SUGGESTED_TX_COUNT_TOTAL'][lint_total_suggestions - 1] += 1 
								profile.report['SUGGESTED_AMT_TOTAL'] += lint_overage
								# tree report variables
								profile.report['SUGGESTED_TREE_COUNT_TOTAL'][lint_tree] += 1
								# already included in SUGGESTED_TREE_MEMBER_TOTAL in processing as parent
								profile.report['SUGGESTED_TREE_TX_COUNT_TOTAL'][lint_tree][lint_total_suggestions - 1] += 1 
								profile.report['SUGGESTED_TREE_AMT_TOTAL'][lint_tree] += lint_overage
							# We updated parent and child chunks.  Let the juggler know.
							tell_juggler_modified("tree",profile.child_pointer)
							tell_juggler_modified("tree",profile.parent_pointer)
						else:
							# Notice if reserves are equal to average we ignore.
							pass
						if profile.report['CHILD_LEVEL_IDX'] > 0:						
							profile.report['CHILD_LEVEL_IDX'] -= 1
							lint_child_idx = profile.report['CHILD_LEVEL_IDX']
							lint_c_id = child_chunk.stuff[lint_tree][lint_c_lvl * -1][lint_child_idx]
							ldict_c_account = child_chunk.stuff[lint_tree][lint_c_lvl][lint_child_idx]
						else:
							# We're done, child index is 0, must be at beginning 
							# of child level on this tree chunk, which means end
							# of this group.
							break
					# We are done checking the children.
					# Now see if we need to make parent suggestions.
					if child_has_deficiency and parent_has_reserves:					
							# create new reference to parents total reserves
							lint_amount_left_to_use = lint_p_rsrv
							# create a sorted version of our list of child tuples
							list_tpl_kids_sorted = sorted(list_tpl_kids, key=itemgetter(2))
							# Instead of populating the suggestion list with values
							# as we go, we'll keep track of fill line.  The fill line
							# should start at the level of the lowest child.
							lint_fill_line = list_tpl_kids_sorted[0][2]
							# now loop from first to last
							# THIS IS THE PRIMARY LOGIC OF GROUP RESERVE EVENING
							for i in range(len(list_tpl_kids_sorted)):
								# tuple list member is (index,id,amt)
								# is this the last one?
								if i == (len(list_tpl_kids_sorted) - 1):
									# We are on the last (or only) index.
									# That means all the children are either
									# even or there's only one, and we still 
									# are below average.  So see if we have
									# enough to make all average or make fill
									# line whatever evenly distributing remaining
									# gets us.
									lint_average = profile.report['TREE_RESERVE_AMT_AVERAGE'][lint_tree]
									lint_difference = lint_average - list_tpl_kids_sorted[i][2]
									lint_needed_to_get_avg = lint_difference * (i + 1)
									if amount_left_to_use < lint_needed_to_get_avg:
										lint_fill_line = lint_fill_line + ((amount_left_to_use - (amount_left_to_use % (i + 1))) / (i + 1))
										break
									else:
										lint_fill_line = lint_average
										break
								if list_tpl_kids_sorted[i][2] == list_tpl_kids_sorted[i + 1][2]:
									# Next account has same as this one.
									# Continue until we find one with more
									# or we're on the last one.
									continue
								else:
									# Next account has more than this one.
									# If we have enough to make 0 to i that much
									# then make next's amount our fill line.
									#
									# If we don't have enough for that then figure out
									# what the fill line would be by spreading remaining
									# between 0 and i and break.
									lint_difference = list_tpl_kids_sorted[i + 1][2] - list_tpl_kids_sorted[i][2]
									lint_needed_to_even = lint_difference * (i + 1)
									if amount_left_to_use < lint_needed_to_even:
										# not enough to make even with next, get our fill line and break
										lint_fill_line = lint_fill_line + ((amount_left_to_use - (amount_left_to_use % (i + 1))) / (i + 1))
										break
									else:
										# enough to make even with next
										lint_fill_line = list_tpl_kids_sorted[i + 1][2]
										amount_left_to_use = amount_left_to_use - lint_needed_to_even
										# break if we have less than 20 scintillions
										if amount_left_to_use < 20: 
											break
										else:
											continue
											
							# Create suggestions in the parent to bring any deficient 
							# children under the fill line, to the fill line.
							for i in range(len(list_tpl_kids_sorted)):
								if list_tpl_kids_sorted[i][2] < lint_fill_line:
									lint_suggestion_amount = lint_fill_line - list_tpl_kids_sorted[i][2]
									# do the childs suggestion (+)
									# list_tpl_kids_sorted member is (index,id,amt)
									ldict_c_account = child_chunk.stuff[lint_tree][lint_p_lvl + 1][list_tpl_kids_sorted[i][0]]
									lint_target_sugg_idx = ldict_c_account[2].index(lint_p_id)
									ldict_c_account[3][lint_target_sugg_idx] = (lint_suggestion_amount)
									# do the parents suggestion (-)
									lint_target_sugg_idx = ldict_p_account[2].index(list_tpl_kids_sorted[i][1])
									ldict_p_account[3][lint_target_sugg_idx] = (lint_suggestion_amount * -1)
									# increment/modify reporting variables
									#
									# Store our total suggestions in key 7 as we only
									# add to reporting variables when processing
									# as child because that could be one more transaction.
									# we do store all the other transaction info for the
									# parent, however, each time we make a suggestion.								
									if ldict_p_account.get(7) is None:
										# Not defined.  
										ldict_p_account[7] = 1
										# These two should only get incremented once for the parent.
										profile.report['SUGGESTED_MEMBER_TOTAL'] += 1
										profile.report['SUGGESTED_TREE_MEMBER_TOTAL'][lint_tree] += 1
									else:
										ldict_p_account[7] += 1
										
									# global report variables
									profile.report['SUGGESTED_COUNT_TOTAL'] += 1
									profile.report['SUGGESTED_AMT_TOTAL'] += lint_suggestion_amount
									# tree report variables
									profile.report['SUGGESTED_TREE_COUNT_TOTAL'][lint_tree] += 1
									profile.report['SUGGESTED_TREE_AMT_TOTAL'][lint_tree] += lint_suggestion_amount
										
									# We updated parent and child chunks.  Let the juggler know.
									tell_juggler_modified("tree",profile.child_pointer)
									tell_juggler_modified("tree",profile.parent_pointer)
								else:
									continue
					# We are done processing this tree reserve group.  Set up
					# pointers to the next one unless we are done with
					# this tree.
					if lint_p_lvl == 1:
						# level 1 is the seed, we are done with this tree
						# Decrement the tree cursor and break
						
						# Also, being that the parent is on the seed, let's 
						# record the final report variables we don't get to
						# since the seed is never processed as a child.
						if not ldict_p_account.get(7) is None:
							profile.report['SUGGESTED_TX_COUNT_TOTAL'][ldict_p_account[7] - 1] += 1 
							profile.report['SUGGESTED_TREE_TX_COUNT_TOTAL'][profile.tree_cursor][ldict_p_account[7] - 1] += 1						
						profile.tree_cursor -= 1
						profile.tree_in_process = False						
						break
					else:
						# So the child level is at least level 3.  To prepare
						# the next group we need to find the next child.  Finding
						# next parent is no good, because it may be an account
						# on that level that had no unique children. So find the
						# next child, even if we have to go up a level, or up 
						# a chunk, and then find the right parent chunk as well.
						# 
						# Then we're set and can just continue this while loop.
						#
						# Let's get started.
						#
						# We decremented the child index unless it was zero, 
						# meaning we are at the end of this level on this chunk.
						# If we're not at zero, the child chunk is good to go.
						if profile.report['CHILD_LEVEL_IDX'] == 0:
							# A level can be split across two or more chunks
							# but you'll never have the 2 distinct levels on two 
							# different chunks for the same tree.  
							# So either:
							# 1. The level above exists on this chunk OR
							# 2. The current level is continued from the previous chunk OR
							# 3. The current level started on this chunk
							if not child_chunk.stuff[profile.tree_cursor].get(lint_p_lvl) is None:
								# It's scenario 1.
								lint_child_idx = len(child_chunk.stuff[profile.tree_cursor][lint_p_lvl * -1]) - 1
								profile.report['CHILD_LEVEL_IDX'] = lint_child_idx
								profile.report['PARENT_LEVEL'] -= 1								
							else:
								# It's scenario 2 or 3.  Let's grab it and
								# figure out what our child level and index needs
								# to be.
								profile.child_pointer -= 1
								child_chunk = get_chunk_from_juggler("tree",profile.child_pointer)
								if not child_chunk.stuff[profile.tree_cursor].get(lint_p_lvl - 1) is None:
									# It's scenario 2.
									# There will be an 'X' in last position of level, but not 
									# in the negative level, FYI.
									lint_child_idx = len(child_chunk.stuff[profile.tree_cursor][(lint_p_lvl + 1) * -1]) - 1
									profile.report['CHILD_LEVEL_IDX'] = lint_child_idx
									# parent level remains the same
								else:
									# It's scenario 3.
									lint_child_idx = len(child_chunk.stuff[profile.tree_cursor][lint_p_lvl * -1]) - 1
									profile.report['CHILD_LEVEL_IDX'] = lint_child_idx
									profile.report['PARENT_LEVEL'] -= 1						
						# Now lets make sure our parent chunk and indexes are set.
						# Everything else but that is good to go for the loop.
						#
						# Parent account id we're looking for
						lint_child_idx = profile.report['CHILD_LEVEL_IDX']
						lint_child_lvl = profile.report['PARENT_LEVEL'] + 1
						lint_parent_lvl = profile.report['PARENT_LEVEL']
						p_looking_id = child_chunk.stuff[profile.tree_cursor][lint_child_lvl][lint_child_idx][6]
						#
						# Is the parent level we need on this chunk?
						while True:							
							if parent.stuff[profile.tree_cursor].get(profile.report['PARENT_LEVEL']) is None:
								# no - need a new chunk
								profile.parent_pointer -= 1
								parent_chunk = get_chunk_from_juggler("tree",profile.parent_pointer)
							else:
								# yes - but is the parent account id we're looking for on this chunk?
								if not p_looking_id in parent.stuff[profile.tree_cursor][lint_parent_lvl * -1]:
									# no - need a new chunk
									profile.parent_pointer -= 1
									parent_chunk = get_chunk_from_juggler("tree",profile.parent_pointer)									
								else:
									# found it!
									lint_idx = parent.stuff[profile.tree_cursor][lint_parent_lvl * -1].index(p_looking_id)
									profile.report['PARENT_LEVEL_IDX'] = lint_idx
									# our parent chunk and id are now set to the next group
									# ready to continue the outer loop.
									break
				else:
				
					if profile.tree_cursor == 1:
					
						# Nothing left but orphans.
						# But could (though slim chance) be on
						# more than one tree chunk.
						if profile.child_pointer == 1:
							# We're done with phase 3.
							profile.phase_cursor = 4
						else:
							profile.child_pointer -= 1
							child_chunk = get_chunk_from_juggler("tree",profile.child_pointer)
					else:					
						# We have more tree(s) to process but 
						# haven't yet started it.
						#
						# If the tree we need to work on doesn't
						# end on this chunk, then finalize this
						# chunk and decrement the child pointer.
						#
						# If the tree we need does end on this
						# chunk, then we're ready to start on a 
						# new tree.						
						if child_chunk.stuff.get(profile.tree_cursor) is None:						
							# This chunk doesn't have the tree we need.
							# Maybe the one previous does.
							profile.child_pointer -= 1
							child_chunk = get_chunk_from_juggler("tree",profile.child_pointer)
						else:
							# This chunk has the tree_cursor key and we
							# haven't processed.  This must be the end of
							# the tree, and there must be at least one
							# unprocessed group on this tree in this chunk.
							#
							# That means this will be the first group 
							# processed for this tree so we must set our
							# level and index on the parent_chunk.
							profile.parent_pointer = profile.report['LP_WITH_KIDS'][profile.tree_cursor]
							parent_chunk = get_chunk_from_juggler("tree",profile.parent_pointer)
							# Parent chunk ready to go.  Now we need to set
							# the parent index and level properly.
							# NOTE: We want -1 because the last-last level has no children.
							# That's what makes it the last level.  That's not a "group".
							# a "group" is a parent and all it's next-level children in the
							# created tree.  And a trees last level will never be 1 as that's
							# what defines an orphan.
							lint_temp = profile.report['LAST_TREE_LEVEL'][profile.tree_cursor] - 1
							profile.report['PARENT_LEVEL'] = lint_temp
							# So we know we got the right chunk, and we know we got the right
							# level to start the parent on.  But we still need the index.
							lint_temp = profile.report['LP_WITH_KIDS_IDX'][profile.tree_cursor]
							profile.report['PARENT_LEVEL_IDX'] = lint_temp
							# The child index (CHILD_LEVEL_IDX) is only used in this phase so we set it
							# in phase 2 when we complete a tree. It should be ready to use.
							profile.tree_in_process = True
							
							
		if profile.phase_cursor == 4:
		
			pass
			# here we sort the tree chunk data to prepare for staging

		if profile.phase_cursor == 6:
		
			pass
			# finalize
		
		return lstr_return_message
		"""
		
		REDO_FINISHED_GRAPH_PROCESS = True
		
		GRAPH_ITERATION_DURATION_SECONDS = 30
		GRAPH_ITERATION_WIGGLE_ROOM_SECONDS = 15
		GRAPH_ITERATION_HIJACK_DURATION_SECONDS = 10
		
		
		class ds_mrgp_profile(ndb.Model):

			status = ndb.StringProperty()
			deadline = ndb.DateTimeProperty()
			phase_cursor = ndb.IntegerProperty()
			tree_cursor = ndb.IntegerProperty()
			count_cursor = ndb.IntegerProperty()
			key_chunks = ndb.IntegerProperty()
			tree_chunks = ndb.IntegerProperty()
			tree_in_process = False				
			staging_chunks = ndb.IntegerProperty()
			map_chunks = ndb.IntegerProperty()
			index_chunks = ndb.IntegerProperty()
			parent_pointer = ndb.IntegerProperty()
			child_pointer = ndb.IntegerProperty()

		"""
		
		
		

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
		
		# STEP 1 (VALIDATE FORMAT)
		# make sure the username format is entered correctly, only a-z, 0-9, and underscore allowed
		if not re.match(r'^[a-z0-9_]+$',lobj_master.request.POST['form_username']):
		
			# bad username format
			# kick them back to registration page with an error
			# error messages are contained in the HTML template and activated by URL query string
			lobj_master.request_handler.redirect('/mob_s_register?user_error=bad_username_format')
		
		# STEP 2 (VALIDATE UNIQUENESS AND PROCESS REQUEST)
		# make sure the chosen username isn't already taken
		elif not lobj_master.user._save_unique_username(lobj_master.request.POST['form_username']):
		
			# username is not unique
			# kick them back to registration page with an error
			# error messages are contained in the HTML template and activated by URL query string
			lobj_master.request_handler.redirect('/mob_s_register?user_error=username_not_unique')		
		
		# SETP 3 (REDIRECT ON SUCCESS)
		# Redirect to non-POST page
		else: lobj_master.request_handler.redirect('/mob_s_register?form_success=username_successfully_assigned')

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
		
		lobj_master.user.HAS_METRIC_ACCOUNT = False
		# let's grab metric account for user so we can look at metric account in development
		key_part1 = str(lobj_master.user.entity.metric_network_ids).zfill(8)
		key_part2 = str(lobj_master.user.entity.metric_account_ids).zfill(8)
		temp_source_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part2))
		temp_lds_source = temp_source_key.get()
		
		# if metric account loads, pass to template
		if not temp_lds_source is None: 
			lobj_master.user.HAS_METRIC_ACCOUNT = True
			lobj_master.user.metric_account_entity = temp_lds_source
		
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
		
		lobj_master.TRACE.append("ph_mob_s_connect.post(): in connect POST function")
		
		
		# Connect Page
		# Get the current network profile
		lobj_master.network_connecting = lobj_master.metric._get_network_summary()
		lint_network_id = lobj_master.network_connecting.network_id
		lint_source_account_id = lobj_master.user.entity.metric_account_ids
		lint_target_account_id = int(lobj_master.request.POST['form_target_id'])
		lstr_result = lobj_master.metric._connect(lint_network_id, lint_source_account_id, lint_target_account_id)
		
		lobj_master.request_handler.redirect('/mob_s_connect?form_result=%s' % lstr_result)	
		
# page handler class for "/mob_s_disconnect"
class ph_mob_s_disconnect(webapp2.RequestHandler):

	def get(self):
		
		# Instantiate the master object, do security and other app checks. If
		# there's an interruption return from this function without processing
		# further.
		lobj_master = master(self,"get","secured")
		if lobj_master.IS_INTERRUPTED:return
		
		lobj_master.TRACE.append("ph_mob_s_disconnect.get(): in disconnect GET function")
		
		# Disconnect Page
		lobj_master.network_connecting = lobj_master.metric._get_network_summary()
		
		template = JINJA_ENVIRONMENT.get_template('templates/tpl_mob_s_disconnect.html')
		self.response.write(template.render(master=lobj_master))
		
	def post(self):
		
		# Instantiate the master object, do security and other app checks. If
		# there's an interruption return from this function without processing
		# further.
		lobj_master = master(self,"post","secured")
		if lobj_master.IS_INTERRUPTED:return
		
		lobj_master.TRACE.append("ph_mob_s_disconnect.post(): in disconnect POST function")
		
		
		# Disconnect Page
		# Get the current network profile
		lobj_master.network_connecting = lobj_master.metric._get_network_summary()
		lint_network_id = lobj_master.network_connecting.network_id
		lint_source_account_id = lobj_master.user.entity.metric_account_ids
		lint_target_account_id = int(lobj_master.request.POST['form_target_id'])
		lstr_result = lobj_master.metric._disconnect(lint_network_id, lint_source_account_id, lint_target_account_id)
		
		lobj_master.request_handler.redirect('/mob_s_disconnect?form_result=%s' % lstr_result)

# page handler class for "/mob_s_modify_reserve"
class ph_mob_s_modify_reserve(webapp2.RequestHandler):

	def get(self):
		
		# Instantiate the master object, do security and other app checks. If
		# there's an interruption return from this function without processing
		# further.
		lobj_master = master(self,"get","secured")
		if lobj_master.IS_INTERRUPTED:return
		
		lobj_master.TRACE.append("ph_mob_s_modify_reserve.get(): in modify_reserve GET function")
		
		# modify_reserve Page
		lobj_master.network_current = lobj_master.metric._get_network_summary()
		
		template = JINJA_ENVIRONMENT.get_template('templates/tpl_mob_s_modify_reserve.html')
		self.response.write(template.render(master=lobj_master))
		
	def post(self):
		
		# Instantiate the master object, do security and other app checks. If
		# there's an interruption return from this function without processing
		# further.
		lobj_master = master(self,"post","secured")
		if lobj_master.IS_INTERRUPTED:return
		
		lobj_master.TRACE.append("ph_mob_s_modify_reserve.post(): in modify_reserve POST function")
		
		
		# modify_reserve Page
		# Get the current network profile
		lobj_master.network_current = lobj_master.metric._get_network_summary()		
		lint_network_id = lobj_master.network_current.network_id
		lint_source_account_id = lobj_master.user.entity.metric_account_ids
		
		lstr_submit_value = lobj_master.request.POST['submit']
		
		if lstr_submit_value == "submit_add_normal":
			lstr_modify_type = "normal_add"
			lstr_amount = lobj_master.request.POST['form_add_normal']
		elif lstr_submit_value == "submit_subtract_normal":
			lstr_modify_type = "normal_subtract"
			lstr_amount = lobj_master.request.POST['form_subtract_normal']
		elif lstr_submit_value == "submit_add_override":
			lstr_modify_type = "override_add"
			lstr_amount = lobj_master.request.POST['form_add_override']
		elif lstr_submit_value == "submit_subtract_override":
			lstr_modify_type = "override_subtract"
			lstr_amount = lobj_master.request.POST['form_subtract_override']
		else: lstr_modify_type = "invalid"
		
		lstr_result = lobj_master.metric._modify_reserve(lint_network_id, lint_source_account_id, lstr_modify_type, lstr_amount)
		
		lobj_master.request_handler.redirect('/mob_s_modify_reserve?form_result=%s' % lstr_result)
		
# page handler class for "/mob_s_make_payment"
class ph_mob_s_make_payment(webapp2.RequestHandler):

	def get(self):
		
		# Instantiate the master object, do security and other app checks. If
		# there's an interruption return from this function without processing
		# further.
		lobj_master = master(self,"get","secured")
		if lobj_master.IS_INTERRUPTED:return
		
		lobj_master.TRACE.append("ph_mob_s_make_payment.get(): in make_payment GET function")
		
		# make_payment Page
		lobj_master.network_current = lobj_master.metric._get_network_summary()
		
		template = JINJA_ENVIRONMENT.get_template('templates/tpl_mob_s_make_payment.html')
		self.response.write(template.render(master=lobj_master))
		
	def post(self):
		
		# Instantiate the master object, do security and other app checks. If
		# there's an interruption return from this function without processing
		# further.
		lobj_master = master(self,"post","secured")
		if lobj_master.IS_INTERRUPTED:return
		
		lobj_master.TRACE.append("ph_mob_s_make_payment.post(): in make_payment POST function")
		
		
		# make_payment Page
		# Get the current network profile
		lobj_master.network_current = lobj_master.metric._get_network_summary()		
		lint_network_id = lobj_master.network_current.network_id
		lint_source_account_id = lobj_master.user.entity.metric_account_ids
		lint_target_account_id = int(lobj_master.request.POST['form_target_id'])
		lstr_amount = lobj_master.request.POST['form_amount']
		
		lstr_result = lobj_master.metric._make_payment(lint_network_id, lint_source_account_id, lint_target_account_id, lstr_amount)
		
		lobj_master.request_handler.redirect('/mob_s_make_payment?form_result=%s' % lstr_result)
		
		
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
	('/mob_s_disconnect', ph_mob_s_disconnect),
	('/mob_s_modify_reserve', ph_mob_s_modify_reserve),
	('/mob_s_make_payment', ph_mob_s_make_payment),
	('/mobile_scaffold1', ph_mob_s_scaffold1),
	('/mobile_test_form1', ph_mob_s_test_form1)
	],debug=True)

##########################################################################
# END: Python Entry point.  This function should be permanent.
##########################################################################


