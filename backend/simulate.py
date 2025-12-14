from environment import *
from quantum_runner import *
import random


def simulate(c, runner, seed=None, steps=10):
    env = Environment(c, seed=seed)
    env.generate_food()
    for i in range(steps):
        front, left, right = env.get_local_sight()
        action = runner.get_action(c.angles, vision=(front, left, right))
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


def mutate(creature, chance, sigma=0.5):
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

    base_angles = [0.0] * 20
    parents = [Creature(base_angles), Creature(base_angles)]

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
    # evolution(40, 10, 0.2, 5, 3)

    angles = [0.14155315570178761, -0.9171240291954361, -1.0552398116809152, 0.16869360391205135, 0.19554332824122123, 1.1671859990410423, -0.430875675014589, 0.23985414436090746, -0.0021288120866479465, -0.2275494330013358, 0.718745996984728, -0.2682483015153413, 0.16989891723604988, 0.3437428550980204, 0.3450233738685601, -0.006039107399554933, 0.02587302583676787, 1.5726320867652386, -0.34673639124215927, -0.5247931172372359]
    render(angles)
