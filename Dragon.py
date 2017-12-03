from Unit import Unit
import random, math

MIN_TIME_BETWEEN_TURNS = 2;
MAX_TIME_BETWEEN_TURNS = 7;
MIN_HITPOINTS = 50;
MAX_HITPOINTS = 100;
MIN_ATTACKPOINTS = 5;
MAX_ATTACKPOINTS = 20;

def distance(pos1, pos2):
	#"the distance between two squares is the sum of the horizontal and vertical distance between them"
	return abs(pos1[0]-pos2[0]) + abs(pos1[1]-pos2[1])

class Dragon(Unit):

	def __init__(self, x, y, u_id):
		super(Dragon, self).__init__(x,y, MIN_HITPOINTS, MAX_HITPOINTS, MIN_ATTACKPOINTS, MAX_ATTACKPOINTS, u_id)
		self.name = 'dragon'
		self.turn = 0
		self.nextTurn = random.randint(MIN_TIME_BETWEEN_TURNS, MAX_TIME_BETWEEN_TURNS)


	def doAction(self, board):
		''' A.I : Sleep while Dragon can't move. Do nothing if dragon is dead. Pick random player close to itself to attack '''
		self.turn += 1
		if self.turn == self.nextTurn: #Wakes up
			self.turn = 0
			self.nextTurn = random.randint(MIN_TIME_BETWEEN_TURNS, MAX_TIME_BETWEEN_TURNS)

			if self.hp <= 0: #If dragon is dead, do nothing
				return 0

			adjPlayers = []
			for x in range(25):
				for y in range(25):
					if board[x][y].name == 'player' and distance((self.x,self.y), (x,y)) <= 2:
						adjPlayers.append((x,y))
			if adjPlayers: #Attack player
				player = random.choice(adjPlayers)
				self.dealDamage(board, player[0], player[1])
				return player


		return 0