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

def get_class_name():
    return 'MyPlayer'

class MyPlayer():
    """Example class for a Kingsheep player"""

    def __init__(self):
        self.name = "My Player"
        self.uzh_shortname = "mplayer"

    def move_sheep(self, figure, field):
        
        #edit here incl. the return statement

        return MOVE_NONE


    def move_wolf(self, figure, field):
        
    	#edit here incl. the return statement

        return MOVE_NONE