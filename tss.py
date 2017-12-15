#Consistency - TSS
from board import Board
from empty import Empty
from Player import Player
from Dragon import Dragon

import sys #TODO remove me

class MoveCommand:
	def __init__(self, who, where):
		self.cmd = "move"
		self.who = who #id
		self.where = where #pos(x,y)

	def execute(self, board):
		#Execute command
		x,y = self.where
		obj = board.findObject(self.who)
		if board.board[x][y].name != 'empty' or not obj:
			#Ignore this command if it can't be executed
			self.result = 'invalid'
			self.antiCommand = None
			return None #Dont broadcast anything
		else: #FIXME use movePlayer function
			oldPosition = (obj.x,obj.y)
			board.board[x][y] = obj
			board.board[obj.x][obj.y] = Empty(obj.x, obj.y)
			obj.x = x
			obj.y = y
			self.result = {"id":self.who, "where": self.where} #It means now id is where
			self.antiCommand = {"cmd": "move", "where": oldPosition}
			return {"cmd": "move", "where": self.where, "id": self.who} #Broadcast this to servers and clients


class DamageCommand:
	def __init__(self, who, target):
		self.cmd = "damage"
		self.who = who
		self.target = target

	def execute(self, board):
		obj = board.findObject(self.who)
		target = board.findObject(self.target)
		if not obj or not target:
			self.result = 'invalid'
			self.antiCommand = None
			return None #Broadcast nothing
		else:
			obj.dealDamage(board, target.x, target.y)
			if target.hp != 0:
				self.result = {"id": self.target, "hp": target.hp} #It means now id has hp
				self.antiCommand = {"cmd": "heal", "subject": self.who, "id":self.target}
				return {"cmd": "damage", "subject": self.who, "id": self.target, "finalHP": target.hp} #Broadcast this to servers and clients
			else:
				oldPlayer = {"x": target.x, "y": target.y, "id": target.id, "hp": target.hp, "ap": target.ap}
				board.board[target.x][target.y] = Empty(obj.x, obj.y)
				self.result = {"x":target.x, "y": target.y, "player": None} #There is no player at x,y
				self.antiCommand = {"cmd": "spawn", "player": oldPlayer}
				return {"cmd": "despawn", "id": target.id}


class HealCommand:
	def __init__(self, who, target):
		self.cmd = "heal"
		self.who = who
		self.target = target
	def execute(self, board):
		obj = board.findObject(self.who)
		target = board.findObject(self.target)
		if not obj or not target:
			self.result = 'invalid'
			self.antiCommand = None
			return None #Broadcast nothing
		else:
			obj.healDamage(board, target.x, target.y)
			self.result = {"id": self.target, "hp": target.hp} #It means now id has hp
			self.antiCommand = {"cmd": "damage", "subject": self.who, "id":self.target}
			return {"cmd": "heal", "subject": self.who, "id": self.target, "finalHP": target.hp} #Broadcast this to servers and clients


class SpawnCommand:
	def __init__(self, unit):
		self.cmd = "spawn"
		self.unit = unit

	def execute(self, board):
		x = self.unit["x"]
		y = self.unit["y"]
		u_id = self.unit["id"]
		hp = self.unit["hp"]
		ap = self.unit["ap"]
		obj = board.findObject(u_id)
		if obj or board.board[x][y].name != 'empty':
			self.result = 'invalid'
			self.antiCommand = None
			return None #Broadcast nothing
		else:
			player = Player(x, y, u_id) #Players are the only ones that are spawn dynamically
			board.insertObject(player)
			self.result = {"x":x, "y":y,"player": self.unit} #There is a player in x,y
			self.antiCommand = {"cmd": "despawn", "id":u_id}
			return {"cmd": "spawn", "player": self.unit} #Broadcast this to servers and clients

class DespawnCommand:
	def __init__(self, who):
		self.cmd = "despawn"
		self.who = who

	def execute(self, board):
		obj = board.findObject(self.who)
		if not obj:
			self.result = 'invalid'
			self.antiCommand = None
			return None #Broadcast nothing
		else:
			oldPlayer = {"x": obj.x, "y": obj.y, "id": obj.id, "hp": obj.hp, "ap": obj.ap}
			board.board[obj.x][obj.y] = Empty(obj.x, obj.y)
			self.result = {"x":obj.x, "y": obj.y, "player": None} #There is no player at x,y
			self.antiCommand = {"cmd": "spawn", "player": oldPlayer}
			return {"cmd": "despawn", "id": self.who}


def createCmd(command, curr_time, issuedBy):
	''' Receives a string with the command received and creates a class Command with everything needed for consistency.
		Attention: curr_time is a time that will be shared with all the commands in the same round. that probably wont be a problem '''

	cmd = command["content"]["cmd"]


	if cmd == "move":
		who = command["content"]["id"]
		res = MoveCommand(who, command["content"]["where"]) #We want move commannds to have an id with the guy to move
	elif cmd == "damage":
		who = command["content"]["id"]
		res = DamageCommand(command["content"]["subject"], who) #We want damage and heal commands to have a "subject" filed with the guy doing the damage/healing
	elif cmd == "heal":
		who = command["content"]["id"]
		res = HealCommand(command["content"]["subject"], who)
	elif cmd == "spawn":
		res = SpawnCommand(command["content"]["player"])
	elif cmd == "despawn":
		who = command["content"]["id"]
		res = DespawnCommand(who)
	else:
		return
	res.timestamp = curr_time #Timestamp added to each command
	res.result = None #When result is none, the command wasn't executed
	res.issuedBy = issuedBy #Server id that issued this command
	return res


