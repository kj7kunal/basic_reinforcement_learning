import time
import random
import shelve

import pdb

import cellular
reload(cellular)
import qlearn_mod_random as qlearn # to use the alternative exploration method
#import qlearn # to use standard exploration method
reload(qlearn)

#DOF to move in grid
directions = 8

#Mouse perceptiveness to environment
lookdist = 3
lookcells = []
for i in range(-lookdist,lookdist+1):
    for j in range(-lookdist,lookdist+1):
        if (abs(i) + abs(j) <= lookdist) and (i != 0 or j != 0):
            lookcells.append((i,j))

#for respawns
def pickRandomLocation():
    while 1:
        x = random.randrange(3,world.width-2)
        y = random.randrange(3,world.height-2)
        cell = world.getCell(x, y)
        if not (cell.wall or len(cell.agents) > 0):
            return cell

def pickRandomLocationM2():
    while 1:
        x = random.randrange(world.width)
        y = random.randrange(world.height)
        cell = world.getCell(x, y)
        if not (cell.wall or len(cell.agents) > 0):
            return cell

def pickRandomLocationM1():
    while 1:
        x = cheese.cell.x + random.randrange(-2,3)
        y = cheese.cell.y + random.randrange(-2,3)
        
        # x = random.randrange(world.width)
        # y = random.randrange(world.height)
        if (x>=0 and x<world.width and y<world.height and y>=0):
            cell = world.getCell(x, y)
            if not (cell.wall or len(cell.agents) > 0):
                return cell

#define a board
class Cell(cellular.Cell):
    wall = False

    def colour(self):
        if self.wall:
            return 'black'
        else:
            return 'white'

    def load(self, data):
        if data == 'X':
            self.wall = True
        else:
            self.wall = False

#define a cat
class Cat(cellular.Agent):
    cell = None
    score = 0
    colour = 'orange'

    def update(self):   
        cell = self.cell
        if cell != mouse.cell:  #if mouse not caught, goes greedily towards mouse
            self.goTowards(mouse.cell)
            while cell == self.cell:   #if best=wall,i.e. self.cell, pick random
                self.goInDirection(random.randrange(directions))

#define cheese
class Cheese(cellular.Agent):
    colour = 'yellow'

    def update(self):
        pass

#define mouse
class Mouse(cellular.Agent):
    colour = 'gray'

    def __init__(self):
        self.ai = None   #stores the Q-learning implementation
        self.ai = qlearn.QLearn(actions=range(directions),
                                alpha=0.8, gamma=0.8, epsilon=0.2)
        self.eaten = 0  #performance
        self.fed = 0
        self.lastState = None #log for learning
        self.lastAction = None

    def update(self):
        # calculate the state of the surrounding cells
        # returns tuple with states of cells within FOV of mouse
        state = self.calcState()
        # asign a reward of -1 by default
        reward = -1

        ## observe the reward and update the Q-value

        # eaten by cat, update q-val by reward -100 for s(a)->s', respawn
        if self.cell == cat.cell:
            self.eaten += 1
            reward = -100
            if self.lastState is not None:
                self.ai.learn(self.lastState, self.lastAction, reward, state)
            self.lastState = None   #restart run
            if len(mouse.ai.q)<9960:
                self.cell = pickRandomLocationM1()
            else:
                self.cell = pickRandomLocationM2()

        #eats cheese, update q-val by reward 50 for s(a)->s'
        if self.cell == cheese.cell:
            self.fed += 1
            reward = 80
            cheese.cell = pickRandomLocation()

        if self.lastState is not None:  #learn the last step
            self.ai.learn(self.lastState, self.lastAction, reward, state)

        # Choose a new action and execute it
        state = self.calcState()
        print(state)
        action = self.ai.chooseAction(state)    #action based on maxQ policy
        self.lastState = state
        self.lastAction = action

        self.goInDirection(action)

    def calcState(self):
        def cellvalue(cell):
            if cat.cell is not None and (cell.x == cat.cell.x and
                                         cell.y == cat.cell.y):
                return 3
            elif cheese.cell is not None and (cell.x == cheese.cell.x and
                                              cell.y == cheese.cell.y):
                return 2
            else:
                return 1 if cell.wall else 0

        return tuple([cellvalue(self.world.getWrappedCell(self.cell.x + j, self.cell.y + i))
                      for i,j in lookcells])


cheese = Cheese()
mouse = Mouse()
cat = Cat()

world = cellular.World(Cell, directions=directions, filename='../worlds/waco.txt')
world.age = 0

world.addAgent(cheese, cell=pickRandomLocation())
world.addAgent(cat)
world.addAgent(mouse)

epsilonx = (0,100000)
epsilony = (0.1,0)
epsilonm = (epsilony[1] - epsilony[0]) / (epsilonx[1] - epsilonx[0])

endAge = world.age + 10000

while world.age < endAge:
    world.update()

    '''if world.age % 100 == 0:
        mouse.ai.epsilon = (epsilony[0] if world.age < epsilonx[0] else
                            epsilony[1] if world.age > epsilonx[1] else
                            epsilonm*(world.age - epsilonx[0]) + epsilony[0])'''

    if world.age % 10000 == 0:
        print "{:d}, e: {:0.2f}, W: {:d}, L: {:d}"\
            .format(world.age, mouse.ai.epsilon, mouse.fed, mouse.eaten)
        mouse.eaten = 0
        mouse.fed = 0

world.display.activate(size=30)
world.display.delay = 1
while 1:
    world.update(mouse.fed, mouse.eaten)
    print len(mouse.ai.q) # print the amount of state/action, reward 
                          # elements stored
    import sys
    bytes = sys.getsizeof(mouse.ai.q)
    print "Bytes: {:d} ({:d} KB)".format(bytes, bytes/1024)
