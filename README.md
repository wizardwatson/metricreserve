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






command creation steps

	



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
					COMMAND: add
					COMMAND: del
					COMMAND: name <name>
					COMMAND: type <type>
					COMMAND: activate
					COMMAND: describe <description>
				
		
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
			
			alias create <alias>
			alias change <alias>
			alias delete
			alias assign
			username assign

		CONTEXT:network:username
				COMMAND:joint
					CONTEXT:parent(client|reserve)
						COMMAND:give(amount)
						COMMAND:take(amount)
						COMMAND:add(child username)
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
		
		
		



CONTEXTS
	root
		introduction
		quickstart
	home
		
	admin
		CreateNetwork
		DeleteNetwork
			# Only if no connections
		RenameNetwork


COMMANDS
	
	
	
	
VIEWS

	home
		your networks
		your sub accounts
		your client accounts
		available networks





VIEW TYPES

	error
	success
	confirm
	
