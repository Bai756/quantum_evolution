from environment import *
from quantum_runner import *
import random


def simulate(c, runner, seed=None, steps=20, grid_size=9, vision_range=None, max_moves = 5, wall_density=0.0):
    env = Environment(c, s=grid_size, seed=seed, max_energy=max_moves, wall_density=wall_density)
    env.generate_food()
    vr = vision_range if vision_range is not None else grid_size // 2
    for i in range(steps):
        action = runner.get_action(c.angles, env.get_sight(n=vr))
        _ = env.step(action)
        if env.player.energy <= 0:
            break
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

    if c.energy <= 0:
        fitness -= 50
    else:
        fitness += 20

    c.reset()
    return c, fitness


def mutate(creature, chance, sigma=3):
    new_angles = creature.angles.copy()
    for i in range(len(new_angles)):
        if random.random() <= chance:
            add = random.uniform(-sigma, sigma)
            new_angles[i] = new_angles[i] + add
    return Creature(new_angles)


def evaluate_average(c, runner, repeats=3, grid_size=9, vision_range=None, max_moves = 5, wall_density=0.0):
    total = 0.0
    for r in range(repeats):
        seed = (hash(tuple(c.angles)) + r) & 0xFFFFFFFF
        # seed = random.randint(0, 9999999)
        _, f = simulate(c, runner, seed=seed, grid_size=grid_size, vision_range=vision_range, max_moves=max_moves, wall_density=wall_density)
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
        print(p.angles)

    # return the angles of the final parents
    return [list(p.angles) for p in parents]


def render(angles, grid_size=9, wall_density=0.0):
    import pygame as pg
    pg.init()
    fps = 2
    c = Creature(angles)
    runner = QuantumRunner()
    env = Environment(c, s=grid_size, seed=random.randint(0, 9999999), wall_density=wall_density)
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
        print("Energy", env.player.energy)

        pg.display.flip()
        clock.tick(fps)

    pg.quit()


if __name__ == "__main__":
    # evolution(20, 10, 0.2, 3, 5)

    angles = [0.49314955464022026, -17.000701033127097, -0.8696918978910082, 7.173013453701259, -10.619195506389651, -25.3888807023303, 16.859678238472217, -16.191769024125808, -30.713596955190308, -30.10772994298271, -32.34004922118576, -7.699319384619486, -30.055116018443517, 12.756593589180547, -18.638222289030637, 19.725279210739103, -9.047420863961793, -11.411062935924665, -31.750835088926884, -40.75576008345652]
    render(angles, wall_density=0.3)

