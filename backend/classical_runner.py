from tensorflow.keras import Sequential, layers
from collections import Counter
import numpy as np

class ClassicalRunner:
    def __init__(self, weights=None):
        self.model = Sequential([
            layers.Input(shape=(3,)),
            layers.Dense(8, activation="tanh"),
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
        # Normalize vision
        x = np.array([
            vision[0] / 2.0,
            vision[1] / 2.0,
            vision[2] / 2.0,
        ], dtype=np.float32)

        logits = self.model(x[None, :], training=False).numpy()[0]

        return int(np.argmax(logits))

    def get_weights(self):
        return self.model.get_weights()


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
    for vision in [(0, 0, 0), (1, 0, 0), (2, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (1, 0, 1), (0, 1, 1), (2, 2, 2)]:
        actions = [runner.get_action(vision) for _ in range(100)]
        print(f"{vision} -", Counter(actions))
