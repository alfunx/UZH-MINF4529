"""
Kingsheep Agent Template

This template is provided for the course 'Practical Artificial Intelligence' of the University of Zürich.

Please edit the following things before you upload your agent:
    - change the name of your file to '[uzhshortname]_A1.py', where [uzhshortname] needs to be your uzh shortname
    - change the name of the class to a name of your choosing
    - change the def 'get_class_name()' to return the new name of your class
    - change the init of your class:
        - self.name can be an (anonymous) name of your choosing
        - self.uzh_shortname needs to be your UZH shortname

The results and rankings of the agents will be published on OLAT using your 'name', not 'uzh_shortname',
so they are anonymous (and your 'name' is expected to be funny, no pressure).

"""

# from config import *
from contextlib import contextmanager
from operator import add, attrgetter
from random import sample
from timeit import default_timer
import copy

# Constants (config)
###############################################################################

#[General_Constants]
FIELD_WIDTH = 19
FIELD_HEIGHT = 15

#[Game_Constants]
NO_ITERATIONS = 100
MAX_CALC_TIME = 1

#[Field_Constants]
CELL_EMPTY = '.'
CELL_SHEEP_1 = 'S'
CELL_SHEEP_1_d = 'U'
CELL_WOLF_1 = 'W'
CELL_SHEEP_2 = 's'
CELL_SHEEP_2_d = 'u'
CELL_WOLF_2 = 'w'
CELL_GRASS = 'g'
CELL_RHUBARB = 'r'
CELL_FENCE = '#'


#[Movements]
MOVE_NONE = 0
MOVE_UP = -1
MOVE_DOWN = 1
MOVE_LEFT = -2
MOVE_RIGHT = 2

#[Awards]
AWARD_RHUBARB = 5
AWARD_GRASS = 1

# Constants
###############################################################################

#[Awards]
AWARD_SHEEP = 100

#[Penalty]
PENALTY_MOVE_NONE = -1
PENALTY_NEAR_WOLF = -float("inf")

#[Movements]
MOVE_COORDS = [(0, -1), (1, 0), (0, 1), (-1, 0)]
COORD_TO_MOVE_CONST = {
        (0, 0): MOVE_NONE,
        (0, -1): MOVE_UP,
        (1, 0): MOVE_RIGHT,
        (0, 1): MOVE_DOWN,
        (-1, 0): MOVE_LEFT
        }

# Timer
###############################################################################

@contextmanager
def elapsed_timer():
    start = default_timer()
    elapser = lambda: default_timer() - start
    yield elapser()
    end = default_timer()
    elapser = lambda: end-start

# Decorators
###############################################################################

def debug_time(func):
    def wrapper(*args, **kwargs):
        with elapsed_timer() as elapsed:
            value = func(*args, **kwargs)
            print(" > Time:", elapsed)
            return value
    return wrapper

def debug_return(func):
    def wrapper(*args, **kwargs):
        value = func(*args, **kwargs)
        print("value:", value, ">>> args:", *args, **kwargs)
        return value
    return wrapper

# Functions
###############################################################################

def get_class_name():
    return 'Alfunx'

def is_near(a, b):
    return a in [b] + list(map(lambda x: tuple(map(add, b, x)), MOVE_COORDS))

def distance(a, b):
    return (a - b) ** 2

def gen_parents(node):
    yield node
    node = node.parent
    while node:
        yield node
        node = node.parent

def sheep_score(playfield, player_nr):
    """
    Returns score for current position of the sheep of player_nr.
    """

    score = 0
    sheep = playfield.get_sheep(player_nr)
    enemy_wolf = playfield.get_wolf(player_nr % 2 + 1)
    if sheep in playfield.rhubarb:
        playfield.rhubarb.remove(sheep)
        score = AWARD_RHUBARB
    if sheep in playfield.grass:
        playfield.grass.remove(sheep)
        score = AWARD_GRASS

    rhubarb_path = [astar(playfield.figure + playfield.fence, sheep, i)
                    for i in playfield.rhubarb]
    grass_path = [astar(playfield.figure + playfield.fence, sheep, i)
                  for i in playfield.grass]

    if is_near(sheep, enemy_wolf):
        score = PENALTY_NEAR_WOLF
    else:
        score += sum(map(lambda x: AWARD_RHUBARB / (len(x) + 1), rhubarb_path)) \
               + sum(map(lambda x: AWARD_GRASS / (len(x) + 1), grass_path))

    return score

def wolf_score(playfield, player_nr):
    """
    Returns score for current position of the wolf of player_nr.
    """

    score = 0
    wolf = playfield.get_wolf(player_nr)
    sheep = playfield.get_sheep(player_nr)
    enemy_sheep = playfield.get_sheep(player_nr % 2 + 1)
    if wolf in playfield.rhubarb:
        playfield.rhubarb.remove(wolf)
        score = AWARD_RHUBARB
    if wolf in playfield.grass:
        playfield.grass.remove(wolf)
        score = AWARD_GRASS

    sheep_path = astar(playfield.figure + playfield.fence, wolf, sheep)
    enemy_sheep_path = astar(playfield.figure + playfield.fence, wolf, enemy_sheep)

    score += AWARD_SHEEP / (len(enemy_sheep_path) + 1)
    if len(sheep_path) > len(enemy_sheep_path):
        rhubarb_path = [astar(playfield.figure + playfield.fence, wolf, i)
                        for i in playfield.rhubarb]
        grass_path = [astar(playfield.figure + playfield.fence, wolf, i)
                      for i in playfield.grass]
        score += sum(map(lambda x: AWARD_RHUBARB / (len(x) + 1), rhubarb_path)) \
               + sum(map(lambda x: AWARD_GRASS / (len(x) + 1), grass_path))

    return score

