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


def get_class_name():
    return 'Joe'

class Joe():
    """Example class for a Kingsheep player"""

    def __init__(self):
        self.name = "masern_at_IFI"
        self.uzh_shortname = "joabau"



    def get_sheep_model(self):
        return None

    def get_wolf_model(self):
        return None





    def get_player_position(self, figure, field):
        x = [x for x in field if figure in x][0]
        return (field.index(x), x.index(figure))

    # defs for sheep
    def food_present(self, field):
        food_present = False

        for line in field:
            for item in line:
                if item == CELL_RHUBARB or item == CELL_GRASS:
                    food_present = True
                    break
        return food_present

    def closest_goal(self, player_number, field):
        possible_goals = []

        if player_number == 1:
            sheep_position = self.get_player_position(CELL_SHEEP_1, field)
        else:
            sheep_position = self.get_player_position(CELL_SHEEP_2, field)

        # make list of possible goals

        y_position = 0
        for line in field:
            x_position = 0
            for item in line:
                if item == CELL_RHUBARB or item == CELL_GRASS:
                    possible_goals.append((y_position, x_position))
                x_position += 1
            y_position += 1

        # determine closest item and return
        distance = 1000
        for possible_goal in possible_goals:
            if (abs(possible_goal[0] - sheep_position[0]) + abs(possible_goal[1] - sheep_position[1])) < distance:
                distance = abs(possible_goal[0] - sheep_position[0]) + abs(possible_goal[1] - sheep_position[1])
                final_goal = (possible_goal)

        return final_goal

    def gather_closest_goal(self, closest_goal, field, figure):
        figure_position = self.get_player_position(figure, field)

        distance_x = figure_position[1] - closest_goal[1]
        distance_y = figure_position[0] - closest_goal[0]

        if distance_x == 0:
            # print('item right above/below me')
            if distance_y > 0:
                if self.valid_move(figure, figure_position[0] - 1, figure_position[1], field):
                    return MOVE_UP
                else:
                    return MOVE_RIGHT
            else:
                if self.valid_move(figure, figure_position[0] + 1, figure_position[1], field):
                    return MOVE_DOWN
                else:
                    return MOVE_RIGHT
        elif distance_y == 0:
            # print('item right beside me')
            if distance_x > 0:
                if self.valid_move(figure, figure_position[0], figure_position[1] - 1, field):

                    return MOVE_LEFT
                else:
                    return MOVE_UP
            else:
                if self.valid_move(figure, figure_position[0], figure_position[1] + 1, field):
                    return MOVE_RIGHT
                else:
                    return MOVE_UP

        else:
            # go left or up
            if distance_x > 0 and distance_y > 0:
                if self.valid_move(figure, figure_position[0], figure_position[1] - 1, field):
                    return MOVE_LEFT
                else:
                    return MOVE_UP

            # go left or down
            elif distance_x > 0 and distance_y < 0:
                if self.valid_move(figure, figure_position[0], figure_position[1] - 1, field):
                    return MOVE_LEFT
                else:
                    return MOVE_DOWN

            # go right or up
            elif distance_x < 0 and distance_y > 0:
                if self.valid_move(figure, figure_position[0], figure_position[1] + 1, field):
                    return MOVE_RIGHT
                else:
                    return MOVE_UP

            # go right or down
            elif distance_x < 0 and distance_y < 0:
                if self.valid_move(figure, figure_position[0], figure_position[1] + 1, field):
                    return MOVE_RIGHT
                else:
                    return MOVE_DOWN

            else:
                print('fail')
                return MOVE_NONE

    def wolf_close(self, player_number, field):
        if player_number == 1:
            sheep_position = self.get_player_position(CELL_SHEEP_1, field)
            wolf_position = self.get_player_position(CELL_WOLF_2, field)
        else:
            sheep_position = self.get_player_position(CELL_SHEEP_2, field)
            wolf_position = self.get_player_position(CELL_WOLF_1, field)

        if (abs(sheep_position[0] - wolf_position[0]) <= 2 and abs(sheep_position[1] - wolf_position[1]) <= 2):
            # print('wolf is close')
            return True
        return False

    def valid_move(self, figure, x_new, y_new, field):
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

    def run_from_wolf(self, player_number, field):
        if player_number == 1:
            sheep_position = self.get_player_position(CELL_SHEEP_1, field)
            wolf_position = self.get_player_position(CELL_WOLF_2, field)
            sheep = CELL_SHEEP_1
        else:
            sheep_position = self.get_player_position(CELL_SHEEP_2, field)
            wolf_position = self.get_player_position(CELL_WOLF_1, field)
            sheep = CELL_SHEEP_2

        distance_x = sheep_position[1] - wolf_position[1]
        abs_distance_x = abs(sheep_position[1] - wolf_position[1])
        distance_y = sheep_position[0] - wolf_position[0]
        abs_distance_y = abs(sheep_position[0] - wolf_position[0])

        # print('player_number %i' %player_number)
        # print('running from wolf')
        # if the wolf is close vertically
        if abs_distance_y == 1 and distance_x == 0:
            # print('wolf is close vertically')
            # if it's above the sheep, move down if possible
            if distance_y > 0:
                if self.valid_move(sheep, sheep_position[0] + 1, sheep_position[1], field):
                    return MOVE_DOWN
            else:  # it's below the sheep, move up if possible
                if self.valid_move(sheep, sheep_position[0] - 1, sheep_position[1], field):
                    return MOVE_UP
                    # if this is not possible, flee to the right or left
            if self.valid_move(sheep, sheep_position[0], sheep_position[1] + 1, field):
                return MOVE_RIGHT
            elif self.valid_move(sheep, sheep_position[0], sheep_position[1] - 1, field):
                return MOVE_LEFT
            else:  # nowhere to go
                return MOVE_NONE

        # else if the wolf is close horizontally
        elif abs_distance_x == 1 and distance_y == 0:
            # print('wolf is close horizontally')
            # if it's to the left, move to the right if possible
            if distance_x > 0:
                if self.valid_move(sheep, sheep_position[0], sheep_position[1] - 1, field):
                    return MOVE_RIGHT
            else:  # it's to the right, move left if possible
                if self.valid_move(sheep, sheep_position[0], sheep_position[1] + 1, field):
                    return MOVE_RIGHT
            # if this is not possible, flee up or down
            if self.valid_move(sheep, sheep_position[0] - 1, sheep_position[1], field):
                return MOVE_UP
            elif self.valid_move(sheep, sheep_position[0] + 1, sheep_position[1], field):
                return MOVE_DOWN
            else:  # nowhere to go
                return MOVE_NONE

        elif abs_distance_x == 1 and abs_distance_y == 1:
            # print('wolf is in my surroundings')
            # wolf is left and up
            if distance_x > 0 and distance_y > 0:
                # move right or down
                if self.valid_move(sheep, sheep_position[0], sheep_position[1] + 1, field):
                    return MOVE_RIGHT
                else:
                    return MOVE_DOWN
            # wolf is left and down
            if distance_x > 0 and distance_y < 0:
                # move right or up
                if self.valid_move(sheep, sheep_position[0], sheep_position[1] + 1, field):
                    return MOVE_RIGHT
                else:
                    return MOVE_UP
            # wolf is right and up
            if distance_x < 0 and distance_y > 0:
                # move left or down
                if self.valid_move(sheep, sheep_position[0], sheep_position[1] - 1, field):
                    return MOVE_LEFT
                else:
                    return MOVE_DOWN
            # wolf is right and down
            if distance_x < 0 and distance_y < 0:
                # move left and up
                if self.valid_move(sheep, sheep_position[0], sheep_position[1] - 1, field):
                    return MOVE_LEFT
                else:
                    return MOVE_UP


        else:  # this method was wrongly called
            return MOVE_NONE




    def move_sheep(self, player_number, field, sheep_model):

        enemyPercentage = 0.9

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

        sheep_position = self.get_player_position(mySheep, field)
        wolf_position = self.get_player_position(myWolf, field)

        i_am_sheep = 1

        # MOVE NONE



        highest_score = self.super_score(field, field, player_number, 1) - 0.1

        highest_score -= self.super_score(field, field, opponent_number, 0) * enemyPercentage

        direction = MOVE_NONE



        # MOVE DOWN FIELD




        if self.valid_move(mySheep, sheep_position[0] + 1, sheep_position[1], field):
            sheep_position_new = [sheep_position[0] + 1, sheep_position[1]]
            sheep_position_old = [sheep_position[0], sheep_position[1]]
            new_field = copy.deepcopy(field)
            new_field[sheep_position_new[0]][sheep_position_new[1]] = mySheep
            new_field[sheep_position_old[0]][sheep_position_old[1]] = "."

            score_down = self.super_score(field, new_field, player_number, 1)
            score_down -= self.super_score(field, new_field, opponent_number, 0) * enemyPercentage
            if score_down > highest_score:
                highest_score = score_down
                direction = MOVE_DOWN


        # MOVE UP FIELD



        if self.valid_move(mySheep, sheep_position[0] - 1, sheep_position[1], field):
            sheep_position_new = [sheep_position[0] - 1, sheep_position[1]]
            sheep_position_old = [sheep_position[0], sheep_position[1]]
            new_field = copy.deepcopy(field)
            new_field[sheep_position_new[0]][sheep_position_new[1]] = mySheep
            new_field[sheep_position_old[0]][sheep_position_old[1]] = "."

            score_up = self.super_score(field, new_field, player_number, 1)
            score_up -= self.super_score(field, new_field, opponent_number, 0) * enemyPercentage
            if score_up > highest_score:
                highest_score = score_up
                direction = MOVE_UP


        # MOVE LEFT FIELD



        if self.valid_move(mySheep, sheep_position[0], sheep_position[1] - 1, field):
            sheep_position_new = [sheep_position[0], sheep_position[1] - 1]
            sheep_position_old = [sheep_position[0], sheep_position[1]]
            new_field = copy.deepcopy(field)
            new_field[sheep_position_new[0]][sheep_position_new[1]] = mySheep
            new_field[sheep_position_old[0]][sheep_position_old[1]] = "."

            score_left = self.super_score(field, new_field, player_number, 1)
            score_left -= self.super_score(field, new_field, opponent_number, 0) * enemyPercentage
            if score_left > highest_score:
                highest_score = score_left
                direction = MOVE_LEFT




        # MOVE RIGHT FIELD



        if self.valid_move(mySheep, sheep_position[0], sheep_position[1] + 1, field):
            sheep_position_new = [sheep_position[0], sheep_position[1] + 1]
            sheep_position_old = [sheep_position[0], sheep_position[1]]
            new_field = copy.deepcopy(field)
            new_field[sheep_position_new[0]][sheep_position_new[1]] = mySheep
            new_field[sheep_position_old[0]][sheep_position_old[1]] = "."

            score_right = self.super_score(field, new_field, player_number, 1)
            score_right -= self.super_score(field, new_field, opponent_number, 0) * enemyPercentage
            if score_right > highest_score:
                highest_score = score_right
                direction = MOVE_RIGHT

        return direction








    # my evaluation function

    def super_score(self, field, new_field, player_number, i_am_sheep):

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
                my_sheep_position = self.get_player_position(mySheep, new_field)
            except:
                my_sheep_position = self.get_player_position(mySheep_dead, new_field)

            my_wolf_position = self.get_player_position(myWolf, new_field)



            try:
                opponent_sheep_position = self.get_player_position(opponentSheep, field)
            except:
                opponent_sheep_position = self.get_player_position(opponentSheep_dead, field)

            opponent_wolf_position = self.get_player_position(opponentWolf, field)

        else:
            try:
                my_sheep_position = self.get_player_position(mySheep, field)
            except:
                my_sheep_position = self.get_player_position(mySheep_dead, field)

            my_wolf_position = self.get_player_position(myWolf, field)

            try:
                opponent_sheep_position = self.get_player_position(opponentSheep, new_field)

            except:
                opponent_sheep_position = self.get_player_position(opponentSheep_dead, new_field)

            opponent_wolf_position = self.get_player_position(opponentWolf, new_field)




        if my_sheep_position == opponent_wolf_position:
            return -300.0
        if my_wolf_position == opponent_sheep_position:
            return 300.0



        if self.valid_move(mySheep, my_sheep_position[0], my_sheep_position[1] - 1, new_field):
            if (my_sheep_position[0], my_sheep_position[1] - 1) == opponent_wolf_position:
                overall_score -= 30


        if self.valid_move(mySheep, my_sheep_position[0], my_sheep_position[1] + 1, new_field):
            if (my_sheep_position[0], my_sheep_position[1] + 1) == opponent_wolf_position:
                overall_score -= 30


        if self.valid_move(mySheep, my_sheep_position[0] - 1, my_sheep_position[1], new_field):
            if (my_sheep_position[0] - 1, my_sheep_position[1]) == opponent_wolf_position:
                overall_score -= 30


        if self.valid_move(mySheep, my_sheep_position[0] + 1, my_sheep_position[1], new_field):
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

        #        S H E E P !!!





        if my_sheep_coords_ohnegras:

            for current_pair in sheep_paths.items():

                if new_field[current_pair[0][0]][current_pair[0][1]] == CELL_GRASS:
                    value = 1.0
                elif new_field[current_pair[0][0]][current_pair[0][1]] == CELL_RHUBARB:
                    value = 5.0
                elif new_field[current_pair[0][0]][current_pair[0][1]] == opponentWolf:
                    value = -50
                else:
                    value = 0.0001


                path_length = len(current_pair[1])
                score = value / path_length

                overall_score += score





        else:




            for current_pair in sheep_paths_nofood.items():


                if new_field[current_pair[0][0]][current_pair[0][1]] == CELL_GRASS:
                    value = 1.0
                elif new_field[current_pair[0][0]][current_pair[0][1]] == CELL_RHUBARB:
                    value = 5.0
                elif new_field[current_pair[0][0]][current_pair[0][1]] == opponentWolf:
                    value = -20
                elif new_field[current_pair[0][0]][current_pair[0][1]] == opponentSheep:
                    value = 10
                else:
                    value = 0.0001



                path_length = len(current_pair[1])
                score = value / path_length


                overall_score += score
                middle_x = 0
                middle_y = 0
                middle_y = abs(15-my_sheep_position[0])
                middle_x = abs(19-my_sheep_position[1])
                overall_score = overall_score / ((middle_y)*1.5 + (middle_x)*1.9 + 1)




        #        W O L F !!!

        if i_am_sheep == 1:

            for current_pair in wolf_paths.items():



                if new_field[current_pair[0][0]][current_pair[0][1]] == opponentSheep:
                    value = 100.0
                else:
                    value = 0.001


                path_length = len(current_pair[1])

                score = value / path_length

                overall_score += score


        if i_am_sheep == 0 and not my_sheep_coords_ohnegras:

            for current_pair in wolf_paths.items():


                if new_field[current_pair[0][0]][current_pair[0][1]] == opponentSheep:
                    value = 50.0
                else:
                    value = 0.001


                path_length = len(current_pair[1])

                score = value / path_length

                overall_score += score



        return overall_score










    # defs for wolf
    def move_wolf(self, player_number, field, wolf_model):

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

        #sheep position is ACTUALLY THE    W O L F    POSITION !!!!

        sheep_position = self.get_player_position(myWolf, field)



        enemyPercentage = 0.9


        i_am_sheep = 0

        # MOVE NONE


        highest_score = self.super_score(field, field, player_number, 1) - 0.2
        highest_score -= self.super_score(field, field, opponent_number, 0) * enemyPercentage
        direction = MOVE_NONE

        # MOVE DOWN FIELD


        if self.valid_move(myWolf, sheep_position[0] + 1, sheep_position[1], field):

            sheep_position_new = [sheep_position[0] + 1, sheep_position[1]]
            sheep_position_old = [sheep_position[0], sheep_position[1]]


            new_field = copy.deepcopy(field)
            new_field[sheep_position_new[0]][sheep_position_new[1]] = myWolf
            new_field[sheep_position_old[0]][sheep_position_old[1]] = "."


            score_down = self.super_score(field, new_field, player_number, 1)
            score_down -= self.super_score(field, new_field, opponent_number, 0) * enemyPercentage
            if score_down > highest_score:
                highest_score = score_down
                direction = MOVE_DOWN


        # MOVE UP FIELD




        if self.valid_move(myWolf, sheep_position[0] - 1, sheep_position[1], field):
            sheep_position_new = [sheep_position[0] - 1, sheep_position[1]]
            sheep_position_old = [sheep_position[0], sheep_position[1]]


            new_field = copy.deepcopy(field)
            new_field[sheep_position_new[0]][sheep_position_new[1]] = myWolf
            new_field[sheep_position_old[0]][sheep_position_old[1]] = "."


            score_up = self.super_score(field, new_field, player_number, 1)
            score_up -= self.super_score(field, new_field, opponent_number, 0) * enemyPercentage
            if score_up > highest_score:
                highest_score = score_up
                direction = MOVE_UP


        # MOVE LEFT FIELD



        if self.valid_move(myWolf, sheep_position[0], sheep_position[1] - 1, field):
            sheep_position_new = [sheep_position[0], sheep_position[1] - 1]
            sheep_position_old = [sheep_position[0], sheep_position[1]]

            new_field = copy.deepcopy(field)
            new_field[sheep_position_new[0]][sheep_position_new[1]] = myWolf
            new_field[sheep_position_old[0]][sheep_position_old[1]] = "."

            score_left = self.super_score(field, new_field, player_number, 1)
            score_left -= self.super_score(field, new_field, opponent_number, 0) * enemyPercentage
            if score_left > highest_score:
                highest_score = score_left
                direction = MOVE_LEFT


        # MOVE RIGHT FIELD



        if self.valid_move(myWolf, sheep_position[0], sheep_position[1] + 1, field):
            sheep_position_new = [sheep_position[0], sheep_position[1] + 1]
            sheep_position_old = [sheep_position[0], sheep_position[1]]
            new_field = copy.deepcopy(field)
            new_field[sheep_position_new[0]][sheep_position_new[1]] = myWolf
            new_field[sheep_position_old[0]][sheep_position_old[1]] = "."

            score_right = self.super_score(field, new_field, player_number, 1)
            score_right -= self.super_score(field, new_field, opponent_number, 0) * enemyPercentage
            if score_right > highest_score:
                highest_score = score_right
                direction = MOVE_RIGHT

        return direction
