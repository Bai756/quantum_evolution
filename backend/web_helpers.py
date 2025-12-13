from simulate import Creature, QuantumRunner, mutate, evaluate_average


def evolution_iter(generations, children, chance, repeats, elites):
    runner = QuantumRunner()
    parents = [
        Creature([0.0000, 1.0472, 3.1416, 3.6652, 0.0000, 3.6652]),
        Creature([4.1888, 0.5236, 4.1888, 2.6180, 0.5236, 1.0472]),
    ]

    best_overall = (parents[0], float('-inf'))

    for gen in range(generations):
        population = []
        for j in range(len(parents)):
            for _ in range(children):
                child = mutate(parents[j], chance)
                population.append(child)

        candidates = parents + population
        cand_with_fit = []
        for c in candidates:
            fit = evaluate_average(c, runner, repeats)
            cand_with_fit.append((c, fit))

        cand_with_fit.sort(key=lambda x: x[1], reverse=True)

        if cand_with_fit[0][1] > best_overall[1]:
            best_overall = (cand_with_fit[0][0], cand_with_fit[0][1])

        if gen % 1 == 0 or gen == generations - 1:
            yield gen, cand_with_fit[0][0], cand_with_fit[0][1]

        next_parents = [cand_with_fit[j][0] for j in range(min(elites, len(cand_with_fit)))]
        parents = [Creature(p.angles) for p in next_parents]

    return best_overall