# A* search algorithm
###############################################################################

class Node():
    """
    A node class for A* Pathfinding.
    """

    def __init__(self, parent=None, coord=None):
        self.parent = parent
        self.coord = coord
        self.g = parent.g + 1 if parent else 0
        self.h = 0
        self.f = 0

    def __eq__(self, other):
        return self.coord == other.coord

def astar(obstacles, start, end):
    """
    Returns a list of tuples (x, y) indicating coordinates, as a path from the
    given start (excluding) to the given end (including) considering the given
    obstacles.
    """

    if start in obstacles:
        obstacles.remove(start)
    if end in obstacles:
        obstacles.remove(end)

    start_node = Node(None, start)
    end_node = Node(None, end)
    todo_nodes = [start_node]
    done_coords = []

    while todo_nodes:
        node = min(todo_nodes, key=attrgetter("f"))
        todo_nodes.remove(node)
        done_coords.append(node.coord)

        # Found end_node, return path excluding start_node
        if node == end_node:
            return [n.coord for n in gen_parents(node)][:0:-1]

        # Try each direction
        for move in MOVE_COORDS:
            coord = tuple(map(add, node.coord, move))

            # Check done_coords, range and obstacles
            if coord in done_coords:
                continue
            if not (0 <= coord[0] < FIELD_WIDTH and 0 <= coord[1] < FIELD_HEIGHT):
                continue
            if coord in obstacles:
                continue

            new_node = Node(node, coord)

            # Node is already in todo_nodes
            for open_node in todo_nodes:
                if new_node == open_node and new_node.g > open_node.g:
                    break
            # Node is not yet in todo_nodes
            else:
                new_node.h = sum(map(distance, new_node.coord, end_node.coord))
                new_node.f = new_node.g + new_node.h
                todo_nodes.append(new_node)

# Playfield class
###############################################################################

class Playfield:
    """
    Struct to store field data.
    """

    def __init__(self, field):
        self.figure = 4 * [None]
        self.grass = []
        self.rhubarb = []
        self.fence = []

        # Parse field strings
        for y, line in enumerate(field):
            for x, char in enumerate(line):
                if char == CELL_SHEEP_1:
                    self.figure[0] = (x, y)
                elif char == CELL_SHEEP_2:
                    self.figure[1] = (x, y)
                elif char == CELL_WOLF_1:
                    self.figure[2] = (x, y)
                elif char == CELL_WOLF_2:
                    self.figure[3] = (x, y)
                elif char == CELL_GRASS:
                    self.grass.append((x, y))
                elif char == CELL_RHUBARB:
                    self.rhubarb.append((x, y))
                elif char == CELL_FENCE:
                    self.fence.append((x, y))

    def get_sheep(self, player_nr):
        return self.figure[player_nr - 1]

    def get_wolf(self, player_nr):
        return self.figure[player_nr + 1]

    def is_coord_available(self, coord):
        return not (coord in self.fence
                    and 0 <= coord[0] < FIELD_WIDTH
                    and 0 <= coord[1] < FIELD_HEIGHT)

    def simulate_sheep(self, player_nr, coord):
        """
        Simulate sheep movement, returns copy of playfield.
        """
        playfield = copy.deepcopy(self)
        playfield.figure[player_nr - 1] = coord
        return playfield

    def simulate_wolf(self, player_nr, coord):
        """
        Simulate wolf movement, returns copy of playfield.
        """
        playfield = copy.deepcopy(self)
        playfield.figure[player_nr + 1] = coord
        return playfield

# Agent
###############################################################################

class Alfunx():
    """
    Alphonse's Kingsheep agent.
    """

    def __init__(self):
        self.name = "alfunx"
        self.uzh_shortname = "amariy"
        self.playfield = None

    def move_sheep(self, player_nr, field):
        return self.debug_move_sheep(player_nr, field)

    @debug_time
    def debug_move_sheep(self, player_nr, field):
        playfield = Playfield(field)
        coord = (0, 0)
        score = sheep_score(playfield, player_nr)
        if playfield.grass or playfield.rhubarb:
            score += PENALTY_MOVE_NONE
        print("score:", score)

        for move in sample(MOVE_COORDS, len(MOVE_COORDS)):
            new_coord = tuple(map(add, playfield.get_sheep(player_nr), move))
            if not playfield.is_coord_available(new_coord):
                continue
            if new_coord in playfield.figure:
                continue
            p = playfield.simulate_sheep(player_nr, new_coord)
            s = sheep_score(p, player_nr)
            print("score:", s, move, new_coord)
            if s > score:
                score = s
                coord = move

        return COORD_TO_MOVE_CONST[coord]

    def move_wolf(self, player_nr, field):
        return self.debug_move_wolf(player_nr, field)

    @debug_time
    def debug_move_wolf(self, player_nr, field):
        playfield = Playfield(field)
        coord = (0, 0)
        score = wolf_score(playfield, player_nr) + PENALTY_MOVE_NONE
        print("score:", score)

        for move in sample(MOVE_COORDS, len(MOVE_COORDS)):
            new_coord = tuple(map(add, playfield.get_wolf(player_nr), move))
            if not playfield.is_coord_available(new_coord):
                continue
            if new_coord in [playfield.get_sheep(player_nr), playfield.get_wolf(player_nr % 2 + 1)]:
                continue
            p = playfield.simulate_wolf(player_nr, new_coord)
            s = wolf_score(p, player_nr)
            print("score:", s, move, new_coord)
            if s > score:
                score = s
                coord = move

        return COORD_TO_MOVE_CONST[coord]
