import traceback
from math import ceil
from copy import deepcopy
import textwrap as twrap

#Class that holds the text and color data for the window's innards
class Content:
    def __init__(self, lines=[], fg=[], bg=[]):
        self.lines = lines
        self.fg = fg
        self.bg = bg

        if len(fg) < len(lines):
            for i in range(len(fg), len(lines)):
                self.fg.append((255,255,255))
        if len(bg) < len(lines):
            for i in range(len(bg), len(lines)):
                self.bg.append((0,0,0))

    #Append a line of content with its foreground and background colors
    def add_line(self, line='', fg=(255,255,255), bg=(0,0,0)):
        self.lines.append(line)
        self.fg.append(fg)
        self.bg.append(bg)
        return

#Class for text that wraps onto new lines inside of window boundaries
class WrapContent(Content):
    def add_line(self, width, line='', fg=(255,255,255), bg=(0,0,0)):
        newlines = twrap.wrap(line, width)
        if newlines != []:
            self.lines += newlines
        for i in range(len(newlines)):
            self.fg.append(fg)
            self.bg.append(bg)
        return


#Create a hoverable piece of text
class Hoverable:
    def __init__(self, text='Test', info='N/A', xpos=0, ypos=0, fg=(255,255,255), bg=(0,0,0), h_fg=(255,255,255), h_bg=(0,0,127)):
        self.text = text
        self.info = info
        self.xpos = xpos
        self.ypos = ypos
        self.fg = fg
        self.bg = bg
        self.h_fg = h_fg
        self.h_bg = h_bg

    def highlight(self, mouse_pos):
        if self.xpos <= mouse_pos[0] < max(self.xpos+1, self.xpos+len(self.text)):
            if self.ypos == mouse_pos[1]:
                return True
        return False

    def render(self, con, mouse_pos):
        if self.highlight(mouse_pos):
            con.print(self.xpos, self.ypos, self.text, self.h_fg, self.h_bg)
            con.print(self.xpos, self.ypos+1, chr(218)+(chr(196)*20)+chr(191), self.fg, self.bg)
            lines = twrap.wrap(self.info, 20)
            i = 0
            for i, line in enumerate(lines):
                con.print(self.xpos, self.ypos+2+i, chr(179)+f'{line:<20}'+chr(179), self.fg, self.bg)
            con.print(self.xpos, self.ypos+3+i, chr(192)+(chr(196)*20)+chr(217), self.fg, self.bg)
        else:
            con.print(self.xpos, self.ypos, self.text, self.fg, self.bg)
        return

#Class that defines a clickable piece of text
class Clickable:
    def __init__(self, text='Test', xpos=0, ypos=0, fg=(255,255,255), bg=(0,0,0), h_fg=(255,255,255), h_bg=(0,0,127), value=0, border=1):
        self.text = text
        self.xpos = xpos
        self.ypos = ypos
        self.fg = fg
        self.bg = bg
        self.h_fg = h_fg
        self.h_bg = h_bg
        self.value = value
        self.clicked = 0
        self.border = border
        self.args = ()

    def function(self, win):
        win.choice = self.value
        self.clicked = 1
        return

    def highlight(self, mouse_pos):
        if self.xpos+1 <= mouse_pos[0] <= self.xpos+len(self.text):
            if self.ypos+1 == mouse_pos[1]:
                return True
        return False

    def click(self, mouse_pos, mousebutton):
        if self.highlight(mouse_pos) and mousebutton == 1:
            return True
        return False

    def render(self, con, mouse_pos):
        if self.border:
            if self.clicked:
                con.print(self.xpos, self.ypos, chr(218), self.fg, self.bg)
                con.print(self.xpos+1, self.ypos, chr(196)*len(self.text), self.fg, self.bg)
                con.print(self.xpos+len(self.text)+1, self.ypos, chr(191), self.fg, self.bg)
                con.print(self.xpos, self.ypos+1, chr(179), self.fg, self.bg)
                con.print(self.xpos+len(self.text)+1, self.ypos+1, chr(179), self.fg, self.bg)
                con.print(self.xpos, self.ypos+2, chr(217)+' '*len(self.text), self.fg, self.bg)
                con.print(self.xpos+len(self.text)+1, self.ypos+2, chr(192), self.fg, self.bg)
            else:
                con.print(self.xpos, self.ypos, chr(218), self.fg, self.bg)
                con.print(self.xpos+1, self.ypos, chr(196)*len(self.text), self.fg, self.bg)
                con.print(self.xpos+len(self.text)+1, self.ypos, chr(191), self.fg, self.bg)
                con.print(self.xpos, self.ypos+1, chr(179), self.fg, self.bg)
                con.print(self.xpos+len(self.text)+1, self.ypos+1, chr(179), self.fg, self.bg)
        if self.highlight(mouse_pos): con.print(self.xpos+1, self.ypos+1, self.text, self.h_fg, self.h_bg)
        else: con.print(self.xpos+1, self.ypos+1, self.text, self.fg, self.bg)
        return
                

