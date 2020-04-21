import bpy

class ExporterScene():

    def __init__(self, cameras=[], meshes=[], lamps=[], materials=[]):
        self.meshes = meshes
        self.cameras = cameras
        self.lamps = lamps
        self.materials = materials

class RenderExporter(bpy.types.Operator):
    bl_idname = "export.scene_to_render"
    bl_label = "& Scene Render exporter"

    def execute(self, context):
        meshes = []
        cameras = []
        lamps = []
        materials = []

        scene = context.scene
        path = scene.render.filepath
        model_path = path + "/model/"
        
        if not os.isdir(model_path):
            try :
                os.mkdir(model_path)
            except OSError:
                print ("Failed Create model directory at " + model_path)
                self.report({"WARNING"}, "Something isn't right")
                return {"CANCELLED"}
        else :
            files = [ f for f in os.listdir(model_path) if f.endswith(".*") ]
            for f in files:
                os.remove(os.path.join(model_path, f))
        
        meshes, cameras, lamps, materials = self.extract_scene_informations(scene)
        
        print(meshes)
        print(cameras)
        print(lamps)
        print(materials)
                
        return {'FINISHED'}

    def extract_scene_informations(self, scene):
        meshes = []
        cameras = []
        lamps = []
        materials = []

        selected_objects = bpy.context.selected_objects

        for obj in selected_objects:
            if obj.type == "MESH":
                meshes.append(obj)
                mesh_mat = obj.active_material
                if mesh_mat not in materials:
                    materials.append(mesh_mat)
            elif obj.type == "LAMP":
                lamps.append(obj)
            if obj.type == "CAMERA":
                cameras.append(obj)
        
        return meshes, cameras, lamps, materials

    def write_scene_file(self, data, path, name):
        scene_file = open(path + name,"w") 
        for d in data:
            scene_file.write(d + "\n")
    
    

#render engine custom begin
class PBRTRenderEngine(bpy.types.RenderEngine):
    bl_idname = 'PBRT_Renderer'
    bl_label = 'PBRT_Renderer'
    bl_use_preview = False
    bl_use_material = True
    bl_use_shading_nodes = False
    bl_use_shading_nodes_custom = False
    bl_use_texture_preview = True
    bl_use_texture = True
    
    def render(self, scene):
        self.report({'ERROR'}, "Use export function in PBRT panel.")

from bl_ui import properties_render
from bl_ui import properties_material
for member in dir(properties_render):
    subclass = getattr(properties_render, member)
    try:
        subclass.COMPAT_ENGINES.add('PBRT_Renderer')
    except:
        pass

for member in dir(properties_material):
    subclass = getattr(properties_material, member)
    try:
        subclass.COMPAT_ENGINES.add('PBRT_Renderer')
    except:
        pass

classes = (
    RenderExporter,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
