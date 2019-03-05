"""
Kingsheep

A simple adverserial game based on the Java version https://github.com/uzh/PAI-Kingsheep.

Version: 0.1

Date: 2.1.2019

Authors:
    - Abraham Bernstein

License: (c) By University of Zurich, Dynamic and Distributed Systems Group ddis.ch
         All rights reserved

"""
import arcade
import os
import time


from kingsheep import kingsheep_iteration, \
    CELL_SHEEP_1, CELL_SHEEP_1_d, CELL_SHEEP_2, CELL_SHEEP_2_d, \
    CELL_WOLF_1, CELL_WOLF_2, \
    CELL_RHUBARB, CELL_GRASS, CELL_FENCE, CELL_EMPTY

SCREEN_WIDTH = 850
SCREEN_HEIGHT = 750
SPRITE_SCALING_PLAYER = 0.9

class KingsheepWindow(arcade.Window):
    """Graphical Interface for Kingsheep"""



    def __init__(self, width, height, name, iterations,
                 field_width, field_height, ks, player1, player2,reason):
        super().__init__(width, height, name)

        # Set the working directory (where we expect to find files) to the same
        # directory this .py file is in. You can leave this out of your own
        # code, but it is needed to easily run the examples using "python -m"
        # as mentioned at the top of this program.
        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)

        self.iteration = 0
        self.iterations = iterations
        self.ks = ks
        self.player1 = player1
        self.player2 = player2
        self.field_width = field_width
        self.field_height = field_height
        self.last_key = -1
        self.reason = reason

        self.sprites = None
        self.grass = []
        self.rhubarb = []
        self.fence = []

        arcade.start_render()
        arcade.set_background_color(arcade.color.LIGHT_GREEN)
        arcade.finish_render()

        # If you have sprite lists, you should create them here,
        # and set them to None

    def quit(self):
        arcade.close_window()

    def make_player(self, player, path):
        sprite =  arcade.Sprite(path, SPRITE_SCALING_PLAYER)
        sprite.center_x = 50
        sprite.center_y = 50
        return sprite

    def setup(self):
        # Create your sprites and sprite lists here

        self.sprites = {}
        self.sprites[CELL_SHEEP_1] = self.make_player(CELL_SHEEP_1, "resources/gfx/sheep1.png")
        self.sprites[CELL_SHEEP_2] = self.make_player(CELL_SHEEP_2, "resources/gfx/sheep2.png")
        self.sprites[CELL_WOLF_1] = self.make_player(CELL_WOLF_1, "resources/gfx/wolf1.png")
        self.sprites[CELL_WOLF_2] = self.make_player(CELL_WOLF_2, "resources/gfx/wolf2.png")


    def get_coordinates(self,x,y):
        screen_x = SCREEN_WIDTH/self.field_width * ( y + 0.5)
        screen_y = SCREEN_HEIGHT - SCREEN_HEIGHT/self.field_height * (x + 0.5)
        return screen_x, screen_y

    def set_coordinates(self, sprite, x, y):
        x_n, y_n = self.get_coordinates(x, y)
        sprite.center_x = x_n
        sprite.center_y = y_n

    def on_draw(self):
        """
        Render the screen.
        """

        # This command should happen before we start drawing. It will clear
        # the screen to the background color, and erase what we drew last frame.
        arcade.start_render()

        field = self.ks.get_field()

        new_grass = []
        new_fence = []
        new_rhubarb = []

        for x in range(len(field)):
            for y in range(len(field[x])):
                fig = field[x][y]
                if fig == CELL_EMPTY:
                    pass
                elif fig == CELL_GRASS:
                    if len(self.grass) == 0:
                        s =  self.make_player(CELL_GRASS, "resources/gfx/grass.png")
                    else:
                        s = self.grass.pop()
                    self.set_coordinates(s, x, y)
                    new_grass.append(s)

                elif fig == CELL_RHUBARB:
                    if len(self.rhubarb) == 0:
                        s =  self.make_player(CELL_RHUBARB, "resources/gfx/rhubarb.png")
                    else:
                        s = self.rhubarb.pop()
                    self.set_coordinates(s, x, y)
                    new_rhubarb.append(s)

                elif fig == CELL_FENCE:
                    if len(self.fence) == 0:
                        s =  self.make_player(CELL_FENCE, "resources/gfx/skigard.png")
                    else:
                        s = self.fence.pop()
                    self.set_coordinates(s, x, y)
                    new_fence.append(s)

                else:
                    if fig == CELL_SHEEP_1_d:
                        fig = CELL_SHEEP_1
                        print("Need to implement dead sheep")
                    if fig == CELL_SHEEP_2_d:
                        fig = CELL_SHEEP_2
                        print("Need to implement dead sheep")

                    self.set_coordinates(self.sprites[fig], x, y)


        self.grass = new_grass
        self.fence = new_fence
        self.rhubarb = new_rhubarb

        # Call draw() on all your sprite lists below
        [x.draw() for x in self.sprites.values()]
        [x.draw() for x in self.grass]
        [x.draw() for x in self.fence]
        [x.draw() for x in self.rhubarb]

        s = "Score:  " + self.ks.name1 + ": " + str(self.ks.score1) +  "  " + \
            self.ks.name2 + ": " + str(self.ks.score2)
        arcade.draw_text(s,10,10, arcade.color.BLACK, 12)

        time.sleep(slowdown)


    def update(self, delta_time):
        """
        All the logic to move, and the game logic goes here.
        Normally, you'll call update() on the sprite lists that
        need it.
        """
        self.iteration += 1

        game_over,reason = kingsheep_iteration(self.iteration, self.ks, self.player1, self.player2,self.reason)

        if debug:
            self.ks.print_ks()

        if self.iteration >= self.iterations or game_over or self.last_key == 113:
            time.sleep(2*slowdown)
            arcade.close_window()


    def on_key_press(self, key, key_modifiers):
        """
        Called whenever a key on the keyboard is pressed.

        For a full list of keys, see:
        http://arcade.academy/arcade.key.html
        """
        self.last_key = key

    def on_key_release(self, key, key_modifiers):
        """
        Called whenever the user lets off a previously pressed key.
        """
        pass

    def on_mouse_motion(self, x, y, delta_x, delta_y):
        """
        Called whenever the mouse moves.
        """
        pass

    def on_mouse_press(self, x, y, button, key_modifiers):
        """
        Called when the user presses a mouse button.
        """
        pass

    def on_mouse_release(self, x, y, button, key_modifiers):
        """
        Called when a user releases a mouse button.
        """
        pass


debug = False
verbosity = 5
slowdown = 0.0

def init(iterations, field_width, field_height, ks, player1, player2, debug_level, verbosity_level, slowdown_level):
    global debug
    global verbosity
    global slowdown
    debug = debug_level
    verbosity = verbosity_level
    slowdown = slowdown_level
    reason = ''

    game = KingsheepWindow(SCREEN_WIDTH, SCREEN_HEIGHT, "Kingsheep", iterations,
                           field_width, field_height, ks, player1, player2,reason)
    game.setup()

    # run game until someone closes it
    arcade.run()
