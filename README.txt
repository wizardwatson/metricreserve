Metric Reserve Stuff

TO DO:

	valid names should be 50 character or less?


PAGES

[root]
	anon message
	logged in message
	
[all networks summary]
	clickable networks
	
[one network summary]
	clickable accounts you have
	
[one account]
	status
	type
	balance
	activity
	reserve stuff if any

[all tickets]
	list of created ones
	list of tagged ones
	
[one ticket]
	qr code
	amount
	memo
	name

[profile]
	messages
	bio
	location
	list of accounts and networks
	
	
	




* must be logged in
** must be admin

ANY CONTEXT:

	l : change to long command
	menu : navigate to menu
	*username change <name> : change primary username
	network : show summary of all networks
	network <name> : switch to specific network view
	
SPECIFIC NETWORK CONTEXT:
 
	**network add <name> : add a new network 
	**network delete : delete an inactive network
	**network type <live|test> : change network type of inactive network
	**network activate : activate an inactive network
	**network skintillionths <amount> : change inactive network conversion ratio
	**network describe <description> : add description to inactive network

	*reserve open
	
	*default <username|alias> : set default account to use on this network

SPECIFIC ACCOUNT [SELF] CONTEXT: 

	*alias change <alias>
	*alias delete
	
	*joint offer
	*joint retrieve
	*joint close
	
	*client offer
	*client close
	
	*clone open
	*clone close
	
	*reserve close

	*modify up|down|destroy|create <amount>
	
	*tickets : go to your accounts ticket page

SPECIFIC ACCOUNT [OTHER] CONTEXT:

	*joint authorize

	*client authorize

	*connect
	*disconnect

	*pay <amount>

	*suggested request <amount>
	*suggested authorize <amount>
	*suggested cancel <amount>
	*suggested deny <amount>
	
	*transfer request <amount>
	*transfer authorize <amount>
	*transfer cancel <amount>
	*transfer deny <amount>

TICKETS ALL [OWNER] CONTEXT: 

*open <name>
*open <name> <user>
*open <name> <amount>
*open <name> <amount> m <memo>
*open <name> <amount> <user>
*open <name> <amount> <user> m <memo>

*close <name> : close an open ticket
*remove <ticket> : remove user association with a ticket

TICKETS ALL [OTHER] CONTEXT:

*ticket <name> : search/go to a specific ticket

TICKETS SPECIFIC [OWNER] CONTEXT: 

*close : close the ticket
*attach <user> : associate a specific user with a ticket
*remove : removes any associated user
*amount <amount> : directly assigns ticket amount value overwriting previous (blanking memo)
*amount <amount> m <memo> : directly assigns ticket amount and memo values overwriting previous

TICKETS SPECIFIC [OTHER] CONTEXT: 

*pay <amount> : pay a ticket
*pay <amount> <amount|percent> : pay a ticket plus add gratuity
*remove : removes visiting users association from a ticket

PROFILE [SELF] CONTEXT:

*message <text> : post message to own feed
*bio <text> : update/set/delete public biographical information
*gravatar email <email> : update email address to use for gravatar
*gravatar type <email|identicon|monstercon|anonymous|metric> : switch gravatar display format
*location <lat> <lng> : set your public location

PROFILE [OTHER] CONTEXT:

*message <text> : post message to anothers feed









dev_appserver.py --clear_datastore=yes app.yaml




TESTDIR=~/src/metricreserve313/metric



TESTDIR=~/src/mr2017development/metric

git clone https://github.com/wizardwatson/metricreserve.git $TESTDIR

cd $TESTDIR

dev_appserver.py --clear_datastore=yes $PWD
dev_appserver.py $PWD

git pull https://github.com/wizardwatson/metricreserve.git





TASKS LEFT 



5. 
	message <user>

6. invoice

invoice : summary
invoice <amount> : create a generic invoice
invoice <user> <amount> : create an invoice for a specific user
ticket <amount> <label>
ticket <label>


7.
	gravatar email(email to use)
	gravatar type(email|identicon|monstercon|anonymous|metric)
	bio
	location

8.  (qr related)
9.  (map related)

10. Finish Templates

11. (admin graph test related)
12. Reporting

