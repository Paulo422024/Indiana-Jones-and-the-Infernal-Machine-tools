# model.py — substituto minimalista do antigo sith.model

from enum import IntEnum, unique

@unique
class Mesh3doNodeType(IntEnum):
    Nothing = 0
    Mesh = 1
    Light = 2
    Sound = 3
    Frame = 4