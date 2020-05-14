import bpy

from bpy.types import (
        Panel,
        Menu,
        Operator,
        )

        
def find_node(material, nodetype):
    if material and material.node_tree:
        ntree = material.node_tree

        active_output_node = None
        for node in ntree.nodes:
            if getattr(node, "type", None) == nodetype:
                if getattr(node, "is_active_output", True):
                    return node
                if not active_output_node:
                    active_output_node = node
        return active_output_node

    return None


def find_node_input(node, name):
    for input in node.inputs:
        if input.name == name:
            return input

    return None

def panel_node_draw(layout, id_data, output_type, input_name):
    if not id_data.use_nodes:
        layout.operator("pbrt.use_shading_nodes", icon='NODETREE')
        return False

    ntree = id_data.node_tree

    node = find_node(id_data, output_type)
    if not node:
        layout.label(text="No output node")
    else:
        input = find_node_input(node, input_name)
        layout.template_node_view(ntree, node, input)

    return True

class RenderButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    # COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return (rd.use_game_engine is False) and (rd.engine in cls.COMPAT_ENGINES)

class PBRTButtonsPanel:
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    COMPAT_ENGINES = {'PBRT'}

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return rd.engine in cls.COMPAT_ENGINES


class PBRT_OT_use_shading_nodes(Operator):
    """Enable nodes on a material, world or lamp"""
    bl_idname = "pbrt.use_shading_nodes"
    bl_label = "Use Nodes"

    @classmethod
    def poll(cls, context):
        return (getattr(context, "material", False) or getattr(context, "world", False) or
                getattr(context, "lamp", False))

    def execute(self, context):
        if context.material:
            context.material.use_nodes = True
        elif context.world:
            context.world.use_nodes = True
        elif context.lamp:
            context.lamp.use_nodes = True

        return {'FINISHED'}

class PBRTMaterial_surface(PBRTButtonsPanel, Panel):
    bl_label = "Surface"
    bl_context = "material"

    @classmethod
    def poll(cls, context):
        return context.material and PBRTButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout

        mat = context.material
        if not panel_node_draw(layout, mat, 'OUTPUT_MATERIAL', 'Surface'):
            layout.prop(mat, "diffuse_color")

class PBRTWorld_surface(PBRTButtonsPanel, Panel):
    bl_label = "Surface"
    bl_context = "world"

    @classmethod
    def poll(cls, context):
        return context.world and PBRTButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout

        world = context.world

        if not panel_node_draw(layout, world, 'OUTPUT_WORLD', 'Surface'):
            layout.prop(world, "horizon_color", text="Color")


class PBRTRender_sampling(PBRTButtonsPanel, Panel):
    bl_label = "Sampling"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        scene = context.scene
       
        col = layout
        col.label("Sampling:")
        col.prop(scene.pbrt, "sampler")
        col.prop(scene.pbrt, "pixelsamples")
        
        
        col.label("Integrator:")
        col.prop(scene.pbrt, "integrator")

        col.prop(scene.pbrt, "maxdepth")

        if scene.pbrt.integrator == "path":
            col.prop(scene.pbrt, "rrthreshold")
        elif scene.pbrt.integrator == "bdpt":
            col.prop(scene.pbrt, "lightsamplestrategy")
            col.prop(scene.pbrt, "strategy")
            col.prop(scene.pbrt, "visualizestrategies")
            col.prop(scene.pbrt, "visualizeweights")
        elif scene.pbrt.integrator == "mtl":
            col.prop(scene.pbrt, "bootstrapsamples")
            col.prop(scene.pbrt, "chains")
            col.prop(scene.pbrt, "mutationsperpixel")
            col.prop(scene.pbrt, "largestepprobability")
            col.prop(scene.pbrt, "sigma")
        elif scene.pbrt.integrator == "sppm":
            col.prop(scene.pbrt, "iterations")
            col.prop(scene.pbrt, "photonsperiteration")
            col.prop(scene.pbrt, "imagewritefrequency")
            col.prop(scene.pbrt, "radius")

        col.label("Accereator:")
        col.prop(scene.pbrt, "accel")

        col.label("")
        col.operator("export.scene_to_pbrt_scene", text="Export PBRT file", icon="NONE")

def get_panels():
    exclude_panels = {
        'DATA_PT_area',
        'DATA_PT_camera_dof',
        'DATA_PT_falloff_curve',
        'DATA_PT_lamp',
        'DATA_PT_preview',
        'DATA_PT_shadow',
        'DATA_PT_spot',
        'DATA_PT_sunsky',
        'MATERIAL_PT_context_material',
        'MATERIAL_PT_diffuse',
        'MATERIAL_PT_flare',
        'MATERIAL_PT_halo',
        'MATERIAL_PT_mirror',
        'MATERIAL_PT_options',
        'MATERIAL_PT_pipeline',
        'MATERIAL_PT_preview',
        'MATERIAL_PT_shading',
        'MATERIAL_PT_shadow',
        'MATERIAL_PT_specular',
        'MATERIAL_PT_sss',
        'MATERIAL_PT_strand',
        'MATERIAL_PT_transp',
        'MATERIAL_PT_volume_density',
        'MATERIAL_PT_volume_integration',
        'MATERIAL_PT_volume_lighting',
        'MATERIAL_PT_volume_options',
        'MATERIAL_PT_volume_shading',
        'MATERIAL_PT_volume_transp',
        'RENDERLAYER_PT_layer_options',
        'RENDERLAYER_PT_layer_passes',
        'RENDERLAYER_PT_views',
        'RENDER_PT_antialiasing',
        'RENDER_PT_bake',
        'RENDER_PT_motion_blur',
        'RENDER_PT_performance',
        'RENDER_PT_post_processing',
        'RENDER_PT_shading',
        'SCENE_PT_simplify',
        'TEXTURE_PT_context_texture',
        'WORLD_PT_ambient_occlusion',
        'WORLD_PT_environment_lighting',
        'WORLD_PT_gather',
        'WORLD_PT_indirect_lighting',
        'WORLD_PT_mist',
        'WORLD_PT_preview',
        'WORLD_PT_world'
        }

    panels = []
    for panel in bpy.types.Panel.__subclasses__():
        if hasattr(panel, 'COMPAT_ENGINES') and 'BLENDER_RENDER' in panel.COMPAT_ENGINES:
            if panel.__name__ not in exclude_panels:
                panels.append(panel)

    return panels

classes = (
    PBRTRender_sampling,
    PBRT_OT_use_shading_nodes,
    PBRTMaterial_surface,
    PBRTWorld_surface,
)


def register():
    
    for panel in get_panels():
        panel.COMPAT_ENGINES.add('PBRT')

    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():

    for panel in get_panels():
        if 'CYCLES' in panel.COMPAT_ENGINES:
            panel.COMPAT_ENGINES.remove('PBRT')

    for cls in classes:
        bpy.utils.unregister_class(cls)