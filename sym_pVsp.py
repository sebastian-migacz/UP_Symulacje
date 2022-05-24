import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
import random
import uuid
from math import sqrt
import time

import pygame
#===================================================================================INIT
pygame.init()

display_width = 1920
display_height = 1080
image_width = 32
image_height = 32

black = (0,0,0)
white = (255,255,255)

gameDisplay = pygame.display.set_mode((display_width,display_height))
pygame.display.set_caption('Symulacje')
clock = pygame.time.Clock()

predatorImg = pygame.image.load('Arctic_wolf.png')
preyImg = pygame.image.load('Gazelle.png')
predatorImg = pygame.transform.scale(predatorImg, (image_width, image_height))
preyImg = pygame.transform.scale(preyImg, (image_width, image_height))




INIT_PREDATORS = 50        #Początkowa liczba drapieżników
INIT_PREYS = 150            #Początkowa liczba ofiar
X_MIN = image_width
X_MAX = display_width - image_width
Y_MIN = image_height
Y_MAX = display_height - image_height
global SAFE_DISTANCE
SAFE_DISTANCE = image_width * 0.25         #odległość potrzebna do ataku drapieżnika
global PREDATOR_EFFECTIVENESS
PREDATOR_EFFECTIVENESS = 70 #liczba z zakresu od 0-100 określająca szansę na śmierć ofiary w starciu z drapieżnikiem
global MAX_VITALITY
MAX_VITALITY = 30           #wytrzymałość drapieżników (ile rund jest w stanie wytrzymać bez jedzenia)
ITERATIONS = 100            #liczba iteracji / kroków w błądzeniu losowym, którą symulujemy
global STEP_SIZE
STEP_SIZE = image_width * 0.3
global PREY_MULTIPLICATION_RATIO
PREY_MULTIPLICATION_RATIO = 0.01  #o ile % zwiększa się liczebność ofiar w każdej rundzie (liczba z zakresu 0-1)
PREDATOR_MULTIPLICATION_RATIO = 0.01  #o ile % zwiększa się liczebność drapieżników w każdej rundzie (liczba z zakresu 0-1)

#===================================================================================BOUNDARIES

class SurfaceBoundaries:
    def __init__(self, x_min, x_max, y_min, y_max):
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        
global surfaceBoundaries
surfaceBoundaries = SurfaceBoundaries(X_MIN, X_MAX, Y_MIN, Y_MAX)

#===================================================================================GLOBAL CLASS

class Position:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        
    def __str__(self):
        return ("Position(" + str(self.x) + ", " + str(self.y) + ")")
    
    def isWithinBoundaries(self) -> bool:
        global surfaceBoundaries
        return (
            surfaceBoundaries.x_min <= self.x <= surfaceBoundaries.x_max 
            and surfaceBoundaries.y_min <= self.y <= surfaceBoundaries.y_max
        )

    def adjust_to_boundaries(self) -> None:
        global surfaceBoundaries
        
        #modelling bouncing from boundaries
        if not self.isWithinBoundaries():
            if self.x < surfaceBoundaries.x_min: 
                delta = surfaceBoundaries.x_min - self.x
                self.x = self.x + 2 * delta
            if self.x > surfaceBoundaries.x_max: 
                delta = self.x - surfaceBoundaries.x_max
                self.x = self.x - 2 * delta
            if self.y < surfaceBoundaries.y_min: 
                delta = surfaceBoundaries.y_min - self.y
                self.y = self.y + 2 * delta
            if self.y > surfaceBoundaries.y_max: 
                delta = self.y - surfaceBoundaries.y_max
                self.y = self.y - 2 * delta
                
    def random_step(self) -> None:
        phi = 2 * np.pi * random.uniform(0, 1)
        self.x += np.cos(phi) * STEP_SIZE
        self.y += np.sin(phi) * STEP_SIZE
        self.adjust_to_boundaries()

def randomPosition() -> Position:
    global surfaceBoundaries
    x = random.uniform(surfaceBoundaries.x_min, surfaceBoundaries.x_max)
    y = random.uniform(surfaceBoundaries.y_min, surfaceBoundaries.y_max)
    return Position(x, y)

def distance(position_a: Position, position_b: Position):
    return sqrt(
        pow(position_a.x - position_b.x, 2) + pow(position_a.y - position_b.y, 2)        
    )

def coin_flip(probability: float) -> bool:
    #accepts probability as number from 0 to 1
    #perform the binomial distribution (returns 0 or 1)    
    return np.random.binomial(1, probability)

def list_to_string(lst: list[object]) -> str:
    string_delimiter = ",\n"
    return string_delimiter.join(str(el) for el in lst)

#===================================================================================PREDATOR

class Predator:
    def __init__(self):
        global MAX_VITALITY

        self.id = uuid.uuid1()
        self.position = randomPosition()
        self.isAlive = True
        self.vitality = MAX_VITALITY
    def __str__(self):
        return ("Predator(" + 
            str(self.id) + ", " + 
            str(self.position) + ", " + 
            str(self.isAlive) + ", " + 
            str(self.vitality) + 
            ")")

global predators
predators = []
for i in range(INIT_PREDATORS):
    predators.append(Predator())
    
