import math
import random


class Creature:
    def __init__(self, angles=None, model=None, max_energy=5):
        self.pos = [0, 0]
        self.age = 0
        self.orientation = 0 # 0: up, 1: right 2: down 3: left
        self.food_eaten = 0
        self.angles = angles
        self.model = model
        self.visited_positions = []
        self.max_energy = max_energy
        self.energy = self.max_energy

    def __repr__(self):
        if self.angles:
            return f"Creature(angles={self.angles})"
        else:
            return f"Creature(model={self.model})"

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
        self.energy = self.max_energy

    def normalize_angles(self):
        for i in range(len(self.angles)):
            self.angles[i] = self.angles[i] % (4*math.pi)


class Environment:
    def __init__(self, creature, s=9, seed=None, max_energy=5):
        self.size = s
        self.grid = [[0] * self.size for i in range(self.size)]
        self.player = creature
        self.player.pos = [s//2, s//2]
        self.grid[s//2][s//2] = 1
        self.player.max_energy = max_energy
        self.player.energy = self.player.max_energy

        if seed:
            random.seed(seed)
        else:
            random.seed()

    def __repr__(self):
        symbols = {0: '.', 1: 'C', 2: 'F'}
        txt = ""
        for row in self.grid:
            for square in row:
                txt += symbols[square] + " "
            txt += "\n"
        return txt

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

        # If energy is depleted action is ignored
        if self.player.energy <= 0:
            pass
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
                    self.player.energy += 5

                self.grid[old[0]][old[1]] = 0
                self.grid[x][y] = 1
                self.player.pos = new
                if new not in self.player.visited_positions:
                    self.player.visited_positions.append(new)
                moved = True

                # consume energy on successful forward moves
                self.player.energy = max(0, self.player.energy - 1)
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
            "orientation": self.player.orientation,
            "energy": self.player.energy,
            "max_energy": self.player.max_energy
        }

    def render(self, screen):
        import pygame as pg
        cell_size = 40
        WHITE = (255, 255, 255)
        BLUE = (50, 100, 255)
        GREEN = (50, 200, 50)
        GRID_COLOR = (180, 180, 180)
        TRIANGLE = (0, 0, 0)

        for row in range(self.size):
            for col in range(self.size):
                val = self.grid[row][col]
                if val == 0:
                    color = WHITE
                elif val == 1:
                    color = BLUE
                elif val == 2:
                    color = GREEN
                else:
                    color = WHITE
                rect = pg.Rect(col * cell_size, row * cell_size, cell_size, cell_size)
                pg.draw.rect(screen, color, rect)

        total_px = self.size * cell_size
        for i in range(self.size + 1):
            x = i * cell_size
            pg.draw.line(screen, GRID_COLOR, (x, 0), (x, total_px), 1)
            y = i * cell_size
            pg.draw.line(screen, GRID_COLOR, (0, y), (total_px, y), 1)

        center_x = self.player.pos[1] * cell_size + cell_size / 2.0
        center_y = self.player.pos[0] * cell_size + cell_size / 2.0

        tri_size = cell_size * 0.35
        h = tri_size // 2.0

        if self.player.orientation == 0:
            points = [(center_x, center_y - h), (center_x - h, center_y + h), (center_x + h, center_y + h)]
        elif self.player.orientation == 1:
            points = [(center_x + h, center_y), (center_x - h, center_y - h), (center_x - h, center_y + h)]
        elif self.player.orientation == 2:
            points = [(center_x, center_y + h), (center_x - h, center_y - h), (center_x + h, center_y - h)]
        else:
            points = [(center_x - h, center_y), (center_x + h, center_y - h), (center_x + h, center_y + h)]

        int_points = [(x, y) for x, y in points]
        pg.draw.polygon(screen, TRIANGLE, int_points)

    def has_food(self):
        for row in self.grid:
            for cell in row:
                if cell == 2:
                    return True
        return False

    def get_sight_blocks(self, n=6):
        row, col = self.player.pos
        # orientation: 0 up, 1 right, 2 down, 3 left
        if self.player.orientation == 0:
            directions = [(-1, 0), (0, -1), (0, 1)]
        elif self.player.orientation == 1:
            directions = [(0, 1), (-1, 0), (1, 0)]
        elif self.player.orientation == 2:
            directions = [(1, 0), (0, 1), (0, -1)]
        else:
            directions = [(0, -1), (1, 0), (-1, 0)]

        blocks = []
        for dr, dc in directions:
            dir_list = []
            for i in range(1, n + 1):
                r = row + dr * i
                c = col + dc * i
                if not self.in_bounds((r, c)):
                    dir_list.append(2)
                else:
                    cell = self.grid[r][c]
                    if cell == 2:
                        # food
                        dir_list.append(1)
                    else:
                        # empty or creature
                        dir_list.append(0)
            blocks.append(dir_list)

        return tuple(blocks)

    def get_sight(self, n=6):
        # returns (front, left, right) with normalized values corresponding to distance to nearest food or wall
        blocks = self.get_sight_blocks(n)
        summary = []
        for dir_list in blocks:
            val = 0
            for i in range(len(dir_list)):
                proximity = (n - i) / n
                if dir_list[i] == 1:
                    val = proximity
                    break
                elif dir_list[i] == 2:
                    val = -proximity
                    break
            summary.append(val)

        return tuple(summary) # front, left, right

if __name__ == "__main__":
    c = Creature()
    env = Environment(c, s=9)
    env.generate_food()
    print(env)
    sight = env.get_sight(4)
    print("Sight:", sight)
