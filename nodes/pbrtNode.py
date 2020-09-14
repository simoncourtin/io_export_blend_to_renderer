import bpy
from io_export_blend_to_renderer import pbrt
from bpy.types import NodeTree, Node, NodeSocket
import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem, NodeItemCustom

import shutil
import os

# Node sockets
def Pbrt_SocketRGBA(socket):
    value = socket.default_value
    return "\"rgb "+ socket.name + "\" ["+ str(value[0]) + " " + str(value[1]) + " " + str(value[2]) +"]"

def Pbrt_SocketINT(socket):
    return "\"integer "+ socket.name + "\" "+ str(socket.default_value)

def Pbrt_SocketBOOL(socket):
    return "\"bool "+ socket.name + "\" "+ str(socket.default_value)

def Pbrt_SocketVALUE(socket):
    return "\"float "+ socket.name + "\" "+ str(socket.default_value)

def Pbrt_SocketSHADER(socket,data):
    if len(socket.links) > 0:
        node = socket.links[0].from_node
        if isinstance(node, PbrtMaterialNode):
            data.append(Pbrt_ExistingExportMaterial(node, "material."+ str(len(data)), data))
            return  "\"string "+ socket.name + "\" \""+ "material."+ str(len(data)-1)+ "\""
    return ""

def Pbrt_AddTexture(socket, node, data):
    tex_type = None
    tex_parameter = ""
    tex_name = "Texture_" + str(len(pbrt.textures))

    if node.type == "TEX_IMAGE":
        tex_type = "imagemap"
        tex_parameter += "\"string filename\" \"textures/"+node.image.name+"\" "
        # TODO copy image file
        try:
            shutil.copyfile(bpy.path.abspath(node.image.filepath), pbrt.texture_path+node.image.name)
        except IOError as io_err:
            os.makedirs(pbrt.texture_path)
            shutil.copyfile(bpy.path.abspath(node.image.filepath), pbrt.texture_path+node.image.name)
    if node.type == "TEX_CHECKER":
        tex_type = "checkerboard"
        color1 = [node.inputs[1].default_value[0], node.inputs[1].default_value[1], node.inputs[1].default_value[2]]
        color2 = [node.inputs[2].default_value[0], node.inputs[2].default_value[1], node.inputs[2].default_value[2]]
        scale = node.inputs[3].default_value
        tex_parameter += "\"float uscale\" ["+str(scale)+"] \"float vscale\" ["+str(scale)+"] "
        tex_parameter += "\"rgb tex1\" " +str(color1)+" \"rgb tex2\" "+str(color2)+" "

    texture = "Texture \""+tex_name+"\" \"spectrum\" \""+tex_type+"\" " + tex_parameter
    data.append(texture)

    return "\"texture "+ socket.name + "\" \"" +tex_name+ "\""

# Export Socket
def Pbrt_ExportSockets(node, data):
    parameters = ""
    for i in node.inputs:
        if i.type == "RGBA" :
            rgba = Pbrt_SocketRGBA(i)
            if(len(i.links) > 0):
                if i.links[0].from_node.type in ["TEX_IMAGE", "TEX_CHECKER"]:
                    rgba = Pbrt_AddTexture(i, i.links[0].from_node, data)
            parameters += rgba
        elif i.type == "INT" :
            parameters += Pbrt_SocketINT(i)
        elif i.type == "VALUE" :
            parameters += Pbrt_SocketVALUE(i)
        elif i.type == "BOOL" :
            parameters += Pbrt_SocketBOOL(i)
        elif i.type == "SHADER" :
            parameters += Pbrt_SocketSHADER(i, data)
        parameters += " "
    return parameters

# Export Material in PBRT scene format
def Pbrt_ExportMaterial(pbrt_mat):
    string_export = "Material \"" + pbrt_mat.pbrt_name + "\" " + Pbrt_ExportSockets(pbrt_mat, new_materials)
    return string_export

def Pbrt_ExistingExportMaterial(pbrt_mat, name, data):
    string_export = "MakeNamedMaterial \""+ name + "\" \"string type\" \"" + pbrt_mat.pbrt_name + "\" " + Pbrt_ExportSockets(pbrt_mat, data)
    return string_export

