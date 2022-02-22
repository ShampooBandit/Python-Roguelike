import math

INIT_EXP = 10
EXP_MULTI = math.e

class Actor_Skill():
    def __init__(self):
        f = open('data_meleeskills.csv', 'r', 1024)

        self.melee_skills = []
        for line in f:
            self.melee_skills.append(line)

        f.close()
