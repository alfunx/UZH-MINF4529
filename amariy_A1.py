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
from collections import deque
from contextlib import contextmanager
from copy import deepcopy
from heapq import heappush, heappop
from itertools import islice
from operator import add
from random import sample
from timeit import default_timer

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
AWARD_RHUBARB = 5.0
AWARD_GRASS = 1.0

# Constants
###############################################################################

#[Awards]
AWARD_SHEEP = 1000.0
AWARD_BLOCK_SHEEP = 0.8

#[Penalty]
PENALTY_MOVE_NONE = -1.0
PENALTY_NEAR_WOLF = -AWARD_SHEEP

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

def calculate_score(playfield, player_nr):
    """
    Returns score for playfield.
    """

    wolf = playfield.get_wolf(player_nr)
    sheep = playfield.get_sheep(player_nr)
    enemy_wolf = playfield.get_wolf(player_nr % 2 + 1)
    enemy_sheep = playfield.get_sheep(player_nr % 2 + 1)

    # Sheep must not be near enemy wolf
    if is_near(sheep, enemy_wolf):
        return PENALTY_NEAR_WOLF

    score = 0

    # Sheep must go to grass
    sheep_to_items = dict(bfs(playfield.fences.union(playfield.figures),
                              sheep, set(playfield.items.keys())))
    score += sum(map(lambda a: playfield.items[a[0]] / len(a[1]), sheep_to_items.items()))

    # Sheep must block enemy sheep
    sheep_to_enemy_sheep = astar(playfield.fences.union({enemy_sheep, sheep}),
                                 sheep, enemy_sheep)
    score += AWARD_BLOCK_SHEEP / len(sheep_to_enemy_sheep)

    # Wolf must go to enemy sheep
    wolf_to_enemy_sheep = astar(playfield.fences.union({enemy_sheep, sheep}),
                                wolf, enemy_sheep)
    score += AWARD_SHEEP / len(wolf_to_enemy_sheep)

    return score

def sheep_score(playfield, player_nr):
    """
    Returns score for current position of the sheep of player_nr.
    """

    sheep = playfield.get_sheep(player_nr)
    enemy_wolf = playfield.get_wolf(player_nr % 2 + 1)
    enemy_sheep = playfield.get_sheep(player_nr % 2 + 1)

    if is_near(sheep, enemy_wolf):
        return PENALTY_NEAR_WOLF

    if not playfield.items:
        enemy_sheep_path = astar(playfield.fences.union({enemy_sheep, sheep}), sheep, enemy_sheep)
        return 1 / len(enemy_sheep_path) + wolf_score(playfield, player_nr)

    # Score if sheep is on item
    score = playfield.items.pop(sheep) if sheep in playfield.items else 0

    # Paths
    item_path = dict(bfs(playfield.fences.union(playfield.figures),
                         sheep, set(playfield.items.keys())))
    # item_path = dict(islice(bfs(playfield.fences.union(playfield.figures),
    #                             sheep, set(playfield.items.keys())), 5))
    # enemy_item_path = dict(bfs(playfield.fences.union(playfield.figures),
    #                            enemy_sheep, set(playfield.items.keys())))
    #
    # # Scores
    # item_scores = dict(map(lambda a: (a[0], playfield.items[a[0]] / len(a[1])),
    #                        item_path.items()))
    # enemy_item_scores = dict(map(lambda a: (a[0], playfield.items[a[0]] / (len(a[1]) + 1)),
    #                              enemy_item_path.items()))
    #
    # return score + sum([(item_scores[k] - enemy_item_scores[k]) for k in playfield.items])

    return score + sum(map(lambda a: playfield.items[a[0]] / len(a[1]), item_path.items()))

def wolf_score(playfield, player_nr):
    """
    Returns score for current position of the wolf of player_nr.
    """

    wolf = playfield.get_wolf(player_nr)
    sheep = playfield.get_sheep(player_nr)
    enemy_wolf = playfield.get_wolf(player_nr % 2 + 1)
    enemy_sheep = playfield.get_sheep(player_nr % 2 + 1)

    if wolf == enemy_sheep:
        return AWARD_SHEEP

    # Paths
    sheep_path = astar(playfield.fences.union({enemy_wolf, enemy_sheep}), wolf, sheep)
    enemy_sheep_path = astar(playfield.fences.union({enemy_sheep, sheep}), wolf, enemy_sheep)

    # Score for enemy_sheep distance
    score = AWARD_SHEEP / len(enemy_sheep_path)

    # Score if wolf is on item
    if wolf in playfield.items:
        score += playfield.items.pop(wolf)

    if len(sheep_path) > len(enemy_sheep_path):
        # Paths
        item_path = dict(bfs(playfield.fences.union(playfield.figures),
                             sheep, set(playfield.items.keys())))
        enemy_item_path = dict(bfs(playfield.fences.union(playfield.figures),
                                   enemy_sheep, set(playfield.items.keys())))

        # Scores
        item_scores = dict(map(lambda a: (a[0], playfield.items[a[0]] / len(a[1]) + 1),
                               item_path.items()))
        enemy_item_scores = dict(map(lambda a: (a[0], playfield.items[a[0]] / (len(a[1]))),
                                     enemy_item_path.items()))

        score += sum([enemy_item_scores[k] - item_scores[k] for k in playfield.items])

    return score

