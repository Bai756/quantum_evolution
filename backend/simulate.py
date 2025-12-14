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
        fitness += 10000
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
    base_angles1 = [random.uniform(-12*pi, 12*pi) for _ in range(len(runner.parameters))]
    base_angles2 = [random.uniform(-12*pi, 12*pi) for _ in range(len(runner.parameters))]
    parents = [Creature(base_angles1), Creature(base_angles2)]

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

        if gen % 3 == 0 or gen == generations - 1:
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
    # evolution(15, 5, 0.2, 3, 2)

    # AHHH LET"s GO
    # This angle thing actually works
    # if food is detected it goes to it
    # if wall is in front, it turns
    # it does get confused when there's food and wall detected but it's good enough
    # moves basically randomly if nothing is detected
    angles = [-20.09431755980479, 27.84902173211906, 12.97414128774676, -23.17734560568782, -8.8197627270775, -30.81576113047188, 9.53460825687316, 27.786606309333322, -30.686859293888464, 23.312997172529787, -26.444862504647897, 15.787270577861467, 8.322822903949204, 34.38061507226649, -32.260507292764274, -32.81703620557763, -18.14604685103268, -2.0989499581109645, -11.716329309921603, -21.75222189562824]
    render(angles)
