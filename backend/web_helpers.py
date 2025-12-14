import asyncio
import random
from math import pi
from simulate import Creature, QuantumRunner, mutate, evaluate_average

async def evolution_async(generations, children, chance, repeats, elites):
    runner = QuantumRunner()

    base_angles1 = [random.uniform(-12 * pi, 12 * pi) for _ in range(len(runner.parameters))]
    base_angles2 = [random.uniform(-12 * pi, 12 * pi) for _ in range(len(runner.parameters))]
    parents = [Creature(base_angles1), Creature(base_angles2)]

    for gen in range(generations):
        population = []
        for j in range(len(parents)):
            for _ in range(children):
                population.append(mutate(parents[j], chance))

        candidates = parents + population
        cand_with_fit = []

        for c in candidates:
            fit = await asyncio.to_thread(evaluate_average, c, runner, repeats)
            cand_with_fit.append((c, fit))
            await asyncio.sleep(0)

        cand_with_fit.sort(key=lambda x: x[1], reverse=True)

        if gen % 1 == 0 or gen == generations - 1:
            yield gen, cand_with_fit[0][0], cand_with_fit[0][1]

        parents = [cand_with_fit[j][0] for j in range(min(elites, len(cand_with_fit)))]
