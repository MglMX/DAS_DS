import random

class Unit(object):
	def __init__(self, x, y, minHitPoints, maxHitPoints, minAttackPoints, maxAttackPoints, unitID):
		self.x = x
		self.y = y
		
		#I dont think we need this
		#self.minHitPoints = minHitPoints
		#self.maxHitPoints = maxHitPoints
		#self.minAttackPoints = minAttackPoints
		#self.maxAttackPoints = maxAttackPoints

		self.id = unitID
		self.name = 'Unit' #Dragons should be 'dragon'. Players should be 'player'
		self.hp = random.randint(minHitPoints, maxHitPoints)
		self.ap = random.randint(minAttackPoints, maxAttackPoints)
		self.maxHP = self.hp


	def adjustHitPoints(self, modifier):
		if(self.hitPoints <= 0):
			return

		self.hitPoints += modifier

		if(self.hitPoints > self.maxHitPoints):
			self.hitPoints = maxHitPoints

		if(self.hitPoints <= 0):
			self.removeUint(x, y)

	  
	def dealDamage(self, board, x, y):
		if board.board[x][y].name == 'dragon':
			board.board[x][y].adjustHitPoints(-self.ap)

	def setPosition(self, x, y):
		self.x = x
		self.y = y
















