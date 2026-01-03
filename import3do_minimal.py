import bpy
import bmesh
import math
import mathutils

from . import model3doLoader
# NÃO importamos Model3do / Mesh3do diretamente para evitar ciclos


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _set_obj_rotation(obj, rotation):
    """Aplica rotação do 3DO no objeto Blender."""
    # rotation vem como (pitch, yaw, roll); aqui interpretamos como Euler XYZ
    euler = mathutils.Euler(rotation, 'XYZ')
    obj.rotation_euler = euler


def _set_obj_pivot(obj, pivot):
    """Move a malha para compensar o pivot do 3DO."""
    pvec = mathutils.Vector(pivot)
    if obj.type == 'MESH' and obj.data is not None and pvec.length > 0:
        obj.data.transform(mathutils.Matrix.Translation(pvec))


def compute_orientation_fix(obj):
    """
    Deteta bones/objetos invertidos e calcula uma correção (em radianos)
    para manter eixos coerentes. Esta correção é pensada para ser aplicada:
    - aqui no objeto
    - e também nos keyframes (no importador KEY)
    """
    if obj.type not in {'EMPTY', 'MESH'}:
        return (0.0, 0.0, 0.0)

    # Matriz local (somente rotação)
    mat = obj.matrix_local.to_3x3()

    # Eixo Z local (deve apontar "para cima" em muitos rigs)
    z_axis = mat @ mathutils.Vector((0, 0, 1))

    fix_x = 0.0
    fix_y = 0.0
    fix_z = 0.0

    # Regra simples: se Z local estiver apontado para baixo, roda 180° em X
    if z_axis.z < 0.0:
        fix_x = math.pi

    # (Opcional) podes adicionar mais regras, por ex. eixo Y invertido, etc.
    # y_axis = mat @ mathutils.Vector((0, 1, 0))
    # if y_axis.y < 0.0:
    #     fix_z = math.pi

    return (fix_x, fix_y, fix_z)


def apply_orientation_fix_to_obj(obj, fix):
    """Aplica a correção de orientação (Euler XYZ) ao objeto."""
    fx, fy, fz = fix
    if fx != 0.0:
        obj.rotation_euler.rotate_axis('X', fx)
    if fy != 0.0:
        obj.rotation_euler.rotate_axis('Y', fy)
    if fz != 0.0:
        obj.rotation_euler.rotate_axis('Z', fz)


# ------------------------------------------------------------
# Mesh creation (geometry only)
# ------------------------------------------------------------

def _make_mesh(mesh3do, uvAbsolute: bool, vertexColors: bool):
    """Cria uma mesh Blender a partir de Mesh3do, sem materiais."""
    mesh = bpy.data.meshes.new(mesh3do.name)

    # Faces: lista de listas de índices de vértice
    faces = [face.vertexIdxs for face in mesh3do.faces]

    # Cria geometria
    mesh.from_pydata(mesh3do.vertices, [], faces)

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()

    # Layers opcionais
    vert_color_layer = bm.loops.layers.color.verify()
    uv_layer = bm.loops.layers.uv.verify()

    # Preenche dados
    for face in bm.faces:
        face3do = mesh3do.faces[face.index]

        # Normal da face
        face.normal = mathutils.Vector(face3do.normal)

        for loop_idx, loop in enumerate(face.loops):
            vidx = loop.vert.index

            # Normal de vértice
            if vidx < len(mesh3do.normals):
                loop.vert.normal = mathutils.Vector(mesh3do.normals[vidx])

            # Vertex Colors
            if vertexColors and vidx < len(mesh3do.vertexColors):
                r, g, b, a = mesh3do.vertexColors[vidx]
                loop[vert_color_layer] = (r, g, b, a)

            # UVs
            if loop_idx < len(face3do.uvIdxs):
                uv_idx = face3do.uvIdxs[loop_idx]
                if 0 <= uv_idx < len(mesh3do.uvs):
                    u, v = mesh3do.uvs[uv_idx]
                    # Infernal Machine costuma ter V invertido
                    loop[uv_layer].uv = (u, -v if not uvAbsolute else v)

    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    return mesh


# ------------------------------------------------------------
# Object creation
# ------------------------------------------------------------

def _create_objects_from_model(model, uvAbsolute: bool,
                               geosetNum: int, vertexColors: bool):

    meshes = model.geosets[geosetNum].meshes

    # Cria objetos para cada node da hierarquia
    for node in model.meshHierarchy:
        meshIdx = node.meshIdx

        if meshIdx > -1:
            mesh3do = meshes[meshIdx]
            mesh = _make_mesh(mesh3do, uvAbsolute, vertexColors)
            obj = bpy.data.objects.new(mesh3do.name, mesh)
        else:
            obj = bpy.data.objects.new(node.name, None)

        bpy.context.scene.collection.objects.link(obj)

        # Pivot, posição, rotação base do 3DO
        _set_obj_pivot(obj, node.pivot)
        obj.location = node.position
        _set_obj_rotation(obj, node.rotation)

        # --------------------------------------------------------
        # Correção automática de bones/objetos invertidos
        # --------------------------------------------------------
        fix = compute_orientation_fix(obj)
        apply_orientation_fix_to_obj(obj, fix)
        node.orientationFix = fix  # guarda para o importador KEY

        node.obj = obj

    # Define parenting pela hierarquia
    for node in model.meshHierarchy:
        if node.parentIdx != -1:
            node.obj.parent = model.meshHierarchy[node.parentIdx].obj


# ------------------------------------------------------------
# Main importer (minimal)
# ------------------------------------------------------------

def import3do_minimal(file_path,
                      uvAbsolute_2_1=True,
                      importVertexColors=True,
                      clearScene=True):
    """
    Importador minimalista:
    - Sem materiais
    - Sem texturas
    - Sem ColorMap
    - Sem radius
    - Sem grupos
    - Apenas geometria + hierarquia
    """

    print(f"Importando 3DO minimalista: {file_path}")

    # Limpa cena
    if clearScene:
        bpy.ops.wm.read_homefile(use_empty=True)

    # Carrega modelo
    model, fileVersion = model3doLoader.load3do(file_path)

    # Loader é de Infernal Machine (3DO 2.3), tratamos como não-JKDF2
    isJkdf2 = False

    if len(model.geosets) == 0:
        print("Nada para importar: modelo sem geosets.")
        return None

    # Cria objetos
    _create_objects_from_model(
        model,
        uvAbsolute=(isJkdf2 and uvAbsolute_2_1),
        geosetNum=0,
        vertexColors=importVertexColors
    )

    # Cria objeto base
    baseObj = bpy.data.objects.new(model.name, None)
    bpy.context.scene.collection.objects.link(baseObj)

    # Usa insertOffset do modelo como posição base
    if hasattr(model, "insertOffset"):
        baseObj.location = model.insertOffset

    # Parent do primeiro nó
    if model.meshHierarchy:
        firstChild = model.meshHierarchy[0].obj
        firstChild.parent = baseObj

    print("Importação minimalista concluída.")
    return baseObj