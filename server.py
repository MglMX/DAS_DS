from socket import *
from utils  import *
import sys, time
import select
from gameLog import Logger

log = Logger(1, [])
#log.println(msg, priority, keywords)

class SendReportState():
	def __init__(self, server):
		'''
		Sends a report to the mediator about how many players are connected to the server
		All states have function "run" '''
		self.server = server
		self.stateName = "Send Report State"
	def run(self):
		if self.server.med_sock is None:
			log.println('Error. No mediator socket. Should publish again', 3, ['error'])
			self.server.state = InitialState(self.server)
		else:
			try:
				report = json.dumps({"type":"Report", "content":{"connectedPlayers":int (self.server.players_number)}})
				send(self.server.med_sock, report)
				self.server.state = HandleClientsState(self.server)
			except Exception, e: #Mediator is inactive
				log.println('Error: '+e, 1, ['error'])
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
			if current-begin > self.TIME_BETWEEN_REPORT: #Check if the time to handle clients has passed so the state should be changed to sendReport
				break
			readable, writeable, error = select.select([self.server.sock,self.server.med_sock], [], [], (self.TIME_BETWEEN_REPORT+begin-current))
			
			if self.server.sock in readable:
				try:
					conn,addr = self.server.sock.accept() #conn holds the socket necessary to connect to the client
					conn.settimeout(1) #FIXME set timeout properly
					succMessage = json.dumps({"type": "SuccesfullConnection", "content": {"info":"Connected succesfully to the server"}})#FIXME Provavly we can directly send the board here
					send(conn, succMessage)
					log.println('Player connected', 1, ['player'])
					self.server.players_number += 1 #TODO create list of players
				except Exception,e:
					log.println('Error receiving client: '+e, 1, ['error'])

			elif self.server.med_sock in readable:
				''' Receive list of servers.
					For now I think it is the only thing the mediator sends the servers '''
				message = receive(self.server.med_sock)
				if message["type"] == "ServerList":
					self.server.neighbours = message["content"]["servers"]
					log.println('Server neighbour list updated: '+str(self.server.neighbours), 1, ['update'])
				elif message["type"] == "Error":
					self.server.med_sock = None
					self.server.state = InitialState(self.server) #Seek for another mediator
					return

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
	def __init__(self, local_port, med_list):
		self.local_ip = self.findIp()
		self.local_port = local_port
		self.med_list = med_list
		self.sock = socket(AF_INET, SOCK_STREAM)

		log.println('Binding to ('+self.local_ip+' , ' + str(self.local_port)+')',3,['init'])
		self.sock.bind((self.local_ip, local_port))
		self.sock.listen(50)
		self.med_sock = None
		self.state = InitialState(self)

		self.players_number = 0
		self.neighbours = [] #Other servers

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
		errors = 0
		while 1:
			for mediator in range(len(self.med_list)):
				s = socket(AF_INET, SOCK_STREAM)
				s.settimeout(0.5)
				ip = self.med_list[mediator][0]
				port = self.med_list[mediator][1]
				try: #Try connecting to each mediator in the same order as it is in utils.py
					log.println('Trying the mediator at ('+ip+','+str(port)+')',1,['publish'])
					s.connect((ip, port))
					nodeType = json.dumps({"type":"InitialConnection","content":{"nodeType":1}}) #JSon indicating that it is a server trying to connect
					send(s, nodeType)
					serverInfo = json.dumps({"type":"ServerInfo","content":{"ip":self.local_ip,"port":self.local_port}}) #JSon with the info of the server
					send(s, serverInfo)

					self.med_sock = s
					break
				except Exception,e:
					log.println('Mediator number %s is not active: %s' % (mediator,e), 1, ['publish'])
					
			else:
				time.sleep(1)
				log.println('There is no active mediator...', 3, ['publish'])
				errors += 1
				if errors == 3: #Try three times before quitting [FIXME number]
					sys.exit()
				else:
					continue
			break

PORT = 6971
'''
if len(sys.argv)>1:
	PORT=int(sys.argv[1]) #optional port passing in case there are more than one server in the network.
'''

print "Indicate port. Ex: 6971"
PORT = int(raw_input("port: "))

s = Server(PORT, MED_LIST)

while 1:
	log.println(s.state.stateName,1,'state') #Debug
	s.run()