def Pbrt_ExportMaterialAreaLight(pbrt_mat):
    node_output = pbrt_mat.node_tree.nodes["Material Output"]
    node = node_output.inputs["Surface"].links[0].from_node
    strenght = node.inputs[1].default_value
    L = node.inputs[0].default_value
    string_export = "AreaLightSource \"diffuse\" \"rgb "+ node.inputs[0].name +"\" ["+ str(L[0]*strenght) + " " + str(L[1]*strenght) + " " + str(L[2]*strenght) +"]"
    return string_export

def Pbrt_ExportEnvironnement(pbrt_environement):
    parameters = ""
    for i in pbrt_environement.inputs:
        if i.type == "RGBA" :
            rgba = Pbrt_SocketRGBA(i)
            if(len(i.links) > 0):
                tex_node = i.links[0].from_node
                if tex_node.type == "TEX_ENVIRONMENT" :
                    try:
                        shutil.copyfile(bpy.path.abspath(tex_node.image.filepath), pbrt.texture_path+tex_node.image.name)
                    except IOError as io_err:
                        os.makedirs(pbrt.texture_path)
                        shutil.copyfile(bpy.path.abspath(tex_node.image.filepath), pbrt.texture_path+tex_node.image.name)
                    rgba = "\"string mapname\" [ \"textures/"+ tex_node.image.name + "\" ]"
            parameters += rgba
        elif i.type == "INT" :
            parameters += Pbrt_SocketINT(i)
        elif i.type == "VALUE" :
            parameters += Pbrt_SocketVALUE(i)
        elif i.type == "BOOL" :
            parameters += Pbrt_SocketBOOL(i)
        parameters += " "
    environement = "LightSource \"infinite\" " + parameters
    return environement

def Pbrt_ExportLamp(node, name):
    lamp_parameter = ""
    if node.type == "EMISSION":
        mult = node.inputs[1].default_value
        color = [node.inputs[0].default_value[0] * mult, node.inputs[0].default_value[1] * mult, node.inputs[0].default_value[2] * mult]
        lamp_parameter += "\"rgb "+name+"\" " + str(color)
    return lamp_parameter

class PbrtMaterialNode(Node):
    bl_idname = "PbrtMaterialNode"
    bl_label = "Pbrt material Node"
    pbrt_name = "pbrt_material"
    def init(self, context):
        self.outputs.new("NodeSocketShader", "BRDF")

    def add_input(self, socket_type, name, default_value):
        input = self.inputs.new(socket_type, name)
        if default_value is not None:
            input.default_value = default_value
        return input

    def add_ouput(self, socket_type, name):
        output = self.outputs.new(socket_type, name)
        return output

    def draw_buttons(self, context, layout):
        layout.label(text="")

    def draw_label(self):
        return "PbrtMaterialNode"


class PbrtAreaLightNode(PbrtMaterialNode):
    bl_idname = "PbrtAreaLight"
    bl_label = "PBRT Area Light Node"
    pbrt_name = "area_light"
    def init(self, context):
        super().init(context)
        self.add_input("NodeSocketColor", "L", (1.0, 1.0, 1.0, 1.0))
        self.add_input("NodeSocketFloat", "Strenght", 1.0)

    def draw_label(self):
        return "Pbrt Areal Light"

class PbrtMatteMaterialNode(PbrtMaterialNode):
    bl_idname = "PbrtMatteMaterial"
    bl_label = "PBRT Matte Material Node"
    pbrt_name = "matte"
    def init(self, context):
        super().init(context)
        self.add_input("NodeSocketColor", "Kd", (1.0, 1.0, 1.0, 1.0))
        self.add_input("NodeSocketFloat", "sigma", 0.0)

    def draw_label(self):
        return "Pbrt Matte"

