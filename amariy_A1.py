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
from copy import deepcopy
from heapq import heappush, heappop
from operator import add
from random import sample

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
AWARD_SHEEP = 10.0
AWARD_BLOCK_SHEEP = 0.1

#[Penalty]
PENALTY_MOVE_NONE = -1.5
PENALTY_NEAR_EDGE = -20.0
PENALTY_NEAR_WOLF = -7.0
PENALTY_STUCK = -0.9

#[Factor]
FACTOR_ENEMY_EAT = -0.5
FACTOR_EAT = 5.0

#[Alpha-Beta]
ALPHA = 5.0 * PENALTY_NEAR_WOLF
BETA = 5.0 * AWARD_SHEEP
ALPHA = float("-inf")
BETA = float("inf")

#[Movements]
MOVE_COORDS = [(0, -1), (1, 0), (0, 1), (-1, 0)]
MOVE_OR_STAY_COORDS = [(0, 0), (0, -1), (1, 0), (0, 1), (-1, 0)]
COORD_TO_MOVE_CONST = {
        (0, 0): MOVE_NONE,
        (0, -1): MOVE_UP,
        (1, 0): MOVE_RIGHT,
        (0, 1): MOVE_DOWN,
        (-1, 0): MOVE_LEFT
        }
COORD_TO_STRING = {
        (0, 0): "·",
        (0, -1): "↑",
        (1, 0): "→",
        (0, 1): "↓",
        (-1, 0): "←"
        }

# Functions
###############################################################################

def get_class_name():
    return 'Alfunx'

def is_near(a, b):
    return a in [tuple(map(add, b, i)) for i in MOVE_OR_STAY_COORDS]

def distance(a, b):
    return (a - b) ** 2

def shuffle(a):
    return sample(a, len(a))

def gen_parents(node):
    yield node
    node = node.parent
    while node:
        yield node
        node = node.parent

def add_margin(coords):
    new_coords = list(coords)
    for c in coords:
        new_coords.extend([tuple(map(add, c, i)) for i in MOVE_COORDS])
    return new_coords

def possible_moves(obstacles, start, wolf=None):
    moves = 0
    for coord in [tuple(map(add, start, i)) for i in MOVE_COORDS]:
        if 0 <= coord[0] < FIELD_WIDTH and 0 <= coord[1] < FIELD_HEIGHT \
                and coord not in obstacles \
                and (not is_near(coord, wolf) if wolf else True):
            moves += 1
    return moves

def evaluate_playfield(playfield, player_nr):
    """
    Returns score for playfield.
    """

    wolf = playfield.get_wolf(player_nr)
    sheep = playfield.get_sheep(player_nr)
    enemy_wolf = playfield.get_wolf(player_nr % 2 + 1)
    enemy_sheep = playfield.get_sheep(player_nr % 2 + 1)

    score = 0.0

    # Sheep must not be near enemy wolf
    if is_near(sheep, enemy_wolf):
        score += PENALTY_NEAR_WOLF

    # Sheep must be able to escape
    moves = possible_moves(playfield.fences.union(playfield.figures),
                           sheep, enemy_wolf)
    if moves < 2:
        score += PENALTY_NEAR_EDGE / (moves + 1)

    if playfield.items:
        # Sheep must go to grass
        sheep_to_items = dict(bfs(playfield.fences.union(playfield.figures),
                                  sheep, playfield.items.keys()))
        score += sum(map(lambda a: playfield.items[a[0]] / len(a[1]),
                         sheep_to_items.items()))

        # Enemy sheep must not go to grass
        enemy_sheep_to_items = dict(bfs(playfield.fences.union(playfield.figures),
                                        enemy_sheep, playfield.items.keys()))
        score += sum(map(lambda a: playfield.items[a[0]] / len(a[1]),
                         enemy_sheep_to_items.items())) * FACTOR_ENEMY_EAT

    else:
        # Sheep must block enemy sheep
        sheep_to_enemy_sheep = astar(playfield.fences.union({enemy_wolf}),
                                     sheep, enemy_sheep)
        if sheep_to_enemy_sheep:
            score += AWARD_BLOCK_SHEEP / len(sheep_to_enemy_sheep)

    # Wolf must follow enemy sheep
    wolf_to_enemy_sheep = astar(playfield.fences.union({sheep, enemy_wolf}),
                                wolf, enemy_sheep)
    if wolf_to_enemy_sheep:
        score += AWARD_SHEEP / len(wolf_to_enemy_sheep)

    return score

