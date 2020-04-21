import bpy

from bpy.types import NodeTree, Node, NodeSocket
import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem, NodeItemCustom

""" for texture
if len(i.links) > 0:
    n = i.links[0].from_node
    if isinstance(n,ShaderNodeTexChecker):
        print("checkerboard")
"""

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

# Export Socket
def Pbrt_ExportSockets(node):
    parameters = ""
    for i in node.inputs:
        if i.type == "RGBA" :
            parameters += Pbrt_SocketRGBA(i)
        elif i.type == "INT" :
            parameters += Pbrt_SocketINT(i)
        elif i.type == "VALUE" :
            parameters += Pbrt_SocketVALUE(i)
        elif i.type == "BOOL" :
            parameters += Pbrt_SocketBOOL(i)
        parameters += " "
    return parameters

# Export Material in PBRT scene format
def Pbrt_ExportMaterial(pbrt_mat):
    string_export = "Material \"" + pbrt_mat.pbrt_name + "\" " + Pbrt_ExportSockets(pbrt_mat)          
    #print(string_export)
    return string_export

def Pbrt_ExistingExportMaterial(pbrt_mat):
    string_export = "\"string type\" \"" + pbrt_mat.pbrt_name + "\" " + Pbrt_ExportSockets(pbrt_mat)          
    #print(string_export)
    return string_export

class PbrtMaterialNode(Node):
    bl_idname = "PbrtMaterialNode"
    bl_label = "Pbrt material Node"
    pbrt_name = "pbrt_material"
    def init(self, context):
        self.outputs.new("NodeSocketShader", "BRDF")

    def add_input(self, socket_type, name, default_value):
        input = self.inputs.new(socket_type, name)
        input.default_value = default_value
        return input

    def add_ouput(self, socket_type, name):
        output = self.outputs.new(socket_type, name)
        return output
        
    def draw_buttons(self, context, layout):
        layout.label(text="")

    def draw_label(self):
        return "PbrtMaterialNode"


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

class PbrtNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ShaderNodeTree'

identifier = 'PBRT_NODES'
node_categories = [PbrtNodeCategory(identifier, "Pbrt Material Nodes", items=[
    NodeItem("PbrtMatteMaterial"),
    NodeItem("PbrtPlasticMaterial"),
    NodeItem("PbrtMetalMaterial"),
    NodeItem("PbrtDisneyMaterial"),
    NodeItem("PbrtGlassMaterial"),
    NodeItem("PbrtKdsubsurfaceMaterial")
])]

classes = (
    PbrtMatteMaterialNode,
    PbrtPlasticMaterialNode,
    PbrtMetalMaterialNode,
    PbrtDisneyMaterialNode,
    PbrtGlassMaterialNode,
    PbrtKdsubsurfaceMaterialNode,
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


