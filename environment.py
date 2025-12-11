import math
import random


class Creature:
    def __init__(self, angles):
        self.pos = [0, 0]
        self.age = 0
        self.orientation = 0
        self.food_eaten = 0
        self.angles = list(angles)
        self.visited_positions = []

    def __repr__(self):
        return f"{self.angles}"

    def forward_pos(self):
        x, y = self.pos
        if self.orientation == 0:
            return [x-1, y]
        elif self.orientation == 1:
            return [x, y+1]
        elif self.orientation == 2:
            return [x+1, y]
        else:
            return [x, y-1]

    def turn_left(self):
        self.orientation = (self.orientation - 1) % 4

    def turn_right(self):
        self.orientation = (self.orientation + 1) % 4

    def reset(self):
        self.pos = [0, 0]
        self.age = 0
        self.orientation = 0
        self.food_eaten = 0
        self.visited_positions = []

    def normalize_angles(self):
        for i in range(len(self.angles)):
            self.angles[i] = self.angles[i] % (4*math.pi)


class Environment:
    def __init__(self, creature, s=5, seed=1):
        self.size = s
        self.grid = [[0] * self.size for i in range(self.size)]
        self.player = creature
        self.player.pos = [s//2, s//2]
        self.grid[s//2][s//2] = 1
        random.seed(seed)

    def __repr__(self):
        txt = ""
        for row in self.grid:
            for col in row:
                txt += str(col) + " "
            txt += "\n"
        return txt[:-1]

    def in_bounds(self, pos):
        return 0 <= pos[0] < self.size and 0 <= pos[1] < self.size

    def empty_positions(self):
        positions = []
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j] == 0:
                    positions.append((i, j))
        return positions

    def generate_food(self):
        num_food = math.ceil(self.size ** 2 / 9)
        chosen = random.sample(self.empty_positions(), num_food)
        for i, j in chosen:
            self.grid[i][j] = 2

    def step(self, action):
        ate = False
        moved = False
        if action == 0:
            pass
        elif action == 1:
            new = self.player.forward_pos()
            if self.in_bounds(new):
                old = self.player.pos
                x, y = new
                if self.grid[x][y] == 2:
                    ate = True
                    self.player.food_eaten += 1

                self.grid[old[0]][old[1]] = 0
                self.grid[x][y] = 1
                self.player.pos = new
                if new not in self.player.visited_positions:
                    self.player.visited_positions.append(new)
                moved = True
        elif action == 2:
            self.player.turn_left()
        elif action == 3:
            self.player.turn_right()
        else:
            raise ValueError("Invalid action", action)

        self.player.age += 1

        return {
            "action": action,
            "moved": moved,
            "ate": ate,
            "position": self.player.pos,
            "orientation": self.player.orientation
        }
