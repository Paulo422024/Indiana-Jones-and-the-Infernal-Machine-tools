from .tokenizer import Tokenizer, TokenType
from .model3do import (
    Model3do,
    Mesh3do,
    Mesh3doFace,
    Model3doGeoSet,
    Mesh3doNode,
    GeometryMode,
    LightMode,
    TextureMode,
    FaceType,
)

# Guarda o último modelo carregado para o importador KEY
last_loaded_model = None


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _expect_section(tok: Tokenizer, expected_name: str):
    t = tok.getToken()
    if not (t.type == TokenType.Identifier and t.value.upper() == "SECTION"):
        raise AssertionError(f"Expected 'SECTION', got {t}")
    t = tok.getToken()
    if not (t.type == TokenType.Punctuator and t.value == ":"):
        raise AssertionError(f"Expected ':', got {t}")
    t = tok.getToken()
    if t.type != TokenType.Identifier:
        raise AssertionError(f"Expected section name, got {t}")
    if t.value.upper() != expected_name.upper():
        raise AssertionError(f"Expected SECTION: {expected_name}, got SECTION: {t.value}")


# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------

def _parse_header(tok: Tokenizer, model: Model3do):
    _expect_section(tok, "HEADER")

    t = tok.getIdentifier()

    if t.isdigit():
        major = int(t)
        ident = tok.getIdentifier()
        if ident.upper() != "DO":
            raise AssertionError(f"Expected 'DO', got {ident}")
    else:
        if t.upper().endswith("DO") and t[:-2].isdigit():
            major = int(t[:-2])
        else:
            raise AssertionError(f"Expected '3 DO' or '3DO', got {t}")

    minor = tok.getFloatNumber()
    model.version = major + minor


# ------------------------------------------------------------
# MODELRESOURCE
# ------------------------------------------------------------

def _parse_modelresource(tok: Tokenizer, model: Model3do):
    _expect_section(tok, "MODELRESOURCE")

    tok.assertIdentifier("MATERIALS")
    num_materials = tok.getIntNumber()

    for _ in range(num_materials):
        idx = tok.getIntNumber()
        tok.assertPunctuator(':')
        name = tok.getSpaceDelimitedString()
        model.materials.append(name)


# ------------------------------------------------------------
# GEOMETRYDEF
# ------------------------------------------------------------

def _parse_geometrydef(tok: Tokenizer, model: Model3do):
    _expect_section(tok, "GEOMETRYDEF")

    tok.assertIdentifier("RADIUS")
    model.radius = tok.getFloatNumber()

    tok.assertIdentifier("INSERT")
    tok.assertIdentifier("OFFSET")
    ix = tok.getFloatNumber()
    iy = tok.getFloatNumber()
    iz = tok.getFloatNumber()
    model.insertOffset = (ix, iy, iz)

    tok.assertIdentifier("GEOSETS")
    num_geosets = tok.getIntNumber()

    for _ in range(num_geosets):
        tok.assertIdentifier("GEOSET")
        geoset_idx = tok.getIntNumber()

        geoset = Model3doGeoSet()
        model.geosets.append(geoset)

        tok.assertIdentifier("MESHES")
        num_meshes = tok.getIntNumber()

        for _m in range(num_meshes):
            _parse_mesh_block(tok, geoset)


# ------------------------------------------------------------
# MESH BLOCK
# ------------------------------------------------------------

def _parse_mesh_block(tok: Tokenizer, geoset: Model3doGeoSet):
    tok.assertIdentifier("MESH")
    mesh_idx = tok.getIntNumber()

    tok.assertIdentifier("NAME")
    name = tok.getSpaceDelimitedString()

    mesh = Mesh3do(mesh_idx, name)
    geoset.meshes.append(mesh)

    tok.assertIdentifier("RADIUS")
    mesh.radius = tok.getFloatNumber()

    tok.assertIdentifier("GEOMETRYMODE")
    mesh.geometryMode = GeometryMode(tok.getIntNumber())

    tok.assertIdentifier("LIGHTINGMODE")
    mesh.lightMode = LightMode(tok.getIntNumber())

    tok.assertIdentifier("TEXTUREMODE")
    mesh.textureMode = TextureMode(tok.getIntNumber())

    _parse_mesh_geometry(tok, mesh)


# ------------------------------------------------------------
# Helper: parse EXTRALIGHT color
# ------------------------------------------------------------

def _parse_face_color(tok: Tokenizer):
    t = tok.peekToken()
    if t.type == TokenType.Punctuator and t.value == '(':
        tok.getToken()

    def _read_component():
        t = tok.peekToken()
        while t.type == TokenType.Punctuator and t.value in ('/', ',', ')'):
            tok.getToken()
            t = tok.peekToken()
        return tok.getFloatNumber()

    r = _read_component()
    g = _read_component()
    b = _read_component()
    a = _read_component()

    t = tok.peekToken()
    if t.type == TokenType.Punctuator and t.value == ')':
        tok.getToken()

    return (r, g, b, a)


# ------------------------------------------------------------
# MESH GEOMETRY
# ------------------------------------------------------------

