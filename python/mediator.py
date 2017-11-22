from socket import *
import select

def send(sock, message):
	sock.send('<MSG>'+message+'</MSG>')

def receive(sock, MAX_SIZE=4096):
	try:
		message = ''
		curr_size = 0
		find = '<MSG>'

		for i in range(len(find)):
			c = sock.recv(1)
			if not c:
				return 'disconnect'
			if c != find[i]:
				print 'Error in receive. Invalid header'
				return

		while '</MSG>' not in message:
			c = sock.recv(1)
			if not c:
				return 'disconnect'
			message += c
			if curr_size > MAX_SIZE+6:
				print 'Received message bigger than MAX_SIZE'
				return

		return message[:-6]
	except:
		print 'Error in receive. Not enough data in buffer or invalid headers'

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

				
				conn,addr = self.master.accept()
				conn.settimeout(1) #Just to avoid deadlock waiting for it to send or recv

				try:
					who = conn.recv(1)
					who = int(who)
				except:
					continue

				if who == 1: #TODO - Security - Authenticate real servers
					#In case it is a server
					print 'New server is trying to join: ', addr
					
					self.servers[addr] = (0, conn)

					self.broadcastList()
				else:
					#In case it is a client
					print 'New client is trying to join: ', addr

					#Search for a good server for him
					minimum = min([self.servers[i][0] for i in self.servers])
					for server in self.servers:
						#TODO - Geographical Scalability - maybe choose the one with less players and closer to the player accordingly to a formula
						if self.servers[server][0] == minimum: 
							try:
								send(conn, str(server)) #This one :D
							except:
								pass
							break

			elif can_recv != []:
				#Receive reports
				servers = self.servers.keys()
				for server in servers:
					if self.servers[server][1] in can_recv:
						message = receive(self.servers[server][1])
						if message == 'disconnect':
							del self.servers[server]
							self.broadcastList()
						try:
							message = int(message)
							self.servers[server] = (message, self.servers[server][1])
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