from math import pi
from environment import *
from quantum_runner import *
import random


def simulate(a, b, runner):
    c = Creature(a, b)
    env = Environment(c)
    env.generate_food()
    for i in range(20):
        action = runner.get_action(a, b)
        _ = env.step(action)
        # print(repr(env))
        # print()

    fitness = c.food_eaten * 10 + len(c.visited_positions)
    return c, fitness

def evolution():
    random.seed(1)
    runner = QuantumRunner()
    a1 = pi / 2
    b1 = pi / 2
    a2 = pi / 2
    b2 = pi / 2

    for i in range(101):
        most_fit = []
        for j in range(20):
            c, f = simulate(a1 + random.uniform(-0.1, 0.1), b1 + random.uniform(-0.1, 0.1), runner)
            # print("fitness", f)
            # print("food", c.food_eaten)
            most_fit.append((c, f))

        for j in range(20):
            c, f = simulate(a2 + random.uniform(-0.1, 0.1), b2 + random.uniform(-0.1, 0.1), runner)
            most_fit.append((c, f))


        sorted_by_fitness = sorted(most_fit, key=lambda x: x[1], reverse=True)
        if i % 10 == 0:
            print(f"{i}: {sorted_by_fitness[0][1]}, {sorted_by_fitness[1][1]}")
            print(a1)
            print(b1)
        a1 = sorted_by_fitness[0][0].a % (2*pi)
        b1 = sorted_by_fitness[0][0].b % (2*pi)

        a2 = sorted_by_fitness[1][0].a % (2*pi)
        b2 = sorted_by_fitness[1][0].b % (2*pi)
        # for rank, (c, fitness) in enumerate(sorted_by_fitness):
        #     print(f"{rank}: {c.a} {c.b} -> {fitness}")
    print(a2)
    print(b2)

if __name__ == "__main__":
    evolution()
