from socket import *
from utils import *
import select,sys

CLIENTCODE  = 0
SERVERCODE  = 1
REPLICACODE = 2

class Mediator:
	def __init__(self, port, replica=False):

		s = socket(AF_INET,SOCK_STREAM)
		s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 3)

		#self.ip = self.findIp() FIXME
		self.ip = 'localhost'
		self.port = port

		s.bind((self.ip, port))
		s.listen(10) #FIXME number of clients connecting at the same time
		self.master = s

		#Servers = dictionary with keys = (ip,port) and values = tuple(playersConnected, socket)
		self.servers = {}
		self.replica = replica
		self.replicaList = []

	def runReplica(self):
		active = MED_LIST[0]
		med_sock = socket(AF_INET, SOCK_STREAM)
		try:
			print active
			med_sock.connect(active) #Connect to active mediator to receive updates
			med_sock.send(str(REPLICACODE))
		except:
			return

		while 1:
			try:
				command = receive(med_sock) #FIXME timeout --> active mediator crashed
				if command == 'disconnect':
					return
			except:
				return
			self.handleCommand(command)

	def handleCommand(self, command):
		''' For now this only updates the server list. Later we need to update the queue to [FIXME] '''
		self.servers = eval(command)
		for server in self.servers:
			self.servers[server] = (self.servers[server][0],None)
		print 'Updated list of servers:',self.servers

	def run(self):
		if self.replica:
			self.runReplica()
			print 'No active mediator. I should take over'
			self.replica = False

		print 'Running on',self.ip,self.port
		if self.master : print 'All ok'

		while 1:
			toCheck = [self.servers[i][1] for i in self.servers if self.servers[i][1] ] #Servers with proper sockets
			toCheck.append(self.master) #New connections
			for replica in self.replicaList:
				toCheck.append(replica) #Replicas -- If they say something its probably an EOF
			can_recv, can_send, exceptions = select.select(toCheck, [], [])

			print can_recv
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
		conn,addr = self.master.accept()
		conn.settimeout(1) #Just to avoid deadlock waiting for it to send or recv

		try:
			who = conn.recv(1)
			who = int(who)
		except:
			return

		if who == SERVERCODE: #TODO - Security - Authenticate real servers
			#In case it is a server
			self.handleNewServer(conn,addr)
		elif who == CLIENTCODE:
			#In case it is a client
			self.handleNewClient(conn,addr)
		elif who == REPLICACODE:
			#In case it is the replica
			self.replicaList.append(conn)

	def handleNewServer(self, conn, addr):
		print 'New server is trying to join: ', addr
		
		publish = receive(conn)
		if publish == 'disconnect' or publish == None: #FIXME
			print 'Error handling new server'
			return
		print 'New server is running at', publish
		publish = publish.split('|')
		publish = (publish[0], int(publish[1])) #(ip,port)
		self.servers[publish] = (0, conn) #TODO - receive port where server will be operational for clients

		self.broadcastList()

	def handleNewClient(self, conn, addr):
		print 'New client is trying to join: ', addr

		#Search for a good server for him
		if len(self.servers) == 0:
			send(conn, "ERROR - Game is offline") #no servers available
		else:
			minimum = min([self.servers[i][0] for i in self.servers])
			for server in self.servers:
				#TODO - Geographical Scalability - maybe choose the one with less players and closer to the player accordingly to a formula
				if self.servers[server][0] == minimum: 
					try:
						send(conn, str(server)) #This one :D
					except:
						pass
					break

	def handleNewReports(self, can_recv):
		servers = self.servers.keys() #List of servers
		for server in servers:
			if self.servers[server][1] in can_recv: #If server sent a message
				message = receive(self.servers[server][1])
				if message == 'disconnect':
					del self.servers[server] #Disconnect a server if its offline
					self.broadcastList()
				try:
					message = int(message)
					self.servers[server] = (message, self.servers[server][1]) #Update number of players
					print server,'has',message,'connected players'
				except:
					pass
		self.updateReplicas()
	def broadcastList(self):
		''' Send an up-to-date list of servers to everyone '''
		message = str([i for i in self.servers])
		for server in self.servers:
			try:
				if self.servers[server][1]:
					send(self.servers[server][1], message)
			except Exception,e:
				print e, 'check this exception to see if you can remove the server from the servers list'
		self.updateReplicas()
	def updateReplicas(self):
		#Update replicas
		toRemove = []
		for replica in self.replicaList:
			try:
				message = {}
				for i in self.servers:
					message[i] = (self.servers[i][0],) #Remove the sockets from the self.servers dictionary and send it
				message = str(message)
				send(replica, message)
			except:
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

if len(sys.argv) > 1 and sys.argv[1] == 'replica': #FIXME way to see if we want to run a replica or the normal server
	mediator = Mediator(MED_LIST[1][1], replica=True)
else:
	mediator = Mediator(MED_LIST[0][1])

mediator.run()