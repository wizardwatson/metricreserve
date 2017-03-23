# metricreserve
Metric Reserve Stuff



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

	CONTEXT: root AS user
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
		
		
		# reserve transfers
		# conversion updating
		# map
		# transaction views
		# subaccounts and cash accounts
		# multi-network
		# polling for pellets
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
		
		
		
		
