from gameLog import Logger
from board  import Board
from empty  import Empty
from Dragon import Dragon
from Player import Player
from tss import TSS #Consistency
from socket import *
from utils  import *
import sys, time
import select, random

#FIXME - general optimizations. its a bit slow with 100 clients right now

DRAGONS_TO_SPAWN = 20

log = Logger(1)
#log.println(msg, priority, keywords)

class ServerConn:
	def __init__(self,conn,server,ip,port):
		self.server = server
		self.conn = conn
		self.ip = ip
		self.port = port
		self.sid = (self.ip, self.port)

	def getIpPort(self):
		return [self.ip,self.port]
	def remove(self):
		self.server.neighbours.remove(self)


class ClientConn:
	def __init__(self, conn, server, reuse_id):
		''' Responsible for managing a client.
			Creates a player in the board.
			Has attributes like the player id, the connecting socket, the last time it sent a report, etc '''

		self.server = server
		self.conn = conn
		self.id = self.server.curr_id
		self.server.curr_id += 1
		success = None
		if reuse_id:
			success = self.tryReuseId(reuse_id)
		if not success:
			self.player = self.spawnPlayer()
		else:
			self.player = success
			self.id = self.player.id
			self.server.curr_id -= 1
		self.lastTimeReport = self.server.timer.getTime()

	def spawnPlayer(self):
		''' Spawn player whereven it can. FIXME: concurrency problems  '''
		board = self.server.tss.trailingStates[0].board
		while 1:
			x = random.randint(0,24)
			y = random.randint(0,24)
			if board.board[x][y].name == 'empty':
				break
		player = Player(x, y, self.id)
		if "-v" in sys.argv:
			print '\n\nCreated client in',x,y,self.id
		#board.insertObject(player)
		return player

	def tryReuseId(self, reuse_id):
		board = self.server.tss.trailingStates[0].board
		for x in range(25):
			for y in range(25):
				if self.server.tss.trailingStates[0].board.board[x][y].id == reuse_id:
					return board.board[x][y]

	def remove(self):
		''' Despawn player and remove it from clients list. FIXME: concurrency problems '''
		if self in self.server.clients:
			self.server.clients.remove(self)
			self.server.players_number -= 1

		#broadcast despawn
		self.server.tss.addCommand({"type": "command", "content": {"cmd": "despawn", "id": self.id}}, self.server.timer.getTime(), self.server.sid)

	def checkIdle(self, curr_time):
		return curr_time-self.lastTimeReport > 70 #AFK X seconds = disconnnect. FIXME


class Timer:
	''' To check the correct time (as the mediator see's it) '''
	def __init__(self):
		self.timeDiff = 0 #Difference of time between server and mediator
	def getTime(self):
		return time.time()+self.timeDiff


