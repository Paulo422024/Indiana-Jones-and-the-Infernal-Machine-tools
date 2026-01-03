bl_info = {
    "name": "Sith 3DO + KEY Minimal Importer",
    "author": "PauloRetro 2026",
    "version": (1, 1, 0),
    "blender": (4, 5, 0),
    "location": "View3D > N-panel > 3DO, File > Import/Export",
    "description": "Importador minimalista de arquivos 3DO e animações KEY do Indiana Jones and the Infernal Machine",
    "category": "Import-Export",
}

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

# UI do importador 3DO
from . import import3do_minimal_ui

# Importadores KEY
from . import keyImporter
from . import keyLoader


# ------------------------------------------------------------
# Operador: Importar KEY Animation
# ------------------------------------------------------------

class IMPORT_OT_KEY(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.sith_key"
    bl_label = "Import KEY Animation (Infernal Machine)"
    bl_options = {'UNDO'}

    filename_ext = ".key"
    filter_glob: StringProperty(default="*.key", options={'HIDDEN'})

    def execute(self, context):
        from .model3doLoader import last_loaded_model
        model = last_loaded_model

        if model is None:
            self.report({'ERROR'}, "Nenhum modelo 3DO carregado. Importe um 3DO primeiro.")
            return {'CANCELLED'}

        keyImporter.import_key(self.filepath, model)
        return {'FINISHED'}




# ------------------------------------------------------------
# Menus
# ------------------------------------------------------------

def menu_func_import(self, context):
    self.layout.operator(IMPORT_OT_KEY.bl_idname, text="Sith KEY Animation (.key)")


# ------------------------------------------------------------
# Registro
# ------------------------------------------------------------

classes = (
    IMPORT_OT_KEY,    
)

def register():
    import3do_minimal_ui.register()

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)   

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)    

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    import3do_minimal_ui.unregister()


if __name__ == "__main__":
    register()