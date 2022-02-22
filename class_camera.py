import tcod

class Camera:
    def __init__(self, width=60, height=50):
        self.width = width
        self.height = height
        self.xpos = 0
        self.ypos = 0

    def center_on_actor(self, actor, dungeon_size):
        self.xpos = actor.xpos - int(self.width/2)
        self.ypos = actor.ypos - int(self.height/2)

        if self.xpos < 0: self.xpos = 0
        elif self.xpos+self.width > dungeon_size[0]: self.xpos = dungeon_size[0]-self.width
        if self.ypos < 0: self.ypos = 0
        elif self.ypos+self.height > dungeon_size[1]: self.ypos = dungeon_size[1]-self.height
