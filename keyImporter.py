import bpy
import mathutils

from .keyLoader import load_key


# ------------------------------------------------------------
# Importa animação KEY para objetos já criados pelo importer 3DO
# ------------------------------------------------------------

def import_key(filepath: str, model):
    print(f"Importando animação KEY: {filepath}")

    key = load_key(filepath)

    # Criar SEMPRE uma nova Action (evita mistura de animações)
    action_name = f"{key.name}_Action"
    action = bpy.data.actions.new(name=action_name)

    # Definir range da timeline
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = key.numFrames - 1

    # Para cada node do KEY, aplicar animação ao objeto correspondente
    for node in key.nodes:

        if node.idx >= len(model.meshHierarchy):
            print(f"Node {node.idx} fora da hierarquia, ignorado.")
            continue

        mesh_node = model.meshHierarchy[node.idx]
        obj = mesh_node.obj

        if obj is None:
            print(f"Node {node.idx} sem objeto, ignorado.")
            continue

        # ------------------------------------------------------------
        # LIMPAR ANIMAÇÃO ANTIGA DO OBJETO
        # ------------------------------------------------------------
        if obj.animation_data:
            obj.animation_data_clear()

        obj.animation_data_create()
        obj.animation_data.action = action

        # Correção de orientação calculada no importador 3DO
        fix = getattr(mesh_node, "orientationFix", (0.0, 0.0, 0.0))
        fx, fy, fz = fix

        # Inserir keyframes
        for kf in node.keyframes:
            frame = kf.frame

            # Posição
            obj.location = mathutils.Vector((
                kf.position.x,
                kf.position.y,
                kf.position.z
            ))
            obj.keyframe_insert(data_path="location", frame=frame)

            # Orientações no KEY: (pitch, yaw, roll)
            p = kf.orientation.x
            y = kf.orientation.y
            r = kf.orientation.z

            # Remapeamento para Blender
            rx = p
            ry = r
            rz = y

            # Correção de orientação do 3DO
            rx += fx
            ry += fy
            rz += fz

            obj.rotation_euler = mathutils.Euler((rx, ry, rz), 'XYZ')
            obj.keyframe_insert(data_path="rotation_euler", frame=frame)

    # Aplicar Action ao objeto base
    base = bpy.data.objects.get(model.name)
    if base:
        if base.animation_data:
            base.animation_data_clear()
        base.animation_data_create()
        base.animation_data.action = action

    print("Importação KEY concluída.")
    return action