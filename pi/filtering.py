import numpy as np

"""
NOTE:
Insert new value at the beginning, leave last value out
"""

class MovingAverage:
    buffer: list[ float ]
    output: float
    size: int

    def __init__(self, size: int = 15):
        self.buffer = [0.0 for _ in range(size)]
        self.output = 0
        self.size = size

    def update(self, newval: float) -> None:
        # assert not hasattr(newval, len)
        self.buffer = [newval, *self.buffer[:-1]]

        # print(self.buffer)

        self.output = sum(self.buffer) / len(self.buffer)
        return self.output
