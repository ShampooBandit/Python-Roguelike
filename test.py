from math import ceil

class WrapContent:
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

    def add_line(self, width, line='', fg=(255,255,255), bg=(0,0,0)):
        newlines = self.format(width, line)
        if newlines != []:
            for l in newlines:
                self.lines.append(l)
        return

    def format(self, width, line):
        result = []
        if width > 0:
            result = [line[x:min(x+width, len(line))] for x in range(0, ceil(len(line) / width) * width, width)]

        return result

content = WrapContent()
content.add_line(5, 'Hello world', [], [])
print(content.lines)