from tensorflow.keras import Sequential, layers
from collections import Counter
import numpy as np

class ClassicalRunner:
    def __init__(self, weights=None):
        self.model = Sequential([
            layers.Input(shape=(3,)),
            layers.Dense(32, activation="relu"),
            layers.Dense(32, activation="relu"),
            layers.Dense(4, activation="linear"),
        ])

        if weights:
            self.model.set_weights(weights)
        else:
            self._randomize_weights()

    def _randomize_weights(self):
        weights = []
        for w in self.model.get_weights():
            weights.append(
                np.random.uniform(-1.0, 1.0, size=w.shape)
            )
        self.model.set_weights(weights)

    def get_action(self, vision):
        x = np.asarray(vision, dtype=np.float32).reshape(1, -1)
        probs = self.model(x, training=False).numpy()[0]

        return int(np.argmax(probs))

    def get_weights(self):
        return self.model.get_weights()

def weights_to_json(weights):
    def r(x):
        return float(round(float(x), 2))

    out_layers = []
    for w in weights:
        arr = np.asarray(w)
        if arr.ndim == 1:
            # if 1d array, just output a list
            shape = [int(arr.shape[0]),]
            weights_list = [r(x) for x in arr.tolist()]
            out_layers.append({"shape": shape, "weights": weights_list})
        elif arr.ndim == 2:
            # if 2d array, output list of lists
            shape = [int(arr.shape[0]), int(arr.shape[1])]
            weights_list = [[r(x) for x in row] for row in arr.tolist()]
            out_layers.append({"shape": shape, "weights": weights_list})

    return {"layers": out_layers}


if __name__ == "__main__":
    file_path = "best_classical_weights.txt"
    with open(file_path, "r") as f:
        weights = []
        current_weight = []
        for line in f:
            line = line.strip()
            if line == "---":
                if current_weight:
                    arr = np.array(current_weight, dtype=float)
                    if arr.ndim == 2 and arr.shape[0] == 1:
                        arr = arr.flatten()
                    weights.append(arr)
                    current_weight = []
            else:
                if line:
                    current_weight.append([float(x) for x in line.split(",")])

        if current_weight:
            arr = np.array(current_weight, dtype=float)
            if arr.ndim == 2 and arr.shape[0] == 1:
                arr = arr.flatten()
            weights.append(arr)

    runner = ClassicalRunner(weights=weights)
    print(weights_to_json(runner.get_weights()))
    # for vision in [(0, 0, 0), (1, 0, 0), (2, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (1, 0, 1), (0, 1, 1), (2, 2, 2)]:
    #     actions = [runner.get_action(vision) for _ in range(100)]
    #     print(f"{vision} -", Counter(actions))
