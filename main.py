from environment import *
from quantum_runner import *
import random
from math import pi


def simulate(angles, runner, seed=None, steps=20):
    if seed is not None:
        random.seed(seed)
    c = Creature(angles)
    env = Environment(c)
    env.generate_food()
    for i in range(steps):
        action = runner.get_action(angles)
        _ = env.step(action)
        # print(repr(env))
        # print()

    # large bonus for clearing all food and more for eating food
    total_food = c.food_eaten
    for row in env.grid:
        for square in row:
            if square == 2:
                total_food += 1

    fitness = c.food_eaten * 100 + len(c.visited_positions)
    if c.food_eaten >= total_food:
        fitness += 10000
    return c, fitness

def mutate(angles, chance, sigma=0.05):
    new_angles = list(angles)
    for i in range(len(new_angles)):
        if random.random() <= chance:
            new_angles[i] = new_angles[i] + random.uniform(-sigma, sigma)
    return new_angles

def evaluate_average(angles, runner, repeats=3):
    total = 0.0
    for r in range(repeats):
        seed = (hash(tuple(angles)) + r) & 0xFFFFFFFF
        _, f = simulate(angles, runner, seed=seed)
        total += f
    return total / repeats

def evolution(generations=100, children=20, chance=0.2, repeats=3, elites=2):
    runner = QuantumRunner()
    parent1 = [pi/2] * 6
    parent2 = [pi/2] * 6

    for i in range(generations):
        population = []

        for _ in range(children):
            child = mutate(parent1, chance)
            fitness = evaluate_average(child, runner, repeats=repeats)
            population.append((child, fitness))

        for _ in range(children):
            child = mutate(parent2, chance)
            fitness = evaluate_average(child, runner, repeats=repeats)
            population.append((child, fitness))

        population.sort(key=lambda x: x[1], reverse=True)
        if i % 5 == 0 or i == generations - 1:
            print(f"gen {i}: best fitness {population[0][1]:.1f}, 2nd {population[1][1]:.1f}")

        next_parents = [population[i][0] for i in range(min(elites, len(population)))]

        while len(next_parents) < 2:
            next_parents.append(mutate(next_parents[0], chance))

        parent1, parent2 = list(next_parents[0]), list(next_parents[1])

        for angles in (parent1, parent2):
            for k in range(len(angles)):
                angles[k] = angles[k] % (2 * pi)

    print("Final parents:")
    print(parent1)
    print(parent2)


if __name__ == "__main__":
    for i in range(5):
        print(random.random())
    evolution(generations=60, children=10, chance=0.2, repeats=5, elites=5)
