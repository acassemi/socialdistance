from meraki_initial_query import CurrentWifiUsers

## Parse the logfile genetated by the Syslog Server to capture
## WiFi users logging in and out.
## This version is only for 802.1x authenticated users
## Configure the Meraki Syslog to send only "Wireless Event Log"

def syslog_parsing(line):
	#Function that flattens the nested list generated by syslog new log line split
	#and parse the items that we need, creating what was called a log entry

	#convert the syslog log line entry into a list
	syslog_fields = line.split()
	fields = []
	#flatten the list (without nested items) and adjust formating
	for item in syslog_fields:
		fields.append(item.replace("'", "").split("="))
	processed_fields = [item for sublist in fields for item in sublist]

	#create the log dict with the date needed
	#timestamp, access point name, type of log, mac address, identity
	#in some cases the position in the list is variable: client mac and identity	
	try:
		timestamp = processed_fields[1]
		log["timestamp"] = timestamp

		access_point = processed_fields[2]
		log["access_point"] = access_point

		index_type = processed_fields.index('type')
		log_type = processed_fields[index_type + 1]
		log["type"] = log_type

		index_client_mac = processed_fields.index('client_mac')
		client_mac = processed_fields[index_client_mac + 1]
		log["client_mac"] = client_mac

		index_identity = processed_fields.index('identity')
		identity = processed_fields[index_identity + 1]
		log["identity"] = identity

	except: pass

	#Call the function that will update the user count
	wifi_user_count_log(log)

