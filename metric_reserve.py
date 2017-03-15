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
import random

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
###  SETTINGS
###
################################################################

NUM_BALANCE_POSITIVE_SHARDS = 20
NUM_BALANCE_NEGATIVE_SHARDS = 20
NUM_RESERVE_POSITIVE_SHARDS = 20
NUM_RESERVE_NEGATIVE_SHARDS = 20

IS_DEBUG = True

GRAPH_FREQUENCY_MINUTES = 15

# $1 of value = 100,000
MAX_RESERVE_MODIFY = 100000000
MAX_PAYMENT = 100000000

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
	outgoing_connection_requests = ndb.PickleProperty(default="EMPTY")
	incoming_connection_requests = ndb.PickleProperty(default="EMPTY")
	incoming_reserve_transfer_requests = ndb.PickleProperty()
	outgoing_reserve_transfer_requests = ndb.PickleProperty()
	suggested_reserve_transfer_requests = ndb.PickleProperty()
	current_timestamp = ndb.DateTimeProperty(auto_now_add=True)
	current_connections = ndb.PickleProperty(default="EMPTY")
	current_reserve_balance = ndb.IntegerProperty()
	current_network_balance = ndb.IntegerProperty()	
	last_connections = ndb.PickleProperty(default="EMPTY")
	last_reserve_balance = ndb.IntegerProperty()
	last_network_balance = ndb.IntegerProperty()
	
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
		self.IS_DEBUG = IS_DEBUG
		# For my own "stack" tracing I just append to a delimited list for later output.
		self.TRACE = []
		
		# Start with what time it is:
		self.TRACE.append("current time:%s" % str(datetime.datetime.now()))
		
		# Calculate the graph process cutoff time for this request
		t_epoch = datetime.datetime(2017, 3, 13, 8, 0, 0, 0)
		t_now = datetime.datetime.now()
		d_since = t_now - t_epoch
		# this requests cutoff time
		t_cutoff = t_now - datetime.timedelta(seconds=(d_since.total_seconds() % (GRAPH_FREQUENCY_MINUTES * 60)))
		self.TRACE.append("request cutoff time:%s" % str(t_cutoff))
		
		
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
		

