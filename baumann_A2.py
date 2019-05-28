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

from config import *
import pickle


import random
from collections import deque
from config import *
from operator import add
import copy


MOVE_COORDS = {(0, +1), (0, -1), (+1, 0), (-1,0)}

def bfs(obstacles, start, end_coords):
    """
    Returns a dictionary with tuples (x, y) as keys indicating coordinates, and
    a list of tuples (x, y) as values indicating the path from the given start
    to the key's cordinate considering the given obstacles.
    """

    seen = set([start])
    queue = deque([[start]])
    end_coords = set(end_coords)
    paths = {}

    while queue and end_coords:
        path = queue.popleft()
        current = path[-1]

        # Found an objective, yield objective and path
        if current in end_coords:
            end_coords.remove(current)
            paths[current] = path

        # Try each direction
        for coord in [tuple(map(add, current, i)) for i in MOVE_COORDS]:
            if not (0 <= coord[0] < FIELD_HEIGHT and 0 <= coord[1] < FIELD_WIDTH):
                continue
            if coord in seen or coord in obstacles:
                continue

            queue.append(path + [coord])
            seen.add(coord)

    return paths

def get_player_position(figure, field):
    x = [x for x in field if figure in x][0]
    return (field.index(x), x.index(figure))

def valid_move(figure, x_new, y_new, field):
    # Neither the sheep nor the wolf, can step on a square outside the map. Imagine the map is surrounded by fences.
    if x_new > FIELD_HEIGHT - 1:
        return False
    elif x_new < 0:
        return False
    elif y_new > FIELD_WIDTH - 1:
        return False
    elif y_new < 0:
        return False

    # Neither the sheep nor the wolf, can enter a square with a fence on.
    if field[x_new][y_new] == CELL_FENCE:
        return False

    # Wolfs can not step on squares occupied by the opponents wolf (wolfs block each other).
    # Wolfs can not step on squares occupied by the sheep of the same player .
    if figure == CELL_WOLF_1:
        if field[x_new][y_new] == CELL_WOLF_2:
            return False
        elif field[x_new][y_new] == CELL_SHEEP_1:
            return False
    elif figure == CELL_WOLF_2:
        if field[x_new][y_new] == CELL_WOLF_1:
            return False
        elif field[x_new][y_new] == CELL_SHEEP_2:
            return False

    # Sheep can not step on squares occupied by the wolf of the same player.
    # Sheep can not step on squares occupied by the opposite sheep.
    if figure == CELL_SHEEP_1:
        if field[x_new][y_new] == CELL_SHEEP_2 or \
                field[x_new][y_new] == CELL_WOLF_1:
            return False
    elif figure == CELL_SHEEP_2:
        if field[x_new][y_new] == CELL_SHEEP_1 or \
                field[x_new][y_new] == CELL_WOLF_2:
            return False

    return True

def super_score(field, new_field, player_number, i_am_sheep):

    overall_score = 0.0

    if player_number == 1:
        mySheep = CELL_SHEEP_1
        mySheep_dead = CELL_SHEEP_1_d
        opponentSheep = CELL_SHEEP_2
        opponentSheep_dead = CELL_SHEEP_2_d
        myWolf = CELL_WOLF_1
        opponentWolf = CELL_WOLF_2
    else:
        mySheep = CELL_SHEEP_2
        mySheep_dead = CELL_SHEEP_2_d
        opponentSheep = CELL_SHEEP_1
        opponentSheep_dead = CELL_SHEEP_1_d
        myWolf = CELL_WOLF_2
        opponentWolf = CELL_WOLF_1

    if i_am_sheep == 1:
        try:
            my_sheep_position = get_player_position(mySheep, new_field)
        except:
            my_sheep_position = get_player_position(mySheep_dead, new_field)

        my_wolf_position = get_player_position(myWolf, new_field)

        try:
            opponent_sheep_position = get_player_position(opponentSheep, field)
        except:
            opponent_sheep_position = get_player_position(opponentSheep_dead, field)

        opponent_wolf_position = get_player_position(opponentWolf, field)

    else:
        try:
            my_sheep_position = get_player_position(mySheep, field)
        except:
            my_sheep_position = get_player_position(mySheep_dead, field)

        my_wolf_position = get_player_position(myWolf, field)

        try:
            opponent_sheep_position = get_player_position(opponentSheep, new_field)

        except:
            opponent_sheep_position = get_player_position(opponentSheep_dead, new_field)

        opponent_wolf_position = get_player_position(opponentWolf, new_field)


    if my_sheep_position == opponent_wolf_position:
        return -300.0
    if my_wolf_position == opponent_sheep_position:
        return 300.0

    if valid_move(mySheep, my_sheep_position[0], my_sheep_position[1] - 1, new_field):
        if (my_sheep_position[0], my_sheep_position[1] - 1) == opponent_wolf_position:
            overall_score -= 30


    if valid_move(mySheep, my_sheep_position[0], my_sheep_position[1] + 1, new_field):
        if (my_sheep_position[0], my_sheep_position[1] + 1) == opponent_wolf_position:
            overall_score -= 30


    if valid_move(mySheep, my_sheep_position[0] - 1, my_sheep_position[1], new_field):
        if (my_sheep_position[0] - 1, my_sheep_position[1]) == opponent_wolf_position:
            overall_score -= 30


    if valid_move(mySheep, my_sheep_position[0] + 1, my_sheep_position[1], new_field):
        if (my_sheep_position[0] + 1, my_sheep_position[1]) == opponent_wolf_position:
            overall_score -= 30