class PbrtPlasticMaterialNode(PbrtMaterialNode):
    bl_idname = "PbrtPlasticMaterial"
    bl_label = "PBRT Plastic Material Node"
    pbrt_name = "plastic"

    def init(self, context):
        super().init(context)
        self.add_input("NodeSocketColor", "Kd", (1.0, 1.0, 1.0, 1.0))
        self.add_input("NodeSocketColor", "Ks", (1.0, 1.0, 1.0, 1.0))
        self.add_input("NodeSocketFloat", "roughness", 0.0)

    def draw_label(self):
        return "Pbrt Plastic"

class PbrtMetalMaterialNode(PbrtMaterialNode):
    bl_idname = "PbrtMetalMaterial"
    bl_label = "PBRT Metal Material Node"
    pbrt_name = "metal"
    def init(self, context):
        super().init(context)
        self.add_input("NodeSocketColor", "eta", (1.0, 1.0, 1.0, 1.0))
        self.add_input("NodeSocketColor", "k", (1.0, 1.0, 1.0, 1.0))
        self.add_input("NodeSocketFloat", "roughness", 0.0)
        #self.add_input("NodeSocketFloat", "uroughness", None)
        #self.add_input("NodeSocketFloat", "vroughness", None)
        self.add_input("NodeSocketBool", "remaproughness", True)

    def draw_label(self):
        return "Pbrt Metal"

class PbrtMirrorMaterialNode(PbrtMaterialNode):
    bl_idname = "PbrtMirrorMaterial"
    bl_label = "PBRT Mirror Material Node"
    pbrt_name = "mirror"
    def init(self, context):
        super().init(context)
        self.add_input("NodeSocketColor", "Kr", (1.0, 1.0, 1.0, 1.0))

    def draw_label(self):
        return "Pbrt Mirror"

class PbrtDisneyMaterialNode(PbrtMaterialNode):
    bl_idname = "PbrtDisneyMaterial"
    bl_label = "PBRT Disney Material Node"
    pbrt_name = "disney"

    def init(self, context):
        super().init(context)
        self.add_input("NodeSocketColor", "color", (1.0, 1.0, 1.0, 1.0))
        self.add_input("NodeSocketFloat", "anisotropic", 0.0)
        self.add_input("NodeSocketFloat", "clearcoat", 0.0)
        self.add_input("NodeSocketFloat", "clearcoatgloss", 1.0)
        self.add_input("NodeSocketFloat", "eta", 1.5)
        self.add_input("NodeSocketFloat", "metallic", 0.0)
        self.add_input("NodeSocketFloat", "roughness", 0.0)
        #self.add_input("NodeSocketColor", "scatterdistance", (1.0, 1.0, 1.0, 1.0))
        self.add_input("NodeSocketFloat", "sheen", 0.0)
        self.add_input("NodeSocketFloat", "sheentint", 0.5)
        self.add_input("NodeSocketFloat", "spectrans", 0.0)
        self.add_input("NodeSocketFloat", "speculartint", 0.0)

    def draw_label(self):
        return "Pbrt Disney"


class PbrtGlassMaterialNode(PbrtMaterialNode):
    bl_idname = "PbrtGlassMaterial"
    bl_label = "PBRT Glass Material Node"
    pbrt_name = "glass"

    def init(self, context):
        super().init(context)
        self.add_input("NodeSocketColor", "Kr", (1.0, 1.0, 1.0, 1.0))
        self.add_input("NodeSocketColor", "Kt", (1.0, 1.0, 1.0, 1.0))
        self.add_input("NodeSocketFloat", "eta", 1.5)
        self.add_input("NodeSocketFloat", "uroughness", 0.0)
        self.add_input("NodeSocketFloat", "vroughness", 0.0)
        self.add_input("NodeSocketBool", "remaproughness", True)

    def draw_label(self):
        return "Pbrt Glass"


