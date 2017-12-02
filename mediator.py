from socket import *
from utils import *
import select,sys, time
from gameLog import Logger

log = Logger(1, [])

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

		#Servers = dictionary with keys = (ip,port) and values = tuple(playersConnected, socket, lastTimeItSentAReport)
		self.servers = {}
		self.queue = Queue() #priority queue
		#TODO SYNCHRONIZE STUFF

		#Replica stuff
		self.replica = replica
		self.replicaList = []
		self.time = time.time()
		self.checkIdle = self.time+5

	def initMasterSocket(self):
		log.println('Opening connections on ('+self.ip+','+str(self.port)+')', 3, ['init'])
		s = socket(AF_INET,SOCK_STREAM)
		s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 3)
		s.bind((self.ip, self.port))
		s.listen(10) #FIXME number of clients connecting at the same time. should support the 100 right?
		self.master = s
	def runReplica(self):
		log.println("I am in runReplica", 1, ['debug'])
		active = MED_LIST[0]
		med_sock = socket(AF_INET, SOCK_STREAM)
		try:
			log.println(active, 1, ['debug'])
			med_sock.connect(active) #Connect to active mediator to receive updates
			nodeType = json.dumps({"type": "InitialConnection","content": {"nodeType": REPLICACODE}})  # JSon indicating that it is a server trying to connect
			send(med_sock, nodeType)
		except:
			med_sock.close()
			return

		while 1:
			self.time = time.time()
			try:
				command = receive(med_sock) #FIXME timeout --> active mediator crashed #
				log.println("Received command from mediator: " + str(command), 2, ['update'])

				if command["type"] == 'Error':
					med_sock.close()
					return
			except Exception, e:
				log.println("Exception receiving command: "+str(e), 1, ['error'])
				med_sock.close()
				return
			self.handleCommand(command)

	def handleCommand(self, command):
		''' For now this only updates the server list. Later we need to update the queue to [FIXME] '''
		log.println("Handle command", 2, ['debug'])
		log.println("Command: "+str(command), 1, ['debug'])
		#FIXME JSON WAY TO DO IT
		if command["type"] == "ServerList":
			for server in self.servers:
				self.servers[server] = (command["content"][str(server)][0],None,self.time)
			log.println('Updated list of servers: '+str(self.servers), 3, ['update'])
		elif command["type"] == "PriorityQueue":
			self.queue.setQueue(command["content"])
			log.println('Updated priority queue', 3, ['update'])


	def run(self):
		if self.replica:
			self.runReplica()
			log.println('No active mediator. I should take over', 3, ['update'])
			self.replica = False

		log.println('Running on '+str(self.ip)+' '+str(self.port), 2, ['init'])
		
		if self.master:
			log.println('All ok', 1, ['init'])
		else:
			self.initMasterSocket()

		while 1:

			self.time = time.time() #Update time
			if self.time > self.checkIdle:
				self.checkIdle = self.time+5
				self.checkIdleServers()

			toCheck = [self.servers[i][1] for i in self.servers if self.servers[i][1] ] #Servers with proper sockets
			toCheck.append(self.master) #New connections
			for replica in self.replicaList:
				toCheck.append(replica) #Replicas -- If they say something its probably an EOF

			can_recv, can_send, exceptions = select.select(toCheck, [], [], 2)

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

	def checkIdleServers(self):
		''' Checks if a server didn't send a report for X seconds. If so, remove it from the server list '''
		toRemove = None
		for server in self.servers:
			if self.time - self.servers[server][2] > 15: #FIXME If it passed X seconds since last report, disconnect server
				toRemove = server
				break
		if toRemove:
			self.servers.pop(toRemove)
			log.println("Server " + str(toRemove) + " TIMEOUT", 3, ['server'])
			self.broadcastList()
			self.updateReplicas()


	def handleNewConnections(self):
		'''Distinguish if it is a server or a client trying to connect to the mediator '''
		conn,addr = self.master.accept()
		log.println(str(addr)+' TRYING TO CONNECT', 1, ['debug','connection'])
		conn.settimeout(1) #Just to avoid deadlock waiting for it to send or recv

		try:
			message = receive(conn)
			if message["type"]=="InitialConnection":				
				who = int(message["content"]["nodeType"])
				
			else:
				log.println("I was expecting IniticalConnection as type in message and got " + message["type"], 2, ['error','connection'])
			
		except:
			return
		
		if who == SERVERCODE: #TODO - Security - Authenticate real servers
			#In case it is a server
			log.println("It is a server trying to connect", 1, ['debug','connection'])
			self.handleNewServer(conn,addr)
		elif who == CLIENTCODE:
			#In case it is a client
			log.println("It is a client trying to connect", 1, ['debug','connection'])
			self.handleNewClient(conn,addr)
		elif who == REPLICACODE:
			#In case it is the replica
			log.println("It is a mediator trying to connect", 1, ['debug','connection'])
			self.replicaList.append(conn)

	def handleNewServer(self, conn, addr):
		''' Add the new server to the list of servers'''
		log.println('New server is trying to join: ' + str(addr), 2, ['connection'])
		
		message = receive(conn) #Obtain the message with the ip and port of the server trying to connect
		if message["type"] == 'Error' or message is None: #FIXME
			log.println('Error handling new server', 2, ['error','connection'])
			return
		
		if message["type"] == 'ServerInfo':
			server  = (message["content"]["ip"],message["content"]["port"]) #(ip,port)
		
		if server in self.servers: 
			#Servers are trying to connect to the replica. The socket is added to servers dictionary
			self.servers[server] = (0, conn, self.time) #TODO - receive port where server will be operational for clients
		else:
			log.println('New server is running at '+ str(server), 2, ['connection'])
			self.servers[server] = (0, conn, self.time) #TODO - receive port where server will be operational for clients

		self.broadcastList()

	def handleNewClient(self, conn, addr):
		'''Sends to the client the ip and port of the server with less connected users '''
		log.println('New client is trying to join: ' + str(addr), 1, ['connection','debug'])

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
						log.println("Information of the server sent to the client", 1, ['connection','debug'])
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
				try: #FIXME Shouldn't this try be before the receive? No because receive doesnt throw errors in utils.py
					if message["type"]=="Report":						
						connectedPlayers = int(message["content"]["connectedPlayers"])
						self.servers[server] = (connectedPlayers, self.servers[server][1], self.time) #Update number of players
						log.println(str(server)+' has '+str(connectedPlayers)+' connected players', 2, ['update', 'report'])
					else:
						log.println("Expecting type == Report but got " + message["type"], 1, ['error', 'report'])
				except:
					pass
		self.updateReplicas()
	def broadcastList(self):
		''' Send an up-to-date list of servers to everyone '''
		log.println("Ready to broadcast", 1, ['debug'])
		# Servers = dictionary with keys = (ip,port) and values = tuple(playersConnected, socket)
		serverList = json.dumps({"type": "ServerList","content": {"servers":[i for i in self.servers] }})

		log.println("message: "+str(serverList), 1, ['debug'])

		for server in self.servers:
			try:
				if self.servers[server][1]:
					log.println("I am going to send a message to the server "+str(server), 1, ['debug'])
					send(self.servers[server][1], serverList)
			except Exception,e:
				log.println(e, 'check this exception to see if you can remove the server from the servers list', 1, ['error'])
		self.updateReplicas()
	def updateReplicas(self):
		#Update replicas
		toRemove = []
		log.println('Im in updateReplicas ' + str(self.replicaList), 1, ['debug'])
		for replica in self.replicaList:
			log.println("Sending server list and queue to replica", 1, ['debug', 'update'])
			try:
				serverList = {}
				for i in self.servers:
					serverList[str(i)] = (self.servers[i][0],) #Remove the sockets from the self.servers dictionary and send it
					log.println("To replica. message["+str(i)+"]: "+str(serverList[str(i)]), 1, ['debug'])
				message1 = json.dumps({"type": "ServerList","content": serverList}) #Send server list
				message2 = json.dumps({"type": "PriorityQueue", "content": self.queue.getQueue()}) # send priority queue

				log.println("To replica. message serverList: "+message1, 1, ['debug','update'])
				log.println("To replica. message queue: "+message2, 1, ['debug','update'])
				send(replica, message1)
				send(replica, message2)
				log.println("Updated replica", 1, ['debug','update'])
			except Exception,e:
				log.println(e,1,['error'])
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

print "Am I a replica?"
answer = raw_input("(y/n): ")
if answer == 'y':
	log.println("I am a replica", 1, ['debug','init'])
	mediator = Mediator(MED_LIST[1][1], replica=True)
else:
	mediator = Mediator(MED_LIST[0][1])


mediator.run()