class SendReportState():
	def __init__(self, server):
		'''
		Sends a report to the mediator about how many players are connected to the server
		All states have function "run" '''
		self.server = server
		self.stateName = "Send Report State"
	def run(self):
		#First, check if any clients are idle and remove them if needed.
		toRemove = []
		curr_time = self.server.timer.getTime()
		for client in self.server.clients:
			if client.checkIdle(curr_time):
				toRemove.append(client)
		for client in toRemove:
			client.remove()

		#Then send updated list of clients to mediator
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

	def handleNewConnection(self, current):
		conn, addr = self.server.sock.accept()
		message = receive(conn)
		if message["type"] == "ConnectionToServer":
			if message["content"]["nodeType"]== 0: #It is a client
				command = self.handleNewClient(conn, message["content"]["reuse_id"])
				self.server.tss.addCommand(command, current, self.server.sid)
				self.server.tss.executeCommands(current)
			elif message["content"]["nodeType"]== 1: #It is a server
				if not self.server.checkIfSocketAlreadySaved(conn):
					self.server.neighbours.append(ServerConn(conn,self.server,addr[0],addr[1])) #addr = (ip,port)
					log.println("Connection accepted from a server and socket created",1)
				if message["content"]["giveMeBoard"]: #FIXME - receiving the board should probably be here
					commandList = []
					for command in self.server.tss.trailingStates[-1].commands:
						if command.cmd == "move":
							jsonCommand = {"type": "command", "content": {"cmd": command.cmd, "timestamp": command.timestamp, "id": command.who, "where": command.where}}
						elif command.cmd in ("heal", "damage"):
							jsonCommand = {"type": "command", "content": {"cmd": command.cmd, "timestamp": command.timestamp, "id": command.target, "subject": command.who}}
						elif command.cmd == "spawn":
							jsonCommand = {"type": "command", "content": {"cmd": command.cmd, "timestamp": command.timestamp, "player": command.unit}}
						elif command.cmd == "despawn":
							jsonCommand = {"type": "command", "content": {"cmd": command.cmd, "timestamp": command.timestamp, "id": command.who}}
						else:
							if "-v" in sys.argv:
								print 'Invalid command',command.cmd
						jsonCommand["content"]["issuedBy"] = command.issuedBy
						commandList.append(jsonCommand)
					message = json.dumps({"type":"InitialBoard", "content":{"board": self.server.tss.trailingStates[-1].board.getBoard(), "commands": commandList}})
					send(conn, message)

	def handleNewClient(self,conn, reuse_id):
		''' First, accept connection. Then, send the board and the player ID '''

		conn.settimeout(1) #FIXME set timeout properly

		log.println('Player connected', 1, ['player'])

		#Send board and player ID

		client = ClientConn(conn, self.server, reuse_id)
		board = json.dumps({"type": "board", "content": {"ID": client.id, "board": self.server.tss.trailingStates[0].board.getBoard()}})
		send(conn, board)

		#Broadcast spawn command to everyone except the client itself
		x = client.player.x
		y = client.player.y
		u_id = client.player.id
		hp = client.player.hp
		ap = client.player.ap

		#Add player to list of clients
		self.server.players_number += 1
		self.server.clients.append(client)
		return {"type": "command", "content": {"cmd": "spawn", "timestamp": self.server.timer.getTime(), "player": {"x":x,"y":y,"id":u_id,"hp":hp,"ap":ap}}} #FIXME - if command fails, try to spawn it elsewhere

	def validMove(self, pos):
		if pos[0] > -1 and pos[0] < 25 and pos[1] > -1 and pos[1] < 25:
			return True
		return False

	def handleCommands(self, readable, curr_time):
		toRemove = []
		for client in self.server.clients:
			if client.conn in readable:
				try:
					command = receive(client.conn)
					if command["type"] == "Error":
						toRemove.append(client)
						continue
					assert command["type"] == "command"

					client.lastTimeReport = curr_time
					if command["content"]["cmd"] in ("damage", "heal"):
						command["content"]["subject"] = client.id

					if command["content"]["cmd"] == "disconnect": #FIXME disconnect now should use the new board
						u_id = command["content"]["id"]
						toRemove.append(client)
						self.server.tss.addCommand({"type": "command", "content": {"cmd": "despawn", "id": u_id}}, curr_time, self.server.sid)
					else:
						self.server.tss.addCommand(command, curr_time, self.server.sid) #FIXME - when a dragon is hit, it might die and we have to broadcast the despawn, etc

				except Exception, e:
					log.println("Error handling commands: " + str(e) + str(type(e)), 2, ['command', 'error']) #FIXME - when a client dies this gives an assertion error
					toRemove.append(client)

		for server in self.server.neighbours:
			if server.conn in readable:
				try:
					command = receive(server.conn)

					assert command["type"] == "command" #Server should otherwise only send commands to each other probably
					#FIXME check the last time it sent report? probably should do the trick described in broadcastCommand instead
					self.server.tss.addCommand(command, command["content"]["timestamp"], server.sid) #FIXME - add server ID probably to solve conflicts and flag saying its a foreign command and shouldt be broadcasted again
				except Exception, e:
					log.println("Error handling server commands: " + str(e) + str(type(e)), 2, ['command', 'error'])
					toRemove.append(server)
		for node in toRemove:
			node.remove()
		self.server.tss.executeCommands(curr_time)

	def run(self):
		begin = self.server.timer.getTime()
		while 1:
			current = self.server.timer.getTime()
			if current-begin > self.TIME_BETWEEN_REPORT: #Check if the time to handle clients has passed so the state should be changed to sendReport
				break
			elif current > self.server.timeToSynch:
				self.server.state = SynchronizeTimeState(self.server)
				return
			elif current > self.server.nextTime:
				self.server.time += 1
				self.server.nextTime = self.server.timer.getTime() + 1 #FIXME time until next turn
				commands = self.server.tss.trailingStates[0].board.dragonsAI(self.server.time) #FIXME - dragons not attacking sometimes. probably has to do with timeout in select 
				if commands:
					for command in commands:
						self.server.tss.addCommand(command, current, self.server.sid)

			toCheck = [i.conn for i in self.server.clients]
			toCheck.append(self.server.sock)
			toCheck.append(self.server.med_sock)
			for server in self.server.neighbours:
				toCheck.append(server.conn)

			timeout = min(self.server.nextTime-current,(self.TIME_BETWEEN_REPORT+begin-current)) #FIXME - is timeout correct? dragons are not attacking when they should
			readable, writeable, error = select.select(toCheck, [], [], timeout)

			if self.server.sock in readable:
				try:
					self.handleNewConnection(current)
				except Exception,e:
					log.println('Error receiving client: '+str(e), 1, ['error'])
				self.server.tss.executeCommands(current)

			elif self.server.med_sock in readable:
				''' Receive list of servers.
					For now I think it is the only thing the mediator sends the servers '''
				message = receive(self.server.med_sock)
				if message["type"] == "ServerList":
					#TODO Create serverConn for every new server on the list
					#self.server.neighbours = message["content"]["servers"]
					neighboursList = message["content"]["servers"] #(ip,port)

					#self.server.createServerSocket(neighboursList) #Dont do this anymore here

					log.println('Server neighbour list updated: '+str(self.server.neighbours), 1, ['update'])
				elif message["type"] == "Error":
					self.server.med_sock = None
					self.server.state = InitialState(self.server) #Seek for another mediator
					return
			else:
				#Client commands
				self.handleCommands(readable, current)

		self.server.state = SendReportState(self.server)


