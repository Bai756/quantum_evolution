import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from environment import Environment, Creature
from simulate import evolution

class CreatureSnapshot(BaseModel):
    angles: List[float]
    pos: List[int]
    orientation: int
    food_eaten: int
    grid: List[List[int]]

def creature_to_snapshot(creature: Creature, env: Environment):
    return CreatureSnapshot(
        angles=list(creature.angles),
        pos=list(creature.pos),
        orientation=int(creature.orientation),
        food_eaten=int(creature.food_eaten),
        grid=env.grid
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
    angles = [[0.0, 1.305084939618391, 3.1416, 3.4405219230155755, -0.05782300140385274, 3.752734189104716], [0.03378434831137653, 1.441234729740852, 3.096222841904588, 3.5313561482881033, 0.1135670575082236, 3.6652],
              [0.03378434831137653, 1.441234729740852, 3.096222841904588, 3.5313561482881033, -0.12436814333957848, 3.6652]]

    creature = Creature(angles[0])
    env = Environment(creature)
    env.generate_food()

    return creature_to_snapshot(creature, env)


@app.post("/run_evolution", response_model=EvolutionResult)
def run_evolution(params: RunParams):
    elites = evolution(params.generations, params.children, params.chance, params.repeats, params.elites)
    return EvolutionResult(elites=elites)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
