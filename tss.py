#Consistency - TSS
from board import Board
from empty import Empty
from Player import Player

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
			return {"cmd": "move", "where": self.where, "id": self.who, "timestamp": self.timestamp} #Broadcast this to servers and clients

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
				print '\n',target.name,'DEAD\n\n'
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
			print '\nSPAWWWWNING\n\n\n'
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
			print '\nDESPAWNING\n'
			oldPlayer = {"x": obj.x, "y": obj.y, "id": obj.id, "hp": obj.hp, "ap": obj.ap}
			board.board[obj.x][obj.y] = Empty(obj.x, obj.y)
			self.result = {"x":x, "y": y, "player": None} #There is no player at x,y
			self.antiCommand = {"cmd": "spawn", "player": oldPlayer}
			return {"cmd": "despawn", "id": self.who}



def createCmd(command, curr_time):
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
		print 'Invalid command',command
		return
	res.timestamp = curr_time #Timestamp added to each command
	res.result = None #When result is none, the command wasn't executed
	return res


class TrailingState:
	def __init__(self, tss, delay, index):
		''' Server is the server.
			Delay is the delay in ms where commands will be executed in this trailing state
			Index is the position of this TrailingState in the list of TrailingStates (so we know which state is the preceding)
		'''
		self.delay = float(delay) / 1000
		if index == 0: #First state has no trailing state
			self.preceding = None
		else:
			self.preceding = tss.trailingStates[index-1]

		self.board = Board()
		self.commands = [] #List of commands ordered by timestamp. Older commands first
	def addCommand(self, command):
		i = 0
		for i in range(len(self.commands)): #Find the place to put the command
			if self.commands[i].timestamp > command.timestamp: #FIXME - SOLVE CONFLICTS CRITICAL: while timestamps are equal, go back, unless there's a command of the same type but the serverID is lower or something 
				break
		self.commands = self.commands[:i] + [command] + self.commands[i:]
	def executeCommands(self, curr_time):
		''' Also check for inconsistencies. Rollback if needed '''
		commandsToBroadCast = []
		for command in self.commands:
			if command.timestamp > curr_time-self.delay:
				break
			#Execute commands
			if not command.result: #If command wasn't executed before
				toBroadCast = command.execute(self.board) #check result from this and the preceding state. if they differ, signal rollback
				if command.preceding: #If there's a preceding state
					if command.result != command.preceding.result:
						pass #SIGNAL ROLLBACK HERE - TODO
				elif toBroadCast:
					commandsToBroadCast.append(toBroadCast)
					print 'goingToBroadCast:',toBroadCast
		return commandsToBroadCast

class TSS:
	def __init__(self, server):
		''' Creates trailing states '''
		self.server = server

		self.trailingStates = []
		self.trailingStates.append(TrailingState(self, 0, 0))
		self.trailingStates.append(TrailingState(self, 100, 1))
		self.trailingStates.append(TrailingState(self, 200, 2))
	def addCommand(self, command, curr_time):
		preceding = None
		for ts in self.trailingStates:
			cmd = createCmd(command, curr_time)
			cmd.preceding = preceding #Same commands are connected 
			preceding = cmd
			ts.addCommand(cmd)

	def executeCommands(self, curr_time):
		''' Also check for inconsistencies. Rollback if needed '''
		for ts in self.trailingStates:
			toBroadCast = ts.executeCommands(curr_time)
			for cmd in toBroadCast:
				self.server.broadcastCommand(cmd)