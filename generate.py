import random as rng
import numpy as np
import math
import time
import tcod
import tcod.path as tpath
import class_tile as tile
import class_map as cmap

def make_dungeon(width=50, height=50, room_density=25, overlap=False, con=None):
    rng.seed()

    dungeon = cmap.Map(width=width, height=height)

    dungeon_filled = 0.0
    dungeon_tiles = (width * height)
    filled_tiles = 0

    #How many times to attempt placing rooms or checking for collision
    collision_tolerance = 10
    room_tolerance = 50

    rooms = []

    i = 0
    r = 0
    
    while dungeon_filled <= room_density and i <= room_tolerance:
        room_width = rng.randint(5,10)
        room_height = rng.randint(5,10)

        room_xpos = rng.randint(2,width-room_width-2)
        room_ypos = rng.randint(2,height-room_height-2)

        #Loop until the room is not colliding with another room if overlap is not allowed
        x = 0
        while not overlap and check_collision(room_width, room_height, room_xpos, room_ypos, rooms) and x <= collision_tolerance:
            room_xpos = rng.randint(2,width-room_width-2)
            room_ypos = rng.randint(2,height-room_height-2)
            x += 1

        #If the room was found to not be colliding with another, place it inside the dungeon tile array
        if x <= collision_tolerance:
            for y in range(room_height):
                for x in range(room_width):
                    set_tile(dungeon, x+room_xpos, y+room_ypos, tile.Tile('.'), 1, 1)
                    if y == 0:
                        set_tile(dungeon, x+room_xpos, room_ypos, tile.Tile('#'), 0, 0)
                        set_tile(dungeon, x+room_xpos, room_ypos+room_height, tile.Tile('#'), 0, 0)
                    if x == 0:
                        set_tile(dungeon, room_xpos, y+room_ypos, tile.Tile('#'), 0, 0)
                        set_tile(dungeon, room_xpos+room_width, y+room_ypos, tile.Tile('#'), 0, 0)

            set_tile(dungeon, room_xpos+room_width, room_ypos+room_height, tile.Tile('#'), 0, 0)
            rooms.append((room_xpos, room_ypos, room_width, room_height))
            r += 1
            filled_tiles += (room_width * room_height)
            dungeon_filled = (filled_tiles / dungeon_tiles) * 100

        #Increment the room tolerance counter
        i += 1

    #Set the dungeon's list of rooms to the generated ones
    dungeon.rooms = rooms
    
    #Create a list of rooms connected by shortest distance
    dungeon.tree = make_tree(rooms)

    #Iterate through the list of nearby rooms and connect each one with a hallway
    for i in range(len(dungeon.tree)):
        x1 = int(rooms[dungeon.tree[i][0]][0] + (rooms[dungeon.tree[i][0]][2]/2))
        y1 = int(rooms[dungeon.tree[i][0]][1] + (rooms[dungeon.tree[i][0]][3]/2))
        x2 = int(rooms[dungeon.tree[i][1]][0] + (rooms[dungeon.tree[i][1]][2]/2))
        y2 = int(rooms[dungeon.tree[i][1]][1] + (rooms[dungeon.tree[i][1]][3]/2))
        for j in hallway(x1, y1, x2, y2):
            set_tile(dungeon, j[0], j[1], tile.Tile('.'), 1, 1)
            check_empty(dungeon, j[0], j[1], dungeon.tiles)

    #Generate the pathfinding map for the dungeon's layout
    dungeon.pathmap = tpath.AStar(dungeon.map, 1.0)
    
    return dungeon

def set_tile(dungeon, x, y, tile, walk, trans):
    dungeon.tiles[y][x] = tile
    dungeon.map.walkable[y][x] = walk
    dungeon.map.transparent[y][x] = trans
    return

#Check if any tiles around the current tile are empty, if so place a wall tile there
def check_empty(dungeon, x, y, tiles):
    if tiles[y+1][x+1].sprite == ' ': set_tile(dungeon, x+1, y+1, tile.Tile('#'), 0, 0)
    if tiles[y-1][x+1].sprite == ' ': set_tile(dungeon, x+1, y-1, tile.Tile('#'), 0, 0)
    if tiles[y+1][x-1].sprite == ' ': set_tile(dungeon, x-1, y+1, tile.Tile('#'), 0, 0)
    if tiles[y-1][x-1].sprite == ' ': set_tile(dungeon, x-1, y-1, tile.Tile('#'), 0, 0)
    if tiles[y+1][x].sprite == ' ': set_tile(dungeon, x, y+1, tile.Tile('#'), 0, 0)
    if tiles[y-1][x].sprite == ' ': set_tile(dungeon, x, y-1, tile.Tile('#'), 0, 0)
    if tiles[y][x+1].sprite == ' ': set_tile(dungeon, x+1, y, tile.Tile('#'), 0, 0)
    if tiles[y][x-1].sprite == ' ': set_tile(dungeon, x-1, y, tile.Tile('#'), 0, 0)
    return

