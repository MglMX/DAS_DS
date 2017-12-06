import random
import pygame,sys
import time

TIME_BETWEEN_COMMANDS = 1
pygame.init()

class clientAI:
    def __init__(self, graphical=True):
        self.graphical = graphical
        if self.graphical:
            self.WIDTH = 500
            self.HEIGHT = 500
            self.scale = (self.WIDTH / 25, self.HEIGHT / 25)
            self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))

    def drawLines(self):
        if self.graphical:
            self.screen.fill((0, 0, 0))  # Clear screen
            for x in range(25):
                pygame.draw.line(self.screen, (255, 255, 255), (x * self.scale[0], 0), (x * self.scale[0], self.HEIGHT))
                pygame.draw.line(self.screen, (255, 255, 255), (0, x * self.scale[1]), (self.WIDTH, x * self.scale[1]))

    def drawUnits(self, unitBoard):
        if self.graphical:
            for x in range(25):
                for y in range(25):
                    if unitBoard[x][y].name == 'dragon':
                        pygame.draw.rect(self.screen, (int(unitBoard[x][y].hp * 2.55), 0, 0),
                                         (x * self.scale[0], y * self.scale[1], self.scale[0], self.scale[1]))
                    elif unitBoard[x][y].name == 'player':
                        if unitBoard[x][y].isUser:
                            pygame.draw.rect(self.screen, (0, int(unitBoard[x][y].hp * 12.7), 0),
                                         (x * self.scale[0], y * self.scale[1], self.scale[0], self.scale[1]))
                        else:
                            pygame.draw.rect(self.screen, (0, 0, int(unitBoard[x][y].hp * 12.7)),
                                         (x * self.scale[0], y * self.scale[1], self.scale[0], self.scale[1]))
    def handleEvents(self,player,board,lock):
        lock.release()
        time.sleep(TIME_BETWEEN_COMMANDS)
        lock.acquire()

        dragon = self.getClosestDragon(board,player)
        if self.graphical:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            pygame.display.flip()

        if dragon is None: #All dragons are killed so there is no closest dragon
            return 5 #Indicating that the client should disconnect
        elif self.getPlayersToHeal(board,player):
            player_to_heal = random.choice(self.getPlayersToHeal(board,player))
            return (player_to_heal.x,player_to_heal.y)
        elif self.distanceToDragon(dragon,player) <= 2:
            return (dragon.x,dragon.y)
        else:
            new_x, new_y = self.getSquareToMove(board,player)
            player.x = new_x  # updating position of the player localy
            player.y = new_y
            return 1 #It could be 1,2,3,4 it indicates moving

    def distance(self, pos1, pos2):
        # "the distance between two squares is the sum of the horizontal and vertical distance between them"
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


    def distanceToDragon(self, dragon,player):
        '''Gets the distance from the player to the dragon'''
        return self.distance((player.x, player.y), (dragon.x, dragon.y))

    def getClosestDragon(self,board,player):
        ''' Returns the dragon that is closest to the player.'''

        dragons = []
        for x in range(25):
            for y in range(25):
                if board[x][y].name == 'dragon':
                    dragons.append(board[x][y])

        minimum_distance = 9999999
        closest_dragon = None
        for dragon in dragons:
            distance_to_dragon = self.distanceToDragon(dragon,player)
            if distance_to_dragon < minimum_distance:
                closest_dragon = dragon
                minimum_distance = distance_to_dragon

        return closest_dragon


    def getSquareToMove(self, board,player):
        ''' Checks where is the dragon and if the player can move to a square to get closer to it. It returns de square where the player should move.'''
        player_x = player.x
        player_y = player.y
        dragon = self.getClosestDragon(board,player)

        if dragon.x > player_x and board[player_x + 1][player_y].name == "empty":
            return (player_x + 1, player_y)  # Right
        elif dragon.x < player_x and board[player_x - 1][player_y].name == "empty":
            return (player_x - 1, player_y)  # Left
        elif dragon.y > player_y and board[player_x][player_y + 1].name == "empty":
            return (player_x, player_y + 1)  # Up
        elif dragon.y < player_y and board[player_x][player_y - 1].name == "empty":
            return (player_x, player_y - 1)  # Down
        return (player.x, player.y)


    def getPlayersToHeal(self,board,player):
        players_to_heal = []
        for x in range(25):
            for y in range(25):
                unit = board[x][y]
                if unit.name == 'player' and unit.id != player.id and self.distance((player.x, player.y), (unit.x, unit.y)) <= 5:
                    if float(unit.hp) / float(unit.maxHP) < 0.5:  # The player has less than 50% of his life
                        players_to_heal.append(unit)

        return players_to_heal