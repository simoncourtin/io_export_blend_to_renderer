import bpy
import os

from io_export_blend_to_render.exporter import ExporterScene, RenderExporter
from io_export_blend_to_render.nodes.pbrtNode import PbrtMaterialNode, Pbrt_ExistingExportMaterial

class PbrtScene(ExporterScene):

    def __init__(self, camera, meshes=[], lamps=[], materials=[]):
        self.camera = camera
        super().__init__([camera], meshes, lamps, materials)

    def export_camera(self, camera=None):
        if camera is None:
            camera = self.camera

        world_matrix = camera.matrix_world.copy()
        eye = world_matrix.col[3]
        look_at = world_matrix.col[2]
        look_at *= -1
        look_at += eye
        fov = camera.data.lens

        data = []
        data.append("LookAt " + str(eye.x) + " " + str(eye.y) + " " + str(eye.z) + " # eye")
        data.append("        "+ str(look_at.x) + " " + str(look_at.y) + " " + str(look_at.z) +"  # look at point")
        data.append("        0 0 1    # up vector")
        data.append("Camera \"perspective\" \"float fov\" " + str(fov))
        return data

    def export_materials(self):
        data = []
        for m in self.materials:
            default_color =  m.diffuse_color
            default_material = "MakeNamedMaterial \""+ m.name +"\" \"string type\" \"matte\" \"rgb Kd\" [" + str(default_color.r) + " "+ str(default_color.g) + " " + str(default_color.b) +"]"
            str_material = default_material
            
            if m.node_tree is not None:
                node_output = m.node_tree.nodes["Material Output"]
                if len(node_output.inputs["Surface"].links) > 0:
                    node_brdf = node_output.inputs["Surface"].links[0].from_node
                    if isinstance(node_brdf, PbrtMaterialNode):
                        str_material = "MakeNamedMaterial \""+ m.name + "\" " + Pbrt_ExistingExportMaterial(node_brdf)

            data.append(str_material)  
        
        return data      

    def export_meshes(self):
        data = []
        for m in self.meshes:
            data.append('AttributeBegin')
            if m.active_material is not None :
                data.append("    NamedMaterial \""+ m.active_material.name + "\"")
            else : 
                data.append("    Material \"matte\" \"rgb Kd\" [ .6 .6 .6 ]")
            data.append("    Shape \"plymesh\" \"string filename\" [ \"models/"+ m.name + ".ply\" ] ")
            data.append('AttributeEnd')

            data.append("")
        
        return data
    
    def export_lamps(self):
        data = []
        for l in self.lamps:
            lamp_type = None
            pos = l.location
            if l.data.type == "POINT":
                data.append("LightSource \"point\" \"point from\" [" + str(pos.x) + " " + str(pos.y) + " " + str(pos.z) +" ] \"rgb I\" [ .5 .5 .5 ]")
            elif l.data.type == "SUN":
                data.append("LightSource \"distant\" \"point from\" [" + str(pos.x) + " " + str(pos.y) + " " + str(pos.z) +" ]")
                data.append("    \"blackbody L\" [3000 1.5]")
        return data


    def exportScene(self, scene): 
        data = []

        data.append("Scale -1 1 1 # flipped image")
        data.extend(self.export_camera())
        
        data.append("Sampler \"halton\" \"integer pixelsamples\" 32")
        
        integrator = "directlighting"
        data.append("Integrator \"" + integrator + "\" ")

        data.append("Film \"image\" \"string filename\" \"output.png\"")
        data.append("     \"integer xresolution\" [" + str(scene.render.resolution_x) + "] \"integer yresolution\" ["+str(scene.render.resolution_y)+"]")
        
        data.append("")
        data.append("WorldBegin")
        data.append("")
        # Add Materials
        data.extend(self.export_materials())
        data.append("")
        # Add Lamps
        data.extend(self.export_lamps())
        # Add Meshes
        data.extend(self.export_meshes())
        data.append("")
        data.append("WorldEnd")

        return data
        
       
class PbrtExporter(RenderExporter):
    bl_idname = "export.scene_to_pbrt_scene"
    bl_label = "& Pbrt Scene Exporter"

    def execute(self, context):
        meshes = []
        cameras = []
        lamps = []
        materials = []

        scene = context.scene
        path = scene.render.filepath
        model_path = path + "/models/"
        
        if not os.path.isdir(model_path):
            try :
                os.mkdir(model_path)
            except OSError:
                print ("Failed Create model directory at " + model_path)
                self.report({"ERROR"}, "Failed Create model directory at " + model_path)
                return {"CANCELLED"}
        else :
            files = [ f for f in os.listdir(model_path) if f.endswith(".ply") ]
            for f in files:
                os.remove(os.path.join(model_path, f))
        
        scene = context.scene
        meshes, cameras, lamps, materials = self.extract_scene_informations(scene)
        
        bpy.ops.object.mode_set(mode='OBJECT')

        # export meshes to ply
        for m in meshes:
            scene.objects.active = m
            bpy.ops.export_mesh.ply(filepath=model_path + str(m.name) + ".ply")
                
        pbrt_scene = PbrtScene(scene.camera, meshes, lamps, materials)
        data = pbrt_scene.exportScene(scene)

        self.write_scene_file(data, path, "scene.pbrt")
        self.report({"INFO"}, "Pbrt Scene Exported")
        return {'FINISHED'}

classes = (
    PbrtExporter,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)