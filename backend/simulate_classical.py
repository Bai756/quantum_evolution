from environment import *
from runner import ClassicalRunner
import random
import numpy as np


def simulate(c, runner, seed=None, steps=10):
    env = Environment(c, seed=seed)
    env.generate_food()
    for i in range(steps):
        action = runner.get_action(env.get_local_sight())
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


def mutate(creature, chance, sigma=0.1):
    weights = creature.model.get_weights()
    new_weights = []
    for w in weights:
        w_new = w.copy()
        if random.random() <= chance:
            mutation = np.random.normal(0, sigma, size=w.shape)
            w_new += mutation
        new_weights.append(w_new)
    return Creature(model=ClassicalRunner(weights=new_weights))


def evaluate_average(c, runner, repeats=3):
    total = 0.0
    for r in range(repeats):
        seed = random.randint(0, 9999999)
        _, f = simulate(c, runner, seed=seed)
        total += f
    return total / repeats


def evolution(generations, children, chance, repeats, elites):
    # random start
    parents = [Creature(model=ClassicalRunner()) for _ in range(elites)]

    for gen in range(generations):
        population = []

        for j in range(len(parents)):
            for _ in range(children):
                child = mutate(parents[j], chance)
                population.append(child)

        candidates = parents + population
        cand_with_fit = []
        for c in candidates:
            cand_with_fit.append((c, evaluate_average(c, c.model, repeats=repeats)))

        cand_with_fit.sort(key=lambda x: x[1], reverse=True)

        if gen % 5 == 0 or gen == generations - 1:
            print(f"gen {gen}: best fitness {cand_with_fit[0][1]:.1f}, 2nd {cand_with_fit[1][1]:.1f}, 3rd {cand_with_fit[2][1]:.1f}")

        parents = [cand_with_fit[j][0] for j in range(min(elites, len(population)))]

    print("Final parents:")
    for p in parents:
        print(p.model.get_weights())

    # return the weights of the final parents
    return [p.model.get_weights() for p in parents]


def render(weights):
    import pygame as pg
    pg.init()
    screen = pg.display.set_mode((200, 200))
    fps = 2
    runner = ClassicalRunner(weights=weights)
    c = Creature(model=runner)
    env = Environment(c, seed=random.randint(0, 9999999))
    env.generate_food()

    clock = pg.time.Clock()

    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

        action = runner.get_action(env.get_local_sight())
        print(action)
        env.step(action)
        env.render(screen)

        pg.display.flip()
        clock.tick(fps)

    pg.quit()


if __name__ == "__main__":
    weights = evolution(20, 10, 0.2, 3, 5)

    # weights = []
    render(weights[0])
