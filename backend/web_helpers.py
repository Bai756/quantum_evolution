import asyncio
import random
from math import pi
from simulate import QuantumRunner, mutate, evaluate_average
from environment import Creature, Environment
from simulate_classical import ClassicalRunner, mutate_classical, evaluate_average as evaluate_average_classical
import numpy as np

async def evolution_async(generations, children, chance, repeats, elites, grid_size, vision_range, max_moves, wall_density, sigma):
    runner = QuantumRunner()

    base_angles1 = [random.uniform(-12 * pi, 12 * pi) for _ in range(len(runner.parameters))]
    base_angles2 = [random.uniform(-12 * pi, 12 * pi) for _ in range(len(runner.parameters))]
    parents = [Creature(base_angles1), Creature(base_angles2)]

    for gen in range(generations):
        population = []
        for j in range(len(parents)):
            for _ in range(children):
                population.append(mutate(parents[j], chance, sigma=sigma))

        candidates = parents + population
        cand_with_fit = []

        for c in candidates:
            fit = await asyncio.to_thread(evaluate_average, c, runner, repeats, grid_size, vision_range, max_moves, wall_density)
            cand_with_fit.append((c, fit))
            await asyncio.sleep(0)

        cand_with_fit.sort(key=lambda x: x[1], reverse=True)

        if gen % 1 == 0 or gen == generations - 1:
            yield gen, cand_with_fit[0][0], cand_with_fit[0][1]

        parents = [cand_with_fit[j][0] for j in range(min(elites, len(cand_with_fit)))]

async def evolution_classical_async(generations, children, chance, repeats, elites, grid_size, vision_range, max_moves, wall_density, sigma):
    parents = [Creature(model=ClassicalRunner()) for _ in range(elites)]

    for gen in range(generations):
        population = []

        for j in range(len(parents)):
            for _ in range(children):
                child = mutate_classical(parents[j], chance, sigma=sigma)
                population.append(child)

        candidates = parents + population
        cand_with_fit = []
        for c in candidates:
            fit = await asyncio.to_thread(evaluate_average_classical, c, c.model, repeats, grid_size, vision_range, max_moves, wall_density)
            cand_with_fit.append((c, fit))
            await asyncio.sleep(0)

        cand_with_fit.sort(key=lambda x: x[1], reverse=True)

        if gen % 1 == 0 or gen == generations - 1:
            yield gen, cand_with_fit[0][0], cand_with_fit[0][1]
            # i can't believe i have to do this because it trains too fast
            await asyncio.sleep(0.5)

        parents = [cand_with_fit[j][0] for j in range(min(elites, len(population)))]

def clone_creature_for_run(base, quantum):
    if quantum:
        runner = QuantumRunner()
        angles = base.angles
        fresh = Creature(angles=angles, max_energy=base.max_energy)
        return fresh, runner

    weights = base.model.get_weights()
    runner = ClassicalRunner(weights=weights)
    fresh = Creature(model=runner, max_energy=base.max_energy)
    return fresh, runner


async def sim_loop(current_best, sim_stop_event, quantum, grid_size, vision_range, max_moves, wall_density, on_snapshot):
    last_version = -1
    env = None
    runner = None

    try:
        while True:
            if sim_stop_event.is_set():
                await asyncio.sleep(0.1)
                continue

            holder = current_best
            if holder.get("creature") is None:
                await asyncio.sleep(0.1)
                continue

            if holder.get("version") != last_version:
                # print("(re)starting simulation for gen", holder.get("generation"))
                last_version = holder.get("version")

                base = holder["creature"]

                fresh, runner = clone_creature_for_run(base, quantum)
                env = Environment(fresh, s=grid_size, max_energy=max_moves, wall_density=wall_density)
                env.generate_food()

            vision = env.get_sight(vision_range)

            if quantum:
                action = runner.get_action(env.player.angles, vision)
            else:
                action = runner.get_action(vision)

            env.step(action)

            holder["fitness"] = compute_fitness(env.player, env)

            await on_snapshot(env, holder)

            if env.player.energy <= 0:
                # print("No energy, simulation done")
                fresh, runner = clone_creature_for_run(base, quantum)
                env = Environment(fresh, s=grid_size, max_energy=max_moves, wall_density=wall_density)
                env.generate_food()
                if not holder["auto_restart"]:
                    # print("stopping simulation")
                    sim_stop_event.set()
                holder["fitness"] = compute_fitness(env.player, env)
                await on_snapshot(env, holder)
                continue

            await asyncio.sleep(0.5)
            if not env.has_food():
                # print("All food eaten, simulation done")
                fresh, runner = clone_creature_for_run(base, quantum)
                env = Environment(fresh, s=grid_size, max_energy=max_moves, wall_density=wall_density)
                env.generate_food()
                if not holder["auto_restart"]:
                    # print("stopping simulation")
                    sim_stop_event.set()
                holder["fitness"] = compute_fitness(env.player, env)
    except asyncio.CancelledError:
        return


def create_genome_text(c: Creature, quantum):
    if quantum:
        angles = c.angles
        return "quantum\n" + ",".join(str(float(a)) for a in angles)

    weights = c.model.get_weights()

    out_lines = ["classical"]
    for layer_weights in weights:
        arr = np.array(layer_weights)
        if arr.ndim == 1:
            out_lines.append(",".join(str(float(x)) for x in arr))
        else:
            for row in arr:
                out_lines.append(",".join(str(float(x)) for x in row))
        out_lines.append("---")

    return "\n".join(out_lines)


def read_mode(genome):
    for line in genome.splitlines():
        line = line.strip()
        return line
    return None


def creature_from_genome_text(genome, max_energy):
    mode = read_mode(genome)
    if not mode:
        raise ValueError("Genome missing mode")
    if mode not in ["quantum", "classical"]:
        raise ValueError(f"Invalid mode: {mode}")

    raw_lines = [ln.rstrip("\n") for ln in genome.splitlines()]

    # drop empty lines
    lines = []
    for line in raw_lines:
        line = line.strip()
        if line == "":
            continue
        lines.append(line)

    # remove the mode line
    if lines:
        lines = lines[1:]

    if mode == "quantum":
        numbers = lines[0]
        angles = [float(x) for x in numbers.split(",")]
        runner = QuantumRunner()
        if len(angles) != len(runner.parameters):
            raise ValueError(f"Invalid number of angles for quantum runner: expected {len(runner.parameters)}, got {len(angles)}")
        return Creature(angles=angles, max_energy=max_energy)

    weights = []
    current_weight = []
    for line in lines:
        line = line.strip()
        if line == "---":
            if current_weight:
                arr = np.array(current_weight, dtype=float)
                if arr.ndim == 2 and arr.shape[0] == 1:
                    arr = arr.flatten()
                weights.append(arr)
                current_weight = []
        else:
            current_weight.append([float(x) for x in line.split(",")])

    if current_weight:
        arr = np.array(current_weight, dtype=float)
        if arr.ndim == 2 and arr.shape[0] == 1:
            arr = arr.flatten()
        weights.append(arr)

    try:
        runner = ClassicalRunner(weights=weights)
    except Exception as e:
        raise ValueError(f"Failed to create ClassicalRunner from weights: {e}")

    return Creature(model=runner, max_energy=max_energy)


def compute_fitness(creature, env):
    total_food = creature.food_eaten
    for row in env.grid:
        for square in row:
            if square == 2:
                total_food += 1

    fitness = creature.food_eaten * 100 + len(creature.visited_positions)

    if creature.food_eaten >= total_food:
        fitness += 1000

    if creature.energy <= 0:
        fitness -= 50
    else:
        fitness += 20

    return fitness