#      if i_am_sheep and field[my_sheep_position[0]][my_sheep_position[1]] == CELL_RHUBARB:

    if field[my_sheep_position[0]][my_sheep_position[1]] == CELL_RHUBARB:
        overall_score += 15.0
    elif field[my_sheep_position[0]][my_sheep_position[1]] == CELL_GRASS:
        overall_score += 4.0


    my_sheep_obstacles = []
    my_sheep_coords = []

    my_sheep_coords_ohnegras = []

    my_sheep_coords_nofood = []
    my_sheep_obstacles_nofood = []

    my_wolf_obstacles = []
    my_wolf_coords = []

    # make list of possible goals
    y_position = 0
    for line in new_field:
        x_position = 0
        for item in line:

        # my wolfe's obstacles and coords
            if item in {CELL_FENCE, mySheep, opponentWolf}:
                my_wolf_obstacles.append((y_position, x_position))
            if item == opponentSheep:
                my_wolf_coords.append((y_position, x_position))

        # my sheep's obstacles and coords With food
            # my sheep's obstacles
            if item in {CELL_FENCE, myWolf, opponentSheep, opponentWolf}:
                my_sheep_obstacles.append((y_position, x_position))
            # my sheep's coords
            if item == CELL_RHUBARB or item == CELL_GRASS:
                my_sheep_coords.append((y_position, x_position))
                my_sheep_coords_ohnegras.append((y_position, x_position))

        # my sheep's obstacles and coords IF NO FOOD AVAILABLE
            # my sheep's obstacles
            if item in {CELL_FENCE, myWolf}:
                my_sheep_obstacles_nofood.append((y_position, x_position))
            if item == opponentWolf or item == opponentSheep:
                my_sheep_coords_nofood.append((y_position, x_position))

            x_position += 1
        y_position += 1



    sheep_paths = bfs(my_sheep_obstacles, my_sheep_position, my_sheep_coords)
    sheep_paths_nofood = bfs(my_sheep_obstacles_nofood, my_sheep_position, my_sheep_coords_nofood)
    wolf_paths = bfs(my_wolf_obstacles, my_wolf_position, my_wolf_coords)





    value = 0.0


    if my_sheep_coords_ohnegras:

        for current_pair in sheep_paths.items():

            if new_field[current_pair[0][0]][current_pair[0][1]] == CELL_GRASS:
                value = 1.0
            elif new_field[current_pair[0][0]][current_pair[0][1]] == CELL_RHUBARB:
                value = 5.0
            elif new_field[current_pair[0][0]][current_pair[0][1]] == opponentWolf:
                value = -30
            else:
                value = 0.0001


            path_length = len(current_pair[1])
            score = value / path_length
            overall_score += score


    elif i_am_sheep == 1:

        for current_pair in sheep_paths_nofood.items():

            if new_field[current_pair[0][0]][current_pair[0][1]] == CELL_GRASS:
                value = 1.0
            elif new_field[current_pair[0][0]][current_pair[0][1]] == CELL_RHUBARB:
                value = 5.0
            elif new_field[current_pair[0][0]][current_pair[0][1]] == opponentWolf:
                value = -1
            elif new_field[current_pair[0][0]][current_pair[0][1]] == opponentSheep:
                value = 30
            else:
                value = 0.0001



            path_length = len(current_pair[1])
            score = value / path_length


            overall_score += score


    if i_am_sheep == 1:

        for current_pair in wolf_paths.items():


            if new_field[current_pair[0][0]][current_pair[0][1]] == opponentSheep:
                value = 85.0
            else:
                value = 0.001


            path_length = len(current_pair[1])

            score = value / path_length

            overall_score += score


    if i_am_sheep == 1 and not my_sheep_coords_ohnegras:

        for current_pair in wolf_paths.items():


            if new_field[current_pair[0][0]][current_pair[0][1]] == opponentSheep:
                value = 85.0
            else:
                value = 0.001


            path_length = len(current_pair[1])

            score = value / path_length

            overall_score += score



    return overall_score