def _parse_mesh_geometry(tok: Tokenizer, mesh: Mesh3do):

    tok.assertIdentifier("VERTICES")
    num_verts = tok.getIntNumber()

    for _ in range(num_verts):
        vidx = tok.getIntNumber()
        tok.assertPunctuator(':')

        x = tok.getFloatNumber()
        y = tok.getFloatNumber()
        z = tok.getFloatNumber()
        r = tok.getFloatNumber()
        g = tok.getFloatNumber()
        b = tok.getFloatNumber()
        a = tok.getFloatNumber()

        mesh.vertices.append((x, y, z))
        mesh.vertexColors.append((r, g, b, a))

    tok.assertIdentifier("TEXTURE")
    tok.assertIdentifier("VERTICES")
    num_uvs = tok.getIntNumber()

    for _ in range(num_uvs):
        uidx = tok.getIntNumber()
        tok.assertPunctuator(':')
        u = tok.getFloatNumber()
        v = tok.getFloatNumber()
        mesh.uvs.append((u, v))

    tok.assertIdentifier("VERTEX")
    tok.assertIdentifier("NORMALS")

    for _ in range(num_verts):
        nidx = tok.getIntNumber()
        tok.assertPunctuator(':')
        nx = tok.getFloatNumber()
        ny = tok.getFloatNumber()
        nz = tok.getFloatNumber()
        mesh.normals.append((nx, ny, nz))

    tok.assertIdentifier("FACES")
    num_faces = tok.getIntNumber()

    for _ in range(num_faces):
        fidx = tok.getIntNumber()
        tok.assertPunctuator(':')

        face = Mesh3doFace()

        face.materialIdx = tok.getIntNumber()
        face.type = FaceType(tok.getIntNumber())
        face.geometryMode = GeometryMode(tok.getIntNumber())
        face.lightMode = LightMode(tok.getIntNumber())
        face.textureMode = TextureMode(tok.getIntNumber())

        col = _parse_face_color(tok)
        face.color = col

        num_face_verts = tok.getIntNumber()

        for _fv in range(num_face_verts):
            t = tok.peekToken()
            while t.type == TokenType.Punctuator and t.value in (')', '(', ']'):
                tok.getToken()
                t = tok.peekToken()

            v_idx = tok.getIntNumber()

            t = tok.peekToken()
            while t.type == TokenType.Punctuator and t.value in (')', '(', ']'):
                tok.getToken()
                t = tok.peekToken()

            tok.assertPunctuator(',')

            t = tok.peekToken()
            while t.type == TokenType.Punctuator and t.value in (')', '(', ']'):
                tok.getToken()
                t = tok.peekToken()

            uv_idx = tok.getIntNumber()

            face.vertexIdxs.append(v_idx)
            face.uvIdxs.append(uv_idx)

        mesh.faces.append(face)

    tok.assertIdentifier("FACE")
    tok.assertIdentifier("NORMALS")

    for _ in range(num_faces):
        fn_idx = tok.getIntNumber()
        tok.assertPunctuator(':')
        nx = tok.getFloatNumber()
        ny = tok.getFloatNumber()
        nz = tok.getFloatNumber()
        mesh.faces[fn_idx].normal = (nx, ny, nz)


# ------------------------------------------------------------
# HIERARCHYDEF
# ------------------------------------------------------------

def _parse_hierarchydef(tok: Tokenizer, model: Model3do):
    _expect_section(tok, "HIERARCHYDEF")

    tok.assertIdentifier("HIERARCHY")
    tok.assertIdentifier("NODES")
    num_nodes = tok.getIntNumber()

    for _ in range(num_nodes):
        node = Mesh3doNode()

        node.idx = tok.getIntNumber()
        tok.assertPunctuator(':')

        node.flags = tok.getIntNumber()
        node.type = tok.getIntNumber()

        node.meshIdx = tok.getIntNumber()
        node.parentIdx = tok.getIntNumber()
        node.firstChildIdx = tok.getIntNumber()
        node.siblingIdx = tok.getIntNumber()
        node.numChildren = tok.getIntNumber()

        px = tok.getFloatNumber()
        py = tok.getFloatNumber()
        pz = tok.getFloatNumber()
        node.position = (px, py, pz)

        pitch = tok.getFloatNumber()
        yaw = tok.getFloatNumber()
        roll = tok.getFloatNumber()
        node.rotation = (pitch, yaw, roll)

        pvx = tok.getFloatNumber()
        pvy = tok.getFloatNumber()
        pvz = tok.getFloatNumber()
        node.pivot = (pvx, pvy, pvz)

        node.name = tok.getIdentifier()

        model.meshHierarchy.append(node)


# ------------------------------------------------------------
# LOAD 3DO
# ------------------------------------------------------------

def load3do(filepath):
    global last_loaded_model

    with open(filepath, "r", encoding="latin-1") as f:
        tok = Tokenizer(f)

        model = Model3do("")

        _parse_header(tok, model)
        _parse_modelresource(tok, model)
        _parse_geometrydef(tok, model)

        try:
            _parse_hierarchydef(tok, model)
        except AssertionError:
            pass

        if not model.name:
            if model.meshHierarchy:
                model.name = model.meshHierarchy[-1].name
            elif model.geosets and model.geosets[0].meshes:
                model.name = model.geosets[0].meshes[0].name
            else:
                model.name = "Model3DO"

        last_loaded_model = model

        return model, 0