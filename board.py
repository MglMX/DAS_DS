from empty import Empty

class Board:
	def  __init__(self):
			self.board = []
			for x in range(25):
				self.board.append([])
				for y in range(25):
					self.board[x].append(Empty(x,y))

	def insertObject(self, object):
			self.board[object.x][object.y] = object

	def getBoard(self):
		return [self.getLine(i) for i in self.board]
	def getLine(self, l):
		res = []
		for i in l:
			res.append((i.name, i.id, i.hp, i.ap, i.maxHP))
		return res

	def movePlayer(self, u_id, pos):
		player = self.findObject(u_id)
		if not player:
			return 0

		x = player.x
		y = player.y

		self.board[x][y] = Empty(x,y)
		self.board[pos[0]][pos[1]] = player
		self.board[pos[0]][pos[1]].x = pos[0]
		self.board[pos[0]][pos[1]].y = pos[1]
		return x,y

	def findObject(self, u_id):
		''' Finds the position of the object with id u_id in the board.
			Returns None if there is no such object '''
		for x in range(25):
			for y in range(25):
				if self.board[x][y].id == u_id:
					self.board[x][y].x = x
					self.board[x][y].y = y
					return self.board[x][y]

	def deleteObject(self,u_id):
		'''Finds the object with u_id and changes it for an empty object. It returns the coordinates where the object was'''
		for x in range(25):
			for y in range(25):
				if self.board[x][y].id == u_id:
					self.board[x][y] = Empty(x,y)
					return (x,y)

	def dragonsAI(self, time):
		commands = []
		for x in range(25):
			for y in range(25):
				if self.board[x][y].name == 'dragon':
					command = self.board[x][y].doAction(self, time)
					if command:
						commands.append(command)
		return commands