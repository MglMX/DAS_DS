#Consistency - TSS
from board import Board

class MoveCommand:
	def __init__(self, who, where):
		self.cmd = "move"
		self.who = who
		self.where = where
	def execute(self, board):
		#Execute command
		pass

class DamageCommand:
	def __init__(self, who, target):
		self.cmd = "damage"
		self.who = who
		self.target = target
	def execute(self, board):
		#Execute command
		pass

class HealCommand:
	def __init__(self, who, target):
		self.cmd = "heal"
		self.who = who
		self.target = target
	def execute(self, board):
		#Execute command
		pass

class SpawnCommand:
	def __init__(self, who):
		self.cmd = "spawn"
		self.who = who
	def execute(self, board):
		#Execute command
		pass

class DespawnCommand:
	def __init__(self, who):
		self.cmd = "despawn"
		self.who = who
	def execute(self, board):
		#Execute command
		pass


def createCmd(self, command, curr_time):
	''' Receives a string with the command received and creates a class Command with everything needed for consistency.
		Attention: curr_time is a time that will be shared with all the commands in the same round. that probably wont be a problem '''
	
	cmd = command["content"]["cmd"]
	who = command["content"]["id"]

	if cmd == "move":
		res = MoveCommand(who, command["content"]["where"]) #We want move commannds to have an id with the guy to move
	elif cmd == "damage":
		res = DamageCommand(command["content"]["subject"], who) #We want damage and heal commands to have a "subject" filed with the guy doing the damage/healing
	elif cmd == "heal":
		res = HealCommand(command["content"]["subject"], who)
	elif cmd == "spawn":
		res = SpawnCommand(who)
	elif cmd == "despawn":
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
		self.commands = [] #List of commands ordered by timestamp
	def addCommand(self, command):
		i = 0
		for i in range(len(self.commands)): #Find the place to put the command
			if self.commands[i].timestamp > command.timestamp:
				break
		self.commands = self.commands[:i] + [command] + self.commands[i:]
	def executeCommands(self, curr_time, board):
		''' Also check for inconsistencies. Rollback if needed '''
		for command in self.commands:
			if command[i].timestamp > curr_time-delay:
				break
			#Execute commands
			command.execute(board) #check result from this and the preceding state. if they differ, signal rollback
			if command.preceding: #If there's a preceding state
				if command.result != command.preceding.result:
					pass #SIGNAL ROLLBACK HERE - TODO

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
			ts.executeCommands(curr_time)
