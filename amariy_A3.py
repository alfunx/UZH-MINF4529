"""
Kingsheep Agent Template

This template is provided for the course 'Practical Artificial Intelligence' of
the University of Zürich.

Please edit the following things before you upload your agent:
    - change the name of your file to '[uzhshortname]_A2.py', where
      [uzhshortname] needs to be your uzh shortname
    - change the name of the class to a name of your choosing
    - change the def 'get_class_name()' to return the new name of your class
    - change the init of your class:
        - self.name can be an (anonymous) name of your choosing
        - self.uzh_shortname needs to be your UZH shortname
    - change the name of the model in get_sheep_model to
      [uzhshortname]_sheep_model
    - change the name of the model in get_wolf_model to
      [uzhshortname]_wolf_model

The results and rankings of the agents will be published on OLAT using your
'name', not 'uzh_shortname', so they are anonymous (and your 'name' is expected
to be funny, no pressure).

"""


GREY = '\033[90m'
RED = '\033[91m'
ENDC = '\033[0m'


# from config import *
import pickle
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
AWARD_BLOCK_SHEEP = 0.6
AWARD_NEAR_EDGE = 0.4
AWARD_NEAR_WOLF = 0.5

#[Penalty]
PENALTY_MOVE_NONE = -1.5
PENALTY_NEAR_EDGE = -1.5
PENALTY_NEAR_WOLF = -12.0

#[Factor]
FACTOR_EAT = 2.0
FACTOR_ENEMY_EAT = 0.5
FACTOR_WOLF_EAT = 0.5

#[Movements]
MOVE_COORDS = [(0, -1), (1, 0), (0, 1), (-1, 0)]
MOVE_OR_STAY_COORDS = [(0, 0), (0, -1), (1, 0), (0, 1), (-1, 0)]
DIAG_COORDS = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
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
CONST_TO_STRING = {
        0: "·",
        -1: "↑",
        2: "→",
        1: "↓",
        -2: "←"
        }


# Functions
###############################################################################

def get_class_name():
    return 'Snowball'

def is_near(a, b):
    return a in {tuple(map(add, b, i)) for i in MOVE_OR_STAY_COORDS}

def surrounding(a):
    if isinstance(a, set):
        return a | {tuple(map(add, x, i)) for i in MOVE_COORDS for x in a}
    if isinstance(a, tuple):
        return {a} | {tuple(map(add, a, i)) for i in MOVE_COORDS}

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

def possible_moves(obstacles, start):
    moves = 0
    for coord in {tuple(map(add, start, i)) for i in MOVE_COORDS}:
        if 0 <= coord[0] < FIELD_WIDTH and 0 <= coord[1] < FIELD_HEIGHT \
                and coord not in obstacles:
            moves += 1
    return moves

def evaluate_playfield_sheep(playfield, player_nr):
    """
    Returns score for playfield (POV of sheep).
    """

    wolf = playfield.get_wolf(player_nr)
    sheep = playfield.get_sheep(player_nr)
    enemy_wolf = playfield.get_wolf(player_nr % 2 + 1)
    enemy_sheep = playfield.get_sheep(player_nr % 2 + 1)

    score = 0.0

    if playfield.items:

        # Sheep must go to grass
        sheep_to_items = dict(bfs(playfield.fences | set(playfield.figures),
                                  sheep, playfield.items.keys()))
        score += sum(map(lambda a: playfield.items[a[0]] / len(a[1]),
                         sheep_to_items.items()))

        if player_nr == 1:

            # Enemy sheep must not go to grass
            enemy_sheep_to_items = dict(bfs(playfield.fences | set(playfield.figures),
                                            enemy_sheep, playfield.items.keys()))
            score -= sum(map(lambda a: playfield.items[a[0]] / len(a[1]) ** 2,
                             enemy_sheep_to_items.items())) * FACTOR_ENEMY_EAT

    else:

        # Sheep must block enemy sheep
        sheep_to_enemy_sheep = astar(playfield.fences | {enemy_wolf, wolf} | surrounding(enemy_wolf),
                                     sheep, enemy_sheep)
        if sheep_to_enemy_sheep:
            score += AWARD_BLOCK_SHEEP / len(sheep_to_enemy_sheep)

        # Enemy sheep must not be able to escape
        enemy_moves = possible_moves(playfield.fences | set(playfield.figures),
                                     enemy_sheep)
        score += AWARD_NEAR_EDGE / (enemy_moves + 1)

        # Sheep must go to wolf
        sheep_to_wolf = astar(playfield.fences | {enemy_sheep, enemy_wolf},
                              sheep, wolf)
        if sheep_to_wolf:
            score += AWARD_NEAR_WOLF / len(sheep_to_wolf)

        # Sheep must be able to escape
        sheep_to_enemy_wolf = astar(playfield.fences | {enemy_sheep, wolf},
                                    sheep, enemy_wolf)
        if sheep_to_enemy_wolf:
            moves = possible_moves(playfield.fences | set(playfield.figures),
                                   sheep)
            score += PENALTY_NEAR_EDGE * (4 - moves) / len(sheep_to_enemy_wolf) / 2
            moves = possible_moves(playfield.fences,
                                   sheep)
            score += PENALTY_NEAR_EDGE * (4 - moves) / len(sheep_to_enemy_wolf) / 2

        # Wolf must follow enemy sheep
        wolf_to_enemy_sheep = astar(playfield.fences | {sheep, enemy_wolf},
                                    wolf, enemy_sheep)
        if wolf_to_enemy_sheep:
            score += AWARD_SHEEP / len(wolf_to_enemy_sheep)

    return score

