class Unit(object):

    def _init_(self, x, y, maxHitPoints, hitPoints, attackPoints, unitID):

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

	hitPoints += modifier

	if(self.hitPoints > self.maxHitPoints):
		hitPoints = maxHitPoints

	if(self.hitPoints <= 0):
		removeUint(x, y)

  
    def dealDamage(x, y, damage):
        

    def healDamage(x, y, healed): 	


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


    def getType(x, y):


    def getUnit(x, y):


    def removeUnit(x, y):


    def moveUnit(x, y):






















