import bpy
import os

from io_export_blend_to_renderer.exporter import ExporterScene, RenderExporter
from io_export_blend_to_renderer.nodes.pbrtNode import PbrtMaterialNode, Pbrt_ExportLamp, PbrtEnvironnementNode, Pbrt_ExistingExportMaterial,Pbrt_ExportEnvironnement, Pbrt_ExportMaterialAreaLight

texture_path = ""

def Pbrt_IsLightMaterial(mat):
    if mat.node_tree is not None:
        node_output = mat.node_tree.nodes["Material Output"]
        if len(node_output.inputs["Surface"].links) > 0:
            node_brdf = node_output.inputs["Surface"].links[0].from_node
            if isinstance(node_brdf, PbrtMaterialNode):
                if node_brdf.pbrt_name == "area_light":
                    return True
    return False

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
        # Comment use Camera description
        # data.append("Camera \"perspective\" \"float fov\" " + str(fov))
        return data

    def export_materials(self):
        data = []
        for m in self.materials:
            if m is None:
                continue

            if m.node_tree is not None:
                node_output = m.node_tree.nodes["Material Output"]
                if len(node_output.inputs["Surface"].links) > 0:
                    node_brdf = node_output.inputs["Surface"].links[0].from_node
                    if isinstance(node_brdf, PbrtMaterialNode):
                        if node_brdf.pbrt_name == "area_light":
                            continue
                        str_material = Pbrt_ExistingExportMaterial(node_brdf, m.name, data)
            else:
                default_color = m.diffuse_color
                default_material = "MakeNamedMaterial \""+ m.name +"\" \"string type\" \"matte\" \"rgb Kd\" [" + str(default_color.r) + " "+ str(default_color.g) + " " + str(default_color.b) +"]"
                str_material = default_material

            data.append(str_material)
        return data

    def export_meshes(self):
        data = []
        for m in self.meshes:
            data.append('AttributeBegin')
            if m.active_material is not None :
                if Pbrt_IsLightMaterial(m.active_material):
                    data.append("    "+Pbrt_ExportMaterialAreaLight(m.active_material))
                else:
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
            from_point = l.location
            color =  "[ .5 .5 .5 ]"
            node_lamp = None
            if l.data.node_tree is not None:
                node_output = l.data.node_tree.nodes["Lamp Output"]
                if len(node_output.inputs["Surface"].links) > 0:
                    node_lamp = node_output.inputs["Surface"].links[0].from_node


            if l.data.type == "POINT":
                if node_lamp is not None:
                    color = Pbrt_ExportLamp(node_lamp, "I")
                else :
                    color = "\"rgb I\" " + color
                data.append("LightSource \"point\" \"point from\" [" + str(from_point.x) + " " + str(from_point.y) + " " + str(from_point.z) +" ] " + color)
            elif l.data.type == "SUN":
                world_matrix = l.matrix_world.copy()
                to_point = (world_matrix.col[2] * - 1.0) + world_matrix.col[3]
                data.append("LightSource \"distant\" \"point from\" [" + str(from_point.x) + " " + str(from_point.y) + " " + str(from_point.z) +" ] \"point to\" [" + str(to_point.x) + " " + str(to_point.y) + " " + str(to_point.z) +" ]")
                if node_lamp is not None:
                    color = Pbrt_ExportLamp(node_lamp, "L")
                else :
                    color = "\"blackbody L\" [3000 1.5]"
                data.append("    "+color)
        return data


    def exportScene(self, scene):
        data = []

        data.append("Scale -1 1 1 # flipped image")
        data.extend(self.export_camera())

        # Sampler, Integrator, ...
        pbrt_properties = scene.pbrt
        data.extend(pbrt_properties.export())

        data.append("Film \"image\" \"string filename\" \""+scene.pbrt.output_file+"\"")
        data.append("     \"integer xresolution\" [" + str(scene.render.resolution_x) + "] \"integer yresolution\" ["+str(scene.render.resolution_y)+"]")
        if bpy.data.scenes["Scene"].render.use_border:
            min_x = round(bpy.data.scenes["Scene"].render.border_min_x,2)
            max_x = round(bpy.data.scenes["Scene"].render.border_max_x,2)
            min_y = round(bpy.data.scenes["Scene"].render.border_min_y,2)
            max_y = round(bpy.data.scenes["Scene"].render.border_max_y,2)
            x_resolution = scene.render.resolution_x
            y_resolution = scene.render.resolution_y
            pix_min = [int(x_resolution * min_x), int(y_resolution * min_y)]
            pix_max = [int(x_resolution * max_x), int(y_resolution * max_y)]
            print("crop : ", pix_min, pix_max)
            data.append("     \"float cropwindow\" [ %.2f %.2f  %.2f %.2f ]" % (min_x, max_x, min_y, max_y))

        data.append("")
        data.append("WorldBegin")
        data.append("")

        #import material and textures
        data_material = self.export_materials()
        # Add Materials
        data.extend(data_material)
        data.append("")
        # Add Lamps
        data.extend(self.export_lamps())
        # Envmap
        world = bpy.data.worlds['World']
        if world.use_nodes and world.node_tree is not None:
            world_output = world.node_tree.nodes["World Output"]
            if len(world_output.inputs["Surface"].links) > 0:
                node_environement = world_output.inputs["Surface"].links[0].from_node
                if isinstance(node_environement, PbrtEnvironnementNode):
                    data.append(Pbrt_ExportEnvironnement(node_environement))
                    data.append("")

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
        global textures
        textures = []

        scene = context.scene
        path = scene.render.filepath
        model_path = path + "/models/"

        global texture_path
        texture_path = path + "/textures/"

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

class PbrtExporterAnim(RenderExporter):
    bl_idname = "export.scene_to_pbrt_anim"
    bl_label = "& Pbrt Anim Exporter"

    def execute(self, context):
        scene = bpy.context.scene
        f_start = scene.frame_start
        f_end = scene.frame_end
        for i in range(f_start, f_end + 1 ):
            bpy.context.scene.frame_set(i)
            # Export scene
            self.export_frame(scene, i)

        bpy.context.scene.frame_set(f_start)
        self.report({"INFO"}, "Pbrt Anim Exported")
        return {'FINISHED'}

    def export_frame(self, scene, frame):
        meshes = []
        cameras = []
        lamps = []
        materials = []
        global textures
        textures = []

        path = scene.render.filepath
        model_path = path + "/models/"

        global texture_path
        texture_path = path + "/textures/"

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

        meshes, cameras, lamps, materials = self.extract_scene_informations(scene)

        bpy.ops.object.mode_set(mode='OBJECT')

        # export meshes to ply
        for m in meshes:
            scene.objects.active = m
            bpy.ops.export_mesh.ply(filepath=model_path + str(m.name) + ".ply")

        pbrt_scene = PbrtScene(scene.camera, meshes, lamps, materials)
        data = pbrt_scene.exportScene(scene)

        self.write_scene_file(data, path, "scene_frame"+str(frame)+".pbrt")
        self.report({"INFO"}, "Pbrt Scene Exported")
        return {'FINISHED'}

#render engine custom begin
class PBRTRenderEngine(bpy.types.RenderEngine):
    bl_idname = 'PBRT'
    bl_label = 'PBRT'
    bl_use_preview = False
    bl_use_material = True
    bl_use_shading_nodes = True
    bl_use_shading_nodes_custom = False
    bl_use_texture_preview = True
    bl_use_texture = True

    def render(self, scene):
        self.report({'ERROR'}, "Use export function in PBRT panel.")


classes = (
    PbrtExporter,
    PbrtExporterAnim,
    PBRTRenderEngine,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
