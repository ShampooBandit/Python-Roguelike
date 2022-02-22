import random as rng

class Actor_Race():
    def __init__(self):
        #Open the file of race data and load them into a list for later referencing
        f = open('data_race.csv', 'r', 1024)

        self.stats = []
        for line in f:
            self.stats.append(line)

        f.close()
        self.stats.pop(0)