class SynchronizeTimeState():
	''' All states have function "run" '''
	def __init__(self, server):
		self.server = server
		self.stateName = "Synchronization state"
	def run(self):
		''' Run synchronization algorithm:
				Send message to mediator
				Receive T1 from mediator (T1 is the time.time() at the mediator when the mediator sends this message)
				Let x be the time that it took to send and receive that answer. x = Tsend + Treceive. Lets assume Tsend = Treceive
				Let T be the time the server should have. T = T1 + Treceive =~ T1 + (Tsend + Treceive) / 2 = T1 + x / 2
				For precision, repeat this process a few times and calculate an average for x/2.
			TODO: the last step (precision) '''
		try:
			msg = json.dumps({"type":"Synch", "content":"Give me your time"})

			T0 = time.time()
			send(self.server.med_sock, msg)
			T1 = receive(self.server.med_sock)
			T2 = time.time()
			x = T2 - T0

			assert T1["type"] == "Synch"
			T1 = float(T1["content"])

			print '\nx: ' + str(x) + ' | TIME AT MEDIATOR: ' + str(T1 + x/2) + '\n' #FIXME remove this print

			self.server.timer.timeDiff = T2 - (T1 + x/2)
			self.server.timeToSynch = self.server.timer.getTime()+200 #FIXME each 200 seconds the server synchronizes
			self.server.state = HandleClientsState(self.server)

		except Exception, e:
			log.println("Error in SynchronizeTimeState: " + str(e), 2, ['error', 'synch'])
			self.server.state = InitialState(self.server)