def my_sheep_features(player_number, field, game_features):
    enemyPercentage = 0.2

    s_feature1 = -100
    s_feature2 = -100
    s_feature3 = -100
    s_feature4 = -100
    s_feature5 = -100

    if player_number == 1:
        opponent_number = 2
    else:
        opponent_number = 1

    if player_number == 1:
        mySheep = CELL_SHEEP_1
        opponentSheep = CELL_SHEEP_2
        myWolf = CELL_WOLF_1
        opponentWolf = CELL_WOLF_2
    else:
        mySheep = CELL_SHEEP_2
        opponentSheep = CELL_SHEEP_1
        myWolf = CELL_WOLF_2
        opponentWolf = CELL_WOLF_1

    sheep_position = get_player_position(mySheep, field)
    wolf_position = get_player_position(myWolf, field)

    i_am_sheep = 1


    s_feature5 = super_score(field, field, player_number, 1) -0.2

    s_feature5 -= super_score(field, field, opponent_number, 0) * enemyPercentage


    if valid_move(mySheep, sheep_position[0] + 1, sheep_position[1], field):
        sheep_position_new = [sheep_position[0] + 1, sheep_position[1]]
        sheep_position_old = [sheep_position[0], sheep_position[1]]
        new_field = copy.deepcopy(field)
        new_field[sheep_position_new[0]][sheep_position_new[1]] = mySheep
        new_field[sheep_position_old[0]][sheep_position_old[1]] = "."

        s_feature2 = super_score(field, new_field, player_number, 1)
        s_feature2 -= super_score(field, new_field, opponent_number, 0) * enemyPercentage


    if valid_move(mySheep, sheep_position[0] - 1, sheep_position[1], field):
        sheep_position_new = [sheep_position[0] - 1, sheep_position[1]]
        sheep_position_old = [sheep_position[0], sheep_position[1]]
        new_field = copy.deepcopy(field)
        new_field[sheep_position_new[0]][sheep_position_new[1]] = mySheep
        new_field[sheep_position_old[0]][sheep_position_old[1]] = "."

        s_feature3 = super_score(field, new_field, player_number, 1)
        s_feature3 -= super_score(field, new_field, opponent_number, 0) * enemyPercentage


    if valid_move(mySheep, sheep_position[0], sheep_position[1] - 1, field):
        sheep_position_new = [sheep_position[0], sheep_position[1] - 1]
        sheep_position_old = [sheep_position[0], sheep_position[1]]
        new_field = copy.deepcopy(field)
        new_field[sheep_position_new[0]][sheep_position_new[1]] = mySheep
        new_field[sheep_position_old[0]][sheep_position_old[1]] = "."

        s_feature4 = super_score(field, new_field, player_number, 1)
        s_feature4 -= super_score(field, new_field, opponent_number, 0) * enemyPercentage


    if valid_move(mySheep, sheep_position[0], sheep_position[1] + 1, field):
        sheep_position_new = [sheep_position[0], sheep_position[1] + 1]
        sheep_position_old = [sheep_position[0], sheep_position[1]]
        new_field = copy.deepcopy(field)
        new_field[sheep_position_new[0]][sheep_position_new[1]] = mySheep
        new_field[sheep_position_old[0]][sheep_position_old[1]] = "."

        s_feature1 = super_score(field, new_field, player_number, 1)
        s_feature1 -= super_score(field, new_field, opponent_number, 0) * enemyPercentage

    game_features.append(s_feature1)
    game_features.append(s_feature2)
    game_features.append(s_feature3)
    game_features.append(s_feature4)
    game_features.append(s_feature5)

    myfeature = game_features.index(max(game_features))
    my_game_features = [0, 0, 0, 0, 0]
    my_game_features[myfeature] = 1

    return my_game_features


