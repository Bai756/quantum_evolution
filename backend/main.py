import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from simulate import Creature, Environment, QuantumRunner
from web_helpers import evolution_async, evolution_classical_async
from simulate_classical import ClassicalRunner

class CreatureSnapshot(BaseModel):
    pos: List[int]
    orientation: int
    food_eaten: int
    grid: List[List[int]]
    fitness: float
    generation: int


def creature_to_snapshot(creature: Creature, env: Environment, fitness: float, generation: int) -> CreatureSnapshot:
    return CreatureSnapshot(
        pos=creature.pos,
        orientation=creature.orientation,
        food_eaten=creature.food_eaten,
        grid=env.grid,
        fitness=fitness,
        generation=generation,
    )


class RunParams(BaseModel):
    generations: int
    children: int
    chance: float
    repeats: int
    elites: int
    grid_size: int
    vision_range: int


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

    current_best = {
        "creature": None,
        "fitness": 0.0,
        "generation": 0,
        "version": 0,
    }
    stop_event = asyncio.Event()

    async def send_simulation_snapshot(env, holder):
        snap = creature_to_snapshot(
            env.player,
            env,
            holder["fitness"],
            holder["generation"],
        )
        await ws.send_json({"simulation": True, **snap.model_dump()})

    async def sim_loop(grid_size, vision_range):
        last_version = -1
        env = None
        runner = None

        try:
            while not stop_event.is_set():
                holder = current_best
                if holder["creature"] is None:
                    # not started yet
                    await asyncio.sleep(0.1)
                    continue

                # If the best creature changed, rebuild the environment and runner.
                if holder["version"] != last_version:
                    print("New best creature", holder["generation"])
                    last_version = holder["version"]

                    base = holder["creature"]
                    if quantum:
                        runner = QuantumRunner()
                        angles = list(base.angles)
                        fresh = Creature(angles=angles)
                    else:
                        weights = base.model.get_weights()
                        fresh = Creature(model=ClassicalRunner(weights=weights))
                        runner = fresh.model

                    env = Environment(fresh, s=grid_size)
                    env.generate_food()

                vision = env.get_sight(vision_range)

                if quantum:
                    action = runner.get_action(env.player.angles, vision)
                else:
                    action = runner.get_action(vision)
                env.step(action)
                await send_simulation_snapshot(env, holder)

                await asyncio.sleep(0.5)
                if not env.has_food():
                    print("Simulation: all food eaten, done")
                    stop_event.set()
                    break
        except asyncio.CancelledError:
            return

    async def send_best(gen, creature, fitness):
        if quantum:
            await ws.send_json(
                {"best": {"fitness": fitness},
                 "generation": gen
                 })
        else:
            await ws.send_json(
                {"best": {"fitness": fitness},
                 "generation": gen
                 })

    try:
        init_payload = await ws.receive_json()
        params = RunParams(**init_payload)

        sim_task = asyncio.create_task(sim_loop(params.grid_size, params.vision_range))

        best_fitness = float("-inf")
        best_final = None

        if quantum:
            async for gen, creature, fitness in evolution_async(params.generations, params.children, params.chance, params.repeats, params.elites, params.grid_size, params.vision_range):
                if fitness >= best_fitness:
                    best_fitness = fitness
                    best_final = (creature, fitness, gen + 1)
                    await send_best(gen + 1, creature, fitness)

                current_best["creature"] = creature
                current_best["fitness"] = fitness
                current_best["generation"] = gen + 1
                current_best["version"] += 1
        else:
            async for gen, creature, fitness in evolution_classical_async(params.generations, params.children, params.chance, params.repeats, params.elites, params.grid_size, params.vision_range):
                if fitness >= best_fitness:
                    best_fitness = fitness
                    best_final = (creature, fitness, gen + 1)
                    await send_best(gen + 1, creature, fitness)

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
        await ws.send_json({"done": True})

        # wait until client disconnects
        try:
            while not stop_event.is_set():
                await ws.receive_text()
        except WebSocketDisconnect:
            pass

    except WebSocketDisconnect:
        return
    except Exception as exc:
        try:
            await ws.send_json({"error": str(exc)})
        finally:
            stop_event.set()
            await ws.close()
    finally:
        # Clean up
        # Apparently sim_task may not be defined if exception happens early
        stop_event.set()
        try:
            sim_task.cancel()
        except Exception:
            pass


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
