# types.py — substituto minimalista do antigo sith.types

from enum import IntFlag


class Flag(IntFlag):
    """Wrapper de flags bitwise baseado em IntFlag."""
    pass


class Vector3f:
    """Vetor 3D simples usado pelo loader KEY e 3DO."""
    __slots__ = ("x", "y", "z")

    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __repr__(self):
        return f"Vector3f({self.x}, {self.y}, {self.z})"