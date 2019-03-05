import random
from config import *

def get_class_name():
    return 'RandomPlayer'

class RandomPlayer():
    """Dummy class for a random Kingsheep player"""

    def __init__(self):
        self.name = "Random Player"
        self.uzh_shortname = "pplayer"

    def move_sheep(self, figure, field):
        return random.randint(0, 4) - 2


    def move_wolf(self, figure, field):
        return random.randint(0, 4) - 2