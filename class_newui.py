from pickle import FALSE
import traceback
from math import ceil
from copy import deepcopy
import textwrap as twrap

#Class that contains a dictionary of layers
class UI:
    def __init__(self, console=None):
        self.console = console
        self.layers = {}
        self.layerIndexCache = []

        self.state = 'NONE'

    #Iterate through the layers starting with 0 as the bottom layer
    #Higher indexes are drawn later, so 0 is the background and the Nth layer is the foreground
    def add_window(self, win, layerIndex):
        if(layerIndex in self.layers):
            self.layers[layerIndex].add_window(win)
        else:
            self.layers[layerIndex] = Layer([win])

        #This array keeps track of the order to render layers in
        #Layers are always drawn from 0 -> topmost layer
        self.layerIndexCache.append(layerIndex)
        self.layerIndexCache.sort()
        return

    #Loop through the layers from top to bottom, stopping on the first visible layer and handling input
    def handle_input(self, mousePos, mouseButton):
        for index in reversed(self.layerIndexCache):
            if self.layers[index].visible:
                self.layers[index].handle_input(mousePos, mouseButton)
                break

    #Call the render function for each window
    def render(self):
        for index in self.layerIndexCache:
            if self.layers[index].visible:
                self.layers[index].render(self.console)

#Class that contains a list of windows that exist together on a layer
class Layer:
    def __init__(self, windows=[], visible=True):
        self.windows = windows
        self.visible = visible

    def add_window(self, win):
        self.windows.append(win)
        return

    def handle_input(self, mousePos, mouseButton):
        for win in self.windows:
            win.handle_input(mousePos, mouseButton)
        return

    def render(self, con):
        for win in self.windows:
            if win.visible:
                win.render(con)
        return

#Class that contains an array of buttons, text, hoverables, or other things that are rendered inside of a box
class Window:
    def __init__(self, xpos=0, ypos=0, width=5, height=5, content=None, border=None, visible=True):
        self.xpos = xpos
        self.ypos = ypos
        self.width = width
        self.height = height
        self.innerWidth = width - 2
        self.innerHeight = height - 2
        if content == None:
            self.content = []
        else:
            self.content = content
        if border == None:
            self.border = Border(self.width, self.height)
        else:
            self.border = border
        self.visible = visible

        self.dirty = True
        self.buffer = []


    def add_content(self, item):
        self.content.append(item)
        self.dirty = True

    def render(self, con):
        if self.dirty:
            self.buffer = []
            #Clear the buffer with spaces
            for x in range(self.width):
                self.buffer.append([])
                for y in range(self.height):
                    self.buffer[x].append(('', (0,0,0), (0,0,0)))

            #Add current visible items to the buffer
            self.border.render(self.buffer)
            for item in self.content:
                if item.visible:
                    item.render(self.buffer)
            
            self.dirty = False
        
        #Loop through buffer and print characters
        for x,i in enumerate(self.buffer):
            for y,j in enumerate(i):
                con.print(self.xpos + x, self.ypos + y, j[0], j[1], j[2])

class Border:
    def __init__(self, width=5, height=5, pieces=[], fg=(255,255,255), bg=(0,0,0)):
        self.width = width
        self.height = height
        #Pieces is an array containing the characters that make up the border
        #[topleft, top, topright, 
        # left, middle, right, 
        # bottomleft, bottom, bottomright]
        if pieces == []:
            self.pieces = [
                chr(218), chr(196), chr(191),
                chr(179), chr(0), chr(179),
                chr(192), chr(196), chr(217)]
        else:
            self.pieces = pieces

        self.fg = fg
        self.bg = bg

    def render(self, buffer):
        #Draw top and bottom characters along the width of window
        for x in range(1, self.width - 1):
            #con.print(self.xpos+x, self.ypos, self.pieces[1], self.fg, self.bg)
            #con.print(self.xpos+x, self.ypos+self.height, self.pieces[7], self.fg, self.bg)
            buffer[x][0]            = (self.pieces[1], self.fg, self.bg)
            buffer[x][self.height - 1]  = (self.pieces[7], self.fg, self.bg)
        #Draw left and right characters along the height of the window
        for y in range(1, self.height - 1):
            #con.print(self.xpos, self.ypos+y, self.pieces[3], self.fg, self.bg)
            #con.print(self.xpos+self.width, self.ypos+y, self.pieces[5], self.fg, self.bg)
            buffer[0][y]          = (self.pieces[3], self.fg, self.bg)
            buffer[self.width - 1][y] = (self.pieces[5], self.fg, self.bg)
        #Draw the corner characters
        #con.print(self.xpos, self.ypos, self.pieces[0], self.fg, self.bg)
        #con.print(self.xpos+self.width, self.ypos, self.pieces[2], self.fg, self.bg)
        #con.print(self.xpos, self.ypos+self.height, self.pieces[6], self.fg, self.bg)
        #con.print(self.xpos+self.width, self.ypos+self.height, self.pieces[8], self.fg, self.bg)
        buffer[0][0]                            = (self.pieces[0], self.fg, self.bg)
        buffer[self.width - 1][0]               = (self.pieces[2], self.fg, self.bg)
        buffer[0][self.height - 1]              = (self.pieces[6], self.fg, self.bg)
        buffer[self.width - 1][self.height - 1] = (self.pieces[8], self.fg, self.bg)

#Class that holds each character with its foreground and background color
class Text:
    def __init__(self, xpos=0, ypos=0, string="", fgColors=[], bgColors=[], visible=True):
        self.xpos = xpos
        self.ypos = ypos
        self.chars = []
        self.visible = visible
        self.set_text(fgColors, bgColors, string)

    #Convert a string into a list of characters with their colors
    def set_text(self, fgColors, bgColors, string=""):
        if fgColors == []: fgColors = [(255,255,255)] * len(string)
        if bgColors == []: bgColors = [(0,0,0)] * len(string)
            
        for i,c in enumerate(string):
            self.chars.append(Character(c, fgColors[i], bgColors[i]))

    def render(self, buffer):
        for i,c in enumerate(self.chars):
            buffer[self.xpos + i][self.ypos] = (c.char,c.fg,c.bg)
            
#Class that holds a character with its color information
class Character:
    def __init__(self, char='', fg=(255,255,255), bg=(0,0,0)):
        self.char = char
        self.fg = fg
        self.bg = bg

#Add clickable buttons, hoverable text, scrollable windows