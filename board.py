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
			res.append((i.name, i.id, i.hp, i.ap))
		return res

	def movePlayer(self, u_id, pos):
		pos2 = self.findObject(u_id)
		if not pos2:
			return 0

		x = pos2[0]
		y = pos2[1]

		self.board[pos[0]][pos[1]] = self.board[x][y]
		self.board[x][y] = Empty(x,y)
		self.board[pos[0]][pos[1]].x = pos[0]
		self.board[pos[0]][pos[1]].y = pos[1]
		return 1

	def findObject(self, u_id):
		''' Finds the position of the object with id u_id in the board.
			Returns None if there is no such object '''
		for x in range(25):
			for y in range(25):
				if self.board[x][y].id == u_id:
					return x,y