import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from simulate import *
from web_helpers import evolution_iter

class CreatureSnapshot(BaseModel):
    angles: List[float]
    pos: List[int]
    orientation: int
    food_eaten: int
    grid: List[List[int]]
    fitness: float
    generation: int


def creature_to_snapshot(creature: Creature, env: Environment, fitness: float = 0.0, generation: int = 0):
    return CreatureSnapshot(
        angles=list(creature.angles),
        pos=list(creature.pos),
        orientation=int(creature.orientation),
        food_eaten=int(creature.food_eaten),
        grid=env.grid,
        fitness=float(fitness),
        generation=int(generation),
    )


class RunParams(BaseModel):
    generations: int
    children: int
    chance: float
    repeats: int
    elites: int


class EvolutionResult(BaseModel):
    elites: List[List[float]]


app = FastAPI()

# change this later
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
def get_creature(idx: int = 0):
    creature = Creature([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    env = Environment(creature)
    env.generate_food()
    return creature_to_snapshot(creature, env, fitness=0.0, generation=0)


@app.websocket("/ws/evolution")
async def ws_evolution(ws: WebSocket):
    print("WebSocket connection for evolution")
    await ws.accept()
    try:
        init = await ws.receive_json()
        params = RunParams(**init)

        # stream snapshots via evolution_iter
        best_final = None
        async def send_snapshot(gen, creature, fitness):
            env = Environment(creature)
            env.generate_food()
            snap = creature_to_snapshot(creature, env, fitness=fitness, generation=gen)
            await ws.send_json(snap.model_dump())

        for gen, best_creature, best_fitness in evolution_iter(
            params.generations, params.children, params.chance, params.repeats, params.elites
        ):
            await send_snapshot(gen, best_creature, best_fitness)
            best_final = (best_creature, best_fitness)

        # send final best summary
        if best_final is not None:
            creature, fitness = best_final
            await ws.send_json({
                "done": False,
                "best": {
                    "angles": list(creature.angles),
                    "fitness": float(fitness),
                }
            })
            env = Environment(Creature(creature.angles))
            env.generate_food()
            runner = QuantumRunner()
            sim_creature = env.player
            for step in range(10):
                action = runner.get_action(sim_creature.angles)
                env.step(action)
                snap = creature_to_snapshot(sim_creature, env, fitness=fitness, generation=params.generations)
                await ws.send_json({"simulation": True, **snap.model_dump()})

        await ws.send_json({"done": True})
    except WebSocketDisconnect:
        return
    except Exception as exc:
        try:
            await ws.send_json({"error": str(exc)})
        finally:
            await ws.close()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