# this is metric reserve class, containing the P2P network/accounting related functionality
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
		lds_metric_account.outgoing_connection_requests = []
		lds_metric_account.incoming_connection_requests = []
		lds_metric_account.incoming_reserve_transfer_requests = []
		lds_metric_account.outgoing_reserve_transfer_requests = []
		lds_metric_account.suggested_reserve_transfer_requests = []
		lds_metric_account.current_connections = []
		lds_metric_account.current_reserve_balance = 0
		lds_metric_account.current_network_balance = 0	
		lds_metric_account.last_connections = []
		lds_metric_account.last_reserve_balance = 0
		lds_metric_account.last_network_balance = 0
		lds_metric_account.key = metric_account_key
		
		# put the metric account id into the user object so we know this user is joined
		lds_user.metric_network_ids = "%s" % fstr_network_id
		lds_user.metric_account_ids = "%s" % str(lds_cursor.current_index).zfill(12)
		
		# save the transaction
		lds_user.put()
		lds_metric_account.put()
		lds_cursor.put()
		
		return "success"
		
	@ndb.transactional(xg=True)
	def _connect(self, fstr_network_id, fstr_source_account_id, fstr_target_account_id):
	
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
		
		source_key = ndb.Key("ds_mr_metric_account", "%s%s" % (fstr_network_id, fstr_source_account_id))
		lds_source = source_key.get()
		
		# error if source doesn't exist
		if lds_source is None: return "error_source_id_not_valid"
		# error if trying to connect to self
		if fstr_source_account_id == fstr_target_account_id: return "error_cant_connect_to_self"
		
		target_key = ndb.Key("ds_mr_metric_account", "%s%s" % (fstr_network_id, fstr_target_account_id))
		lds_target = target_key.get()
		
		# error if target doesn't exist
		if lds_target is None: return "error_target_id_not_valid"

		# Five situations where we don't even try to connect
		# 1. Source and target are already connected.
		if fstr_target_account_id in lds_source.current_connections: return "error_already_connected"
		# 2. Source already has outgoing connection request to target
		if fstr_target_account_id in lds_source.outgoing_connection_requests: return "error_connection_already_requested"
		# 3. Target incoming connection requests is maxed out
		if len(lds_target.incoming_connection_requests) > 19: return "error_target_incoming_requests_maxed"
		# 4. Source outgoing connection requests is maxed out
		if len(lds_source.outgoing_connection_requests) > 19: return "error_target_incoming_requests_maxed"
		# 5. Target or source has reached their maximum number of connections
		if len(lds_source.current_connections) > 19: return "error_source_connections_maxed"
		if len(lds_target.current_connections) > 19: return "error_target_connections_maxed"
		
		# should be ok to connect
		# check if the target has the source in it's outgoing connection requests
		if fstr_source_account_id in lds_target.outgoing_connection_requests:
			
			# target already connected, this is a connection request authorization
			
			# First thing we need to do-and probably should abstract this later STUB
			# since we will need in other places-is we need to figure out our cutoff
			# time for "current_timestamp" based on graph processing frequency.
			#
			# My basic idea is to subtract the frequencies modulus since epoch time
			# (which I'm arbitralily making 8am UTC March 13th, 2017) from the current
			# datetime.  We'll set frequency in minutes but convert to seconds since
			# that's what timedelta uses in python.
			
			t_epoch = datetime.datetime(2017, 3, 13, 8, 0, 0, 0)
			t_now = datetime.datetime.now()
			d_since = t_now - t_epoch
			# this requests cutoff time
			t_cutoff = t_now - datetime.timedelta(seconds=(d_since.total_seconds() % (GRAPH_FREQUENCY_MINUTES * 60)))
			
			# Worthy to note here, perhaps, is that we are evaluating the "old" 
			# current_timestamps for the two parties involved independently, even though the 
			# "new" current_timestamp will be the same.
			
			# update the source account
			if lds_source.current_timestamp > t_cutoff:
				
				# last transaction was in current time window, no need to swap
				# a.k.a. overwrite current
				lds_source.current_connections.append(fstr_target_account_id)
				lds_source.incoming_connection_requests.remove(fstr_target_account_id)
				
			else:
			
				# last transaction was in previous time window, swap
				# a.k.a. move "old" current into "last" before overwriting
				lds_source.last_connections = lds_source.current_connections
				lds_source.last_reserve_balance = lds_source.current_reserve_balance
				lds_source.last_network_balance = lds_source.current_network_balance
				lds_source.current_connections.append(fstr_target_account_id)
				lds_source.incoming_connection_requests.remove(fstr_target_account_id)
				
	
			# update the target account
			if lds_target.current_timestamp > t_cutoff:
				
				# last transaction was in current time window, no need to swap
				# a.k.a. overwrite current
				lds_target.current_connections.append(fstr_source_account_id)
				lds_target.outgoing_connection_requests.remove(fstr_source_account_id)
				
			else:
			
				# last transaction was in previous time window, swap
				# a.k.a. move "old" current into "last" before overwriting
				lds_target.last_connections = lds_source.current_connections
				lds_target.last_reserve_balance = lds_source.current_reserve_balance
				lds_target.last_network_balance = lds_source.current_network_balance
				lds_target.current_connections.append(fstr_source_account_id)
				lds_target.outgoing_connection_requests.remove(fstr_source_account_id)
			
			# only update current_timestamp for graph dependent transactions??? STUB
			lds_source.current_timestamp = datetime.datetime.now()
			lds_target.current_timestamp = datetime.datetime.now()
			lds_source.put()
			lds_target.put()			
			return "success_connection_request_authorized"
			
			
		else:
			# target not yet connected, this is a connection request
			lds_source.outgoing_connection_requests.append(fstr_target_account_id)
			lds_target.incoming_connection_requests.append(fstr_source_account_id)
			lds_source.put()
			lds_target.put()
			return "success_connection_request_completed"
		
	
	@ndb.transactional(xg=True)
	def _disconnect(self, fstr_network_id, fstr_source_account_id, fstr_target_account_id):
	
		source_key = ndb.Key("ds_mr_metric_account", "%s%s" % (fstr_network_id, fstr_source_account_id))
		lds_source = source_key.get()
		
		# error if source doesn't exist
		if lds_source is None: return "error_source_id_not_valid"
		# error if trying to disconnect from self
		if fstr_source_account_id == fstr_target_account_id: return "error_cant_disconnect_from_self"
		
		target_key = ndb.Key("ds_mr_metric_account", "%s%s" % (fstr_network_id, fstr_target_account_id))
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
		
		if fstr_target_account_id in lds_source.incoming_connection_requests:
		
			# benign change with respect to graph
			lds_source.incoming_connection_requests.remove(fstr_target_account_id)
			lds_target.outgoing_connection_requests.remove(fstr_source_account_id)
			lds_source.put()
			lds_target.put()
			return "success_denied_target_connection_request"
		
		elif fstr_target_account_id in lds_source.outgoing_connection_requests:
		
			# benign change with respect to graph
			lds_target.incoming_connection_requests.remove(fstr_target_account_id)
			lds_source.outgoing_connection_requests.remove(fstr_source_account_id)
			lds_source.put()
			lds_target.put()
			return "success_withdrew_connection_request"
		
		elif fstr_target_account_id in lds_source.current_connections:
		
			# update the source account
			if lds_source.current_timestamp > t_cutoff:
				
				# last transaction was in current time window, no need to swap
				# a.k.a. overwrite current
				lds_source.current_connections.remove(fstr_target_account_id)
				
			else:
			
				# last transaction was in previous time window, swap
				# a.k.a. move "old" current into "last" before overwriting
				lds_source.last_connections = lds_source.current_connections
				lds_source.last_reserve_balance = lds_source.current_reserve_balance
				lds_source.last_network_balance = lds_source.current_network_balance
				lds_source.current_connections.remove(fstr_target_account_id)				
	
			# update the target account
			if lds_target.current_timestamp > t_cutoff:
				
				# last transaction was in current time window, no need to swap
				# a.k.a. overwrite current
				lds_target.current_connections.remove(fstr_source_account_id)
				
			else:
			
				# last transaction was in previous time window, swap
				# a.k.a. move "old" current into "last" before overwriting
				lds_target.last_connections = lds_source.current_connections
				lds_target.last_reserve_balance = lds_source.current_reserve_balance
				lds_target.last_network_balance = lds_source.current_network_balance
				lds_target.current_connections.remove(fstr_source_account_id)
				
			# only update current_timestamp for graph dependent transactions??? STUB
			lds_source.current_timestamp = datetime.datetime.now()
			lds_target.current_timestamp = datetime.datetime.now()
			lds_source.put()
			lds_target.put()
			return "success_cancelled_connection"
			
		else: return "error_nothing_to_disconnect"
		
	@ndb.transactional(xg=True)
	def _modify_reserve(self, fstr_network_id, fstr_source_account_id, fstr_type, fstr_amount):

		# First, get the source account.
		source_key = ndb.Key("ds_mr_metric_account", "%s%s" % (fstr_network_id, fstr_source_account_id))
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
			lint_amount = int(fstr_amount)
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
			lds_counter1.count += 1
			lds_counter1.put()
			
			# increment positive reserve shard
			lint_shard_string_index = str(random.randint(0, NUM_RESERVE_POSITIVE_SHARDS - 1))
			lds_counter2 = ds_mr_positive_reserve_shard.get_by_id(lint_shard_string_index)
			if lds_counter2 is None:
				lds_counter2 = ds_mr_positive_reserve_shard(id=lint_shard_string_index)
			lds_counter2.count += 1
			lds_counter2.put()
			
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
			lds_counter3.count += 1
			lds_counter3.put()
			
			# increment negative reserve shard
			lint_shard_string_index = str(random.randint(0, NUM_RESERVE_NEGATIVE_SHARDS - 1))
			lds_counter4 = ds_mr_negative_reserve_shard.get_by_id(lint_shard_string_index)
			if lds_counter4 is None:
				lds_counter4 = ds_mr_negative_reserve_shard(id=lint_shard_string_index)
			lds_counter4.count += 1
			lds_counter4.put()
			
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
			lds_counter5.count += 1
			lds_counter5.put()
			
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
			lds_counter6.count += 1
			lds_counter6.put()
			
			lstr_return_message = "success_reserve_override_subtract"
			
		else: return "error_invalid_transaction_type"
		
		# If we're here, then we modified something, so need to do 
		# graph process time window check before saving data. Reserve
		# modification always effects the graph state.
		
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

		# only update current_timestamp for graph dependent transactions??? STUB
		lds_source.current_timestamp = datetime.datetime.now()
		lds_source.put()
		return lstr_return_message

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
		
		lobj_master.TRACE.append("ph_mob_s_connect.post(): in connect POST function")
		
		
		# Connect Page
		# Get the current network profile
		lobj_master.network_connecting = lobj_master.metric._get_network_summary()
		lstr_network_id = lobj_master.network_connecting.network_id
		lstr_source_account_id = lobj_master.user.entity.metric_account_ids
		lstr_target_account_id = lobj_master.request.POST['form_target_id']
		lstr_result = lobj_master.metric._connect(lstr_network_id, lstr_source_account_id, lstr_target_account_id)
		
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
		lstr_network_id = lobj_master.network_connecting.network_id
		lstr_source_account_id = lobj_master.user.entity.metric_account_ids
		lstr_target_account_id = lobj_master.request.POST['form_target_id']
		lstr_result = lobj_master.metric._disconnect(lstr_network_id, lstr_source_account_id, lstr_target_account_id)
		
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
		lstr_network_id = lobj_master.network_current.network_id
		lstr_source_account_id = lobj_master.user.entity.metric_account_ids
		
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
		
		lstr_result = lobj_master.metric._modify_reserve(lstr_network_id, lstr_source_account_id, lstr_modify_type, lstr_amount)
		
		lobj_master.request_handler.redirect('/mob_s_modify_reserve?form_result=%s' % lstr_result)
		
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
	('/mobile_scaffold1', ph_mob_s_scaffold1),
	('/mobile_test_form1', ph_mob_s_test_form1)
	],debug=True)

##########################################################################
# END: Python Entry point.  This function should be permanent.
##########################################################################


