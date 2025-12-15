from environment import *
from quantum_runner import *
import random


def simulate(c, runner, seed=None, steps=10):
    env = Environment(c, seed=seed)
    env.generate_food()
    for i in range(steps):
        action = runner.get_action(c.angles, env.get_local_sight())
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


def evaluate_average(c, runner, repeats=3):
    total = 0.0
    for r in range(repeats):
        seed = (hash(tuple(c.angles)) + r) & 0xFFFFFFFF
        # seed = random.randint(0, 9999999)
        _, f = simulate(c, runner, seed=seed)
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


def render(angles):
    pg.init()
    screen = pg.display.set_mode((200, 200))
    fps = 2
    c = Creature(angles)
    runner = QuantumRunner()
    env = Environment(c, seed=random.randint(0, 9999999))
    env.generate_food()

    clock = pg.time.Clock()

    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

        action = runner.get_action(c.angles, vision=env.get_local_sight())
        print(action)
        env.step(action)
        env.render(screen)

        pg.display.flip()
        clock.tick(fps)

    pg.quit()


if __name__ == "__main__":
    # evolution(20, 10, 0.2, 3, 5)

    angles = [34.54886511018649, -12.097268748762534, -9.177594991590729, 28.643305517127473, -0.274457538387189, 32.83530940763925, -6.444542576025194, -21.349586688070268, -10.120956402620724, -20.049398906949275, 1.8075166748596487, -12.00778838841676, -26.18011520334503, -20.026699621147, -19.913412870670722, 20.292132058523187, 27.381391378412914, -23.91878140753745, -1.316596000358409, -19.149377898547215]
    render(angles)
