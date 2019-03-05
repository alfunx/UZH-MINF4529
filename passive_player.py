from config import *

def get_class_name():
    return 'PassivePlayer'

class PassivePlayer():
    """Passive Kingsheep player (doesn't move)"""

    def __init__(self):
        self.name = "Passive Player"
        self.uzh_shortname = "pplayer"

    def move_sheep(self, figure, field):
        return MOVE_NONE

    def move_wolf(self, figure, field):
        return MOVE_NONE