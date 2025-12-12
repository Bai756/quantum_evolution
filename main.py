from environment import *
from quantum_runner import *
import random
from math import pi


def simulate(c, runner, seed=None, steps=20):
    env = Environment(c, seed=seed)
    env.generate_food()
    for i in range(steps):
        action = runner.get_action(c.angles)
        _ = env.step(action)
        # print(repr(env))

    # large bonus for clearing all food and more for eating food
    total_food = c.food_eaten
    for row in env.grid:
        for square in row:
            if square == 2:
                total_food += 1

    fitness = c.food_eaten * 100 + len(c.visited_positions)
    if c.food_eaten >= total_food:
        fitness += 10000
    c.reset()
    return c, fitness

def mutate(creature, chance, sigma=0.2):
    new_angles = creature.angles.copy()
    for i in range(len(new_angles)):
        if random.random() <= chance:
            add = random.uniform(-sigma, sigma)
            new_angles[i] = new_angles[i] + add
    return Creature(new_angles)

def evaluate_average(c, runner, repeats=3):
    total = 0.0
    for r in range(repeats):
        #seed = (hash(tuple(angles)) + r) & 0xFFFFFFFF
        seed = random.randint(0, 9999999)
        _, f = simulate(c, runner, seed=seed)
        total += f
    return total / repeats

def evolution(generations, children, chance, repeats, elites):
    runner = QuantumRunner()
    parents = [Creature([0.0000, 1.0472, 3.1416, 3.6652, 0.0000, 3.6652]),
               Creature([4.1888, 0.5236, 4.1888, 2.6180, 0.5236, 1.0472])]

    for i in range(generations):
        population = []

        for j in range(len(parents)):
            for _ in range(children):
                child = mutate(parents[j], chance)
                population.append(child)

        candidates = parents + population
        cand_with_fit = []
        for c in candidates:
            cand_with_fit.append((c, evaluate_average(c, runner, repeats)))

        cand_with_fit.sort(key=lambda x: x[1], reverse=True)

        if i % 5 == 0 or i == generations - 1:
            print(f"gen {i}: best fitness {cand_with_fit[0][1]:.1f}, 2nd {cand_with_fit[1][1]:.1f}")

        next_parents = [cand_with_fit[j][0] for j in range(min(elites, len(population)))]

        parents = [next_parents[j] for j in range(elites)]

        # for child in parents:
        #     child.normalize_angles()

    print("Final parents:")
    for p in parents:
        print(p)

def render(angles):
    pg.init()
    screen = pg.display.set_mode((200, 200))
    fps = 2
    c = Creature(angles)
    runner = QuantumRunner()
    env = Environment(c)
    env.generate_food()

    clock = pg.time.Clock()

    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

        action = runner.get_action(c.angles)
        print(action)
        env.step(action)
        env.render(screen)

        pg.display.flip()
        clock.tick(fps)

    pg.quit()

if __name__ == "__main__":
    # evolution(10, 10, 0.2, 5, 3)

    # angles[1] and [2] work pretty well
    angles = [[0.0, 1.305084939618391, 3.1416, 3.4405219230155755, -0.05782300140385274, 3.752734189104716], [0.03378434831137653, 1.441234729740852, 3.096222841904588, 3.5313561482881033, 0.1135670575082236, 3.6652],
              [0.03378434831137653, 1.441234729740852, 3.096222841904588, 3.5313561482881033, -0.12436814333957848, 3.6652]]
    render(angles[0])