#Loop through the tiles between the starting and ending points, and generate a list of (x,y) tuples matching the walkable tiles in a hallway connecting rooms
def hallway(x1, y1, x2, y2):
    pixelpos = []
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)

    if x1 <= x2:
        for x in range(x1, x2+1):
            pixelpos.append((x, y1))
        if y1 <= y2:
            for y in range(y1, y2+1):
                pixelpos.append((x2, y))
        else:
            for y in range(y2, y1+1):
                pixelpos.append((x2, y))
    else:
        for x in range(x2, x1+1):
            pixelpos.append((x, y2))
        if y1 <= y2:
            for y in range(y1, y2+1):
                pixelpos.append((x1, y))
        else:
            for y in range(y2, y1+1):
                pixelpos.append((x1, y))

    return pixelpos

#Generate a list from a given list of rooms, with (roomID 1, roomID 2, distance) tuples as elements
def make_tree(rooms):
    tree = {}
    if len(rooms) > 0:
        for i in range(len(rooms)-1):
            for j in range(i+1, len(rooms)):
                x1 = rooms[i][0]+(rooms[i][2]/2)
                y1 = rooms[i][1]+(rooms[i][3]/2)
                x2 = rooms[j][0]+(rooms[j][2]/2)
                y2 = rooms[j][1]+(rooms[j][3]/2)
                d = math.sqrt((x2-x1)**2 + (y2-y1)**2)
                try:
                    if tree[i][2] > d:
                        tree[i] = (i,j,d)
                except KeyError:
                    tree[i] = (i,j,d)
    return tree

#Check if the given dimensions collide with any existing rooms
def check_collision(w, h, x, y, rooms):
    if len(rooms) > 0:
        for i in range(len(rooms)):
            rx = rooms[i][0]
            ry = rooms[i][1]
            rw = rooms[i][2]
            rh = rooms[i][3]
            is_colliding = (
                ((rx <= x <= rx+rw or rx <= x+w <= rx+rw) and (ry <= y <= ry+rh or ry <= y+h <= ry+rh)) or
                ((x <= rx <= x+w or x <= rx+rw <= x+w) and (y <= ry <= y+h or y <= ry+rh <= y+h)) or
                (rx <= x+int(w/2) <= rx+rw and ry <= y+int(h/2) <= ry+rh)
                )
                
            if is_colliding:
                return is_colliding
        return is_colliding
    else:
        return False

#Connect all the floors in a given dungeon with up/down stairs
def connect_floors(dungeon):
    if len(dungeon) > 1:
        for i, floor in enumerate(dungeon):
            if i == 0:
                room = rng.randint(0, len(floor.rooms)-1)
                x = rng.randint(floor.rooms[room][0]+1, floor.rooms[room][0]+floor.rooms[room][2]-1)
                y = rng.randint(floor.rooms[room][1]+1, floor.rooms[room][1]+floor.rooms[room][3]-1)
                set_tile(dungeon[i], x, y, tile.Tile('>'), 1, 1)
                floor.stairs_down = (x,y)
            elif 1 <= i < len(dungeon)-1:
                room = rng.randint(0, len(floor.rooms)-1)
                x = rng.randint(floor.rooms[room][0]+1, floor.rooms[room][0]+floor.rooms[room][2]-1)
                y = rng.randint(floor.rooms[room][1]+1, floor.rooms[room][1]+floor.rooms[room][3]-1)
                set_tile(dungeon[i], x, y, tile.Tile('<'), 1, 1)
                floor.stairs_up = (x,y)
                room = rng.randint(0, len(floor.rooms)-1)
                downx = rng.randint(floor.rooms[room][0]+1, floor.rooms[room][0]+floor.rooms[room][2]-1)
                downy = rng.randint(floor.rooms[room][1]+1, floor.rooms[room][1]+floor.rooms[room][3]-1)
                while downx == x and downy == y:
                    room = rng.randint(0, len(floor.rooms)-1)
                    downx = rng.randint(floor.rooms[room][0]+1, floor.rooms[room][0]+floor.rooms[room][2]-1)
                    downy = rng.randint(floor.rooms[room][1]+1, floor.rooms[room][1]+floor.rooms[room][3]-1)
                set_tile(dungeon[i], downx, downy, tile.Tile('>'), 1, 1)
                floor.stairs_down = (downx,downy)
            else:
                room = rng.randint(0, len(floor.rooms)-1)
                x = rng.randint(floor.rooms[room][0]+1, floor.rooms[room][0]+floor.rooms[room][2]-1)
                y = rng.randint(floor.rooms[room][1]+1, floor.rooms[room][1]+floor.rooms[room][3]-1)
                set_tile(dungeon[i], x, y, tile.Tile('<'), 1, 1)
                floor.stairs_up = (x,y)

    return
