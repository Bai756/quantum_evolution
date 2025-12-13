import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from environment import Environment, Creature

class CreatureData(BaseModel):
    angles: List[float]
    pos: List[int]
    orientation: int
    fruits_eaten: int
    grid: List[List[int]]

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


@app.get("/creature", response_model=CreatureData)
def get_creature(idx: int = 0):
    angles = [[0.0, 1.305084939618391, 3.1416, 3.4405219230155755, -0.05782300140385274, 3.752734189104716], [0.03378434831137653, 1.441234729740852, 3.096222841904588, 3.5313561482881033, 0.1135670575082236, 3.6652],
              [0.03378434831137653, 1.441234729740852, 3.096222841904588, 3.5313561482881033, -0.12436814333957848, 3.6652]]

    creature = Creature(angles[0])
    env = Environment(creature)
    env.generate_food()

    fruits_eaten = creature.food_eaten

    return CreatureData(
        angles=list(creature.angles),
        pos=list(creature.pos),
        orientation=int(creature.orientation),
        fruits_eaten=int(fruits_eaten),
        grid=env.grid
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
