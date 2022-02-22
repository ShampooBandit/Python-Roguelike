import class_tile as tile
import tcod.map as tmap
import tcod.path as tpath
import numpy as np
import class_actor as act

class Map:
    def __init__(self, width=25, height=25):
        self.width = width
        self.height = height

        self.stairs_up = None
        self.stairs_down = None

        self.map = tmap.Map(width=width, height=height)

        value = np.empty((), dtype=object)
        value[()] = (False, None)
        self.occupied = np.full((height, width), value, dtype=object)

        self.pathmap = None

        self.tree = {}
        self.rooms = []

        self.tiles = [[tile.Tile() for x in range(self.width)] for y in range(self.height)]

    #Loop through the list of tiles at the camera offset and render those tiles into the console
    def render(self, con, camera):
        for x in range(0, camera.width):
            for y in range(0, camera.height):
                con.print(x, y, self.tiles[camera.ypos+y][camera.xpos+x].sprite, self.tiles[camera.ypos+y][x].fg, self.tiles[camera.ypos+y][x].bg)
        return

    #Same as render but takes the visible tiles to the player into account as well as their previously visited tiles
    def render_fov(self, memory, con, camera):
        for x in range(0, camera.width):
            for y in range(0, camera.height):
                if memory[camera.ypos+y][camera.xpos+x]: con.print(x, y, self.tiles[camera.ypos+y][camera.xpos+x].sprite, tuple(int(i/2) for i in self.tiles[camera.ypos+y][camera.xpos+x].fg), tuple(int(i/2) for i in self.tiles[camera.ypos+y][camera.xpos+x].bg))
                if self.map.fov[camera.ypos+y][camera.xpos+x]: con.print(x, y, self.tiles[camera.ypos+y][camera.xpos+x].sprite, self.tiles[camera.ypos+y][camera.xpos+x].fg, self.tiles[camera.ypos+y][camera.xpos+x].bg)
        return

    #Determine player's vision
    def calculate_fov(self, pov, r):
        self.map.compute_fov(pov[0], pov[1], r, True)
        return
