from environment import *
from quantum_runner import *
import random


def simulate(c, runner, seed=None, steps=10, grid_size=9):
    env = Environment(c, s=grid_size, seed=seed)
    env.generate_food()
    for i in range(steps):
        action = runner.get_action(c.angles, env.get_sight(n=grid_size//2))
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
        fitness += 1000
    c.reset()
    return c, fitness


def mutate(creature, chance, sigma=3):
    new_angles = creature.angles.copy()
    for i in range(len(new_angles)):
        if random.random() <= chance:
            add = random.uniform(-sigma, sigma)
            new_angles[i] = new_angles[i] + add
    return Creature(new_angles)


def evaluate_average(c, runner, repeats=3, grid_size=9):
    total = 0.0
    for r in range(repeats):
        seed = (hash(tuple(c.angles)) + r) & 0xFFFFFFFF
        # seed = random.randint(0, 9999999)
        _, f = simulate(c, runner, seed=seed, grid_size=grid_size)
        total += f
    return total / repeats


def evolution(generations, children, chance, repeats, elites):
    runner = QuantumRunner()

    # random start
    parents = []
    for _ in range(elites):
        angles = [random.uniform(-12*pi, 12*pi) for _ in range(len(runner.parameters))]
        parents.append(Creature(angles))

    for gen in range(generations):
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

        if gen % 5 == 0 or gen == generations - 1:
            print(f"gen {gen}: best fitness {cand_with_fit[0][1]:.1f}, 2nd {cand_with_fit[1][1]:.1f}, 3rd {cand_with_fit[2][1]:.1f}")

        parents = [cand_with_fit[j][0] for j in range(min(elites, len(population)))]

        # for child in parents:
        #     child.normalize_angles()

    print("Final parents:")
    for p in parents:
        print(p)

    # return the angles of the final parents
    return [list(p.angles) for p in parents]


def render(angles, grid_size=9):
    import pygame as pg
    pg.init()
    fps = 2
    c = Creature(angles)
    runner = QuantumRunner()
    env = Environment(c, s=grid_size, seed=random.randint(0, 9999999))
    env.generate_food()
    screen = pg.display.set_mode((40 * env.size, 40 * env.size))

    clock = pg.time.Clock()

    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

        action = runner.get_action(c.angles, vision=env.get_sight())
        print(action)
        env.step(action)
        env.render(screen)

        pg.display.flip()
        clock.tick(fps)

    pg.quit()


if __name__ == "__main__":
    # evolution(20, 10, 0.2, 3, 5)

    angles = [-29.0837202551213, 34.855525154033025, -2.8092032794397612, -3.8994805031321, 27.21273607795417, 25.52637708603278, -29.392948398981908, -16.836954149972538, -4.7529119088527825, -0.6266165086584694, 7.078803902470396, -20.655962038102903, -31.078898546148473, 23.896015687653687, 9.122053983864246, 10.857857149352515, 3.7682642660411005, 23.659698078377474, -31.657232688278064, -23.546241246807334]
    render(angles)
