from environment import *
from classical_runner import ClassicalRunner
import random
import numpy as np


def simulate(c, runner, seed=None, steps=10, grid_size=9):
    env = Environment(c, s=grid_size, seed=seed)
    env.generate_food()
    for i in range(steps):
        action = runner.get_action(env.get_sight(n=grid_size//2))
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


def mutate_classical(creature, chance, sigma=1):
    weights = creature.model.get_weights()
    new_weights = []
    for w in weights:
        w_new = w.copy()
        if random.random() <= chance:
            mutation = np.random.normal(0, sigma, size=w.shape)
            w_new += mutation
        new_weights.append(w_new)
    return Creature(model=ClassicalRunner(weights=new_weights))


def evaluate_average(c, runner, repeats=3, grid_size=9):
    total = 0.0
    for r in range(repeats):
        seed = random.randint(0, 9999999)
        _, f = simulate(c, runner, seed=seed, grid_size=grid_size)
        total += f
    return total / repeats


def evolution(generations, children, chance, repeats, elites):
    # random start
    parents = [Creature(model=ClassicalRunner()) for _ in range(elites)]

    for gen in range(generations):
        population = []

        for j in range(len(parents)):
            for _ in range(children):
                child = mutate_classical(parents[j], chance)
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


def render(weights, grid_size=9):
    import pygame as pg
    pg.init()
    fps = 2
    runner = ClassicalRunner(weights=weights)
    c = Creature(model=runner)
    env = Environment(c, s=grid_size, seed=random.randint(0, 9999999))
    env.generate_food()
    screen = pg.display.set_mode((40 * env.size, 40 * env.size))

    clock = pg.time.Clock()

    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

        action = runner.get_action(env.get_sight())
        print(action)
        env.step(action)
        env.render(screen)

        pg.display.flip()
        clock.tick(fps)

    pg.quit()


if __name__ == "__main__":
    weights = evolution(20, 10, 0.2, 3, 5)

    # save the top weight to a txt file
    file_path = "best_classical_weights.txt"
    with open(file_path, "w") as f:
        for layer_weights in weights[0]:
            arr = np.array(layer_weights)
            if arr.ndim == 1:
                f.write(",".join(str(float(x)) for x in arr) + "\n")
            else:
                for row in arr:
                    f.write(",".join(str(float(x)) for x in row) + "\n")
            f.write("---\n")

    render(weights[0])