13.  (cart/register related)

		# cart and register
		
			register_program{
				"id": <uid>
				"name": <unique name>
				"owner": account_id
				"access": public|private
				plu_data:[(<label>,<price>,<type>)...]}
					# label is just text description
					# price is a number
					# type can be taxable|untaxable|percent

			register_data{
				"active": <uid>
					# users can have up to 20 registers assigned, this tells which one currently in use
				"assigned": [[<register program id>,<tax percent>]]...
				"baskets":[(<label>,<amount>)]...




			CONTEXT: register [id] AS user	
				<id> plu [u]
				[quantity] x [id] plu [u]
				(<label>) ([amount]) [%] [u]
				[quantity] x [label] [amount]
				subtotal
				suspend
					# Suspends the current transaction in first available basket, else warns none available.
				unsuspend
				invoice [<account id of user>]
				use <register program slot assigned to this user>|<register program name>

				void [<line number>]
					# void last entry
					# if line number specified, void that line only			
				clear
					# restart transaction fresh
				exit
					# exit context to root
				cash [<payment method description>]
					# if not invoicing through metric reserve but want to save transaction
					# any text after cash will be added to the memo portion of the transaction

14. Bitcoin





To Do List:
	Last Login?  Activity counters, counters, counters, counters...
	remove transfer requests on disconnects
	never let transaction amounts (lint_amount) be negative


FUNCTIONS

	CONTEXT:AS anonymous
		CLASS METRIC
			get_network_summary(fint_network_id)
			
	CONTEXT:AS user
		CLASS USER
			save_unique_username(fstr_name)
			change_unique_username(fstr_name)
			
		CLASS METRIC
			get_network_summary(fint_network_id)
			join_network(fint_user_id,fint_network_id)
			leave_network(fint_account_id,fint_network_id)
			connect(fint_network_id,fint_source_account_id,fint_target_account_id)
			disconnect(fint_network_id,fint_source_account_id,fint_target_account_id)
			modify_reserve(fint_network_id,fint_source_account_id,fstr_type,fstr_amount)
			make_payment(fint_network_id,fint_source_account_id,fstr_amount)
			process_reserve_transfer(fint_network_id,fint_source_account_id,fstr_type,fstr_amount,fstr_type)
			
	CONTEXT:AS system
		CLASS METRIC
			process_graph(fint_network_id)
			
	CONTEXT:AS administrator
	



COMMANDS
		plain = keyword
		[brackets] = contents optional
		(parentheses) = contents required
		split|by|pipe = mutually exclusive elements
		<anglebrackets> = variable argument

	CONTEXT: home AS user
		invoice [<user>] <amount>
		pay <user>|<invoice> [<amount>] [<gratuity>]
		
		connect <user>
		disconnect <user>
		join <network>
		leave <network>
		reserve up|down|destroy|create <amount>
		username [change] [name]
		profile [<user>]
		summary [<network>]
		
		
		
		
		CONTEXT: admin	
			COMMAND:network 
				COMMAND: network add <name>
				COMMAND: network delete
				COMMAND: network <name>
				COMMAND: network type <LIVE|TEST>
				COMMAND: network activate
				COMMAND: network skintillionths <amount>
				COMMAND: network describe <description>
				
		
		CONTEXT: root
			using(network)
		
		CONTEXT: user
			COMMAND: username change(desired username)
			COMMAND: username alias add(desired alias)
			COMMAND: username alias del(desired alias)
			COMMAND: gravatar email(email to use)
			COMMAND: gravatar type(email|identicon|monstercon|anonymous|metric)
			COMMAND: bio
			COMMAND: location





	
alias change <alias>
alias delete


*** joint ***
(parent/child)
PARENT
	joint offer
	joint close
	joint retrieve
CHILD
	joint authorize
	joint close

*** client ***
(parent/child)
PARENT
	client offer
	client close
CHILD
	client authorize
	client close
	
*** clone ***
(self only)
clone open
clone close

*** reserve ***
(self only)
reserve open
reserve close






		CONTEXT:network:username
				COMMAND:joint
					CONTEXT:parent(client|reserve)
						COMMAND:offer (child username)
						COMMAND:del(child username)
					CONTEXT:child
						COMMAND:ask(parent username)
						COMMAND:del(parent username)
				COMMAND:sub
					CONTEXT:parent(client|reserve)
						COMMAND:give(amount)
						COMMAND:take(amount)
						COMMAND:add(child username)
						COMMAND:del(child username)
				COMMAND:client
					CONTEXT:parent(reserve)
						COMMAND:add(child username)
						COMMAND:del(child username)
						COMMAND:give(amount)
					CONTEXT:child
						COMMAND:del
				COMMAND:reserve
					COMMAND:add
					COMMAND:connect
					COMMAND:disconnect
					COMMAND:modify up|down|create|destroy(amount)
					COMMAND:transfer
					COMMAND:del
				(all accounts)
				COMMAND:pay
				COMMAND:invoice
		
		
		
		# reserve accounts can have client, joint, and sub accounts.  20 maximum across all networks.
		# client accounts can have joint, and sub accounts in that network.  20 maximum across all networks.
		
		
		# reserve transfers
		# map
		# transaction views
		# subaccounts and cash accounts
		# multi-network
		# message
		
			message wizardwatson [<text>]
			... [<more message>]

# metric account: this is the main account information
class ds_mr_metric_account(ndb.Model):

	account_id = ndb.IntegerProperty()
	network_id = ndb.IntegerProperty()
	user_id = ndb.StringProperty()
	tx_index = ndb.IntegerProperty()
	account_status = ndb.StringProperty()
	account_type = ndb.StringProperty()
	account_parent = ndb.IntegerProperty()
	account_grandparent = ndb.PickleProperty()
	account_sub_children = ndb.PickleProperty()
	account_client_children = ndb.PickleProperty()
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


		
		
		



	
