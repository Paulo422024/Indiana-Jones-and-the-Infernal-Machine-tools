import bpy
from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator, Panel
import os

# Importa o importer minimalista
from .import3do_minimal import import3do_minimal


# ------------------------------------------------------------
# Operador: Importar 3DO Minimal
# ------------------------------------------------------------

class IMPORT_OT_3DO_Minimal(Operator):
    bl_idname = "import_scene.3do_minimal"
    bl_label = "Importar 3DO (Minimal)"
    bl_description = "Importa um arquivo 3DO usando o importador minimalista"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(
        name="Arquivo 3DO",
        description="Selecione o arquivo .3do",
        subtype='FILE_PATH'
    )

    clear_scene: BoolProperty(
        name="Limpar Cena",
        default=True,
        description="Limpa a cena antes de importar"
    )

    import_vertex_colors: BoolProperty(
        name="Importar Vertex Colors",
        default=True
    )

    def execute(self, context):
        if not self.filepath.lower().endswith(".3do"):
            self.report({'ERROR'}, "Selecione um arquivo .3do válido")
            return {'CANCELLED'}

        import3do_minimal(
            self.filepath,
            uvAbsolute_2_1=True,
            importVertexColors=self.import_vertex_colors,
            clearScene=self.clear_scene
        )

        # Guardar caminho do modelo para auto-detecção de KEY
        from .model3doLoader import last_loaded_model
        if last_loaded_model:
            last_loaded_model.filepath = self.filepath

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


# ------------------------------------------------------------
# Operador: Importar KEY Animation
# ------------------------------------------------------------

class IMPORT_OT_KEY_Panel(Operator):
    bl_idname = "import_scene.sith_key_panel"
    bl_label = "Importar KEY Animation"
    bl_description = "Importa um arquivo KEY e aplica ao modelo 3DO carregado"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(
        name="Arquivo KEY",
        description="Selecione o arquivo .key",
        subtype='FILE_PATH'
    )

    def execute(self, context):
        from .model3doLoader import last_loaded_model
        from .keyImporter import import_key

        model = last_loaded_model

        if model is None:
            self.report({'ERROR'}, "Nenhum modelo 3DO carregado. Importe um 3DO primeiro.")
            return {'CANCELLED'}

        import_key(self.filepath, model)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


# ------------------------------------------------------------
# Painel no Blender (tecla N)
# ------------------------------------------------------------

class VIEW3D_PT_Import3DOMinimal(Panel):
    bl_label = "Importar 3DO + KEY"
    bl_idname = "VIEW3D_PT_import_3do_minimal"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "3DO + Key"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        # -------------------------
        # Importar 3DO
        # -------------------------
        col.label(text="Importação Minimalista")
        col.operator("import_scene.3do_minimal", text="Importar 3DO (Minimal)")

        col.separator()

        # -------------------------
        # Pasta manual para animações
        # -------------------------
        scene = context.scene

        if not hasattr(scene, "sith_anim_folder"):
            scene.sith_anim_folder = ""

        col.label(text="Pasta das animações (opcional):")
        col.prop(scene, "sith_anim_folder", text="")

        col.separator()

        # -------------------------
        # Auto-detecção de KEY
        # -------------------------
        col.label(text="Importar Animação")

        from .model3doLoader import last_loaded_model
        model = last_loaded_model

        if model is None:
            col.label(text="Nenhum 3DO carregado.", icon="ERROR")
            return

        # 1) Se o utilizador definiu pasta manual → usar essa
        manual_folder = scene.sith_anim_folder.strip()
        search_folder = None

        if manual_folder and os.path.isdir(manual_folder):
            search_folder = manual_folder
        else:
            # 2) Caso contrário → usar a pasta do 3DO
            model_path = getattr(model, "filepath", None)
            if model_path:
                search_folder = os.path.dirname(model_path)

        if not search_folder:
            col.label(text="Não foi possível determinar a pasta.", icon="ERROR")
            return

        base = os.path.splitext(os.path.basename(model.filepath))[0]

        key_candidates = [
            f for f in os.listdir(search_folder)
            if f.lower().startswith(base.lower()) and f.lower().endswith(".key")
        ]

        if not key_candidates:
            col.label(text="Nenhuma animação encontrada.", icon="INFO")
            col.operator("import_scene.sith_key_panel", text="Importar KEY manualmente")
            return

        col.label(text="Animações encontradas:")

        for keyfile in key_candidates:
            op = col.operator("import_scene.sith_key_panel", text=keyfile)
            op.filepath = os.path.join(search_folder, keyfile)


# ------------------------------------------------------------
# Registro
# ------------------------------------------------------------

classes = (
    IMPORT_OT_3DO_Minimal,
    IMPORT_OT_KEY_Panel,
    VIEW3D_PT_Import3DOMinimal,
)

def register():
    bpy.types.Scene.sith_anim_folder = StringProperty(
        name="Pasta de Animações",
        description="Pasta onde estão os arquivos KEY",
        subtype='DIR_PATH',
        default=""
    )

    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    del bpy.types.Scene.sith_anim_folder

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)