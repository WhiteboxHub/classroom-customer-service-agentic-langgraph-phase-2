import random

class ChaosMonkey:
    """
    Simulates API failures (500s) to test recovery loops [cite: 991]
    """
    @staticmethod
    def maybe_fail(probability: float = 0.2):
        if random.random() < probability:
            raise Exception("Chaos Monkey: Simulated 500 Error")