# Simulate
###############################################################################

def simulate(playfield, player_nr, phase=None, a=ALPHA, b=BETA, d=1):
    if not phase:
        phase = 4 if player_nr == 1 else 5

    # Max depth, return score
    if not d:
        return evaluate_playfield(playfield, player_nr)

    # maximum = evaluate_playfield(playfield, player_nr)
    # if b > maximum:
    #     b = maximum
    #     if a >= b:
    #         return b

    wolf = playfield.get_wolf(player_nr)
    sheep = playfield.get_sheep(player_nr)
    enemy_wolf = playfield.get_wolf(player_nr % 2 + 1)
    enemy_sheep = playfield.get_sheep(player_nr % 2 + 1)
    active = wolf if phase in {5, 6} else sheep

    # Try each direction
    for coord in shuffle([tuple(map(add, active, i)) for i in MOVE_OR_STAY_COORDS]):
        if not playfield.is_coord_available(coord):
            continue

        score = 0.0

        # Wolf phase
        if phase in {5, 6}:
            if coord in {sheep, enemy_wolf}:
                continue
            if coord == wolf:
                score += PENALTY_MOVE_NONE
        # Sheep phase
        else:
            if coord in {wolf, enemy_sheep, enemy_wolf}:
                continue
            if coord == sheep:
                score += PENALTY_MOVE_NONE

        if phase in {5, 6} and coord == enemy_sheep:
            score += AWARD_SHEEP
        else:
            new_playfield = playfield.move_figure(active, coord)
            eat_score = new_playfield.items.pop(coord, 0.0)
            score += eat_score * FACTOR_EAT if phase not in {5, 6} else 0.0
            score -= simulate(new_playfield, player_nr % 2 + 1, phase % 6 + 1, -b, -a, d - 1)

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
    heap = [start_node]
    seen = set()

    while heap:
        node = heappop(heap)
        seen.add(node.coord)

        # Found end, return path
        if node.coord == end:
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
                if new_node == open_node:
                    if new_node.g < open_node.g:
                        open_node.g = new_node.g
                        open_node.f = new_node.g + sum(map(distance, new_node.coord, end))
                    break
            # Node is not yet in heap
            else:
                new_node.f = new_node.g + sum(map(distance, new_node.coord, end))
                heappush(heap, new_node)

# Breadth First Search (BFS) algorithm
###############################################################################