class PbrtKdsubsurfaceMaterialNode(PbrtMaterialNode):
    bl_idname = "PbrtKdsubsurfaceMaterial"
    bl_label = "PBRT Kdsubsurface Material Node"
    pbrt_name = "kdsubsurface"

    def init(self, context):
        super().init(context)
        self.add_input("NodeSocketColor", "Kd", (1.0, 1.0, 1.0, 1.0))
        self.add_input("NodeSocketFloat", "mfp", 0.0)
        self.add_input("NodeSocketFloat", "eta", 1.3)
        self.add_input("NodeSocketColor", "Kr", (1.0, 1.0, 1.0, 1.0))
        self.add_input("NodeSocketColor", "Kd", (1.0, 1.0, 1.0, 1.0))
        self.add_input("NodeSocketFloat", "uroughness", 0.0)
        self.add_input("NodeSocketFloat", "vroughness", 0.0)
        self.add_input("NodeSocketBool", "remaproughness", True)

    def draw_label(self):
        return "Pbrt Kdsubsurface"

class PbrtSubstrateMaterialode(PbrtMaterialNode):
    bl_idname = "PbrtSubstrateMaterial"
    bl_label = "PBRT Substrate Material Node"
    pbrt_name = "substrate"

    def init(self, context):
        super().init(context)
        self.add_input("NodeSocketColor", "Kd", (1.0, 1.0, 1.0, 1.0))
        self.add_input("NodeSocketColor", "Ks", (1.0, 1.0, 1.0, 1.0))
        self.add_input("NodeSocketFloat", "uroughness", 0.0)
        self.add_input("NodeSocketFloat", "vroughness", 0.0)
        self.add_input("NodeSocketBool", "remaproughness", True)

    def draw_label(self):
        return "Pbrt Kdsubsurface"

class PbrtMixtureMaterialNode(PbrtMaterialNode):
    bl_idname = "PbrtMixtureMaterial"
    bl_label = "PBRT Mixure Material Node"
    pbrt_name = "mix"

    def init(self, context):
        super().init(context)
        self.add_input("NodeSocketFloat", "amount", 0.5)
        self.add_input("NodeSocketShader", "namedmaterial1", None)
        self.add_input("NodeSocketShader", "namedmaterial2", None)

    def draw_label(self):
        return "Pbrt Mixure"

class PbrtEnvironnementNode(PbrtMaterialNode):
    bl_idname = "PbrtEnvironementMaterial"
    bl_label = "PBRT Environement Node"
    pbrt_name = "environement"
    def init(self, context):
        super().init(context)
        self.add_input("NodeSocketColor", "L", (1.0, 1.0, 1.0, 1.0))
        self.add_input("NodeSocketInt", "samples", 1)

    def draw_label(self):
        return "Pbrt Environement"

class PbrtNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ShaderNodeTree'

identifier = 'PBRT_NODES'
node_categories = [PbrtNodeCategory(identifier, "Pbrt Material Nodes", items=[
    NodeItem("PbrtMatteMaterial"),
    NodeItem("PbrtPlasticMaterial"),
    NodeItem("PbrtMetalMaterial"),
    NodeItem("PbrtMirrorMaterial"),
    NodeItem("PbrtDisneyMaterial"),
    NodeItem("PbrtGlassMaterial"),
    NodeItem("PbrtKdsubsurfaceMaterial"),
    NodeItem("PbrtSubstrateMaterial"),
    NodeItem("PbrtMixtureMaterial"),
    NodeItem("PbrtEnvironementMaterial"),
    NodeItem("PbrtAreaLight")
])]

classes = (
    PbrtMatteMaterialNode,
    PbrtPlasticMaterialNode,
    PbrtMetalMaterialNode,
    PbrtMirrorMaterialNode,
    PbrtDisneyMaterialNode,
    PbrtGlassMaterialNode,
    PbrtKdsubsurfaceMaterialNode,
    PbrtSubstrateMaterialode,
    PbrtMixtureMaterialNode,
    PbrtEnvironnementNode,
    PbrtAreaLightNode
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    if identifier in nodeitems_utils._node_categories:
        nodeitems_utils.unregister_node_categories(identifier)
    nodeitems_utils.register_node_categories(identifier, node_categories)

def unregister():
    nodeitems_utils.unregister_node_categories(identifier)
    for cls in classes:
        bpy.utils.unregister_class(cls)

    nodeitems_utils.unregister_node_categories("PBRT_MATERIAL_TREE")
