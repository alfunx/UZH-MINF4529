from config import *

def get_class_name():
    return 'KeyboardPlayer'

class KeyboardPlayer():
    """Keyboard Kingsheep player (doesn't move)"""

    def __init__(self):
        self.name = "Keyboard Player"
        self.uzh_shortname = "kplayer"

    def get_input(self, text):
        reply = input(text + "( u - up, h - left, k - down, l - right)")
        if reply[0] == 'u':
            return MOVE_UP
        elif reply[0] == 'h':
            return MOVE_LEFT
        elif reply[0] == 'l':
            return MOVE_RIGHT
        elif reply[0] == 'k':
            return MOVE_DOWN
        else:
            return MOVE_NONE

    def move_sheep(self):
        return self.get_input("Move Sheep")

    def move_wolf(self):
        return self.get_input("Move Wolf")