def bfs(obstacles, start, end_coords):
    """
    Returns a dictionary with tuples (x, y) as keys indicating coordinates, and
    a list of tuples (x, y) as values indicating the path from the given start
    to the key's cordinate considering the given obstacles.
    """

    seen = set([start])
    queue = deque([[start]])
    end_coords = set(end_coords)

    while queue and end_coords:
        path = queue.popleft()
        current = path[-1]

        # Found an objective, yield objective and path
        if current in end_coords:
            end_coords.remove(current)
            yield (current, path)

        # Try each direction
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
        playfield.figures[self.figures.index(figure)] = coord
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

    def move_sheep(self, player_nr, field):
        playfield = Playfield(field)
        wolf = playfield.get_wolf(player_nr)
        sheep = playfield.get_sheep(player_nr)
        enemy_wolf = playfield.get_wolf(player_nr % 2 + 1)
        enemy_sheep = playfield.get_sheep(player_nr % 2 + 1)

        # Score if sheep stays
        best_move = (0, 0)
        best_score = PENALTY_MOVE_NONE
        best_score -= simulate(playfield, player_nr % 2 + 1, 4 if player_nr == 1 else 5) * 0.5
        best_score -= simulate(playfield, player_nr % 2 + 1, 2 if player_nr == 1 else 3) * 0.5

        # Sheep must not be near wolf
        if is_near(sheep, enemy_wolf):
            best_score += PENALTY_NEAR_WOLF

        # Sheep must be able to escape
        moves = possible_moves(playfield.fences.union(playfield.figures),
                               sheep, enemy_wolf)
        if moves < 2:
            best_score += PENALTY_NEAR_EDGE / (moves + 1)

        print("\nplayer:", player_nr)
        print("score:", COORD_TO_STRING[best_move], "{0:.2f}".format(best_score))

        # Try each direction
        for move in shuffle(MOVE_COORDS):
            coord = tuple(map(add, sheep, move))

            if not playfield.is_coord_available(coord):
                continue
            if coord in playfield.figures:
                continue

            new_playfield = playfield.move_figure(sheep, coord)
            score = new_playfield.items.pop(coord, 0.0) * FACTOR_EAT

            score -= simulate(new_playfield, player_nr % 2 + 1, 4 if player_nr == 1 else 5) * 0.5
            score -= simulate(new_playfield, player_nr % 2 + 1, 2 if player_nr == 1 else 3) * 0.5

            # Sheep must not be near wolf
            if is_near(coord, enemy_wolf):
                score += PENALTY_NEAR_WOLF

            # Sheep must be able to escape
            moves = possible_moves(new_playfield.fences.union(new_playfield.figures),
                                   coord, enemy_wolf)
            if moves < 2:
                score += PENALTY_NEAR_EDGE / (moves + 1)

            print("score:", COORD_TO_STRING[move], "{0:.2f}".format(score))

            if score > best_score:
                best_score = score
                best_move = move

        print("go:   ", COORD_TO_STRING[best_move])
        return COORD_TO_MOVE_CONST[best_move]

    def move_wolf(self, player_nr, field):
        playfield = Playfield(field)
        wolf = playfield.get_wolf(player_nr)
        sheep = playfield.get_sheep(player_nr)
        enemy_wolf = playfield.get_wolf(player_nr % 2 + 1)
        enemy_sheep = playfield.get_sheep(player_nr % 2 + 1)

        # Score if wolf stays
        best_move = (0, 0)
        phase = 6 if player_nr == 1 else 1
        best_score = -simulate(playfield, player_nr % 2 + 1, phase) + PENALTY_MOVE_NONE

        # Wolf must follow enemy sheep
        wolf_to_enemy_sheep = astar(playfield.fences.union({sheep, enemy_wolf}),
                                    wolf, enemy_sheep)
        if wolf_to_enemy_sheep:
            best_score += AWARD_SHEEP / len(wolf_to_enemy_sheep)

        # Enemy sheep must not go to grass
        enemy_sheep_to_items = dict(bfs(playfield.fences.union(playfield.figures),
                                        enemy_sheep, playfield.items.keys()))
        best_score += sum(map(lambda a: playfield.items[a[0]] / len(a[1]),
                              enemy_sheep_to_items.items())) * FACTOR_ENEMY_EAT

        print("\nplayer:", player_nr)
        print("score:", COORD_TO_STRING[best_move], "{0:.2f}".format(best_score))

        # Try each direction
        for move in shuffle(MOVE_COORDS):
            coord = tuple(map(add, wolf, move))

            if not playfield.is_coord_available(coord):
                continue
            if coord in {sheep, enemy_wolf}:
                continue
            if coord == enemy_sheep:
                return COORD_TO_MOVE_CONST[move]

            new_playfield = playfield.move_figure(wolf, coord)
            new_playfield.items.pop(coord, 0.0)
            score = -simulate(new_playfield, player_nr % 2 + 1, phase)

            # Wolf must follow enemy sheep
            wolf_to_enemy_sheep = astar(new_playfield.fences.union({sheep, enemy_wolf}),
                                        coord, enemy_sheep)
            if wolf_to_enemy_sheep:
                score += AWARD_SHEEP / len(wolf_to_enemy_sheep)

            # Enemy sheep must not go to grass
            enemy_sheep_to_items = dict(bfs(new_playfield.fences.union(new_playfield.figures),
                                            enemy_sheep, new_playfield.items.keys()))
            score += sum(map(lambda a: new_playfield.items[a[0]] / len(a[1]),
                             enemy_sheep_to_items.items())) * FACTOR_ENEMY_EAT

            print("score:", COORD_TO_STRING[move], "{0:.2f}".format(score))

            if score > best_score:
                best_score = score
                best_move = move

        print("go:   ", COORD_TO_STRING[best_move])
        return COORD_TO_MOVE_CONST[best_move]
