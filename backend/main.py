import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from simulate import Creature, Environment, QuantumRunner
from web_helpers import evolution_async, evolution_classical_async
from simulate_classical import ClassicalRunner
import numpy as np


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
        csv = lines[0]
        angles = [float(x) for x in csv.split(",")]
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

    runner = ClassicalRunner(weights=weights)
    return Creature(model=runner, max_energy=max_energy)


class CreatureSnapshot(BaseModel):
    pos: List[int]
    orientation: int
    food_eaten: int
    grid: List[List[int]]
    fitness: float
    generation: int
    energy: int
    max_energy: int


def creature_to_snapshot(creature: Creature, env: Environment, fitness: float, generation: int) -> CreatureSnapshot:
    return CreatureSnapshot(
        pos=creature.pos,
        orientation=creature.orientation,
        food_eaten=creature.food_eaten,
        grid=env.grid,
        fitness=fitness,
        generation=generation,
        energy=creature.energy,
        max_energy=creature.max_energy
    )


class RunParams(BaseModel):
    generations: int
    children: int
    chance: float
    sigma: float
    repeats: int
    elites: int
    grid_size: int
    vision_range: int
    max_moves: int
    wall_density: float


class GenomeParams(BaseModel):
    run_genome: bool
    genome_text: str
    grid_size: int
    vision_range: int
    max_moves: int
    wall_density: float


class EvolutionResult(BaseModel):
    elites: List[List[float]]


app = FastAPI()

