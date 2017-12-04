from utils  import * #receive and send
from socket import *
from gui    import Gui
from Dragon import Dragon
from Player import Player
from board  import Board
from empty  import Empty
from clientAI import clientAI
import pygame, sys, time, random

from threading import Thread, Semaphore #There is a thread waiting for server commands and updating the gui

class Client:
	def __init__(self, med_list, reuse_id=None, reuse_gui=None):
		self.s = None #Will hold the connection between client and server
		self.med_list = med_list

		ip, port = self.getServer() #Fetch a server from the mediator

		self.s = socket(AF_INET, SOCK_STREAM) 
		self.s.connect((ip, port))  #Connect to server
		self.s.settimeout(2) #FIXME timeout 
		self.board = Board()
		self.lock = Semaphore()

		if reuse_id:
			self.id = reuse_id

		self.changed = 0 #Board has changed
		print 'Successfully connected.'
		self.lookupAnotherServer = False

		if not reuse_gui:
			self.gui = Gui()
		else:
			self.gui = reuse_gui

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

				if command["type"] == "Error":
					if command["content"]["info"] == "timedout":
						continue

				assert command["type"] == "command"
				command = command["content"]
				self.lock.acquire()

				if command["cmd"] == "move": #MOVE CMD
					u_id = command["id"]
					pos = command["where"]

					print 'Moving player:',u_id,'to',pos
					self.board.movePlayer(u_id, pos)
					self.changed = 1

				elif command["cmd"] == "spawn" : #SPAWN CMD
					player = command["player"]
					x = player["x"]
					y = player["y"]
					u_id = player["id"]
					hp = player["hp"]
					ap = player["ap"]
					player = Player(x,y,u_id)
					player.hp = hp
					player.ap = ap
					self.board.board[x][y] = player
					self.changed = 1

				elif command["cmd"] == "despawn":
					u_id = command["playerID"]
					pos = self.board.findObject(u_id)
					if pos:
						x,y = pos
						if self.board.board[x][y].name == 'player':
							self.board.board[x][y] = Empty(x,y)
							self.changed = 1

				elif command["cmd"] == "heal":
					u_id = command["id"]
					#Heal player
					x,y = self.board.findObject(u_id)
					self.board.board[x][y].healDamage(self.board, x, y)
					self.changed = 1
				elif command["cmd"] == "damage":
					u_id = command["id"]
					#Damage dragon
					x,y = self.board.findObject(u_id)
					self.board.board[x][y].dealDamage(self.board, x, y)
					self.changed = 1
				self.lock.release()

		except Exception,e:
			print 'Error ready command: ' + str(e)
			print type(e)
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

		self.id = playerID
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

		
		self.player = s.receiveBoard()

		self.changed = 1
		t.start() #Start daemon after receiving the full board

		while 1:
			self.lock.acquire()

			if self.lookupAnotherServer:
				self.s.close()
				self.lock.release()
				t.join()
				return 0

			if self.changed:
				self.changed = 0
				self.gui.drawLines()			 #Draw grid
				self.gui.drawUnits(self.board.board)

			event = self.gui.handleEvents(self.player, self.board.board)
			if event != 0:
				self.changed = 1
			
			if event in (1,2,3,4):   #Left
				self.sendCommand(json.dumps({"type":"command", "content": {"cmd": "move", "id": self.player.id, "where": (self.player.x, self.player.y)}}))
			elif event != 0:
				target = self.board.board[event[0]][event[1]]
				if target.name == 'dragon':
					cmd = "damage"
				elif target.name == 'player':
					cmd = "heal"
				else:
					continue
				self.sendCommand(json.dumps({"type":"command", "content": {"cmd": cmd, "id": target.id}}))
			self.lock.release()

			#Switch case event for movement
			pygame.display.flip()




#s = Client(MED_LIST)
s = Client(MED_LIST,reuse_gui=clientAI()) #Comment in order to not use AI
while 1:
	status = s.runGame()
	if s.lookupAnotherServer: #Server crashed or something
		s = Client(MED_LIST, reuse_id=s.id, reuse_gui=s.gui)