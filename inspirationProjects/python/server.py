from socket import *
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
				self.server.med_sock.send('<MSG>%s</MSG>' % self.server.players_number)
			except:
				pass #TODO increase number of errors until it reaches a certain point
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
			if current-begin > self.TIME_BETWEEN_REPORT:
				break
			readable, writeable, error = select.select([], [], [], (self.TIME_BETWEEN_REPORT+begin-current))
		self.server.state = SendReportState(self.server)

		
class InitialState():
	''' All states have function "run" '''
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
			s.connect((self.med_ip, self.med_port))
			s.send('1')
			self.med_sock = s
		except:
			print 'Error. Mediator is off'
			sys.exit(0)

PORT = 6970
MED_PORT = 6969
MED_IP = 'localhost'

s = Server(PORT, MED_IP, MED_PORT)

while 1:
	print s.state.stateName #Debug
	s.run()