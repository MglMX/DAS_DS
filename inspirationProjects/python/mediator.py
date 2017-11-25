from socket import *
from utils import *
import select

class Mediator:
	def __init__(self, port):

		s = socket(AF_INET,SOCK_STREAM)
		s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 3)
		s.bind(('localhost', port))
		s.listen(2)
		self.master = s

		#Servers = dictionary with keys = (ip,port) and values = tuple(playersConnected, socket)
		self.servers = {}
	def run(self):
		print 'Running'

		while 1:
			can_recv, can_send, exceptions = select.select([self.servers[i][1] for i in self.servers]+[self.master], [], [])

			if self.master in can_recv: #Could be a new server or a new client
				self.handleNewConnections()

			elif can_recv != []:
				self.handleNewReports(can_recv)
				
	def handleNewConnections(self):
		conn,addr = self.master.accept()
		conn.settimeout(1) #Just to avoid deadlock waiting for it to send or recv

		try:
			who = conn.recv(1)
			who = int(who)
		except:
			return

		if who == 1: #TODO - Security - Authenticate real servers
			#In case it is a server
			self.handleNewServer(conn,addr)
		else:
			#In case it is a client
			self.handleNewClient(conn,addr)

	def handleNewServer(self, conn, addr):
		print 'New server is trying to join: ', addr
		
		publish = receive(conn)
		if publish == 'disconnect': #FIXME
			print 'Error'
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
	def broadcastList(self):
		''' Send an up-to-date list of servers to everyone '''
		message = str([i for i in self.servers])
		for server in self.servers:
			try:
				send(self.servers[server][1], message)
			except Exception,e:
				print e, 'check this exception to see if you can remove the server from the servers list'


PORT = 6969

mediator = Mediator(PORT)
mediator.run()