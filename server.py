from socket import *
from utils import *
import sys, time
import select

class SendReportState():
	def __init__(self, server):
		''' All states have function "run" '''
		self.server = server
		self.stateName = "Send Report State"
	def run(self):
		if self.server.med_sock == None:
			print 'Error. No mediator socket. Should publish again'
			self.server.state = InitialState(self.server)
		else:
			try:
				send(self.server.med_sock, str(self.server.players_number))
			except Exception, e:
				print e #TODO increase number of errors until it reaches a certain point
			self.server.state = HandleClientsState(self.server)

class HandleClientsState():
	''' All states have function "run" '''
	def __init__(self, server):
		self.server = server
		self.stateName = "Handle Clients State"
		self.TIME_BETWEEN_REPORT = 5 #X.   Each X seconds the server should send the mediator a report with the players that are connected
	def run(self):
		begin = time.time()
		while 1:
			current = time.time()
			if current-begin > self.TIME_BETWEEN_REPORT: #Check if the time to handle clients has passed so the state should be changed to sendReport
				break
			readable, writeable, error = select.select([self.server.sock], [], [], (self.TIME_BETWEEN_REPORT+begin-current))
			if self.server.sock in readable:
				conn,addr = self.server.sock.accept() #conn holds the socket necessary to connect to the client
				conn.settimeout(1) #FIXME set timeout properly
				send(conn, "Hey")
				print 'Player connected'
				self.server.players_number += 1 #TODO create list of players
		self.server.state = SendReportState(self.server)

		
class InitialState():
	''' All states have function "run"	'''
	def __init__(self, server):
		self.server = server
		self.stateName = "Initial State"
	def run(self):
		self.server.publish()
		self.server.state = HandleClientsState(self.server)

class Server:
	def __init__(self, local_port, med_ip, med_port):
		self.local_ip = self.findIp()
		self.local_port = local_port
		self.med_ip = med_ip
		self.med_port = med_port

		self.sock = socket(AF_INET, SOCK_STREAM)

		print 'Binding to ('+self.local_ip+' , ' + str(self.local_port)+')'
		self.sock.bind((self.local_ip, local_port))
		self.sock.listen(50)
		self.med_sock = None
		self.state = InitialState(self)

		self.players_number = 0

	def findIp(self):
		''' Find local IP address '''
		s = socket(AF_INET, SOCK_DGRAM)
		s.connect(("8.8.8.8", 80))
		res = s.getsockname()[0]
		s.close()
		return res

	def run(self): 
		#State machine
		self.state.run()
	def publish(self):
		''' Publish this server on the mediator allowing it to receive updates from other servers '''
		s = socket(AF_INET, SOCK_STREAM)
		s.settimeout(0.5)
		try:
			s.connect((self.med_ip, self.med_port)) #Connection with the mediator
			s.send('1') #Specify that the it is a server trying to connect
			send(s, self.local_ip+"|"+str(self.local_port)) #Send to the mediator the ip and port of the server

			self.med_sock = s
		except:
			print 'Error. Mediator is off'
			sys.exit(0)

PORT = 6971
MED_PORT = 6969
MED_IP = 'localhost'

if len(sys.argv)>1:
	PORT=int(sys.argv[1]) #optional port passing in case there are more than one server in the network.

s = Server(PORT, MED_IP, MED_PORT)

while 1:
	print s.state.stateName #Debug
	s.run()