origins = [
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/creature", response_model=CreatureSnapshot)
def get_creature():
    creature = Creature([0.0])
    env = Environment(creature)
    env.generate_food()
    return creature_to_snapshot(creature, env, 0.0, 0)


@app.websocket("/ws/evolution")
async def ws_evolution(ws: WebSocket):
    await ws.accept()

    q = ws.query_params.get("quantum", "1")
    quantum = q.lower() in ("1", "true")

    current_best: dict = {
        "creature": None,
        "fitness": 0.0,
        "generation": 0,
        "version": 0,
    }

    sim_stop_event = asyncio.Event()

    async def safe_send(data):
        try:
            await ws.send_json(data)
            return True
        except (WebSocketDisconnect, RuntimeError, ConnectionResetError, asyncio.CancelledError):
            return False
        except Exception:
            return False

    async def send_simulation_snapshot(env, holder):
        snap = creature_to_snapshot(
            env.player,
            env,
            holder["fitness"],
            holder["generation"],
        )
        return await safe_send({"simulation": True, **snap.model_dump()})

    def _clone_creature_for_run(base: Creature):
        if quantum:
            runner = QuantumRunner()
            angles = base.angles
            fresh = Creature(angles=angles, max_energy=base.max_energy)
            return fresh, runner

        weights = base.model.get_weights()
        runner = ClassicalRunner(weights=weights)
        fresh = Creature(model=runner, max_energy=base.max_energy)
        return fresh, runner

    def reset_best_simulation():
        current_best["version"] += 1
        sim_stop_event.clear()

    async def sim_loop(grid_size, vision_range, max_moves, wall_density):
        last_version = -1
        env = None
        runner = None

        try:
            while True:
                if sim_stop_event.is_set():
                    # Wait until resets
                    await asyncio.sleep(0.1)
                    continue

                holder = current_best
                if holder["creature"] is None:
                    # not started yet
                    await asyncio.sleep(0.1)
                    continue

                # If the best creature changed OR was reset, rebuild the environment and runner.
                if holder["version"] != last_version:
                    print("(re)starting simulation for gen", holder["generation"])
                    last_version = holder["version"]

                    base = holder["creature"]
                    if not isinstance(base, Creature):
                        await asyncio.sleep(0.1)
                        continue
                    fresh, runner = _clone_creature_for_run(base)

                    env = Environment(fresh, s=grid_size, max_energy=max_moves, wall_density=wall_density)
                    env.generate_food()

                vision = env.get_sight(vision_range)

                if quantum:
                    action = runner.get_action(env.player.angles, vision)
                else:
                    action = runner.get_action(vision)

                env.step(action)
                await send_simulation_snapshot(env, holder)

                if env.player.energy <= 0:
                    print("No energy, simulation done")
                    sim_stop_event.set()
                    await send_simulation_snapshot(env, holder)
                    continue

                await asyncio.sleep(0.5)
                if not env.has_food():
                    print("All food eaten, simulation done")
                    sim_stop_event.set()
        except asyncio.CancelledError:
            return

    async def send_best(gen, creature, fitness):
        text = create_genome_text(creature, quantum=quantum)
        return await safe_send({"best": {"fitness": fitness, "genome_text": text}, "generation": gen})

    sim_task = None

    try:
        init_payload = await ws.receive_json()

        print("Received init payload:", init_payload)
        # run a genome directly
        if init_payload.get("run_genome") is True:
            print("starting genome run")
            params = GenomeParams(**init_payload)

            try:
                print("parsing genome")
                genome_mode = read_mode(params.genome_text)
                print("genome mode:", genome_mode)
                if genome_mode == "quantum":
                    quantum = True
                if genome_mode == "classical":
                    quantum = False
                base = creature_from_genome_text(params.genome_text, max_energy=params.max_moves)
            except Exception as e:
                print("Failed to parse genome:", e)
                await safe_send({"error": f"Failed to parse genome: {e}"})
                return

            print("quantum mode:", quantum)
            print("creature:", base)
            current_best["creature"] = base
            current_best["fitness"] = 0.0
            current_best["generation"] = 0
            current_best["version"] += 1

            sim_task = asyncio.create_task(sim_loop(params.grid_size, params.vision_range, params.max_moves, params.wall_density))

            while True:
                msg = await ws.receive_json()
                if msg.get("reset_simulation"):
                    reset_best_simulation()
                    ok = await safe_send({"reset_acknowledge": True})
                    if not ok:
                        break
            return

        # regular evolution
        params = RunParams(**init_payload)

        sim_task = asyncio.create_task(sim_loop(params.grid_size, params.vision_range, params.max_moves, params.wall_density))

        best_fitness = float("-inf")
        best_final = None

        if quantum:
            async for gen, creature, fitness in evolution_async(params.generations, params.children, params.chance, params.repeats, params.elites, params.grid_size, params.vision_range, params.max_moves, params.wall_density, params.sigma):
                if fitness >= best_fitness:
                    best_fitness = fitness
                    best_final = (creature, fitness, gen + 1)
                    ok = await send_best(gen + 1, creature, fitness)
                    if not ok:
                        break

                current_best["creature"] = creature
                current_best["fitness"] = fitness
                current_best["generation"] = gen + 1
                current_best["version"] += 1
        else:
            async for gen, creature, fitness in evolution_classical_async(params.generations, params.children, params.chance, params.repeats, params.elites, params.grid_size, params.vision_range, params.max_moves, params.wall_density, params.sigma):
                if fitness >= best_fitness:
                    best_fitness = fitness
                    best_final = (creature, fitness, gen + 1)
                    ok = await send_best(gen + 1, creature, fitness)
                    if not ok:
                        break

                current_best["creature"] = creature
                current_best["fitness"] = fitness
                current_best["generation"] = gen + 1
                current_best["version"] += 1

        final_creature, final_fitness, final_gen = best_final

        current_best["creature"] = final_creature
        current_best["fitness"] = final_fitness
        current_best["generation"] = final_gen
        current_best["version"] += 1

        # Send a final best
        await send_best(final_gen, final_creature, final_fitness)
        await safe_send({"done": True})

        # Keep connection open to expect a {"reset_simulation": true}
        while True:
            msg = await ws.receive_json()
            if msg.get("reset_simulation"):
                reset_best_simulation()
                ok = await safe_send({"reset_acknowledge": True})
                if not ok:
                    break

    except WebSocketDisconnect:
        return
    except Exception:
        sim_stop_event.set()
        try:
            await ws.close()
        except Exception:
            pass
    finally:
        sim_stop_event.set()
        try:
            sim_task.cancel()
        except Exception:
            pass


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

# TODO:
# make the genome run directly better
