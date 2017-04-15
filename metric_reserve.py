"""


DATASTORE: USER AND ACCOUNT RELATED

	ds_mr_user
	ds_mr_user_message
	ds_mr_unique_dummy_entity
	ds_mr_network_profile
	ds_mr_system_cursor
	ds_mr_network_cursor
	ds_mr_metric_account
	ds_mr_tx_log

DATASTORE: COUNTER RELATED

	ds_mr_positive_balance_shard
	ds_mr_negative_balance_shard
	ds_mr_positive_reserve_shard
	ds_mr_negative_reserve_shard

DATASTORE: GRAPH RELATED

	ds_mrgp_profile
	ds_mrgp_staging_chunk
	ds_mrgp_index_chunk
	ds_mrgp_tree_chunk
	ds_mrgp_report_chunk
	ds_mrgp_map_chunk

DATASTORE: DEBUG RELATED

	ds_mrgp_big_pickle


CLASS: master(object)

	def __init__(self, fobj_request,fstr_request_type,fstr_security_req)

CLASS: user(object)

	def __init__(self, fobj_master)
	def _load_user(self,fobj_google_account)
	def _create_user_transactional(self,fstr_username,fobj_google_obj)

	@ndb.transactional(xg=True)
	def _create_user_transactional(self,fstr_username,fobj_google_obj)

	@ndb.transactional(xg=True)
	def _change_username_transactional(self,fstr_username)

	def _message(self,fstr_target_name,fstr_text)
	def _get_gravatar_url(self,user_obj,size=80)
		
	@ndb.transactional()	
	def _modify_user(self,fkey,fvalue):

CLASS: metric(object)

	def __init__(self, fobj_master)

	@ndb.transactional(xg=True)
	def _network_add(self,fname)

	@ndb.transactional(xg=True)
	def _network_modify(self,fname,fnewname=None,fdescription=None,fskintillionths=None,ftype=None,fstatus=None,delete_network=False)

	def _get_all_accounts(self,fstr_network_name)
	def _get_all_networks(self)
	def _get_network(self,fstr_network_name=None,fint_network_id=None)

	@ndb.transactional(xg=True)
	def _save_unique_alias(self,fstr_alias,fint_network_id,fint_account_id)

	@ndb.transactional(xg=True)
	def _alias_change_transactional(self,fstr_current_alias,fstr_new_alias=None,fbool_delete=False)

	@ndb.transactional(xg=True)
	def _get_account_label(self,fint_network_id,fint_account_id)

	@ndb.transactional(xg=True)
	def _other_account_transactional(self,fstr_network_name,fstr_source_name,fstr_target_name,fstr_type)

	@ndb.transactional(xg=True)
	def _reserve_open_transactional(self,fstr_network_name)

	@ndb.transactional(xg=True)
	def _name_validate_transactional(self,fstr_network_name,fstr_source_name=None,fstr_target_name=None)
	
	@ndb.transactional(xg=True)
	def _connect_transactional(self,fstr_network_name,fstr_source_name,fstr_target_name)	
	
	@ndb.transactional(xg=True)
	def _disconnect_transactional(self, fstr_network_name, fstr_source_name, fstr_target_name)	
	
	def _modify_reserve(self,fstr_network_name,fstr_source_name,fstr_type,fstr_amount)	
	
	@ndb.transactional(xg=True)
	def _modify_reserve_transactional(self,fstr_network_name,fstr_source_name,fstr_type,fstr_amount,fint_conversion)
	
	def _make_payment(self,fstr_network_name,fstr_source_name,fstr_target_name,fstr_amount)
	
	@ndb.transactional(xg=True)
	def _make_payment_transactional(self,fstr_network_name,fstr_source_name,fstr_target_name,fstr_amount,fint_conversion)

	def _process_reserve_transfer(self,fstr_network_name,fstr_source_name,fstr_target_name,fstr_amount,fstr_type)

	@ndb.transactional(xg=True)
	def _process_reserve_transfer_transactional(self,fstr_network_name,fstr_source_name,fstr_target_name,fstr_amount,fstr_type,fint_conversion)

	@ndb.transactional(xg=True)
	def _leave_network(self, fstr_network_name,fstr_source_name)

	@ndb.transactional(xg=True)
	def _joint_retrieve_transactional(self, fstr_network_name,fstr_source_name,fstr_target_name,fstr_amount,fint_conversion)

	def _get_default(self,fstr_network_name,fstr_source_name):

	def _set_default(self,fstr_network_name,fstr_source_name):

	@ndb.transactional(xg=True)
	def _set_default_transactional(self,fint_network_id,fstr_source_name):

	STUB def _create_ticket(self,fstr_network_name,fstr_source_name,fstr_amount,fstr_ticket_name)
	
	STUB @ndb.transactional(xg=True)
	STUB def _create_ticket_transactional(self,fstr_network_name,fstr_source_name,fstr_amount,fint_conversion)	

	def _process_graph(self, fint_network_id)


"""


############################################################################79
###
###  IMPORTS
###
##############################################################################

# These are standard python libraries.
import os
import urllib
import hashlib
import datetime
import time
import re
import pickle
import random
import bisect
from operator import itemgetter
from decimal import *
# for debugging on dev_appserver.py only
import pdb
# how to invoke: Just put this on any line: "pdb.set_trace()"
# read about pdb: https://cloud.google.com/appengine/docs/standard/python/tools/using-local-server#Python_Debugging_with_PDB

# these are standard GAE imports
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.datastore.datastore_query import Cursor

# These are app.yaml imports.
import webapp2
import jinja2

# These are my custom modules.
# [example]: from [directory] import [some py file without extension]
from library import mdetect

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

	user_id = ndb.StringProperty(indexed=False)
	username = ndb.StringProperty(indexed=False,default="EMPTY")
	email = ndb.StringProperty(indexed=False)
	
	user_status = ndb.StringProperty(indexed=False)
	
	name_first = ndb.StringProperty(indexed=False)
	name_middle = ndb.StringProperty(indexed=False)
	name_last = ndb.StringProperty(indexed=False)
	name_suffix = ndb.StringProperty(indexed=False)
	
	gravatar_url = ndb.StringProperty(indexed=False)
	gravatar_type = ndb.StringProperty(default="identicon",indexed=False)
	bio = ndb.TextProperty(indexed=False)
	location_latitude = ndb.IntegerProperty(default=3905580000,indexed=False)
	location_longitude = ndb.IntegerProperty(default=-9568900000,indexed=False)
	
	date_created = ndb.DateTimeProperty(auto_now_add=True,indexed=False)
	
	total_reserve_accounts = ndb.IntegerProperty(default=0,indexed=False) # 30 max
	total_other_accounts = ndb.IntegerProperty(default=0,indexed=False) # 20 max
	total_child_accounts = ndb.IntegerProperty(default=0,indexed=False) # 20 max
	
	reserve_network_ids = ndb.PickleProperty()
	reserve_account_ids = ndb.PickleProperty()
	reserve_labels = ndb.PickleProperty()
	reserve_default = ndb.PickleProperty()
	
	client_network_ids = ndb.PickleProperty()
	client_account_ids = ndb.PickleProperty()
	client_parent_ids = ndb.PickleProperty()
	client_labels = ndb.PickleProperty()
	client_default = ndb.PickleProperty()
	parent_client_offer_network_id = ndb.IntegerProperty(default=0,indexed=False)
	parent_client_offer_account_id = ndb.IntegerProperty(default=0,indexed=False)
	parent_client_offer_user_id = ndb.StringProperty(default="EMPTY",indexed=False)
	
	joint_network_ids = ndb.PickleProperty()
	joint_account_ids = ndb.PickleProperty()
	joint_parent_ids = ndb.PickleProperty()
	joint_labels = ndb.PickleProperty()
	joint_default = ndb.PickleProperty()
	parent_joint_offer_network_id = ndb.IntegerProperty(default=0,indexed=False)
	parent_joint_offer_account_id = ndb.IntegerProperty(default=0,indexed=False)
	parent_joint_offer_user_id = ndb.StringProperty(default="EMPTY",indexed=False)
	
	clone_network_ids = ndb.PickleProperty()
	clone_account_ids = ndb.PickleProperty()
	clone_parent_ids = ndb.PickleProperty()
	clone_labels = ndb.PickleProperty()
	clone_default = ndb.PickleProperty()
	
	child_client_network_ids = ndb.PickleProperty()
	child_client_account_ids = ndb.PickleProperty()
	child_client_parent_ids = ndb.PickleProperty()
	child_client_offer_network_id = ndb.IntegerProperty(default=0,indexed=False)
	child_client_offer_account_id = ndb.IntegerProperty(default=0,indexed=False)
	child_client_offer_user_id = ndb.StringProperty(default="EMPTY",indexed=False)
	
	child_joint_network_ids = ndb.PickleProperty()
	child_joint_account_ids = ndb.PickleProperty()
	child_joint_parent_ids = ndb.PickleProperty()
	child_joint_offer_network_id = ndb.IntegerProperty(default=0,indexed=False)
	child_joint_offer_account_id = ndb.IntegerProperty(default=0,indexed=False)
	child_joint_offer_user_id = ndb.StringProperty(default="EMPTY",indexed=False)
	
	extra_pickle = ndb.PickleProperty()

# a Model for user messages
class ds_mr_user_message(ndb.Model):

	date_created = ndb.DateTimeProperty(auto_now_add=True)
	create_user_id = ndb.StringProperty()
	target_user_id = ndb.StringProperty()
	message_content = ndb.PickleProperty()
	gravatar_url = ndb.StringProperty(indexed=False)
	gravatar_type = ndb.StringProperty(indexed=False)
	username = ndb.StringProperty(indexed=False)

# this is just an entity solely used to enforce name uniqueness in other
# objects via transactions google's datastore requires a little extra work
# to enforce a unique constraint
class ds_mr_unique_dummy_entity(ndb.Model):

	unique_name = ndb.StringProperty(indexed=False)
	name_type = ndb.StringProperty(indexed=False)
	network_id = ndb.IntegerProperty(indexed=False)
	account_id = ndb.IntegerProperty(indexed=False)
	user_id = ndb.StringProperty(indexed=False)
	date_created = ndb.DateTimeProperty(auto_now_add=True,indexed=False)

# network profile: this entity contains information about specific graph
class ds_mr_network_profile(ndb.Model):

	network_name = ndb.StringProperty(indexed=False)
	network_id = ndb.IntegerProperty(indexed=False)
	network_status = ndb.StringProperty(indexed=False,default="INACTIVE")
	network_type = ndb.StringProperty(indexed=False,default="LIVE")
	description = ndb.StringProperty(indexed=False)
	skintillionths = ndb.IntegerProperty(indexed=False,default=100000)
	orphan_count = ndb.IntegerProperty(indexed=False)
	total_trees = ndb.IntegerProperty(indexed=False)
	last_graph_process = ndb.StringProperty(default="EMPTY",indexed=False)
	date_created = ndb.DateTimeProperty(auto_now_add=True,indexed=False)

# system settings
class ds_mr_system_settings(ndb.Model):

	data = ndb.PickleProperty()

# network cursor: this entity maintains the index of networks
class ds_mr_system_cursor(ndb.Model):

	current_index = ndb.IntegerProperty(indexed=False)
	
# network cursor: this entity maintains the index of network accounts
class ds_mr_network_cursor(ndb.Model):

	network_id = ndb.IntegerProperty(indexed=False)
	current_index = ndb.IntegerProperty(indexed=False)

# metric account: this is the main account information
class ds_mr_metric_account(ndb.Model):

	account_id = ndb.IntegerProperty(indexed=False)
	network_id = ndb.IntegerProperty(indexed=False)
	user_id = ndb.StringProperty(indexed=False)
	tx_index = ndb.IntegerProperty(indexed=False)
	decimal_places = ndb.IntegerProperty(default=2,indexed=False)
	account_status = ndb.StringProperty(indexed=False)
	account_type = ndb.StringProperty(indexed=False)
	account_parent = ndb.IntegerProperty(default=0,indexed=False)
	outgoing_connection_requests = ndb.PickleProperty()
	incoming_connection_requests = ndb.PickleProperty()
	incoming_reserve_transfer_requests = ndb.PickleProperty()
	outgoing_reserve_transfer_requests = ndb.PickleProperty()
	suggested_inactive_incoming_reserve_transfer_requests = ndb.PickleProperty()
	suggested_inactive_outgoing_reserve_transfer_requests = ndb.PickleProperty()
	suggested_active_incoming_reserve_transfer_requests = ndb.PickleProperty()
	suggested_active_outgoing_reserve_transfer_requests = ndb.PickleProperty()
	current_timestamp = ndb.DateTimeProperty(auto_now_add=True,indexed=False)
	current_connections = ndb.PickleProperty()
	current_reserve_balance = ndb.IntegerProperty(default=0,indexed=False)
	current_network_balance = ndb.IntegerProperty(default=0,indexed=False)	
	last_connections = ndb.PickleProperty()
	last_reserve_balance = ndb.IntegerProperty(default=0,indexed=False)
	last_network_balance = ndb.IntegerProperty(default=0,indexed=False)
	date_created = ndb.DateTimeProperty(auto_now_add=True,indexed=False)
	extra_pickle = ndb.PickleProperty()

# metric ticket
class ds_mr_metric_ticket_index(ndb.Model):

	account_id = ndb.IntegerProperty(indexed=False)
	network_id = ndb.IntegerProperty(indexed=False)
	user_id = ndb.StringProperty(indexed=False)
	ticket_data = ndb.PickleProperty()
	
class ds_mr_metric_ticket_tape(ndb.Model):

	ticket_name = ndb.StringProperty(indexed=False)
	ticket_tape = ndb.PickleProperty()

class ds_mr_metric_ticket_plu(ndb.Model):

	plu_data = ndb.PickleProperty()

# transaction log:  think "bank statements"
class ds_mr_tx_log(ndb.Model):

	category = ndb.StringProperty(default="MRTX",indexed=False)
	tx_index = ndb.IntegerProperty(default=0,indexed=False)
	tx_type = ndb.StringProperty(indexed=False) # should always be set when used
	amount = ndb.IntegerProperty(default=0,indexed=False)
	access = ndb.StringProperty(default="PUBLIC",indexed=False)
	description = ndb.StringProperty(default=None,indexed=False) # should always be set when used
	memo = ndb.StringProperty(default=None,indexed=False)
	date_created = ndb.DateTimeProperty(auto_now_add=True,indexed=False)
	user_id_created = ndb.StringProperty(default="SYSTEM",indexed=False)
	network_id = ndb.IntegerProperty(default=0,indexed=False)
	account_id = ndb.IntegerProperty(default=0,indexed=False)
	source_account = ndb.IntegerProperty(default=0,indexed=False)
	target_account = ndb.IntegerProperty(default=0,indexed=False)
	current_network_balance = ndb.IntegerProperty(default=0,indexed=False)
	current_reserve_balance = ndb.IntegerProperty(default=0,indexed=False)
	
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

class ds_multi_mrgp_profile(ndb.Model):
	current_time_key = ndb.StringProperty(indexed=False)
	current_status = ndb.StringProperty(indexed=False)
	network_index = ndb.StringProperty(indexed=False)

class ds_mrgp_profile(ndb.Model):

	status = ndb.StringProperty(indexed=False)
	deadline = ndb.DateTimeProperty(indexed=False)
	max_account = ndb.IntegerProperty(indexed=False)
	phase_cursor = ndb.IntegerProperty(indexed=False)
	tree_cursor = ndb.IntegerProperty(indexed=False)
	count_cursor = ndb.IntegerProperty(indexed=False)
	tree_chunks = ndb.IntegerProperty(indexed=False)
	tree_in_process = ndb.BooleanProperty(indexed=False)
	index_chunks = ndb.IntegerProperty(indexed=False)
	parent_pointer = ndb.IntegerProperty(indexed=False)
	child_pointer = ndb.IntegerProperty(indexed=False)
	index_chunk_counter = ndb.IntegerProperty(indexed=False)
	tree_chunk_counter = ndb.IntegerProperty(indexed=False)
	map_chunk_counter = ndb.IntegerProperty(indexed=False)
	report = ndb.PickleProperty(indexed=False)

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
# *** the map chunk ***
class ds_mrgp_map_chunk(ndb.Model):
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
	
		@ndb.transactional()
		def create_system_settings_object():		
			settings_key = ndb.Key("ds_mr_system_settings", "metric_reserve_settings")
			lds_settings = settings_key.get()
			if not lds_settings is None:
				return lds_settings
			lds_settings = ds_mr_system_settings()
			lds_settings.key = settings_key
			lds_settings.data = {}
			# set default dict keys
			# lds_settings.data["some_key"] = "" 
			# blank if secured/set at run time or "some value" if no biggy to keep on github, etc.
			lds_settings.data["google_maps_api_key"] = "EMPTY"
			lds_settings.put()
			return lds_settings			
		# load settings
		settings_key = ndb.Key("ds_mr_system_settings", "metric_reserve_settings")
		settings_entity = settings_key.get()
		if settings_entity is None:
			settings_entity = create_system_settings_object()
		self.SETTINGS = settings_entity
		
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
		self.DEBUG_VARS = {}
		# A var for functions in different objects to pass around error/success codes
		self.RETURN_CODE = ""
		
		# see if this site is being viewed on mobile browser
		self.IS_MOBILE = False
		user_agent = self.request.headers["User-Agent"]
		http_accept = self.request.headers["Accept"]
		if user_agent and http_accept:
			agent = mdetect.UAgentInfo(userAgent=user_agent, httpAccept=http_accept)
			is_tablet = agent.detectTierTablet()
			is_phone = agent.detectTierIphone()
			if is_tablet or is_phone or agent.detectMobileQuick():
				self.IS_MOBILE = True
				self.TRACE.append("mobile detected")
			else:
				self.TRACE.append("mobile not detected")
		
		# instantiate a user via class - see 'class user(object)'
		self.user = user(self)
		
		# instantiate the metric object
		self.metric = metric(self)
		
		# sometimes our security or other app checks (like system being offline) 
		# interrupt normal page processing and return other information like errors
		# to the browser. So each page handler class will break out before processing
		# if this variable becomes true.
		self.IS_INTERRUPTED = False
		
		
		
		
		###############################################
		###############################################
		#DEBUG STUFF BEGIN
		###############################################
		###############################################
		
		# mobile QR link for debug
		self.QR1_DEBUG = self._get_qr_url(("https://8080-dot-2189742-dot-devshell.appspot.com" + self.request.path_qs))
				
		
		# GRAVATAR/IDENTICON TESTING
		#lstr_gravatar_url = hashlib.md5("wizardwatson@gmail.com".lower()).hexdigest() + "?s=80&d=identicon&f=y" 
		#d=identicon
		#f=y  ...means force the default
		#s is size
		#self.DEBUG_VARS["gravatar_test"] = ('https://www.gravatar.com/avatar/%s' % lstr_gravatar_url)
		

		# Start with what time it is:
		self.TRACE.append("current time:%s" % str(datetime.datetime.now()))
		
		
		
		"""
		tree_index_test = ds_mrgp_big_pickle()
		tree_index_test.stuff = []
		for i in range(1,150001):
			tree_index_test.stuff.append(random.randint(1,9000000))
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
		
		"""
		
		
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
		
		
		
		###############################################
		###############################################
		#DEBUG STUFF END
		###############################################
		###############################################
		
		"""
		OLD SECURITY PATTERN
		NO LONGER USED
		

		
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
		"""

	def _get_qr_url(self,furl,size=200):
	
		# mobile QR link for debug
		qr_link_base = "https://chart.googleapis.com/chart?cht=qr&chs=" + str(size) + "&chl="
		return qr_link_base + urllib.quote_plus(furl)
		
	@ndb.transactional()
	def _modify_settings(self,fkey,fvalue):
	
		"""
		@ndb.transactional()
		def create_system_settings_object(self):		
			settings_key = ndb.Key("ds_mr_system_settings", "metric_reserve_settings")
			lds_settings = settings_key.get()
			if not lds_settings is None:
				return lds_settings
			lds_settings = ds_mr_system_settings()
			lds_settings.key = settings_key
			# set default dict keys
			# lds_settings.data["some_key"] = "" 
			# blank if secured/set at run time or "some value" if no biggy to keep on github, etc.
			lds_settings.put()
			return lds_settings			
		# load settings
		settings_key = ndb.Key("ds_mr_system_settings", "metric_reserve_settings")
		settings_entity = settings_key.get()
		if settings_entity is None:
			settings_entity = create_system_settings_object()
			return None # False meaning "not created"
		self.SETTINGS = settings_entity
		"""
	
	
		# get settings object transactionally
		settings_key = ndb.Key("ds_mr_system_settings","metric_reserve_settings")
		settings_entity = settings_key.get()
		if not settings_entity:
			self.RETURN_CODE = "1276"
			return False # error Couldn't load system setttings
		
		if fkey.lower() not in settings_entity.data:
			self.RETURN_CODE = "1277"
			return False # error System settings variable name invalid.

		if fkey == "google_maps_api_key":
			settings_entity.data[fkey] = fvalue
	
		"""
		if fkey == "my_key":
			settings_entity.data[my_key] = fvalue
		"""				
		
		settings_entity.put()
		self.RETURN_CODE = "7056" # success Successfully modified system settings.
		return True

	def dump(self,fdump):
		self.page = {}
		self.page["title"] = "DUMP"
		self.DUMP = True
		self.DUMP_STUFF = fdump
		template = JINJA_ENVIRONMENT.get_template('templates/tpl_mob_command.html')
		self.response.write(template.render(master=self))

		
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
			# So that our entity references resolve in function definitions
			# when not logged in, go ahead and assign self.entity to the class
			# even though we never reference in logic if not logged in.
			self.entity = ds_mr_user()
		
		# GAE Authentication Variables
		self.LOG_IN_GAE_HREF = users.create_login_url(self.PARENT.request.path)
		self.LOG_IN_GAE_LINKTEXT = 'Login'
		self.LOG_OUT_GAE_HREF = users.create_logout_url('/')
		self.LOG_OUT_GAE_LINKTEXT = 'Logout'
		
   	def _load_user(self,fobj_google_account):
   
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
			while True:
				# new users get temporary username automatically upon first login
				some_letters = "abcdefghijkmnprstuvwxyz"
				first_int = str(random.randint(1,999)).zfill(3)
				second_int = str(random.randint(1,999)).zfill(3)
				temp_username = "user" + first_int + second_int + random.choice(some_letters) + random.choice(some_letters)			
				ldata_user = self._create_user_transactional(temp_username,fobj_google_account)
				if not ldata_user is None:
					break
		return ldata_user
		
	@ndb.transactional(xg=True)
	def _create_user_transactional(self,fstr_username,fobj_google_obj):
	
		# new name check
		maybe_new_key = ndb.Key("ds_mr_unique_dummy_entity", fstr_username)
		maybe_dummy_entity = maybe_new_key.get()
		if maybe_dummy_entity is not None:
			self.PARENT.TRACE.append("metric._save_unique_name():entity was returned")
			return None # False meaning "not created"
		self.PARENT.TRACE.append("metric._save_unique_name():entity was NOT returned")
		new_name_entity = ds_mr_unique_dummy_entity()
		new_name_entity.unique_name = fstr_username
		new_name_entity.key = maybe_new_key 
		
		# this function loads a user entity from a key
		user_key = ndb.Key("ds_mr_user",fobj_google_obj.user_id())
		ldata_user = user_key.get()
		if ldata_user:
			return ldata_user # User already exists
			
		# create a new user
		ldata_user = ds_mr_user()
		ldata_user.user_id = fobj_google_obj.user_id()			
		ldata_user.user_status = 'VERIFIED'
		ldata_user.email = fobj_google_obj.email()
		ldata_user.gravatar_url = fobj_google_obj.email()
		#ldata_user.gravatar_url = "https://www.gravatar.com/avatar/" + hashlib.md5(gravatar_email.lower()).hexdigest() + "?s=40d=identicon"
		ldata_user.key = user_key	

		# set default sequences
		ldata_user.reserve_network_ids = []
		ldata_user.reserve_account_ids = []
		ldata_user.reserve_labels = []
		ldata_user.reserve_default = []

		ldata_user.client_network_ids = []
		ldata_user.client_account_ids = []
		ldata_user.client_parent_ids = []
		ldata_user.client_labels = []
		ldata_user.client_default = []

		ldata_user.joint_network_ids = []
		ldata_user.joint_account_ids = []
		ldata_user.joint_parent_ids = []
		ldata_user.joint_labels = []
		ldata_user.joint_default = []

		ldata_user.clone_network_ids = []
		ldata_user.clone_account_ids = []
		ldata_user.clone_parent_ids = []
		ldata_user.clone_labels = []
		ldata_user.clone_default = []

		ldata_user.child_client_network_ids = []
		ldata_user.child_client_account_ids = []
		ldata_user.child_client_parent_ids = []

		ldata_user.child_joint_network_ids = []
		ldata_user.child_joint_account_ids = []
		ldata_user.child_joint_parent_ids = []
	
		lstr_tx_type = "NEW USER CREATED"
		lstr_tx_description = "A new user was created in the application."
		
		new_name_entity.name_type = "username"
		new_name_entity.user_id = ldata_user.user_id
		# assign new username to user
		ldata_user.user_status = "ACTIVE"
		ldata_user.username = fstr_username
		new_name_entity.put()
		ldata_user.put()
		
		# transaction log:  think "bank statements"
		lds_tx_log = ds_mr_tx_log()
		lds_tx_log.tx_type = lstr_tx_type # SHORT WORD(S) FOR WHAT TRANSACTION DID
		lds_tx_log.description = lstr_tx_description
		lds_tx_log.memo = fstr_username
		lds_tx_log.user_id_created = ldata_user.user_id # google id
		lds_tx_log.put()
		
		return ldata_user
		
	@ndb.transactional(xg=True)
	def _change_username_transactional(self,fstr_username):

		# new username check
		maybe_new_key = ndb.Key("ds_mr_unique_dummy_entity", fstr_username)
		maybe_dummy_entity = maybe_new_key.get()
		if maybe_dummy_entity is not None:
			self.PARENT.TRACE.append("metric._save_unique_name():entity was returned")
			return False # False meaning "not created"			
		new_name_entity = ds_mr_unique_dummy_entity()
		new_name_entity.unique_name = fstr_username
		new_name_entity.key = maybe_new_key
		new_name_entity.name_type = "username"		
		
		# get the user transactionally
		user_key = ndb.Key("ds_mr_user",self.PARENT.user.entity.user_id)
		ldata_user = user_key.get()
		new_name_entity.user_id = ldata_user.user_id
		new_name_entity.put()
		# delete old name making available for others to now use
		old_key = ndb.Key("ds_mr_unique_dummy_entity", ldata_user.username)
		old_key.delete()
		# assign new username to user
		
		# change every label using that old name in account labels to new name
		for i in range(len(ldata_user.reserve_labels)):
			if ldata_user.reserve_labels[i] == ldata_user.username:
				ldata_user.reserve_labels[i] = fstr_username
		for i in range(len(ldata_user.client_labels)):
			if ldata_user.client_labels[i] == ldata_user.username:
				ldata_user.client_labels[i] = fstr_username
		for i in range(len(ldata_user.joint_labels)):
			if ldata_user.joint_labels[i] == ldata_user.username:
				ldata_user.joint_labels[i] = fstr_username
		for i in range(len(ldata_user.clone_labels)):
			if ldata_user.clone_labels[i] == ldata_user.username:
				ldata_user.clone_labels[i] = fstr_username

		ldata_user.username = fstr_username
		ldata_user.put()

		# transaction log:  think "bank statements"
		lds_tx_log = ds_mr_tx_log()
		lds_tx_log.tx_type = "USERNAME CHANGED" # SHORT WORD(S) FOR WHAT TRANSACTION DID
		lds_tx_log.description = "A user changed their username." 
		lds_tx_log.memo = fstr_username
		lds_tx_log.user_id_created = ldata_user.user_id
		lds_tx_log.put()
		
		return True # True meaning "created"
	
	def _get_user_messages(self,fstr_target_name,fstr_fcursor=None,fstr_rcursor=None):
	
		# get target user_id
		name_key = ndb.Key("ds_mr_unique_dummy_entity", fstr_target_name)
		name_entity = name_key.get()
		if name_entity is None:
			self.PARENT.RETURN_CODE = "1279"
			return False # error Target name invalid.

		query = ds_mr_user_message.query(ds_mr_user_message.target_user_id == name_entity.user_id)
		query = query.order(-ds_mr_user_message.date_created)		
		reverse_query = ds_mr_user_message.query(ds_mr_user_message.target_user_id == name_entity.user_id)
		reverse_query = reverse_query.order(ds_mr_user_message.date_created)
		
		messages_per_page = 3
		
		# if both are None then must be beginning.
		# if forward exists user for previous link
		
		if not fstr_rcursor is None:
			# reverse cursor used
			cursor = Cursor(urlsafe=fstr_rcursor)
			reversed_messages, prev_cursor, prev_more = reverse_query.fetch_page(messages_per_page, start_cursor=cursor)
			messages = list(reversed(reversed_messages))
			# the old cursor is now the next cursor
			next_cursor = Cursor(urlsafe=fstr_rcursor)
			next_more = True
		
		if not fstr_fcursor is None:
			# forward cursor used
			cursor = Cursor(urlsafe=fstr_fcursor)
			messages, next_cursor, next_more = query.fetch_page(messages_per_page, start_cursor=cursor)
			# the old cursor is now the previous cursor
			prev_cursor = Cursor(urlsafe=fstr_fcursor)
			prev_more = True
			
		if fstr_fcursor is None and fstr_rcursor is None:
			# if neither cursor passed, we're at beginning
			messages, next_cursor, next_more = query.fetch_page(messages_per_page)
			prev_cursor = None
			prev_more = False
			
		return messages, next_cursor, next_more, prev_cursor, prev_more
	
	def _message(self,fstr_target_name,fstr_text):
	
		"""
		# a Model for user messages
		class ds_mr_user_message(ndb.Model):

			date_created = ndb.DateTimeProperty(auto_now_add=True)
			create_user_id = ndb.StringProperty()
			target_user_id = ndb.StringProperty()
			message_content = ndb.PickleProperty()
		"""
		
		# get target user_id
		name_key = ndb.Key("ds_mr_unique_dummy_entity", fstr_target_name)
		name_entity = name_key.get()
		if name_entity is None:
			self.PARENT.RETURN_CODE = "1230"
			return False # error Target name invalid.
		new_message = ds_mr_user_message()
		new_message.create_user_id = self.PARENT.user.entity.user_id
		new_message.gravatar_url = self.PARENT.user.entity.gravatar_url
		new_message.gravatar_type = self.PARENT.user.entity.gravatar_type
		new_message.username = self.PARENT.user.entity.username
		new_message.target_user_id = name_entity.user_id
		new_message.message_content = fstr_text
		new_message.put()
		self.PARENT.RETURN_CODE = "7057" # success Successfully added message.
		return True

	def _get_gravatar_url(self,fgurl,fgtype,size=80):
		
		# GRAVATAR DOCS
		# http://en.gravatar.com/site/implement/images/
		#
		# Base Request
		# default = "identicon"
		# lstr_email = "myusersemail@mr.com" 
		# lstr_base = "https://www.gravatar.com/avatar/"
		# lstr_hash = hashlib.md5(lstr_email.lower()).hexdigest()
		# lstr_query_string = "?s=80&d=identicon&f=y"urllib.urlencode({'d':default, 's':str(size), 'f':'y'})
		# lstr_url = lstr_base + lstr_hash + lstr_query_string
		#
		# "s" is size in pixels, always square
		# "d" is default, options are:
		#		d=identicon : shows identicon for email hash
		#		d=mm : anonymous mystery man
		# 		d=monsterid : like identicon only monster face
		# 		d=wavatar : like identicon only random faces
		# 		d=retro : like identicon only 8-bit retro graphic
		#		d=blank : transparent PNG aka. nothing
		#		d=404 : no image, return 404 response
		# "f" is forcedefault, set to y if you want to force one of above set defaults
		
		lstr_base = "https://www.gravatar.com/avatar/"
		lstr_hash = hashlib.md5(fgurl.lower()).hexdigest()
		if fgtype == "gravatar":
			lstr_query_string = urllib.urlencode({'s':str(size)})
		else:
			lstr_query_string = urllib.urlencode({'d':fgtype, 's':str(size), 'f':'y'})
		return lstr_base + lstr_hash + "?" + lstr_query_string
		
	@ndb.transactional()	
	def _modify_user(self,fkey,fvalue):
	
		# get user transactionally
		# this function loads a user entity from a key
		user_key = ndb.Key("ds_mr_user",self.PARENT.user.entity.user_id)
		lds_user = user_key.get()
		if not lds_user:
			self.PARENT.RETURN_CODE = "1269"
			return False # error Couldn't load user
		
		if fkey.lower() not in ["gurl","gtype","bio","location"]:
			self.PARENT.RETURN_CODE = "1270"
			return False # error Invalid user modification type.
		
		if fkey == "gurl":
			if fvalue.lower() == "default":
				lds_user.gravatar_url = lds_user.email
			else:
				lds_user.gravatar_url = fvalue
		
		if fkey == "gtype":
			if fvalue.lower() not in ["identicon","mm","monsterid","wavatar","retro","gravatar"]:
				self.PARENT.RETURN_CODE = "1271"
				return False # error Invalid gravatar type value for user modification.
			else:
				lds_user.gravatar_type = fvalue
		
		if fkey == "bio":
			lds_user.bio = fvalue
		
		if fkey == "location":
			# lat/long decimal format, positive negative
			if not len(fvalue.split()) == 2:
				self.PARENT.RETURN_CODE = "1272"
				return False # error User modification for location requires 2 values (lat/long).			
			lat = fvalue.split()[0]
			long = fvalue.split()[1]
			try:
				lat = float(lat)
				long = float(long)
			except:
				self.PARENT.RETURN_CODE = "1273"
				return False # error Invalid lat/long values for user modification.
			if lat < -90 or lat > 90:
				self.PARENT.RETURN_CODE = "1274"
				return False # error Latitude out of range.  Must be between 90 and -90.				
			if long < -180 or long > 180:
				self.PARENT.RETURN_CODE = "1275"
				return False # error Longitude out of range.  Must be between 180 and -180.
			lds_user.location_latitude = int(lat * 100000000)
			lds_user.location_longitude = int(long * 100000000)
			
			
		
		lds_user.put()
		#pdb.set_trace()
		self.PARENT.RETURN_CODE = "7055" # success Successfully modified user.
		return True
			
	def _get_user_list(self,user_list):
	
		pass
			
# this is metric reserve class, containing the P2P network/accounting related functionality
class metric(object):

	# intialization function, called when object is instantiated with or without a function call
	def __init__(self, fobj_master):
	
		# give this object a reference to the master object
		self.PARENT = fobj_master

	def _view_tickets(self,fstr_network_name,fstr_account_name,fstr_ticket_name=None,fpage=1):
	
		def get_formatted_amount(network,account,raw_amount):

			return "{:28,.2f}".format(round(Decimal(raw_amount) / Decimal(network.skintillionths), account.decimal_places))
			# make sure has correct amount of decimal places
			
		def has_this_account(user_obj,network_id,account_name):

			# verify the user object has the network/account and that the label matches
			for i in range(len(user_obj.reserve_network_ids)):
				if user_obj.reserve_network_ids[i] == network_id:
					if user_obj.reserve_labels[i] == account_name:
						return user_obj.reserve_account_ids[i]
			for i in range(len(user_obj.client_network_ids)):
				if user_obj.client_network_ids[i] == network_id:
					if user_obj.client_labels[i] == account_name:
						return user_obj.client_account_ids[i]
			for i in range(len(user_obj.joint_network_ids)):
				if user_obj.joint_network_ids[i] == network_id:
					if user_obj.joint_labels[i] == account_name:
						return user_obj.joint_account_ids[i]
			for i in range(len(user_obj.clone_network_ids)):
				if user_obj.clone_network_ids[i] == network_id:
					if user_obj.clone_labels[i] == account_name:
						return user_obj.clone_account_ids[i]
			return False	

		def _get_default(fstr_network,fstr_user):

			network_id = fstr_network.network_id
			source_user = fstr_user
			for i in range(len(source_user.reserve_network_ids)):
				if source_user.reserve_network_ids[i] == network_id:
					if source_user.reserve_default[i] == True:
						return source_user.reserve_account_ids[i], source_user.reserve_labels[i]
			for i in range(len(source_user.client_network_ids)):
				if source_user.client_network_ids[i] == network_id: 
					if source_user.client_default[i] == True:
						return source_user.client_account_ids[i], source_user.client_labels[i]
			for i in range(len(source_user.joint_network_ids)):
				if source_user.joint_network_ids[i] == network_id: 
					if source_user.joint_default[i] == True:
						return source_user.joint_account_ids[i], source_user.joint_labels[i]
			for i in range(len(source_user.clone_network_ids)):
				if source_user.clone_network_ids[i] == network_id: 
					if source_user.clone_default[i] == True:
						return source_user.clone_account_ids[i], source_user.clone_labels[i]
			return None, None

		def get_or_insert_ticket_index(fint_network_id,fint_account_id,fstr_user_id):
		
			ticket_index_key = ndb.Key("ds_mr_metric_ticket_index", "%s%s" % (fint_network_id, fint_account_id))
			ticket_index_entity = ticket_index_key.get()
			if ticket_index_entity is None:
				ticket_index_entity = ds_mr_metric_ticket_index()
				ticket_index_entity.key = ticket_index_key
				ticket_index_entity.account_id = fint_account_id
				ticket_index_entity.user_id = fstr_user_id
				ticket_index_entity.network_id = fint_network_id
				ticket_index_entity.ticket_data = {}
			if not "ticket_count" in source_ticket_index.ticket_data:
				# initialize ticket_data
				ticket_index_entity.ticket_data["ticket_count"] = 0
				ticket_index_entity.ticket_data["ticket_labels"] = []
				ticket_index_entity.ticket_data["ticket_amounts"] = []
				ticket_index_entity.ticket_data["ticket_memos"] = []
				ticket_index_entity.ticket_data["ticket_tag_network_ids"] = []
				ticket_index_entity.ticket_data["ticket_tag_account_ids"] = []
				ticket_index_entity.ticket_data["ticket_tag_user_ids"] = []

				ticket_index_entity.ticket_data["tag_count"] = 0
				ticket_index_entity.ticket_data["tag_labels"] = []
				ticket_index_entity.ticket_data["tag_amounts"] = []
				ticket_index_entity.ticket_data["tag_memos"] = []
				ticket_index_entity.ticket_data["tag_network_ids"] = []
				ticket_index_entity.ticket_data["tag_account_ids"] = []
				ticket_index_entity.ticket_data["tag_user_ids"] = []			
			return ticket_index_entity

		def get_label_for_account(user_obj,network_id,account_id):		
			for i in range(len(user_obj.reserve_network_ids)):
				if user_obj.reserve_network_ids[i] == network_id:
					if user_obj.reserve_account_ids[i] == account_id:
						return user_obj.reserve_labels[i]
			for i in range(len(user_obj.client_network_ids)):
				if user_obj.client_network_ids[i] == network_id:
					if user_obj.client_account_ids[i] == account_id:
						return user_obj.client_labels[i]
			for i in range(len(user_obj.joint_network_ids)):
				if user_obj.joint_network_ids[i] == network_id:
					if user_obj.joint_account_ids[i] == account_id:
						return user_obj.joint_labels[i]
			for i in range(len(user_obj.clone_network_ids)):
				if user_obj.clone_network_ids[i] == network_id:
					if user_obj.clone_account_ids[i] == account_id:
						return user_obj.clone_labels[i]
			return None
			
		# get network first
		network = self._get_network(fstr_network_name=fstr_network_name)
		# get the name to get user_id
		name_key = ndb.Key("ds_mr_unique_dummy_entity", fstr_account_name)
		name_entity = name_key.get()
		if name_entity is None:
			self.PARENT.RETURN_CODE = "STUB" # error Invalid account name
			return False
		# need to verify that user has this named account
		owner_user_key = ndb.Key("ds_mr_user",name_entity.user_id)
		owner_user = owner_user_key.get()
		if owner_user is None:
			self.PARENT.RETURN_CODE = "STUB" # error Couldn't load ticket owner user object
			return False	
		result = has_this_account(owner_user,fstr_account_name)
		if not result:
			self.PARENT.RETURN_CODE = "STUB" # error Ticket owner name does not match user for this network
			return False
		# ok, we have valid account id, load metric account
		owner_account_id = result
		owner_metric_key = ndb.Key("ds_mr_metric_account", "%s%s" % (str(network.network_id).zfill(8),str(owner_account_id).zfill(12)))
		owner_metric_entity = owner_metric_key.get()
		if owner_metric_entity is None:
			self.PARENT.RETURN_CODE = "STUB"
			return False # error Could not load metric account
		# Get the ticket data entity
		owner_ticket_entity = get_or_insert_ticket_index(network.network_id,owner_account_id,owner_user.user_id)
		# Tickets are account type independent.  All accounts can pay/receive
		# so all can use tickets the same.
		ft = {}
		# Is the logged in viewer the owner?
		if name_entity.user_id == self.PARENT.user.entity.user_id:
			ft["is_owner"] == True
		else:
			ft["is_owner"] == False
		# Are we viewing all tickets or just one?
		if fstr_ticket_name is None:
			# Viewing all tickets
			ft["network_name"] = fstr_network_name
			ft["account_name"] = fstr_account_name
			# Do we need to get tickets owner is tagged with or
			# tickets visitor is tagged with from this owner?
			if ft["is_owner"]:
				# Get tickets owner is tagged with from others.
				ft["has_owner_tags"] = False
				ft["owner_tags"] = []
				ft["owner_tag_count"] = 0
				user_keys = []
				for i in range (len(owner_ticket_entity.ticket_data["tag_labels"])):
					ft["has_owner_tags"] = True
					ft["owner_tag_count"] += 1
					new_ticket = {}						
					new_ticket["ticket_label"] = owner_ticket_entity.ticket_data["tag_labels"][i]
					a = network
					b = owner_metric_entity
					c = owner_ticket_entity.ticket_data["tag_amounts"][i]
					new_ticket["ticket_amount"] = get_formatted_amount(a,b,c)
					new_ticket["ticket_memo"] = owner_ticket_entity.ticket_data["tag_memos"][i]
					new_ticket["ticket_tag_network_id"] = owner_ticket_entity.ticket_data["tag_network_ids"][i]
					new_ticket["ticket_tag_account_id"] = owner_ticket_entity.ticket_data["tag_account_ids"][i]
					new_ticket["ticket_tag_user_id"] = owner_ticket_entity.ticket_data["tag_user_ids"][i]						
					# We need to get username/alias of this ticket owner for
					# display, but for now just group the keys, so we can do
					# them all at once
					user_key = ndb.Key("ds_mr_user",new_ticket["ticket_tag_user_id"])
					user_keys.append(user_key)
					# leave blank till after we query users
					new_ticket["ticket_tag_user_account_name"] = ""						
					ft["owner_tags"].append(new_ticket)
				if ft["owner_has_tags"]:
					# need to get account labels for display and linking
					user_objects = ndb.get_multi(user_keys)
					for i in range(len(user_objects)):
						a = user_objects[i]
						b = network.network_id
						c = ft["owner_tags"][i]["ticket_tag_account_id"]
						ft["owner_tags"][i]["ticket_tag_user_account_name"] = get_label_for_account(a,b,c)
				# We've got owners "tagged by others" tickets taken care of, 
				# now lets load the actual lists of tickets for this owner.
				
				tickets_per_page = 10
				
				ft["all_tickets_count"] = owner_ticket_entity.ticket_data["ticket_count"]
				ft["has_tickets"] = False
				
				if ft["all_tickets_count"] > 0:
					ft["has_tickets"] = True
					last_ticket_idx = (int(fpage) * tickets_per_page) - 1
					first_ticket_idx = last_ticket_idx - tickets_per_page - 1
					if first_ticket_idx > (ft["all_tickets_count"] - 1):
						self.PARENT.RETURN_CODE = "STUB"
						return False # error Invalid page passed
					if last_ticket_idx > (ft["all_tickets_count"] - 1):
						last_ticket_idx = ft["all_tickets_count"] - 1
					if last_ticket_idx == ft["all_tickets_count"] - 1:
						ft["next_page"] = "0"
					else:
						ft["next_page"] = str(int(fpage) + 1)
					if first_ticket_idx > 0:
						ft["prev_page"] = str(int(fpage) - 1)
					else:
						ft["prev_page"] = "0"
						
					# let's loop through our tickets for this page
					current_idx = first_ticket_idx
					user_keys_bool = []
					user_keys = []
					while True:
						new_ticket = {}
						new_ticket["ticket_label"] = owner_ticket_entity.ticket_data["ticket_labels"][current_idx]
						a = network
						b = owner_metric_entity
						c = owner_ticket_entity.ticket_data["ticket_amounts"][current_idx]
						new_ticket["ticket_amount"] = get_formatted_amount(a,b,c)
						new_ticket["ticket_memo"] = owner_ticket_entity.ticket_data["ticket_memos"][current_idx]
						new_ticket["ticket_tag_network_id"] = owner_ticket_entity.ticket_data["ticket_tag_network_ids"][current_idx]
						new_ticket["ticket_tag_account_id"] = owner_ticket_entity.ticket_data["ticket_tag_account_ids"][current_idx]
						new_ticket["ticket_tag_user_id"] = owner_ticket_entity.ticket_data["ticket_tag_user_ids"][current_idx]
						if new_ticket["ticket_tag_user_id"] is None:
							# ticket is not tagged
							new_ticket["ticket_is_tagged"] = False
							user_keys_bool.append(False)
						else:
							new_ticket["ticket_is_tagged"] = True
							
							# We need to get username/alias of this ticket tagged identity for
							# display, but for now just group the keys, so we can do
							# them all at once
							user_key = ndb.Key("ds_mr_user",new_ticket["ticket_tag_user_id"])
							user_keys_bool.append(True)
							user_keys.append(user_key)
							# leave blank till after we query users
							new_ticket["ticket_tag_user_account_name"] = ""	
							
						ft["all_tickets"].append(new_ticket)
						if current_idx == last_ticket_idx:
							break
						else:
							current_idx += 1
					# get all users, then repopulate user_keys_bool
					user_objects = ndb.get_multi(user_keys)
					user_counter = 0
					for i in range(len(user_keys_bool)):
						if user_keys_bool[i]:
							user_keys_bool[i] = user_objects[user_counter]
							a = user_keys_bool[i]
							b = network.network_id
							c = ft["all_tickets"][i]["ticket_tag_account_id"]
							ft["all_tickets"][i]["ticket_tag_user_account_name"] = get_label_for_account(a,b,c)
							user_counter += 1

			else:
				# Get tickets visitor is tagged with from owner.
				# Visitors don't get to see all the tickets, just the ones
				# they are tagged in.  A informational message should direct
				# them to search for a ticket name or click on one they
				# are tagged with.
				ft["network_name"] = fstr_network_name
				ft["account_name"] = fstr_account_name
				ft["has_visitor_tags"] = False
				ft["visitor_tags"] = []
				ft["visitor_tag_count"] = 0
				for i in range (len(owner_ticket_entity.ticket_data["ticket_labels"])):
					if owner_ticket_entity.ticket_data["ticket_tag_user_ids"][i] == self.PARENT.user.entity.user_id:
						ft["has_visitor_tags"] = True
						ft["visitor_tag_count"] += 1
						new_ticket = {}						
						new_ticket["ticket_label"] = owner_ticket_entity.ticket_data["ticket_labels"][i]
						a = network
						b = owner_metric_entity
						c = owner_ticket_entity.ticket_data["ticket_amounts"][i]
						new_ticket["ticket_amount"] = get_formatted_amount(a,b,c)
						new_ticket["ticket_memo"] = owner_ticket_entity.ticket_data["ticket_memos"][i]
						new_ticket["ticket_tag_network_id"] = owner_ticket_entity.ticket_data["ticket_tag_network_ids"][i]
						new_ticket["ticket_tag_account_id"] = owner_ticket_entity.ticket_data["ticket_tag_account_ids"][i]
						new_ticket["ticket_tag_user_id"] = owner_ticket_entity.ticket_data["ticket_tag_user_ids"][i]						
						# get the username/alias for visitor this ticket is referencing
						a = self.PARENT.user.entity
						b = network.network_id
						c = ft["ticket_tag_account_id"]
						new_ticket["ticket_tag_user_account_name"] = get_label_for_account(a,b,c)						
						ft["visitor_tags"].append(new_ticket)

		else:
			# Viewing one ticket
			if not fstr_ticket_name in owner_ticket_entity.ticket_data["ticket_labels"]:
				self.PARENT.RETURN_CODE = "STUB"
				return False # error Ticket label doesn't exist for owner account
			else:
				# get the index of this ticket
				idx = owner_ticket_entity.ticket_data["ticket_labels"].index(fstr_ticket_name)
				ft["network_name"] = fstr_network_name
				ft["account_name"] = fstr_account_name
				ft["ticket_count"] = 1
				ft["ticket_label"] = owner_ticket_entity.ticket_data["ticket_labels"][idx]
				a = network
				b = owner_metric_entity
				c = owner_ticket_entity.ticket_data["ticket_amounts"][idx]
				ft["ticket_amount"] = get_formatted_amount(a,b,c)
				ft["ticket_memo"] = owner_ticket_entity.ticket_data["ticket_memos"][idx]
				ft["ticket_tag_network_id"] = owner_ticket_entity.ticket_data["ticket_tag_network_ids"][idx]
				ft["ticket_tag_account_id"] = owner_ticket_entity.ticket_data["ticket_tag_account_ids"][idx]
				ft["ticket_tag_user_id"] = owner_ticket_entity.ticket_data["ticket_tag_user_ids"][idx]
				if not ft["ticket_tag_user_id"] is None:				
					# need to get tagged users label
					tagged_user_key = ndb.Key("ds_mr_user",ft["ticket_tag_user_id"])
					tagged_user = tagged_user_key.get()
					if tagged_user is None:
						self.PARENT.RETURN_CODE = "STUB" # error Couldn't load tagged user object
						return False
					a = tagged_user
					b = network.network_id
					c = ft["ticket_tag_account_id"]
					ft["ticket_tag_user_account_name"] = get_label_for_account(a,b,c)
					if ft["ticket_tag_user_account_name"] is None:
						self.PARENT.RETURN_CODE = "STUB" # error Couldn't render tagged user account name
						return False
					ft["ticket_has_tag"] = True
				else:
					ft["ticket_has_tag"] = False				
				if ft["ticket_tag_user_id"] == self.PARENT.user.entity.user_id:
					ft["visitor_is_tagged"] = True
				else:
					ft["visitor_is_tagged"] = False
				# get the QR code url for the ticket
				host_name = "STUB"
				path_qs = "/tickets?vn=%s&va=%s&vt=%s" % (fstr_network_name,fstr_account_name,fstr_ticket_name)
				qr_url = host_name + path_qs
				ft["ticket_qr_code_url"] = self.PARENT.metric._get_qr_url(qr_url)
				
				
			
		return ft	
		
	def _view_ledger(self,fstr_network_name,fstr_account_name,fpage=1):
	
		def get_formatted_amount(network,account,raw_amount):

			return "{:28,.2f}".format(round(Decimal(raw_amount) / Decimal(network.skintillionths), account.decimal_places))
			# make sure has correct amount of decimal places
			

		def has_this_account(user_obj,network_id,account_name):

			# verify the user object has the network/account and that the label matches
			for i in range(len(user_obj.reserve_network_ids)):
				if user_obj.reserve_network_ids[i] == network_id:
					if user_obj.reserve_labels[i] == account_name:
						return user_obj.reserve_account_ids[i]
			for i in range(len(user_obj.client_network_ids)):
				if user_obj.client_network_ids[i] == network_id:
					if user_obj.client_labels[i] == account_name:
						return user_obj.client_account_ids[i]
			for i in range(len(user_obj.joint_network_ids)):
				if user_obj.joint_network_ids[i] == network_id:
					if user_obj.joint_labels[i] == account_name:
						return user_obj.joint_account_ids[i]
			for i in range(len(user_obj.clone_network_ids)):
				if user_obj.clone_network_ids[i] == network_id:
					if user_obj.clone_labels[i] == account_name:
						return user_obj.clone_account_ids[i]
			return False		
		
		name_key = ndb.Key("ds_mr_unique_dummy_entity", fstr_account_name)
		name_entity = name_key.get()
		if name_entity is None:
			self.PARENT.RETURN_CODE = "1285" # error Invalid account name
			return False
		if not name_entity.user_id == self.PARENT.user.entity.user_id:
			self.PARENT.RETURN_CODE = "1286" # error Account user doesn't match logged in user.
			return False
		
		network = self._get_network(fstr_network_name=fstr_network_name)

		source_user_key = ndb.Key("ds_mr_user",self.PARENT.user.entity.user_id)
		source_user = source_user_key.get()
		
		account_id = has_this_account(source_user,network.network_id,fstr_account_name)
		if not account_id:
			self.PARENT.RETURN_CODE = "1288" # error Account name does not belong to user.
			return False

		# transactionally get the source and target metric accounts
		key_part1 = str(network.network_id).zfill(8)
		key_part2 = str(account_id).zfill(12)
		metric_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part2))
		metric_entity = metric_key.get()
		if metric_entity is None:
			self.PARENT.RETURN_CODE = "1289"
			return False # error Could not load metric account

		transactions_per_page = 10
		
		start_index = ((int(fpage) - 1) * transactions_per_page * -1) + metric_entity.tx_index
		if start_index < 1:
			self.PARENT.RETURN_CODE = "1290"
			return False # error Ledger page out of range
		finish_index = start_index + 1 - transactions_per_page
		if finish_index < 1: finish_index = 1
		# construct list of transaction ledger keys
		current_index = start_index
		list_of_keys = []
		while True:			
			tx_log_key = ndb.Key("ds_mr_tx_log", "MRTX2%s%s%s" % (key_part1, key_part2,str(current_index).zfill(12)))
			list_of_keys.append(tx_log_key)
			if current_index == finish_index:
				break
			else:
				current_index -= 1
		
		list_of_raw_transactions = ndb.get_multi(list_of_keys)
		
		if finish_index == 1:
			next_page = 0
		else:
			next_page = int(fpage) + 1
			
		if start_index == metric_entity.tx_index:
			prev_page = 0
		else:
			prev_page = int(fpage) - 1
	
		if metric_entity.account_type == "RESERVE":
		
			# formatted transactions for RESERVE accounts
			ft = {}
			ft["network_name"] = fstr_network_name
			ft["network_id"] = network.network_id
			ft["username_alias"] = fstr_account_name
			ft["account_id"] = metric_entity.account_id
			ft["total_transactions"] = metric_entity.tx_index
			ft["status"] = metric_entity.account_status
			ft["type"] = metric_entity.account_type
			a = network
			b = metric_entity
			ft["network_balance"] = get_formatted_amount(a,b,metric_entity.current_network_balance)
			ft["reserve_balance"] = get_formatted_amount(a,b,metric_entity.current_reserve_balance)
			ft["date_created"] = metric_entity.date_created
			m = str(ft["date_created"].month)
			d = str(ft["date_created"].day)
			y = str(ft["date_created"].year)
			ft["d_date_created"] = "%s/%s/%s" % (m,d,y)
			ft["prev_page"] = str(prev_page)
			ft["next_page"] = str(next_page)
			ft["start_index"] = start_index
			ft["finish_index"] = finish_index
			ft["transactions"] = []
			
			is_even = False
			for tx in list_of_raw_transactions:			
				ftx = {}
				ftx["tx_index"] = tx.tx_index
				if is_even:
					is_even = False
					ftx["even_odd"] = "even"
				else:
					is_even = True
					ftx["even_odd"] = "odd"
				ftx["tx_type"] = tx.tx_type
				ftx["amount"] = get_formatted_amount(a,b,tx.amount)
				ftx["description"] = tx.description
				ftx["memo"] = tx.memo
				ftx["date_created"] = tx.date_created
				ftx["current_network_balance"] = get_formatted_amount(a,b,tx.current_network_balance)
				ftx["current_reserve_balance"] = get_formatted_amount(a,b,tx.current_reserve_balance)
				# format display amounts and balances for this transaction
				ftx["d_id"] = ftx["tx_index"]
				m = str(ftx["date_created"].month)
				d = str(ftx["date_created"].day)
				y = str(ftx["date_created"].year)
				ftx["d_date"] = "%s/%s/%s" % (m,d,y)
				ftx["d_memo"] = ftx["memo"]
				ftx["d_r_bal"] = ftx["current_reserve_balance"]
				ftx["d_n_bal"] = ftx["current_network_balance"]
				"""
				
				# Transaction types and their effect on ledger.
				
				(NA) "JOINT ACCOUNT CREATED ON NETWORK"
				(NA) "CLIENT ACCOUNT CREATED ON NETWORK"
				(NA) "CLONE ACCOUNT CREATED ON NETWORK"
				(NA) "JOINED NETWORK"

				-res "RESERVE OVERRIDE SUBTRACT"
				+res "RESERVE OVERRIDE ADD"
				-r&n "RESERVE SUBTRACT"
				+r&n "RESERVE ADD"

				-net "PAYMENT MADE"
				+net "PAYMENT RECEIVED"

				+res "USER INCOMING RESERVE TRANSFER AUTHORIZED"
				-res "USER OUTGOING RESERVE TRANSFER AUTHORIZED"
				+res "SUGGESTED INCOMING RESERVE TRANSFER AUTHORIZED"
				-res "SUGGESTED OUTGOING RESERVE TRANSFER AUTHORIZED"

				-net "JOINT RETRIEVE OUT"
				+net "JOINT RETRIEVE IN"

				-net "TICKET PAYMENT MADE"
				+net "TICKET PAYMENT RECEIVED"
				
				# so we'll group like formatting together
				"""
				checker = []
				checker.append("JOINT ACCOUNT CREATED ON NETWORK")
				checker.append("CLIENT ACCOUNT CREATED ON NETWORK")
				checker.append("CLONE ACCOUNT CREATED ON NETWORK")
				checker.append("JOINED NETWORK")
				checker.append("RESERVE OVERRIDE SUBTRACT")
				checker.append("RESERVE OVERRIDE ADD")
				checker.append("RESERVE SUBTRACT")
				checker.append("RESERVE ADD")
				checker.append("PAYMENT MADE")
				checker.append("PAYMENT RECEIVED")
				checker.append("USER INCOMING RESERVE TRANSFER AUTHORIZED")
				checker.append("USER OUTGOING RESERVE TRANSFER AUTHORIZED")
				checker.append("SUGGESTED INCOMING RESERVE TRANSFER AUTHORIZED")
				checker.append("SUGGESTED OUTGOING RESERVE TRANSFER AUTHORIZED")
				checker.append("JOINT RETRIEVE OUT")
				checker.append("JOINT RETRIEVE IN")
				checker.append("TICKET PAYMENT MADE")
				checker.append("TICKET PAYMENT RECEIVED")
				
				if not ftx["tx_type"] in checker:
					self.PARENT.RETURN_CODE = "1284"
					return False # error Bad transaction type.					
				
				# (NA)
				if (ftx["tx_type"] == "JOINT ACCOUNT CREATED ON NETWORK" or 
					ftx["tx_type"] == "CLIENT ACCOUNT CREATED ON NETWORK" or 
					ftx["tx_type"] == "CLONE ACCOUNT CREATED ON NETWORK" or
					ftx["tx_type"] == "JOINED NETWORK"):
					# just zero amounts and balances, creation transaction				
					ftx["d_res"] = " "
					ftx["d_net"] = " "
					ft["transactions"].append(ftx)
				
				# -res
				if (ftx["tx_type"] == "RESERVE OVERRIDE SUBTRACT" or 
					ftx["tx_type"] == "USER OUTGOING RESERVE TRANSFER AUTHORIZED" or 
					ftx["tx_type"] == "SUGGESTED OUTGOING RESERVE TRANSFER AUTHORIZED"):
					# 				
					ftx["d_res"] = "-%s" % ftx["amount"]
					ftx["d_net"] = " "
					ft["transactions"].append(ftx)

				# +res
				if (ftx["tx_type"] == "RESERVE OVERRIDE ADD" or 
					ftx["tx_type"] == "USER INCOMING RESERVE TRANSFER AUTHORIZED" or 
					ftx["tx_type"] == "SUGGESTED INCOMING RESERVE TRANSFER AUTHORIZED"):
					# 				
					ftx["d_res"] = "+%s" % ftx["amount"]
					ftx["d_net"] = " "
					ft["transactions"].append(ftx)

				# -net
				if (ftx["tx_type"] == "PAYMENT MADE" or 
					ftx["tx_type"] == "JOINT RETRIEVE OUT" or 
					ftx["tx_type"] == "TICKET PAYMENT MADE"):
					# 				
					ftx["d_res"] = " "
					ftx["d_net"] = "-%s" % ftx["amount"]
					ft["transactions"].append(ftx)

				# +net
				if (ftx["tx_type"] == "PAYMENT RECEIVED" or 
					ftx["tx_type"] == "JOINT RETRIEVE IN" or 
					ftx["tx_type"] == "TICKET PAYMENT RECEIVED"):
					# 				
					ftx["d_res"] = " "
					ftx["d_net"] = "+%s" % ftx["amount"]
					ft["transactions"].append(ftx)

				# -r&n
				if (ftx["tx_type"] == "RESERVE SUBTRACT"):
					# 				
					ftx["d_res"] = "-%s" % ftx["amount"]
					ftx["d_net"] = "-%s" % ftx["amount"]
					ft["transactions"].append(ftx)

				# +r&n
				if (ftx["tx_type"] == "RESERVE ADD"):
					# 				
					ftx["d_res"] = "+%s" % ftx["amount"]
					ftx["d_net"] = "+%s" % ftx["amount"]
					ft["transactions"].append(ftx)
					
			return ft		

		if metric_entity.account_type == "CLIENT":

			# formatted transactions for CLIENT accounts
			ft = {}
			ft["network_name"] = fstr_network_name
			ft["network_id"] = network.network_id
			ft["username_alias"] = fstr_account_name
			ft["account_id"] = metric_entity.account_id
			ft["total_transactions"] = metric_entity.tx_index
			ft["status"] = metric_entity.account_status
			ft["type"] = metric_entity.account_type
			a = network
			b = metric_entity
			ft["network_balance"] = get_formatted_amount(a,b,metric_entity.current_network_balance)
			ft["date_created"] = metric_entity.date_created
			m = str(ft["date_created"].month)
			d = str(ft["date_created"].day)
			y = str(ft["date_created"].year)
			ft["d_date_created"] = "%s/%s/%s" % (m,d,y)
			ft["prev_page"] = str(prev_page)
			ft["next_page"] = str(next_page)
			ft["start_index"] = start_index
			ft["finish_index"] = finish_index
			ft["transactions"] = []
			
			is_even = False
			for tx in list_of_raw_transactions:			
				ftx = {}
				ftx["tx_index"] = tx.tx_index
				if is_even:
					is_even = False
					ftx["even_odd"] = "even"
				else:
					is_even = True
					ftx["even_odd"] = "odd"
				ftx["tx_type"] = tx.tx_type
				ftx["amount"] = get_formatted_amount(a,b,tx.amount)
				ftx["description"] = tx.description
				ftx["memo"] = tx.memo
				ftx["date_created"] = tx.date_created
				ftx["current_network_balance"] = get_formatted_amount(a,b,tx.current_network_balance)
				# format display amounts and balances for this transaction
				ftx["d_id"] = ftx["tx_index"]
				m = str(ftx["date_created"].month)
				d = str(ftx["date_created"].day)
				y = str(ftx["date_created"].year)
				ftx["d_date"] = "%s/%s/%s" % (m,d,y)
				ftx["d_memo"] = ftx["memo"]
				ftx["d_n_bal"] = ftx["current_network_balance"]
				"""
				
				# Transaction types and their effect on ledger.
				
				(NA) "CLIENT ACCOUNT CREATED ON NETWORK"

				-net "PAYMENT MADE"
				+net "PAYMENT RECEIVED"

				-net "TICKET PAYMENT MADE"
				+net "TICKET PAYMENT RECEIVED"
				
				# so we'll group like formatting together
				"""
				checker = []
				checker.append("CLIENT ACCOUNT CREATED ON NETWORK")
				checker.append("PAYMENT MADE")
				checker.append("PAYMENT RECEIVED")
				checker.append("TICKET PAYMENT MADE")
				checker.append("TICKET PAYMENT RECEIVED")
				
				if not ftx["tx_type"] in checker:
					self.PARENT.RETURN_CODE = "STUB"
					return False # error Bad transaction type.					
				
				# (NA)
				if (ftx["tx_type"] == "CLIENT ACCOUNT CREATED ON NETWORK"):
					# just zero amounts and balances, creation transaction				
					ftx["d_net"] = " "
					ft["transactions"].append(ftx)

				# -net
				if (ftx["tx_type"] == "PAYMENT MADE" or 
					ftx["tx_type"] == "TICKET PAYMENT MADE"):
					# 				
					ftx["d_net"] = "-%s" % ftx["amount"]
					ft["transactions"].append(ftx)

				# +net
				if (ftx["tx_type"] == "PAYMENT RECEIVED" or 
					ftx["tx_type"] == "TICKET PAYMENT RECEIVED"):
					# 				
					ftx["d_net"] = "+%s" % ftx["amount"]
					ft["transactions"].append(ftx)
					
			return ft
			
		if metric_entity.account_type == "JOINT":
		
			# formatted transactions for JOINT accounts
			ft = {}
			ft["network_name"] = fstr_network_name
			ft["network_id"] = network.network_id
			ft["username_alias"] = fstr_account_name
			ft["account_id"] = metric_entity.account_id
			ft["total_transactions"] = metric_entity.tx_index
			ft["status"] = metric_entity.account_status
			ft["type"] = metric_entity.account_type
			a = network
			b = metric_entity
			ft["network_balance"] = get_formatted_amount(a,b,metric_entity.current_network_balance)
			ft["date_created"] = metric_entity.date_created
			m = str(ft["date_created"].month)
			d = str(ft["date_created"].day)
			y = str(ft["date_created"].year)
			ft["d_date_created"] = "%s/%s/%s" % (m,d,y)
			ft["prev_page"] = str(prev_page)
			ft["next_page"] = str(next_page)
			ft["start_index"] = start_index
			ft["finish_index"] = finish_index
			ft["transactions"] = []
			
			is_even = False
			for tx in list_of_raw_transactions:			
				ftx = {}
				ftx["tx_index"] = tx.tx_index
				if is_even:
					is_even = False
					ftx["even_odd"] = "even"
				else:
					is_even = True
					ftx["even_odd"] = "odd"
				ftx["tx_type"] = tx.tx_type
				ftx["amount"] = get_formatted_amount(a,b,tx.amount)
				ftx["description"] = tx.description
				ftx["memo"] = tx.memo
				ftx["date_created"] = tx.date_created
				ftx["current_network_balance"] = get_formatted_amount(a,b,tx.current_network_balance)
				# format display amounts and balances for this transaction
				ftx["d_id"] = ftx["tx_index"]
				m = str(ftx["date_created"].month)
				d = str(ftx["date_created"].day)
				y = str(ftx["date_created"].year)
				ftx["d_date"] = "%s/%s/%s" % (m,d,y)
				ftx["d_memo"] = ftx["memo"]
				ftx["d_n_bal"] = ftx["current_network_balance"]
				"""
				
				# Transaction types and their effect on ledger.
				
				(NA) "JOINT ACCOUNT CREATED ON NETWORK"
				-net "JOINT RETRIEVE OUT"
				
				-net "PAYMENT MADE"
				+net "PAYMENT RECEIVED"

				-net "TICKET PAYMENT MADE"
				+net "TICKET PAYMENT RECEIVED"
				
				# so we'll group like formatting together
				"""
				checker = []
				checker.append("JOINT ACCOUNT CREATED ON NETWORK")
				checker.append("JOINT RETRIEVE OUT")
				checker.append("PAYMENT MADE")
				checker.append("PAYMENT RECEIVED")
				checker.append("TICKET PAYMENT MADE")
				checker.append("TICKET PAYMENT RECEIVED")
				
				if not ftx["tx_type"] in checker:
					self.PARENT.RETURN_CODE = "STUB"
					return False # error Bad transaction type.					
				
				# (NA)
				if (ftx["tx_type"] == "JOINT ACCOUNT CREATED ON NETWORK"):
					# just zero amounts and balances, creation transaction				
					ftx["d_net"] = " "
					ft["transactions"].append(ftx)

				# -net
				if (ftx["tx_type"] == "PAYMENT MADE" or
					ftx["tx_type"] == "JOINT RETRIEVE OUT" or
					ftx["tx_type"] == "TICKET PAYMENT MADE"):
					# 				
					ftx["d_net"] = "-%s" % ftx["amount"]
					ft["transactions"].append(ftx)

				# +net
				if (ftx["tx_type"] == "PAYMENT RECEIVED" or 
					ftx["tx_type"] == "TICKET PAYMENT RECEIVED"):
					# 				
					ftx["d_net"] = "+%s" % ftx["amount"]
					ft["transactions"].append(ftx)
					
			return ft
			
		if metric_entity.account_type == "CLONE":
		
			# formatted transactions for RESERVE accounts
			ft = {}
			ft["network_name"] = fstr_network_name
			ft["network_id"] = network.network_id
			ft["username_alias"] = fstr_account_name
			ft["account_id"] = metric_entity.account_id
			ft["total_transactions"] = metric_entity.tx_index
			ft["status"] = metric_entity.account_status
			ft["type"] = metric_entity.account_type
			a = network
			b = metric_entity
			ft["network_balance"] = get_formatted_amount(a,b,metric_entity.current_network_balance)
			ft["date_created"] = metric_entity.date_created
			m = str(ft["date_created"].month)
			d = str(ft["date_created"].day)
			y = str(ft["date_created"].year)
			ft["d_date_created"] = "%s/%s/%s" % (m,d,y)
			ft["prev_page"] = str(prev_page)
			ft["next_page"] = str(next_page)
			ft["start_index"] = start_index
			ft["finish_index"] = finish_index
			ft["transactions"] = []
			
			is_even = False
			for tx in list_of_raw_transactions:			
				ftx = {}
				ftx["tx_index"] = tx.tx_index
				if is_even:
					is_even = False
					ftx["even_odd"] = "even"
				else:
					is_even = True
					ftx["even_odd"] = "odd"
				ftx["tx_type"] = tx.tx_type
				ftx["amount"] = get_formatted_amount(a,b,tx.amount)
				ftx["description"] = tx.description
				ftx["memo"] = tx.memo
				ftx["date_created"] = tx.date_created
				ftx["current_network_balance"] = get_formatted_amount(a,b,tx.current_network_balance)
				# format display amounts and balances for this transaction
				ftx["d_id"] = ftx["tx_index"]
				m = str(ftx["date_created"].month)
				d = str(ftx["date_created"].day)
				y = str(ftx["date_created"].year)
				ftx["d_date"] = "%s/%s/%s" % (m,d,y)
				ftx["d_memo"] = ftx["memo"]
				ftx["d_n_bal"] = ftx["current_network_balance"]
				"""
				
				# Transaction types and their effect on ledger.
				
				(NA) "CLONE ACCOUNT CREATED ON NETWORK"

				-net "PAYMENT MADE"
				+net "PAYMENT RECEIVED"

				-net "TICKET PAYMENT MADE"
				+net "TICKET PAYMENT RECEIVED"
				
				# so we'll group like formatting together
				"""
				checker = []
				checker.append("CLONE ACCOUNT CREATED ON NETWORK")
				checker.append("PAYMENT MADE")
				checker.append("PAYMENT RECEIVED")
				checker.append("TICKET PAYMENT MADE")
				checker.append("TICKET PAYMENT RECEIVED")
				
				if not ftx["tx_type"] in checker:
					self.PARENT.RETURN_CODE = "1284"
					return False # error Bad transaction type.					
				
				# (NA)
				if (ftx["tx_type"] == "CLONE ACCOUNT CREATED ON NETWORK"):
					# just zero amounts and balances, creation transaction				
					ftx["d_net"] = " "
					ft["transactions"].append(ftx)

				# -net
				if (ftx["tx_type"] == "PAYMENT MADE" or 
					ftx["tx_type"] == "TICKET PAYMENT MADE"):
					# 				
					ftx["d_net"] = "-%s" % ftx["amount"]
					ft["transactions"].append(ftx)

				# +net
				if (ftx["tx_type"] == "PAYMENT RECEIVED" or 
					ftx["tx_type"] == "TICKET PAYMENT RECEIVED"):
					# 				
					ftx["d_net"] = "+%s" % ftx["amount"]
					ft["transactions"].append(ftx)
					
			return ft
			
		self.PARENT.RETURN_CODE = "1283"
		return False # error Account type not recognized
					
	def _view_network_account(self,fstr_network_name,fstr_account_name):
	
		def get_formatted_amount(network,account,raw_amount):
			
			return "{:28,.2f}".format(round(Decimal(raw_amount) / Decimal(network.skintillionths), account.decimal_places))

		def get_ticket_info(fdict,fmetric):
			ticket_index_key = ndb.Key("ds_mr_metric_ticket_index", "%s%s" % (fmetric.network_id, fmetric.account_id))
			ticket_index_entity = ticket_index_key.get()
			if ticket_index_entity is None:
				fdict["ticket_count"] = 0
				fdict["ticket_tag_count"] = 0
			else:
				fdict["ticket_count"] = ticket_index_entity.ticket_data["ticket_count"]
				fdict["ticket_tag_count"] = ticket_index_entity.ticket_data["tag_count"]
			
		def get_parent_for_account(network_id,account_id):
			
			# get parent metric account
			metric_key = ndb.Key("ds_mr_metric_account","%s%s" % (str(network_id).zfill(8),str(account_id).zfill(12)))
			metric_account = metric_key.get()
			if metric_account is None:
				self.PARENT.RETURN_CODE = "STUB" # error Couldn't load parent metric account.
				return False, None, None
			user_key = ndb.Key("ds_mr_user", "%s" % str(metric_account.user_id))
			user_entity = user_key.get()
			if user_entity is None:
				self.PARENT.RETURN_CODE = "STUB" # error Couldn't load parent user object.
				return False, None, None
			return True, user_entity, metric_account
							
		def get_label_for_account(user_obj,network_id,account_id,fstr_type):		
			if fstr_type == "RESERVE":
				for i in range(len(user_obj.reserve_network_ids)):
					if user_obj.reserve_network_ids[i] == network_id:
						if user_obj.reserve_account_ids[i] == account_id:
							return user_obj.reserve_labels[i]
			if fstr_type == "CLIENT":
				for i in range(len(user_obj.client_network_ids)):
					if user_obj.client_network_ids[i] == network_id:
						if user_obj.client_account_ids[i] == account_id:
							return user_obj.client_labels[i]
			if fstr_type == "JOINT":
				for i in range(len(user_obj.joint_network_ids)):
					if user_obj.joint_network_ids[i] == network_id:
						if user_obj.joint_account_ids[i] == account_id:
							return user_obj.joint_labels[i]
			if fstr_type == "CLONE":
				for i in range(len(user_obj.clone_network_ids)):
					if user_obj.clone_network_ids[i] == network_id:
						if user_obj.clone_account_ids[i] == account_id:
							return user_obj.clone_labels[i]
							
		# first get the default account on this network for the requesting user.
		result, network, s_account_id, s_username_alias, s_user_object = self._get_default(fstr_network_name,self.PARENT.user.entity.user_id)
		if not result: return result # pass up errors
		# account_id could be None if user doesn't have an account on this 
		# network, but our main concern here, is whether or not the account_name
		# requested is this user's default account on that network.
		network_id = network.network_id
		if s_username_alias == fstr_account_name:
			viewing_default_account = True
			# this is our default account on this network
			metric_account_key = ndb.Key("ds_mr_metric_account","%s%s" % (str(network_id).zfill(8),str(s_account_id).zfill(12)))
			t_account_id = s_account_id
			t_user_object = s_user_object
			viewing_my_account = True
		else:
			viewing_default_account = False
			# viewing others or non-default account
			#
			# We're going to need to query the fstr_account_name to get the 
			# user object and account_id.  We already got the network_id
			# non-transactionally from the above process now let's get the 
			# account_id.
			# pass to validation as target so don't get "source is user" security fail
			validation_result = self._name_validate_transactional(None,None,fstr_account_name,network_id)
			if not validation_result:
				# pass up error
				return False
			t_account_id = validation_result[2]
			t_user_object = validation_result[4]
			if t_user_object.user_id == self.PARENT.user.entity.user_id:
				viewing_my_account = True
			else:
				viewing_my_account = False
			metric_account_key = ndb.Key("ds_mr_metric_account","%s%s" % (str(network_id).zfill(8),str(t_account_id).zfill(12)))
		metric_account_entity = metric_account_key.get()
		if metric_account_entity is None:
			self.PARENT.RETURN_CODE = "1280" # error Invalid account id
			return False
		# We display an account differently based on the account type
		if metric_account_entity.account_type == "RESERVE":
		
			reserve_complete = {}
			get_ticket_info(reserve_complete,metric_account_entity)
			reserve_complete["is_my_account"] = viewing_my_account
			reserve_complete["is_my_default"] = viewing_default_account
			reserve_complete["network_name"] = fstr_network_name
			reserve_complete["network_id"] = network_id
			reserve_complete["username_alias"] = fstr_account_name
			reserve_complete["account_id"] = metric_account_entity.account_id
			reserve_complete["tx_index"] = metric_account_entity.tx_index
			reserve_complete["status"] = metric_account_entity.account_status
			reserve_complete["type"] = metric_account_entity.account_type
			a = network
			b = metric_account_entity
			reserve_complete["network_balance"] = get_formatted_amount(a,b,metric_account_entity.current_network_balance)
			reserve_complete["reserve_balance"] = get_formatted_amount(a,b,metric_account_entity.current_reserve_balance)
			reserve_complete["date_created"] = metric_account_entity.date_created
			m = str(reserve_complete["date_created"].month)
			d = str(reserve_complete["date_created"].day)
			y = str(reserve_complete["date_created"].year)
			reserve_complete["d_date_created"] = "%s/%s/%s" % (m,d,y)
			reserve_complete["latitude"] = t_user_object.location_latitude
			reserve_complete["longitude"] = t_user_object.location_longitude
			reserve_complete["map_marker_count"] = 1
			reserve_complete["map_data"] = []
			# create marker data for target account
			marker = {}
			marker["link"] = ""
			marker["polyline"] = ""
			marker["username_alias"] = fstr_account_name
			marker["latitude"] = reserve_complete["latitude"]
			marker["longitude"] = reserve_complete["longitude"]
			reserve_complete["map_data"].append(marker)		
			# reserve accounts don't have parents
			reserve_complete["has_parent"] = False
			reserve_complete["has_connections"] = False
			reserve_complete["connections"] = []
			reserve_complete["has_incoming_connection_requests"] = False
			reserve_complete["incoming_connection_requests"] = []
			reserve_complete["has_outgoing_connection_requests"] = False
			reserve_complete["outgoing_connection_requests"] = []
			reserve_complete["has_child_client_accounts"] = False
			reserve_complete["child_client_accounts"] = []
			reserve_complete["has_child_joint_accounts"] = False
			reserve_complete["child_joint_accounts"] = []
			reserve_complete["has_child_client_offer"] = False
			reserve_complete["has_child_joint_offer"] = False
			
			# let's get the counts for our subsets then grab 
			# accounts and users all in one go
			reserve_complete["connection_count"] = len(metric_account_entity.current_connections)
			reserve_complete["incoming_connection_requests_count"] = len(metric_account_entity.incoming_connection_requests)
			reserve_complete["outgoing_connection_requests_count"] = len(metric_account_entity.outgoing_connection_requests)
			reserve_complete["child_client_account_count"] = 0
			reserve_complete["child_joint_account_count"] = 0
			
			all_account_id_list = []
			
			for i in range(len(metric_account_entity.current_connections)):
				all_account_id_list.append(metric_account_entity.current_connections[i])
			for i in range(len(metric_account_entity.incoming_connection_requests)):
				all_account_id_list.append(metric_account_entity.incoming_connection_requests[i])
			for i in range(len(metric_account_entity.outgoing_connection_requests)):
				all_account_id_list.append(metric_account_entity.outgoing_connection_requests[i])
			# For child and joint we need to match network and acount id
			# for this reserve account with what's in the user object.
			for i in range(len(t_user_object.child_client_network_ids)):
				if t_user_object.child_client_network_ids[i] == network_id:
					if t_user_object.child_client_parent_ids[i] == metric_account_entity.account_id:
						# match
						reserve_complete["child_client_account_count"] += 1
						all_account_id_list.append(metric_account_entity.child_client_account_ids[i])

			for i in range(len(t_user_object.child_joint_network_ids)):
				if t_user_object.child_joint_network_ids[i] == network_id:
					if t_user_object.child_joint_parent_ids[i] == metric_account_entity.account_id:
						#match
						reserve_complete["child_joint_account_count"] += 1
						all_account_id_list.append(metric_account_entity.child_joint_account_ids[i])
						
			# now make a list of keys from our account/network ids
			all_accounts_key_list = []
			for i in range(len(all_account_id_list)):
				a_key = ndb.Key("ds_mr_metric_account","%s%s" % (str(network_id).zfill(8),str(all_account_id_list[i]).zfill(12)))
				all_accounts_key_list.append(a_key)
			# get the list of associated accounts
			list_of_associated_accounts = ndb.get_multi(all_accounts_key_list)
			# now loop through the account list to get the list of user objects for those accounts
			all_users_key_list = []
			for i in range(len(list_of_associated_accounts)):
				a_key = ndb.Key("ds_mr_user","%s" % list_of_associated_accounts[i].user_id)
				all_users_key_list.append(a_key)
			
			# don't grab accounts for offers
			reserve_complete["child_client_offer_count"] = 0
			reserve_complete["child_joint_offer_count"] = 0
			if not t_user_object.child_client_offer_account_id == 0:
				reserve_complete["has_child_client_offer"] = True
				reserve_complete["child_client_offer_count"] += 1
				all_accounts_key_list.append(None)
				a_key = ndb.Key("ds_mr_user","%s" % t_user_object.child_client_offer_user_id)
				all_users_key_list.append(a_key)
			else:
				reserve_complete["has_child_client_offer"] = False
			if not t_user_object.child_joint_offer_account_id == 0:
				reserve_complete["has_child_joint_offer"] = True
				reserve_complete["child_joint_offer_count"] += 1
				all_accounts_key_list.append(None)
				a_key = ndb.Key("ds_mr_user","%s" % t_user_object.child_joint_offer_user_id)
				all_users_key_list.append(a_key)
			else:
				reserve_complete["has_child_joint_offer"] = False
				
			# get the list of associated users
			list_of_associated_users = ndb.get_multi(all_users_key_list)			
			if None in list_of_associated_accounts or None in list_of_associated_users:
				self.PARENT.RETURN_CODE = "1281" # error Associated account/user entities back.
				return False
				
			# let's process the associated accounts/users now
			# list of associated accounts and list of associated users
			# should be the same length and be indexed parallely.
			group_counter = 0
			last_connection_idx = reserve_complete["connection_count"]
			last_incoming_connection_request_idx = last_connection_idx + reserve_complete["incoming_connection_requests_count"]
			last_outgoing_connection_request_idx = last_incoming_connection_request_idx + reserve_complete["outgoing_connection_requests_count"] 
			last_child_client_account_idx = last_outgoing_connection_request_idx + reserve_complete["child_client_account_count"]  
			last_child_joint_account_idx = last_child_client_account_idx + reserve_complete["child_joint_account_count"]
			last_child_client_offer_idx = last_child_joint_account_idx + reserve_complete["child_client_offer_count"]
			last_child_joint_offer_idx = last_child_client_offer_idx + reserve_complete["child_joint_offer_count"]
			for i in range(len(list_of_associated_accounts)):
				
				next_entity = {}
				next_marker = {}
				
				# process connections
				if i < last_connection_idx:
					reserve_complete["has_connections"] = True
					a = list_of_associated_users[i]
					b = network_id
					c = list_of_associated_accounts[i].account_id
					d = list_of_associated_accounts[i].account_type
					next_entity["username_alias"] = get_label_for_account(a,b,c,d)
					a = network
					b = metric_account_entity
					c = list_of_associated_accounts[i].current_network_balance
					d = list_of_associated_accounts[i].current_reserve_balance
					next_entity["network_balance"] = get_formatted_amount(a,b,c)
					next_entity["reserve_balance"] = get_formatted_amount(a,b,d)
					next_entity["connection_count"] = len(list_of_associated_accounts[i].current_connections)
					next_entity["latitude"] = list_of_associated_users[i].location_latitude
					next_entity["longitude"] = list_of_associated_users[i].location_longitude
					# transfers outgoing are shown prefixed "out -"
					# transfers incoming are shown prefixed "in +"
					# if this associated account is present in primary account...
					this_id = list_of_associated_accounts[i].account_id
					next_entity["transfer_request"] = "None" # default
					next_entity["suggested_transfer_inactive"] = "None" # default
					next_entity["suggested_transfer_active"] = "None" # default
					if this_id in metric_account_entity.incoming_reserve_transfer_requests:
						c = metric_account_entity.incoming_reserve_transfer_requests[this_id]
						next_entity["transfer_request"] = "in + %s" % get_formatted_amount(a,b,c)
					if this_id in metric_account_entity.outgoing_reserve_transfer_requests:
						c = metric_account_entity.outgoing_reserve_transfer_requests[this_id]
						next_entity["transfer_request"] = "out - %s" % get_formatted_amount(a,b,c)
					if this_id in metric_account_entity.suggested_inactive_incoming_reserve_transfer_requests:
						c = metric_account_entity.suggested_inactive_incoming_reserve_transfer_requests[this_id]
						next_entity["suggested_transfer_inactive"] = "in + %s" % get_formatted_amount(a,b,c)
					if this_id in metric_account_entity.suggested_inactive_outgoing_reserve_transfer_requests:
						c = metric_account_entity.suggested_inactive_outgoing_reserve_transfer_requests[this_id]
						next_entity["suggested_transfer_inactive"] = "out - %s" % get_formatted_amount(a,b,c)
					if this_id in metric_account_entity.suggested_active_incoming_reserve_transfer_requests:
						c = metric_account_entity.suggested_active_incoming_reserve_transfer_requests[this_id]
						next_entity["suggested_transfer_active"] = "in + %s" % get_formatted_amount(a,b,c)
					if this_id in metric_account_entity.suggested_active_outgoing_reserve_transfer_requests:
						c = metric_account_entity.suggested_active_outgoing_reserve_transfer_requests[this_id]
						next_entity["suggested_transfer_active"] = "out - %s" % get_formatted_amount(a,b,c)
					reserve_complete["connections"].append(next_entity)
					next_marker["link"] = ""
					next_marker["polyline"] = ""
					next_marker["username_alias"] = next_entity["username_alias"]
					next_marker["latitude"] = next_entity["latitude"]
					next_marker["longitude"] = next_entity["longitude"]
					reserve_complete["map_data"].append(next_marker)
					continue

				# process incoming connection requests
				if i < last_incoming_connection_request_idx:
					reserve_complete["has_incoming_connection_requests"] = True
					a = list_of_associated_users[i]
					b = network_id
					c = list_of_associated_accounts[i].account_id
					d = list_of_associated_accounts[i].account_type
					next_entity["username_alias"] = get_label_for_account(a,b,c,d)
					a = network
					b = metric_account_entity
					c = list_of_associated_accounts[i].current_network_balance
					d = list_of_associated_accounts[i].current_reserve_balance
					next_entity["network_balance"] = get_formatted_amount(a,b,c)
					next_entity["reserve_balance"] = get_formatted_amount(a,b,d)
					next_entity["connection_count"] = len(list_of_associated_accounts[i].current_connections)
					next_entity["latitude"] = list_of_associated_users[i].location_latitude
					next_entity["longitude"] = list_of_associated_users[i].location_longitude
					reserve_complete["incoming_connection_requests"].append(next_entity)
					next_marker["link"] = ""
					next_marker["polyline"] = ""
					next_marker["username_alias"] = next_entity["username_alias"]
					next_marker["latitude"] = next_entity["latitude"]
					next_marker["longitude"] = next_entity["longitude"]
					reserve_complete["map_data"].append(next_marker)
					continue

				# process outgoing connection requests
				if i < last_outgoing_connection_request_idx:
					reserve_complete["has_outgoing_connection_requests"] = True
					a = list_of_associated_users[i]
					b = network_id
					c = list_of_associated_accounts[i].account_id
					d = list_of_associated_accounts[i].account_type
					next_entity["username_alias"] = get_label_for_account(a,b,c,d)
					a = network
					b = metric_account_entity
					c = list_of_associated_accounts[i].current_network_balance
					d = list_of_associated_accounts[i].current_reserve_balance
					next_entity["network_balance"] = get_formatted_amount(a,b,c)
					next_entity["reserve_balance"] = get_formatted_amount(a,b,d)
					next_entity["connection_count"] = len(list_of_associated_accounts[i].current_connections)
					next_entity["latitude"] = list_of_associated_users[i].location_latitude
					next_entity["longitude"] = list_of_associated_users[i].location_longitude
					reserve_complete["outgoing_connection_requests"].append(next_entity)
					next_marker["link"] = ""
					next_marker["polyline"] = ""
					next_marker["username_alias"] = next_entity["username_alias"]
					next_marker["latitude"] = next_entity["latitude"]
					next_marker["longitude"] = next_entity["longitude"]
					reserve_complete["map_data"].append(next_marker)
					continue

				# process child client accounts
				if i < last_child_client_account_idx:
					reserve_complete["has_child_client_accounts"] = True
					a = list_of_associated_users[i]
					b = network_id
					c = list_of_associated_accounts[i].account_id
					d = list_of_associated_accounts[i].account_type
					next_entity["username_alias"] = get_label_for_account(a,b,c,d)
					a = network
					b = metric_account_entity
					c = list_of_associated_accounts[i].current_network_balance
					d = list_of_associated_accounts[i].current_reserve_balance
					next_entity["network_balance"] = get_formatted_amount(a,b,c)
					next_entity["latitude"] = list_of_associated_users[i].location_latitude
					next_entity["longitude"] = list_of_associated_users[i].location_longitude
					reserve_complete["child_client_accounts"].append(next_entity)
					next_marker["link"] = ""
					next_marker["polyline"] = ""
					next_marker["username_alias"] = next_entity["username_alias"]
					next_marker["latitude"] = next_entity["latitude"]
					next_marker["longitude"] = next_entity["longitude"]
					reserve_complete["map_data"].append(next_marker)
					continue

				# process child joint accounts
				if i < last_child_joint_account_idx:
					reserve_complete["has_child_joint_accounts"] = True
					a = list_of_associated_users[i]
					b = network_id
					c = list_of_associated_accounts[i].account_id
					d = list_of_associated_accounts[i].account_type
					next_entity["username_alias"] = get_label_for_account(a,b,c,d)
					a = network
					b = metric_account_entity
					c = list_of_associated_accounts[i].current_network_balance
					d = list_of_associated_accounts[i].current_reserve_balance
					next_entity["network_balance"] = get_formatted_amount(a,b,c)
					next_entity["latitude"] = list_of_associated_users[i].location_latitude
					next_entity["longitude"] = list_of_associated_users[i].location_longitude
					reserve_complete["child_client_accounts"].append(next_entity)
					next_marker["link"] = ""
					next_marker["polyline"] = ""
					next_marker["username_alias"] = next_entity["username_alias"]
					next_marker["latitude"] = next_entity["latitude"]
					next_marker["longitude"] = next_entity["longitude"]
					reserve_complete["map_data"].append(next_marker)
					continue
					
				# process client account offer
				if i < last_child_client_offer_idx:

					reserve_complete["client_child_entity"] = {}
					reserve_complete["client_child_entity"]["username"] = list_of_associated_users[i].username


				# process joint account offer
				if i < last_child_joint_offer_idx:

					reserve_complete["joint_child_entity"] = {}
					reserve_complete["joint_child_entity"]["username"] = list_of_associated_users[i].username

					# check for child account offers

					"""
					{% if blok.has_child_client_offer %}
					<ul class="myclass" data-inset="true" data-role="listview" data-divider-theme="a">
						<li data-role="list-divider">Child Client Account Offer</li>
						<li><a href="/network?vn={{ blok.account.client_child_entity.network_name }}&va={{ blok.account.client_child_entity.username }}">
						<h3>{{ blok.account.client_child_entity.username }}</h3>
						<p><b>Username</b>: {{ blok.account.client_child_entity.username }}</p>
						</a></li>
					</ul>
					{% endif %}
					{% if blok.has_child_joint_offer %}
					<ul class="myclass" data-inset="true" data-role="listview" data-divider-theme="a">
						<li data-role="list-divider">Child Joint Account Offer</li>
						<li><a href="/network?vn={{ blok.account.joint_child_entity.network_name }}&va={{ blok.account.joint_child_entity.username }}">
						<h3>{{ blok.account.joint_child_entity.username }}</h3>
						<p><b>Username</b>: {{ blok.account.joint_child_entity.username }}</p>
						</a></li>
					</ul>
					{% endif %}

					child_client_offer_network_id = ndb.IntegerProperty(default=0,indexed=False)
					child_client_offer_account_id = ndb.IntegerProperty(default=0,indexed=False)
					child_client_offer_user_id = ndb.StringProperty(default="EMPTY",indexed=False)

					child_joint_offer_network_id = ndb.IntegerProperty(default=0,indexed=False)
					child_joint_offer_account_id = ndb.IntegerProperty(default=0,indexed=False)
					child_joint_offer_user_id = ndb.StringProperty(default="EMPTY",indexed=False)

					"""

				
					continue
				
				"""
				DATA LAYOUT FOR RESERVE COMPLETE
				
				reserve_complete["connections_count"]
				reserve_complete["connections"] = []
				reserve_complete["connections"][i] = {}
				reserve_complete["connections"][i]["username_alias"]
				reserve_complete["connections"][i]["network_balance"]
				reserve_complete["connections"][i]["reserve_balance"]
				reserve_complete["connections"][i]["connection_count"]
				reserve_complete["connections"][i]["latitude"]
				reserve_complete["connections"][i]["longitude"]
				reserve_complete["connections"][i]["transfer_request"]
				reserve_complete["connections"][i]["suggested_transfer_inactive"]
				reserve_complete["connections"][i]["suggested_transfer_active"]
				reserve_complete["incoming_connection_requests_count"]
				reserve_complete["incoming_connections_requests"] = []
				reserve_complete["incoming_connections_requests"][i] = {}
				reserve_complete["incoming_connections_requests"][i]["username_alias"]
				reserve_complete["incoming_connections_requests"][i]["network_balance"]
				reserve_complete["incoming_connections_requests"][i]["reserve_balance"]
				reserve_complete["incoming_connections_requests"][i]["connection_count"]
				reserve_complete["incoming_connections_requests"][i]["latitude"]
				reserve_complete["incoming_connections_requests"][i]["longitude"]
				reserve_complete["outgoing_connection_requests_count"]
				reserve_complete["outgoing_connections_requests"] = []
				reserve_complete["outgoing_connections_requests"][i] = {}
				reserve_complete["outgoing_connections_requests"][i]["username_alias"]
				reserve_complete["outgoing_connections_requests"][i]["network_balance"]
				reserve_complete["outgoing_connections_requests"][i]["reserve_balance"]
				reserve_complete["outgoing_connections_requests"][i]["connection_count"]
				reserve_complete["outgoing_connections_requests"][i]["latitude"]
				reserve_complete["outgoing_connections_requests"][i]["longitude"]
				reserve_complete["child_client_account_count"]
				reserve_complete["child_client_accounts"] = []
				reserve_complete["child_client_accounts"][i] = {}
				reserve_complete["child_client_accounts"][i]["username_alias"]
				reserve_complete["child_client_accounts"][i]["network_balance"]
				reserve_complete["child_client_accounts"][i]["latitude"]
				reserve_complete["child_client_accounts"][i]["longitude"]
				reserve_complete["child_joint_account_count"]
				reserve_complete["child_joint_accounts"] = []
				reserve_complete["child_joint_accounts"][i] = {}
				reserve_complete["child_joint_accounts"][i]["username_alias"]
				reserve_complete["child_joint_accounts"][i]["network_balance"]
				reserve_complete["child_joint_accounts"][i]["latitude"]
				reserve_complete["child_joint_accounts"][i]["longitude"]
				reserve_complete["map_marker_count"]
				reserve_complete["map_data"] = []
				reserve_complete["map_data"][i] = {}
				reserve_complete["map_data"][i]["link"]
				reserve_complete["map_data"][i]["polyline"]
				reserve_complete["map_data"][i]["username_alias"]
				reserve_complete["map_data"][i]["latitude"]
				reserve_complete["map_data"][i]["longitude"]		
				"""
				
			return reserve_complete
			
		if metric_account_entity.account_type == "CLIENT":
			
			client_complete = {}
			get_ticket_info(client_complete,metric_account_entity)
			client_complete["is_my_account"] = viewing_my_account
			client_complete["is_my_default"] = viewing_default_account
			client_complete["network_name"] = fstr_network_name
			client_complete["network_id"] = network_id
			client_complete["username_alias"] = fstr_account_name
			client_complete["account_id"] = metric_account_entity.account_id
			client_complete["tx_index"] = metric_account_entity.tx_index
			client_complete["status"] = metric_account_entity.account_status
			client_complete["type"] = metric_account_entity.account_type
			a = network
			b = metric_account_entity
			client_complete["network_balance"] = get_formatted_amount(a,b,metric_account_entity.current_network_balance)
			client_complete["date_created"] = metric_account_entity.date_created
			m = str(client_complete["date_created"].month)
			d = str(client_complete["date_created"].day)
			y = str(client_complete["date_created"].year)
			client_complete["d_date_created"] = "%s/%s/%s" % (m,d,y)
			client_complete["latitude"] = t_user_object.location_latitude
			client_complete["longitude"] = t_user_object.location_longitude
			client_complete["map_marker_count"] = 1
			client_complete["map_data"] = []
			# create marker data for target account
			marker = {}
			marker["link"] = ""
			marker["polyline"] = ""
			marker["username_alias"] = fstr_account_name
			marker["latitude"] = client_complete["latitude"]
			marker["longitude"] = client_complete["longitude"]
			client_complete["map_data"].append(marker)
			# get the client accounts parent information
			client_complete["has_parent"] = True
			result, parent_user, parent_metric = get_parent_for_account(network_id,metric_account_entity.account_parent)
			if not result:
				return False # error pass up error
			client_complete["parent_entity"] = {}
			a = parent_user
			b = network_id
			c = parent_metric.account_id
			d = parent_metric.account_type
			client_complete["parent_entity"]["username_alias"] = get_label_for_account(a,b,c,d)
			a = network
			b = parent_metric
			c = parent_metric.current_network_balance
			d = parent_metric.current_reserve_balance
			client_complete["parent_entity"]["network_balance"] = get_formatted_amount(a,b,c)
			client_complete["parent_entity"]["reserve_balance"] = get_formatted_amount(a,b,d)
			# get ticket tag count

			return client_complete

		if metric_account_entity.account_type == "JOINT":
				
			joint_complete = {}
			get_ticket_info(joint_complete,metric_account_entity)
			joint_complete["is_my_account"] = viewing_my_account
			joint_complete["is_my_default"] = viewing_default_account
			joint_complete["network_name"] = fstr_network_name
			joint_complete["network_id"] = network_id
			joint_complete["username_alias"] = fstr_account_name
			joint_complete["account_id"] = metric_account_entity.account_id
			joint_complete["tx_index"] = metric_account_entity.tx_index
			joint_complete["status"] = metric_account_entity.account_status
			joint_complete["type"] = metric_account_entity.account_type
			a = network
			b = metric_account_entity
			joint_complete["network_balance"] = get_formatted_amount(a,b,metric_account_entity.current_network_balance)
			joint_complete["date_created"] = metric_account_entity.date_created
			m = str(joint_complete["date_created"].month)
			d = str(joint_complete["date_created"].day)
			y = str(joint_complete["date_created"].year)
			joint_complete["d_date_created"] = "%s/%s/%s" % (m,d,y)
			joint_complete["latitude"] = t_user_object.location_latitude
			joint_complete["longitude"] = t_user_object.location_longitude
			joint_complete["map_marker_count"] = 1
			joint_complete["map_data"] = []
			# create marker data for target account
			marker = {}
			marker["link"] = ""
			marker["polyline"] = ""
			marker["username_alias"] = fstr_account_name
			marker["latitude"] = joint_complete["latitude"]
			marker["longitude"] = joint_complete["longitude"]
			joint_complete["map_data"].append(marker)		
			# get the joint accounts parent information
			joint_complete["has_parent"] = True
			result, parent_user, parent_metric = get_parent_for_account(network_id,metric_account_entity.account_parent)
			if not result:
				return False # error pass up error
			joint_complete["parent_entity"] = {}
			a = parent_user
			b = network_id
			c = parent_metric.account_id
			d = parent_metric.account_type
			joint_complete["parent_entity"]["username_alias"] = get_label_for_account(a,b,c,d)
			a = network
			b = parent_metric
			c = parent_metric.current_network_balance
			d = parent_metric.current_reserve_balance
			joint_complete["parent_entity"]["network_balance"] = get_formatted_amount(a,b,c)
			joint_complete["parent_entity"]["reserve_balance"] = get_formatted_amount(a,b,d)
			
			return joint_complete
			
		if metric_account_entity.account_type == "CLONE":
				
			clone_complete = {}
			get_ticket_info(clone_complete,metric_account_entity)
			clone_complete["is_my_account"] = viewing_my_account
			clone_complete["is_my_default"] = viewing_default_account
			clone_complete["network_name"] = fstr_network_name
			clone_complete["network_id"] = network_id
			clone_complete["username_alias"] = fstr_account_name
			clone_complete["account_id"] = metric_account_entity.account_id
			clone_complete["tx_index"] = metric_account_entity.tx_index
			clone_complete["status"] = metric_account_entity.account_status
			clone_complete["type"] = metric_account_entity.account_type
			a = network
			b = metric_account_entity
			clone_complete["network_balance"] = get_formatted_amount(a,b,metric_account_entity.current_network_balance)
			clone_complete["date_created"] = metric_account_entity.date_created
			m = str(clone_complete["date_created"].month)
			d = str(clone_complete["date_created"].day)
			y = str(clone_complete["date_created"].year)
			clone_complete["d_date_created"] = "%s/%s/%s" % (m,d,y)
			clone_complete["latitude"] = t_user_object.location_latitude
			clone_complete["longitude"] = t_user_object.location_longitude
			clone_complete["map_marker_count"] = 1
			clone_complete["map_data"] = []
			# create marker data for target account
			marker = {}
			marker["link"] = ""
			marker["polyline"] = ""
			marker["username_alias"] = fstr_account_name
			marker["latitude"] = clone_complete["latitude"]
			marker["longitude"] = clone_complete["longitude"]
			clone_complete["map_data"].append(marker)		
			# get the clone accounts parent information
			clone_complete["has_parent"] = True
			result, parent_user, parent_metric = get_parent_for_account(network_id,metric_account_entity.account_parent)
			if not result:
				return False # error pass up error
			clone_complete["parent_entity"] = {}
			a = parent_user
			b = network_id
			c = parent_metric.account_id
			d = parent_metric.account_type
			clone_complete["parent_entity"]["username_alias"] = get_label_for_account(a,b,c,d)
			a = network
			b = parent_metric
			c = parent_metric.current_network_balance
			d = parent_metric.current_reserve_balance
			clone_complete["parent_entity"]["network_balance"] = get_formatted_amount(a,b,c)
			clone_complete["parent_entity"]["reserve_balance"] = get_formatted_amount(a,b,d)
			
			return clone_complete
			
		self.PARENT.RETURN_CODE = "1282" # error Invalid account type
		return False
		
	@ndb.transactional(xg=True)
	def _network_add(self,fname):
	
		# new name check
		maybe_key = ndb.Key("ds_mr_unique_dummy_entity", fname)
		maybe_dummy_entity = maybe_key.get()
		if maybe_dummy_entity is not None:
			self.PARENT.TRACE.append("metric._save_unique_name():entity was returned")
			# network name already exists
			self.PARENT.RETURN_CODE = "1105"
			return False # False meaning "not created"
		new_name_entity = ds_mr_unique_dummy_entity()
		new_name_entity.unique_name = fname
		new_name_entity.key = maybe_key
		new_name_entity.name_type = "networkname"
		
		# Before we can assign a network id, we need to figure out
		# what the network id count is.  This is stored in our 
		# system cursor, which is similar to network cursor we are
		# about to create only for networks.  If the system cursor
		# hasn't been created yet, we'll create it.
		system_cursor_key = ndb.Key("ds_mr_system_cursor", "system")
		system_cursor = system_cursor_key.get()
		if system_cursor is None:
			system_cursor = ds_mr_system_cursor()
			system_cursor.key = system_cursor_key
			system_cursor.current_index = 1
		else:
			system_cursor.current_index +=1
		system_cursor.put()
		new_name_entity.network_id = system_cursor.current_index
		new_name_entity.put()
		
		net_id = system_cursor.current_index

		# create the network profile
		network_key = ndb.Key("ds_mr_network_profile", "%s" % str(net_id).zfill(8))
		new_network_profile = ds_mr_network_profile()
		new_network_profile.network_name = fname
		new_network_profile.network_id = net_id
		new_network_profile.orphan_count = 0
		new_network_profile.total_trees = 0
		# use the proper key from above
		new_network_profile.key = network_key
		new_network_profile.put()

		# also make the cursor for the network when making the network
		network_cursor_key = ndb.Key("ds_mr_network_cursor", "%s" % str(net_id).zfill(8))
		new_network_cursor = ds_mr_network_cursor()
		new_network_cursor.current_index = 0
		new_network_cursor.network_id = net_id
		new_network_cursor.key = network_cursor_key
		new_network_cursor.put()

		# transaction log
		lds_tx_log = ds_mr_tx_log()
		lds_tx_log.tx_type = "NETWORK ADDED" # SHORT WORD(S) FOR WHAT TRANSACTION DID
		lds_tx_log.description = "A new network was created." 
		lds_tx_log.memo = "%s %s" % (fname, str(net_id))
		lds_tx_log.user_id_created = self.PARENT.user.entity.user_id
		lds_tx_log.network_id = net_id
		lds_tx_log.put()

		return True

	@ndb.transactional(xg=True)
	def _network_modify(self,fname,fnewname=None,fdescription=None,fskintillionths=None,ftype=None,fstatus=None,delete_network=False):
	
		# get network by name
		network_name_key = ndb.Key("ds_mr_unique_dummy_entity", fname)
		network_name_entity = network_name_key.get()
		if network_name_entity is None:
			self.PARENT.RETURN_CODE = "1109"
			return False # Name not valid
		# get the network from the name entity reference
		net_id = network_name_entity.network_id
		network_key = ndb.Key("ds_mr_network_profile", "%s" % str(net_id).zfill(8))
		network_profile = network_key.get()
		
		tx_description = ""
		
		if delete_network:
			if network_profile.network_status == "INACTIVE":
				network_profile.network_status = "DELETED"
				network_profile.put()
				tx_description = "Network deleted."
			else:
				# can't delete, only inactive networks can be deleted manually
				self.PARENT.RETURN_CODE = "1106"
				return False
		else:
			if not fdescription is None:
				if not network_profile.network_status == "INACTIVE":
					self.PARENT.RETURN_CODE = "1108"
					return False
				network_profile.description = fdescription
				tx_description = "Network description updated."
			if not fskintillionths is None:
				if not network_profile.network_status == "INACTIVE":
					self.PARENT.RETURN_CODE = "1108"
					return False
				network_profile.skintillionths = fskintillionths
				tx_description = "Network skintillionth conversion updated."
			if not ftype is None:
				if not network_profile.network_status == "INACTIVE":
					self.PARENT.RETURN_CODE = "1108"
					return False
				network_profile.network_type = ftype
				tx_description = "Network type updated."
			if not fstatus is None:
				if not network_profile.network_status == "INACTIVE":
					self.PARENT.RETURN_CODE = "1108"
					return False
				network_profile.network_status = fstatus
				tx_description = "Network status updated."
			if not fnewname is None:
				# verify new name is valid
				new_name_key = ndb.Key("ds_mr_unique_dummy_entity", fnewname)
				new_name_entity = new_name_key.get()
				if new_name_entity is None:
					new_name_entity = ds_mr_unique_dummy_entity()
					new_name_entity.unique_name = fnewname
					network_profile.network_name = fnewname
					new_name_entity.network_id = net_id
					new_name_entity.key = new_name_key
					new_name_entity.name_type = "networkname"
					new_name_entity.put()
					network_name_key.delete()
					tx_description = "Network name changed."
				else:
					# network name already exists
					self.PARENT.RETURN_CODE = "1105"
					return False
			network_profile.put()
		
		# transaction log
		lds_tx_log = ds_mr_tx_log()
		lds_tx_log.tx_type = "NETWORK MODIFIED" # SHORT WORD(S) FOR WHAT TRANSACTION DID
		lds_tx_log.description = tx_description 
		lds_tx_log.memo = "%s %s" % (fname, str(net_id))
		lds_tx_log.user_id_created = self.PARENT.user.entity.user_id
		lds_tx_log.network_id = net_id
		lds_tx_log.put()
		
		return True

	def _get_all_accounts(self,fstr_network_name):	
		
		# get network by name
		network_name_key = ndb.Key("ds_mr_unique_dummy_entity", fstr_network_name)
		network_name_entity = network_name_key.get()
		if network_name_entity is None:
			self.PARENT.RETURN_CODE = "1134"
			return False # Name not valid
		if not network_name_entity.name_type == "networkname":
			self.PARENT.RETURN_CODE = "1135"
			return False
		net_id = network_name_entity.network_id
		list_of_account_ids = []
		list_of_group_ids = []
		list_of_labels = []
		
		"""
		RESERVE ACCOUNT 
		LABEL:
		
		CUSTOMER ACCOUNTS 
		ID: 1 LABEL: wizardwatson
		
		JOINT ACCOUNTS
		ID: 45 LABEL: wizardwatson
		
		CLONE ACCOUNTS
		ID: 4567 LABEL: wizardwatson
		
		SPONSORED JOINT ACCOUNTS
		
		
		SPONSORED CLIENT ACCOUNTS
		"""
		for i in range(len(self.PARENT.user.entity.reserve_network_ids)):
			if self.PARENT.user.entity.reserve_network_ids[i] == net_id:
				list_of_account_ids.append(self.PARENT.user.entity.reserve_account_ids[i])
				list_of_group_ids.append(1)
				list_of_labels.append(self.PARENT.user.entity.reserve_labels[i])
		for i in range(len(self.PARENT.user.entity.client_network_ids)):
			if self.PARENT.user.entity.client_network_ids[i] == net_id:
				list_of_account_ids.append(self.PARENT.user.entity.client_account_ids[i])
				list_of_group_ids.append(2)
				list_of_labels.append(self.PARENT.user.entity.client_labels[i])
		for i in range(len(self.PARENT.user.entity.joint_network_ids)):
			if self.PARENT.user.entity.joint_network_ids[i] == net_id:
				list_of_account_ids.append(self.PARENT.user.entity.joint_account_ids[i])
				list_of_group_ids.append(3)
				list_of_labels.append(self.PARENT.user.entity.joint_labels[i])
		for i in range(len(self.PARENT.user.entity.clone_network_ids)):
			if self.PARENT.user.entity.clone_network_ids[i] == net_id:
				list_of_account_ids.append(self.PARENT.user.entity.clone_account_ids[i])
				list_of_group_ids.append(4)
				list_of_labels.append(self.PARENT.user.entity.clone_labels[i])
		for i in range(len(self.PARENT.user.entity.child_client_network_ids)):
			if self.PARENT.user.entity.child_client_network_ids[i] == net_id:
				list_of_account_ids.append(self.PARENT.user.entity.child_client_account_ids[i])
				list_of_group_ids.append(5)
		for i in range(len(self.PARENT.user.entity.child_joint_network_ids)):
			if self.PARENT.user.entity.child_joint_network_ids[i] == net_id:
				list_of_account_ids.append(self.PARENT.user.entity.child_joint_account_ids[i])
				list_of_group_ids.append(6)
		
		if len(list_of_account_ids) == 0:
			return None
			
		# now construct a list of keys
		list_of_keys = []
		for i in range(len(list_of_account_ids)):
			a_key = ndb.Key("ds_mr_metric_account","%s%s" % (str(net_id).zfill(8),str(list_of_account_ids[i]).zfill(12)))
			list_of_keys.append(a_key)
		list_of_accounts = ndb.get_multi(list_of_keys)
		
		groups = {}
		
		groups["reserve_account"] = None
		groups["client_accounts"] = []
		groups["joint_accounts"] = []
		groups["clone_accounts"] = []
		groups["child_client_accounts"] = []
		groups["child_joint_accounts"] = []
		
		groups["has_reserve_account"] = False
		groups["has_client_accounts"] = False
		groups["has_joint_accounts"] = False
		groups["has_clone_accounts"] = False
		groups["has_child_client_accounts"] = False
		groups["has_child_joint_accounts"] = False
		
		for i in range(len(list_of_accounts)):
			if list_of_group_ids[i] == 1:
				groups["has_reserve_account"] = True
				list_of_accounts[i].extra_pickle = {'account':list_of_labels[i],'network':fstr_network_name}
				groups["reserve_account"] = list_of_accounts[i]
			if list_of_group_ids[i] == 2:
				groups["has_client_accounts"] = True
				list_of_accounts[i].extra_pickle = {'account':list_of_labels[i],'network':fstr_network_name}
				groups["client_accounts"].append(list_of_accounts[i])
			if list_of_group_ids[i] == 3:
				groups["has_joint_accounts"] = True
				list_of_accounts[i].extra_pickle = {'account':list_of_labels[i],'network':fstr_network_name}
				groups["joint_accounts"].append(list_of_accounts[i])
			if list_of_group_ids[i] == 4:
				groups["has_clone_accounts"] = True
				list_of_accounts[i].extra_pickle = {'account':list_of_labels[i],'network':fstr_network_name}
				groups["clone_accounts"].append(list_of_accounts[i])
			if list_of_group_ids[i] == 5:
				groups["has_child_client_accounts"] = True
				list_of_accounts[i].extra_pickle = {'account':list_of_labels[i],'network':fstr_network_name}
				groups["child_client_accounts"].append(list_of_accounts[i])
			if list_of_group_ids[i] == 6:
				groups["has_child_joint_accounts"] = True
				list_of_accounts[i].extra_pickle = {'account':list_of_labels[i],'network':fstr_network_name}
				groups["child_joint_accounts"].append(list_of_accounts[i])
						
		return groups
		
	def _get_all_networks(self):
	
		"""
			We want to show all networks to everyone, but if they are members of
			certain networks we will show those on top.

			FOR LOGGED IN USERS:

			My Live Networks (inset)
			
			My Test Networks (inset)

			[Other] Live Networks (inset)
			
			[Other] Test Networks (inset/collapsible)
			Inactive Networks (inset/collapsible)
			Deleted Networks (inset/collapsible)


			FOR ANONYMOUS VIEWERS:

			Live Networks (inset)

			Test Networks (inset/collapsible)
			Inactive Networks (inset/collapsible)
			Deleted Networks (inset/collapsible)		
		"""
		system_cursor_key = ndb.Key("ds_mr_system_cursor", "system")
		system_cursor = system_cursor_key.get()
		if system_cursor is None:
			# No networks in the system yet.
			return None
		
		list_of_keys = []
		for i in range(1,system_cursor.current_index + 1):
			a_key = ndb.Key("ds_mr_network_profile","%s" % str(i).zfill(8))
			list_of_keys.append(a_key)
		list_of_networks = ndb.get_multi(list_of_keys)
		
		groups = {}
		groups["has_my_live_networks"] = False
		groups["has_my_test_networks"] = False
		groups["has_live_networks"] = False
		groups["has_one_of_test_inactive_deleted"] = False
		groups["has_test_networks"] = False
		groups["has_inactive_networks"] = False
		groups["has_deleted_networks"] = False
		
		groups["my_live_networks"] = []
		groups["my_test_networks"] = []
		groups["live_networks"] = []
		groups["test_networks"] = []
		groups["inactive_networks"] = []
		groups["deleted_networks"] = []
		
		if self.PARENT.user.IS_LOGGED_IN:
			for network in list_of_networks:
				if network.network_status == "DELETED":
					groups["has_deleted_networks"] = True
					groups["deleted_networks"].append(network)
				elif network.network_status == "INACTIVE":
					groups["has_inactive_networks"] = True
					groups["inactive_networks"].append(network)
				elif network.network_status == "ACTIVE":
					if network.network_type == "LIVE":
						if network.network_id in self.PARENT.user.entity.reserve_network_ids:
							groups["has_my_live_networks"] = True
							groups["my_live_networks"].append(network)
						elif network.network_id in self.PARENT.user.entity.joint_network_ids:
							groups["has_my_live_networks"] = True
							groups["my_live_networks"].append(network)
						elif network.network_id in self.PARENT.user.entity.client_network_ids:
							groups["has_my_live_networks"] = True
							groups["my_live_networks"].append(network)
						else:
							groups["has_live_networks"] = True
							groups["live_networks"].append(network)
					elif network.network_type == "TEST":
						if network.network_id in self.PARENT.user.entity.reserve_network_ids:
							groups["has_my_test_networks"] = True
							groups["my_test_networks"].append(network)	
						elif network.network_id in self.PARENT.user.entity.joint_network_ids:
							groups["has_my_test_networks"] = True
							groups["my_test_networks"].append(network)	
						elif network.network_id in self.PARENT.user.entity.client_network_ids:
							groups["has_my_test_networks"] = True
							groups["my_test_networks"].append(network)	
						else:
							groups["has_test_networks"] = True
							groups["test_networks"].append(network)
		else:
			for network in list_of_networks:
				if network.network_status == "DELETED":
					groups["has_deleted_networks"] = True
					groups["deleted_networks"].append(network)
				elif network.network_status == "INACTIVE":
					groups["has_inactive_networks"] = True
					groups["inactive_networks"].append(network)
				elif network.network_status == "ACTIVE":
					if network.network_type == "LIVE":
						groups["has_live_networks"] = True
						groups["live_networks"].append(network)
					elif network.network_type == "TEST":
						groups["has_test_networks"] = True
						groups["test_networks"].append(network)
		if groups["has_test_networks"] or groups["has_inactive_networks"] or groups["has_deleted_networks"]:		
			groups["has_one_of_test_inactive_deleted"] = True
							
		return groups

	def _get_network(self,fstr_network_name=None,fint_network_id=None):
	
		if not fstr_network_name is None:
			# get network by name
			network_name_key = ndb.Key("ds_mr_unique_dummy_entity", fstr_network_name)
			network_name_entity = network_name_key.get()
			if network_name_entity is None:
				self.PARENT.RETURN_CODE = "1109"
				return None # Name not valid
			# get the network from the name entity reference
			net_id = network_name_entity.network_id
			network_key = ndb.Key("ds_mr_network_profile", "%s" % str(net_id).zfill(8))
			network_profile = network_key.get()
		elif not fint_network_id is None:
			# get network by id
			network_key = ndb.Key("ds_mr_network_profile","%s" % str(fint_network_id).zfill(8))
			network_profile = network_key.get()
			if network_profile is None:
				self.PARENT.RETURN_CODE = "1110"
				return None # Name not valid
		return network_profile

	@ndb.transactional(xg=True)
	def _save_unique_alias(self,fstr_alias,fint_network_id,fint_account_id):
	
		# new alias check
		maybe_new_key = ndb.Key("ds_mr_unique_dummy_entity", fstr_alias)
		maybe_dummy_entity = maybe_new_key.get()
		if maybe_dummy_entity is not None:
			return False # False meaning "not created"
		new_entity = ds_mr_unique_dummy_entity()
		new_entity.unique_name = fstr_alias
		new_entity.key = maybe_new_key		
		new_entity.name_type = "alias"
		new_entity.user_id = self.PARENT.user.entity.user_id
		new_entity.account_id = fint_account_id
		new_entity.network_id = fint_network_id
		new_entity.put()
						
		return True # True meaning "created"

	@ndb.transactional(xg=True)
	def _alias_change_transactional(self,fstr_current_alias,fstr_new_alias=None,fbool_delete=False):
	
		"""
		
		TRANSACTIONAL OBJECTS FOR THIS FUNCTION:
		
		(modified) current user object : ds_mr_user
		(deleted) current alias name object : ds_mr_unique_dummy_entity
		
		if changing rather than deleting:
			(created) new alias name object : ds_mr_unique_dummy_entity
			
		"""
		
		# Get current alias
		current_alias_key = ndb.Key("ds_mr_unique_dummy_entity", fstr_current_alias)
		current_alias_entity = current_alias_key.get()
		if current_alias_entity is None:
				self.PARENT.RETURN_CODE = "1225"
				return None # error Current alias invalid
		if not current_alias_entity.name_type == "alias":
				self.PARENT.RETURN_CODE = "1226"
				return None # error Name passed is not an alias of a metric account.
		
		# Get the current user transactionally.
		current_user_key = ndb.Key("ds_mr_user",current_alias_entity.user_id)
		current_user = current_user_key.get()
		if current_user is None:
				self.PARENT.RETURN_CODE = "1227"
				return None # error User id from current alias is invalid.
				
		# The logged in user must be the target
		if not current_user.user_id == self.PARENT.user.entity.user_id:
				self.PARENT.RETURN_CODE = "1299"
				return None # error For alias change, target must be current user.
		
			
		if not fbool_delete:
			new_label = fstr_new_alias		
			if self._save_unique_alias(fstr_new_alias,current_alias_entity.network_id,current_alias_entity.account_id):
				current_alias_key.delete()
				self.PARENT.RETURN_CODE = "7043" # Successfully changed alias.
			else:
				self.PARENT.RETURN_CODE = "1228"
				return False # error New alias chosen is not unique.
		else:
			new_label = current_user.username
			# We are wanting to delete this alias, but for that, the 
			# username must be available.
			username_in_use = False
			for i in range(len(current_user.reserve_network_ids)):
				if current_user.reserve_network_ids[i] == current_alias_entity.network_id:
					if current_user.reserve_labels[i] == current_user.username:
						username_in_use = True
						break
			for i in range(len(current_user.client_network_ids)):
				if current_user.client_network_ids[i] == current_alias_entity.network_id:
					if current_user.client_labels[i] == current_user.username:
						username_in_use = True
						break
			for i in range(len(current_user.joint_network_ids)):
				if current_user.joint_network_ids[i] == current_alias_entity.network_id:
					if current_user.joint_labels[i] == current_user.username:
						username_in_use = True
						break		
			for i in range(len(current_user.clone_network_ids)):
				if current_user.clone_network_ids[i] == current_alias_entity.network_id:
					if current_user.clone_labels[i] == current_user.username:
						username_in_use = True
						break
			if username_in_use:
				self.PARENT.RETURN_CODE = "1229"
				return False # error Cannot delete alias as username already a label on this network.
			else:
				# delete the alias
				current_alias_key.delete()
				self.PARENT.RETURN_CODE = "7044" # Successfully deleted alias. Account now uses username.
				
		# put the new label in the users account list
		for i in range(len(current_user.reserve_network_ids)):
			if current_user.reserve_network_ids[i] == current_alias_entity.network_id:
				if current_user.reserve_account_ids[i] == current_alias_entity.account_id:
					current_user.reserve_labels[i] = new_label
					break
		for i in range(len(current_user.client_network_ids)):
			if current_user.client_network_ids[i] == current_alias_entity.network_id:
				if current_user.client_account_ids[i] == current_alias_entity.account_id:
					current_user.client_labels[i] = new_label
					break
		for i in range(len(current_user.joint_network_ids)):
			if current_user.joint_network_ids[i] == current_alias_entity.network_id:
				if current_user.joint_account_ids[i] == current_alias_entity.account_id:
					current_user.joint_labels[i] = new_label
					break		
		for i in range(len(current_user.clone_network_ids)):
			if current_user.clone_network_ids[i] == current_alias_entity.network_id:
				if current_user.clone_account_ids[i] == current_alias_entity.account_id:
					current_user.clone_labels[i] = new_label
					break
						
		current_user.put()
		return True

	@ndb.transactional(xg=True)
	def _get_account_label(self,fint_network_id,fint_account_id):
	
		# Create a new alias if the user has more than one account
		# on this network, and "username" is not available.
		has_multiple = False
		username_in_use = False
		for i in range(len(self.PARENT.user.entity.reserve_network_ids)):
			if self.PARENT.user.entity.reserve_network_ids[i] == fint_network_id:
				has_multiple = True
				if self.PARENT.user.entity.reserve_labels[i] == self.PARENT.user.entity.username:
					username_in_use = True
					break
		for i in range(len(self.PARENT.user.entity.client_network_ids)):
			if self.PARENT.user.entity.client_network_ids[i] == fint_network_id:
				has_multiple = True
				if self.PARENT.user.entity.client_labels[i] == self.PARENT.user.entity.username:
					username_in_use = True
					break
		for i in range(len(self.PARENT.user.entity.joint_network_ids)):
			if self.PARENT.user.entity.joint_network_ids[i] == fint_network_id:
				has_multiple = True
				if self.PARENT.user.entity.joint_labels[i] == self.PARENT.user.entity.username:
					username_in_use = True
					break		
		for i in range(len(self.PARENT.user.entity.clone_network_ids)):
			if self.PARENT.user.entity.clone_network_ids[i] == fint_network_id:
				has_multiple = True
				if self.PARENT.user.entity.clone_labels[i] == self.PARENT.user.entity.username:
					username_in_use = True
					break
	
		if username_in_use:
			# create a random alias
			while True:
				some_letters = "abcdefghijkmnprstuvwxyz"
				first_int = str(random.randint(1,999)).zfill(3)
				second_int = str(random.randint(1,999)).zfill(3)
				alias = "alias" + first_int + second_int + random.choice(some_letters) + random.choice(some_letters)			
				if self._save_unique_alias(alias,fint_network_id,fint_account_id):
					break
			return alias
		else:
			# "username" is available
			return self.PARENT.user.entity.username

	def _other_account(self,fstr_network_name,fstr_source_name,fstr_target_name,fstr_type):

		# we don't want/need to get the network conversion rate inside a transaction.
		network = self._get_network(fstr_network_name)
		if network is None: return False # pass up error code
		return self._other_account_transactional(network.network_id,fstr_source_name,fstr_target_name,fstr_type)
		
	@ndb.transactional(xg=True)
	def _other_account_transactional(self,fint_network_id,fstr_source_name,fstr_target_name,fstr_type):
	
		def check_default(fobj_user):
		
			# Check default is just making sure a default account exists
			# when a user adds or deletes accounts.  They may delete the
			# default, or they may add a second account without designating
			# a default.  This makes sure they always have a default if 
			# there is more than one account for them in that network and
			# the system needs to pick one for a function where the user
			# doesn't specifically designate manually.  For instance, a 
			# "search and pay" after deleting 1 of 3 accounts in a network
			# which happens to be the default.
		
			checker = {}
			# first loop set sets checker to True from default of False
			# if a default account is found.
			for i in range(len(fobj_user.reserve_network_ids)):
				if not fobj_user.reserve_network_ids[i] in checker:
					# add the network id as a key to our checker if it doesn't exist
					checker[fobj_user.reserve_network_ids[i]] = fobj_user.reserve_default[i]
				if fobj_user.reserve_default[i]: checker[fobj_user.reserve_network_ids[i]] = True
				
			for i in range(len(fobj_user.client_network_ids)):
				if not fobj_user.client_network_ids[i] in checker:
					# add the network id as a key to our checker if it doesn't exist
					checker[fobj_user.client_network_ids[i]] = fobj_user.client_default[i]
				if fobj_user.client_default[i]: checker[fobj_user.client_network_ids[i]] = True
				
			for i in range(len(fobj_user.joint_network_ids)):
				if not fobj_user.joint_network_ids[i] in checker:
					# add the network id as a key to our checker if it doesn't exist
					checker[fobj_user.joint_network_ids[i]] = fobj_user.joint_default[i]
				if fobj_user.joint_default[i]: checker[fobj_user.joint_network_ids[i]] = True
				
			for i in range(len(fobj_user.clone_network_ids)):
				if not fobj_user.clone_network_ids[i] in checker:
					# add the network id as a key to our checker if it doesn't exist
					checker[fobj_user.clone_network_ids[i]] = fobj_user.clone_default[i]
				if fobj_user.clone_default[i]: checker[fobj_user.clone_network_ids[i]] = True

			# second loop says, if the checker for that network id is False
			# set the checker for that network id and the default value on
			# that account to True.
			for i in range(len(fobj_user.reserve_network_ids)):
				if checker[fobj_user.reserve_network_ids[i]] == False:
					checker[fobj_user.reserve_network_ids[i]] = True
					fobj_user.reserve_default[i] = True
					
			for i in range(len(fobj_user.client_network_ids)):
				if checker[fobj_user.client_network_ids[i]] == False:
					checker[fobj_user.client_network_ids[i]] = True
					fobj_user.client_default[i] = True

			for i in range(len(fobj_user.joint_network_ids)):
				if checker[fobj_user.joint_network_ids[i]] == False:
					checker[fobj_user.joint_network_ids[i]] = True
					fobj_user.joint_default[i] = True

			for i in range(len(fobj_user.clone_network_ids)):
				if checker[fobj_user.clone_network_ids[i]] == False:
					checker[fobj_user.clone_network_ids[i]] = True
					fobj_user.clone_default[i] = True
					
		if fstr_type == "joint offer":
		
			"""
			joint offer			
				SOURCE: current user object/account		
				TARGET: other user object			
				ACTION: Modifies user objects
			"""		
			validation_result = self._name_validate_transactional(None,fstr_source_name,fstr_target_name,fint_network_id)
			if not validation_result:
				# pass up error
				return False
			
			network_id = validation_result[0]
			source_account_id = validation_result[1]
			source_user = validation_result[3]
			target_account_id = validation_result[2]
			target_user = validation_result[4]
			
			# transactionally get the source and target metric accounts
			key_part1 = str(network_id).zfill(8)
			key_part2 = str(source_account_id).zfill(12)
			source_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part2))
			lds_source_metric = source_key.get()

			# error if source doesn't exist
			if lds_source_metric is None:
				self.PARENT.RETURN_CODE = "1206"
				return False # error: source id is not valid
			# error if trying to offer to self
			if source_account_id == target_account_id: 
				self.PARENT.RETURN_CODE = "1175"
				return False # error: cannot make account offer to self.
			# error if not a reserve account
			if not lds_source_metric.account_type == "RESERVE" and not lds_source_metric.account_status == "ACTIVE":
				self.PARENT.RETURN_CODE = "1176"
				return False # error: only active reserve accounts can offer, source is not
				
			# 1. Source cannot have any existing child joint offers.
			if not source_user.child_joint_offer_network_id == 0:
				self.PARENT.RETURN_CODE = "1177"
				return False # error: Source currently has existing joint offer.  Previous offers must be cancelled/authorized before new ones created.
			# 2. Target cannot have any existing joint offers.
			if not target_user.parent_joint_offer_network_id == 0:
				self.PARENT.RETURN_CODE = "1178"
				return False # error: Target currently has offer for joint account.  Previous offers must be cancelled/authorized before new ones created.
			# 3. Source must not be maxed out on child accounts.
			if not source_user.total_child_accounts > 19:
				self.PARENT.RETURN_CODE = "1179"
				return False # error: Source child accounts is currently at maximum.
			# 4. Target must not be maxed out on alternate accounts.
			if not target_user.total_other_accounts > 19:
				self.PARENT.RETURN_CODE = "1180"
				return False # error: Target other accounts is currently at maximum.
				
			# should be ok to create this offer
			source_user.child_joint_offer_network_id = network_id
			source_user.child_joint_offer_account_id = 0
			source_user.child_joint_offer_user_id = target_user.user_id
			target_user.parent_joint_offer_network_id = network_id
			target_user.parent_joint_offer_account_id = source_account_id
			target_user.parent_joint_offer_user_id = source_user.user_id
			
			source_user.put()
			target_user.put()
			
			self.PARENT.RETURN_CODE = "7029" # success: Joint account offer successfully created.
			
			return True
			
		if fstr_type == "joint offer cancel":
		
			"""
			joint offer	cancel		
				SOURCE: current user object/account		
				TARGET: other user object			
				ACTION: Modifies user objects
			"""	
			validation_result = self._name_validate_transactional(None,fstr_source_name,None,fint_network_id)
			if not validation_result:
				# pass up error
				return False
			
			network_id = validation_result[0]
			source_user = validation_result[3]
			
			# as long as joint offer matches both source and target, either can delete
			if source_user.child_joint_offer_network_id == 0:
				self.PARENT.RETURN_CODE = "1181"
				return False # error: The source has no active joint offer.			
			# We allow for the fact that cancelling offers can be done from any context
			# so we may not have a handle on the target user_id.  So lets just re-query
			# the target just to be sure.		
			# load user transactionally
			target_user_key = ndb.Key("ds_mr_user",source_user.child_joint_offer_user_id)
			target_user = source_user_key.get()
			# error if target doesn't exist
			if target_user is None:
				self.PARENT.RETURN_CODE = "1182"
				return False # error: target id is not valid
			
			source_user.child_joint_offer_network_id = 0
			source_user.child_joint_offer_account_id = 0
			source_user.child_joint_offer_user_id = "EMPTY"
			target_user.parent_joint_offer_network_id = 0
			target_user.parent_joint_offer_account_id = 0
			target_user.parent_joint_offer_user_id = "EMPTY"
			
			source_user.put()
			target_user.put()
			
			self.PARENT.RETURN_CODE = "7030" # success: Joint account offer successfully cancelled.
			
			return True

		if fstr_type == "joint offer deny":
		
			"""
			joint offer	cancel		
				SOURCE: current user object/account		
				TARGET: other user object			
				ACTION: Modifies user objects
			"""		
			validation_result = self._name_validate_transactional(None,fstr_source_name,None,fint_network_id)
			if not validation_result:
				# pass up error
				return False
			
			network_id = validation_result[0]
			source_user = validation_result[3]
			
			# as long as joint offer matches both source and target, either can delete
			if source_user.parent_joint_offer_network_id == 0:
				self.PARENT.RETURN_CODE = "1183"
				return False # error: The source has not been offered a joint account.			
			# We allow for the fact that cancelling offers can be done from any context
			# so we may not have a handle on the target user_id.  So lets just re-query
			# the target just to be sure.		
			# load user transactionally
			target_user_key = ndb.Key("ds_mr_user",source_user.parent_joint_offer_user_id)
			target_user = source_user_key.get()
			# error if target doesn't exist
			if target_user is None:
				self.PARENT.RETURN_CODE = "1184"
				return False # error: target id is not valid
			
			target_user.child_joint_offer_network_id = 0
			target_user.child_joint_offer_account_id = 0
			target_user.child_joint_offer_user_id = "EMPTY"
			source_user.parent_joint_offer_network_id = 0
			source_user.parent_joint_offer_account_id = 0
			source_user.parent_joint_offer_user_id = "EMPTY"
			
			source_user.put()
			target_user.put()
			
			self.PARENT.RETURN_CODE = "7031" # success: Joint account offer successfully denied.
			
			return True
			
		if fstr_type == "joint authorize":
		
			"""
			joint authorize		
				SOURCE: current user object				
				TARGET: other user object/account
				ACTION: Modifies user objects AND makes new account
			"""		
			validation_result = self._name_validate_transactional(None,fstr_source_name,None,fint_network_id)
			if not validation_result:
				# pass up error
				return False
			
			network_id = validation_result[0]
			source_user = validation_result[3]
			
			# make sure source actually has a joint offer
			if source_user.parent_joint_offer_user_id == 0:
				self.PARENT.RETURN_CODE = "1185"
				return False # error: The source has no active joint offer.
			
			# load target transactionally
			target_user_key = ndb.Key("ds_mr_user",source_user.parent_joint_offer_user_id)
			target_user = source_user_key.get()
			# error if target doesn't exist
			if target_user is None:
				self.PARENT.RETURN_CODE = "1186"
				return False # error: target id is not valid
			
			fail_this = False
			if not source_user.parent_joint_offer_network_id == target_user.child_joint_offer_network_id: fail_this = True
			if not source_user.parent_joint_offer_account_id == target_user.child_joint_offer_account_id: fail_this = True
			if not source_user.parent_joint_offer_user_id == target_user.child_joint_offer_user_id: fail_this = True

			if not fail_this:
				# We're good to go.
				# load cursor transactionally
				cursor_key = ndb.Key("ds_mr_network_cursor", "%s" % str(network_id).zfill(8))		
				lds_cursor = cursor_key.get()
				lds_cursor.current_index += 1
				# 1. Get label for the new account
				label = self._get_account_label(network_id,lds_cursor.current_index)
				# 2. Create new account
				# create a new metric account with key equal to current cursor/index for this network
				new_metric_account_key = ndb.Key("ds_mr_metric_account","%s%s" % (str(network_id).zfill(8),str(lds_cursor.current_index).zfill(12)))
				lds_new_metric_account = ds_mr_metric_account()
				
				lds_new_metric_account.network_id = network_id
				lds_new_metric_account.account_id = lds_cursor.current_index
				lds_new_metric_account.user_id = source_user.user_id
				# creating the account is our first transaction
				lds_new_metric_account.tx_index = 1
				lds_new_metric_account.account_status = "ACTIVE"		
				lds_new_metric_account.account_type = "JOINT"
				lds_new_metric_account.account_parent = source_user.parent_joint_offer_account_id
				lds_new_metric_account.key = new_metric_account_key
				
				# mutable defaults
				lds_new_metric_account.outgoing_connection_requests = []
				lds_new_metric_account.incoming_connection_requests = []
				lds_new_metric_account.incoming_reserve_transfer_requests = {}
				lds_new_metric_account.outgoing_reserve_transfer_requests = {}
				lds_new_metric_account.suggested_inactive_incoming_reserve_transfer_requests = {}
				lds_new_metric_account.suggested_inactive_outgoing_reserve_transfer_requests = {}
				lds_new_metric_account.suggested_active_incoming_reserve_transfer_requests = {}
				lds_new_metric_account.suggested_active_outgoing_reserve_transfer_requests = {}
				lds_new_metric_account.current_connections = []
				lds_new_metric_account.last_connections = []
				
				# update the source user object
				source_user.total_other_accounts += 1
				source_user.joint_network_ids.append(network_id)
				source_user.joint_account_ids.append(lds_cursor.current_index)
				source_user.joint_labels.append(label)
				source_user.joint_default.append(False)
				source_user.parent_joint_offer_network_id = 0
				source_user.parent_joint_offer_account_id = 0
				source_user.parent_joint_offer_user_id = "EMPTY"
				# update the target user object
				target_user.total_other_accounts += 1
				target_user.child_joint_network_ids.append(network_id)
				target_user.child_joint_account_ids.append(lds_cursor.current_index)
				target_user.child_joint_parent_ids.append(lds_new_metric_account.account_parent)
				target_user.child_joint_offer_network_id = 0
				target_user.child_joint_offer_account_id = 0
				target_user.child_joint_offer_user_id = "EMPTY"
				
				# transaction log
				tx_source_log_key = ndb.Key("ds_mr_tx_log", "MRTX2%s%s%s" % (str(network_id).zfill(8),str(lds_cursor.current_index).zfill(12),str(1).zfill(12)))
				lds_source_tx_log = ds_mr_tx_log()
				lds_source_tx_log.key = tx_source_log_key
				lds_source_tx_log.tx_index = 1
				lds_source_tx_log.tx_type = "JOINT ACCOUNT CREATED ON NETWORK" # SHORT WORD(S) FOR WHAT TRANSACTION DID
				lds_source_tx_log.description = "A joint account was created for you."
				lds_source_tx_log.memo = "Account Opened"
				lds_source_tx_log.category = "MRTX2"
				lds_source_tx_log.amount = 0
				lds_source_tx_log.user_id_created = source_user.user_id
				lds_source_tx_log.network_id = network_id
				lds_source_tx_log.account_id = lds_cursor.current_index
				lds_source_tx_log.source_account = lds_cursor.current_index
				lds_source_tx_log.target_account = source_user.parent_joint_offer_account_id
				lds_source_tx_log.put()

				# transaction log
				lds_target_tx_log = ds_mr_tx_log()
				lds_target_tx_log.tx_type = "CHILD JOINT ACCOUNT CREATED ON NETWORK" # SHORT WORD(S) FOR WHAT TRANSACTION DID
				lds_target_tx_log.description = "A child user created a joint account on network." 
				lds_target_tx_log.user_id_created = source_user.user_id
				lds_target_tx_log.network_id = network_id
				lds_target_tx_log.account_id = lds_cursor.current_index
				lds_target_tx_log.source_account = lds_cursor.current_index 
				lds_target_tx_log.target_account = source_user.parent_joint_offer_account_id
				lds_target_tx_log.put()

				# save the transaction
				check_default(source_user)
				source_user.put()
				target_user.put()
				lds_new_metric_account.put()
				lds_cursor.put()

				self.PARENT.RETURN_CODE = "7032" # success: Joint account account successfully created.

				return True
			else:
				self.PARENT.RETURN_CODE = "1187"
				return False # error: Source and target joint offers did not match.
					
		if fstr_type == "client offer":
		
			"""
			client offer			
				SOURCE: current user object/account		
				TARGET: other user object			
				ACTION: Modifies user objects
			"""		
			validation_result = self._name_validate_transactional(None,fstr_source_name,fstr_target_name,fint_network_id)
			if not validation_result:
				# pass up error
				return False
			
			network_id = validation_result[0]
			source_account_id = validation_result[1]
			source_user = validation_result[3]
			target_account_id = validation_result[2]
			target_user = validation_result[4]
			
			# transactionally get the source and target metric accounts
			key_part1 = str(network_id).zfill(8)
			key_part2 = str(source_account_id).zfill(12)
			source_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part2))
			lds_source_metric = source_key.get()

			# error if source doesn't exist
			if lds_source_metric is None:
				self.PARENT.RETURN_CODE = "1188"
				return False # error: source id is not valid
			# error if trying to offer to self
			if source_account_id == target_account_id: 
				self.PARENT.RETURN_CODE = "1189"
				return False # error: cannot make account offer to self.
			# error if not a reserve account
			if not lds_source_metric.account_type == "RESERVE" and not lds_source_metric.account_status == "ACTIVE":
				self.PARENT.RETURN_CODE = "1190"
				return False # error: only active reserve accounts can offer, source is not
				
			# 1. Source cannot have any existing child client offers.
			if not source_user.child_client_offer_network_id == 0:
				self.PARENT.RETURN_CODE = "1191"
				return False # error: Source currently has existing client offer.  Previous offers must be cancelled/authorized before new ones created.
			# 2. Target cannot have any existing client offers.
			if not target_user.parent_client_offer_network_id == 0:
				self.PARENT.RETURN_CODE = "1192"
				return False # error: Target currently has offer for client account.  Previous offers must be cancelled/authorized before new ones created.
			# 3. Source must not be maxed out on child accounts.
			if not source_user.total_child_accounts > 19:
				self.PARENT.RETURN_CODE = "1193"
				return False # error: Source child accounts is currently at maximum.
			# 4. Target must not be maxed out on alternate accounts.
			if not target_user.total_other_accounts > 19:
				self.PARENT.RETURN_CODE = "1194"
				return False # error: Target other accounts is currently at maximum.
				
			# should be ok to create this offer
			source_user.child_client_offer_network_id = network_id
			source_user.child_client_offer_account_id = 0
			source_user.child_client_offer_user_id = target_user.user_id
			target_user.parent_client_offer_network_id = network_id
			target_user.parent_client_offer_account_id = source_account_id
			target_user.parent_client_offer_user_id = source_user.user_id
			
			source_user.put()
			target_user.put()
			
			self.PARENT.RETURN_CODE = "7033" # success: Client account offer successfully created.
			
			return True
			
		if fstr_type == "client offer cancel":
		
			"""
			client offer	cancel		
				SOURCE: current user object/account		
				TARGET: other user object			
				ACTION: Modifies user objects
			"""	
			validation_result = self._name_validate_transactional(None,fstr_source_name,None,fint_network_id)
			if not validation_result:
				# pass up error
				return False
			
			network_id = validation_result[0]
			source_user = validation_result[3]
			
			# as long as client offer matches both source and target, either can delete
			if source_user.child_client_offer_network_id == 0:
				self.PARENT.RETURN_CODE = "1195"
				return False # error: The source has no active client offer.			
			# We allow for the fact that cancelling offers can be done from any context
			# so we may not have a handle on the target user_id.  So lets just re-query
			# the target just to be sure.		
			# load user transactionally
			target_user_key = ndb.Key("ds_mr_user",source_user.child_client_offer_user_id)
			target_user = source_user_key.get()
			# error if target doesn't exist
			if target_user is None:
				self.PARENT.RETURN_CODE = "1196"
				return False # error: target id is not valid
			
			source_user.child_client_offer_network_id = 0
			source_user.child_client_offer_account_id = 0
			source_user.child_client_offer_user_id = "EMPTY"
			target_user.parent_client_offer_network_id = 0
			target_user.parent_client_offer_account_id = 0
			target_user.parent_client_offer_user_id = "EMPTY"
			
			source_user.put()
			target_user.put()
			
			self.PARENT.RETURN_CODE = "7034" # success: Client account offer successfully cancelled.
			
			return True

		if fstr_type == "client offer deny":
		
			"""
			client offer	deny		
				SOURCE: current user object/account		
				TARGET: other user object			
				ACTION: Modifies user objects
			"""		
			validation_result = self._name_validate_transactional(None,fstr_source_name,None,fint_network_id)
			if not validation_result:
				# pass up error
				return False
			
			network_id = validation_result[0]
			source_user = validation_result[3]
			
			# as long as client offer matches both source and target, either can delete
			if source_user.parent_client_offer_network_id == 0:
				self.PARENT.RETURN_CODE = "1197"
				return False # error: The source has not been offered a client account.			
			# We allow for the fact that cancelling offers can be done from any context
			# so we may not have a handle on the target user_id.  So lets just re-query
			# the target just to be sure.		
			# load user transactionally
			target_user_key = ndb.Key("ds_mr_user",source_user.parent_client_offer_user_id)
			target_user = source_user_key.get()
			# error if target doesn't exist
			if target_user is None:
				self.PARENT.RETURN_CODE = "1198"
				return False # error: target id is not valid
			
			target_user.child_client_offer_network_id = 0
			target_user.child_client_offer_account_id = 0
			target_user.child_client_offer_user_id = "EMPTY"
			source_user.parent_client_offer_network_id = 0
			source_user.parent_client_offer_account_id = 0
			source_user.parent_client_offer_user_id = "EMPTY"
			
			source_user.put()
			target_user.put()
			
			self.PARENT.RETURN_CODE = "7035" # success: Client account offer successfully denied.
			
			return True
			
		if fstr_type == "client authorize":
		
			"""
			client authorize		
				SOURCE: current user object				
				TARGET: other user object/account
				ACTION: Modifies user objects AND makes new account
			"""		
			validation_result = self._name_validate_transactional(None,fstr_source_name,None,fint_network_id)
			if not validation_result:
				# pass up error
				return False
			
			network_id = validation_result[0]
			source_user = validation_result[3]
			
			# make sure source actually has a client offer
			if source_user.parent_client_offer_user_id == 0:
				self.PARENT.RETURN_CODE = "1199"
				return False # error: The source has no active client offer.
			
			# load target transactionally
			target_user_key = ndb.Key("ds_mr_user",source_user.parent_client_offer_user_id)
			target_user = source_user_key.get()
			# error if target doesn't exist
			if target_user is None:
				self.PARENT.RETURN_CODE = "1200"
				return False # error: target id is not valid
			
			fail_this = False
			if not source_user.parent_client_offer_network_id == target_user.child_client_offer_network_id: fail_this = True
			if not source_user.parent_client_offer_account_id == target_user.child_client_offer_account_id: fail_this = True
			if not source_user.parent_client_offer_user_id == target_user.child_client_offer_user_id: fail_this = True

			if not fail_this:
				# We're good to go.
				# load cursor transactionally
				cursor_key = ndb.Key("ds_mr_network_cursor", "%s" % str(network_id).zfill(8))		
				lds_cursor = cursor_key.get()
				lds_cursor.current_index += 1
				# 1. Get label for the new account
				label = self._get_account_label(network_id,lds_cursor.current_index)
				# 2. Create new account
				# create a new metric account with key equal to current cursor/index for this network
				new_metric_account_key = ndb.Key("ds_mr_metric_account","%s%s" % (str(network_id).zfill(8),str(lds_cursor.current_index).zfill(12)))
				lds_new_metric_account = ds_mr_metric_account()
				
				lds_new_metric_account.network_id = network_id
				lds_new_metric_account.account_id = lds_cursor.current_index
				lds_new_metric_account.user_id = source_user.user_id
				# creating the account is our first transaction
				lds_new_metric_account.tx_index = 1
				lds_new_metric_account.account_status = "ACTIVE"		
				lds_new_metric_account.account_type = "CLIENT"
				lds_new_metric_account.account_parent = source_user.parent_client_offer_account_id
				
				# mutable defaults
				lds_new_metric_account.outgoing_connection_requests = []
				lds_new_metric_account.incoming_connection_requests = []
				lds_new_metric_account.incoming_reserve_transfer_requests = {}
				lds_new_metric_account.outgoing_reserve_transfer_requests = {}
				lds_new_metric_account.suggested_inactive_incoming_reserve_transfer_requests = {}
				lds_new_metric_account.suggested_inactive_outgoing_reserve_transfer_requests = {}
				lds_new_metric_account.suggested_active_incoming_reserve_transfer_requests = {}
				lds_new_metric_account.suggested_active_outgoing_reserve_transfer_requests = {}
				lds_new_metric_account.current_connections = []
				lds_new_metric_account.last_connections = []
				
				lds_new_metric_account.key = new_metric_account_key
				
				# update the source user object
				source_user.total_other_accounts += 1
				source_user.client_network_ids.append(network_id)
				source_user.client_account_ids.append(lds_cursor.current_index)
				source_user.client_labels.append(label)
				source_user.client_default.append(False)
				source_user.parent_client_offer_network_id = 0
				source_user.parent_client_offer_account_id = 0
				source_user.parent_client_offer_user_id = "EMPTY"
				# update the target user object
				target_user.total_other_accounts += 1
				target_user.child_client_network_ids.append(network_id)
				target_user.child_client_account_ids.append(lds_cursor.current_index)
				target_user.child_client_parent_ids.append(lds_new_metric_account.account_parent)
				target_user.child_client_offer_network_id = 0
				target_user.child_client_offer_account_id = 0
				target_user.child_client_offer_user_id = "EMPTY"
				
				# transaction log
				tx_source_log_key = ndb.Key("ds_mr_tx_log", "MRTX2%s%s%s" % (str(network_id).zfill(8),str(lds_cursor.current_index).zfill(12),str(1).zfill(12)))
				lds_source_tx_log = ds_mr_tx_log()
				lds_source_tx_log.key = tx_source_log_key
				lds_source_tx_log.tx_index = 1
				lds_source_tx_log.tx_type = "CLIENT ACCOUNT CREATED ON NETWORK" # SHORT WORD(S) FOR WHAT TRANSACTION DID
				lds_source_tx_log.description = "A client account was created for you." 
				lds_source_tx_log.memo = "Account Opened"
				lds_source_tx_log.category = "MRTX2"
				lds_source_tx_log.amount = 0
				lds_source_tx_log.user_id_created = source_user.user_id
				lds_source_tx_log.network_id = network_id
				lds_source_tx_log.account_id = lds_cursor.current_index
				lds_source_tx_log.source_account = lds_cursor.current_index
				lds_source_tx_log.target_account = source_user.parent_client_offer_account_id
				lds_source_tx_log.put()

				# transaction log
				lds_target_tx_log = ds_mr_tx_log()
				lds_target_tx_log.tx_type = "CHILD CLIENT ACCOUNT CREATED ON NETWORK" # SHORT WORD(S) FOR WHAT TRANSACTION DID
				lds_target_tx_log.description = "A child user created a client account on network." 
				lds_target_tx_log.user_id_created = source_user.user_id
				lds_target_tx_log.network_id = network_id
				lds_target_tx_log.account_id = lds_cursor.current_index
				lds_target_tx_log.source_account = lds_cursor.current_index 
				lds_target_tx_log.target_account = source_user.parent_client_offer_account_id
				lds_target_tx_log.put()

				# save the transaction
				check_default(source_user)
				source_user.put()
				target_user.put()
				lds_new_metric_account.put()
				lds_cursor.put()

				self.PARENT.RETURN_CODE = "7036" # success: Client account successfully created.

				return True
				
			else:
				self.PARENT.RETURN_CODE = "1201"
				return False # error: Source and target client offers did not match.
				
		if fstr_type == "clone open":
		
			"""
			clone open			
				SOURCE: current user object/account		
				TARGET: None
				ACTION: Modifies this user AND makes new account
			"""		
			validation_result = self._name_validate_transactional(None,fstr_source_name,None,fint_network_id)
			if not validation_result:
				# pass up error
				return False
			
			network_id = validation_result[0]
			source_account_id = validation_result[1]
			source_user = validation_result[3]
			
			# transactionally get the source and target metric accounts
			key_part1 = str(network_id).zfill(8)
			key_part2 = str(source_account_id).zfill(12)
			source_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part2))
			lds_source_metric = source_key.get()

			# error if source doesn't exist
			if lds_source_metric is None:
				self.PARENT.RETURN_CODE = "1202"
				return False # error: source id is not valid
			# error if not a reserve account
			if not lds_source_metric.account_type == "RESERVE" and not lds_source_metric.account_status == "ACTIVE":
				self.PARENT.RETURN_CODE = "1203"
				return False # error: only active reserve accounts can create clone accounts, source is not
				
			# 1. Source must not be maxed out on other accounts.
			if source_user.total_child_accounts > 19:
				self.PARENT.RETURN_CODE = "1204"
				return False # error: Source other accounts is currently at maximum.
				
			# We're good to go.
			# load cursor transactionally
			cursor_key = ndb.Key("ds_mr_network_cursor", "%s" % str(network_id).zfill(8))		
			lds_cursor = cursor_key.get()
			lds_cursor.current_index += 1
			# 1. Get label for the new account
			label = self._get_account_label(network_id,lds_cursor.current_index)
			# 2. Create new account
			# create a new metric account with key equal to current cursor/index for this network
			new_metric_account_key = ndb.Key("ds_mr_metric_account","%s%s" % (str(network_id).zfill(8),str(lds_cursor.current_index).zfill(12)))
			lds_new_metric_account = ds_mr_metric_account()

			lds_new_metric_account.network_id = network_id
			lds_new_metric_account.account_id = lds_cursor.current_index
			lds_new_metric_account.user_id = source_user.user_id
			# creating the account is our first transaction
			lds_new_metric_account.tx_index = 1
			lds_new_metric_account.account_status = "ACTIVE"		
			lds_new_metric_account.account_type = "CLONE"
			lds_new_metric_account.account_parent = lds_source_metric.account_id
			
			# mutable defaults
			lds_new_metric_account.outgoing_connection_requests = []
			lds_new_metric_account.incoming_connection_requests = []
			lds_new_metric_account.incoming_reserve_transfer_requests = {}
			lds_new_metric_account.outgoing_reserve_transfer_requests = {}
			lds_new_metric_account.suggested_inactive_incoming_reserve_transfer_requests = {}
			lds_new_metric_account.suggested_inactive_outgoing_reserve_transfer_requests = {}
			lds_new_metric_account.suggested_active_incoming_reserve_transfer_requests = {}
			lds_new_metric_account.suggested_active_outgoing_reserve_transfer_requests = {}
			lds_new_metric_account.current_connections = []
			lds_new_metric_account.last_connections = []
			
			lds_new_metric_account.key = new_metric_account_key

			# update the source user object
			source_user.total_other_accounts += 1
			source_user.clone_network_ids.append(network_id)
			source_user.clone_account_ids.append(lds_cursor.current_index)
			source_user.clone_parent_ids.append(lds_source_metric.account_id)
			source_user.clone_labels.append(label)
			source_user.clone_default.append(False)

			# transaction log
			tx_source_log_key = ndb.Key("ds_mr_tx_log", "MRTX2%s%s%s" % (str(network_id).zfill(8),str(lds_cursor.current_index).zfill(12),str(1).zfill(12)))
			lds_source_tx_log = ds_mr_tx_log()
			lds_source_tx_log.key = tx_source_log_key
			lds_source_tx_log.tx_index = 1
			lds_source_tx_log.tx_type = "CLONE ACCOUNT CREATED ON NETWORK" # SHORT WORD(S) FOR WHAT TRANSACTION DID
			lds_source_tx_log.description = "A clone account was created for you." 
			lds_source_tx_log.memo = "Account Opened"
			lds_source_tx_log.category = "MRTX2"
			lds_source_tx_log.amount = 0
			lds_source_tx_log.user_id_created = source_user.user_id
			lds_source_tx_log.network_id = network_id
			lds_source_tx_log.account_id = lds_cursor.current_index
			lds_source_tx_log.source_account = lds_cursor.current_index
			lds_source_tx_log.target_account = lds_source_metric.account_id
			lds_source_tx_log.put()

			# save the transaction
			check_default(source_user)
			source_user.put()
			lds_new_metric_account.put()
			lds_cursor.put()

			self.PARENT.RETURN_CODE = "7037" # success: Clone account successfully created.

			return True
			
		else:
			self.PARENT.RETURN_CODE = "1205"
			return False # error transaction type not recognized		
	
	def _reserve_open(self,fstr_network_name):
	
		# we don't want/need to get the network conversion rate inside a transaction.
		network = self._get_network(fstr_network_name)
		if network is None: return False # pass up error code
		return self._reserve_open_transactional(network.network_id)
	
	@ndb.transactional(xg=True)
	def _reserve_open_transactional(self,fint_network_id):

		def check_default(fobj_user):
		
			# Check default is just making sure a default account exists
			# when a user adds or deletes accounts.  They may delete the
			# default, or they may add a second account without designating
			# a default.  This makes sure they always have a default if 
			# there is more than one account for them in that network and
			# the system needs to pick one for a function where the user
			# doesn't specifically designate manually.  For instance, a 
			# "search and pay" after deleting 1 of 3 accounts in a network
			# which happens to be the default.
		
			checker = {}
			# first loop set sets checker to True from default of False
			# if a default account is found.
			for i in range(len(fobj_user.reserve_network_ids)):
				if not fobj_user.reserve_network_ids[i] in checker:
					# add the network id as a key to our checker if it doesn't exist
					checker[fobj_user.reserve_network_ids[i]] = fobj_user.reserve_default[i]
				if fobj_user.reserve_default[i]: checker[fobj_user.reserve_network_ids[i]] = True
				
			for i in range(len(fobj_user.client_network_ids)):
				if not fobj_user.client_network_ids[i] in checker:
					# add the network id as a key to our checker if it doesn't exist
					checker[fobj_user.client_network_ids[i]] = fobj_user.client_default[i]
				if fobj_user.client_default[i]: checker[fobj_user.client_network_ids[i]] = True
				
			for i in range(len(fobj_user.joint_network_ids)):
				if not fobj_user.joint_network_ids[i] in checker:
					# add the network id as a key to our checker if it doesn't exist
					checker[fobj_user.joint_network_ids[i]] = fobj_user.joint_default[i]
				if fobj_user.joint_default[i]: checker[fobj_user.joint_network_ids[i]] = True
				
			for i in range(len(fobj_user.clone_network_ids)):
				if not fobj_user.clone_network_ids[i] in checker:
					# add the network id as a key to our checker if it doesn't exist
					checker[fobj_user.clone_network_ids[i]] = fobj_user.clone_default[i]
				if fobj_user.clone_default[i]: checker[fobj_user.clone_network_ids[i]] = True

			# second loop says, if the checker for that network id is False
			# set the checker for that network id and the default value on
			# that account to True.
			for i in range(len(fobj_user.reserve_network_ids)):
				if checker[fobj_user.reserve_network_ids[i]] == False:
					checker[fobj_user.reserve_network_ids[i]] = True
					fobj_user.reserve_default[i] = True
					
			for i in range(len(fobj_user.client_network_ids)):
				if checker[fobj_user.client_network_ids[i]] == False:
					checker[fobj_user.client_network_ids[i]] = True
					fobj_user.client_default[i] = True

			for i in range(len(fobj_user.joint_network_ids)):
				if checker[fobj_user.joint_network_ids[i]] == False:
					checker[fobj_user.joint_network_ids[i]] = True
					fobj_user.joint_default[i] = True

			for i in range(len(fobj_user.clone_network_ids)):
				if checker[fobj_user.clone_network_ids[i]] == False:
					checker[fobj_user.clone_network_ids[i]] = True
					fobj_user.clone_default[i] = True

		# A user can create a reserve account if:
		# 1. They are not already a member.
		# 2. They haven't reached there maximum number of accounts.
		# 
		# Fewer restrictions on reserve accounts as opposed to other
		# types as they are not dependent on any other account.

		validation_result = self._name_validate_transactional(None,None,None,fint_network_id)
		if not validation_result:
			# pass up error
			return False
		
		network_id = validation_result[0]

		# load user transactionally
		user_key = ndb.Key("ds_mr_user",self.PARENT.user.entity.user_id)
		lds_user = user_key.get()		
		
		if network_id in lds_user.reserve_network_ids:
			# already have a reserve account on this network
			self.PARENT.RETURN_CODE = "1112"
			return False
		
		if not lds_user.total_reserve_accounts < 30:
			# maximum reserve accounts reached
			self.PARENT.RETURN_CODE = "1111"
			return False
		
		
		# load cursor transactionally
		cursor_key = ndb.Key("ds_mr_network_cursor", "%s" % str(network_id).zfill(8))		
		lds_cursor = cursor_key.get()
		lds_cursor.current_index += 1
		
		# get a label for this account
		# STUB try/catch exception in case alias loop fail
		label = self._get_account_label(network_id,lds_cursor.current_index)
	
		# create a new metric account with key equal to current cursor/index for this network
		metric_account_key = ndb.Key("ds_mr_metric_account","%s%s" % (str(network_id).zfill(8),str(lds_cursor.current_index).zfill(12)))
		
		lds_metric_account = ds_mr_metric_account()
		lds_metric_account.network_id = network_id
		lds_metric_account.account_id = lds_cursor.current_index
		lds_metric_account.user_id = lds_user.user_id
		# creating the account is our first transaction
		lds_metric_account.tx_index = 1
		lds_metric_account.account_status = "ACTIVE"		
		lds_metric_account.account_type = "RESERVE"
		
		# mutable defaults
		lds_metric_account.outgoing_connection_requests = []
		lds_metric_account.incoming_connection_requests = []
		lds_metric_account.incoming_reserve_transfer_requests = {}
		lds_metric_account.outgoing_reserve_transfer_requests = {}
		lds_metric_account.suggested_inactive_incoming_reserve_transfer_requests = {}
		lds_metric_account.suggested_inactive_outgoing_reserve_transfer_requests = {}
		lds_metric_account.suggested_active_incoming_reserve_transfer_requests = {}
		lds_metric_account.suggested_active_outgoing_reserve_transfer_requests = {}
		lds_metric_account.current_connections = []
		lds_metric_account.last_connections = []
		
		lds_metric_account.key = metric_account_key
		
		# update the user object
		lds_user.total_reserve_accounts += 1

		lds_user.reserve_network_ids.append(network_id)
		lds_user.reserve_account_ids.append(lds_cursor.current_index)
		lds_user.reserve_labels.append(label)
		lds_user.reserve_default.append(False)
		
		# transaction log
		tx_log_key = ndb.Key("ds_mr_tx_log", "MRTX2%s%s%s" % (str(network_id).zfill(8),str(lds_cursor.current_index).zfill(12),str(1).zfill(12)))
		lds_tx_log = ds_mr_tx_log()
		lds_tx_log.key = tx_log_key
		lds_tx_log.tx_index = 1
		lds_tx_log.tx_type = "JOINED NETWORK" # SHORT WORD(S) FOR WHAT TRANSACTION DID
		lds_tx_log.description = "A user joined a network." 
		lds_tx_log.memo = "Account Opened"
		lds_tx_log.category = "MRTX2"
		lds_tx_log.amount = 0
		lds_tx_log.user_id_created = lds_user.user_id
		lds_tx_log.network_id = network_id
		lds_tx_log.account_id = lds_cursor.current_index
		lds_tx_log.source_account = lds_cursor.current_index 
		lds_tx_log.put()
		
		# save the transaction
		check_default(lds_user)
		lds_user.put()
		lds_metric_account.put()
		lds_cursor.put()
		
		return True
	
	@ndb.transactional(xg=True)
	def _name_validate_transactional(self,fstr_network_name=None,fstr_source_name=None,fstr_target_name=None,fint_network_id=None):
	
		# return network id, and source/target id associated with that network transactionally.
		
		# STUB After modifying this to work for not just reserve accounts realized I'm storing account
		# and network id for aliases in the name entity itself.  Ugh.  Maybe, change later to cut down 
		# unnecessary looping.  Could've done it easier.
		
		##########
		# GET NETWORK INFO FIRST
		##########
		
		if fint_network_id is None:
			# transactionally get the name/users to get to the network/account ids
			network_name_key = ndb.Key("ds_mr_unique_dummy_entity", fstr_network_name)
			network_name_entity = network_name_key.get()
			if network_name_entity is None:
				self.PARENT.RETURN_CODE = "1113"
				return False # network name invalid

			network_id = network_name_entity.network_id
		else:
			network_id = fint_network_id
		
		##########
		# GET SOURCE INFO IF REQUESTED
		##########
		
		if fstr_source_name is None:
			source_account_id = 0
			lds_source_user = None
		else:		
			source_account_id = 0
			source_name_key = ndb.Key("ds_mr_unique_dummy_entity", fstr_source_name)
			source_name_entity = source_name_key.get()
			if source_name_entity is None:
				self.PARENT.RETURN_CODE = "1114"
				return False # source name invalid
			# Before we get the metric accounts, we need to get the user objects
			# and verify that the requesting user is in fact the source account
			# specified and that both source and target exist on the network 
			# specified.
			if not self.PARENT.user.entity.user_id == source_name_entity.user_id:
				self.PARENT.RETURN_CODE = "1115"
				return False # source account must be current logged in user
			
			# load users transactionally
			source_user_key = ndb.Key("ds_mr_user",source_name_entity.user_id)
			lds_source_user = source_user_key.get()
			# We are looking for a match on network_id AND the name passed in.
			# We want this to work for all account types, so we have to loop
			# since we may have more than one occurrence of network_id in an
			# account sequence (like joint/client/clone).  We don't care about
			# the type as that will be known when calling function queries the
			# metric account itself.
			
			for i in range(len(lds_source_user.reserve_network_ids)):
				if lds_source_user.reserve_network_ids[i] == network_id:
					if lds_source_user.reserve_labels[i] == fstr_source_name:
						source_account_id = lds_source_user.reserve_account_ids[i]
						break
			# keep looking if we haven't found
			if source_account_id == 0:
				for i in range(len(lds_source_user.client_network_ids)):
					if lds_source_user.client_network_ids[i] == network_id:
						if lds_source_user.client_labels[i] == fstr_source_name:
							source_account_id = lds_source_user.client_account_ids[i]
							break			
			# keep looking if we haven't found
			if source_account_id == 0:
				for i in range(len(lds_source_user.joint_network_ids)):
					if lds_source_user.joint_network_ids[i] == network_id:
						if lds_source_user.joint_labels[i] == fstr_source_name:
							source_account_id = lds_source_user.joint_account_ids[i]
							break
			# keep looking if we haven't found
			if source_account_id == 0:
				for i in range(len(lds_source_user.clone_network_ids)):
					if lds_source_user.clone_network_ids[i] == network_id:
						if lds_source_user.clone_labels[i] == fstr_source_name:
							source_account_id = lds_source_user.clone_account_ids[i]
							break
			# keep looking if we haven't found
			if source_account_id == 0:
				for i in range(len(lds_source_user.child_client_network_ids)):
					if lds_source_user.child_client_network_ids[i] == network_id:
						if lds_source_user.child_client_labels[i] == fstr_source_name:
							source_account_id = lds_source_user.child_client_account_ids[i]
							break
			# keep looking if we haven't found
			if source_account_id == 0:
				for i in range(len(lds_source_user.child_joint_network_ids)):
					if lds_source_user.child_joint_network_ids[i] == network_id:
						if lds_source_user.child_joint_labels[i] == fstr_source_name:
							source_account_id = lds_source_user.child_joint_account_ids[i]
							break		
			
			if source_account_id == 0:
				self.PARENT.RETURN_CODE = "1116"
				return False # source user has no account on the named network

		##########
		# GET TARGET INFO IF REQUESTED
		##########
		
		if fstr_target_name is None:
			target_account_id = 0
			lds_target_user = None
		else:
			target_account_id = 0
			target_name_key = ndb.Key("ds_mr_unique_dummy_entity", fstr_target_name)
			target_name_entity = target_name_key.get()
			if target_name_entity is None:
				self.PARENT.RETURN_CODE = "1119"
				return False # target name invalid	
				
			# load user transactionally
			target_user_key = ndb.Key("ds_mr_user",target_name_entity.user_id)
			lds_target_user = target_user_key.get()
			# We are looking for a match on network_id AND the name passed in.
			# We want this to work for all account types, so we have to loop
			# since we may have more than one occurrence of network_id in an
			# account sequence (like joint/client/clone).  We don't care about
			# the type as that will be known when calling function queries the
			# metric account itself.
			# DEBUG
			# pdb.set_trace()			
			for i in range(len(lds_target_user.reserve_network_ids)):
				if lds_target_user.reserve_network_ids[i] == network_id:
					if lds_target_user.reserve_labels[i] == fstr_target_name:
						target_account_id = lds_target_user.reserve_account_ids[i]
						break
			# keep looking if we haven't found
			if target_account_id == 0:
				for i in range(len(lds_target_user.client_network_ids)):
					if lds_target_user.client_network_ids[i] == network_id:
						if lds_target_user.client_labels[i] == fstr_target_name:
							target_account_id = lds_target_user.client_account_ids[i]
							break			
			# keep looking if we haven't found
			if target_account_id == 0:
				for i in range(len(lds_target_user.joint_network_ids)):
					if lds_target_user.joint_network_ids[i] == network_id:
						if lds_target_user.joint_labels[i] == fstr_target_name:
							target_account_id = lds_target_user.joint_account_ids[i]
							break
			# keep looking if we haven't found
			if target_account_id == 0:
				for i in range(len(lds_target_user.clone_network_ids)):
					if lds_target_user.clone_network_ids[i] == network_id:
						if lds_target_user.clone_labels[i] == fstr_target_name:
							target_account_id = lds_target_user.clone_account_ids[i]
							break
			# keep looking if we haven't found
			if target_account_id == 0:
				for i in range(len(lds_target_user.child_client_network_ids)):
					if lds_target_user.child_client_network_ids[i] == network_id:
						if lds_target_user.child_client_labels[i] == fstr_target_name:
							target_account_id = lds_target_user.child_client_account_ids[i]
							break
			# keep looking if we haven't found
			if target_account_id == 0:
				for i in range(len(lds_target_user.child_joint_network_ids)):
					if lds_target_user.child_joint_network_ids[i] == network_id:
						if lds_target_user.child_joint_labels[i] == fstr_target_name:
							target_account_id = lds_target_user.child_joint_account_ids[i]
							break		
			
			if target_account_id == 0:
				self.PARENT.RETURN_CODE = "1120"
				return False # target user has no account on the named network


		# Should be good to go if we got this far.  It means the 
		# source/target username/alias's used, have a metric reserve
		# account on the network that the network name passed maps
		# to.
			
		return (network_id,source_account_id,target_account_id,lds_source_user,lds_target_user)
		
	def _connect(self,fstr_network_name,fstr_source_name,fstr_target_name):
	
		# we don't want/need to get the network conversion rate inside a transaction.
		network = self._get_network(fstr_network_name)
		if network is None: return False # pass up error code
		return self._connect_transactional(network.network_id,fstr_source_name,fstr_target_name)
	
	@ndb.transactional(xg=True)
	def _connect_transactional(self,fint_network_id,fstr_source_name,fstr_target_name):
		
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
		
		validation_result = self._name_validate_transactional(None,fstr_source_name,fstr_target_name,fint_network_id)
		if not validation_result:
			# pass up error
			return False
		
		network_id = validation_result[0]
		source_account_id = validation_result[1]
		target_account_id = validation_result[2]
				
		# transactionally get the source and target metric accounts
		key_part1 = str(network_id).zfill(8)
		key_part2 = str(source_account_id).zfill(12)
		source_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part2))
		lds_source = source_key.get()
		
		# error if source doesn't exist
		if lds_source is None:
			self.PARENT.RETURN_CODE = "1123"
			return False # error_source_id_not_valid
		# error if trying to connect to self
		if source_account_id == target_account_id: 
			self.PARENT.RETURN_CODE = "1124"
			return False # error_cant_connect_to_self
		# error if not a reserve account
		if not lds_source.account_type == "RESERVE" and not lds_source.account_status == "ACTIVE":
			self.PARENT.RETURN_CODE = "1125"
			return False # only active reserve accounts can connect, source is not
		
		key_part3 = str(target_account_id).zfill(12)
		target_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part3))
		lds_target = target_key.get()
		
		# error if target doesn't exist
		if lds_target is None:
			self.PARENT.RETURN_CODE = "1126"
			return False # error_target_id_not_valid
		# error if not a reserve account
		if not lds_target.account_type == "RESERVE" and not lds_target.account_status == "ACTIVE":
			self.PARENT.RETURN_CODE = "1127"
			return False # active reserve accounts can connect, target is not

		# Five situations where we don't even try to connect
		# 1. Source and target are already connected.
		if target_account_id in lds_source.current_connections:
			self.PARENT.RETURN_CODE = "1128"
			return False # return "error_already_connected"
		# 2. Source already has outgoing connection request to target
		if target_account_id in lds_source.outgoing_connection_requests:
			self.PARENT.RETURN_CODE = "1129"
			return False # error_connection_already_requested"
		# 3. Target incoming connection requests is maxed out
		if len(lds_target.incoming_connection_requests) > 19:
			self.PARENT.RETURN_CODE = "1130"
			return False # error_target_incoming_requests_maxed"
		# 4. Source outgoing connection requests is maxed out
		if len(lds_source.outgoing_connection_requests) > 19:
			self.PARENT.RETURN_CODE = "1131"
			return False # error_target_incoming_requests_maxed"
		# 5. Target or source has reached their maximum number of connections
		if len(lds_source.current_connections) > 19:
			self.PARENT.RETURN_CODE = "1132"
			return False # error_source_connections_maxed"
		if len(lds_target.current_connections) > 19:
			self.PARENT.RETURN_CODE = "1133"
			return False # error_target_connections_maxed"
		
		# should be ok to connect
		# check if the target has the source in it's outgoing connection requests
		if source_account_id in lds_target.outgoing_connection_requests:
			
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
				lds_source.current_connections.append(target_account_id)
				lds_source.incoming_connection_requests.remove(target_account_id)
				
			else:
			
				# last transaction was in previous time window, swap
				# a.k.a. move "old" current into "last" before overwriting
				lds_source.last_connections = lds_source.current_connections
				lds_source.last_reserve_balance = lds_source.current_reserve_balance
				lds_source.last_network_balance = lds_source.current_network_balance
				lds_source.current_connections.append(target_account_id)
				lds_source.incoming_connection_requests.remove(target_account_id)
				
	
			# update the target account
			if lds_target.current_timestamp > t_cutoff:
				
				# last transaction was in current time window, no need to swap
				# a.k.a. overwrite current
				lds_target.current_connections.append(source_account_id)
				lds_target.outgoing_connection_requests.remove(source_account_id)
				
			else:
			
				# last transaction was in previous time window, swap
				# a.k.a. move "old" current into "last" before overwriting
				lds_target.last_connections = lds_target.current_connections
				lds_target.last_reserve_balance = lds_target.current_reserve_balance
				lds_target.last_network_balance = lds_target.current_network_balance
				lds_target.current_connections.append(source_account_id)
				lds_target.outgoing_connection_requests.remove(source_account_id)
			
			# only update current_timestamp for graph dependent transactions??? STUB
			lstr_source_tx_type = "INCOMING CONNECTION AUTHORIZED"
			lstr_source_tx_description = "INCOMING CONNECTION AUTHORIZED"
			lstr_target_tx_type = "OUTGOING CONNECTION AUTHORIZED"
			lstr_target_tx_description = "OUTGOING CONNECTION AUTHORIZED"
			lds_source.current_timestamp = datetime.datetime.now()
			lds_target.current_timestamp = datetime.datetime.now()			
			self.PARENT.RETURN_CODE = "7009" # success_connection_request_authorized
			
			
		else:
			# target not yet connected, this is a connection request
			lstr_source_tx_type = "OUTGOING CONNECTION REQUEST"
			lstr_source_tx_description = "OUTGOING CONNECTION REQUEST"
			lstr_target_tx_type = "INCOMING CONNECTION REQUEST"
			lstr_target_tx_description = "INCOMING CONNECTION REQUEST"
			lds_source.outgoing_connection_requests.append(target_account_id)
			lds_target.incoming_connection_requests.append(source_account_id)
			self.PARENT.RETURN_CODE = "7010" # success_connection_request_completed
		
		
		# source transaction log
		source_lds_tx_log = ds_mr_tx_log()
		source_lds_tx_log.category = "MRTX" # GENERAL TRANSACTION GROUPING
		# tx_index should be based on incremented metric_account value
		source_lds_tx_log.tx_type = lstr_source_tx_type # SHORT WORD(S) FOR WHAT TRANSACTION DID
		source_lds_tx_log.access = "PRIVATE" # "PUBLIC" OR "PRIVATE"
		source_lds_tx_log.description = lstr_source_tx_description 
		source_lds_tx_log.user_id_created = lds_source.user_id
		source_lds_tx_log.network_id = network_id
		source_lds_tx_log.account_id = source_account_id
		source_lds_tx_log.source_account = source_account_id 
		source_lds_tx_log.target_account = target_account_id
		source_lds_tx_log.put()

		# target transaction log
		target_lds_tx_log = ds_mr_tx_log()
		# tx_index should be based on incremented metric_account value
		target_lds_tx_log.tx_type = lstr_target_tx_type # SHORT WORD(S) FOR WHAT TRANSACTION DID
		target_lds_tx_log.access = "PRIVATE" # "PUBLIC" OR "PRIVATE"
		target_lds_tx_log.description = lstr_target_tx_description 
		target_lds_tx_log.user_id_created = lds_source.user_id
		target_lds_tx_log.network_id = network_id
		target_lds_tx_log.account_id = target_account_id
		target_lds_tx_log.source_account = source_account_id 
		target_lds_tx_log.target_account = target_account_id
		target_lds_tx_log.put()
		
		lds_source.put()
		lds_target.put()
		return True	

	def _disconnect(self, fstr_network_name, fstr_source_name, fstr_target_name):
	
		# we don't want/need to get the network conversion rate inside a transaction.
		network = self._get_network(fstr_network_name)
		if network is None: return False # pass up error code
		return self._disconnect_transactional(network.network_id,fstr_source_name,fstr_target_name)

	@ndb.transactional(xg=True)
	def _disconnect_transactional(self, fint_network_id, fstr_source_name, fstr_target_name):

		# first get id's instead of names
		validation_result = self._name_validate_transactional(None,fstr_source_name,fstr_target_name,fint_network_id)
		if not validation_result:
			# pass up error
			return False
		
		network_id = validation_result[0]
		source_account_id = validation_result[1]
		target_account_id = validation_result[2]
		
		# transactionally get the source and target metric accounts
		key_part1 = str(network_id).zfill(8)
		key_part2 = str(source_account_id).zfill(12)
		key_part3 = str(target_account_id).zfill(12)
		source_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part2))
		lds_source = source_key.get()
		if lds_source is None:
			self.PARENT.RETURN_CODE = "1136"
			return False # error source id not valid
		target_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part3))
		lds_target = target_key.get()
		
		# error if target doesn't exist
		if lds_target is None:
			self.PARENT.RETURN_CODE = "1137"
			return False # error target id not valid
		
		# error if not a reserve account
		if not lds_source.account_type == "RESERVE" and not lds_source.account_status == "ACTIVE":
			self.PARENT.RETURN_CODE = "1145"
			return False # only active reserve accounts can disconnect, source is not

		# error if not a reserve account
		if not lds_target.account_type == "RESERVE" and not lds_target.account_status == "ACTIVE":
			self.PARENT.RETURN_CODE = "1146"
			return False # active reserve accounts can disconnect, target is not
		
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
		
		if target_account_id in lds_source.incoming_connection_requests:
		
			# benign change with respect to graph
			lds_source.incoming_connection_requests.remove(target_account_id)
			lds_target.outgoing_connection_requests.remove(source_account_id)
			lstr_source_tx_type = "INCOMING CONNECTION REQUEST DENIED"
			lstr_source_tx_description = "INCOMING CONNECTION REQUEST DENIED"
			lstr_target_tx_type = "OUTGOING CONNECTION REQUEST DENIED"
			lstr_target_tx_description = "OUTGOING CONNECTION REQUEST DENIED"
			
			self.PARENT.RETURN_CODE = "7012" # success denied target connection request
		
		elif target_account_id in lds_source.outgoing_connection_requests:
		
			# benign change with respect to graph
			lds_target.incoming_connection_requests.remove(source_account_id)
			lds_source.outgoing_connection_requests.remove(target_account_id)
			lstr_source_tx_type = "OUTGOING CONNECTION REQUEST WITHDRAWN"
			lstr_source_tx_description = "OUTGOING CONNECTION REQUEST WITHDRAWN"
			lstr_target_tx_type = "INCOMING CONNECTION REQUEST WITHDRAWN"
			lstr_target_tx_description = "INCOMING CONNECTION REQUEST WITHDRAWN"
			self.PARENT.RETURN_CODE = "7013" # success withdrew connection request
		
		elif target_account_id in lds_source.current_connections:
		
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
				lds_source.current_connections.remove(target_account_id)
				
			else:
			
				# last transaction was in previous time window, swap
				# a.k.a. move "old" current into "last" before overwriting
				lds_source.last_connections = lds_source.current_connections
				lds_source.last_reserve_balance = lds_source.current_reserve_balance
				lds_source.last_network_balance = lds_source.current_network_balance
				lds_source.current_connections.remove(target_account_id)				
	
			# update the target account
			if lds_target.current_timestamp > t_cutoff:
				
				# last transaction was in current time window, no need to swap
				# a.k.a. overwrite current
				lds_target.current_connections.remove(source_account_id)
				
			else:
			
				# last transaction was in previous time window, swap
				# a.k.a. move "old" current into "last" before overwriting
				lds_target.last_connections = lds_target.current_connections
				lds_target.last_reserve_balance = lds_target.current_reserve_balance
				lds_target.last_network_balance = lds_target.current_network_balance
				lds_target.current_connections.remove(source_account_id)
				
			# only update current_timestamp for graph dependent transactions??? STUB
			lds_source.current_timestamp = datetime.datetime.now()
			lds_target.current_timestamp = datetime.datetime.now()
			lstr_source_tx_type = "DISCONNECTION BY THIS ACCOUNT"
			lstr_source_tx_description = "DISCONNECTION BY THIS ACCOUNT"
			lstr_target_tx_type = "DISCONNECTION BY OTHER ACCOUNT"
			lstr_target_tx_description = "DISCONNECTION BY OTHER ACCOUNT"
			self.PARENT.RETURN_CODE = "7014" # success cancelled connection
			
		else:
			self.PARENT.RETURN_CODE = "1138"
			return False # error_nothing_to_disconnect

		# ADD TWO TRANSACTIONS LIKE CONNECT()
		# source transaction log
		source_lds_tx_log = ds_mr_tx_log()
		# tx_index should be based on incremented metric_account value
		source_lds_tx_log.tx_type = lstr_source_tx_type # SHORT WORD(S) FOR WHAT TRANSACTION DID
		source_lds_tx_log.access = "PRIVATE" # "PUBLIC" OR "PRIVATE"
		source_lds_tx_log.description = lstr_source_tx_description 
		source_lds_tx_log.user_id_created = lds_source.user_id
		source_lds_tx_log.network_id = network_id
		source_lds_tx_log.account_id = source_account_id
		source_lds_tx_log.source_account = source_account_id 
		source_lds_tx_log.target_account = target_account_id
		source_lds_tx_log.put()

		# target transaction log
		target_lds_tx_log = ds_mr_tx_log()
		# tx_index should be based on incremented metric_account value
		target_lds_tx_log.tx_type = lstr_target_tx_type # SHORT WORD(S) FOR WHAT TRANSACTION DID
		# typically we'll make target private for bilateral transactions so that
		# when looking at a system view, we don't see duplicates.
		target_lds_tx_log.access = "PRIVATE" # "PUBLIC" OR "PRIVATE"
		target_lds_tx_log.description = lstr_target_tx_description 
		target_lds_tx_log.user_id_created = lds_source.user_id
		target_lds_tx_log.network_id = network_id
		target_lds_tx_log.account_id = target_account_id
		target_lds_tx_log.source_account = source_account_id 
		target_lds_tx_log.target_account = target_account_id
		target_lds_tx_log.put()

		lds_source.put()
		lds_target.put()
		return True

	def _modify_reserve(self,fstr_network_name,fstr_source_name,fstr_type,fstr_amount):
	
		# we don't want/need to get the network conversion rate inside a transaction.
		network = self._get_network(fstr_network_name)
		if network is None: return False # pass up error code
		return self._modify_reserve_transactional(network.network_id,fstr_source_name,fstr_type,fstr_amount,network.skintillionths)

	@ndb.transactional(xg=True)
	def _modify_reserve_transactional(self,fint_network_id,fstr_source_name,fstr_type,fstr_amount,fint_conversion):

		# first get id's instead of names
		validation_result = self._name_validate_transactional(None,fstr_source_name,None,fint_network_id)
		if not validation_result:
			# pass up error
			return False
		
		network_id = validation_result[0]
		source_account_id = validation_result[1]		
		
		# First, get the source account.
		key_part1 = str(network_id).zfill(8)
		key_part2 = str(source_account_id).zfill(12)
		source_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part2))
		lds_source = source_key.get()
		
		# error if source doesn't exist
		if lds_source is None:
			self.PARENT.RETURN_CODE = "1139"
			return False # error source id not valid"
		
		# error if not a reserve account
		if not lds_source.account_type == "RESERVE" and not lds_source.account_status == "ACTIVE":
			self.PARENT.RETURN_CODE = "1147"
			return False # only active reserve accounts can disconnect, source is not
		
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
			lint_amount = int(float(fstr_amount)*fint_conversion)
		except ValueError, ex:
			self.PARENT.RETURN_CODE = "1140"
			return False # error_invalid_amount_passed"
		
		# make sure amount isn't over the maximum
		if lint_amount > MAX_RESERVE_MODIFY:
			self.PARENT.RETURN_CODE = "1141"
			return False # error_amount_exceeds_maximum_allowed"
		
		# if we don't modify one or the other, "new" will be previous
		lint_new_balance = lds_source.current_network_balance
		lint_new_reserve = lds_source.current_reserve_balance		
		
		# 4 types of reserve modifications are possible
		if fstr_type == "add":		
		
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
			
			lstr_source_tx_type = "RESERVE ADD"
			lstr_source_tx_description = "Res Add"
			self.PARENT.RETURN_CODE = "7015" # success_reserve_normal_add

		elif fstr_type == "subtract":
		
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
			
			lstr_source_tx_type = "RESERVE SUBTRACT"
			lstr_source_tx_description = "Res Sub"
			self.PARENT.RETURN_CODE = "7016" # success_reserve_normal_subtract
			
		elif fstr_type == "create":

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
			
			lstr_source_tx_type = "RESERVE OVERRIDE ADD"
			lstr_source_tx_description = "Res OVR Add"
			self.PARENT.RETURN_CODE = "7017" # success_reserve_override_add
			
		elif fstr_type == "destroy":
		
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
			
			lstr_source_tx_type = "RESERVE OVERRIDE SUBTRACT"
			lstr_source_tx_description = "Res OVR Sub"
			self.PARENT.RETURN_CODE = "7018" # success_reserve_override_subtract
			
		else:
			self.PARENT.RETURN_CODE = "1117"
			return False # error_invalid_transaction_type
		
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
		tx_log_key = ndb.Key("ds_mr_tx_log", "MRTX2%s%s%s" % (key_part1, key_part2,str(lds_source.tx_index).zfill(12)))
		lds_tx_log = ds_mr_tx_log()
		lds_tx_log.key = tx_log_key
		# tx_index should be based on incremented metric_account value
		lds_tx_log.tx_index = lds_source.tx_index
		lds_tx_log.tx_type = lstr_source_tx_type # SHORT WORD(S) FOR WHAT TRANSACTION DID
		lds_tx_log.amount = lint_amount
		lds_tx_log.current_network_balance = lds_source.current_network_balance
		lds_tx_log.current_reserve_balance = lds_source.current_reserve_balance
		lds_tx_log.access = "PRIVATE" # "PUBLIC" OR "PRIVATE"
		lds_tx_log.description = lstr_source_tx_description 
		lds_tx_log.memo = lstr_source_tx_description 
		lds_tx_log.category = "MRTX2"
		lds_tx_log.user_id_created = lds_source.user_id
		lds_tx_log.network_id = network_id
		lds_tx_log.account_id = source_account_id
		lds_tx_log.source_account = source_account_id 
		lds_tx_log.target_account = 0
		lds_tx_log.put()
		
		# only update current_timestamp for graph dependent transactions??? STUB
		lds_source.current_timestamp = datetime.datetime.now()
		lds_source.put()
		return True

	def _make_payment(self,fstr_network_name,fstr_source_name,fstr_target_name,fstr_amount):
	
		# we don't want/need to get the network conversion rate inside a transaction.
		network = self._get_network(fstr_network_name)
		if network is None: return False # pass up error code
		return self._make_payment_transactional(network.network_id,fstr_source_name,fstr_target_name,fstr_amount,network.skintillionths)

	@ndb.transactional(xg=True)
	def _make_payment_transactional(self,fint_network_id,fstr_source_name,fstr_target_name,fstr_amount,fint_conversion):

		# first get id's instead of names
		validation_result = self._name_validate_transactional(None,fstr_source_name,fstr_target_name,fint_network_id)
		if not validation_result:
			# pass up error
			return False
		
		network_id = validation_result[0]
		source_account_id = validation_result[1]		
		target_account_id = validation_result[2]		
		
		# make a payment
		# transfer network balance from one user to another
		# this does not affect our global balance counters
				
		# get the source and target metric accounts
		
		key_part1 = str(network_id).zfill(8)
		key_part2 = str(source_account_id).zfill(12)
		key_part3 = str(target_account_id).zfill(12)
		source_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part2))
		lds_source = source_key.get()
		
		# error if source doesn't exist
		if lds_source is None:
			self.PARENT.RETURN_CODE = "1118"
			return False # error_source_id_not_valid
		# error if trying to connect to self
		if source_account_id == target_account_id:
			self.PARENT.RETURN_CODE = "1121"
			return False # error_cant_pay_self
		
		target_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part3))
		lds_target = target_key.get()
		
		# error if target doesn't exist
		if lds_target is None:
			self.PARENT.RETURN_CODE = "1122"
			return False # error_target_id_not_valid
		
		# make sure fstr_amount actually is an integer
		try:
			lint_amount = int(float(fstr_amount)*fint_conversion)
		except ValueError, ex:
			self.PARENT.RETURN_CODE = "1142"
			return False # error_invalid_amount_passed
		
		# can't exceed maximum allowed payment
		if lint_amount > MAX_PAYMENT:
			self.PARENT.RETURN_CODE = "1143"
			return False # error_amount_exceeds_maximum_allowed

		# STUB make sure all lint_amount inputs are greater than 0
		# can't pay if you don't have that much
		if lds_source.current_network_balance < lint_amount:
			self.PARENT.RETURN_CODE = "1144"
			return False # error_not_enough_balance_to_make_payment
		
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
		source_tx_log_key = ndb.Key("ds_mr_tx_log", "MRTX2%s%s%s" % (key_part1, key_part2,str(lds_source.tx_index).zfill(12)))
		source_lds_tx_log = ds_mr_tx_log()
		source_lds_tx_log.key = source_tx_log_key
		# tx_index should be based on incremented metric_account value
		source_lds_tx_log.tx_index = lds_source.tx_index
		source_lds_tx_log.tx_type = "PAYMENT MADE" # SHORT WORD(S) FOR WHAT TRANSACTION DID
		source_lds_tx_log.memo = "Pay to %s" % fstr_target_name		
		source_lds_tx_log.category = "MRTX2"
		source_lds_tx_log.amount = lint_amount
		source_lds_tx_log.current_network_balance = lds_source.current_network_balance
		source_lds_tx_log.current_reserve_balance = lds_source.current_reserve_balance
		source_lds_tx_log.access = "PUBLIC" # "PUBLIC" OR "PRIVATE"
		source_lds_tx_log.description = "PAYMENT MADE" 
		source_lds_tx_log.user_id_created = lds_source.user_id
		source_lds_tx_log.network_id = network_id
		source_lds_tx_log.account_id = source_account_id
		source_lds_tx_log.source_account = source_account_id 
		source_lds_tx_log.target_account = target_account_id
		source_lds_tx_log.put()

		lds_target.tx_index += 1
		# target transaction log
		target_tx_log_key = ndb.Key("ds_mr_tx_log", "MRTX2%s%s%s" % (key_part1, key_part3,str(lds_target.tx_index).zfill(12)))
		target_lds_tx_log = ds_mr_tx_log()
		target_lds_tx_log.key = target_tx_log_key
		# tx_index should be based on incremented metric_account value
		target_lds_tx_log.tx_index = lds_target.tx_index
		target_lds_tx_log.tx_type = "PAYMENT RECEIVED" # SHORT WORD(S) FOR WHAT TRANSACTION DID
		target_lds_tx_log.memo = "Paid by %s" % fstr_source_name		
		target_lds_tx_log.category = "MRTX2"
		target_lds_tx_log.amount = lint_amount
		target_lds_tx_log.current_network_balance = lds_target.current_network_balance
		target_lds_tx_log.current_reserve_balance = lds_target.current_reserve_balance
		# typically we'll make target private for bilateral transactions so that
		# when looking at a system view, we don't see duplicates.
		target_lds_tx_log.access = "PRIVATE" # "PUBLIC" OR "PRIVATE"
		target_lds_tx_log.description = "PAYMENT RECEIVED" 
		target_lds_tx_log.user_id_created = lds_source.user_id
		target_lds_tx_log.network_id = network_id
		target_lds_tx_log.account_id = target_account_id
		target_lds_tx_log.source_account = source_account_id 
		target_lds_tx_log.target_account = target_account_id
		target_lds_tx_log.put()
		
		lds_source.put()
		lds_target.put()
		self.PARENT.RETURN_CODE = "7019" # success_payment_succeeded
		return True

	def _process_reserve_transfer(self,fstr_network_name,fstr_source_name,fstr_target_name,fstr_amount,fstr_type):
	
		# we don't want/need to get the network conversion rate inside a transaction.
		network = self._get_network(fstr_network_name)
		if network is None: return False # pass up error code
		return self._process_reserve_transfer_transactional(network.network_id,fstr_source_name,fstr_target_name,fstr_amount,fstr_type,network.skintillionths)

	@ndb.transactional(xg=True)
	def _process_reserve_transfer_transactional(self,fint_network_id,fstr_source_name,fstr_target_name,fstr_amount,fstr_type,fint_conversion):

		# first get id's instead of names
		validation_result = self._name_validate_transactional(None,fstr_source_name,fstr_target_name,fint_network_id)
		if not validation_result:
			# pass up error
			return False
		
		network_id = validation_result[0]
		source_account_id = validation_result[1]		
		target_account_id = validation_result[2]	

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
		
		key_part1 = str(network_id).zfill(8)
		key_part2 = str(source_account_id).zfill(12)
		key_part3 = str(target_account_id).zfill(12)
		source_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part2))
		lds_source = source_key.get()
		
		# error if source doesn't exist
		if lds_source is None:
			self.PARENT.RETURN_CODE = "1150"
			return False # error_source_id_not_valid
		# error if trying to write check to self
		if source_account_id == target_account_id:
			self.PARENT.RETURN_CODE = "1151"
			return False # error_source_and_target_ids_cannot_be_the_same
		
		target_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part3))
		lds_target = target_key.get()
		
		# error if target doesn't exist
		if lds_target is None:
			self.PARENT.RETURN_CODE = "1152"
			return False # error_target_id_not_valid
		
		# error if not a reserve account
		if not lds_source.account_type == "RESERVE" and not lds_source.account_status == "ACTIVE":
			self.PARENT.RETURN_CODE = "1148"
			return False # only active reserve accounts can disconnect, source is not

		# error if not a reserve account
		if not lds_target.account_type == "RESERVE" and not lds_target.account_status == "ACTIVE":
			self.PARENT.RETURN_CODE = "1149"
			return False # active reserve accounts can disconnect, target is not

		# make sure fstr_amount actually is an integer
		try:
			lint_amount = int(float(fstr_amount)*fint_conversion)
		except ValueError, ex:
			self.PARENT.RETURN_CODE = "1153"
			return False # error_invalid_amount_passed
			
		if not target_account_id in lds_source.current_connections:
			self.PARENT.RETURN_CODE = "1154"
			return False # error_source_and_target_not_connected
		
		# We don't do a lot of checks on the requesting a transfer side, because graph state changes, and users may
		# be writing transfer requests in anticipation of balance updates.  So we only do the main checks when we
		# actually try to authorize a reserve transfer.
		
		if fstr_type == "storing_suggested":		
			
			# This is a new suggestion from the graph process.  If any previous exist 
			# that are in the inactive queue, delete them.
			lds_source.suggested_inactive_incoming_reserve_transfer_requests.pop(target_account_id,None)
			lds_source.suggested_inactive_outgoing_reserve_transfer_requests.pop(target_account_id,None)
			lds_target.suggested_inactive_incoming_reserve_transfer_requests.pop(source_account_id,None)
			lds_target.suggested_inactive_outgoing_reserve_transfer_requests.pop(source_account_id,None)
			# create new request
			lds_source.suggested_inactive_outgoing_reserve_transfer_requests[target_account_id] = lint_amount
			lds_target.suggested_inactive_incoming_reserve_transfer_requests[source_account_id] = lint_amount
			
			lstr_source_tx_type = "SUGGESTED OUTGOING RESERVE TRANSFER STORED"
			lstr_source_tx_description = "SUGGESTED OUTGOING RESERVE TRANSFER STORED"
			lstr_target_tx_type = "SUGGESTED INCOMING RESERVE TRANSFER STORED"
			lstr_target_tx_description = "SUGGESTED INCOMING RESERVE TRANSFER STORED"
			self.PARENT.RETURN_CODE = "7020" # success_suggested_reserve_transfer_stored

		elif fstr_type == "suggested request":
			
			# We're "activating" a suggested one.  So we move it to active queue.  This let's
			# the other party know that they can authorize it.  But it's the web, so need to
			# make sure that inactive request still exists
			if not target_account_id in lds_source.suggested_inactive_outgoing_reserve_transfer_requests:
				self.PARENT.RETURN_CODE = "1155"
				return False # error_activation_request_has_no_inactive_match_on_id
			# ...and has the same amount
			if not lint_amount == lds_source.suggested_inactive_outgoing_reserve_transfer_requests[target_account_id]:
				self.PARENT.RETURN_CODE = "1156"
				return False # error_activation_request_has_no_inactive_match_on_amount
			# before inactive can be moved to active, any old activated, suggested transfers must be
			# either cancelled or completed.  We don't automatically cancel an active one since it may
			# be in process.
			if target_account_id in lds_source.suggested_active_incoming_reserve_transfer_requests:
				self.PARENT.RETURN_CODE = "1157"
				return False # error_active_must_be_completed_or_cancelled_before_new_activation
			if target_account_id in lds_source.suggested_active_outgoing_reserve_transfer_requests:
				self.PARENT.RETURN_CODE = "1158"
				return False # error_active_must_be_completed_or_cancelled_before_new_activation
				
			# request is valid
			# move inactive to active, leaving inactive empty
			lds_source.suggested_inactive_incoming_reserve_transfer_requests.pop(target_account_id,None)
			lds_source.suggested_inactive_outgoing_reserve_transfer_requests.pop(target_account_id,None)
			lds_target.suggested_inactive_incoming_reserve_transfer_requests.pop(source_account_id,None)
			lds_target.suggested_inactive_outgoing_reserve_transfer_requests.pop(source_account_id,None)
			# create new request
			lds_source.suggested_active_outgoing_reserve_transfer_requests[target_account_id] = lint_amount
			lds_target.suggested_active_incoming_reserve_transfer_requests[source_account_id] = lint_amount
			
			lstr_source_tx_type = "SUGGESTED OUTGOING RESERVE TRANSFER ACTIVATED"
			lstr_source_tx_description = "SUGGESTED OUTGOING RESERVE TRANSFER ACTIVATED"
			lstr_target_tx_type = "SUGGESTED INCOMING RESERVE TRANSFER ACTIVATED"
			lstr_target_tx_description = "SUGGESTED INCOMING RESERVE TRANSFER ACTIVATED"
			self.PARENT.RETURN_CODE = "7021" # success_suggested_reserve_transfer_activated
			
		elif fstr_type == "suggested cancel" or fstr_type == "suggested deny":
		
			# This is similar to a "disconnect()".  Once a suggested transfer is active, either
			# party to it, can deny/withdraw it.  The special case here, is that if the inactive
			# suggested slot is empty, we move this one back to it.  If not, we simply delete it
			# as the system has already suggested a new one.
			
			# source is always the one doing the action, let's see which situation we're in first
			if target_account_id in lds_source.suggested_active_outgoing_reserve_transfer_requests:
				
				# we are deactiving our own activation
				# verify amount
				if not lint_amount == lds_source.suggested_active_outgoing_reserve_transfer_requests[target_account_id]:
					self.PARENT.RETURN_CODE = "1159"
					return False # error_deactivation_request_has_no_active_match_on_amount"
				# if inactive slot is empty, we move before deleting otherwise just delete
				if not target_account_id in lds_source.suggested_inactive_outgoing_reserve_transfer_requests:
					if not target_account_id in lds_source.suggested_inactive_incoming_reserve_transfer_requests:
						# ok to copy back to inactive
						lds_source.suggested_inactive_outgoing_reserve_transfer_requests[target_account_id] = lint_amount
						lds_target.suggested_inactive_incoming_reserve_transfer_requests[source_account_id] = lint_amount
				# delete the suggested active entries
				lds_source.suggested_active_outgoing_reserve_transfer_requests.pop(target_account_id,None)
				lds_target.suggested_active_incoming_reserve_transfer_requests.pop(source_account_id,None)
				
				lstr_source_tx_type = "SUGGESTED OUTGOING RESERVE TRANSFER DEACTIVATED"
				lstr_source_tx_description = "SUGGESTED OUTGOING RESERVE TRANSFER DEACTIVATED"
				lstr_target_tx_type = "SUGGESTED INCOMING RESERVE TRANSFER DEACTIVATED"
				lstr_target_tx_description = "SUGGESTED INCOMING RESERVE TRANSFER DEACTIVATED"
				self.PARENT.RETURN_CODE = "7022" # success_suggested_reserve_transfer_deactivated
			
			elif target_account_id in lds_source.suggested_active_incoming_reserve_transfer_requests:
			
				# we are denying the targets activation
				# verify amount
				if not lint_amount == lds_source.suggested_active_incoming_reserve_transfer_requests[target_account_id]:
					self.PARENT.RETURN_CODE = "1160"
					return False # error_denial_request_has_no_active_match_on_amount
				# if inactive slot is empty, we move before deleting otherwise just delete
				if not target_account_id in lds_source.suggested_inactive_outgoing_reserve_transfer_requests:
					if not target_account_id in lds_source.suggested_inactive_incoming_reserve_transfer_requests:
						# ok to copy back to inactive
						lds_source.suggested_inactive_incoming_reserve_transfer_requests[target_account_id] = lint_amount
						lds_target.suggested_inactive_outgoing_reserve_transfer_requests[source_account_id] = lint_amount
				# delete the suggested active entries
				lds_source.suggested_active_incoming_reserve_transfer_requests.pop(target_account_id,None)
				lds_target.suggested_active_outgoing_reserve_transfer_requests.pop(source_account_id,None)
				
				lstr_source_tx_type = "SUGGESTED INCOMING RESERVE TRANSFER DENIED"
				lstr_source_tx_description = "SUGGESTED INCOMING RESERVE TRANSFER DENIED"
				lstr_target_tx_type = "SUGGESTED OUTGOING RESERVE TRANSFER DENIED"
				lstr_target_tx_description = "SUGGESTED OUTGOING RESERVE TRANSFER DENIED"
				self.PARENT.RETURN_CODE = "7023" # success_suggested_reserve_transfer_denied
			
			else:
				self.PARENT.RETURN_CODE = "1161"
				return False # error_no_suggested_active_request_between_source_and_target	
		
		elif fstr_type == "transfer request":
		
			# new outgoing transfer request from source
			# must complete or cancel old ones before making a new one
			if target_account_id in lds_source.incoming_reserve_transfer_requests:
				self.PARENT.RETURN_CODE = "1162"
				return False # error_existing_transfer_requests_must_be_completed_or_cancelled_before_creating_new_one
			if target_account_id in lds_source.outgoing_reserve_transfer_requests:
				self.PARENT.RETURN_CODE = "1163"
				return False # error_existing_transfer_requests_must_be_completed_or_cancelled_before_creating_new_one
			# create new request
			lds_source.outgoing_reserve_transfer_requests[target_account_id] = lint_amount
			lds_target.incoming_reserve_transfer_requests[source_account_id] = lint_amount
			
			lstr_source_tx_type = "USER OUTGOING RESERVE TRANSFER REQUESTED"
			lstr_source_tx_description = "USER OUTGOING RESERVE TRANSFER REQUESTED"
			lstr_target_tx_type = "USER INCOMING RESERVE TRANSFER REQUESTED"
			lstr_target_tx_description = "USER INCOMING RESERVE TRANSFER REQUESTED"
			self.PARENT.RETURN_CODE = "7024" # success_user_reserve_transfer_requested
			
		elif fstr_type == "transfer cancel":
			
			# creator of a transfer request is cancelling
			# verify source actually has an outgoing for correct amount and if so delete it
			if target_account_id in lds_source.outgoing_reserve_transfer_requests:
				if not lint_amount == lds_source.outgoing_reserve_transfer_requests[target_account_id]:
					self.PARENT.RETURN_CODE = "1164"
					return False # error_cancellation_request_does_not_match_outgoing_amount
			else:
				self.PARENT.RETURN_CODE = "1165"
				return False # error_cancel_request_does_not_have_match_in_outgoing_requests_for_source
			# delete the transfer request in question
			lds_source.outgoing_reserve_transfer_requests.pop(target_account_id,None)
			lds_target.incoming_reserve_transfer_requests.pop(source_account_id,None)
			
			lstr_source_tx_type = "USER OUTGOING RESERVE TRANSFER WITHDRAWN"
			lstr_source_tx_description = "USER OUTGOING RESERVE TRANSFER WITHDRAWN"
			lstr_target_tx_type = "USER INCOMING RESERVE TRANSFER WITHDRAWN"
			lstr_target_tx_description = "USER INCOMING RESERVE TRANSFER WITHDRAWN"
			self.PARENT.RETURN_CODE = "7025" # success_user_reserve_transfer_cancelled

		elif fstr_type == "transfer deny":
			
			# source is denying targets requested transfer
			# verify source actually has an incoming request for correct amount and if so delete it
			if target_account_id in lds_source.incoming_reserve_transfer_requests:
				if not lint_amount == lds_source.incoming_reserve_transfer_requests[target_account_id]:
					self.PARENT.RETURN_CODE = "1166"
					return False # error_cancellation_request_does_not_match_incoming_amount
			else:
				self.PARENT.RETURN_CODE = "1167"
				return False # error_cancel_request_does_not_have_match_in_incoming_requests_for_source
			# delete the transfer request in question
			lds_source.incoming_reserve_transfer_requests.pop(target_account_id,None)
			lds_target.outgoing_reserve_transfer_requests.pop(source_account_id,None)
			
			lstr_source_tx_type = "USER INCOMING RESERVE TRANSFER DENIED"
			lstr_source_tx_description = "USER INCOMING RESERVE TRANSFER DENIED"
			lstr_target_tx_type = "USER OUTGOING RESERVE TRANSFER DENIED"
			lstr_target_tx_description = "USER OUTGOING RESERVE TRANSFER DENIED"
			self.PARENT.RETURN_CODE = "7026" # success_user_reserve_transfer_denied
		
		elif fstr_type == "suggested authorize":

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
			if not target_account_id in lds_source.suggested_active_incoming_reserve_transfer_requests:
				self.PARENT.RETURN_CODE = "1168"
				return False # error_no_request_in_active_suggested_incoming_for_target
			# make sure it's the same amount
			if not lds_source.suggested_active_incoming_reserve_transfer_requests[target_account_id] == lint_amount:
				self.PARENT.RETURN_CODE = "1169"
				return False # error_authorization_amount_does_not_match_incoming_request
			# make sure target still has enough to pay
			if not lds_target.current_reserve_balance > lint_amount:
				self.PARENT.RETURN_CODE = "1170"
				return False # error_target_has_insufficient_reserves_for_transfer			
			
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
			lds_source.suggested_active_incoming_reserve_transfer_requests.pop(target_account_id,None)
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
			if not target_account_id in lds_source.suggested_inactive_outgoing_reserve_transfer_requests:
				if not target_account_id in lds_source.suggested_inactive_incoming_reserve_transfer_requests:
					# ok to copy back to inactive
					lds_source.suggested_inactive_incoming_reserve_transfer_requests[target_account_id] = lint_amount
					lds_target.suggested_inactive_outgoing_reserve_transfer_requests[source_account_id] = lint_amount
				
			# update the target account
			lds_target.suggested_active_outgoing_reserve_transfer_requests.pop(source_account_id,None)
			lds_target.current_reserve_balance -= lint_amount
			lds_target.current_timestamp = datetime.datetime.now()

			lstr_source_tx_type = "SUGGESTED INCOMING RESERVE TRANSFER AUTHORIZED"
			lstr_source_tx_description = "SUGGESTED INCOMING RESERVE TRANSFER AUTHORIZED"
			lstr_target_tx_type = "SUGGESTED OUTGOING RESERVE TRANSFER AUTHORIZED"
			lstr_target_tx_description = "SUGGESTED OUTGOING RESERVE TRANSFER AUTHORIZED"
			self.PARENT.RETURN_CODE = "7027" # success_suggested_reserve_transfer_authorized
			
		elif fstr_type == "transfer authorize":
		
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
			if not target_account_id in lds_source.incoming_reserve_transfer_requests:
				self.PARENT.RETURN_CODE = "1171"
				return False # error_no_request_in_incoming_for_target
			if not lds_source.incoming_reserve_transfer_requests[target_account_id] == lint_amount:
				self.PARENT.RETURN_CODE = "1172"
				return False # error_authorization_amount_does_not_match_incoming_request
			if not lds_target.current_reserve_balance > lint_amount:
				self.PARENT.RETURN_CODE = "1173"
				return False # error_target_has_insufficient_reserves_for_transfer			
			
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
			lds_source.incoming_reserve_transfer_requests.pop(target_account_id,None)
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
			lds_target.outgoing_reserve_transfer_requests.pop(source_account_id,None)
			lds_target.current_reserve_balance -= lint_amount
			lds_target.current_timestamp = datetime.datetime.now()

			lstr_source_tx_type = "USER INCOMING RESERVE TRANSFER AUTHORIZED"
			lstr_source_tx_description = "USER INCOMING RESERVE TRANSFER AUTHORIZED"
			lstr_target_tx_type = "USER OUTGOING RESERVE TRANSFER AUTHORIZED"
			lstr_target_tx_description = "USER OUTGOING RESERVE TRANSFER AUTHORIZED"
			self.PARENT.RETURN_CODE = "7028" # success_user_reserve_transfer_authorized

		else:
			self.PARENT.RETURN_CODE = "1174"
			return False # error_transaction_type_invalid
			
		if fstr_type == "suggested authorize" or fstr_type == "transfer authorize":
			
			# a payment related transaction
			
			lds_source.tx_index += 1
			# source transaction log
			source_tx_log_key = ndb.Key("ds_mr_tx_log", "MRTX2%s%s%s" % (key_part1, key_part2,str(lds_source.tx_index).zfill(12)))
			source_lds_tx_log = ds_mr_tx_log()
			source_lds_tx_log.key = source_tx_log_key
			# tx_index should be based on incremented metric_account value
			source_lds_tx_log.tx_index = lds_source.tx_index
			source_lds_tx_log.tx_type = lstr_source_tx_type # SHORT WORD(S) FOR WHAT TRANSACTION DID
			source_lds_tx_log.memo = "Reserve TR from %s" % fstr_target_name
			source_lds_tx_log.category = "MRTX2"
			source_lds_tx_log.amount = lint_amount
			source_lds_tx_log.current_network_balance = lds_source.current_network_balance
			source_lds_tx_log.current_reserve_balance = lds_source.current_reserve_balance
			source_lds_tx_log.access = "PUBLIC" # "PUBLIC" OR "PRIVATE"
			source_lds_tx_log.description = lstr_source_tx_description 
			source_lds_tx_log.user_id_created = lds_source.user_id
			source_lds_tx_log.network_id = network_id
			source_lds_tx_log.account_id = source_account_id
			source_lds_tx_log.source_account = source_account_id 
			source_lds_tx_log.target_account = target_account_id
			source_lds_tx_log.put()

			lds_target.tx_index += 1
			# target transaction log
			target_tx_log_key = ndb.Key("ds_mr_tx_log", "MRTX2%s%s%s" % (key_part1, key_part3,str(lds_target.tx_index).zfill(12)))
			target_lds_tx_log = ds_mr_tx_log()
			target_lds_tx_log.key = target_tx_log_key
			# tx_index should be based on incremented metric_account value
			target_lds_tx_log.tx_index = lds_target.tx_index
			target_lds_tx_log.tx_type = lstr_target_tx_type # SHORT WORD(S) FOR WHAT TRANSACTION DID
			target_lds_tx_log.memo = "Reserve TR to %s" % fstr_source_name
			target_lds_tx_log.category = "MRTX2"
			target_lds_tx_log.amount = lint_amount
			target_lds_tx_log.current_network_balance = lds_target.current_network_balance
			target_lds_tx_log.current_reserve_balance = lds_target.current_reserve_balance
			# typically we'll make target private for bilateral transactions so that
			# when looking at a system view, we don't see duplicates.
			target_lds_tx_log.access = "PRIVATE" # "PUBLIC" OR "PRIVATE"
			target_lds_tx_log.description = lstr_target_tx_description 
			target_lds_tx_log.user_id_created = lds_source.user_id
			target_lds_tx_log.network_id = network_id
			target_lds_tx_log.account_id = target_account_id
			target_lds_tx_log.source_account = source_account_id 
			target_lds_tx_log.target_account = target_account_id
			target_lds_tx_log.put()
			
		else:
		
			# not a payment related transaction
			
			# ADD TWO TRANSACTIONS LIKE CONNECT()
			# source transaction log
			source_lds_tx_log = ds_mr_tx_log()
			# tx_index should be based on incremented metric_account value
			source_lds_tx_log.tx_type = lstr_source_tx_type # SHORT WORD(S) FOR WHAT TRANSACTION DID
			source_lds_tx_log.amount = lint_amount
			source_lds_tx_log.access = "PUBLIC" # "PUBLIC" OR "PRIVATE"
			source_lds_tx_log.description = lstr_source_tx_description 
			source_lds_tx_log.user_id_created = lds_source.user_id
			source_lds_tx_log.network_id = network_id
			source_lds_tx_log.account_id = source_account_id
			source_lds_tx_log.source_account = source_account_id 
			source_lds_tx_log.target_account = target_account_id
			source_lds_tx_log.put()

			# target transaction log
			target_lds_tx_log = ds_mr_tx_log()
			# tx_index should be based on incremented metric_account value
			target_lds_tx_log.tx_type = lstr_target_tx_type # SHORT WORD(S) FOR WHAT TRANSACTION DID
			target_lds_tx_log.amount = lint_amount
			# typically we'll make target private for bilateral transactions so that
			# when looking at a system view, we don't see duplicates.
			target_lds_tx_log.access = "PRIVATE" # "PUBLIC" OR "PRIVATE"
			target_lds_tx_log.description = lstr_target_tx_description 
			target_lds_tx_log.user_id_created = lds_source.user_id
			target_lds_tx_log.network_id = network_id
			target_lds_tx_log.account_id = target_account_id
			target_lds_tx_log.source_account = source_account_id 
			target_lds_tx_log.target_account = target_account_id
			target_lds_tx_log.put()
		
		lds_source.put()
		lds_target.put()
		return True

	def _leave_network(self, fstr_network_name,fstr_source_name,fstr_type):
	
		# we don't want/need to get the network info inside a transaction.
		network = self._get_network(fstr_network_name)
		if network is None: return False # pass up error code
		return self._leave_network_transactional(network.network_id,fstr_source_name,fstr_type)
		
	@ndb.transactional(xg=True)
	def _leave_network_transactional(self,fint_network_id,fstr_source_name,fstr_type):

		def check_default(fobj_user):
		
			# Check default is just making sure a default account exists
			# when a user adds or deletes accounts.  They may delete the
			# default, or they may add a second account without designating
			# a default.  This makes sure they always have a default if 
			# there is more than one account for them in that network and
			# the system needs to pick one for a function where the user
			# doesn't specifically designate manually.  For instance, a 
			# "search and pay" after deleting 1 of 3 accounts in a network
			# which happens to be the default.
		
			checker = {}
			# first loop set sets checker to True from default of False
			# if a default account is found.
			for i in range(len(fobj_user.reserve_network_ids)):
				if not fobj_user.reserve_network_ids[i] in checker:
					# add the network id as a key to our checker if it doesn't exist
					checker[fobj_user.reserve_network_ids[i]] = fobj_user.reserve_default[i]
				if fobj_user.reserve_default[i]: checker[fobj_user.reserve_network_ids[i]] = True
				
			for i in range(len(fobj_user.client_network_ids)):
				if not fobj_user.client_network_ids[i] in checker:
					# add the network id as a key to our checker if it doesn't exist
					checker[fobj_user.client_network_ids[i]] = fobj_user.client_default[i]
				if fobj_user.client_default[i]: checker[fobj_user.client_network_ids[i]] = True
				
			for i in range(len(fobj_user.joint_network_ids)):
				if not fobj_user.joint_network_ids[i] in checker:
					# add the network id as a key to our checker if it doesn't exist
					checker[fobj_user.joint_network_ids[i]] = fobj_user.joint_default[i]
				if fobj_user.joint_default[i]: checker[fobj_user.joint_network_ids[i]] = True
				
			for i in range(len(fobj_user.clone_network_ids)):
				if not fobj_user.clone_network_ids[i] in checker:
					# add the network id as a key to our checker if it doesn't exist
					checker[fobj_user.clone_network_ids[i]] = fobj_user.clone_default[i]
				if fobj_user.clone_default[i]: checker[fobj_user.clone_network_ids[i]] = True

			# second loop says, if the checker for that network id is False
			# set the checker for that network id and the default value on
			# that account to True.
			for i in range(len(fobj_user.reserve_network_ids)):
				if checker[fobj_user.reserve_network_ids[i]] == False:
					checker[fobj_user.reserve_network_ids[i]] = True
					fobj_user.reserve_default[i] = True
					
			for i in range(len(fobj_user.client_network_ids)):
				if checker[fobj_user.client_network_ids[i]] == False:
					checker[fobj_user.client_network_ids[i]] = True
					fobj_user.client_default[i] = True

			for i in range(len(fobj_user.joint_network_ids)):
				if checker[fobj_user.joint_network_ids[i]] == False:
					checker[fobj_user.joint_network_ids[i]] = True
					fobj_user.joint_default[i] = True

			for i in range(len(fobj_user.clone_network_ids)):
				if checker[fobj_user.clone_network_ids[i]] == False:
					checker[fobj_user.clone_network_ids[i]] = True
					fobj_user.clone_default[i] = True
					
		validation_result = self._name_validate_transactional(None,fstr_source_name,None,fint_network_id)
		if not validation_result:
			# pass up error
			return False

		network_id = validation_result[0]
		source_account_id = validation_result[1]
		source_user = validation_result[3]

		def delete_if_not_username(fstr_label):			
			if not fstr_label == source_user.username:			
				label_key = ndb.Key("ds_mr_unique_dummy_entity", fstr_label)
				label_key.delete()

		# transactionally get the source and target metric accounts
		key_part1 = str(network_id).zfill(8)
		key_part2 = str(source_account_id).zfill(12)
		source_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part2))
		lds_source_metric = source_key.get()

		# error if source doesn't exist
		if lds_source_metric is None:
				self.PARENT.RETURN_CODE = "1207"
				return False # error Source id is invalid.
						
		if fstr_type == "joint close":
			if lds_source_metric.current_network_balance > 0:
				self.PARENT.RETURN_CODE = "1208"
				return False # error Network balance must be zero in order to close joint account.
			
			for i in range(len(source_user.joint_network_ids)):
				if source_user.joint_network_ids[i] == network_id:
					if source_user.joint_account_ids[i] == source_account_id:
						# load parent metric account
						key_part3 = str(source_user.joint_parent_ids[i]).zfill(12)
						parent_metric_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part3))
						lds_parent_metric = parent_metric_key.get()
						# load parent user object
						parent_user_key = ndb.Key("ds_mr_user",lds_parent_metric.user_id)
						parent_user = parent_user_key.get()
						# error if parent doesn't exist
						if parent_user is None:
							self.PARENT.RETURN_CODE = "1209"
							return False # error: parent id is not valid
						# update source user object
						source_user.total_other_accounts -= 1
						del source_user.joint_network_ids[i]
						del source_user.joint_account_ids[i]
						del source_user.joint_parent_ids[i]
						delete_if_not_username(source_user.joint_labels[i])
						del source_user.joint_labels[i]
						del source_user.joint_default[i]		
						# update parent user object
						parent_user.total_child_accounts -= 1
						for j in range (len(parent_user.child_joint_network_ids)):
							if parent_user.child_joint_network_ids[j] == network_id:
								if parent_user.child_joint_account_ids[j] == source_account_id:
									del parent_user.child_joint_network_ids[i]
									del parent_user.child_joint_account_ids[i]
									del parent_user.child_joint_parent_ids[i]						
						# update source metric account
						lds_source_metric.account_status = "DELETED"
						lds_source_metric.current_timestamp = datetime.datetime.now()
						# create transaction						
						# transaction log
						lds_tx_log = ds_mr_tx_log()
						lds_tx_log.tx_type = "JOINT CLOSE" # SHORT WORD(S) FOR WHAT TRANSACTION DID
						lds_tx_log.access = "PUBLIC" # "PUBLIC" OR "PRIVATE"
						lds_tx_log.description = "A user closed a joint account." 
						lds_tx_log.user_id_created = source_user.user_id
						lds_tx_log.network_id = network_id
						lds_tx_log.account_id = source_account_id
						lds_tx_log.source_account = source_account_id
						lds_tx_log.put()
						check_default(source_user)
						source_user.put()
						parent_user.put()
						lds_source_metric.put()						
						break
						
			self.PARENT.RETURN_CODE = "7038" # Successfully closed joint account.			
			return True
		
		elif fstr_type == "client close":
			if lds_source_metric.current_network_balance > 0:
				self.PARENT.RETURN_CODE = "1210"
				return False # error Network balance must be zero in order to close client account. 

			for i in range(len(source_user.client_network_ids)):
				if source_user.client_network_ids[i] == network_id:
					if source_user.client_account_ids[i] == source_account_id:
						# load parent metric account
						key_part3 = str(source_user.client_parent_ids[i]).zfill(12)
						parent_metric_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part3))
						lds_parent_metric = parent_metric_key.get()
						# load parent user object
						parent_user_key = ndb.Key("ds_mr_user",lds_parent_metric.user_id)
						parent_user = parent_user_key.get()
						# error if parent doesn't exist
						if parent_user is None:
							self.PARENT.RETURN_CODE = "1211"
							return False # error: parent id is not valid
						# update source user object
						source_user.total_other_accounts -= 1
						del source_user.client_network_ids[i]
						del source_user.client_account_ids[i]
						del source_user.client_parent_ids[i]
						delete_if_not_username(source_user.client_labels[i])
						del source_user.client_labels[i]
						del source_user.client_default[i]
						# update parent user object
						parent_user.total_child_accounts -= 1
						for j in range (len(parent_user.child_client_network_ids)):
							if parent_user.child_client_network_ids[j] == network_id:
								if parent_user.child_client_account_ids[j] == source_account_id:
									del parent_user.child_client_network_ids[i]
									del parent_user.child_client_account_ids[i]
									del parent_user.child_client_parent_ids[i]						
						# update source metric account
						lds_source_metric.account_status = "DELETED"
						lds_source_metric.current_timestamp = datetime.datetime.now()
						# create transaction						
						# transaction log
						lds_tx_log = ds_mr_tx_log()
						# tx_index should be based on incremented metric_account value
						lds_tx_log.tx_type = "CLIENT CLOSE" # SHORT WORD(S) FOR WHAT TRANSACTION DID
						lds_tx_log.access = "PUBLIC" # "PUBLIC" OR "PRIVATE"
						lds_tx_log.description = "A user closed a client account." 
						lds_tx_log.user_id_created = source_user.user_id
						lds_tx_log.network_id = network_id
						lds_tx_log.account_id = source_account_id
						lds_tx_log.source_account = source_account_id
						lds_tx_log.put()
						check_default(source_user)
						source_user.put()
						parent_user.put()
						lds_source_metric.put()						
						break
						
			self.PARENT.RETURN_CODE = "7039" # Successfully closed client account.			
			return True

		elif fstr_type == "clone close":
			if lds_source_metric.current_network_balance > 0:
				self.PARENT.RETURN_CODE = "1212"
				return False # error Network balance must be zero in order to close clone account. 

			for i in range(len(source_user.clone_network_ids)):
				if source_user.clone_network_ids[i] == network_id:
					if source_user.clone_account_ids[i] == source_account_id:
						# update source user object
						source_user.total_other_accounts -= 1
						del source_user.clone_network_ids[i]
						del source_user.clone_account_ids[i]
						del source_user.clone_parent_ids[i]
						delete_if_not_username(source_user.clone_labels[i])
						del source_user.clone_labels[i]
						del source_user.clone_default[i]
						# update source metric account
						lds_source_metric.account_status = "DELETED"
						lds_source_metric.current_timestamp = datetime.datetime.now()
						# create transaction						
						# transaction log
						lds_tx_log = ds_mr_tx_log()
						# tx_index should be based on incremented metric_account value
						lds_tx_log.tx_type = "CLONE CLOSE" # SHORT WORD(S) FOR WHAT TRANSACTION DID
						lds_tx_log.access = "PUBLIC" # "PUBLIC" OR "PRIVATE"
						lds_tx_log.description = "A user closed a clone account." 
						lds_tx_log.user_id_created = source_user.user_id
						lds_tx_log.network_id = network_id
						lds_tx_log.account_id = source_account_id
						lds_tx_log.source_account = source_account_id
						lds_tx_log.put()
						check_default(source_user)
						source_user.put()
						lds_source_metric.put()						
						break
						
			self.PARENT.RETURN_CODE = "7040" # Successfully closed reserve account.			
			return True

		elif fstr_type == "reserve close":
		
			# error if account still has connections
			if len(lds_source_metric.current_connections) > 0:
				self.PARENT.RETURN_CODE = "1213"
				return False # error Account still has connections.
		
			# error if account still has child accounts
			if lds_source_metric.total_child_accounts > 0:
				self.PARENT.RETURN_CODE = "1214"
				return False # error Account still has child accounts.
			
			if lds_source_metric.current_network_balance > 0:
				self.PARENT.RETURN_CODE = "1215"
				return False # error Network balance must be zero in order to close clone account.

			for i in range(len(source_user.reserve_network_ids)):
				if source_user.reserve_network_ids[i] == network_id:
					if source_user.reserve_account_ids[i] == source_account_id:
						# update source user object
						source_user.total_reserve_accounts -= 1
						del source_user.reserve_network_ids[i]
						del source_user.reserve_account_ids[i]
						del source_user.reserve_parent_ids[i]
						delete_if_not_username(source_user.reserve_labels[i])
						del source_user.reserve_labels[i]
						del source_user.reserve_default[i]
						# update source metric account
						lds_source_metric.account_status = "DELETED"
						lds_source_metric.current_timestamp = datetime.datetime.now()
						# create transaction						
						# transaction log
						lds_tx_log = ds_mr_tx_log()
						# tx_index should be based on incremented metric_account value
						lds_tx_log.tx_type = "RESERVE CLOSE" # SHORT WORD(S) FOR WHAT TRANSACTION DID
						lds_tx_log.access = "PUBLIC" # "PUBLIC" OR "PRIVATE"
						lds_tx_log.description = "A user closed a reserve account." 
						lds_tx_log.user_id_created = source_user.user_id
						lds_tx_log.network_id = network_id
						lds_tx_log.account_id = source_account_id
						lds_tx_log.source_account = source_account_id
						lds_tx_log.put()
						check_default(source_user)
						source_user.put()
						lds_source_metric.put()						
						break
						
			self.PARENT.RETURN_CODE = "7041" # Successfully closed clone account.			
			return True
				
		else:
			self.PARENT.RETURN_CODE = "1216"
			return False # error Transaction type not recognized. 

	def _joint_retrieve(self,fstr_network_name,fstr_source_name,fstr_target_name,fstr_amount):
	
		# we don't want/need to get the network conversion rate inside a transaction.
		network = self._get_network(fstr_network_name=fstr_network_name)
		if network is None: return False # pass up error code
		return self._joint_retrieve_transactional(network.network_id,fstr_source_name,fstr_target_name,fstr_amount,network.skintillionths)

	@ndb.transactional(xg=True)
	def _joint_retrieve_transactional(self,fint_network_id,fstr_source_name,fstr_target_name,fstr_amount,fint_conversion):

		validation_result = self._name_validate_transactional(None,fstr_source_name,fstr_target_name,fint_network_id)
		if not validation_result:
			# pass up error
			return False

		network_id = validation_result[0]
		source_account_id = validation_result[1]
		source_user = validation_result[3]
		target_account_id = validation_result[2]
		target_user = validation_result[4]

		# a "joint retrieve" is a reverse payment.  A parent account
		# is taking money out of a child account.  So it's basically
		# the same process as a payment with a couple extra 
		# permission checks.
		
		key_part1 = str(network_id).zfill(8)
		key_part2 = str(source_account_id).zfill(12)
		key_part3 = str(target_account_id).zfill(12)
		source_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part2))
		lds_source_metric = source_key.get()


		# error if source doesn't exist
		if lds_source_metric is None:
			self.PARENT.RETURN_CODE = "1217"
			return False # error Source id is invalid.
		# error if trying to connect to self
		if source_account_id == target_account_id:
			self.PARENT.RETURN_CODE = "1218"
			return False # error Can't retrieve from self.
		
		target_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part3))
		lds_target_metric = target_key.get()
		
		# error if target doesn't exist
		if lds_target_metric is None:
			self.PARENT.RETURN_CODE = "1219"
			return False # error Target id is invalid.
		
		# make sure source actually has rights to do this
		child_has_parent = False
		for i in range(len(target_user.joint_network_ids)):
			if target_user.joint_network_ids[i] == network_id:
				if target_user.joint_account_ids[i] == target_account_id:
					if target_user.joint_parent_ids[i] == source_account_id:
						child_has_parent = True
						break
		
		if not child_has_parent:
			self.PARENT.RETURN_CODE = "1220"
			return False # error Target is not a child joint account of source.
		
		parent_has_child = False
		for i in range(len(source_user.child_joint_network_ids)):
			if source_user.child_joint_network_ids[i] == network_id:
				if source_user.child_joint_account_ids[i] == target_account_id:
					if source_user.child_joint_parent_ids[i] == source_account_id:
						parent_has_child = True
						break
						
		if not parent_has_child:
			self.PARENT.RETURN_CODE = "1221"
			return False # error Target is not a child joint account of source.
						
		# make sure fstr_amount actually is an integer
		try:
			lint_amount = int(float(fstr_amount)*fint_conversion)
		except ValueError, ex:
			self.PARENT.RETURN_CODE = "1222"
			return False # error Invalid amount passed.
		
		# can't exceed maximum allowed payment
		if lint_amount > MAX_PAYMENT:
			self.PARENT.RETURN_CODE = "1223"
			return False # error Retrieve amount exceeds maximum payment allowed.

		# make sure all lint_amount inputs are greater than 0
		# can't pay if you don't have that much
		if lds_target_metric.current_network_balance < lint_amount:
			self.PARENT.RETURN_CODE = "1224"
			return False # error Joint account does not have enough balance for the retrieval requested.
		
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
		if lds_source_metric.current_timestamp > t_cutoff:

			# last transaction was in current time window, no need to swap
			# a.k.a. overwrite current
			lds_source_metric.current_network_balance -= lint_amount

		else:

			# last transaction was in previous time window, swap
			# a.k.a. move "old" current into "last" before overwriting
			lds_source_metric.last_connections = lds_source_metric.current_connections
			lds_source_metric.last_reserve_balance = lds_source_metric.current_reserve_balance
			lds_source_metric.last_network_balance = lds_source_metric.current_network_balance
			lds_source_metric.current_network_balance += lint_amount				

		# update the target account
		if lds_target_metric.current_timestamp > t_cutoff:

			# last transaction was in current time window, no need to swap
			# a.k.a. overwrite current
			lds_target_metric.current_network_balance += lint_amount

		else:

			# last transaction was in previous time window, swap
			# a.k.a. move "old" current into "last" before overwriting
			lds_target_metric.last_connections = lds_target_metric.current_connections
			lds_target_metric.last_reserve_balance = lds_target_metric.current_reserve_balance
			lds_target_metric.last_network_balance = lds_target_metric.current_network_balance
			lds_target_metric.current_network_balance -= lint_amount

		# only update current_timestamp for graph dependent transactions??? STUB
		lds_source_metric.current_timestamp = datetime.datetime.now()
		lds_target_metric.current_timestamp = datetime.datetime.now()
		
		# ADD TWO TRANSACTIONS LIKE CONNECT()
		lds_source_metric.tx_index += 1
		# source transaction log
		source_tx_log_key = ndb.Key("ds_mr_tx_log", "MRTX2%s%s%s" % (key_part1, key_part2,str(lds_source_metric.tx_index).zfill(12)))
		source_lds_tx_log = ds_mr_tx_log()
		source_lds_tx_log.key = source_tx_log_key
		# tx_index should be based on incremented metric_account value
		source_lds_tx_log.tx_index = lds_source_metric.tx_index
		source_lds_tx_log.tx_type = "JOINT RETRIEVE IN" # SHORT WORD(S) FOR WHAT TRANSACTION DID
		source_lds_tx_log.memo = "Joint TR from %s" % fstr_target_name
		source_lds_tx_log.category = "MRTX2"
		source_lds_tx_log.amount = lint_amount
		source_lds_tx_log.current_network_balance = lds_source_metric.current_network_balance
		source_lds_tx_log.current_reserve_balance = lds_source_metric.current_reserve_balance
		source_lds_tx_log.access = "PUBLIC" # "PUBLIC" OR "PRIVATE"
		source_lds_tx_log.description = "JOINT ACCOUNT FUNDS RETRIEVED" 
		source_lds_tx_log.user_id_created = lds_source_metric.user_id
		source_lds_tx_log.network_id = network_id
		source_lds_tx_log.account_id = source_account_id
		source_lds_tx_log.source_account = source_account_id 
		source_lds_tx_log.target_account = target_account_id
		source_lds_tx_log.put()

		lds_target_metric.tx_index += 1
		# target transaction log
		target_tx_log_key = ndb.Key("ds_mr_tx_log", "MRTX2%s%s%s" % (key_part1, key_part3,str(lds_target_metric.tx_index).zfill(12)))
		target_lds_tx_log = ds_mr_tx_log()
		target_lds_tx_log.key = target_tx_log_key
		# tx_index should be based on incremented metric_account value
		target_lds_tx_log.tx_index = lds_target_metric.tx_index
		target_lds_tx_log.tx_type = "JOINT RETRIEVE OUT" # SHORT WORD(S) FOR WHAT TRANSACTION DID
		target_lds_tx_log.memo = "Joint TR to %s" % fstr_source_name
		target_lds_tx_log.category = "MRTX2"
		target_lds_tx_log.amount = lint_amount
		target_lds_tx_log.current_network_balance = lds_target_metric.current_network_balance
		target_lds_tx_log.current_reserve_balance = lds_target_metric.current_reserve_balance
		# typically we'll make target private for bilateral transactions so that
		# when looking at a system view, we don't see duplicates.
		target_lds_tx_log.access = "PRIVATE" # "PUBLIC" OR "PRIVATE"
		target_lds_tx_log.description = "JOINT ACCOUNT FUNDS TO PARENT ACCOUNT" 
		target_lds_tx_log.user_id_created = lds_source.user_id
		target_lds_tx_log.network_id = network_id
		target_lds_tx_log.account_id = target_account_id
		target_lds_tx_log.source_account = source_account_id 
		target_lds_tx_log.target_account = target_account_id
		target_lds_tx_log.put()
		
		lds_source_metric.put()
		lds_target_metric.put()
		self.PARENT.RETURN_CODE = "7042" # success Joint account retrieval successful.
		return True

	def _get_default(self,fstr_network_name,fstr_user_id):

		network = self._get_network(fstr_network_name)
		if network is None: return False, None, None, None # pass up error code
		network_id = network.network_id
		# this function loads a user entity from a key
		source_user_key = ndb.Key("ds_mr_user",fstr_user_id)
		source_user = source_user_key.get()
		for i in range(len(source_user.reserve_network_ids)):
			if source_user.reserve_network_ids[i] == network_id:
				if source_user.reserve_default[i] == True:
					return True, network, source_user.reserve_account_ids[i], source_user.reserve_labels[i], source_user
		for i in range(len(source_user.client_network_ids)):
			if source_user.client_network_ids[i] == network_id: 
				if source_user.client_default[i] == True:
					return True, network, source_user.client_account_ids[i], source_user.client_labels[i], source_user
		for i in range(len(source_user.joint_network_ids)):
			if source_user.joint_network_ids[i] == network_id: 
				if source_user.joint_default[i] == True:
					return True, network, source_user.joint_account_ids[i], source_user.joint_labels[i], source_user
		for i in range(len(source_user.clone_network_ids)):
			if source_user.clone_network_ids[i] == network_id: 
				if source_user.clone_default[i] == True:
					return True, network, source_user.clone_account_ids[i], source_user.clone_labels[i], source_user
		return True, network, None, None, None
				
	def _set_default(self,fstr_network_name,fstr_source_name):

		network = self._get_network(fstr_network_name)
		if network is None: return False # pass up error code
		return self._set_default_transactional(network.network_id,fstr_source_name)
		
	@ndb.transactional(xg=True)
	def _set_default_transactional(self,fint_network_id,fstr_source_name):

		validation_result = self._name_validate_transactional(None,fstr_source_name,None,fint_network_id)
		if not validation_result:
			# pass up error
			return False

		network_id = validation_result[0]
		source_account_id = validation_result[1]
		source_user = validation_result[3]
		set_successful = False
		for i in range(len(source_user.reserve_network_ids)):
			if source_user.reserve_network_ids[i] == network_id:
				if source_user.reserve_account_ids[i] == source_account_id:
					source_user.reserve_default[i] = True
					set_successful = True
				else:
					source_user.reserve_default[i] = False
			
		for i in range(len(source_user.client_network_ids)):
			if source_user.client_network_ids[i] == network_id:
				if source_user.client_account_ids[i] == source_account_id:
					source_user.client_default[i] = True
					set_successful = True
				else:
					source_user.client_default[i] = False
					
		for i in range(len(source_user.joint_network_ids)):
			if source_user.joint_network_ids[i] == network_id:
				if source_user.joint_account_ids[i] == source_account_id:
					source_user.joint_default[i] = True
					set_successful = True
				else:
					source_user.joint_default[i] = False
					
		for i in range(len(source_user.clone_network_ids)):
			if source_user.clone_network_ids[i] == network_id:
				if source_user.clone_account_ids[i] == source_account_id:
					source_user.clone_default[i] = True
					set_successful = True
				else:
					source_user.clone_default[i] = False
			
		if set_successful:
			self.PARENT.RETURN_CODE = "7046" # Successfully set default account.
			source_user.put()
			return True
		else:
			self.PARENT.RETURN_CODE = "1231" # error Could not find account in user object.
			return False

	def _process_ticket(self,fstr_network_name,fstr_owner_name,fstr_visitor_name,fct,fstr_ticket_name=None):

		# we don't want/need to get the network conversion rate inside a transaction.
		network = self._get_network(fstr_network_name)
		if network is None: return False # pass up error code
		return self._process_ticket_transactional(network.network_id,fstr_owner_name,fstr_visitor_name,fct,network.skintillionths,fstr_ticket_name)

	@ndb.transactional(xg=True)
	def _process_ticket_transactional(self,fint_network_id,fstr_owner_name,fstr_visitor_name,fct,fint_conversion,fstr_ticket_name):

		amount = None
		user = None
		memo = None
		ticket_name = None
		gratuity_amount = None
		gratuity_percent = None
		
		def is_valid_number(fstr_num,fstr_type="amount"):
		
			# make sure fstr_amount actually is an integer
			if fstr_type == "amount":
				try:
					lint_amount = int(float(fstr_num)*fint_conversion)
					amount = lint_amount
					return True
				except ValueError, ex:
					self.PARENT.RETURN_CODE = "1232"
					return False # error Invalid amount passed.
			if fstr_type == "gratuity_amount":
				try:
					lint_amount = int(float(fstr_num)*fint_conversion)
					gratuity_amount = lint_amount
					return True
				except ValueError, ex:
					self.PARENT.RETURN_CODE = "1233"
					return False # error Invalid amount passed.
			if fstr_type == "gratuity_percent":
				if not fstr_num[-1] == "%":
					self.PARENT.RETURN_CODE = "1234"
					return False # error Gratuity missing percent
				del fstr_num[-1]					
				try:
					float_amount = float(fstr_num)
					gratuity_percent = fstr_num
					return True
				except ValueError, ex:
					self.PARENT.RETURN_CODE = "1235"
					return False # error Invalid gratuity percent passed.
			self.PARENT.RETURN_CODE = "1236"
			return False # error Invalid type passed.
		
		def is_valid_name(fstr_name,fstr_type=None):

			# a valid name is comprised of re.match(r'^[a-z0-9_]+$',fstr_name)
			# so only a-z, 0-9, or an underscore
			# additionally:
			# 1. Can't end or begin with an underscore
			# 2. Can't be less than three characters
			# 3. Must contain at least one letter.
			# 4. If 10 or less in length, must contain at lease one
			# number and at least one letternumber as keywords 
			# reserve the 10 or less space without numbers
			# or underscores.
			if not re.match(r'^[a-z0-9_]+$',fstr_name):
				return False
			if not re.search('[a-z]',fstr_name):
				return False
			if not len(fstr_name) > 2:
				return False
			if fstr_name[:1] == "_" or fstr_name[-1:] == "_":
				return False
			if len(fstr_name) < 11 and not re.search('[0-9]',fstr_name):
				return False
			if fstr_type == "user":
				user = fstr_name
			if fstr_type == "ticket":
				ticket_name = fstr_name
			return True
		
		def parse_for_memo(command_seq,index_max):
		
			found = False
			new_command_seq = []
			m_count = 0
			for i in range(len(command_seq)):
				if i > index_max:
					break
				else:
					new_command_seq.append()
					if command_seq[i] == "m":
						found = True
						# Find the index of the 'nth' occurrence of "m" 
						# from raw command. Take everything after that
						# point as the memo variable.
						start = command_seq[-1].find("m")
						while start > 0 and m_count > 0:
							start = command_seq[-1].find("m",start + 1)
							m_count -= 1
						# now start equals the index of the "m" we want
						memo = command_seq[-1][(start + 1):]
						break
					else:
						m_count += command_seq[i].count("m")
						new_command_seq.append(command_seq[i])
			if found:
				return (new_command_seq,memo)
			else:
				return (command_seq,memo)
		
		def get_or_insert_ticket_index(fint_network_id,fint_account_id,fstr_user_id):
		
			ticket_index_key = ndb.Key("ds_mr_metric_ticket_index", "%s%s" % (fint_network_id, fint_account_id))
			ticket_index_entity = ticket_index_key.get()
			if ticket_index_entity is None:
				ticket_index_entity = ds_mr_metric_ticket_index()
				ticket_index_entity.key = ticket_index_key
				ticket_index_entity.account_id = fint_account_id
				ticket_index_entity.user_id = fstr_user_id
				ticket_index_entity.network_id = fint_network_id
				ticket_index_entity.ticket_data = {}
			if not "ticket_count" in source_ticket_index.ticket_data:
				# initialize ticket_data
				ticket_index_entity.ticket_data["ticket_count"] = 0
				ticket_index_entity.ticket_data["ticket_labels"] = []
				ticket_index_entity.ticket_data["ticket_amounts"] = []
				ticket_index_entity.ticket_data["ticket_memos"] = []
				ticket_index_entity.ticket_data["ticket_tag_network_ids"] = []
				ticket_index_entity.ticket_data["ticket_tag_account_ids"] = []
				ticket_index_entity.ticket_data["ticket_tag_user_ids"] = []

				ticket_index_entity.ticket_data["tag_count"] = 0
				ticket_index_entity.ticket_data["tag_labels"] = []
				ticket_index_entity.ticket_data["tag_amounts"] = []
				ticket_index_entity.ticket_data["tag_memos"] = []
				ticket_index_entity.ticket_data["tag_network_ids"] = []
				ticket_index_entity.ticket_data["tag_account_ids"] = []
				ticket_index_entity.ticket_data["tag_user_ids"] = []			
			return ticket_index_entity
			
		raw_command = fct[-1]

		# We have a ticket name.
		#
		# OWNER FUNCTIONS:
		#  1. close : close the ticket
		#  2. remove : removes any user tags
		#  3. attach <username> : tags a user with this ticket
		#  4. amount <amount> : directly assigns ticket amount value overwriting previous (blanking memo)
		#  5. amount <amount> m <memo> : same as amount but with memo
		#  6. open <name>
		#  7. open <name> m <memo>
		#  8. open <name> <user>
		#  9. open <name> <user> m <memo>
		# 10. open <name> <amount>
		# 11. open <name> <amount> m <memo>
		# 12. open <name> <user> <amount>
		# 13. open <name> <user> <amount> m <memo>
		# 
		# TAGGED USER FUNCTIONS
		# 1. remove : removes a users tag from a ticket
		#
		# ANYONE FUNCTIONS
		# 1. pay <amount> : pay a ticket
		# 2. pay <amount> <amount|percent> : pay a ticket plus add gratuity

		result = parse_for_memo(fct,4)
		ct = result[0]
		memo = result[1]
				
		# If there is a "visitor" user besides the owner of this ticket, it means
		# that the owner is not the one executing the action.  But we still need
		# to validate both.  So we'll get the user objects and account id's from
		# the names.  fstr_visitor_name will never be populated if the ticket 
		# owner is simply referencing them in the command.
		
		if fstr_visitor_name is None:
			
			# Must be ticket owner executing commands

			# If the ticket hasn't been created yet then
			# only available command is "open".		
			if fstr_ticket_name is None:

				# we can only be doing "open" command, which creates a new ticket
				if not ct[0] == "open":
					self.PARENT.RETURN_CODE = "1237" # error Command not valid.  No ticket name specified.
					return False

				if not len(ct) > 1:
					self.PARENT.RETURN_CODE = "1238" # error Not enough arguments for open ticket command.
					return False

				if not is_valid_name(ct[1],"ticket"):
					self.PARENT.RETURN_CODE = "1239" # error Ticket name provided is not valid.
					return False			

				if len(ct) > 4:
					self.PARENT.RETURN_CODE = "1240" # error Too many arguments for open ticket command.
					return False

				# Now we know:
				# 1. command is 2, 3, or 4 in length				
				# 2. first token is "open"
				# 3. if they passed a memo it's in the memo variable or memo is None
				#
				# Length 3 is the only variable now, it could be "user" or "amount"
				# in index 2.
				if len(ct) == 3:
					if not is_valid_name(ct[2],"user"):
						self.PARENT.RETURN_CODE = "1241" # error User name provided is not valid.
						return False
					elif not is_valid_number(ct[2]):
						self.PARENT.RETURN_CODE = "1242" # error Amount provided is not valid.
						return False
					else:
						self.PARENT.RETURN_CODE = "1243" # error Ticket open() command parsing error on 3rd token. Must be valid username or amount.
						return False
				if len(ct) == 4: 
					# open <name> <user> <amount>	
					if not is_valid_name(ct[2],"user"):
						self.PARENT.RETURN_CODE = "1244" # error Ticket open() command parsing error on 3rd token. Must be valid username.
						return False

					if not is_valid_number(ct[3]):
						self.PARENT.RETURN_CODE = "1245" # error Ticket open() command parsing error on 4th token. Must be valid amount.
						return False

				# At this point, regardless of length, we have our
				# four variables.  
				validation_result = self._name_validate_transactional(None,fstr_owner_name,user,fint_network_id)
				if not validation_result:
					# pass up error
					return False

				network_id = validation_result[0]
				source_account_id = validation_result[1]
				source_user = validation_result[3]
				source_ticket_index = get_or_insert_ticket_index(network_id,source_account_id,source_user.user_id)

				# Now we just need to make sure the ticket name is available
				# in the source's index and that the target, if exists, isn't
				# maxed out in ticket tags.


				if source_ticket_index.ticket_data["ticket_count"] > 999:
					self.PARENT.RETURN_CODE = "1246" # error Open tickets already at maximum.
					return False

				if ticket_name in source_ticket_index.ticket_data["ticket_labels"]:
					self.PARENT.RETURN_CODE = "1247" # error Ticket name already in use.
					return False

				# add ticket data for source
				source_ticket_index.ticket_data["ticket_count"] += 1
				source_ticket_index.ticket_data["ticket_labels"].append(ticket_name)
				source_ticket_index.ticket_data["ticket_amounts"].append(amount)
				source_ticket_index.ticket_data["ticket_memos"].append(memo)
				source_ticket_index.ticket_data["ticket_tag_network_ids"].append(None) 
				source_ticket_index.ticket_data["ticket_tag_account_ids"].append(None) 
				source_ticket_index.ticket_data["ticket_tag_user_ids"].append(None) 

				if not user is None:
					target_account_id = validation_result[2]
					target_user = validation_result[4]
					target_ticket_index = get_or_insert_ticket_index(network_id,target_account_id,target_user.user_id)

					if target_ticket_index.ticket_data["tag_count"] > 19:
						self.PARENT.RETURN_CODE = "1248" # error Target tag count already at maximum.
						return False

					target_ticket_index.ticket_data["tag_count"] += 1
					target_ticket_index.ticket_data["tag_labels"].append(ticket_name)
					target_ticket_index.ticket_data["tag_amounts"].append(amount)
					target_ticket_index.ticket_data["tag_memos"].append(amount)
					target_ticket_index.ticket_data["tag_network_ids"].append(network_id)
					target_ticket_index.ticket_data["tag_account_ids"].append(source_account_id)
					target_ticket_index.ticket_data["tag_user_ids"].append(source_user.user_id)

					source_ticket_index.ticket_data["ticket_tag_network_ids"][-1] = network_id
					source_ticket_index.ticket_data["ticket_tag_account_ids"][-1] = target_account_id
					source_ticket_index.ticket_data["ticket_tag_user_ids"][-1] = target_user.user_id

					source_ticket_index.put()
					target_ticket_index.put()	
					self.PARENT.RETURN_CODE = "7047" # success Ticket successfully opened.
					return True
				else:
					source_ticket_index.put()
					self.PARENT.RETURN_CODE = "7048" # success Ticket successfully opened.
					return True		
			else:
			
				parse_match = False
				# implement owner commands
				if len(ct) == 1 and ct[0] == "close":
					parse_match = True
					command_switch = "close"
					ticket_name = fstr_ticket_name
				if len(ct) == 2 and ct[0] == "close":
					parse_match = True
					command_switch = "close"
					ticket_name = ct[1]
				if len(ct) == 2 and ct[0] == "attach":
					parse_match = True
					command_switch = "attach"
					user = ct[1]
					ticket_name = fstr_ticket_name
				if len(ct) == 2 and ct[0] == "remove":
					parse_match = True
					command_switch = "remove"
					ticket_name = ct[1]
				if len(ct) == 1 and ct[0] == "remove":
					parse_match = True
					command_switch = "remove"
					ticket_name = fstr_ticket_name
				if len(ct) == 2 and ct[0] == "amount":
					if not is_valid_number(ct[2]):
						self.PARENT.RETURN_CODE = "1249" # error Amount provided is not valid.
						return False
					parse_match = True
					command_switch = "amount"
					ticket_name = fstr_ticket_name
				if not parse_match:
					self.PARENT.RETURN_CODE = "1250" # error Invalid ticket command. Failed to parse.
					return False
				
				# Get the owner user id and metric account id.  We don't know for sure yet what 
				# tagged id we may need because we have to have ticket index first of owner.
				validation_result = self._name_validate_transactional(None,fstr_owner_name,user,fint_network_id)
				if not validation_result:
					# pass up error
					return False

				network_id = validation_result[0]
				source_account_id = validation_result[1]
				source_user = validation_result[3]
				source_ticket_index = get_or_insert_ticket_index(network_id,source_account_id,source_user.user_id)
				if not ticket_name in source_ticket_index["ticket_labels"]:
					self.PARENT.RETURN_CODE = "1251" # error Ticket name not in source index.
					return False
				# Do we need to modify a tagged account ticket index? Does it have a tag.
				ticket_name_index = source_ticket_index.ticket_data["ticket_labels"].index(ticket_name)
				target_ticket_index = None
				if source_ticket_index.ticket_data["ticket_tag_user_ids"][ticket_name_index] is None:
					# It is not tagged.
					# If trying to "attach", "user" was defined and passed to validation function
					if command_switch == "attach":
						target_account_id = validation_result[2]
						target_user = validation_result[4]
						target_ticket_index = get_or_insert_ticket_index(network_id,target_account_id,target_user.user_id)
						# Fail if target has too many tags already
						if target_ticket_index.ticket_data["tag_count"] > 19:
							self.PARENT.RETURN_CODE = "1252" # error Target already has too many ticket tags.
							return False
					# Fail if trying to remove.
					if command_switch == "remove":
						self.PARENT.RETURN_CODE = "1253" # error Ticket is not currently tagged to a user.  Nothing to remove.
						return False
				else:
					# It is tagged.
					# Fail if trying to attach another.
					if command_switch == "attach":
						self.PARENT.RETURN_CODE = "1254" # error Ticket already tagged to a user.
						return False
					# tagged user wasn't passed in, it is implied in source's ticket index
					target_account_id = source_ticket_index.ticket_data["ticket_tag_account_ids"][ticket_name_index]
					target_user_id = source_ticket_index.ticket_data["ticket_tag_user_ids"][ticket_name_index]
					target_ticket_index = get_or_insert_ticket_index(network_id,target_account_id,target_user_id)
					# find the tagged index for source ticket
					found_tagged_index = False
					for i in range(len(target_ticket_index["tag_network_ids"])):
						if not target_ticket_index.ticket_data["tag_network_ids"][i] == network_id:
							continue
						if not target_ticket_index.ticket_data["tag_account_ids"][i] == source_account_id:
							continue
						if not target_ticket_index.ticket_data["tag_labels"][i] == ticket_name:
							continue
						found_tagged_index = True
						tagged_index = i
						break							
					if not found_tagged_index:
						self.PARENT.RETURN_CODE = "1255" # error DATAERROR: Source ticket not in tagged user ticket index.
						return False
				
				# All checks/setup completed, ready to modify and save.
				if command_switch == "close":
					source_ticket_index.ticket_data["ticket_count"] -= 1
					del source_ticket_index.ticket_data["ticket_labels"][ticket_name_index]
					del source_ticket_index.ticket_data["ticket_amounts"][ticket_name_index]
					del source_ticket_index.ticket_data["ticket_memos"][ticket_name_index]
					del source_ticket_index.ticket_data["ticket_tag_network_ids"][ticket_name_index]
					del source_ticket_index.ticket_data["ticket_tag_account_ids"][ticket_name_index]
					del source_ticket_index.ticket_data["ticket_tag_user_ids"][ticket_name_index]
					if not target_ticket_index is None:
						target_ticket_index.ticket_data["tag_count"] -= 1
						del target_ticket_index.ticket_data["tag_labels"][tagged_index]
						del target_ticket_index.ticket_data["tag_amounts"][tagged_index]
						del target_ticket_index.ticket_data["tag_memos"][tagged_index]
						del target_ticket_index.ticket_data["tag_network_ids"][tagged_index]
						del target_ticket_index.ticket_data["tag_account_ids"][tagged_index]
						del target_ticket_index.ticket_data["tag_user_ids"][tagged_index]
						target_ticket_index.put()
					source_ticket_index.put()
					self.PARENT.RETURN_CODE = "7049" # success Ticket successfully closed.
					return True
				if command_switch == "amount":
					source_ticket_index.ticket_data["ticket_amounts"][ticket_name_index] = amount
					source_ticket_index.ticket_data["ticket_memos"][ticket_name_index] = memo
					if not target_ticket_index is None:
						target_ticket_index.ticket_data["tag_amounts"][tagged_index] = amount
						target_ticket_index.ticket_data["tag_memos"][tagged_index] = memo
						target_ticket_index.put()
					source_ticket_index.put()
					self.PARENT.RETURN_CODE = "7050" # success Ticket amount successfully changed.
					return True
				if command_switch == "remove":
					source_ticket_index.ticket_data["ticket_tag_network_ids"][ticket_name_index] = None
					source_ticket_index.ticket_data["ticket_tag_account_ids"][ticket_name_index] = None
					source_ticket_index.ticket_data["ticket_tag_user_ids"][ticket_name_index] = None
					target_ticket_index.ticket_data["tag_count"] -= 1
					del target_ticket_index.ticket_data["tag_labels"][tagged_index]
					del target_ticket_index.ticket_data["tag_amounts"][tagged_index]
					del target_ticket_index.ticket_data["tag_memos"][tagged_index]
					del target_ticket_index.ticket_data["tag_network_ids"][tagged_index]
					del target_ticket_index.ticket_data["tag_account_ids"][tagged_index]
					del target_ticket_index.ticket_data["tag_user_ids"][tagged_index]
					target_ticket_index.put()
					source_ticket_index.put()
					self.PARENT.RETURN_CODE = "7051" # success Ticket tag successfully removed.
					return True
				if command_switch == "attach":
					source_ticket_index.ticket_data["ticket_tag_network_ids"][ticket_name_index] = network_id
					source_ticket_index.ticket_data["ticket_tag_account_ids"][ticket_name_index] = target_account_id
					source_ticket_index.ticket_data["ticket_tag_user_ids"][ticket_name_index] = target_user.user_id
					target_ticket_index.ticket_data["tag_count"] += 1
					target_ticket_index.ticket_data["tag_labels"].append(ticket_name)
					target_ticket_index.ticket_data["tag_amounts"].append(source_ticket_index.ticket_data["ticket_amounts"][ticket_name_index])
					target_ticket_index.ticket_data["tag_memos"].append(source_ticket_index.ticket_data["ticket_memos"][ticket_name_index])
					target_ticket_index.ticket_data["tag_network_ids"].append(network_id)
					target_ticket_index.ticket_data["tag_account_ids"].append(source_account_id)
					target_ticket_index.ticket_data["tag_user_ids"].append(source_user.user_id)
					target_ticket_index.put()
					source_ticket_index.put()
					self.PARENT.RETURN_CODE = "7052" # success Ticket successfully closed.
					return True
		else:
			
			ticket_name = fstr_ticket_name
			# implement visitor commands
			# We will pass the visitor as the source to the validation function
			# since we want it to fail if the visitor is not the one executing
			# the command in these cases.  We will validate that the
			# owner owns the ticket.
			validation_result = self._name_validate_transactional(None,fstr_visitor_name,fstr_owner_name,fint_network_id)
			if not validation_result:
				# pass up error
				return False
			
			network_id = validation_result[0]
			visitor_account_id = validation_result[1]
			visitor_user = validation_result[3]
			visitor_ticket_index = get_or_insert_ticket_index(network_id,visitor_account_id,visitor_user.user_id)
			owner_account_id = validation_result[2]
			owner_user = validation_result[4]
			owner_ticket_index = get_or_insert_ticket_index(network_id,owner_account_id,owner_user.user_id)
			
			if not ticket_name in owner_ticket_index["ticket_labels"]:
				self.PARENT.RETURN_CODE = "1256" # error Ticket name not in owner index.
				return False
				
			# get the ticket name index from owner
			ticket_name_index = owner_ticket_index.ticket_data["ticket_labels"].index(ticket_name)
			# is this ticket tagged?
			tagged_index = None
			if owner_ticket_index.ticket_data["ticket_tag_network_ids"][ticket_name_index] is None:
				# it is not tagged
				# Fail if visitor trying to remove a tag
				if ct[0] == "remove":
					self.PARENT.RETURN_CODE = "1257" # error Ticket name not in owner index.
					return False
				
			else:
				# it is tagged
				# find the tagged index for source ticket
				found_tagged_index = False
				for i in range(len(visitor_ticket_index["tag_network_ids"])):
					if not visitor_ticket_index.ticket_data["tag_network_ids"][i] == network_id:
						continue
					if not visitor_ticket_index.ticket_data["tag_account_ids"][i] == owner_account_id:
						continue
					if not visitor_ticket_index.ticket_data["tag_labels"][i] == ticket_name:
						continue
					found_tagged_index = True
					tagged_index = i
					break							
				if not found_tagged_index:
					self.PARENT.RETURN_CODE = "1258" # error DATAERROR: Source ticket not in tagged user ticket index.
					return False
				if ct[0] == "remove" and len(ct) == 1:
					# we can handle remove functionality right here
					owner_ticket_index.ticket_data["ticket_tag_network_ids"][ticket_name_index] = None
					owner_ticket_index.ticket_data["ticket_tag_account_ids"][ticket_name_index] = None
					owner_ticket_index.ticket_data["ticket_tag_user_ids"][ticket_name_index] = None
					visitor_ticket_index.ticket_data["tag_count"] -= 1
					del visitor_ticket_index.ticket_data["tag_labels"][tagged_index]
					del visitor_ticket_index.ticket_data["tag_amounts"][tagged_index]
					del visitor_ticket_index.ticket_data["tag_memos"][tagged_index]
					del visitor_ticket_index.ticket_data["tag_network_ids"][tagged_index]
					del visitor_ticket_index.ticket_data["tag_account_ids"][tagged_index]
					del visitor_ticket_index.ticket_data["tag_user_ids"][tagged_index]
					owner_ticket_index.put()
					visitor_ticket_index.put()
					self.PARENT.RETURN_CODE = "7053" # success Ticket tag successfully removed.
					return True
				
			# only should have "pay" command now
			parse_match = False
			if len(ct) == 2 and ct[0] == "pay" and is_valid_number(ct[1]):
				parse_match = True
				# pay <amount>
			
			
			if len(ct) == 3 and ct[0] == "pay" and is_valid_number(ct[1]) and is_valid_number(ct[2]):
				parse_match = True
				# pay <amount> <plus gratuity as flat amount>
			
			
			if len(ct) == 3 and ct[0] == "pay" and is_valid_number(ct[1]) and is_valid_percent(ct[2]):
				parse_match = True
				# pay <amount> <plus gratuity as percentage of previous amount>
				
			if not parse_match:
				self.PARENT.RETURN_CODE = "1259" # error Invalid ticket command. Failed to parse.
				return False

			# error if payment amount doesn't match ticket amount
			if not amount == owner_ticket_index.ticket_data["ticket_amounts"][ticket_name_index]:
				self.PARENT.RETURN_CODE = "1260"
				return False # error Ticket pay fail. Payment amount must match ticket amount.

			# STEPS FOR PAYING A TICKET
			# 1. Visitor makes payment to owner.
			# 2. If tag exists we remove tag.

			pay_source_account_id = visitor_account_id		
			pay_target_account_id = owner_account_id		

			# make a payment
			# transfer network balance from one user to another
			# this does not affect our global balance counters

			# get the source and target metric accounts

			key_part1 = str(network_id).zfill(8)
			key_part2 = str(pay_source_account_id).zfill(12)
			key_part3 = str(pay_target_account_id).zfill(12)
			pay_source_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part2))
			lds_pay_source = pay_source_key.get()

			# error if source doesn't exist
			if lds_pay_source is None:
				self.PARENT.RETURN_CODE = "1261"
				return False # error Ticket pay fail. Visitor metric account failed to load.
			# error if trying to connect to self
			if pay_source_account_id == pay_target_account_id:
				self.PARENT.RETURN_CODE = "1262"
				return False # error Ticket pay fail. Source and Target are the same.  Can't pay self.

			pay_target_key = ndb.Key("ds_mr_metric_account", "%s%s" % (key_part1, key_part3))
			lds_pay_target = pay_target_key.get()

			# error if target doesn't exist
			if lds_pay_target is None:
				self.PARENT.RETURN_CODE = "1263"
				return False # error Ticket pay fail. Owner metric account failed to load.

			# Calculate the payment amount
			# Gratuity must be greater than zero.
			# Percent cannot be greater than 100.
			if not gratuity_amount is None:
				if not gratuity_amount > 0:
					self.PARENT.RETURN_CODE = "1264"
					return False # error Ticket pay fail. Cannot have negative gratuity amount.
				else:
					lint_amount = amount + gratuity_amount
			if not gratuity_percent is None:
				if float(gratuity_percent) <= 0:
					self.PARENT.RETURN_CODE = "1265"
					return False # error Ticket pay fail. Cannot have negative gratuity percent.
				
				if float(gratuity_percent) > 100:
					self.PARENT.RETURN_CODE = "1266"
					return False # error Ticket pay fail. Cannot have gratuity percent greater than 100.
					
				lint_amount = amount + (amount * float(gratuity_percent) / 100)
					
			# can't exceed maximum allowed payment
			if lint_amount > MAX_PAYMENT:
				self.PARENT.RETURN_CODE = "1267"
				return False # error Ticket pay fail. Payment amount exceeds maximum allowed.

			# STUB make sure all lint_amount inputs are greater than 0
			# can't pay if you don't have that much
			if lds_pay_source.current_network_balance < lint_amount:
				self.PARENT.RETURN_CODE = "1268"
				return False # error Ticket pay fail. Visitor does not have sufficient balance to pay.

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
			if lds_pay_source.current_timestamp > t_cutoff:

				# last transaction was in current time window, no need to swap
				# a.k.a. overwrite current
				lds_pay_source.current_network_balance -= lint_amount

			else:

				# last transaction was in previous time window, swap
				# a.k.a. move "old" current into "last" before overwriting
				lds_pay_source.last_connections = lds_pay_source.current_connections
				lds_pay_source.last_reserve_balance = lds_pay_source.current_reserve_balance
				lds_pay_source.last_network_balance = lds_pay_source.current_network_balance
				lds_pay_source.current_network_balance -= lint_amount				

			# update the target account
			if lds_pay_target.current_timestamp > t_cutoff:

				# last transaction was in current time window, no need to swap
				# a.k.a. overwrite current
				lds_pay_target.current_network_balance += lint_amount

			else:

				# last transaction was in previous time window, swap
				# a.k.a. move "old" current into "last" before overwriting
				lds_pay_target.last_connections = lds_pay_target.current_connections
				lds_pay_target.last_reserve_balance = lds_pay_target.current_reserve_balance
				lds_pay_target.last_network_balance = lds_pay_target.current_network_balance
				lds_pay_target.current_network_balance += lint_amount

			# only update current_timestamp for graph dependent transactions??? STUB
			lds_pay_source.current_timestamp = datetime.datetime.now()
			lds_pay_target.current_timestamp = datetime.datetime.now()

			# ADD TWO TRANSACTIONS LIKE CONNECT()
			lds_pay_source.tx_index += 1
			# source transaction log
			pay_source_tx_log_key = ndb.Key("ds_mr_tx_log", "MRTX2%s%s%s" % (key_part1, key_part2,str(lds_pay_source.tx_index).zfill(12)))
			pay_source_lds_tx_log = ds_mr_tx_log()
			pay_source_lds_tx_log.key = pay_source_tx_log_key
			# tx_index should be based on incremented metric_account value
			pay_source_lds_tx_log.tx_index = lds_pay_source.tx_index
			pay_source_lds_tx_log.tx_type = "TICKET PAYMENT MADE" # SHORT WORD(S) FOR WHAT TRANSACTION DID
			pay_source_lds_tx_log.memo = "Ticket paid to %s" % fstr_owner_name
			pay_source_lds_tx_log.category = "MRTX2"
			pay_source_lds_tx_log.amount = lint_amount
			pay_source_lds_tx_log.current_network_balance = lds_pay_source.current_network_balance
			pay_source_lds_tx_log.current_reserve_balance = lds_pay_source.current_reserve_balance
			pay_source_lds_tx_log.memo = source_ticket_index.ticket_data["ticket_memos"][ticket_name_index]
			pay_source_lds_tx_log.access = "PRIVATE" # "PUBLIC" OR "PRIVATE"
			pay_source_lds_tx_log.description = "Ticket payment made for ticket name: %s" % ticket_name 
			pay_source_lds_tx_log.user_id_created = lds_pay_source.user_id
			pay_source_lds_tx_log.network_id = network_id
			pay_source_lds_tx_log.account_id = pay_source_account_id
			pay_source_lds_tx_log.source_account = pay_source_account_id 
			pay_source_lds_tx_log.target_account = pay_target_account_id
			pay_source_lds_tx_log.put()

			lds_pay_target.tx_index += 1
			# target transaction log
			pay_target_tx_log_key = ndb.Key("ds_mr_tx_log", "MRTX2%s%s%s" % (key_part1, key_part3,str(lds_pay_target.tx_index).zfill(12)))
			pay_target_lds_tx_log = ds_mr_tx_log()
			pay_target_lds_tx_log.key = pay_target_tx_log_key
			# tx_index should be based on incremented metric_account value
			pay_target_lds_tx_log.tx_index = lds_pay_target.tx_index
			pay_target_lds_tx_log.tx_type = "TICKET PAYMENT RECEIVED" # SHORT WORD(S) FOR WHAT TRANSACTION DID
			pay_target_lds_tx_log.memo = "Ticket paid from %s" % fstr_visitor_name
			pay_target_lds_tx_log.category = "MRTX2"
			pay_target_lds_tx_log.amount = lint_amount
			pay_target_lds_tx_log.current_network_balance = lds_pay_target.current_network_balance
			pay_target_lds_tx_log.current_reserve_balance = lds_pay_target.current_reserve_balance
			# typically we'll make target private for bilateral transactions so that
			# when looking at a system view, we don't see duplicates.
			pay_target_lds_tx_log.access = "PRIVATE" # "PUBLIC" OR "PRIVATE"
			pay_target_lds_tx_log.description = "Ticket payment received for ticket name: %s Memo: %s" % (ticket_name,source_ticket_index.ticket_data["ticket_memos"][ticket_name_index])
			pay_target_lds_tx_log.user_id_created = lds_pay_source.user_id
			pay_target_lds_tx_log.network_id = network_id
			pay_target_lds_tx_log.account_id = pay_target_account_id
			pay_target_lds_tx_log.source_account = pay_source_account_id 
			pay_target_lds_tx_log.target_account = pay_target_account_id
			pay_target_lds_tx_log.put()

			if not tagged_index is None:
				# only change we make automatically to paid tickets is to remove the tag
				owner_ticket_index.ticket_data["ticket_tag_network_ids"][ticket_name_index] = None
				owner_ticket_index.ticket_data["ticket_tag_account_ids"][ticket_name_index] = None
				owner_ticket_index.ticket_data["ticket_tag_user_ids"][ticket_name_index] = None
				visitor_ticket_index.ticket_data["tag_count"] -= 1
				del visitor_ticket_index.ticket_data["tag_labels"][tagged_index]
				del visitor_ticket_index.ticket_data["tag_amounts"][tagged_index]
				del visitor_ticket_index.ticket_data["tag_memos"][tagged_index]
				del visitor_ticket_index.ticket_data["tag_network_ids"][tagged_index]
				del visitor_ticket_index.ticket_data["tag_account_ids"][tagged_index]
				del visitor_ticket_index.ticket_data["tag_user_ids"][tagged_index]
				owner_ticket_index.put()
				visitor_ticket_index.put()
			lds_pay_source.put()
			lds_pay_target.put()
			self.PARENT.RETURN_CODE = "7054" # success Ticket payment succeeded.
			return True	
				
				
































	def _multi_graph_process(self):
	
		# So...we meet again.
		
		# Each NETWORK!!! has a process lock. Network, not application
				
		# first get the cutoff time
		# It is from the cutoff time that we derive the entity key/id
		# for the profile.  
		t_now = datetime.datetime.now()
		d_since = t_now - T_EPOCH
		t_cutoff = t_now - datetime.timedelta(seconds=(d_since.total_seconds() % (GRAPH_FREQUENCY_MINUTES * 60)))
		# make a nice string to serve as our key "YYYYMMDDHHMM"
		current_time_key = "%s%s%s%s%s" % (str(t_cutoff.year),
			str(t_cutoff.month).zfill(2),
			str(t_cutoff.day).zfill(2),
			str(t_cutoff.hour).zfill(2),
			str(t_cutoff.minute).zfill(2))

		# get or insert the multi-graph_process profile
		multi_gp_key = ndb.Key("ds_multi_mrgp_profile","master")
		multi_gp_entity = multi_gp_key.get()
		if multi_gp_entity is None:
			multi_gp_entity = ds_multi_mrgp_profile()
			multi_gp_entity.key = multi_gp_key
			multi_gp_entity.current_time_key = current_time_key
			multi_gp_entity.current_status = "UNFINISHED"
			multi_gp_entity.network_index = 1
			multi_gp_entity.put()
			
		if multi_gp_entity.current_time_key == current_time_key:
			if multi_gp_entity.current_status = "FINISHED":
				# nothing to do right now
				return
		else:
			# crossed the time window, need to restart
			multi_gp_entity.current_time_key = current_time_key
			multi_gp_entity.current_status = "UNFINISHED"
			multi_gp_entity.network_index = 1	
		
		deadline_seconds_away = (GRAPH_ITERATION_DURATION_SECONDS + 
			GRAPH_ITERATION_WIGGLE_ROOM_SECONDS)

		deadline = t_now + datetime.timedelta(seconds=deadline_seconds_away)

		while t_now < deadline:
		
			result_status, result_profile = self._process_graph(network_id, current_time_key, deadline)
			
			
			t_now = datetime.datetime.now()


	def _process_graph(self, fint_network_id, fstr_current_time_key):
	
		profile_key_time_part = fstr_current_time_key
			
		# We use a transactional timelock mechanism to make sure one
		# and only one process is processing each specific window
		# of time, for each specific network id.
		
		profile_key_network_part = str(fint_network_id).zfill(8)
		
		""" 
		**************************************************
		**************************************************
		
		LOCAL FUNCTION: process_lock()
		
		**************************************************
		**************************************************
		"""
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
					else: return "PROCESS LOCKED", profile
						
				if profile.status == "FINISHED":
				
					if not REDO_FINISHED_GRAPH_PROCESS:
						return "PROCESS FINISHED FOR CURRENT TIMEFRAME", profile
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
				# Chunk counters are used to track 
				# if we should overwrite when restarting
				# a previous graph process.
				profile.staging_chunk_counter = 0
				profile.index_chunk_counter = 0
				profile.tree_chunk_counter = 0
				profile.map_chunk_counter = 0
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
				profile.report['TOTAL_TREES'] = 0
				profile.report['PARENT_LEVEL'] = 1 # Level Parent
				profile.report['PARENT_LEVEL_IDX'] = 0 # Level Parent Index
				profile.report['CHILD_LEVEL_IDX'] = 0 # Level Parent Index
		
			profile.status = "IN PROCESS"
			deadline_seconds_away = (GRAPH_ITERATION_DURATION_SECONDS + 
						GRAPH_ITERATION_WIGGLE_ROOM_SECONDS)
			profile.deadline = t_now + datetime.timedelta(seconds=deadline_seconds_away)
			profile.put()
			return "GOT THE LOCK", profile
						
		result_status, result_profile = process_lock()
		
		# If we didn't get the lock, we're done.
		if not result_status == "GOT THE LOCK": return result_status, result_profile
		
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
		""" 
		**************************************************
		**************************************************
		
		LOCAL FUNCTION: get_chunk_from_juggler()
		
		**************************************************
		**************************************************
		"""
		def get_chunk_from_juggler(fstr_type,fint_index,fbool_new=False):
		
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
				# overwrite if new process, don't even try to retrieve
				if fint_index > profile.index_chunk_counter: index_chunk_member = index_chunk_key.get()
				if index_chunk_member is None:
					index_chunk_member = ds_mrgp_index_chunk()
					index_chunk_member.key = index_chunk_key
					# Load our generic chunk or create so
					# that we don't have to wait for a 100,000
					# list loop to happen. If this is first time
					# ever, create the generic index.
					generic_index_key = ndb.Key("ds_mrgp_index_chunk","GENERIC_INDEX_CHUNK_500_THOUSAND_FALSES_LIST")
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
					profile.index_chunk_counter += 1
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
				# overwrite if new process, don't even try to retrieve
				if fint_index > profile.tree_chunk_counter: tree_chunk_member = tree_chunk_key.get()
				# if the chunk we're trying to get doesn't exist, create it
				if tree_chunk_member is None:
					tree_chunk_member = ds_mrgp_tree_chunk()
					tree_chunk_member.key = tree_chunk_key
					tree_chunk_member.stuff = {}
					tree_chunk_member.stuff[1] = []
					# we had to create this tree chunk
					# make sure juggler knows it needs to save it later
					juggler_to_put[juggler_key] = True
					profile.tree_chunk_counter += 1
					if profile.tree_chunks < fint_index:
						profile.tree_chunks = fint_index
				# create a reference in the juggler
				juggler[juggler_key] = tree_chunk_member
				return tree_chunk_member

			if fstr_type == "map":
			
				# first see if it's already in the juggler
				juggler_key = ("%s_%s" % (fstr_type, str(fint_index)))
				if juggler_key in juggler: return juggler[juggler_key]
				# not there, get or create
				key_part1 = profile_key_network_part
				key_part2 = profile_key_time_part
				key_part3 = str(fint_index).zfill(12)
				map_chunk_key = ndb.Key("ds_mrgp_map_chunk","%s%s%s" % (key_part1, key_part2, key_part3))
				# overwrite if new process, don't even try to retrieve
				if fint_index > profile.map_chunk_counter: map_chunk_member = map_chunk_key.get()
				if map_chunk_member is None:
					map_chunk_member = ds_mrgp_map_chunk()
					map_chunk_member.key = map_chunk_key
					# Load our generic chunk or create so
					# that we don't have to wait for a 150,000
					# list loop to happen. If this is first time
					# ever, create the generic index.
					generic_map_key = ndb.Key("ds_mrgp_index_chunk","GENERIC_MAP_CHUNK_150_THOUSAND_0_LIST")
					generic_map_chunk = generic_map_key.get()
					if generic_map_chunk is None:
						t_list = []
						for i in range(1,150001):
							t_list.append(0)
						generic_map_chunk = ds_mrgp_map_chunk()
						generic_map_chunk.stuff = t_list
						generic_map_chunk.key = generic_map_key
						generic_map_chunk.put()					
					map_chunk_member.stuff = generic_map_chunk.stuff
					# we had to create this index chunk
					# make sure juggler knows it needs to save it later
					juggler_to_put[juggler_key] = True
					profile.map_chunk_counter += 1
				# create a reference in the juggler
				juggler[juggler_key] = map_chunk_member
				return map_chunk_member

		""" 
		**************************************************
		**************************************************
		
		LOCAL FUNCTION: tell_juggler_modified()
		
		**************************************************
		**************************************************
		"""
		def tell_juggler_modified(fstr_type,fint_index):
			
			juggler_key = ("%s_%s" % (fstr_type, str(fint_index)))
			if not juggler_key in juggler_to_put:
				juggler_to_put[juggler_key] = True
			return None

		""" 
		**************************************************
		**************************************************
		
		LOCAL FUNCTION: do_juggler_puts()
		
		**************************************************
		**************************************************
		"""
		@ndb.transactional(xg=True)
		def do_juggler_puts():
		
			# always put() the profile
			profile.put()
			# every chunk object should have a reference in the juggler
			for juggler_to_put_key in juggler_to_put:
				juggler[juggler_to_put_key].put()
				del juggler_to_put[juggler_to_put_key]

		""" 
		**************************************************
		**************************************************
		
		LOCAL FUNCTION: process_stop()
		
		**************************************************
		**************************************************
		"""	
		def process_stop(fbool_is_finished=False):
			if fbool_is_finished:
				profile.status = "FINISHED"
			else:
				profile.status = "PAUSED"		
			do_juggler_puts()
			
			@ndb.transactional
			def final_save_for_network_profile():
				network_key = ndb.Key("ds_mr_network_profile", "%s" % str(fint_network_id).zfill(8))
				network_profile = network_key.get()
				network_profile.orphan_count = profile.report['ORPHAN_MEMBER_TOTAL']
				network_profile.total_trees = profile.report['TOTAL_TREES']
				network_profile.last_graph_process = profile_key_time_part
				network_profile.put()
			
		""" 
		**************************************************
		**************************************************
		
		LOCAL FUNCTION: deadline_reached()
		
		**************************************************
		**************************************************
		"""
		lint_deadline_compute_factor = 0
		def deadline_reached(fbool_use_compute_factor=False):
			# If the compute factor is > 1000 then we do a check, otherwise
			# wait until it is.
			if fbool_use_compute_factor:
				if lint_deadline_compute_factor > 1000:
					lint_deadline_compute_factor = 0
				else:
					return False
			# If we've passed the deadline do our puts
			if datetime.datetime.now() > process.deadline:
				do_juggler_puts()
				return True
			else:
				# else do our puts if 10 or more entites in juggler put
				if len(juggler_to_put) > 9:
					do_juggler_puts()
				return False
			
		
		""" 
		--------------------------------------------------------
		--------------------------------------------------------
		--------------------------------------------------------
		
		PHASE 1: CREATE THE STAGING CHUNKS FROM ACCOUNTS
		
		--------------------------------------------------------
		--------------------------------------------------------
		--------------------------------------------------------
		"""
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
				# quit if no accounts yet
				if profile.max_account == 0: return process_stop(True)
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
					this_staging_chunk.stuff = chunk_stuff
					this_staging_chunk.put()
					profile.staging_chunk_counter += 1
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
		
		""" 
		--------------------------------------------------------
		--------------------------------------------------------
		--------------------------------------------------------
		
		PHASE 2: BUILD THE TREE CHUNKS FROM CONNECTIONS
		
		--------------------------------------------------------
		--------------------------------------------------------
		--------------------------------------------------------
		"""
		
		""" 
		**************************************************
		**************************************************

		PHASE 2 FUNCTION: phz2_get_acct_fsc()

		**************************************************
		**************************************************
		"""
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

		""" 
		**************************************************
		**************************************************

		PHASE 2 FUNCTION: phz2_acct_in_idx()

		**************************************************
		**************************************************
		"""
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
				# *** INDEX CHUNK MODIFICATION ***
				tell_juggler_modified("index",lint_index_chunk_id)
				return False		 			
		""" 
		**************************************************
		**************************************************

		PHASE 2 FUNCTION: phz2_chk_chnk_sz()

		**************************************************
		**************************************************
		"""
		# tree process function helper #3
		# see if our tree chunk is too big and we need to spawn another
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
				profile.child_pointer += 1
				if profile.tree_in_process:
					# Before we abandon the previous tree chunk, we need to leave
					# a breadcrumb, so the parent knows when to leap to the next
					# tree chunk.  Place an 'X' where the next entity info would
					# have been.
					child_chunk.stuff[profile.tree_cursor][temp_LP + 1].append('X')
					# *** TREE CHUNK MODIFICATION ***
					tell_juggler_modified("tree",profile.child_pointer - 1)
					# Now change reference for "child" to new chunk.
					child_chunk = get_chunk_from_juggler("tree",profile.child_pointer,True)
					# Overwrite the default header info with current tree info.
					child_chunk.stuff[profile.tree_cursor] = {}
					# *** TREE CHUNK MODIFICATION ***
					tell_juggler_modified("tree",profile.child_pointer)
				else:
					# We must have filled up from orphans
					# Defaults will suffice, since not working on a tree at the moment.
					child_chunk = get_chunk_from_juggler("tree",profile.child_pointer,True)
				return None
			return None
		
		# PHASE 2 DESCRIPTION:
		#
		# we have queried all the accounts in the network and they
		# now reside in staging chunks of 2500 accounts each. In
		# Phase 2 we build the tree hierarchy which creates a proof
		# as to which sets of accounts have a "path" between them.
		#
		# I call each set a "tree".  The most populated tree is 
		# assumed to be the main network.  The other trees are 
		# considered off the main network.  An account with no 
		# connections is called an "orphan".  
		#
		# key [1] in the staging chunk for each account is reserved
		# for the "tree" value.  1 = orphan.  While building the 
		# tree chunks we start with 2 and increment.
		#
		# Really, this is going to be the slowest part of the algorithm.
		# This phase specifically, as we're accessing essne
		# It's my hope that with 1,000,000 nodes, perhaps the use of 
		# memcache and devoting sufficient RAM in GAE deployments will
		# suffice and still allow the app to exist as a web application
		# without using backends.
		
		# Network could have all deleted accounts and still have gotten
		# to this point.  Make sure the staging chunk counter actually
		# had an active account to where at least one staging chunk was
		# actually created before proceeding.
		if profile.staging_chunk_counter == 0: return process_stop(True)
		
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
			parent_chunk = get_chunk_from_juggler("tree",profile.parent_pointer,lbool_new)
			# For small networks, they will always be the same
			# For a large tree they may diverge in which tree 
			# chunk they are pointing at
			if profile.parent_pointer == profile.child_pointer:
				child_chunk = get_chunk_from_juggler("tree",profile.child_pointer,lbool_new)
			else:
				child_chunk = parent_chunk
				
			# Our tree_cursor tracks which tree we are on
			if profile.tree_cursor == 0:
				profile.tree_cursor = 1
			# Our count_cursor tracks which account_id we start new trees on
			if profile.count_cursor == 0:
				profile.count_cursor = 1
			# used by chunk creator function phz2_chk_chnk_sz()
			lint_tree_chunk_size_factor = 0
			
			# PHASE 2 PART 3
			# our staging chunk(s) is/are ready
			# our index chunk(s) is/are ready
			# our tree chunk(s) is/are ready
			# 
			# we are ready to enter our main tree process loop
			# let's define the functions it uses first		

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
						parent_chunk = get_chunk_from_juggler("tree",profile.parent_pointer)
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
							# *** TREE CHUNK MODIFICATION ***
							tell_juggler_modified("tree",profile.child_pointer)
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
							# *** TREE CHUNK MODIFICATION ***
							tell_juggler_modified("tree",profile.child_pointer)
							lint_tree_chunk_size_factor += 1
							profile.report['ORPHAN_RESERVE_AMT_TOTAL'] += lresult[5]
							profile.report['ORPHAN_NETWORK_AMT_TOTAL'] += lresult[4]
							profile.report['ORPHAN_MEMBER_TOTAL'] += 1
					
						else:
							# has connections
							# add seed to dict and start tree
							profile.tree_cursor += 1
							profile.report["TOTAL_TREES"] += 1
							child_chunk.stuff[profile.tree_cursor] = {}
							# make level one this new seed
							child_chunk.stuff[profile.tree_cursor][1] = []
							child_chunk.stuff[profile.tree_cursor][-1] = []
							# put the new account seed in level 1 sequence
							child_chunk.stuff[profile.tree_cursor][1].append(lresult)
							child_chunk.stuff[profile.tree_cursor][-1].append(profile.count_cursor)
							# *** TREE CHUNK MODIFICATION ***
							tell_juggler_modified("tree",profile.child_pointer)
							profile.tree_in_process = True
							lint_tree_chunk_size_factor += 10						
					if profile.count_cursor == profile.max_account:
						# we're done with phase 2
						profile.phase_cursor = 3
						if deadline_reached(): return process_stop()
						break
					else:
						profile.count_cursor += 1
						lint_deadline_compute_factor += 1
						continue

		""" 
		--------------------------------------------------------
		--------------------------------------------------------
		--------------------------------------------------------
		
		PHASE 3: DO RESERVE EVENING ON TREE CHUNKS
		
		--------------------------------------------------------
		--------------------------------------------------------
		--------------------------------------------------------
		"""
		
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
							# *** TREE CHUNK MODIFICATION ***
							tell_juggler_modified("tree",profile.child_pointer)
							# *** TREE CHUNK MODIFICATION ***
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
									# *** TREE CHUNK MODIFICATION ***
									tell_juggler_modified("tree",profile.child_pointer)
									# *** TREE CHUNK MODIFICATION ***
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
							profile.count_cursor = 0
							break
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


		""" 
		--------------------------------------------------------
		--------------------------------------------------------
		--------------------------------------------------------
		
		PHASE 4: CREATE MAP CHUNKS FROM IDS TO TREE RESULTS
		
		--------------------------------------------------------
		--------------------------------------------------------
		--------------------------------------------------------
		"""
		
		if profile.phase_cursor == 4:
		
			# Create a map index, that points account ids implicitly to tree chunks
			# so when users load there account, there's a way to point at tree data.

			# how many maps to query/create?
			# one for every 150,000 accounts
			t_num = ((profile.max_account - (profile.max_account % 150000)) / 150000) + 1			
			# initialize map chunks if not already done
			if not profile.map_chunk_counter == t_num:
				for i in range(profile.map_chunk_counter + 1,t_num + 1):
					index_chunk[i] = get_chunk_from_juggler("map",i)
					if deadline_reached(True): return process_stop()

			def scan_tree_chunk_for_ids(fint_chunk_id, fint_start_marker):
			
				ldict_blocked_ids = {}
				tree_chunk = get_chunk_from_juggler("tree",fint_chunk_id)
				raw_list = []
				for tree_key in tree_chunk.stuff:
					# Ignore orphans, map default value is orphan.
					# Also, ignore blocks we've already processed.
					if tree_key == 1: continue
					for level_key in tree_chunk.stuff[tree_key]:
						if level_key < 0:
							for i in range(len(tree_chunk.stuff[tree_key][level_key])):
								account_id = tree_chunk.stuff[tree_key][level_key][i]
								raw_list.append(account_id)
				raw_list.sort()
				marker = (fint_start_marker * 150000) + 150000
				map_chunk_id = 1
				for account_id in raw_list:
					if account_id <= marker:
						if ldict_blocked_ids.get(map_chunk_id) is None:
							ldict_blocked_ids[map_chunk_id] = []
						ldict_blocked_ids[map_chunk_id].append(account_id)							
					else:
						marker = marker + 150000
						map_chunk_id = map_chunk_id + 1				
				return ldict_blocked_ids
				
			while True:
			
				# Use ***profile.child_pointer*** for position.
				# It should have been set to 1 after phase 3.
				# ***profile.tree_chunks*** was incremented each time
				# ...a tree chunk was created so that tells us
				# ...when to stop.
				# We will use ***profile.count_cursor*** to tell us 
				# which map chunk we are currently updating. So
				# it's fine if we don't finish a complete tree
				# chunk in one iteration.  We will at least finish
				# one map chunk for whatever id's for the current
				# tree chunk were assigned to that map chunk.
				
				# get our blocked ids
				ldict_blocked_ids = scan_tree_chunk_for_ids(profile.child_pointer,profile.count_cursor)
				
				for block_key in ldict_blocked_ids:			
					if deadline_reached(True): return process_stop()
					# This if statement below allows the process to stop
					# in the middle of processing this chunk.  If
					# we stop, the profile.count_cursor will still
					# be set to where the correct block_key gets 
					# done first.
					if block_key < profile.count_cursor: continue
					map_chunk = get_chunk_from_juggler("map",block_key,lbool_new)
					# loop through accounts in this block of ids
					for account_id in ldict_blocked_ids[block_key]:
						# set account position in map chunk to tree value
						# *** MAP CHUNK MODIFICATION ***
						map_chunk.stuff[(account_id % 150000) - 1] = profile.child_pointer
						tell_juggler_modified("map",block_key)
					# make the profile.count_cursor the current block key
					profile.count_cursor = block_key
					
				profile.child_pointer += 1
				if profile.child_pointer > profile.tree_chunks:
					# We're done, completely.
					process_stop(True)
				else:
					# keep going
					profile.count_cursor = 0					

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

# page handler class for command based pages
class ph_command(webapp2.RequestHandler):

	# command
	# 
	# This "command" pattern I've chosen is basically a command line/
	# web page hybrid.  Tried to make it as "REST"y as possible for 
	# simplicity.  Every page that uses it comes in as a GET or a POST.
	# The GET requests use the "context", which is the url path and 
	# query string key/values, as the means to decide what to display.
	# Whereas, the POST requests use the command text to decide what
	# to "do" and the "context" can be a requirement, or unnecessary.
	# 
	# If the user hits the submit button with no command in it, it
	# simply turns the request into a redirect back to itself (refresh).
	# In fact the FORM action always targets the current path/context
	# but a command could have a different context target implied.
	#
	# For instance you could be on the home page (root context) and 
	# then directly type the command "pay bob 3.50" then the command
	# (assuming you are logged in and you and bob share a network)
	# would automatically target the context 
	# "/network/account?netid=mynetwork&accid=bob"
	
	def get_pqc(self):
	
		# Context is important in the pattern I've chosen.  Since I'm
		# trying to cram all the functions into a nice list in the form
		# of a if/elif/elif case/select type statement I need to have
		# another variable which condenses the context.  Sometimes we're
		# operating on a network object, sometimes an account on that
		# network, sometimes someone elses account on that network.  Or
		# perhaps even a shopping cart, on someone elses account on a
		# network that we're not even on.  So instead of checking context
		# for each function we'll just assign an integer for the command
		# functions to check against that we'll define here.
		#
		# pqc[] = "Path/Query Context object"
		# pqc[0] = identifier
		# pqc[1-n] = relevant query values for that id
		
		result = []		

		if self.master.PATH_CONTEXT == "root/tickets" and "vn" in self.master.request.GET and "va" in self.master.request.GET:
			# view all tickets
			result.append(100)
			result.append(self.master.request.GET["vn"])
			result.append(self.master.request.GET["va"])
		if self.master.PATH_CONTEXT == "root/tickets" and "vn" in self.master.request.GET and "va" in self.master.request.GET and "vt" in self.master.request.GET:
			# view specific ticket
			result.append(110)
			result.append(self.master.request.GET["vn"])
			result.append(self.master.request.GET["va"])
			result.append(self.master.request.GET["vt"])
		if self.master.PATH_CONTEXT == "root/ledger" and "vn" in self.master.request.GET and "va" in self.master.request.GET:
			# view specific account ledger
			result.append(90)
			result.append(self.master.request.GET["vn"])
			result.append(self.master.request.GET["va"])
		if self.master.PATH_CONTEXT == "root/network" and "vn" in self.master.request.GET and "va" in self.master.request.GET:
			# view specific account
			result.append(80)
			result.append(self.master.request.GET["vn"])
			result.append(self.master.request.GET["va"])
		if self.master.PATH_CONTEXT == "root/network" and "vn" in self.master.request.GET:
			# view specific network
			result.append(10)
			result.append(self.master.request.GET["vn"])
		if self.master.PATH_CONTEXT == "root/network":
			# view all networks
			result.append(20)
		if self.master.PATH_CONTEXT == "root" and "view_menu" in self.master.request.GET:
			# view root menu
			result.append(30)
		if self.master.PATH_CONTEXT == "root":
			# home page
			result.append(40)
		if self.master.PATH_CONTEXT == "root/profile" and "va" in self.master.request.GET:
			# viewing someone else's profile
			result.append(50)
			result.append(self.master.request.GET["va"])
		if self.master.PATH_CONTEXT == "root/profile":
			# viewing users own profile
			result.append(60)
		if self.master.PATH_CONTEXT == "root/messages" and "channel" in self.master.request.GET:
			# messages page
			result.append(70)
			result.append(self.master.request.GET["channel"])
					
		return result
	
	def is_valid_name(self,fstr_name):
	
		# a valid name is comprised of re.match(r'^[a-z0-9_]+$',fstr_name)
		# so only a-z, 0-9, or an underscore
		# additionally:
		# 1. Can't end or begin with an underscore
		# 2. Can't be less than three characters
		# 3. Must contain at least one letter.
		# 4. If 10 or less in length, must contain at lease one
		# number and at least one letternumber as keywords 
		# reserve the 10 or less space without numbers
		# or underscores.
		if not re.match(r'^[a-z0-9_]+$',fstr_name):
			return False
		if not re.search('[a-z]',fstr_name):
			return False
		if not len(fstr_name) > 2:
			return False
		if fstr_name[:1] == "_" or fstr_name[-1:] == "_":
			return False
		if len(fstr_name) < 11 and not re.search('[0-9]',fstr_name):
			return False
		return True
	
	def url_path(self,new_vars=None,new_path=None,error_code=None,confirm_code=None,success_code=None):

		
		if not error_code is None:
			path_part = self.master.request.path
			if new_vars is None: new_vars = {}
			new_vars["xerror_code"] = error_code
			new_vars["xlast_view"] = urllib.quote_plus(self.master.request.path_qs)
		elif not confirm_code is None:
			path_part = self.master.request.path
			if new_vars is None: new_vars = {}
			new_vars["xconfirm_code"] = confirm_code
		elif not success_code is None:
			path_part = self.master.request.path
			if new_vars is None: new_vars = {}
			new_vars["xsuccess_code"] = success_code
		else:
			if new_vars is None:
				if new_path is None:
					return self.master.request.path_qs
				else:
					# If we're sending to new path we
					# don't use old query string.
					return new_path
			else:
				if new_path is None:
					path_part = self.master.request.path_qs
				else:
					path_part = new_path

		if "?" not in path_part:
			path_string = path_part + "?"
		else:
			path_string = path_part + "&"
		if isinstance(new_vars, dict):
			for key in new_vars:
				path_string += key + "=" + urllib.quote_plus(str(new_vars[key])) + "&"
			if path_string.endswith("&"): path_string = path_string[:-1]
		else:
			# we assume a string was passed like 'queryvar=queryvalue'
			path_string += new_vars			
		return path_string	
		
	def get_text_for(self,marker_word,command_text):
	
		# Commands we split() into a list, but if this was a command
		# intended to submit raw text like a bio, description, or 
		# message, we need to reparse it to get our raw text.  This 
		# function basically says, "give me everything after 'marker_word'
		# as a string".
		end_of_marker_word = command_text.index(marker_word) + len(marker_word)
		return command_text[end_of_marker_word:].strip()		

	def get_label_for_account(self,user_obj,network_id,account_id,fstr_type):		
		if fstr_type == "RESERVE":
			for i in range(len(user_obj.reserve_network_ids)):
				if user_obj.reserve_network_ids[i] == network_id:
					if user_obj.reserve_account_ids[i] == account_id:
						return user_obj.reserve_labels[i]
		if fstr_type == "CLIENT":
			for i in range(len(user_obj.client_network_ids)):
				if user_obj.client_network_ids[i] == network_id:
					if user_obj.client_account_ids[i] == account_id:
						return user_obj.client_labels[i]
		if fstr_type == "JOINT":
			for i in range(len(user_obj.joint_network_ids)):
				if user_obj.joint_network_ids[i] == network_id:
					if user_obj.joint_account_ids[i] == account_id:
						return user_obj.joint_labels[i]
		if fstr_type == "CLONE":
			for i in range(len(user_obj.clone_network_ids)):
				if user_obj.clone_network_ids[i] == network_id:
					if user_obj.clone_account_ids[i] == account_id:
						return user_obj.clone_labels[i]

	def get_formatted_amount(self,network,account,raw_amount):

		return "{:28,.2f}".format(round(Decimal(raw_amount) / Decimal(network.skintillionths), account.decimal_places))
			
	def get(self):
		
		# Instantiate the master object, do security and other app checks. If
		# there's an interruption return from this function without processing
		# further.
		lobj_master = master(self,"get","unsecured")
		self.master = lobj_master
		r = lobj_master.request_handler
		if lobj_master.IS_INTERRUPTED:return
		
		# get the context
		lobj_master.PATH_CONTEXT = ("root/" + lobj_master.request.path.strip("/")).strip("/")
		# make the menu link href
		lobj_master.MENU_LINK = self.url_path(new_vars="view_menu=1",new_path="/")
		lobj_master.TRACE.append("self.PATH_CONTEXT = %s" % lobj_master.PATH_CONTEXT)
		
		lobj_master.TRACE.append("ph_command.get(): in ph_command GET function")
		
		# get path/query context
		pqc = self.get_pqc()
		
		# create shorter references to our objects
		lobj_master.bloks = []
		lobj_master.page = {}
		context = lobj_master.PATH_CONTEXT
		bloks = lobj_master.bloks
		page = lobj_master.page
		if lobj_master.user.IS_LOGGED_IN:
			page["username"] = lobj_master.user.entity.username
		else:
			# if running locally in development show a made-up IP
			if lobj_master.request.host[:9] == "localhost":
				page["username"] = "127.0.0.1"			
			else:
				page["username"] = lobj_master.request.remote_addr
				
		page["context"] = "CONTEXT: (<b>%s</b>) AS: (<b>%s</b>)" % (context,page["username"])

		# use while loop as case statement
		# break out when we select a case
		while True:
		
			###################################
			# TEST BLOCK PROCESS
			###################################

			# first check our error/success/confirm requests
			if "test_code" in lobj_master.request.GET:
				page["title"] = "TEST"
				blok = {}
				blok["type"] = "test"
				blok["test_code"] = lobj_master.request.GET["test_code"]
				bloks.append(blok)	
				break

			###################################
			# ERROR PROCESS
			###################################

			# first check our error/success/confirm requests
			if "xerror_code" in lobj_master.request.GET:
				page["title"] = "ERROR"
				blok = {}
				blok["type"] = "error"
				blok["error_code"] = lobj_master.request.GET["xerror_code"]
				blok["last_view_link"] = urllib.unquote(lobj_master.request.GET["xlast_view"])
				blok["last_view_link_text"] = "Link to last View"
				bloks.append(blok)	
				break		

			###################################
			# CONFIRM PROCESS
			###################################

			if "xconfirm_code" in lobj_master.request.GET:
				page["title"] = "CONFIRM"
				blok = {}
				blok["type"] = "confirm"
				blok["confirm_code"] = lobj_master.request.GET["xconfirm_code"]
				blok["form_hidden_command_text"] = urllib.unquote(lobj_master.request.GET["xct"])
				bloks.append(blok)	
				break	

			###################################
			# SUCCESS PROCESS
			###################################

			if "xsuccess_code" in lobj_master.request.GET:
				page["title"] = "SUCCESS"
				blok = {}
				blok["type"] = "success"
				blok["success_code"] = lobj_master.request.GET["xsuccess_code"]
				bloks.append(blok)	
				break	

			###################################
			# CONTEXT/VIEW PROCESS
			###################################

			# make bloks from context
			if pqc[0] == 110:
			
				# one ticket
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				page["title"] = "TICKET"
				blok["type"] = "one ticket"
				blok["ticket"] = lobj_master.metric._view_tickets(pqc[1],pqc[2],pqc[3])
				if not blok["ticket"]:
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				bloks.append(blok)
				break
				
			if pqc[0] == 100:
			
				# all tickets
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				page["title"] = "TICKETS"
				blok["type"] = "all tickets"
				if "tp" in lobj_master.request.GET:
					ticket_page = lobj_master.request.GET["tp"]
				else:
					ticket_page = 1
				blok["tickets"] = lobj_master.metric._view_tickets(pqc[1],pqc[2],fpage=ticket_page)
				if not blok["tickets"]:
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				bloks.append(blok)
				break
			
			if pqc[0] == 90:
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				page["title"] = "VIEW LEDGER"
				blok = {}
				blok["type"] = "ledger"
				if "lp" in lobj_master.request.GET:
					ledger_page = lobj_master.request.GET["lp"]
				else:
					ledger_page = 1
				blok["ledger"] = lobj_master.metric._view_ledger(pqc[1],pqc[2],ledger_page)
				if not blok["ledger"]:
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				bloks.append(blok)
				break
			if pqc[0] == 80:
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				page["title"] = "VIEW ACCOUNT"
				blok = {}
				blok["type"] = "one account"
				blok["account"] = lobj_master.metric._view_network_account(pqc[1],pqc[2])
				if not blok["account"]:
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				bloks.append(blok)
				break
				
			if pqc[0] == 70:
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				page["title"] = "MESSAGES"
				"""				
				# a Model for user messages
				class ds_mr_user_message(ndb.Model):
				
					date_created = ndb.DateTimeProperty(auto_now_add=True)
					create_user_id = ndb.StringProperty()
					target_user_id = ndb.StringProperty()
					message_content = ndb.PickleProperty()
					gravatar_url = ndb.StringProperty(indexed=False)
					gravatar_type = ndb.StringProperty(indexed=False)
					username = ndb.StringProperty(indexed=False)
				"""
				blok = {}
				blok["type"] = "messages"
				blok["messages_raw"] = ""
				blok["messages"] = []
				blok["channel"] = pqc[1]
				blok["next_more"] = False
				blok["next_cursor"] = ""
				blok["prev_more"] = False
				blok["prev_cursor"] = ""
				if "fcursor" in lobj_master.request.GET:
					current_fcursor = lobj_master.request.GET["fcursor"]
				else:
					current_fcursor = None
				if "rcursor" in lobj_master.request.GET:
					current_rcursor = lobj_master.request.GET["rcursor"]
				else:
					current_rcursor = None
				a, b, c, d, e = lobj_master.user._get_user_messages(pqc[1],current_fcursor,current_rcursor)
				blok["messages_raw"] = a
				blok["next_cursor"] = b
				blok["next_more"] = c
				blok["prev_cursor"] = d
				blok["prev_more"] = e
				if not blok["next_cursor"] is None:
					blok["next_cursor"] = blok["next_cursor"].urlsafe()
				if not blok["prev_cursor"] is None:
					blok["prev_cursor"] = blok["prev_cursor"].urlsafe()
				for message in blok["messages_raw"]:
					formatted_message = {}
					formatted_message["avatar_url"] = lobj_master.user._get_gravatar_url(message.gravatar_url,message.gravatar_type)
					formatted_message["date"] = message.date_created
					formatted_message["text"] = message.message_content
					formatted_message["username"] = message.username
					blok["messages"].append(formatted_message)
				bloks.append(blok)
				break

			if pqc[0] == 50:
				page["title"] = "OTHER PROFILE"
				blok = {}
				blok["type"] = "other_profile"
				# need to get our user based on va GET var

				name_entity_key = ndb.Key("ds_mr_unique_dummy_entity", pqc[1])
				name_entity = name_entity_key.get()
				if name_entity is None:
					# error User name is invalid
					r.redirect(self.url_path(error_code="1295"))
					return None
				other_user_key = ndb.Key("ds_mr_user", name_entity.user_id) 
				other_user = other_user_key.get()
				if other_user is None:
					# error Can't load user entity
					r.redirect(self.url_path(error_code="1296"))
					return None

				blok["gravatar_url"] = lobj_master.user._get_gravatar_url(other_user.gravatar_url,other_user.gravatar_type)
				blok["bio"] = other_user.bio
				blok["username"] = other_user.username
				blok["lat"] = float(other_user.location_latitude) / 100000000
				blok["long"] = float(other_user.location_longitude) / 100000000
				bloks.append(blok)	
				break
				
			if pqc[0] == 60:
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				page["title"] = "MY PROFILE"
				blok = {}
				blok["type"] = "my_profile"
				# get own user transactionally
				self_user_key = ndb.Key("ds_mr_user", lobj_master.user.entity.user_id) 
				self_user = self_user_key.get()
				blok["gravatar_url"] = lobj_master.user._get_gravatar_url(self_user.gravatar_url,self_user.gravatar_type)
				blok["bio"] = self_user.bio
				blok["username"] = self_user.username
				blok["lat"] = float(self_user.location_latitude) / 100000000
				blok["long"] = float(self_user.location_longitude) / 100000000
				
				# format offers if any
				if self_user.parent_client_offer_account_id == 0:
					blok["has_client_offer"] = False
				else:
					blok["has_client_offer"] = True
					blok["client_parent_entity"] = {}
					network = lobj_master.metric._get_network(fint_network_id=self_user.parent_client_offer_network_id)
					client_parent_user_key = ndb.Key("ds_mr_user", self_user.parent_client_offer_user_id) 
					client_parent_user = client_parent_user_key.get()
					client_parent_metric_key = ndb.Key("ds_mr_metric_account", "%s%s" % (str(network.network_id).zfill(8),str(self_user.parent_client_offer_account_id).zfill(12))) 
					client_parent_metric = client_parent_user_key.get()
					a = client_parent_user
					b = network.network_id
					c = self_user.parent_client_offer_account_id
					d = client_parent_metric.account_type
					blok["client_parent_entity"]["username_alias"] = self.get_label_for_account()
					blok["client_parent_entity"]["network_name"] = network.network_name
					a = network
					b = client_parent_metric
					c = client_parent_metric.current_network_balance
					d = client_parent_metric.current_reserve_balance
					blok["client_parent_entity"]["network_balance"] = self.get_formatted_amount(a,b,c)
					blok["client_parent_entity"]["reserve_balance"] = self.get_formatted_amount(a,b,d)

				if self_user.parent_joint_offer_account_id == 0:
					blok["has_joint_offer"] = False
				else:
					blok["has_joint_offer"] = True
					blok["joint_parent_entity"] = {}
					network = lobj_master.metric._get_network(fint_network_id=self_user.parent_joint_offer_network_id)
					joint_parent_user_key = ndb.Key("ds_mr_user", self_user.parent_joint_offer_user_id) 
					joint_parent_user = joint_parent_user_key.get()
					joint_parent_metric_key = ndb.Key("ds_mr_metric_account", "%s%s" % (str(network.network_id).zfill(8),str(self_user.parent_joint_offer_account_id).zfill(12))) 
					joint_parent_metric = joint_parent_user_key.get()
					a = joint_parent_user
					b = network.network_id
					c = self_user.parent_joint_offer_account_id
					d = joint_parent_metric.account_type
					blok["joint_parent_entity"]["username_alias"] = self.get_label_for_account()
					blok["joint_parent_entity"]["network_name"] = network.network_name
					a = network
					b = joint_parent_metric
					c = joint_parent_metric.current_network_balance
					d = joint_parent_metric.current_reserve_balance
					blok["joint_parent_entity"]["network_balance"] = self.get_formatted_amount(a,b,c)
					blok["joint_parent_entity"]["reserve_balance"] = self.get_formatted_amount(a,b,d)
				
				bloks.append(blok)	
				break

			if pqc[0] == 40:
				page["title"] = "ROOT"
				blok = {}
				blok["type"] = "home"
				bloks.append(blok)	
				break

			if pqc[0] == 30:
				page["title"] = "MENU ROOT"
				blok = {}
				blok["type"] = "menu"
				blok["menuitems"] = []

				menuitem = {}
				menuitem["href"] = "/"
				menuitem["label"] = "Root"
				blok["menuitems"].append(menuitem)

				menuitem = {}
				menuitem["href"] = "/network"
				menuitem["label"] = "All Networks"
				blok["menuitems"].append(menuitem)

				if lobj_master.user.IS_LOGGED_IN:
					menuitem = {}
					menuitem["href"] = "/profile"
					menuitem["label"] = "My Profile"
					blok["menuitems"].append(menuitem)

				menuitem = {}
				menuitem["href"] = "/?test_code=8002"
				menuitem["label"] = "Test Bloks"
				blok["menuitems"].append(menuitem)
				bloks.append(blok)	
				break	

			if pqc[0] == 20:
				# view all networks
				page["title"] = "NETWORKS"
				blok = {}
				blok["type"] = "all networks"
				"""
				We want to show all networks to everyone, but if they are members of
				certain networks we will show those on top.

				FOR LOGGED IN USERS:

				My Live Networks (inset)

				My Test Networks (inset)

				[Other] Live Networks (inset)

				[Other] Test Networks (inset/collapsible)
				Inactive Networks (inset/collapsible)
				Deleted Networks (inset/collapsible)


				FOR ANONYMOUS VIEWERS:

				Live Networks (inset)

				Test Networks (inset/collapsible)
				Inactive Networks (inset/collapsible)
				Deleted Networks (inset/collapsible)		
				"""
				blok["groups"] = self.master.metric._get_all_networks()
				bloks.append(blok)	
				break


				pass	
			if pqc[0] == 10:
				# view specific network
				# view all networks
				blok = {}
				blok["type"] = "one network"
				blok["network"] = self.master.metric._get_network(fstr_network_name=pqc[1])
				if blok["network"] is None: 
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
					return None
				page["title"] = blok["network"].network_name
				bloks.append(blok)

				# now lets add the view of the users accounts
				blok2 = {}
				blok2["type"] = "all accounts"
				blok2["groups"] = self.master.metric._get_all_accounts(fstr_network_name=pqc[1])
				bloks.append(blok2)	
				break

			# context not recognized
			# show error
			page["title"] = "ERROR"
			blok = {}
			blok["type"] = "error"
			blok["error_code"] = "1002"
			blok["last_view_link"] = "/"
			blok["last_view_link_text"] = "Link to ROOT"
			bloks.append(blok)	
			break			
		
		template = JINJA_ENVIRONMENT.get_template('templates/tpl_mob_command.html')
		self.response.write(template.render(master=lobj_master))
		
	def post(self):
		
		# Instantiate the master object, do security and other app checks. If
		# there's an interruption return from this function without processing
		# further.
		lobj_master = master(self,"post","unsecured")
		self.master = lobj_master
		if lobj_master.IS_INTERRUPTED:return

		# get the command text
		lstr_command_text = lobj_master.request.POST['form_command_text']
		if lstr_command_text.isspace() or not lstr_command_text or lstr_command_text is None:
			# No command passed, just treat as a refresh, but if they hit
			# enter when command field is empty and they are also currently
			# on a error/success/confirm view, then we strip out any query
			# string vars related to those views before refreshing.
			# 
			# That's why we prefix all result view query variables with x.
			stripped_GET = {}
			for key in lobj_master.request.GET:
				# if first character of query string var name is 'x'
				if key[:1] == "x":
					# skip it
					pass
				else:
					#include it
					stripped_GET[key] = lobj_master.request.GET[key]					
			lobj_master.request_handler.redirect(self.url_path(new_vars=stripped_GET,new_path=lobj_master.request.path))
		else:
			# create a shorter reference to the request handler
			r = lobj_master.request_handler
			# parse the command and make sure all lowercase
			ct = lstr_command_text.lower().split()
			ctraw = lstr_command_text.split()
			ctraw.append(lstr_command_text)  
			# is this a confirmation of a previously entered command?
			is_confirmed = False
			if ct[0] == "confirm" and len(ct) == 1:
				# yes, it is
				# check the hidden confirmed command
				lstr_command_text = lobj_master.request.POST['form_hidden_command_text']
				if lstr_command_text.isspace() or not lstr_command_text or lstr_command_text is None:
					# no command passed, just treat as a refresh
					r.redirect(self.url_path(error_code="1001"))
					return
				else:
					# Make what was in the hidden field what we actually process
					# and continue.
					ct = lstr_command_text.lower().split()
					ctraw = lstr_command_text.split()
					ctraw.append(lstr_command_text)
					is_confirmed = True			
			
			# get the context
			lobj_master.PATH_CONTEXT = ("root/" + lobj_master.request.path.strip("/")).strip("/")
			
			# get path/query context and variables
			pqc = self.get_pqc()
			
			"""
			PROCESS THE COMMANDS
			
			This is the main switch for processing commands.
			Most of the logic/rules/permissions for various
			functions/pages are handled here.
			
			"""
			
			
			
			"""
			# create shorter references to our objects
			lobj_master.bloks = []
			lobj_master.page = {}
			context = lobj_master.PATH_CONTEXT
			bloks = lobj_master.bloks
			page = lobj_master.page
			lobj_master.TRACE.append("%s" %(ct))
			lobj_master.TRACE.append("%s" %(pqc[0]))
			lobj_master.TRACE.append("%s" %(1))
			lobj_master.TRACE.append("%s" %(1))
			lobj_master.TRACE.append("%s" %(1))
			lobj_master.TRACE.append("%s" %(1))
			lobj_master.TRACE.append("%s" %(1))
			template = JINJA_ENVIRONMENT.get_template('templates/tpl_mob_command.html')
			self.response.write(template.render(master=lobj_master))
			return
			
			"""
			#return lobj_master.dump([pqc[0],pqc[1],ct[0],ct[1]])
			###################################
			# long command
			# 
			# from any context
			###################################
			if  len(ct) == 3 and ct[0] == "settings":
				# only admins can modify settings
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif not lobj_master.user.IS_ADMIN:
					r.redirect(self.url_path(error_code="1103"))
				elif not lobj_master._modify_settings(ct[1],ctraw[2]):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					r.redirect(self.url_path(success_code=lobj_master.RETURN_CODE))
				return	
			###################################
			# long command
			# 
			# from any context
			###################################
			if  len(ct) == 1 and ct[0] == "l":
				r.redirect(self.url_path(new_vars="xcs=long"))
				return		
			###################################
			# menu
			# 
			# from any context
			###################################
			if  len(ct) == 1 and ct[0] == "menu":
				r.redirect(self.url_path(new_vars="view_menu=1",new_path="/"))
				return
			###################################
			# user and account search
			# 
			# from any context
			###################################
			if  len(ct) == 2 and ct[0] == "user":
				if not self.is_valid_name(ct[1]):
					r.redirect(self.url_path(error_code="1101"))
				else:
					r.redirect(self.url_path(new_vars=("va=%s" % ct[1]),new_path="/profile"))
				return
			if  len(ct) == 2 and ct[0] == "account":
				if not self.is_valid_name(ct[1]):
					r.redirect(self.url_path(error_code="1101"))
				else:
					# get the network name before we redirect
					name_entity_key = ndb.Key("ds_mr_unique_dummy_entity", ct[1])
					name_entity = name_entity_key.get()
					if name_entity is None:
						# error Account name is invalid
						r.redirect(self.url_path(error_code="1297"))
						return None
					other_user_key = ndb.Key("ds_mr_user", name_entity.user_id) 
					other_user = other_user_key.get()
					if other_user is None:
						# error Can't load user entity
						r.redirect(self.url_path(error_code="1298"))
						return None
					# We've got a valid user, now search the user to
					# see if the name passed is a valid account.  If
					# it's not, don't fail, just kick them to the profile.
					# If successful, send them to the account.
					
					network_id = None
					for i in range(len(other_user.reserve_network_ids)):
						if other_user.reserve_labels[i] == ct[1]:
							network_id = other_user.reserve_network_ids[i]
							break
					if network_id is None:
						for i in range(len(other_user.client_network_ids)):
							if other_user.client_labels[i] == ct[1]:
								network_id = other_user.client_network_ids[i]
								break	
						
					if network_id is None:
						for i in range(len(other_user.joint_network_ids)):
							if other_user.joint_labels[i] == ct[1]:
								network_id = other_user.joint_network_ids[i]
								break	
						
					if network_id is None:
						for i in range(len(other_user.clone_network_ids)):
							if other_user.clone_labels[i] == ct[1]:
								network_id = other_user.clone_network_ids[i]
								break
								
					if network_id is None:
						# can't find an account with that name, so send to user profile
						r.redirect(self.url_path(new_vars=("va=%s" % other_user.username),new_path="/profile"))
					else:
						# found an account with that name, send to account view page after
						# getting network label
						network = lobj_master.metric._get_network(fint_network_id=network_id)
						r.redirect(self.url_path(new_vars=("vn=%s&va=%s" % (network.network_name,ct[1])),new_path="/network"))
				return				
			###################################
			# username change <USERNAME>
			# 
			# from any context
			###################################
			if len(ct) == 3 and ("%s %s" % (ct[0],ct[1])) == "username change":
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif not self.is_valid_name(ct[2]):
					r.redirect(self.url_path(error_code="1101"))
				elif not is_confirmed:
					# need confirmation before changing a username
					ltemp = {}
					ltemp["xold_username"] = lobj_master.user.entity.username
					ltemp["xnew_username"] = ct[2]
					ltemp["xct"] = "username change %s" % ct[2]
					r.redirect(self.url_path(new_vars=ltemp,confirm_code="6001"))
				elif not lobj_master.user._change_username_transactional(ct[2]):
					r.redirect(self.url_path(error_code="1102"))
				else:
					ltemp = {}
					ltemp["xold_username"] = lobj_master.user.entity.username
					ltemp["xnew_username"] = ct[2]
					r.redirect(self.url_path(new_vars=ltemp,success_code="7001"))
				return
			###################################
			# modify user settings
			# 
			# from any context
			###################################
			if len(ct) == 2 and ct[0] in ["gurl","gtype"]:
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif not lobj_master.user._modify_user(ct[0],ct[1]):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					r.redirect(self.url_path(success_code=lobj_master.RETURN_CODE))
				return				
			if len(ct) == 3 and ct[0] == "location":
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif not lobj_master.user._modify_user(ct[0],"%s %s" % (ct[1],ct[2])):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					r.redirect(self.url_path(success_code=lobj_master.RETURN_CODE))
				return		
			if ct[0] == "bio" and len(ct) > 1:
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif not lobj_master.user._modify_user(ct[0],self.get_text_for("bio",ctraw[-1])):
					r.redirect(self.url_path(new_path="/profile",error_code=lobj_master.RETURN_CODE))
				else:
					r.redirect(self.url_path(new_path="/profile",success_code=lobj_master.RETURN_CODE))
				return			
			###################################
			# user message
			# 
			# from message context
			###################################
			if pqc[0] == 70 and len(ct) > 1 and ct[0] == "message":
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif not lobj_master.user._message(pqc[1],self.get_text_for("message",ctraw[-1])):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					time.sleep(2)
					#lobj_master.dump([lobj_master.request.path_qs])
					r.redirect(self.url_path(new_path=lobj_master.request.path_qs))
				# no success code, just return, smoother
				return		
			###################################
			# network add <NETWORK NAME> : add a new network [admin only]
			# network <NETWORK NAME> : view a network
			# network : view network summary for all networks
			# 
			# from any context
			###################################
			if len(ct) == 3 and ("%s %s" % (ct[0],ct[1])) == "network add":
				# only admins can create a network
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif not lobj_master.user.IS_ADMIN:
					r.redirect(self.url_path(error_code="1103"))
				elif not self.is_valid_name(ct[2]):
					r.redirect(self.url_path(error_code="1104"))
				elif not lobj_master.metric._network_add(ct[2]):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					ltemp = {}
					ltemp["xnew_network_name"] = ct[2]
					r.redirect(self.url_path(new_vars=ltemp,success_code="7002"))
				return
			if  len(ct) == 2 and ct[0] == "network" and not ct[1] == "delete" and not ct[1] == "activate":
				ltemp = {}
				ltemp["vn"] = ct[1]
				r.redirect(self.url_path(new_vars=ltemp,new_path="/network"))
				return
			if  len(ct) == 1 and ct[0] == "network":
				r.redirect("/network")
				return
			###################################
			# network delete : delete a network [admin only]
			# network activate : change network status to ACTIVE [admin only]
			# network type live : set network type to live [admin only]
			# network type test : set network type to test [admin only]
			# network name <valid name> : change the name of a network [admin only]
			# network skintillionths <positive integer> : set conversion rate of network [admin only]
			# 
			# all only from network:network_id context
			###################################
			if pqc[0] == 10 and len(ct) == 2 and ("%s %s" % (ct[0],ct[1])) == "network delete":
				# only admins can delete a network
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif not lobj_master.user.IS_ADMIN:
					r.redirect(self.url_path(error_code="1103"))
				elif not lobj_master.metric._network_modify(fname=pqc[1],delete_network=True):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					ltemp = {}
					ltemp["xnetwork_name"] = pqc[1]
					ltemp["vn"] = pqc[1]
					r.redirect(self.url_path(new_vars=ltemp,success_code="7003"))
				return
			if pqc[0] == 10 and len(ct) == 2 and ("%s %s" % (ct[0],ct[1])) == "network activate":
				# only admins can change the status of a network
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif not lobj_master.user.IS_ADMIN:
					r.redirect(self.url_path(error_code="1103"))
				elif not is_confirmed:
					# need confirmation before activating a network
					ltemp = {}
					ltemp["xnetwork_name"] = pqc[1]
					ltemp["xct"] = "network activate"
					# Need to declare query vars necessary for 
					# pqc[]/context on the confirm page or else
					# we won't get back here on confirm.
					ltemp["vn"] = pqc[1]
					r.redirect(self.url_path(new_vars=ltemp,confirm_code="6002"))
				elif not lobj_master.metric._network_modify(fname=pqc[1],fstatus="ACTIVE"):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					ltemp = {}
					ltemp["xnetwork_name"] = pqc[1]
					ltemp["vn"] = pqc[1]
					r.redirect(self.url_path(new_vars=ltemp,success_code="7004"))
				return
			if pqc[0] == 10 and len(ct) == 3 and ("%s %s %s" % (ct[0],ct[1],ct[2])) == "network type live":
				# only admins can change the type of a network
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif not lobj_master.user.IS_ADMIN:
					r.redirect(self.url_path(error_code="1103"))
				elif not lobj_master.metric._network_modify(fname=pqc[1],ftype="LIVE"):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					ltemp = {}
					ltemp["xnetwork_name"] = pqc[1]
					ltemp["vn"] = pqc[1]
					r.redirect(self.url_path(new_vars=ltemp,success_code="7005"))
				return
			if pqc[0] == 10 and len(ct) == 3 and ("%s %s %s" % (ct[0],ct[1],ct[2])) == "network type test":
				# only admins can change the type of a network
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif not lobj_master.user.IS_ADMIN:
					r.redirect(self.url_path(error_code="1103"))
				elif not lobj_master.metric._network_modify(fname=pqc[1],ftype="TEST"):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					ltemp = {}
					ltemp["xnetwork_name"] = pqc[1]
					ltemp["vn"] = pqc[1]
					r.redirect(self.url_path(new_vars=ltemp,success_code="7006"))
				return
			if pqc[0] == 10 and len(ct) > 2 and ("%s %s" % (ct[0],ct[1])) == "network describe":
				# only admins can change the description of a network
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif not lobj_master.user.IS_ADMIN:
					r.redirect(self.url_path(error_code="1103"))
				elif not lobj_master.metric._network_modify(fname=pqc[1],fdescription=self.get_text_for("describe",lstr_command_text)):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					ltemp = {}
					ltemp["xnetwork_name"] = pqc[1]
					ltemp["vn"] = pqc[1]
					r.redirect(self.url_path(new_vars=ltemp,success_code="7045"))
				return
			if pqc[0] == 10 and len(ct) == 3 and ("%s %s" % (ct[0],ct[1])) == "network skintillionths":
				# only admins can change the type of a network
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif not lobj_master.user.IS_ADMIN:
					r.redirect(self.url_path(error_code="1103"))
				elif not re.match(r'^[0-9]+$',ct[2]) or not (int(ct[2])) < 1000000000000000 or not (int(ct[2])) > 0:
					r.redirect(self.url_path(error_code="1107"))
				elif not lobj_master.metric._network_modify(fname=pqc[1],fskintillionths=int(ct[2])):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					ltemp = {}
					ltemp["xnetwork_name"] = pqc[1]
					ltemp["xskintillionths"] = ct[2]
					ltemp["vn"] = pqc[1]
					r.redirect(self.url_path(new_vars=ltemp,success_code="7007"))
				return
			if pqc[0] == 10 and len(ct) == 3 and ("%s %s" % (ct[0],ct[1])) == "network name":
				# only admins can change a network name
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif not lobj_master.user.IS_ADMIN:
					r.redirect(self.url_path(error_code="1103"))
				elif not self.is_valid_name(ct[2]):
					r.redirect(self.url_path(error_code="1104"))
				elif not is_confirmed:
					# need confirmation before changing a network name
					ltemp = {}
					ltemp["xold_network_name"] = pqc[1]
					ltemp["xnew_network_name"] = ct[2]
					ltemp["xct"] = "network name %s" % ct[2]
					# Need to declare query vars necessary for 
					# pqc[]/context on the confirm page or else
					# we won't get back here on confirm.
					ltemp["vn"] = pqc[1]
					r.redirect(self.url_path(new_vars=ltemp,confirm_code="6003"))
				elif not lobj_master.metric._network_modify(fname=pqc[1],fnewname=ct[2]):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					ltemp = {}
					ltemp["xold_network_name"] = pqc[1]
					ltemp["xnew_network_name"] = ct[2]
					ltemp["vn"] = ct[2]
					r.redirect(self.url_path(new_vars=ltemp,success_code="7008"))		
				return
			###################################
			# reserve add : 
			# joint authorize :
			# client authorize : 
			# 
			# These three functions are done from the single network
			# view context.  All other account functions are done from
			# the single account view context.
			###################################
			if pqc[0] == 10 and len(ct) == 2 and ("%s %s" % (ct[0],ct[1])) == "reserve open":
				# create a reserve account on this network for the user
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif not is_confirmed:
					# need confirmation before creating a reserve account
					ltemp = {}
					ltemp["xnetwork_name"] = pqc[1]
					ltemp["xct"] = "reserve open"
					# Need to declare query vars necessary for 
					# pqc[]/context on the confirm page or else
					# we won't get back here on confirm.
					ltemp["vn"] = pqc[1]
					r.redirect(self.url_path(new_vars=ltemp,confirm_code="6004"))
				elif not lobj_master.metric._reserve_open(pqc[1]):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					ltemp = {}
					ltemp["vn"] = pqc[1]
					ltemp["xnetwork_name"] = pqc[1]
					r.redirect(self.url_path(new_vars=ltemp,success_code="7011"))
				return
			###################################
			#modify up|down|destroy|create <amount>
			#connect
			#disconnect
			#pay <amount>
			#suggested request <amount>
			#suggested authorize <amount>
			#suggested cancel <amount>
			#suggested deny <amount>
			#transfer request <amount>
			#transfer authorize <amount>
			#transfer cancel <amount>
			#transfer deny <amount>
			###################################
			if (pqc[0] == 80 or pqc[0] == 90) and len(ct) == 3 and ct[0] == "modify":
				# modify reserve command
				a, network, c, account_name, e = lobj_master.metric._get_default(pqc[1],lobj_master.user.entity.user_id)
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif not ct[1] in ["add","subtract","create","destroy"]:
					# error Subcommand for modify command not recognized.  Must be 'add', 'subtract', 'create', or 'destroy'.
					r.redirect(self.url_path(error_code="1291"))
				elif not a:
					# error Pass up error from get_default function.
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				elif not account_name:
					# error No account found for user on this network.
					r.redirect(self.url_path(error_code="1292"))
				# they must be viewing their own reserve account to make
				# reserve modifications.
				elif not account_name == pqc[2] or not network.network_name == pqc[1]:
					# error Must be viewing your own reserve account to make reserve modifications.
					r.redirect(self.url_path(error_code="1292"))
				elif not lobj_master.metric._modify_reserve(pqc[1],account_name,ct[1],ct[2]):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					ltemp = {}
					ltemp["vn"] = pqc[1]
					ltemp["va"] = pqc[2]
					r.redirect(self.url_path(new_vars=ltemp,success_code=lobj_master.RETURN_CODE))
				return
				
			if pqc[0] == 80 and len(ct) == 1 and ct[0] == "connect":
				a, network, c, account_name, e = lobj_master.metric._get_default(pqc[1],lobj_master.user.entity.user_id)
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif not a:
					# error Pass up error from get_default function.
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				elif not account_name:
					# error No account found for user on this network.
					r.redirect(self.url_path(error_code="1292"))
				# now we have a user account label on the network
				elif not lobj_master.metric._connect(pqc[1],account_name,pqc[2]):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					ltemp = {}
					ltemp["vn"] = pqc[1]
					ltemp["va"] = pqc[2]
					r.redirect(self.url_path(new_vars=ltemp,success_code=lobj_master.RETURN_CODE))
				return

			if pqc[0] == 80 and len(ct) == 1 and ct[0] == "disconnect":
				a, network, c, account_name, e = lobj_master.metric._get_default(pqc[1],lobj_master.user.entity.user_id)
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif not a:
					# error Pass up error from get_default function.
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				elif not account_name:
					# error No account found for user on this network.
					r.redirect(self.url_path(error_code="1292"))
				# now we have a user account label on the network
				elif not lobj_master.metric._disconnect(pqc[1],account_name,pqc[2]):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					ltemp = {}
					ltemp["vn"] = pqc[1]
					ltemp["va"] = pqc[2]
					r.redirect(self.url_path(new_vars=ltemp,success_code=lobj_master.RETURN_CODE))
				return

			if pqc[0] == 80 and len(ct) == 3 and ct[0] in ["transfer","suggested"]:
				# modify reserve command
				a, network, c, account_name, e = lobj_master.metric._get_default(pqc[1],lobj_master.user.entity.user_id)
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif not ct[1] in ["authorize","request","cancel","deny"]:
					# error Subcommand for suggested/transfer command not recognized.  Must be 'add', 'subtract', 'create', or 'destroy'.
					r.redirect(self.url_path(error_code="1294"))
				elif not a:
					# error Pass up error from get_default function.
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				elif not account_name:
					# error No account found for user on this network.
					r.redirect(self.url_path(error_code="1292"))
				# we have a user account referenced now
				elif not lobj_master.metric._process_reserve_transfer(pqc[1],account_name,pqc[2],ct[2],"%s %s" % (ct[0],ct[1])):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					ltemp = {}
					ltemp["vn"] = pqc[1]
					ltemp["va"] = pqc[2]
					r.redirect(self.url_path(new_vars=ltemp,success_code=lobj_master.RETURN_CODE))
				return

			if pqc[0] == 80 and len(ct) == 2 and ct[0] == "pay":
				a, network, c, account_name, e = lobj_master.metric._get_default(pqc[1],lobj_master.user.entity.user_id)
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif not a:
					# error Pass up error from get_default function.
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				elif not account_name:
					# error No account found for user on this network.
					r.redirect(self.url_path(error_code="1292"))
				# now we have a user account label on the network
				elif not lobj_master.metric._make_payment(pqc[1],account_name,pqc[2],ct[1]):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					ltemp = {}
					ltemp["vn"] = pqc[1]
					ltemp["va"] = pqc[2]
					r.redirect(self.url_path(new_vars=ltemp,success_code=lobj_master.RETURN_CODE))
				return

			if pqc[0] == 80 and len(ct) == 2 and "%s %s" % (ct[0],ct[1]) == "alias delete":
				# delete alias associated with this account
				# replace with username (error if username unavailable)
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif not lobj_master.metric._alias_change_transactional(pqc[2],None,True):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					ltemp = {}
					ltemp["vn"] = pqc[1]
					ltemp["va"] = pqc[2]
					r.redirect(self.url_path(new_vars=ltemp,success_code=lobj_master.RETURN_CODE))
				return
			if pqc[0] == 80 and len(ct) == 3 and "%s %s" % (ct[0],ct[1]) == "alias change":
				# change alias associated with this account
				# replace with username (error if username unavailable)
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif not lobj_master.metric._alias_change_transactional(pqc[2],ct[2]):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					ltemp = {}
					ltemp["vn"] = pqc[1]
					ltemp["va"] = pqc[2]
					r.redirect(self.url_path(new_vars=ltemp,success_code=lobj_master.RETURN_CODE))
				return
			if pqc[0] == 80 and len(ct) == 1 and ct[0] == "default":
				# change default network account
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif not lobj_master.metric._set_default(pqc[1],pqc[2]):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					ltemp = {}
					ltemp["vn"] = pqc[1]
					ltemp["va"] = pqc[2]
					r.redirect(self.url_path(new_vars=ltemp,success_code=lobj_master.RETURN_CODE))
				return
			if pqc[0] == 80 and len(ct) == 2 and "%s %s" % (ct[0],ct[1]) == "clone open":
				# open clone account through this reserve account
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif not lobj_master.metric._other_account(pqc[1],pqc[2],None,"clone open"):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					ltemp = {}
					ltemp["vn"] = pqc[1]
					ltemp["va"] = pqc[2]
					r.redirect(self.url_path(new_vars=ltemp,success_code=lobj_master.RETURN_CODE))
				return
			if pqc[0] == 80 and len(ct) == 2 and "%s %s" % (ct[0],ct[1]) in ["clone close","reserve close","joint close","client close"]:
				# close account
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif not lobj_master.metric._leave_network(pqc[1],pqc[2],("%s %s" % (ct[0],ct[1]))):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					ltemp = {}
					ltemp["vn"] = pqc[1]
					ltemp["va"] = pqc[2]
					r.redirect(self.url_path(new_vars=ltemp,success_code=lobj_master.RETURN_CODE))
				return
			if pqc[0] == 80 and len(ct) == 3 and "%s %s" % (ct[0],ct[1]) in ["joint offer","client offer"]:
				# offer to be parent account
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif not self.is_valid_name(ct[2]):
					r.redirect(self.url_path(error_code="1104"))
				elif not lobj_master.metric._other_account(pqc[1],pqc[2],ct[2],("%s %s" % (ct[0],ct[1]))):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					ltemp = {}
					ltemp["vn"] = pqc[1]
					ltemp["va"] = pqc[2]
					r.redirect(self.url_path(new_vars=ltemp,success_code=lobj_master.RETURN_CODE))
				return
			if len(ct) == 3 and "%s %s %s" % (ct[0],ct[1],ct[2]) == "client offer deny":
				# deny an existing joint/client offer
				net_id = self.PARENT.user.entity.parent_client_offer_network_id
				source_name = self.PARENT.user.entity.username
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				# make sure they actually have 
				elif net_id == 0:
					# error No client offer exists
					r.redirect(self.url_path(error_code="STUB"))
				elif not lobj_master.metric._other_account_transactional(net_id,source_name,None,"client offer deny"):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					r.redirect(self.url_path(success_code=lobj_master.RETURN_CODE))
				return
			if len(ct) == 3 and "%s %s %s" % (ct[0],ct[1],ct[2]) == "joint offer deny":
				# deny an existing joint/client offer
				net_id = self.PARENT.user.entity.parent_joint_offer_network_id
				source_name = self.PARENT.user.entity.username
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				# make sure they actually have 
				elif net_id == 0:
					# error No joint offer exists
					r.redirect(self.url_path(error_code="STUB"))
				elif not lobj_master.metric._other_account_transactional(net_id,source_name,None,"joint offer deny"):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					r.redirect(self.url_path(success_code=lobj_master.RETURN_CODE))
				return
			if len(ct) == 3 and "%s %s %s" % (ct[0],ct[1],ct[2]) == "client offer cancel":
				# cancel an existing joint/client offer
				net_id = self.PARENT.user.entity.child_client_offer_network_id
				source_name = self.PARENT.user.entity.username
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				# make sure they actually have 
				elif net_id == 0:
					# error No client offer exists
					r.redirect(self.url_path(error_code="STUB"))
				elif not lobj_master.metric._other_account_transactional(net_id,source_name,None,"client offer cancel"):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					r.redirect(self.url_path(success_code=lobj_master.RETURN_CODE))
				return
			if len(ct) == 3 and "%s %s %s" % (ct[0],ct[1],ct[2]) == "joint offer cancel":
				# cancel an existing joint/client offer
				net_id = self.PARENT.user.entity.child_joint_offer_network_id
				source_name = self.PARENT.user.entity.username
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				# make sure they actually have 
				elif net_id == 0:
					# error No joint offer exists
					r.redirect(self.url_path(error_code="STUB"))
				elif not lobj_master.metric._other_account_transactional(net_id,source_name,None,"joint offer cancel"):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					r.redirect(self.url_path(success_code=lobj_master.RETURN_CODE))
				return
			if pqc[0] == 80 and len(ct) == 2 and "%s %s" % (ct[0],ct[1]) in ["joint authorize","client authorize"]:
				# authorize to be child account
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif lobj_master.user.entity is None
					# error User not registered
					r.redirect(self.url_path(error_code="STUB"))
				elif not lobj_master.metric._other_account(pqc[1],lobj_master.user.entity.username,pqc[2],("%s %s" % (ct[0],ct[1]))):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					ltemp = {}
					ltemp["vn"] = pqc[1]
					ltemp["va"] = pqc[2]
					r.redirect(self.url_path(new_vars=ltemp,success_code=lobj_master.RETURN_CODE))
				return
			if pqc[0] == 80 and len(ct) == 3 and "%s %s" % (ct[0],ct[1]) in ["joint retrieve"]:
				# retrieve funds from child joint account
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
					return
				a, network, c, account_name, e = lobj_master.metric._get_default(pqc[1],lobj_master.user.entity.user_id)
				if not a:
					# error Pass up error from get_default function.
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				elif not account_name:
					# error No account found for user on this network.
					r.redirect(self.url_path(error_code="1292"))
				# now we have a user account label on the network
				elif not lobj_master.metric._joint_retrieve(pqc[1],account_name,pqc[2],ct[2]):
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					ltemp = {}
					ltemp["vn"] = pqc[1]
					ltemp["va"] = pqc[2]
					r.redirect(self.url_path(new_vars=ltemp,success_code=lobj_master.RETURN_CODE))
				return

			"""
			ticket functions parsed separately
			
			
			TICKETS ALL [OWNER] CONTEXT: 

			(#) *open <name>
			(#) *open <name> <user>
			(#) *open <name> <amount>
			(#) *open <name> <amount> m <memo>
			(#) *open <name> <amount> <user>
			(#) *open <name> <amount> <user> m <memo>

			(#) *close <name> : close an open ticket
			(#) *remove <ticket> : remove user association with a ticket

			TICKETS ALL [OTHER] CONTEXT:

			(#) *ticket <name> : search/go to a specific ticket

			TICKETS SPECIFIC [OWNER] CONTEXT: 

			(#) *close : close the ticket
			(#) *attach <user> : associate a specific user with a ticket
			(#) *remove : removes any associated user
			(#) *amount <amount> : directly assigns ticket amount value overwriting previous (blanking memo)
			(#) *amount <amount> m <memo> : directly assigns ticket amount and memo values overwriting previous

			TICKETS SPECIFIC [OTHER] CONTEXT: 

			(#) *pay <amount> : pay a ticket
			(#) *pay <amount> <amount|percent> : pay a ticket plus add gratuity
			(#) *remove : removes visiting users association from a ticket
			"""

			ticket_1st_tokens = ["open","close","remove","attach","amount","pay"]
			ticket_ct = ct.append(lstr_command_text)
			if pqc[0] == 110 and ct[0] in ticket_1st_tokens:
				# specific ticket
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
					return
				a, network, c, account_name, e = lobj_master.metric._get_default(pqc[1],lobj_master.user.entity.user_id)
				# We want to know if the default is the account we're viewing.
				# That determines whether the user is the owner or a visitor
				# in the ticket context.  Even if the user owns the account, if
				# it's not set to default, they are a visitor.
				if not a:
					# error Pass up error from get_default function.
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
					return
				elif not account_name:
					# error No account found for user on this network.
					r.redirect(self.url_path(error_code="1292"))
					return
				else:
					# Determine whether visitor or owner.
					if account_name == pqc[2]:
						visitor = None
					else:
						visitor = account_name
				if not lobj_master.metric._process_ticket(pqc[1],pqc[2],visitor,ticket_ct,pqc[3]):
					# error Pass up error
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					ltemp = {}
					ltemp["vn"] = pqc[1]
					ltemp["va"] = pqc[2]
					ltemp["vt"] = pqc[3]
					r.redirect(self.url_path(new_vars=ltemp,success_code=lobj_master.RETURN_CODE))
				return
					
			
			if pqc[0] == 100 and ct[0] in ticket_1st_tokens:
				# all tickets
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
					return
				a, network, c, account_name, e = lobj_master.metric._get_default(pqc[1],lobj_master.user.entity.user_id)
				# We want to know if the default is the account we're viewing.
				# That determines whether the user is the owner or a visitor
				# in the ticket context.  Even if the user owns the account, if
				# it's not set to default, they are a visitor.
				if not a:
					# error Pass up error from get_default function.
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
					return
				elif not account_name:
					# error No account found for user on this network.
					r.redirect(self.url_path(error_code="1292"))
					return
				else:
					# Determine whether visitor or owner.
					if account_name == pqc[2]:
						visitor = None
					else:
						visitor = account_name
				if not lobj_master.metric._process_ticket(pqc[1],pqc[2],visitor,ticket_ct):
					# error Pass up error
					r.redirect(self.url_path(error_code=lobj_master.RETURN_CODE))
				else:
					ltemp = {}
					ltemp["vn"] = pqc[1]
					ltemp["va"] = pqc[2]
					r.redirect(self.url_path(new_vars=ltemp,success_code=lobj_master.RETURN_CODE))
				return
				
			if ct[0] == "ticket" and len(ct) == 2 and (pqc[0] == 100 or pqc[0] == 110):
				# ticket search
				if not lobj_master.user.IS_LOGGED_IN:
					r.redirect(self.url_path(error_code="1003"))
				elif not self.is_valid_name(ct[2]):
					r.redirect(self.url_path(error_code="1104"))
				else:
					ltemp = {}
					ltemp["vn"] = pqc[1]
					ltemp["va"] = pqc[2]
					ltemp["vt"] = pqc[3]
					r.redirect(self.url_path(new_vars=ltemp))
				return

			###################################
			# command not recognized
			###################################
			r.redirect(self.url_path(error_code="1278"))
			return
			
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

# All this function does is tell the module which path to match to which 
# class. It then calls either 'get'/'post' function on that class depending
# on the request type. The path argument takes a regular expression.

# steps to add a new page
# 1. Create the template you want to use
# 2. Add it to the tuple-ey/sequencey thingy below
# 3. Create the class you designate below like the others with a get/post

application = webapp2.WSGIApplication([
	('/', ph_command),
	('/network', ph_command),
	('/profile', ph_command),
	('/messages', ph_command),
	('/ledger', ph_command),
	('/tickets', ph_command)
	],debug=True)

##########################################################################
# END: Python Entry point.  This function should be permanent.
##########################################################################