def evaluate_playfield_wolf(playfield, player_nr):
    """
    Returns score for playfield (POV of wolf).
    """

    wolf = playfield.get_wolf(player_nr)
    sheep = playfield.get_sheep(player_nr)
    enemy_wolf = playfield.get_wolf(player_nr % 2 + 1)
    enemy_sheep = playfield.get_sheep(player_nr % 2 + 1)

    score = 0.0

    if playfield.items:

        # Sheep must go to grass
        sheep_to_items = dict(bfs(playfield.fences | set(playfield.figures),
                                  sheep, playfield.items.keys()))
        score += sum(map(lambda a: playfield.items[a[0]] / len(a[1]) ** 2,
                         sheep_to_items.items()))

        # Enemy sheep must not go to grass
        enemy_sheep_to_items = dict(bfs(playfield.fences | set(playfield.figures),
                                        enemy_sheep, playfield.items.keys()))
        score -= sum(map(lambda a: playfield.items[a[0]] / len(a[1]) ** 2,
                         enemy_sheep_to_items.items())) * FACTOR_ENEMY_EAT

    # Sheep must be able to escape
    sheep_to_enemy_wolf = astar(playfield.fences | {enemy_sheep, wolf},
                                sheep, enemy_wolf)
    if sheep_to_enemy_wolf:
        moves = possible_moves(playfield.fences | set(playfield.figures),
                               sheep)
        score += PENALTY_NEAR_EDGE * (4 - moves) / len(sheep_to_enemy_wolf) / 2
        moves = possible_moves(playfield.fences,
                               sheep)
        score += PENALTY_NEAR_EDGE * (4 - moves) / len(sheep_to_enemy_wolf) / 2

    # Enemy wolf must not go near sheep
    enemy_wolf_to_sheep = astar(playfield.fences | {enemy_sheep, wolf},
                                enemy_wolf, sheep)
    if enemy_wolf_to_sheep:
        score -= AWARD_SHEEP / len(enemy_wolf_to_sheep) * FACTOR_ENEMY_EAT

    # Wolf must follow enemy sheep
    wolf_to_enemy_sheep = astar(playfield.fences | {sheep, enemy_wolf},
                                wolf, enemy_sheep)
    if wolf_to_enemy_sheep:
        score += AWARD_SHEEP / len(wolf_to_enemy_sheep)

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
        for coord in {tuple(map(add, node.coord, i)) for i in MOVE_COORDS}:
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
        for coord in {tuple(map(add, current, i)) for i in MOVE_COORDS}:
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

    def is_coord_available(self, coord, virtual_fence=()):
        return coord not in self.fences \
                and 0 <= coord[0] < FIELD_WIDTH \
                and 0 <= coord[1] < FIELD_HEIGHT \
                and coord not in virtual_fence

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


# Sheep features
###############################################################################

def sheep_features(field, figure):
    """
    Returns array with sheep-features for given field and figure.
    """

    # playfield, sheeps and wolfs
    playfield = Playfield(field)
    wolf = playfield.get_wolf(figure)
    sheep = playfield.get_sheep(figure)
    enemy_wolf = playfield.get_wolf(figure % 2 + 1)
    enemy_sheep = playfield.get_sheep(figure % 2 + 1)

    # Score features
    ###########################################################################

    # best score
    best_score = None

    # best move
    best_move = None

    # score if sheep stays
    score = PENALTY_NEAR_WOLF if is_near(sheep, enemy_wolf) else 0.0
    score += evaluate_playfield_sheep(playfield, figure)
    if playfield.items:
        score += PENALTY_MOVE_NONE
    best_score = score
    best_move = (0, 0)

    print(GREY + COORD_TO_STRING[best_move], ": ", best_score, ENDC)

    # try each direction
    for move in shuffle(MOVE_COORDS):
        coord = tuple(map(add, sheep, move))

        if not playfield.is_coord_available(coord):
            continue
        if coord in playfield.figures:
            continue

        new_playfield = playfield.move_figure(sheep, coord)
        score = new_playfield.items.pop(coord, 0.0) * FACTOR_EAT
        if is_near(coord, enemy_wolf):
            score += PENALTY_NEAR_WOLF
        score += evaluate_playfield_sheep(new_playfield, figure)

        print(GREY + COORD_TO_STRING[move], ": ", score, ENDC)

        if score > best_score:
            best_score = score
            best_move = move

    # create feature array for this game state
    features = [

        # current score is highest
        1 if (0, 0) == best_move else 0,

        # score left is highest
        1 if (-1, 0) == best_move else 0,

        # score right is highest
        1 if (1, 0) == best_move else 0,

        # score above is highest
        1 if (0, -1) == best_move else 0,

        # score below is highest
        1 if (0, 1) == best_move else 0]

    # assert all features have been inserted
    assert len(features) == 5

    return features