# Simulate
###############################################################################

def simulate(playfield, player_nr, phase=None, a=-float("inf"), b=float("inf"), d=3):
    if not phase:
        phase = 3 if player_nr == 1 else 4

    if not d:
        return calculate_score(playfield, player_nr)

    maximum = calculate_score(playfield, player_nr)
    if b > maximum:
        b = maximum
        if a >= b:
            return b

    # mscore = -float("inf")

    wolf = playfield.get_wolf(player_nr)
    sheep = playfield.get_sheep(player_nr)
    enemy_wolf = playfield.get_wolf(player_nr % 2 + 1)
    enemy_sheep = playfield.get_sheep(player_nr % 2 + 1)
    active = wolf if phase in {5, 6} else sheep

    for coord in [tuple(map(add, sheep, i)) for i in MOVE_COORDS]:
        if not playfield.is_coord_available(coord):
            continue

        score = 0

        if phase in {5, 6}:
            if coord in {sheep, enemy_wolf}:
                continue
            if coord == enemy_sheep:
                return float("inf")
        else:
            if coord in playfield.figures:
                continue
            if is_near(coord, enemy_wolf):
                score += PENALTY_NEAR_WOLF

        new_playfield = playfield.move_figure(active, coord)
        eat_score = new_playfield.items.pop(coord, 0)
        score += eat_score if phase not in {5, 6} else 0
        score -= simulate(new_playfield, player_nr % 2 + 1, phase % 6 + 1, -b, -a, d - 1)

    #     if score > mscore:
    #         mscore = score
    #
    # return mscore

        if score >= b:
            return score
        if score > a:
            a = score

    return a

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

    def __lt__(self, other):
        return self.f < other.f

def astar(obstacles, start, end):
    """
    Returns a list of tuples (x, y) indicating coordinates, as a path from the
    given start to the given end considering the given obstacles.
    """

    if start in obstacles:
        obstacles.remove(start)
    if end in obstacles:
        obstacles.remove(end)

    start_node = Node(None, start)
    end_node = Node(None, end)
    heap = [start_node]
    seen = set()

    while heap:
        node = heappop(heap)
        seen.add(node.coord)

        # Found end_node, return path excluding start_node
        if node == end_node:
            return [n.coord for n in gen_parents(node)][::-1]

        # Try each direction
        for coord in [tuple(map(add, node.coord, i)) for i in MOVE_COORDS]:
            # Check seen, range and obstacles
            if not (0 <= coord[0] < FIELD_WIDTH and 0 <= coord[1] < FIELD_HEIGHT):
                continue
            if coord in seen or coord in obstacles:
                continue

            new_node = Node(node, coord)

            # Node is already in heap
            for open_node in heap:
                if new_node == open_node and new_node.g > open_node.g:
                    break
            # Node is not yet in heap
            else:
                new_node.h = sum(map(distance, new_node.coord, end_node.coord))
                new_node.f = new_node.g + new_node.h
                heappush(heap, new_node)

# Breadth First Search (BFS) algorithm
###############################################################################

def bfs(obstacles, start, end_coords):
    """
    Returns a dictionary with tuples (x, y) as keys indicating coordinates, and
    a list of tuples (x, y) as values indicating the path from the given start
    to the key's cordinate considering the given obstacles. Mutates
    'end_coords'.
    """

    seen = set([start])
    queue = deque([[start]])

    while queue and end_coords:
        path = queue.popleft()
        current = path[-1]

        if current in end_coords:
            end_coords.remove(current)
            yield (current, path)

        for coord in [tuple(map(add, current, i)) for i in MOVE_COORDS]:
            if not (0 <= coord[0] < FIELD_WIDTH and 0 <= coord[1] < FIELD_HEIGHT):
                continue
            if coord in seen or coord in obstacles:
                continue

            queue.append(path + [coord])
            seen.add(coord)

# Playfield class
###############################################################################

