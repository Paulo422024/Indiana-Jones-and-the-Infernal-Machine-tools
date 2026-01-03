from enum import IntEnum, unique
from typing import List

from .types import Flag, Vector3f
from .model import Mesh3doNodeType


@unique
class KeyFlag(Flag):
    Loop              = 0x0
    UsePuppetFPS      = 0x1
    NoLoop            = 0x2
    PauseOnLastFrame  = 0x4
    RestartActive     = 0x8
    DisableFadeIn     = 0x10
    FadeOutAndNoLoop  = 0x20


@unique
class KeyframeFlag(IntEnum):
    NoChange          = 0
    PositionChange    = 1
    OrientationChange = 2
    AllChange         = 3


class Keyframe:
    def __init__(self):
        self.f = KeyframeFlag.NoChange
        self.frme = 0
        self.pos = Vector3f()
        self.orien = Vector3f()
        self.dpos = Vector3f()
        self.drot = Vector3f()

    @property
    def flags(self): return self.f
    @flags.setter
    def flags(self, v): self.f = v

    @property
    def frame(self): return self.frme
    @frame.setter
    def frame(self, v): self.frme = v

    @property
    def position(self): return self.pos
    @position.setter
    def position(self, v): self.pos = v

    @property
    def orientation(self): return self.orien
    @orientation.setter
    def orientation(self, v): self.orien = v

    @property
    def deltaPosition(self): return self.dpos
    @deltaPosition.setter
    def deltaPosition(self, v): self.dpos = v

    @property
    def deltaRotation(self): return self.drot
    @deltaRotation.setter
    def deltaRotation(self, v): self.drot = v


class KeyNode:
    def __init__(self):
        self.n = 0
        self.mesh_name = ""
        self.kfs = []

    @property
    def idx(self): return self.n
    @idx.setter
    def idx(self, v): self.n = v

    @property
    def meshName(self): return self.mesh_name
    @meshName.setter
    def meshName(self, v): self.mesh_name = v

    @property
    def keyframes(self): return self.kfs
    @keyframes.setter
    def keyframes(self, v): self.kfs = v


class Key:
    def __init__(self, name):
        self.n = name
        self.f = KeyFlag.Loop
        self.t = Mesh3doNodeType.Nothing
        self.frames = 0
        self.nfps = 0.0
        self.joints = 0
        self.m = []
        self.n = []

    @property
    def name(self): return self.n
    @name.setter
    def name(self, v): self.n = v

    @property
    def flags(self): return self.f
    @flags.setter
    def flags(self, v): self.f = v

    @property
    def nodeTypes(self): return self.t
    @nodeTypes.setter
    def nodeTypes(self, v): self.t = v

    @property
    def numFrames(self): return self.frames
    @numFrames.setter
    def numFrames(self, v): self.frames = v

    @property
    def numJoints(self): return self.joints
    @numJoints.setter
    def numJoints(self, v): self.joints = v

    @property
    def fps(self): return self.nfps
    @fps.setter
    def fps(self, v): self.nfps = v

    @property
    def markers(self): return self.m
    @markers.setter
    def markers(self, v): self.m = v

    @property
    def nodes(self): return self.n
    @nodes.setter
    def nodes(self, v): self.n = v