# Wolf features
###############################################################################

def wolf_features(field, figure):
    """
    Returns array with wolf-features for given field and figure.
    """

    # playfield, sheeps and wolfs
    playfield = Playfield(field)
    wolf = playfield.get_wolf(figure)
    sheep = playfield.get_sheep(figure)
    enemy_wolf = playfield.get_wolf(figure % 2 + 1)
    enemy_sheep = playfield.get_sheep(figure % 2 + 1)

    # Score features
    ###########################################################################

    # best score
    best_score = None

    # best move
    best_move = None

    # score if wolf stays
    best_score = evaluate_playfield_wolf(playfield, figure)
    best_move = (0, 0)

    print(GREY + COORD_TO_STRING[best_move], ": ", best_score, ENDC)

    # try each direction
    for move in shuffle(MOVE_COORDS):
        coord = tuple(map(add, wolf, move))

        if not playfield.is_coord_available(coord):
            continue
        if coord in {sheep, enemy_wolf}:
            continue

        score = 0.0

        if coord == enemy_sheep:
            score += AWARD_SHEEP
        else:
            new_playfield = playfield.move_figure(wolf, coord)
            score += new_playfield.items.pop(coord, 0.0) * FACTOR_WOLF_EAT
            score += evaluate_playfield_wolf(new_playfield, figure)

        print(GREY + COORD_TO_STRING[move], ": ", score, ENDC)

        if score > best_score:
            best_score = score
            best_move = move

    # create feature array for this game state
    features = [

        # current score is highest
        1 if (0, 0) == best_move else 0,

        # score left is highest
        1 if (-1, 0) == best_move else 0,

        # score right is highest
        1 if (1, 0) == best_move else 0,

        # score above is highest
        1 if (0, -1) == best_move else 0,

        # score below is highest
        1 if (0, 1) == best_move else 0]

    # assert all features have been inserted
    assert len(features) == 5

    return features


# Agent
###############################################################################

class Snowball():
    """
    Agent for assignment 2, by Alphonse Mariyagnanaseelan.
    """

    def __init__(self):
        self.name = "snowball"
        self.uzh_shortname = "amariy"

    def get_sheep_model(self):
        return pickle.load(open('amariy_sheep_model.sav', 'rb'))

    def get_wolf_model(self):
        return pickle.load(open('amariy_wolf_model.sav', 'rb'))

    def move_sheep(self, figure, field, sheep_model):
        result = sheep_model.predict([sheep_features(field, figure)])
        print("go: ", RED + CONST_TO_STRING[result[0]] + ENDC)
        return result

    def move_wolf(self, figure, field, wolf_model):
        result = wolf_model.predict([wolf_features(field, figure)])
        print("go: ", RED + CONST_TO_STRING[result[0]] + ENDC)
        return result


# s = Snowball()
# sheep = pickle.load(open('/home/amariya/Dropbox/UZH/19-FS/Practical Artificial Intelligence/Exercise/Assignment_3/amariya_player/amariy_sheep_model.sav', 'rb'))
# wolf = pickle.load(open('/home/amariya/Dropbox/UZH/19-FS/Practical Artificial Intelligence/Exercise/Assignment_3/amariya_player/amariy_wolf_model.sav', 'rb'))
#
# fields = [
#     [['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', 'r', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', 'S', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', 'w', 's', 'W', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.']],
#     [['.', '.', '.', '.', '.', '.', '.', '.', 'W', 's', 'w', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', 'S', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', 'r', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.']],
#     [['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['w', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['s', '.', '.', '.', '.', '.', '.', 'r', '.', 'S', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['W', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.']],
#     [['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', 'W'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', 'S', '.', 'r', '.', '.', '.', '.', '.', '.', 's'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', 'w'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.']],
#     [['.', '.', '.', '.', '.', '.', '.', '.', '.', 'w', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', 's', 'W', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', 'S', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.']]]
#
# for f in fields:
#     # s.move_sheep(1, f, sheep)
#     print(sheep_features(f, 1))
#
# fields = [
#     [['.', '.', '.', '.', '.', '.', '.', '.', '.', 'S', 'w', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', 's', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', 'W', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.']],
#     [['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', 'W', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', 's', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', 'w', 'S', '.', '.', '.', '.', '.', '.', '.', '.', '.']],
#     [['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['w', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['S', '.', '.', '.', '.', '.', '.', 's', '.', 'W', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.']],
#     [['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', 'W', '.', 's', '.', '.', '.', '.', '.', '.', 'S'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', 'w'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.']],
#     [['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', 'r', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '#', '#', '#', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '#', 's', '#', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '#', '#', '#', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', 'r', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', 'S', '.', '.', '.', '.', '.', '.', 'w', '.', 'W', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.']]]
#
# for f in fields:
#     # s.move_wolf(1, f, wolf)
#     print(wolf_features(f, 1))