class Playfield:
    """
    Struct to store field data.
    """

    def __init__(self, field):
        self.figures = 4 * [None]
        self.items = {}
        self.fences = set()

        # Parse field strings
        for y, line in enumerate(field):
            for x, char in enumerate(line):
                if char == CELL_SHEEP_1:
                    self.figures[0] = (x, y)
                elif char == CELL_SHEEP_2:
                    self.figures[1] = (x, y)
                elif char == CELL_WOLF_1:
                    self.figures[2] = (x, y)
                elif char == CELL_WOLF_2:
                    self.figures[3] = (x, y)
                elif char == CELL_GRASS:
                    self.items[(x, y)] = AWARD_GRASS
                elif char == CELL_RHUBARB:
                    self.items[(x, y)] = AWARD_RHUBARB
                elif char == CELL_FENCE:
                    self.fences.add((x, y))
                elif char == CELL_SHEEP_1_d:
                    self.figures[0] = (x, y)
                elif char == CELL_SHEEP_2_d:
                    self.figures[1] = (x, y)

    def get_sheep(self, player_nr):
        return self.figures[player_nr - 1]

    def get_wolf(self, player_nr):
        return self.figures[player_nr + 1]

    def is_coord_available(self, coord):
        return not coord in self.fences \
                and 0 <= coord[0] < FIELD_WIDTH \
                and 0 <= coord[1] < FIELD_HEIGHT

    def move_figure(self, figure, coord):
        """
        Simulate figure movement, return copy of playfield.
        """
        playfield = deepcopy(self)
        playfield.figures[playfield.figures.index(figure)] = coord
        return playfield


    def simulate_sheep(self, player_nr, coord):
        """
        Simulate sheep movement, return copy of playfield.
        """
        playfield = deepcopy(self)
        playfield.figures[player_nr - 1] = coord
        return playfield

    def simulate_wolf(self, player_nr, coord):
        """
        Simulate wolf movement, return copy of playfield.
        """
        playfield = deepcopy(self)
        playfield.figures[player_nr + 1] = coord
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

        wolf = playfield.get_wolf(player_nr)
        sheep = playfield.get_sheep(player_nr)
        enemy_wolf = playfield.get_wolf(player_nr % 2 + 1)
        enemy_sheep = playfield.get_sheep(player_nr % 2 + 1)

        coord = (0, 0)
        score = 0.0

        if is_near(sheep, enemy_wolf):
            score += -float("inf")
        else:
            score += -simulate(playfield, player_nr % 2 + 1)

        if playfield.items:
            score += PENALTY_MOVE_NONE

        print("\nplayer:", player_nr)
        print("score:", coord, score)

        for move in sample(MOVE_COORDS, len(MOVE_COORDS)):
            new_coord = tuple(map(add, sheep, move))

            if not playfield.is_coord_available(new_coord):
                continue
            if new_coord in playfield.figures:
                continue
            if is_near(new_coord, enemy_wolf):
                continue

            new_playfield = playfield.move_figure(sheep, new_coord)
            new_score = new_playfield.items.pop(new_coord, 0)
            if is_near(new_coord, enemy_wolf):
                new_score += PENALTY_NEAR_WOLF
            new_score -= simulate(new_playfield, player_nr % 2 + 1)

            print("score:", move, new_score)

            if new_score > score:
                score = new_score
                coord = move

        print("go:   ", coord)
        return COORD_TO_MOVE_CONST[coord]

    def move_wolf(self, player_nr, field):
        return self.debug_move_wolf(player_nr, field)

    @debug_time
    def debug_move_wolf(self, player_nr, field):
        playfield = Playfield(field)

        wolf = playfield.get_wolf(player_nr)
        sheep = playfield.get_sheep(player_nr)
        enemy_wolf = playfield.get_wolf(player_nr % 2 + 1)
        enemy_sheep = playfield.get_sheep(player_nr % 2 + 1)

        coord = (0, 0)
        phase = 6 if player_nr == 1 else 1
        score = -simulate(playfield, player_nr % 2 + 1, phase) + PENALTY_MOVE_NONE

        print("\nplayer:", player_nr)
        print("score:", coord, score)

        for move in sample(MOVE_COORDS, len(MOVE_COORDS)):
            new_coord = tuple(map(add, wolf, move))

            if not playfield.is_coord_available(new_coord):
                continue
            if new_coord in {sheep, enemy_wolf}:
                continue
            if new_coord == enemy_sheep:
                return COORD_TO_MOVE_CONST[move]

            new_playfield = playfield.move_figure(wolf, new_coord)
            new_score = new_playfield.items.pop(new_coord, 0)
            new_score -= simulate(new_playfield, player_nr % 2 + 1, phase)

            print("score:", move, new_score)

            if new_score > score:
                score = new_score
                coord = move

        print("go:   ", coord)
        return COORD_TO_MOVE_CONST[coord]