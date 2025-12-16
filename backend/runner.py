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
    print("start")
    runner = ClassicalRunner(weights=[[-0.98467565, -0.7568704 ,  0.49763608, -0.7747624 , -0.4939476 ,
        -0.40649942,  0.4878192 , -0.38594908],
       [ 0.50112903, -1.0577985 ,  0.7714104 ,  0.45268178, -0.23736063,
         0.01158876,  0.8222665 , -0.3842181 ],
       [ 0.76227695, -1.0852277 ,  0.10910174, -1.138058  ,  0.41732997,
         0.10171562,  0.6722212 , -0.91750693]])
    print("loaded")
    for vision in [(0, 0, 0), (1, 0, 0), (2, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (1, 0, 1), (0, 1, 1), (2, 2, 2)]:
        actions = [runner.get_action(vision) for _ in range(100)]
        print(f"{vision} -", Counter(actions))



