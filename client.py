from utils  import * #receive and send
from socket import *
from gui    import Gui, Dragon, Player
from board  import Board
from empty  import Empty
import pygame, sys, time

from threading import Thread, Semaphore #There is a thread waiting for server commands and updating the gui

class Client:
	def __init__(self, med_list):
		self.s = None #Will hold the connection between client and server
		self.med_list = med_list

		ip, port = self.getServer() #Fetch a server from the mediator

		self.s = socket(AF_INET, SOCK_STREAM) 
		self.s.connect((ip, port))  #Connect to server
		self.board = Board()
		self.lock = Semaphore()

		self.changed = 0 #Board has changed FIXME testing purposes mostly
		print 'Successfully connected.'
		self.lookupAnotherServer = False

	def getServer(self):
		print "Inside getServer"
		errors = 0
		while 1:
			for mediator in range(len(self.med_list)): #Trying all the possible mediators.
				s = socket(AF_INET, SOCK_STREAM)
				s.settimeout(0.5)
				ip = self.med_list[mediator][0]
				port = self.med_list[mediator][1]
				try:
					s.connect((ip, port)) #Connect to mediator
					nodeType = json.dumps({"type":"InitialConnection","content":{"nodeType":0}}) #JSon indicating that it is a client trying to connect
					send(s, nodeType)
					print "I indicated the mediator that I am a client"
					message = receive(s)								#Receive server ip and port
					print "Received server to connect to"
					break								
				except Exception, e:
					print 'Mediator number %s is not active: %s' % (mediator,e)
			else:
				errors += 1
				if errors == 3:
					print 'There is no active mediator...'
					sys.exit(0)
				else:
					print 'Trying again...'
					time.sleep(1)
					continue
			break
		if message["type"]=="Error":
			print "The was an error while getting the server Info"
			print message
			sys.exit()
		elif message["type"]=="ServerInfo":
			print "Getting server info"
			server = (message["content"]["ip"],message["content"]["port"])
			return server

	def serverConnectionDaemon(self):
		try:
			while 1:
				command = receive(self.s)
				assert command["type"] == "command"
				command = command["content"]
				self.lock.acquire()
				if command["cmd"] == "move":
					u_id = command["id"]
					pos = command["where"]

					print 'Moving player:',u_id,'to',pos
					self.board.movePlayer(u_id, pos)
					self.changed = 1
				self.lock.release()


		except Exception,e:
			print 'Error ready command: ' + str(e) #TODO - Try to find another server or something
			self.lock.acquire()
			self.lookupAnotherServer = True
			self.lock.release()
			return

	def receiveBoard(self) :
		msg = receive(self.s)
		assert msg["type"] == "board"
		msg = msg["content"]
		
		boardServer = msg["board"]
		playerID = msg["ID"]
		player = None

		for x in range(25):
			for y in range(25):
				if boardServer[x][y][0] == 'dragon':
					self.board.insertObject(Dragon(x, y, boardServer[x][y][1]))
				elif boardServer[x][y][0] == 'player':
					if boardServer[x][y][1] != playerID:
						self.board.insertObject(Player(x, y, boardServer[x][y][1]))
					else:
						player = Player(x, y, playerID, isUser=True)
						self.board.insertObject(player)
		return player

	def sendCommand(self, command):
		''' FIXME - This shouldnt receive a json. Or should it? '''
		try:
			send(self.s, command)
		except Exception, e:
			print 'Error sending command:',e
			self.lookupAnotherServer = True

	def runGame(self):
		''' Careful with accessing shared resources. Use locks. '''

		#Setup daemon to continuosly run commands
		t = Thread(target=self.serverConnectionDaemon)
		t.setDaemon(True)

		gui = Gui()
		player = s.receiveBoard()

		self.changed = 1
		t.start() #Start daemon after receiving the full board

		#drag1 = Dragon(5,6)
		#board.insertObject(drag1)
		#drag2 = Dragon(9,6)
		#board.insertObject(drag2)
		#play1 = Player(14, 12)
		#board.insertObject(play1)
		#play2 = Player(15, 12)
		#board.insertObject(play2)

		
		while 1:
			self.lock.acquire()
			if self.lookupAnotherServer:

				self.lookupAnotherServer = False
				#FIXME code duplication
				self.board = Board()
				ip, port = self.getServer() #Fetch a server from the mediator
				self.s = socket(AF_INET, SOCK_STREAM) 
				self.s.connect((ip, port))  #Connect to server
				#Here we should send a message saying we would like to restore our previous state if possible

				t = Thread(target=self.serverConnectionDaemon)
				t.setDaemon(True)
				player = s.receiveBoard()
				self.changed = 1
				t.start() #Start daemon after receiving the full board


			if self.changed:
				self.changed = 0
				gui.screen.fill((0,0,0)) #Clear screen
				gui.drawLines()			 #Draw grid
				gui.drawUnits(self.board.board)
			event = gui.handleEvents(player, self.board.board)	
			if event != 0:
				self.changed = 1
			
			if event in (1,2,3,4):   #Left
				self.sendCommand(json.dumps({"type":"command", "content": {"cmd": "move", "id": player.id, "where": (player.x, player.y)}}))
			self.lock.release()

			#Switch case event for movement
			pygame.display.flip()


s = Client(MED_LIST)
s.runGame()