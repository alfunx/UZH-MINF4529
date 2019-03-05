from config import *

def get_class_name():
    return 'GreedyPlayer'

class GreedyPlayer():
    """Greedy Kingsheep player. Sheep flee from the wolf or go to the nearest food 
    in a straight line, wolves go to sheep in a straight line."""

    def __init__(self):
        self.name = "Greedy Player"
        self.uzh_shortname = "gplayer"

    def get_player_position(self,figure,field):
        x = [x for x in field if figure in x][0]
        return (field.index(x), x.index(figure))

    #defs for sheep
    def food_present(self,field):
        food_present = False

        for line in field: 
            for item in line:
                if item == CELL_RHUBARB or item == CELL_GRASS:
                    food_present = True
                    break
        return food_present

    def closest_goal(self,player_number,field):
        possible_goals = []
        
        if player_number == 1:
            sheep_position = self.get_player_position(CELL_SHEEP_1,field)
        else:
            sheep_position = self.get_player_position(CELL_SHEEP_2,field)

        #make list of possible goals

        y_position = 0
        for line in field:
            x_position = 0
            for item in line:
                if item == CELL_RHUBARB or item == CELL_GRASS:
                    possible_goals.append((y_position,x_position))
                x_position += 1
            y_position += 1

        #determine closest item and return
        distance = 1000
        for possible_goal in possible_goals:
            if (abs(possible_goal[0]-sheep_position[0])+abs(possible_goal[1]-sheep_position[1])) < distance:
                distance = abs(possible_goal[0]-sheep_position[0])+abs(possible_goal[1]-sheep_position[1])
                final_goal = (possible_goal)
                
        return final_goal

    def gather_closest_goal(self,closest_goal,field,figure):
        figure_position = self.get_player_position(figure,field)

        distance_x = figure_position[1]-closest_goal[1]
        distance_y = figure_position[0]-closest_goal[0]
        
        if distance_x == 0:
            #print('item right above/below me')
            if distance_y > 0:
                if self.valid_move(figure, figure_position[0]-1,figure_position[1],field):
                    return MOVE_UP
                else:
                    return MOVE_RIGHT
            else:
                if self.valid_move(figure, figure_position[0]+1,figure_position[1],field):
                    return MOVE_DOWN
                else:
                    return MOVE_RIGHT
        elif distance_y == 0:
            #print('item right beside me')
            if distance_x > 0:
                if self.valid_move(figure, figure_position[0],figure_position[1]-1,field):
                    
                    return MOVE_LEFT
                else:
                    return MOVE_UP
            else:
                if self.valid_move(figure, figure_position[0],figure_position[1]+1,field):
                    return MOVE_RIGHT
                else:
                    return MOVE_UP
        
        else:
            #go left or up
            if distance_x > 0 and distance_y > 0:
                if self.valid_move(figure, figure_position[0],figure_position[1]-1,field):
                    return MOVE_LEFT
                else:
                    return MOVE_UP

            #go left or down
            elif distance_x > 0 and distance_y < 0:
                if self.valid_move(figure, figure_position[0],figure_position[1]-1,field):
                    return MOVE_LEFT
                else:
                    return MOVE_DOWN

            #go right or up
            elif distance_x < 0 and distance_y > 0:
                if self.valid_move(figure,figure_position[0],figure_position[1]+1,field):
                    return MOVE_RIGHT
                else:
                    return MOVE_UP

            #go right or down
            elif distance_x < 0 and distance_y < 0:
                if self.valid_move(figure,figure_position[0],figure_position[1]+1,field):
                    return MOVE_RIGHT
                else:
                    return MOVE_DOWN

            else:
                print('fail')
                return MOVE_NONE

    def wolf_close(self,player_number,field):
        if player_number == 1:
            sheep_position = self.get_player_position(CELL_SHEEP_1,field)
            wolf_position = self.get_player_position(CELL_WOLF_2,field)
        else:
            sheep_position = self.get_player_position(CELL_SHEEP_2,field)
            wolf_position = self.get_player_position(CELL_WOLF_1,field)

        if (abs(sheep_position[0]-wolf_position[0]) <= 2 and abs(sheep_position[1]-wolf_position[1]) <= 2):
            #print('wolf is close')
            return True
        return False

    def valid_move(self, figure, x_new, y_new, field):
         # Neither the sheep nor the wolf, can step on a square outside the map. Imagine the map is surrounded by fences.
        if x_new > FIELD_HEIGHT - 1:
            return False
        elif x_new < 0:
            return False
        elif y_new > FIELD_WIDTH -1:
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

    def run_from_wolf(self,player_number,field):
        if player_number == 1:
            sheep_position = self.get_player_position(CELL_SHEEP_1,field)
            wolf_position = self.get_player_position(CELL_WOLF_2,field)
            sheep = CELL_SHEEP_1
        else:
            sheep_position = self.get_player_position(CELL_SHEEP_2,field)
            wolf_position = self.get_player_position(CELL_WOLF_1,field)
            sheep = CELL_SHEEP_2

        distance_x = sheep_position[1] - wolf_position[1]
        abs_distance_x = abs(sheep_position[1] - wolf_position[1])
        distance_y = sheep_position[0] - wolf_position[0]
        abs_distance_y = abs(sheep_position[0] - wolf_position[0])

        #print('player_number %i' %player_number)
        #print('running from wolf')
        #if the wolf is close vertically
        if abs_distance_y == 1 and distance_x == 0:
            #print('wolf is close vertically')
            #if it's above the sheep, move down if possible
            if distance_y > 0:
                if self.valid_move(sheep,sheep_position[0]+1,sheep_position[1], field):
                    return MOVE_DOWN
            else: #it's below the sheep, move up if possible
                if self.valid_move(sheep,sheep_position[0]-1,sheep_position[1], field):
                    return MOVE_UP            
            # if this is not possible, flee to the right or left
            if self.valid_move(sheep,sheep_position[0],sheep_position[1]+1, field):
                return MOVE_RIGHT
            elif self.valid_move(sheep,sheep_position[0],sheep_position[1]-1, field):
                return MOVE_LEFT
            else: #nowhere to go
                return MOVE_NONE

        #else if the wolf is close horizontally
        elif abs_distance_x == 1 and distance_y == 0:
            #print('wolf is close horizontally')
            #if it's to the left, move to the right if possible
            if distance_x > 0:
                if self.valid_move(sheep,sheep_position[0],sheep_position[1]-1, field):
                    return MOVE_RIGHT
            else: #it's to the right, move left if possible
                if self.valid_move(sheep,sheep_position[0],sheep_position[1]+1, field):
                    return MOVE_RIGHT
            #if this is not possible, flee up or down
            if self.valid_move(sheep,sheep_position[0]-1,sheep_position[1], field):
                return MOVE_UP
            elif self.valid_move(sheep,sheep_position[0]+1,sheep_position[1], field):
                return MOVE_DOWN
            else: #nowhere to go
                return MOVE_NONE

        elif abs_distance_x == 1 and abs_distance_y == 1:
            #print('wolf is in my surroundings')
            #wolf is left and up
            if distance_x > 0 and distance_y > 0:
                #move right or down
                if self.valid_move(sheep,sheep_position[0],sheep_position[1]+1, field):
                    return MOVE_RIGHT
                else:
                    return MOVE_DOWN
            #wolf is left and down
            if distance_x > 0 and distance_y < 0:
                #move right or up
                if self.valid_move(sheep,sheep_position[0],sheep_position[1]+1, field):
                    return MOVE_RIGHT
                else:
                    return MOVE_UP
            #wolf is right and up
            if distance_x < 0 and distance_y > 0:
                #move left or down
                if self.valid_move(sheep,sheep_position[0],sheep_position[1]-1, field):
                    return MOVE_LEFT
                else:
                    return MOVE_DOWN
            #wolf is right and down
            if distance_x < 0 and distance_y < 0:
                #move left and up
                if self.valid_move(sheep,sheep_position[0],sheep_position[1]-1, field):
                    return MOVE_LEFT
                else:
                    return MOVE_UP


        else: #this method was wrongly called
            return MOVE_NONE

    def move_sheep(self,player_number,field):
        if player_number == 1:
            figure = CELL_SHEEP_1
        else:
            figure = CELL_SHEEP_2

        if self.wolf_close(player_number,field):
            #print('wolf close move')
            return self.run_from_wolf(player_number,field)
        elif self.food_present(field):
            #print('gather food move')
            return self.gather_closest_goal(self.closest_goal(player_number,field),field,figure)
        else:
            return MOVE_NONE

    #defs for wolf
    def move_wolf(self,player_number,field):
        if player_number == 1:
            sheep_position = self.get_player_position(CELL_SHEEP_2,field)
            return self.gather_closest_goal(sheep_position,field,CELL_WOLF_1)
        else:
            sheep_position = self.get_player_position(CELL_SHEEP_1,field)
            return self.gather_closest_goal(sheep_position,field,CELL_WOLF_2)