from Unit import Unit

MIN_TIME_BETWEEN_TURNS = 2
MAX_TIME_BETWEEN_TURNS = 7
MAX_HITPOINTS = 20
MIN_HITPOINTS = 10
MIN_ATTACKPOINTS = 1
MAX_ATTACKPOINTS = 10


class Player(Unit):
	def __init__(self, x, y, u_id, isUser=False):
		super(Player, self).__init__(x,y, MIN_HITPOINTS, MAX_HITPOINTS, MIN_ATTACKPOINTS, MAX_ATTACKPOINTS, u_id)
		self.name = 'player'
		self.isUser = isUser

	def healDamage(self, board, x, y): 	
		if board.board[x][y].name == 'player':
			board.board[x][y].adjustHitPoints(self.ap)