def wifi_user_count_log(log):
#Function to process the WiFi log parsed to capture just
#the number of users, identify of the users and at which
#AP these users are connected and authenticated
	
	#logs example
	#log = {'timestamp': '1592094556.940247523', 'access_point': 'MR33_Sala', 'type': '8021x_auth', 'client_mac': '38:F9:D3:4C:B1:39', 'identity': 'user1@mail.com'}
	#{'timestamp': '1592132340.048859064', 'access_point': 'MR18_Quartos', 'type': 'disassociation', 'client_mac': 'D8:8F:76:93:6B:D1', 'identity': 'user2@cisco.com'}
	
	#check if the entry is for an diassociation of an authenticated user with identity
	if "identity" in log and log["type"] == "disassociation":
		#get the name of the ap of the event
		ap_name = log["access_point"]
		identity = log["identity"]
		timestamp = log["timestamp"]
		#mac function disabled, need to address the scenario of same user with multiple devices first
		#mac = log["client_mac"]

		#get the existent status for that AP
		#get the index of the AP data in the wifi_count list
		for index, aps in enumerate(wifi_count, start=0):
			if aps["ap_name"] == ap_name:
				list_index = index
				ap_status = aps		
		
		#print log entry for debug only - can be removed
		print ("------------------------------")
		print ("User {} disassociation".format(identity))
		#print (log)
		#print ()
		
		#next blocks will build the new data for that AP
		
		#only delete user if the list has a user count higher than 0 and if the log entry has identity field
		#because of that users that are logging with PSK won't be counted

		if ap_status["ap_user_count"] > 0 and identity in ap_status["clients_identity"]:

			try:
				#remove list entry
				print()
				print ("Old AP Status")
				print (wifi_count[list_index])
				del wifi_count[list_index]

				#items fo the new entry will be
				new_last_update = timestamp
				new_ap_user_count = ap_status["ap_user_count"] - 1
				new_identity_list = ap_status["clients_identity"]
				new_identity_list.remove(identity)
				#mac function disabled, need to address the scenario of same user with multiple devices first
				#new_client_mac_list = ap_status["clients_mac"]
				#new_client_mac_list.remove(mac)
				#print(new_client_mac_list)

				#create a new entry for that AP and add to the wifi_count list
				print()
				print ("New AP Status")
				list_new_item = {"ap_name": ap_name, "ap_user_count": new_ap_user_count, "clients_identity": new_identity_list, "last_update": new_last_update}
				print(list_new_item)
				wifi_count.append(list_new_item)		
			
			except: 
				print()
				print("User couldn't be removed - user or ap doesn't exist in the list")
			
			print()
			print("Updated WiFi list is :")
			print(wifi_count)
			print()

			""" TODO
			Add here a function that gest the wifi_count list of dict and create a new entry in the DB
			"""
		
		else: 
			print()
			print("This AP has no clients or this client was not found at the AP, can't remove it")
			print()
			print("Updated WiFi list is :")
			print (wifi_count)
			print()


	#check if the entry is for an association of an authenticated user with identity	
	elif "identity" in log and log["type"] == "8021x_auth":
		#get the name of the ap of the event
		ap_name = log["access_point"]
		identity = log["identity"]
		timestamp = log["timestamp"]

		#mac function disabled, need to address the scenario of same user with multiple devices first
		#mac = log["client_mac"]

		#get the existent status for that AP
		#get the index of the AP data in the wifi_count list
		for index, aps in enumerate(wifi_count, start=0):
			if aps["ap_name"] == ap_name:
				list_index = index
				ap_status = aps

		#print log entry for debug only - can be removed
		print ("------------------------------")
		print ("User {} association".format(identity))
		#print (log)
		#print ()


		#next blocks will build the new data for that AP
		
		#only add user if the log entry has identity field and user is not already in the ap list
		#because of that users that are logging with PSK won't be counted
		
		if identity not in ap_status["clients_identity"]:
		
			try:
				#remove list entry
				print()
				print ("Old AP Status")
				print (wifi_count[list_index])
				del wifi_count[list_index]

				#items fo the new entry will be
				new_last_update = timestamp
				new_ap_user_count = ap_status["ap_user_count"] + 1
				new_identity_list = ap_status["clients_identity"]
				new_identity_list.append(identity)
				#mac function disabled, need to address the scenario of same user with multiple devices first
				#new_client_mac_list = ap_status["clients_mac"]
				#new_client_mac_list.append(mac)
				#print(new_client_mac_list)

				#create a new entry for that AP and add to the wifi_count list
				print()
				print ("New AP status")
				list_new_item = {"ap_name": ap_name, "ap_user_count": new_ap_user_count, "clients_identity": new_identity_list, "last_update": new_last_update}
				print (list_new_item)
				wifi_count.append(list_new_item)

			except: 
				print()
				print("User couldn't be added")
			
			print()
			print("Updated WiFi list is :")
			print(wifi_count)
			print()

			""" TODO
			Add here a function that gest the wifi_count list of dict and create a new entry in the DB
			"""

	else: 
		#un comment for debug of the other messages not used in WiFi Log
		#print ("------------------------------")
		#print (log)
		#print ()
		#print("Informational Only. No action taken. Log entry is not in use for wifi user count update")
		#print()
		#print("Updated WiFi list is :")
		#print(wifi_count)
		pass

"""TODO
add here the function that will update the wifi count status
on the DB
"""


if __name__ == '__main__':

	#starting the dict logs and wifi_count list
	log = {}
	wifi_count = []


	"""TODO
	#make a function here to grab this info from Meraki
	#get the list of AP and the users
	#make the list wifi_count that has all the APs dict
	#
	#At this point starting with a manual imput with zero clients
	#code will handle the error inserted because of that


	wifi_count = [
		{"ap_name": "MR33_Sala",
		"ap_user_count": 0,
		"clients_identity": [],
		"last_update": ""
		},
		{"ap_name": "MR18_Quartos",
		"ap_user_count": 0,
		"clients_identity": [],
		"last_update": ""
		},
		{"ap_name": "MR24_Cozinha",
		"ap_user_count": 0,
		"clients_identity": [],
		"last_update": ""
		}
		]
"""
	#idea for the wifi_count list including users mac address
	#{"ap_name": ap_name, "ap_user_count": new_ap_user_count, "clients_identity": new_identity_list, "clients_mac": new_client_mac_list}
	#not implemented with mac address because the logic is not ready to handle the scenario of a user with multiple devices

	wifi_count = CurrentWifiUsers()
	print()
	print("Initial WiFi list is :")
	print (wifi_count)
	print()
	print()

	with open('youlogfile.log') as f:
		while True:
			line = f.readline()
			if line:
				syslog_parsing(line)