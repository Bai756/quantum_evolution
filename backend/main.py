import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from environment import Creature, Environment
import web_helpers
from classical_runner import weights_to_json
from quantum_runner import serialize_circuit
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path


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
    visualize: bool


class GenomeParams(BaseModel):
    run_genome: bool
    genome_text: str
    grid_size: int
    vision_range: int
    max_moves: int
    wall_density: float
    visualize: bool


class EvolutionResult(BaseModel):
    elites: List[List[float]]


app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

# Serve Vite assets
app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

# Serve React index.html
@app.get("/")
def serve_react():
    return FileResponse(FRONTEND_DIST / "index.html")

# origins = [
#     "http://localhost:5173"
# ]
#
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_methods=["*"],
#     allow_headers=["*"]
# )


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

    visualize = False

    async def send_best(generation, creature, fitness):
        data = {
            "best": {
                "fitness": fitness,
                "genome_text": web_helpers.create_genome_text(creature, quantum)
            },
            "generation": generation
        }

        if visualize:
            if quantum:
                data["best"]["visualization"] = {"circuit": serialize_circuit(creature.angles)}
            else:
                weights = creature.model.get_weights()
                data["best"]["visualization"] = {"network": weights_to_json(weights)}
        return await safe_send(data)

    async def safe_send(data):
        try:
            await ws.send_json(data)
            return True
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

    def reset_best_simulation():
        current_best["version"] += 1
        sim_stop_event.clear()

    sim_task = None

    try:
        init_payload = await ws.receive_json()

        visualize = bool(init_payload.get("visualize", False))

        # run a genome directly
        if init_payload.get("run_genome") is True:
            params = GenomeParams(**init_payload)

            try:
                genome_mode = web_helpers.read_mode(params.genome_text)
                if genome_mode == "quantum":
                    quantum = True
                if genome_mode == "classical":
                    quantum = False
                base = web_helpers.creature_from_genome_text(params.genome_text, max_energy=params.max_moves)
            except Exception as e:
                await safe_send({"error": f"Failed to parse genome: {e}"})
                return

            current_best["creature"] = base
            current_best["fitness"] = 0.0
            current_best["generation"] = 0
            current_best["version"] += 1

            # send initial best so frontend gets genome_text and optionally visualization
            await send_best(0, base, 0.0)

            sim_task = asyncio.create_task(web_helpers.sim_loop(current_best, sim_stop_event, quantum, params.grid_size, params.vision_range, params.max_moves, params.wall_density, send_simulation_snapshot))

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

        sim_task = asyncio.create_task(web_helpers.sim_loop(current_best, sim_stop_event, quantum, params.grid_size, params.vision_range, params.max_moves, params.wall_density, send_simulation_snapshot, auto_restart=True))

        best_fitness = float("-inf")
        best_final = None

        if quantum:
            async for gen, creature, fitness in web_helpers.evolution_async(params.generations, params.children, params.chance, params.repeats, params.elites, params.grid_size, params.vision_range, params.max_moves, params.wall_density, params.sigma):
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
            async for gen, creature, fitness in web_helpers.evolution_classical_async(params.generations, params.children, params.chance, params.repeats, params.elites, params.grid_size, params.vision_range, params.max_moves, params.wall_density, params.sigma):
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
            if sim_task:
                sim_task.cancel()
        except Exception:
            pass


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