def my_wolf_features(player_number, field, game_features):
    w_feature1 = -100
    w_feature2 = -100
    w_feature3 = -100
    w_feature4 = -100
    w_feature5 = -100

    if player_number == 1:
        opponent_number = 2
    else:
        opponent_number = 1

    if player_number == 1:
        mySheep = CELL_SHEEP_1
        opponentSheep = CELL_SHEEP_2
        myWolf = CELL_WOLF_1
        opponentWolf = CELL_WOLF_2
    else:
        mySheep = CELL_SHEEP_2
        opponentSheep = CELL_SHEEP_1
        myWolf = CELL_WOLF_2
        opponentWolf = CELL_WOLF_1


    sheep_position = get_player_position(myWolf, field)

    enemyPercentage = 0.2

    i_am_sheep = 0


    w_feature5 = super_score(field, field, player_number, 1) - 0.2
    w_feature5 -= super_score(field, field, opponent_number, 0) * enemyPercentage



    if valid_move(myWolf, sheep_position[0] + 1, sheep_position[1], field):

        sheep_position_new = [sheep_position[0] + 1, sheep_position[1]]
        sheep_position_old = [sheep_position[0], sheep_position[1]]


        new_field = copy.deepcopy(field)
        new_field[sheep_position_new[0]][sheep_position_new[1]] = myWolf
        new_field[sheep_position_old[0]][sheep_position_old[1]] = "."


        w_feature2 = super_score(field, new_field, player_number, 1)
        w_feature2 -= super_score(field, new_field, opponent_number, 0) * enemyPercentage



    if valid_move(myWolf, sheep_position[0] - 1, sheep_position[1], field):
        sheep_position_new = [sheep_position[0] - 1, sheep_position[1]]
        sheep_position_old = [sheep_position[0], sheep_position[1]]


        new_field = copy.deepcopy(field)
        new_field[sheep_position_new[0]][sheep_position_new[1]] = myWolf
        new_field[sheep_position_old[0]][sheep_position_old[1]] = "."


        w_feature3 = super_score(field, new_field, player_number, 1)
        w_feature3 -= super_score(field, new_field, opponent_number, 0) * enemyPercentage


    if valid_move(myWolf, sheep_position[0], sheep_position[1] - 1, field):
        sheep_position_new = [sheep_position[0], sheep_position[1] - 1]
        sheep_position_old = [sheep_position[0], sheep_position[1]]

        new_field = copy.deepcopy(field)
        new_field[sheep_position_new[0]][sheep_position_new[1]] = myWolf
        new_field[sheep_position_old[0]][sheep_position_old[1]] = "."

        w_feature4 = super_score(field, new_field, player_number, 1)
        w_feature4 -= super_score(field, new_field, opponent_number, 0) * enemyPercentage


    if valid_move(myWolf, sheep_position[0], sheep_position[1] + 1, field):
        sheep_position_new = [sheep_position[0], sheep_position[1] + 1]
        sheep_position_old = [sheep_position[0], sheep_position[1]]
        new_field = copy.deepcopy(field)
        new_field[sheep_position_new[0]][sheep_position_new[1]] = myWolf
        new_field[sheep_position_old[0]][sheep_position_old[1]] = "."

        w_feature1 = super_score(field, new_field, player_number, 1)
        w_feature1 -= super_score(field, new_field, opponent_number, 0) * enemyPercentage

    game_features.append(w_feature1)
    game_features.append(w_feature2)
    game_features.append(w_feature3)
    game_features.append(w_feature4)
    game_features.append(w_feature5)

    myfeature = game_features.index(max(game_features))
    my_game_features = [0, 0, 0, 0, 0]
    my_game_features[myfeature] = 1

    return my_game_features


def get_class_name():
    return 'JoaBau'



class JoaBau():
    """Example class for a Kingsheep player"""

    def __init__(self):
        self.name = "wie_traktor_panzer"
        self.uzh_shortname = "JoaBau"

    def get_sheep_model(self):
        return pickle.load(open('baumann_sheep_model.sav','rb'))

    def get_wolf_model(self):
        return pickle.load(open('baumann_wolf_model.sav','rb'))

    def move_sheep(self, figure, field, sheep_model):


        X_sheep = []
        
        #preprocess field to get features, add to X_field
        #this code is largely copied from the Jupyter Notebook where the models were trained

        #create empty feature array for this game state
        game_features = []
        
        if figure == 1:
            player_number = 1
        else:
            player_number = 2

        game_features = my_sheep_features(player_number, field, game_features)

        #add features and move to X_sheep and Y_sheep
        X_sheep.append(game_features)

        result = sheep_model.predict(X_sheep)
        return result


    def move_wolf(self, figure, field, wolf_model):

        # create empty feature array for this game state
        game_features = []
        X_wolf = []

        if figure == 1:
            player_number = 1
        else:
            player_number = 2


        game_features = my_wolf_features(player_number, field, game_features)

        #add features and move to X_wolf and Y_wolf
        X_wolf.append(game_features)

        result = wolf_model.predict(X_wolf)

        return result
