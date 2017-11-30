from socket import *
from utils  import *
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
				self.server.state = HandleClientsState(self.server)
			except Exception, e: #Mediator is inactive
				print 'Error:',e
				self.server.state = InitialState(self.server) #Try to contact other mediator
			

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
			readable, writeable, error = select.select([self.server.sock], [], [], (self.TIME_BETWEEN_REPORT+begin-current))
			if self.server.sock in readable:
				conn,addr = self.server.sock.accept()
				conn.settimeout(1) #FIXME set timeout properly
				send(conn, "Hey")
				print 'Player connected'
				self.server.players_number += 1 #TODO create list of players
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
	def __init__(self, local_port, med_list):
		self.local_ip = self.findIp()
		self.local_port = local_port
		self.med_list = med_list
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
		''' Publish this server on themediator allowing it to receive updates from other servers '''
		errors = 0
		while 1:
			for mediator in range(len(self.med_list)):
				s = socket(AF_INET, SOCK_STREAM)
				s.settimeout(0.5)
				ip = self.med_list[mediator][0]
				port = self.med_list[mediator][1]
				try: #Try connecting to each mediator in the same order as it is in utils.py
					print 'Trying the mediator at ('+ip+','+str(port)+')'
					s.connect((ip, port))
					s.send('1')
					send(s, self.local_ip+"|"+str(self.local_port))

					self.med_sock = s
					break
				except Exception,e:
					print 'Mediator number %s is not active: %s' % (mediator,e)
					
			else:
				time.sleep(1)
				print 'There is no active mediator...'
				errors += 1
				if errors == 3: #Try three times before quitting [FIXME number]
					sys.exit()
				else:
					continue
			break


PORT = 6971

if len(sys.argv)>1:
	PORT=int(sys.argv[1]) #optional port passing in case there are more than one server in the network.

s = Server(PORT, MED_LIST)

while 1:
	print s.state.stateName #Debug
	s.run()