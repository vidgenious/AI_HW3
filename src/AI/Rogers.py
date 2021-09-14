import random
import sys
sys.path.append("..")  #so other modules can be found in parent dir
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import *
from AIPlayerUtils import *
import math

"""
Lore of RogersWasTheChosenOne
"""

##
#AIPlayer
#Description: The responsbility of this class is to interact with the game by
#deciding a valid move based on a given game state. This class has methods that
#will be implemented by students in Dr. Nuxoll's AI course.
#
#Variables:
#   playerId - The id of the player.
##
class AIPlayer(Player):

    #__init__
    #Description: Creates a new Player
    #
    #Parameters:
    #   inputPlayerId - The id to give the new player (int)
    #   cpy           - whether the player is a copy (when playing itself)
    ##
    def __init__(self, inputPlayerId):
        super(AIPlayer,self).__init__(inputPlayerId, "RogersWasTheChosenOne")

    #getFoodScore
    #
    #Description: gets a score based on the amount of food
    #
    #Parameters:
    #   foodCount - the amount of food the agent has
    #
    #Returns either 0.0 - 0.55 or 1.0 if theres a winning move
    def getFoodScore(self, foodCount):
        if foodCount == 11:
            return 1.0
        elif foodCount == 1:
            return 0.1
        else:
            return 0.1 + 0.05 * (foodCount-1)
        
    #getQueensScore
    #
    #Description: gets a score based on the queens position
    #
    #Parameters:
    #   currentState - the current game state
    #   queen - the agents queen
    #   myInv - the inventory of the agent
    #returns 0.0-0.05 detpending on the queens location
    def getQueenScore(self, currentState, queen, myInv):
        if getConstrAt(currentState, queen.coords) != None and \
                (getConstrAt(currentState, queen.coords).type == ANTHILL or \
                getConstrAt(currentState, queen.coords).type == TUNNEL or \
                getConstrAt(currentState, queen.coords).type == FOOD):
            return 0.0
        return 0.05 * 1.0/(approxDist(queen.coords, myInv.getAnthill().coords))
    
    #getWorkersScore
    #
    #Description: gets a a score based on the workers posiiton
    #
    #Parameters:
    #   currentState - the current game state
    #   workers - the list of workers
    #   myInv - the inventory of the agent
    #   
    #returns sum of 
    #0.0 - 0.08 based on amount of workers
    #-0.005 if ant is standing on anthill or tunnel
    #0.0-0.02 * num ants if not carrying food
    #0.015 - 0.035 * num ants if carrying food
    #min is 0.0
    #theoretical max is 0.08 + 0.035 * 2 = 0.15
    def getWorkersScore(self, currentState, workers, myInv):
        #makes sure there is only 0-2 workers
        if len(workers) == 0:
            return 0.0
        if len(workers) > 2:
            return 0.0
        myFood = getConstrList(currentState, 2, (FOOD,))
        #incentivises building more workers
        total_score = .04 * len(workers)

        #goes through workers
        for worker in workers:
            #when workers not carrying
            if not worker.carrying:
                #disincentivises standing on anthills or tunnels
                if approxDist(myInv.getAnthill().coords, worker.coords) == 0 or \
                        approxDist(myInv.getTunnels()[0].coords, worker.coords) == 0:
                    total_score -= 0.005
                #incentivises being on food
                if min([approxDist(food.coords, worker.coords) for food in myFood]) == 0:
                    total_score += 0.02
                #incentivises moving towards food
                else:
                    total_score += 0.02 * 1.0/(1.0 + min([approxDist(food.coords, worker.coords) for food in myFood]))
            #when carrying food
            else:
                #disincentifises standing on food
                if min([approxDist(food.coords, worker.coords) for food in myFood]) == 0:
                    total_score -= 0.005
                #incentifises moving on tunnel or anthill
                if approxDist(myInv.getAnthill().coords, worker.coords) == 0 or \
                        approxDist(myInv.getTunnels()[0].coords, worker.coords) == 0:
                    total_score += 0.05
                #incentifizes moving towards tunnel or anthill
                else:
                    total_score += 0.015 + 0.02 * 1.0/(1.0 + \
                        min([approxDist(myInv.getAnthill().coords, worker.coords), \
                            approxDist(myInv.getTunnels()[0].coords, worker.coords)]))
        return total_score
    
    #getEnemyScore
    #
    #score that penalizes more worker ants
    #Works for <= 32 workers
    #
    #Parameters:
    #   currentState - the current game state
    #   playerID - the id of the agent
    #
    #Returns -1.7 to .8 based on number of ants 
    #Negative amounts are absurdly unlikely
    def getEnemyScore(self, currentState, playerID):
        enemyAnts = getAntList(currentState, (playerID + 1) % 2, (QUEEN, WORKER, SOLDIER, DRONE, R_SOLDIER))
        return .8 - (0.025 * len(enemyAnts))
    
    #getDronesScore
    #
    #score that is based on number of drones and positions of said drones
    #
    #Parameters:
    #   currentState - the currrent game state
    #   drones - the drones the agent has
    #   playerID - the ID of the agent
    #
    #returns sum of
    #0.0-0.1 based on if drone exists
    #0.0-0.04 based on position of drone
    #min is 0.0
    #theoretical max is 0.14
    def getDronesScore(self, currentState, drones, playerID):
        #incentivises only 1 drone
        if len(drones) == 0 or len(drones) > 1:
            return 0.0
        #gets enemy ants
        enemySoldierAnts = getAntList(currentState, (playerID + 1) % 2, (SOLDIER,))
        enemyHunterAnts = getAntList(currentState, (playerID + 1) % 2, (R_SOLDIER,))
        enemyWorkerAnts = getAntList(currentState, (playerID + 1) % 2, (WORKER,))
        enemyDroneAnts = getAntList(currentState, (playerID + 1) % 2, (DRONE,))
        
        total_score = 0.1 * len(drones)
        #moves drones towards all ants except soldiers
        #priority is R_SOLDIERS, WORKERS, THEN DRONES
        #avoids drones
        for drone in drones:
            if len(enemySoldierAnts) != 0:
                #sigmoid
                total_score += 0.04 * (1/(1 + math.exp(-(min([approxDist(enemy.coords, drone.coords) for enemy in enemySoldierAnts])-2))))
            if len(enemyHunterAnts) != 0:
                total_score += 0.04 * (1/(1+min([approxDist(enemy.coords, drone.coords) for enemy in enemyHunterAnts])))
                continue
            if len(enemyWorkerAnts) != 0:
                total_score += 0.04 * (1/(1+min([approxDist(enemy.coords, drone.coords) for enemy in enemyWorkerAnts])))
                continue
            if len(enemyDroneAnts) != 0:
                total_score += 0.04 * (1/(1+min([approxDist(enemy.coords, drone.coords) for enemy in enemyDroneAnts])))
                continue
            total_score += 0.04
        return total_score
    
    #getSoldierScore
    #
    #score that is based on number and position of soldiers
    #
    #Parameters:
    #   currentState - the current game state
    #   soldiers - the list of soldiers the agent has
    #   playerID - the id of the agent
    #
    #Returns the sum of 
    #0.0-0.15 for having a soldier
    #0.0-0.01 for having soldier well positioned
    #min is 0.0
    #max is 0.16
    def getSoldierScore(self, currentState, soldiers, playerID):
        # incentivises only 1 soldier
        if len(soldiers) == 0 or len(soldiers) > 1:
            return 0.0
        # gets enemy drones
        enemyDroneAnts = getAntList(currentState, (playerID + 1) % 2, (DRONE,))

        #rewards haveing soldier
        total_score = 0.15 * len(soldiers)

        #moves soldiers toward drones
        for soldier in soldiers:
            if len(enemyDroneAnts) != 0:
                total_score += 0.01 * (1/(1+min([approxDist(enemy.coords, soldier.coords) for enemy in enemyDroneAnts])))
                continue
            else:
                total_score += 0.01

        return total_score
    
    #utility
    #
    #Parameters:
    #   currentState - the current game state
    #   move - the move to get to the current game state
    #
    #Returns the utility of the given state
    def utility(self, currentState, move):
        penalty = 0.0
        #penalizes standing state
        if move != None and move.moveType == MOVE_ANT and len(move.coordList) == 1:
            penalty -= 1.0
        #get necessary variables
        me = currentState.whoseTurn
        myInv = getCurrPlayerInventory(currentState)
        #evaluates food score and terminates if winning move is found
        foodScore = self.getFoodScore(myInv.foodCount)
        if foodScore == 1.0:
            return foodScore
        #gets score based on workers position
        workerAnts = getAntList(currentState, me, (WORKER,))
        workersScore = self.getWorkersScore(currentState, workerAnts, myInv)
        #gets score based on queens position
        queenAnts = getAntList(currentState, me, (QUEEN,))
        queenScore = self.getQueenScore(currentState, queenAnts[0], myInv)
        #gets score based on drones position
        droneAnts = getAntList(currentState, me, (DRONE,))
        droneScore = self.getDronesScore(currentState, droneAnts, me)
        #gets score based on soldiers position
        soldierAnts = getAntList(currentState, me, (SOLDIER,))
        soldierScore = self.getSoldierScore(currentState, soldierAnts, me)
        #gets score based on enemies ants
        enemyScore = self.getEnemyScore(currentState, me)
        #returns total score scaled to meet requirements of homework
        return 0.56 * (foodScore + workersScore + queenScore + droneScore + soldierScore + penalty + enemyScore)

    #bestMove
    #
    #goes through valid moves and finds the best one
    #
    #Parameters:
    #   nodeArray: list of all possible moves
    #
    #Returns the best possible move
    def bestMove(self, nodeArray):
        best_node = None
        for node in nodeArray:
            if node["move"].moveType == MOVE_ANT and len(node["move"].coordList) == 1:
                continue
            if best_node == None:
                best_node = node
                continue
            node_utility = node["evaluation"]
            if node_utility > best_node["evaluation"]:
                best_node = node
        return best_node


    
    ##
    #getPlacement
    #
    #Description: called during setup phase for each Construction that
    #   must be placed by the player.  These items are: 1 Anthill on
    #   the player's side; 1 tunnel on player's side; 9 grass on the
    #   player's side; and 2 food on the enemy's side.
    #
    #Parameters:
    #   construction - the Construction to be placed.
    #   currentState - the state of the game at this point in time.
    #
    #Return: The coordinates of where the construction is to be placed
    ##
    def getPlacement(self, currentState):
        numToPlace = 0
        #implemented by students to return their next move
        if currentState.phase == SETUP_PHASE_1:    #stuff on my side
            numToPlace = 11
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    #Choose any x location
                    x = random.randint(0, 9)
                    #Choose any y location on your side of the board
                    y = random.randint(0, 3)
                    #Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        #Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        elif currentState.phase == SETUP_PHASE_2:   #stuff on foe's side
            numToPlace = 2
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    #Choose any x location
                    x = random.randint(0, 9)
                    #Choose any y location on enemy side of the board
                    y = random.randint(6, 9)
                    #Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        #Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        else:
            return [(0, 0)]
    
    ##
    #getMove
    #Description: Gets the next move from the Player.
    #
    #Parameters:
    #   currentState - The state of the current game waiting for the player's move (GameState)
    #
    #Return: The Move to be made
    ##
    def getMove(self, currentState):
        print("Current Utility: " + str(self.utility(currentState, None)))
        allMoves = listAllLegalMoves(currentState)
        nodeList = []

        # create list of GameState objects that result from
        # making each legal move

        for move in allMoves:
            moveState = getNextState(currentState, move)
            nodeDict = {
                "move": move,
                "state": moveState,
                "depth": 1,
                "evaluation": self.utility(moveState, move) + 1,
                "parent": None
            }
            nodeList.append(nodeDict)
        
        return self.bestMove(nodeList)["move"]
    
    ##
    #getAttack
    #Description: Gets the attack to be made from the Player
    #
    #Parameters:
    #   currentState - A clone of the current state (GameState)
    #   attackingAnt - The ant currently making the attack (Ant)
    #   enemyLocation - The Locations of the Enemies that can be attacked (Location[])
    ##
    def getAttack(self, currentState, attackingAnt, enemyLocations):
        #Attack a random enemy.
        return enemyLocations[0] 

    ##
    #registerWin
    #
    # This agent doens't learn
    #
    def registerWin(self, hasWon):
        #method templaste, not implemented
        pass
