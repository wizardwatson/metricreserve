# metricreserve
Metric Reserve Stuff

dev_appserver.py --clear_datastore=yes app.yaml




TESTDIR=~/src/metricreserve313/metric



TESTDIR=~/src/mr2017development/metric

git clone https://github.com/wizardwatson/metricreserve.git $TESTDIR

cd $TESTDIR

dev_appserver.py --clear_datastore=yes $PWD
dev_appserver.py $PWD

git pull https://github.com/wizardwatson/metricreserve.git





TASKS LEFT 

2. 
	clone close
	reserve close
	joint close
	client close
3.
	joint retrieve
4.
	alias change <name>
	alias delete
5. (textarea?)
	network describe
	message <user>

6. invoice

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


		
		
		



	