#===================================================================================PREY
class Prey:
    def __init__(self):
        self.id = uuid.uuid1()
        self.position = randomPosition()
        self.isAlive = True
        
    def get_endangering_predators(self) -> list[Predator]:
        global predators
        global SAFE_DISTANCE
        
        def are_too_close(predator: Predator, prey: Prey) -> bool:
            return (distance(prey.position, predator.position) < SAFE_DISTANCE)

        return list(filter(lambda predator: are_too_close(self, predator), predators))
        
    def chance_to_die(self, endangering_predators_number: int) -> float:
        global PREDATOR_EFFECTIVENESS
        
        chance_to_survive = pow(((100 - PREDATOR_EFFECTIVENESS) / 100), endangering_predators_number)
        return 1 - chance_to_survive
    
    def __str__(self):
        return ("Prey(" + 
                str(self.id) + ", " + 
                str(self.position) + ", " + 
                str(self.isAlive) +
                ")")

global preys
preys = []
for i in range(INIT_PREYS):
    preys.append(Prey())

global dead_predators
dead_predators = []
global dead_preys
dead_preys = []

#===================================================================================    

def find_endangered_preys_and_attacking_predators():
    global predators
    endangered_preys = list()
    for prey in preys:
        endangering_predators = prey.get_endangering_predators()
        
        if len(endangering_predators) > 0:
            chance_to_die = prey.chance_to_die(len(endangering_predators))
            endangered_preys.append((prey, endangering_predators, chance_to_die))
    return endangered_preys
    
def mark_predators_meal(happy_predators):
    global predators
    for predator in predators:
        if predator in happy_predators:
            predator.vitality = MAX_VITALITY
            
def clash_preys_and_predators(endangered_preys):
    for (prey, endangering_predators, chance_to_die) in endangered_preys:
        prey_dies = (coin_flip(chance_to_die) == 1) # == 1 converts 0/1 to False/True
        if prey_dies:
            #print(str(prey) + " got killed by " + str(len(endangering_predators)) + " predators")
            prey.isAlive = False
            mark_predators_meal(endangering_predators)
            
def decrement_predators_vitality():
    global predators
    for predator in predators:
        predator.vitality = predator.vitality - 1
        if predator.vitality <= 0:
            predator.isAlive = False
            
def filter_out_dead_predators():
    global predators
    global dead_predators
    
    new_dead_predators = list(filter(lambda predator: (predator.isAlive == False), predators))
    alive_predators = list(filter(lambda predator: (predator.isAlive == True), predators))
    predators = alive_predators
    dead_predators += new_dead_predators
    
def filter_out_dead_preys():
    global preys
    global dead_preys
        
    new_killed_preys = list(filter(lambda prey: (prey.isAlive == False), preys))
    alive_preys = list(filter(lambda prey: (prey.isAlive == True), preys))
    preys = alive_preys
    dead_preys += new_killed_preys
    
def add_new_born_preys():
    global preys
    
    new_preys_number = round(len(preys) * PREY_MULTIPLICATION_RATIO) + 1
    new_preys = []
    for i in range(new_preys_number):
        new_preys.append(Prey())
    preys = preys + new_preys
    
def add_new_born_predators():
    global predators
    
    new_predators_number = round(len(predators) * PREDATOR_MULTIPLICATION_RATIO) + 1
    new_predators = []
    for i in range(new_predators_number):
        new_predators.append(Predator())
    predators = predators + new_predators
    
def move_alive_animals_by_one_random_step():
    global predators
    global preys
    
    for predator in predators:
        predator.position.random_step()
        gameDisplay.blit(predatorImg,(predator.position.x,predator.position.y)) # try
    for prey in preys:
        prey.position.random_step()
        gameDisplay.blit(preyImg,(prey.position.x,prey.position.y))
        
def perform_one_iteration():
    endangered_preys = find_endangered_preys_and_attacking_predators()
    clash_preys_and_predators(endangered_preys)
    decrement_predators_vitality()
    filter_out_dead_predators()
    filter_out_dead_preys()
    add_new_born_preys()
    add_new_born_predators()
    move_alive_animals_by_one_random_step()

    
preys_count_history = []
predators_count_history = []

#===================================================================================    
def predator(x,y):
    gameDisplay.blit(predatorImg,(x,y))
 

def prey(x,y):
    gameDisplay.blit(preyImg,(x,y)) 
    

x1 = (display_width * 0.5) - image_width
y1 = (display_height * 0.8) - image_height

x2 = (display_width * 0.5) - image_width
y2 = (display_height * 0.8)
i = 0
crashed = False



while not crashed:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            crashed = True
            
        if event.type == pygame.KEYDOWN:
            if event.type == pygame.K_LEFT:
                ITERATIONS += 100
            
    
    
    
    if(i<= ITERATIONS):
        gameDisplay.fill(white)
        perform_one_iteration()
        print("Iteration " + str(i) + ":")
        print("Dead preys: " + str(len(dead_preys)))
        print("Dead predators: " + str(len(dead_predators)))
        print("Alive preys: " + str(len(preys)))
        print("Alive predators: " + str(len(predators)))
        print("TOTAL ITERATIONS " + str(ITERATIONS))
        print()
        preys_count_history.append(len(preys))
        predators_count_history.append(len(predators))
        i+=1
        
        #pygame.display.update() 
        pygame.display.flip()
        
        time.sleep(0.1)
    clock.tick(60)
    
pygame.quit()
quit()