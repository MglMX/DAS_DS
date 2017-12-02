class Unit:
    def __init__(self, x, y, maxHitPoints, hitPoints, attackPoints, unitID):
		self.x = x
		self.y = y
		self.maxHitPoints = maxHitPoints
		self.hitPoints = hitPoints
		self.attackPoints = attackPoints
		self.unitID = unitID
		self.running = false

    def adjustHitPoints(modifier):
		if(self.hitPoints <= 0):
			return

		self.hitPoints += modifier

		if(self.hitPoints > self.maxHitPoints):
			self.hitPoints = maxHitPoints

		if(self.hitPoints <= 0):
			self.removeUint(x, y)

	  
    def dealDamage(x, y, damage):
        ''' TODO '''
        pass

    def healDamage(x, y, healed): 	
    	''' TODO '''
    	pass

    def getMaxHitPoints():
    	return self.maxHitPoints

    def getUnitID():
		return self.unitID


    def setPosition(x, y):
		self.x = x
		self.y = y


    def getX():
		return self.x

    def getY():
		return self.y


    def getHitPoints():
		return self.hitPoints


    def getAttackPoints():
		return self.attackPoints


    def spawn(x, y):
    	''' TODO '''
    	pass

    def getType(x, y):
    	''' Abstract function '''
    	pass

    def removeUnit(x, y):
    	''' not sure what TODO here '''
    	pass





