class InitialState():
	''' All states have function "run"	'''
	def __init__(self, server):
		self.server = server
		self.stateName = "Initial State"
	def run(self):
		self.server.publish()
		self.server.state = SynchronizeTimeState(self.server)
		try:
			message = receive(self.server.med_sock)
			assert message["type"] == 'ServerList'
			neighbours = message["content"]["servers"]
			self.server.curr_id = len(neighbours)*1000
			if len(neighbours) != 1: #If the server is the only one in the network it should generate the board and spawn the dragons
				log.println("I am not the first in the networkd. I should ask for the board.", 1)
				self.server.createServerSocket(neighbours)
				#neighbourConn = random.choice(self.server.neighbours) #FIXME Choose any of the neighbours to ask for the board. May cause problems
			else:
				self.server.spawnDragons()


		except Exception, e:
			log.println("Error in InitialState: " + str(e) + str(type(e)), 2, ['error', 'init'])


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
		self.timer = Timer()
		self.timeToSynch = None


		self.time = 0 #TURN
		self.nextTime = self.timer.getTime() + 1 #FIXME time until next turn
		self.curr_id = 1 #Next ID to assign
		#################

		self.clients = []

		self.tss = TSS(self)
		self.sid = (self.local_ip, self.local_port)

	def spawnDragons(self):
		i = 0
		while i < DRAGONS_TO_SPAWN:
			x = random.randint(0,24)
			y = random.randint(0,24)
			if self.tss.trailingStates[0].board.board[x][y].name == 'empty':
				for tss in self.tss.trailingStates:
					tss.board.insertObject(Dragon(x,y,self.curr_id))
				self.curr_id += 1
				i += 1

	def createServerSocket(self,neighboursList):
		''' Receives a list of (ip,port).Takes every item of the list and checks if it has been created and if not it adds them to the server list of neighbours'''
		alreadyCreated = False

		for serverIpPort in neighboursList:
			for serverConn in self.neighbours:

				if serverIpPort == serverConn.getIpPort():
					alreadyCreated = True
					break

			if not alreadyCreated and (serverIpPort[0] != self.local_ip or (serverIpPort[0] == self.local_ip and serverIpPort[1] != self.local_port)):  # if it is not created and it is not myself
				receivedBoard = False
				try:
					log.println("New server added to the list of servers", 1)
					serverSocket = socket(AF_INET, SOCK_STREAM)
					serverSocket.connect((serverIpPort[0], serverIpPort[1]))  # serverIpPort = (ip,port)

					server_connection = json.dumps(
						{"type": "ConnectionToServer", "content": {"nodeType": 1, "giveMeBoard": not receivedBoard}})
					try:
						send(serverSocket, server_connection)  # Indicate to the server that I am a server
						message = receive(serverSocket)
						if message["type"] == "InitialBoard":
							receivedBoard = True
							#Receive board here
							board = message["content"]["board"] #List of list of tuples
							commands = message["content"]["commands"]
							#Replace boards
							for ts in self.tss.trailingStates:
								for x in range(25):
									for y in range(25):
										if board[x][y][0] == 'dragon':
											newDragon = Dragon(x, y, board[x][y][1])
											newDragon.hp = board[x][y][2]
											newDragon.ap = board[x][y][3]
											ts.board.insertObject(newDragon)

										elif board[x][y][0] == 'player':
											newPlayer = Player(x, y, board[x][y][1])
											newPlayer.hp = board[x][y][2]
											newPlayer.ap = board[x][y][3]
											ts.board.insertObject(newPlayer)

							#Add commands
							for command in commands:
								self.tss.addCommand(command, command["content"]["timestamp"], command["issuedBy"]) #FIXME id of server should be put there when sending the board

					except Exception, e:
						log.println("Error indicating server that I am a server " + str(e), 1, ['Error'])

					self.neighbours.append(
						ServerConn(serverSocket, self, serverIpPort[0], serverIpPort[1]))
				except Exception, e:
					log.println("It was not possible to connect to the server: " + str(serverIpPort) + "|" + str(e),1,['Error'])

			alreadyCreated = False


	def checkIfSocketAlreadySaved(self,socket):

		alreadySaved = False
		for serverConn in self.neighbours:
			if serverConn.conn == socket:
				alreadySaved = True
				break

		return alreadySaved

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
				s.settimeout(1)
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
				if errors == 3: #Try three times before quitting [FIXME number of times]
					sys.exit()
				else:
					continue
			break

	def broadcastCommand(self, command, exceptClient=None, clientsOnly=False):
		''' FIXME should group commands and send them all at once right?'''
		toRemove = []
		for client in self.clients:
			if client != exceptClient:
				try:
					send(client.conn, json.dumps({"type": "command", "content": command}))
				except Exception, e:
					log.println("Error broadcasting command to client: " + str(e), 2, ['error'])
					toRemove.append(client)

		if not clientsOnly:
			for server in self.neighbours:
				try:
					send(server.conn, json.dumps({"type": "command", "content": command}))
				except Exception, e:
					log.println("Error broadcasting command to server: " + str(e), 2, ['error'])
					toRemove.append(server)

		for node in toRemove:
			node.remove()

PORT = 6971

try:
	PORT=int(sys.argv[1]) #optional port passing in case there are more than one server in the network.
except:
	print "Indicate port. Ex: 6971"
	PORT = int(raw_input("port: "))

s = Server(PORT, MED_LIST)

while 1:
	log.println(s.state.stateName,1,'state') #Debug
	s.run()
