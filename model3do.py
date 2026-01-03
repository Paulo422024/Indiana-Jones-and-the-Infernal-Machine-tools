# ------------------------------------------------------------
# Tipos simples (aceitam qualquer número do 3DO)
# ------------------------------------------------------------

class GeometryMode(int):
    pass

class LightMode(int):
    pass

class TextureMode(int):
    pass

class FaceType(int):
    pass

class Mesh3doNodeFlags(int):
    pass

class Mesh3doNodeType(int):
    pass


# ------------------------------------------------------------
# Estruturas de dados do modelo 3DO
# ------------------------------------------------------------

class Mesh3doFace:
    def __init__(self):
        self.materialIdx = -1
        self.type = FaceType(0)
        self.geometryMode = GeometryMode(0)
        self.lightMode = LightMode(0)
        self.textureMode = TextureMode(0)

        self.color = (1.0, 1.0, 1.0, 1.0)

        self.vertexIdxs = []
        self.uvIdxs = []
        self.normal = (0.0, 0.0, 0.0)


class Mesh3do:
    def __init__(self, idx, name):
        self.idx = idx
        self.name = name

        self.radius = 0.0

        self.geometryMode = GeometryMode(0)
        self.lightMode = LightMode(0)
        self.textureMode = TextureMode(0)

        self.vertices = []
        self.vertexColors = []
        self.uvs = []
        self.normals = []
        self.faces = []


class Model3doGeoSet:
    def __init__(self):
        self.meshes = []


class Mesh3doNode:
    def __init__(self):
        self.idx = 0
        self.flags = Mesh3doNodeFlags(0)
        self.type = Mesh3doNodeType(0)

        self.meshIdx = -1
        self.parentIdx = -1
        self.firstChildIdx = -1
        self.siblingIdx = -1
        self.numChildren = 0

        self.position = (0.0, 0.0, 0.0)
        self.rotation = (0.0, 0.0, 0.0)
        self.pivot = (0.0, 0.0, 0.0)

        self.name = ""
        self.obj = None


class Model3do:
    def __init__(self, name):
        self.name = name
        self.radius = 0.0
        self.insertOffset = (0.0, 0.0, 0.0)

        self.materials = []
        self.geosets = []
        self.meshHierarchy = []