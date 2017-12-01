from socket import *
from utils import *
import select,sys

CLIENTCODE  = 0
SERVERCODE  = 1
REPLICACODE = 2

class Queue:
	def __init__(self):
		self.queueList = []
		self.timestamp = 0
		self.addTick = 10
	def getQueue(self):
		''' Returns the queue as a string to send to the servers '''
		return str((self.timestamp,self.timestamp+self.addTick, self.queueList )) #FIXME JSON
	def tick(self):
		self.timestamp += self.addTick #First, set new time stamp of the queue
		#Then, change the queue
		size = len(self.queueList)
		for i in range(size/2):
			tmp = self.queueList[i]
			self.queueList[i] = self.queueList[size-i-1]
			self.queueList[size-i-1] = tmp
	def getQueueList(self):
		return self.queueList
	def setQueue(self, queue):
		self.timestamp = queue[0]
		self.addTick   = queue[1]
		self.queueList = queue[2]
	def addToQueue(self, server):
		''' Server is tuple (ip,port) that uniquely identifies it '''
		self.queueList.append(server)

class Mediator:
	def __init__(self, port, replica=False):

		#self.ip = self.findIp() FIXME at deployment
		self.ip = 'localhost'
		self.port = port
		self.master = None
		if not replica:
			self.initMasterSocket()

		#Servers = dictionary with keys = (ip,port) and values = tuple(playersConnected, socket)
		self.servers = {}
		self.queue = Queue() #priority queue
		#TODO SYNCHRONIZE STUFF

		#Replica stuff
		self.replica = replica
		self.replicaList = []

	def initMasterSocket(self):
		print 'Opening connections on ('+self.ip+','+str(self.port)+')'
		s = socket(AF_INET,SOCK_STREAM)
		s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 3)
		s.bind((self.ip, self.port))
		s.listen(10) #FIXME number of clients connecting at the same time. should support the 100 right?
		self.master = s
	def runReplica(self):
		print "I am in runReplica"
		active = MED_LIST[0]
		med_sock = socket(AF_INET, SOCK_STREAM)
		try:
			print active
			med_sock.connect(active) #Connect to active mediator to receive updates
			nodeType = json.dumps({"type": "InitialConnection","content": {"nodeType": REPLICACODE}})  # JSon indicating that it is a server trying to connect
			send(med_sock, nodeType)
		except:
			med_sock.close()
			return

		while 1:
			try:
				command = receive(med_sock) #FIXME timeout --> active mediator crashed #
				print "Received command from mediator:",command

				if command["type"] == 'Error':
					med_sock.close()
					return
			except Exception, e:
				print "Exception receiving command",e
				#print "Exception receiving command in mediator: %s"(e)
				med_sock.close()
				return
			self.handleCommand(command)

	def handleCommand(self, command):
		''' For now this only updates the server list. Later we need to update the queue to [FIXME] '''
		print "Handle command"
		print "Command: ",command
		#FIXME JSON WAY TO DO IT
		if command["type"] == "ServerList":
			for server in self.servers:
				self.servers[server] = (command["content"][str(server)][0],None)
			print 'Updated list of servers:',self.servers
		elif command["type"] == "PriorityQueue":
			self.queue.setQueue(command["content"])
			print 'Updated priority queue'


	def run(self):
		if self.replica:
			self.runReplica()
			print 'No active mediator. I should take over'
			self.replica = False

		print 'Running on',self.ip,self.port
		
		if self.master:
			print 'All ok'
		else:
			self.initMasterSocket()

		while 1:
			toCheck = [self.servers[i][1] for i in self.servers if self.servers[i][1] ] #Servers with proper sockets
			toCheck.append(self.master) #New connections
			for replica in self.replicaList:
				toCheck.append(replica) #Replicas -- If they say something its probably an EOF

			can_recv, can_send, exceptions = select.select(toCheck, [], [])

			if self.master in can_recv: #Could be a new server or a new client
				self.handleNewConnections()

			elif can_recv != []:
				toRemove = None
				for replica in self.replicaList:
					if replica in can_recv:
						toRemove = replica
						break
				else:
					self.handleNewReports(can_recv)
				if toRemove:
					self.replicaList.remove(toRemove)
				
	def handleNewConnections(self):
		'''Distinguish if it is a server or a client trying to connect to the mediator '''
		conn,addr = self.master.accept()
		print addr,'TRYING TO CONNECT'
		conn.settimeout(1) #Just to avoid deadlock waiting for it to send or recv

		try:
			message = receive(conn)
			if message["type"]=="InitialConnection":				
				who = int(message["content"]["nodeType"])
				
			else:
				print "I was expecting IniticalConnection as type in message and got " + message["type"]
			
		except:
			return
		
		if who == SERVERCODE: #TODO - Security - Authenticate real servers
			#In case it is a server
			print "It is a server trying to connect"
			self.handleNewServer(conn,addr)
		elif who == CLIENTCODE:
			#In case it is a client
			print "It is a client trying to connect"
			self.handleNewClient(conn,addr)
		elif who == REPLICACODE:
			#In case it is the replica
			print "It is a mediator trying to connect"
			self.replicaList.append(conn)

	def handleNewServer(self, conn, addr):
		''' Add the new server to the list of servers'''
		print 'New server is trying to join: ', addr
		
		message = receive(conn) #Obtain the message with the ip and port of the server trying to connect
		if message["type"] == 'Error' or message is None: #FIXME
			print 'Error handling new server'
			return
		
		if message["type"] == 'ServerInfo':
			server  = (message["content"]["ip"],message["content"]["port"]) #(ip,port)
		
		if server in self.servers: 
			#Servers are trying to connect to the replica. The socket is added to servers dictionary
			self.servers[server] = (0, conn) #TODO - receive port where server will be operational for clients
		else:
			print 'New server is running at', server
			self.servers[server] = (0, conn) #TODO - receive port where server will be operational for clients

		self.broadcastList()

	def handleNewClient(self, conn, addr):
		'''Sends to the client the ip and port of the server with less connected users '''
		print 'New client is trying to join: ', addr

		#Search for a good server for him
		if len(self.servers) == 0:
			errorInfo = json.dumps({"type": "Error", "content": {"info": "The server is offline"}})
			send(conn, errorInfo) #no servers available
		else:
			minimum = min([self.servers[i][0] for i in self.servers])
			for server in self.servers:				
				#TODO - Geographical Scalability - maybe choose the one with less players and closer to the player accordingly to a formula
				if self.servers[server][0] == minimum: 
					try:
						serverInfo = json.dumps({"type":"ServerInfo","content":{"ip":str(server[0]),"port":int(server[1])}})
						send(conn, serverInfo) #This one :D
						print "Information of the server sent to the client"
					except:
						pass
					break

	def handleNewReports(self, can_recv):
		''' '''
		servers = self.servers.keys() #List of servers
		for server in servers:
			if self.servers[server][1] in can_recv: #If server sent a message
				message = receive(self.servers[server][1])				
				if message["type"] == 'Error': #FIXME when would the mediator receive disconnect? change for message["type"]=="Disconnect"
					del self.servers[server] #Disconnect a server if its offline
					self.broadcastList()
				try: #FIXME Shouldn't this try be before the receive?
					if message["type"]=="Report":						
						connectedPlayers = int(message["content"]["connectedPlayers"])
						self.servers[server] = (connectedPlayers, self.servers[server][1]) #Update number of players
						print server,'has',connectedPlayers,'connected players'
					else:
						print "Expecting type == Report but got " + message["type"]
				except:
					pass
		self.updateReplicas()
	def broadcastList(self):
		''' Send an up-to-date list of servers to everyone '''
		print "Ready to broadcast"
		# Servers = dictionary with keys = (ip,port) and values = tuple(playersConnected, socket)
		serverList = json.dumps({"type": "ServerList","content": {"servers":[i for i in self.servers] }})

		print "message: "+str(serverList)

		for server in self.servers:
			try:
				if self.servers[server][1]:
					print "I am going to send a message to the server "+str(server)
					send(self.servers[server][1], serverList)
			except Exception,e:
				print e, 'check this exception to see if you can remove the server from the servers list'
		self.updateReplicas()
	def updateReplicas(self):
		#Update replicas
		toRemove = []
		print 'Im in updateReplicas',self.replicaList
		for replica in self.replicaList:
			print "Sending server list and queue to replica"
			try:
				serverList = {}
				for i in self.servers:
					serverList[str(i)] = (self.servers[i][0],) #Remove the sockets from the self.servers dictionary and send it
					print "To replica. message[",i,"]: ",serverList[str(i)]
				message1 = json.dumps({"type": "ServerList","content": serverList}) #Send server list
				message2 = json.dumps({"type": "PriorityQueue", "content": self.queue.getQueue()}) # send priority queue

				print "To replica. message serverList:",message1
				print "To replica. message queue:",message2
				send(replica, message1)
				send(replica, message2)
				print "Updated replica"
			except Exception,e:
				print e
				toRemove.append(replica)

		#Remove replicas that are not answering anymore
		for replica in toRemove:
			self.replicaList.remove(replica)


	def findIp(self):
		''' Find local IP address '''
		s = socket(AF_INET, SOCK_DGRAM)
		s.connect(("8.8.8.8", 80))
		res = s.getsockname()[0]
		s.close()
		return res

'''
if len(sys.argv) > 1 and sys.argv[1] == 'replica': #FIXME way to see if we want to run a replica or the normal server
	mediator = Mediator(MED_LIST[1][1], replica=True)
else:
	mediator = Mediator(MED_LIST[0][1])
'''

answer = raw_input("Am I a replica? (y/n)")
if answer == 'y':
	print "I am a replica"
	mediator = Mediator(MED_LIST[1][1], replica=True)
else:
	mediator = Mediator(MED_LIST[0][1])


mediator.run()