#Class that defines the window and its borders
class Window:
    def __init__(self, xpos=0, ypos=0, width=5, height=5, content=None, border=[], border_fg=(255,255,255), border_bg=(0,0,0), choice=0, visible=1):
        self.xpos = xpos
        self.ypos = ypos
        self.width = width
        self.height = height
        self.border_fg = border_fg
        self.border_bg = border_bg

        if border == []:
            self.border = [
                chr(218), chr(196), chr(191),
                chr(179), chr(0), chr(179),
                chr(192), chr(196), chr(217),
                chr(195), chr(194), chr(180), chr(193),
                ]
        else:
            self.border = border

        self.content_layers = []
        self.content_layers.append(content)

        self.hoverables = [[]]
        self.clickables = []
        
        self.cursor_pos = 0
        self.choice = choice
        self.visible = visible

    def handle_input(self, mouse_pos, mousebutton):
        if len(self.clickables) > 0:
            for c in self.clickables:
                if c.click(mouse_pos, mousebutton):
                    try:
                        c.function(*c.args)
                    except Exception:
                        traceback.print_exc()
                        c.function(c.args)
                    break
            for c in self.clickables:
                if self.choice != c.value:
                    c.clicked = 0
        return

    #Loop through the window size and draw the border pieces, before looping through the lines of content and drawing out the text
    def render(self, con, mouse_pos):
        if self.visible:
            #Loop through the size of the window and draw border characters
            for x in range(self.width):
                con.print(self.xpos+x, self.ypos, self.border[1], self.border_fg, self.border_bg)
                con.print(self.xpos+x, self.ypos+self.height, self.border[7], self.border_fg, self.border_bg)
                for y in range(self.height):
                    if x == 0:
                        con.print(self.xpos+1, self.ypos+1+y, ' '*(self.width-1), self.border_fg, self.border_bg)
                        con.print(self.xpos, self.ypos+y, self.border[3], self.border_fg, self.border_bg)
                        con.print(self.xpos+self.width, self.ypos+y, self.border[5], self.border_fg, self.border_bg)
            con.print(self.xpos, self.ypos, self.border[0], self.border_fg, self.border_bg)
            con.print(self.xpos+self.width, self.ypos, self.border[2], self.border_fg, self.border_bg)
            con.print(self.xpos, self.ypos+self.height, self.border[6], self.border_fg, self.border_bg)
            con.print(self.xpos+self.width, self.ypos+self.height, self.border[8], self.border_fg, self.border_bg)
            
            #Loop through the clickable text and render those
            for c in self.clickables:
                c.render(con, mouse_pos)

            #Loop through the lines of content in the selected choice and render each line
            for i, line in enumerate(self.content_layers[self.choice].lines):
                if len(line) > 0:
                    if line[0] == '─': con.print(self.xpos, self.ypos+1+i, self.border[9], self.border_fg, self.border_bg)
                    elif line[0] == '═': con.print(self.xpos, self.ypos+1+i, self.border[9], self.border_fg, self.border_bg)
                    if line[-1] == '─': con.print(self.xpos+self.width, self.ypos+1+i, self.border[11], self.border_fg, self.border_bg)
                    elif line[-1] == '═': con.print(self.xpos+self.width, self.ypos+1+i, self.border[11], self.border_fg, self.border_bg)
            
                try:
                    con.print(self.xpos+1, self.ypos+1+i, line, self.content_layers[self.choice].fg[i], self.content_layers[self.choice].bg[i])
                except Exception:
                    traceback.print_exc()
            
            try:
                for h in reversed(self.hoverables[self.choice]):
                    h.render(con, mouse_pos)
            except:
                pass
        return

class ScrollableWindow(Window):
    def __init__(self, xpos=0, ypos=0, width=5, height=5, content=None, border=[], border_fg=(255,255,255), border_bg=(0,0,0), choice=0, visible=1):
        c = content
        super().__init__(xpos, ypos, width, height, content, border, border_fg, border_bg, choice, visible)

        self.yscroll = 0
        self.full_content = deepcopy(content)
        self.update()

    def add_line(self, line):
        self.full_content.add_line(self.width, line)
        self.update()

    def update(self):
        slice_from = len(self.full_content.lines) - self.yscroll
        slice_to = max(0, slice_from - self.height + 1)
        self.content_layers[self.choice].lines = self.full_content.lines[slice_to:slice_from]
        self.content_layers[self.choice].fg = self.full_content.fg[slice_to:slice_from]
        self.content_layers[self.choice].bg = self.full_content.bg[slice_to:slice_from]

#Class that contains a 2d list of layers, each inner list containing the windows
class UI:
    def __init__(self, console=None):
        self.console = console
        self.layers = [[] for i in range(1)]

        self.state = 'NONE'

    #Iterate through the layers starting with 0 as the bottom layer
    #Higher indexes are drawn later, so 0 is the background and the Nth layer is the foreground
    def add_window(self, win, layer):
        try:
            self.layers[layer].append(win)
        except:
            for i in range(len(self.layers), layer+1):
                self.layers.append([])
            self.layers[layer].append(win)
        return

    def handle_input(self, mouse_pos, mousebutton):
        for win in reversed(self.layers[-1]):
            if win.visible == 1:
                win.handle_input(mouse_pos, mousebutton)
                break

    #Call the render function for each window
    def render(self, mouse_pos):
        for layer in self.layers:
            for win in layer:
                win.render(self.console, mouse_pos)
