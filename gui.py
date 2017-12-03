import pygame,random,sys
from board import Board
from empty import Empty

pygame.init()
class Gui:
	def __init__(self):
		self.WIDTH = 500
		self.HEIGHT = 500
		self.scale = (self.WIDTH/25, self.HEIGHT/25)
		self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))

	def drawLines(self):
		for x in range(25):
			pygame.draw.line(self.screen, (255,255,255), (x*self.scale[0],0), (x*self.scale[0], self.HEIGHT))
			pygame.draw.line(self.screen, (255,255,255), (0,x*self.scale[1]), (self.WIDTH,x*self.scale[1]))
	def drawUnits(self, unitBoard):
		for x in range(25):
			for y in range(25):
				if unitBoard[x][y].name == 'dragon':
					pygame.draw.rect(self.screen, (int(unitBoard[x][y].hp*2.55),0,0), (x*self.scale[0],y*self.scale[1], self.scale[0], self.scale[1]))
				elif unitBoard[x][y].name == 'player':
					pygame.draw.rect(self.screen, (0,0,int(unitBoard[x][y].hp*12.7)), (x*self.scale[0],y*self.scale[1], self.scale[0],self.scale[1]))
	def handleEvents(self, play, board):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()
			elif event.type == 2:
				if event.key == 276:
					if 0 < play.x and board[play.x-1][play.y].name == 'empty':
						play.x = play.x - 1
						#board[play.x][play.y] = play
						#board[play.x+1][play.y] = Empty(play.x+1,play.y)
						print 'left', play.x
						return 1
				elif event.key == 273:
					if 0 < play.y and board[play.x][play.y-1].name == 'empty':
						play.y = play.y - 1
						#board[play.x][play.y] = play
						#board[play.x][play.y+1] = Empty(play.x,play.y+1)
						print 'up', play.y
						return 2	
				elif event.key == 275:
					if 24 > play.x  and board[play.x+1][play.y].name == 'empty':
						play.x = play.x + 1
						#board[play.x][play.y] = play
						#board[play.x-1][play.y] = Empty(play.x-1,play.y)
						print 'right', play.x
						return 3
				elif event.key == 274:
					if 24 > play.y and board[play.x][play.y+1].name == 'empty':
						play.y = play.y + 1
						#board[play.x][play.y] = play
						#board[play.x][play.y-1] = Empty(play.x,play.y-1)
						print 'down', play.y
						return 4	
				elif event.key == 32:
					print 'fire'
				else:
					print event.key
				return 0
			elif event.type == 5:
				(x,y) = event.pos
				x = x/20
				y = y/20
				print x, y
				if board[x][y].name == 'dragon' and abs(play.x-x) + abs(play.y-y) <= 2:
					#attack
					print 'attack dragon'
					return (x,y)
				elif board[x][y].name == 'player' and abs(play.x-x) + abs(play.y-y) <= 5:
					#heal
					print 'heal player'
					return (x,y)
		return 0
