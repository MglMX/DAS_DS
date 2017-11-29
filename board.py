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