class TrailingState:
	def __init__(self, tss, delay, index,last=False):
		''' Server is the server.
			Delay is the delay in ms where commands will be executed in this trailing state
			Index is the position of this TrailingState in the list of TrailingStates (so we know which state is the preceding)
			last is a flag indicating if this TSS is the last on the list
		'''
		self.delay = float(delay) / 1000
		if index == 0: #First state has no trailing state
			self.preceding = None
		else:
			self.preceding = tss.trailingStates[index-1]

		self.lastTSS = last
		self.board = Board()
		self.commands = [] #List of commands ordered by timestamp. Older commands first

	def addCommand(self, command):
		i = 0
		size = len(self.commands)
		while i < size: #Find the place to put the command
			if self.commands[i].timestamp > command.timestamp:
				break
			i += 1

		while i > 0:
			i -= 1
			if self.commands[i].timestamp < command.timestamp or self.commands[i].issuedBy >= command.issuedBy:
				#Solve conflicts using the server ids
				i += 1
				break

		self.commands = self.commands[:i] + [command] + self.commands[i:]

	def executeRollBack(self, command, nr=0):
		#Copy the board from this ts to the preceding ts's.
		if not self.preceding:
			return nr

		board = self.board.getBoard()
		self.preceding.board = Board()
		for x in range(25):
			for y in range(25):
				if board[x][y][0] == 'dragon':
					newDragon = Dragon(x, y, board[x][y][1])
					newDragon.hp = board[x][y][2]
					newDragon.ap = board[x][y][3]
					self.preceding.board.insertObject(newDragon)

				elif board[x][y][0] == 'player':
					newPlayer = Player(x, y, board[x][y][1])
					newPlayer.hp = board[x][y][2]
					newPlayer.ap = board[x][y][3]
					newPlayer.maxHP = board[x][y][4]
					self.preceding.board.insertObject(newPlayer)

		#Mark all the commands with timestamp > command.timestamp from the preceding ts as not executed

		nr = 0
		for i in range(len(self.preceding.commands)-1,-1,-1):
			commandPrec = self.preceding.commands[i]
			if commandPrec.timestamp > command.timestamp:
				commandPrec.result = None
				nr += 1 #Probably variable i would be enough but whatever
			else:
				break

		#TODO If the real-time ts commands were marked as not executed, broadcast the antiCommands for the users
			#Easier way to do it: Clients have a list of commands and servers just tells the client how many commands to go back
		return self.preceding.executeRollBack(command.preceding, nr) #Rollbacks should have a domino effect on all preceding states

	def executeCommands(self, curr_time):
		''' Also check for inconsistencies. Rollback if needed '''
		commandsToBroadCast = []
		rollBack = None

		toRemove = [] #Commands to remove in case this is the last tss

		for command in self.commands:
			if command.timestamp > curr_time-self.delay:
				break
			#Execute commands
			if not command.result: #If command wasn't executed before
				toBroadCast = command.execute(self.board) #check result from this and the preceding state. if they differ, signal rollback
				if command.preceding: #If there's a preceding state
					if command.result != command.preceding.result:
						rollBack = command
						break
					else:
						if self.lastTSS:
							toRemove.append(command)
				elif toBroadCast:
					toBroadCast["issuedBy"] = command.issuedBy
					toBroadCast["timestamp"] = command.timestamp
					commandsToBroadCast.append(toBroadCast)

		if rollBack:
			nr = self.executeRollBack(command)
			if nr:
				commandsToBroadCast.append({"cmd": "rollback", "number": nr})

		for command in toRemove:
			self.deleteCommand(command)

		return commandsToBroadCast

	def deleteCommand(command):
		if self.preceding:
			self.preceding.deleteCommand(command.preceding) #Domino effect on deleting command

		self.commands.remove(command)

class TSS:
	def __init__(self, server):
		''' Creates trailing states '''
		self.server = server

		self.trailingStates = []
		self.trailingStates.append(TrailingState(self, 0, 0))
		self.trailingStates.append(TrailingState(self, 100, 1))
		self.trailingStates.append(TrailingState(self, 200, 2))

	def addCommand(self, command, curr_time, issuedBy):
		preceding = None
		for ts in self.trailingStates:
			cmd = createCmd(command, curr_time, issuedBy)
			cmd.preceding = preceding #Same commands are connected
			preceding = cmd
			ts.addCommand(cmd)

	def executeCommands(self, curr_time):
		''' Also check for inconsistencies. Rollback if needed '''
		for ts in self.trailingStates:
			toBroadCast = ts.executeCommands(curr_time)
			for cmd in toBroadCast:
				if "issuedBy" in cmd and cmd["issuedBy"] == self.server.sid:
					self.server.broadcastCommand(cmd) #We only want to broadcast commands sent by this server
				else:
					self.server.broadcastCommand(cmd, clientsOnly=True) #Dont broadcast what is not ours to other servers
