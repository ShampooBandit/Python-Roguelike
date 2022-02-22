import class_race as race
import class_skill as skill
import random as rng
import numpy as np
import math
import tcod.path as tpath
import time
import lookups as l

def get_time():
    return int(round(time.time() * 1000))

class Actor:
    def __init__(self, name='', sprite='@', xpos=0, ypos=0, bg=(0,0,0), fg=(255,255,255), race=None, floor=0, level=1):
        if name == '':
            self.name = race[1]
        else:
            self.name = name
        self.sprite = sprite
        self.bg = bg
        self.fg = fg
        self.xpos = xpos
        self.ypos = ypos
        self.race = race
        self.floor = floor
        self.stats = [
            int(race[2]), #HP
            int(race[2]), #MAXHP
            int(race[3]), #SP
            int(race[3]), #MAXSP
            int(race[4]), #STR
            int(race[5]), #DEX
            int(race[6]), #CON
            int(race[7]), #INT
            int(race[8]), #WIL
            int(race[9]), #SPI
            int(race[10]), #PER
            int(race[11]), #LUK
            ]
        self.description = race[12]

        self.level = level
        self.exp = 0

        self.melee_skills = []
        self.range_skills = []
        self.magic_skills = []
        self.defence_skills = []
        self.utility_skills = []

        self.init_skills()

        self.memory = []

        self.fov = []
        self.vision = int(self.stats[10]*1.5)

        self.alert = 0
        self.goal = None
        self.path = []
        self.step = 0
        self.direction = 0
        self.sight = []
        self.target = None

        self.room = 0

    def init_skills(self):
        skills = skill.Actor_Skill()
        skill_list = self.race[15].split('/')
        for s in skill_list:
            skill_data = s.split('-')
            if skill_data[0] == 'me':
                self.melee_skills.append(skills.melee_skills[int(skill_data[1])].split(','))

    def get_skill_next(self, skill_type, skill_num):
        if skill_type == 'me':
            return skill.INIT_EXP*int((1 - skill.EXP_MULTI**(self.get_skill_level(skill_type, skill_num)+1))/(1 - skill.EXP_MULTI))
        else:
            return 0

    def get_skill_level(self, skill_type, skill_num):
        if skill_type == 'me':
            return int((1/math.log(skill.EXP_MULTI)) * math.log((skill.INIT_EXP + (skill.EXP_MULTI - 1) * int(self.melee_skills[skill_num][2]))/skill.INIT_EXP))
        else:
            return 0

    def sigmoid(self, x, σ, λ):
        x = x**λ
        σ = σ**λ
        
        return (x / (x + σ))

    def direction_switcher(self, arg):
        switcher = {}
        switcher[(0,0)] = self.direction
        switcher[(1,0)] = 0     #right
        switcher[(1,1)] = 45    #up right
        switcher[(0,1)] = 90    #up
        switcher[(-1,1)] = 135  #up left
        switcher[(-1,0)] = 180  #left
        switcher[(-1,-1)] = 225 #down left
        switcher[(0,-1)] = 270  #down
        switcher[(1,-1)] = 315  #down right

        func = switcher.get(arg, lambda: 0)
        return func

    def render(self, con, camera):
        con.print(self.xpos-(camera.xpos), self.ypos-(camera.ypos), self.sprite, (self.fg[0], self.fg[1]-int(self.alert*2.55), self.fg[2]-int(self.alert*2.55)), self.bg)
        return

    #Math calculation functions
    def calc_distance(self, x1, y1, x2, y2):
        return math.sqrt((abs(x2-x1))**2 + (abs(y2-y1))**2)

    def is_clockwise(self, p1, p2):
        return (-p1[0]*p2[1] + p1[1]*p2[0]) > 0

    def is_within_radius(self, p, r):
        return p[0]*p[0] + p[1]*p[1] <= r

    def is_inside_sector(self, point, center, sector_start, sector_end, radius):
        rel_point = (point[0]-center[0], point[1]-center[1])

        a = self.is_clockwise(sector_start, rel_point)
        b = self.is_clockwise(sector_end, rel_point)
        c = self.is_within_radius(rel_point, radius)
        return not a and b and c

    #Main AI to handle what the actor does at various alert levels
    def alert_ai(self, dungeon, actors):
        self.alert = min(100, self.alert)
        self.alert = max(0, self.alert)
        if self.alert <= 15: #Nothing noticed
            self.wander(dungeon, actors)
        elif 16 <= self.alert <= 40: #Low suspicion
            pass
        elif 41 <= self.alert <= 70: #Medium suspicion
            pass
        elif 71 <= self.alert <= 99: #High suspicion
            pass
        elif self.alert == 100: #Found the player
            return self.persue_target(dungeon, actors)
        return ""

    #Check if the position coordinates given contain another actor already
    def is_tile_occupied(self, dungeon, position):
        return dungeon.occupied[position[1]][position[0]]

    #Check if actor argument is the target, if so do combat
    def melee_combat(self, actor):
        hit_chance = 50 + self.stats[5] - int(actor.stats[5]/2) - int(actor.stats[11]/2)
        damage = max(self.stats[4] - int(actor.stats[6]/2), 0)
            
        if rng.randint(1,100) <= hit_chance:
            actor.stats[0] -= damage
            if actor.death_check():
                reward = int((self.sigmoid(math.e, 1, (actor.level / self.level) - 1) * 2) * (actor.level * 100))
                print("Exp: ", reward)
                self.exp += reward
            word = "hitpoint" if damage == 1 else "hitpoints"
            line = f'{self.name} hit the {actor.name} for {damage} {word}!'
            return line
        else:
            return f'{self.name} missed the {actor.name}.'

    #Check if ur ded lol
    def death_check(self):
        if self.stats[0] <= 0:
            return True
        return False
        
    #Actively move towards the target and seek out its current position
    def persue_target(self, dungeon, actors):
        if self.goal != (self.target.xpos, self.target.ypos):
            self.goal = (self.target.xpos, self.target.ypos)
            self.step = 0
            self.path = dungeon.pathmap.get_path(self.xpos, self.ypos, self.goal[0], self.goal[1])
        return self.take_step(dungeon, actors)

    #Take a step along the current path if possible
    def take_step(self, dungeon, actors):
        if self.step < len(self.path):
            diff = (self.path[self.step][0]-self.xpos, self.path[self.step][1]-self.ypos)

            self.direction = self.direction_switcher(diff)

            self.get_vision_cone(actors)

            act = self.is_tile_occupied(dungeon, self.path[self.step])

            if not act[0]:
                dungeon.occupied[self.ypos][self.xpos] = (False, None)
                self.xpos = self.path[self.step][0]
                self.ypos = self.path[self.step][1]
                dungeon.occupied[self.ypos][self.xpos] = (True, self)
                self.step += 1
            elif act[1] == self.target:
                return self.melee_combat(act[1])
            else:
                self.room = rng.randint(0,len(dungeon.rooms)-1)
                roomx = rng.randint(dungeon.rooms[self.room][0]+1,dungeon.rooms[self.room][2]+dungeon.rooms[self.room][0]-1)
                roomy = rng.randint(dungeon.rooms[self.room][1]+1,dungeon.rooms[self.room][3]+dungeon.rooms[self.room][1]-1)
            
                self.goal = (roomx, roomy)
                self.step = 0
                self.path = dungeon.pathmap.get_path(self.xpos, self.ypos, roomx, roomy)
        return ""

    #Aimlessly wander around the map
    def wander(self, dungeon, actors):
        if self.goal == None or (self.xpos == self.goal[0] and self.ypos == self.goal[1]) or self.path == []:
            action = rng.randint(0,1000)

            if action <= 980:
                self.get_vision_cone(actors)
                pass
            elif 981 <= action <= 990:
                self.direction = rng.randint(0, 359)
                self.get_vision_cone(actors)
                pass
            elif 991 <= action <= 995:
                roomx = rng.randint(dungeon.rooms[self.room][0]+1,dungeon.rooms[self.room][2]+dungeon.rooms[self.room][0]-1)
                roomy = rng.randint(dungeon.rooms[self.room][1]+1,dungeon.rooms[self.room][3]+dungeon.rooms[self.room][1]-1)
            
                self.goal = (roomx, roomy)
                self.step = 0
                self.path = dungeon.pathmap.get_path(self.xpos, self.ypos, roomx, roomy)
            elif 996 <= action <= 1000:
                self.room = rng.randint(0,len(dungeon.rooms)-1)
                roomx = rng.randint(dungeon.rooms[self.room][0]+1,dungeon.rooms[self.room][2]+dungeon.rooms[self.room][0]-1)
                roomy = rng.randint(dungeon.rooms[self.room][1]+1,dungeon.rooms[self.room][3]+dungeon.rooms[self.room][1]-1)
            
                self.goal = (roomx, roomy)
                self.step = 0
                self.path = dungeon.pathmap.get_path(self.xpos, self.ypos, roomx, roomy)
        else:
            self.take_step(dungeon, actors)
            pass
        return

    #Determine what units are visible to the actor
    def get_vision_cone(self, actors):
        self.sight = []
        x1 = int(l.cosine[(self.direction+30) % 360] * self.vision)
        y1 = int(l.sine[(self.direction+30) % 360] * self.vision)
        x2 = int(l.cosine[(self.direction-30) % 360] * self.vision)
        y2 = int(l.sine[(self.direction-30) % 360] * self.vision)

        for a in actors:
            if a != self:
                if self.is_inside_sector((a.xpos, a.ypos), (self.xpos, self.ypos), (x2, y2), (x1, y1), self.vision*self.vision):
                    self.sight.append(a)
        return

    #Check for an actor within sight tiles
    def check_sight(self, actor):
        insight = False
        if actor in self.sight and self.fov[actor.ypos][actor.xpos]: insight = True
        return insight
