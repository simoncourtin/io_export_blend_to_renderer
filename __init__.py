bl_info = {
    "name": "Export Blend to render format",
    "category": "Import-Export",
    "blender": (2, 79, 2),
}

import sys
import os
import bpy
import shutil

from bpy.types import (
            AddonPreferences,
            PropertyGroup,
            #Operator,
            )

from bpy.props import (
        StringProperty,
        BoolProperty,
        IntProperty,
        FloatProperty,
        FloatVectorProperty,
        EnumProperty,
        PointerProperty,
        CollectionProperty,
        )

from io_export_blend_to_renderer import exporter
from io_export_blend_to_renderer import pbrt
from io_export_blend_to_renderer import nodes
from io_export_blend_to_renderer import ui

enum_samplers = (
    ('02sequence', "02sequence", ""),
    ('halton', "halton", ""),
    ('maxmindist', "maxmindist", ""),
    ('random', "random", ""),
    ('stratified', "stratified", "")
    )


enum_integrator = (
    ('bdpt', "BDPT Integrator", ""),
    ('directlighting', "Direct Lighting Integrator", ""),
    ('mtl', "MLT Integrator", ""),
    ('path', "Path Integrator", ""),
    ('sppm', "SPPM Integrator", ""),
    ('whitted', "Whitted Integrator", "")
    )

enum_lightsamplestrategy = (
    ('uniform', "uniform", "Samples all light sources uniformly"),
    ('power', "power", "Samples light sources according to their emitted power"),
    ('spatial', "spatial", "Computes light contributions in regions of the scene and samples from a related distribution")
)


enum_accelerator = (
    ('bvh', "BVHAccel", ""),
    ('kdtree', "KdTreeAccel", "")
)

enum_camera = (
    ('perspective', "perspective", ""),
    ('orthographic', "orthographic", ""),
    ('realistic', "realistic", ""),
    ('environment', "environment", "")
    )

class RenderPBRTSettingsScene(PropertyGroup):
    
    output_file = StringProperty(
                name="Output File Name",
                description="Name of output img file",
                default='output.png',
                )


    sampler = EnumProperty(
                name="Sampler",
                description="Sampler to use for sampling",
                items=enum_samplers,
                default='halton',
                )
    
    integrator = EnumProperty(
                name="Integrator",
                description="Integrator to use for computes radiance arriving at the film plane from surfaces and participating media in the scene. ",
                items=enum_integrator,
                default='path',
                )

    pixelsamples = IntProperty(
            name="Samples",
            description="Number of samples",
            min=1, 
            default=64)

    use_shading_nodes = BoolProperty(
            name="Use Shading Node", 
            default=True)


    # PathIntegrator 
    maxdepth = IntProperty(
            name="Max depth",
            description="Maximum length of a light-carrying path sampled by the integrator",
            min=1, 
            default=5)

    rrthreshold = FloatProperty(
            name="rrthreshold",
            description="Determines when Russian roulette is applied to paths: when the maximum spectral component of the path contribution falls beneath this value, Russian roulette starts to be used.",
            min=1.0, 
            default=1.0)


    # BDPTIntegrator 
    lightsamplestrategy = EnumProperty(
                    name="Light Sample Strategy",
                    description="Technique used for sampling light sources.",
                    items=enum_lightsamplestrategy,
                    default='spatial',
                    )

    strategy = StringProperty(
            name="Strategy",
            description="The strategy to use for sampling direct lighting.", 
            default="all")

    visualizestrategies = BoolProperty(
                        name="Visualize Strategies",
                        description="If true, an image is saved for each (s,t) bidirectional path generation strategy used by the integrator. ", 
                        default=False)

    visualizeweights = BoolProperty(
                    name="Visualize Weights",
                    description="If true, an image is saved with the multiple importance sampling weights for each (s,t) bidirectional path generation strategy.", 
                    default=False)

    # MLTIntegrator
    bootstrapsamples = IntProperty(
            name="Boot strap samples",
            description="Number of samples to take during the \"bootstrap\" phase; some of these samples are used for initial light-carrying paths for the Metropolis algorithm.",
            min=0, 
            default=100000)

    chains = IntProperty(
            name="Chains",
            description="Number of unique Markov chains chains to follow with the Metropolis algorithm.",
            min=0, 
            default=1000)

    mutationsperpixel = IntProperty(
            name="Mutations per pixel",
            description="Number of path mutations to apply per pixel in the image.",
            min=0, 
            default=100)

    largestepprobability = FloatProperty(
            name="Large Step Probability",
            description="Probability of discarding the current path and generating a new random path ",
            min=0.0, 
            default=0.3)

    sigma = FloatProperty(
            name="Sigma",
            description="Standard deviation of the perturbation applied to random samples in [0,1] used for small path mutations",
            min=0.0, 
            max=1.0, 
            default=0.01)

    #SPPMIntegrator 
    iterations = IntProperty(
            name="Iterations",
            description="Total number of iterations of photon shooting from light sources",
            min=0, 
            default=64)

    photonsperiteration = IntProperty(
            name="Photons per iteration",
            description="Number of photons to shoot from light sources in each iteration. With the default value, -1, the number is automatically set to be equal to the number of pixels in the image.",
            default=-1)

    imagewritefrequency = IntProperty(
            name="Image write frequency",
            description="Frequency at which to write out the current image, in photon shooting iterations.",
            min=0, 
            default=0)

    radius = FloatProperty(
            name="Radius",
            description="Initial photon search radius.",
            default=1.0)
    
    #Accelerator
    accel = EnumProperty(
            name="Acelerator",
            description="",
            items=enum_accelerator,
            default='kdtree',
            )

    # Camera
    camera = EnumProperty(
             name="Camera",
             description="Parameters for camera",
             items=enum_camera,
             default='perspective',
             )
    # Perspective et orthographic
    lensradius = FloatProperty(
            name="lensradius",
            description="The radius of the lens. Used to render scenes with depth of field and focus effects. The default value yields a pinhole camera.",
            default=0.0)

    focaldistance = FloatProperty(
            name="focaldistance",
            description="The focal distance of the lens. If \"lensradius\" is zero, this has no effect. Otherwise, it specifies the distance from the camera origin to the focal plane.",
            default=0.0)

    # Perspective
    fov = FloatProperty(
            name="fov",
            description="Specifies the field of view for the perspective camera. This is the spread angle of the viewing frustum along the narrower of the image's width and height.",
            default=90.0)

    halffov = FloatProperty(
            name="focaldistance",
            description="The focal distance of the lens. If \"lensradius\" is zero, this has no effect. Otherwise, it specifies the distance from the camera origin to the focal plane.",
            default=0.0)

    # Realistic
    lensfile = StringProperty(
            name="lensfile",
            description="Specifies the name of a lens description file that gives the collection of lens elements in the lens system.",
            default="",
            subtype = 'FILE_PATH')

    aperturediameter = FloatProperty(
            name="aperturediameter",
            description="Diameter of the lens system's aperture, specified in mm. The smaller the aperture, the less light reaches the film plane, but the greater the range of distances that are in focus.",
            default=1.0)

    focusdistance = FloatProperty(
            name="focusdistance",
            description="Specifies the field of view for the perspective camera. This is the spread angle of the viewing frustum along the narrower of the image's width and height.",
            default=10.0)

    simpleweighting = IntProperty(
            name="simpleweighting",
            description="Indicates whether incident radiance at the film plane should just be weighted by the cosine-to-the-4th term, or whether it should also include the additional weighting terms that account for the shutter open time and the projected area of the exit pupil are included so that the image records incident energy on the film plane.",
            default=True)
    
    all_prop = {
                "rrthreshold" : rrthreshold[1],
                "lightsamplestrategy" : lightsamplestrategy[1],
                "strategy" : strategy[1],
                "visualizestrategies" : visualizestrategies[1],
                "visualizeweights" : visualizeweights[1],
                "bootstrapsamples" : bootstrapsamples[1],
                "chains" : chains[1],
                "mutationsperpixel" : mutationsperpixel[1],
                "largestepprobability" : largestepprobability[1],
                "sigma" : sigma[1],
                "lensradius" : lensradius[1],
                "fov" : fov[1],
                "lensfile" : lensfile[1],
                "aperturediameter" : aperturediameter[1],
                "focusdistance" : focusdistance[1],
                "simpleweighting" : simpleweighting[1]
        }

    def exportProperty(self, prop_name, value):
            prop = self.all_prop[prop_name]
            if isinstance(value, int):
                    return "\"integer "+ prop["attr"] +"\" " + str(value)
            elif isinstance(value, float):
                    return "\"float "+ prop["attr"] +"\" " + str(value)
            elif isinstance(value, bool):
                    return "\"bool "+ prop["attr"] +"\" " + str(value)
            elif isinstance(value, str):
                    return "\"string "+ prop["attr"] +"\" " + "\"" + str(value) + "\""

    def export(self):
        
        data = []
        # Sampler
        sampler = "Sampler \"" + self.sampler + "\" \"integer pixelsamples\" " + str(self.pixelsamples)
        # Camera
        camera = "Camera \"" + self.camera + "\""
        # Integrator
        integrator = "Integrator \"" + self.integrator + "\" \"integer maxdepth\" " + str(self.maxdepth)

        params = []
        export_path = bpy.data.scenes["Scene"].render.filepath
        if self.integrator == "path":
                if self.rrthreshold != self.all_prop["rrthreshold"]["default"]:
                        params.append(self.exportProperty("rrthreshold", self.rrthreshold))
        elif self.integrator == "bdpt":
                if self.lightsamplestrategy != self.all_prop["lightsamplestrategy"]["default"]:
                        params.append(self.exportProperty("lightsamplestrategy", self.lightsamplestrategy))
                if self.strategy != self.all_prop["strategy"]["default"]:
                        params.append(self.exportProperty("strategy", self.strategy))
                if self.visualizestrategies != self.all_prop["visualizestrategies"]["default"]:
                       params.append(self.exportProperty("visualizestrategies", self.visualizestrategies))
                if self.visualizeweights != self.all_prop["visualizeweights"]["default"]:
                       params.append(self.exportProperty("visualizeweights", self.visualizeweights))
        elif self.integrator == "mtl":
                if self.bootstrapsamples != self.all_prop["bootstrapsamples"]["default"]:
                        params.append(self.exportProperty("bootstrapsamples", self.bootstrapsamples))
                if self.chains != self.all_prop["chains"]["default"]:
                        params.append(self.exportProperty("chains", self.chains))
                if self.mutationsperpixel != self.all_prop["mutationsperpixel"]["default"]:
                        params.append(self.exportProperty("mutationsperpixel", self.mutationsperpixel))
                if self.largestepprobability != self.all_prop["largestepprobability"]["default"]:
                        params.append(self.exportProperty("largestepprobability", self.largestepprobability))
                if self.sigma != self.all_prop["sigma"]["default"]:
                        params.append(self.exportProperty("sigma", self.sigma))
        elif self.integrator == "sppm":
                if self.iterations != self.all_prop["iterations"]["default"]:
                        params.append(self.exportProperty("iterations", self.iterations))
                if self.photonsperiteration != self.all_prop["photonsperiteration"]["default"]:
                        params.append(self.exportProperty("photonsperiteration", self.photonsperiteration))
                if self.imagewritefrequency != self.all_prop["imagewritefrequency"]["default"]:
                        params.append(self.exportProperty("imagewritefrequency", self.imagewritefrequency))
                if self.radius != self.all_prop["radius"]["default"]:
                        params.append(self.exportProperty("radius", self.radius))

        integrator_params = ""
        for p in params:
                integrator_params += p + " "
        
        camera_params = []
        if self.camera == "perspective":
                camera_params.append(self.exportProperty("lensradius", self.lensradius))
                camera_params.append(self.exportProperty("fov", self.fov))
        elif self.camera == "orthographic":
                camera_params.append(self.exportProperty("lensradius", self.lensradius))
                camera_params.append(self.exportProperty("fov", self.fov))
        elif self.camera == "realistic":
                file_path = bpy.path.abspath(self.lensfile)
                file_name = file_path.split("/")[-1]
                try:
                        shutil.copyfile(bpy.path.abspath(file_path), export_path + file_name)
                except IOError as io_err:
                        os.makedirs(export_path)
                        shutil.copyfile(bpy.path.abspath(file_path), export_path + file_name)
                camera_params.append(self.exportProperty("lensfile", "./" + file_name))
                camera_params.append(self.exportProperty("aperturediameter", self.aperturediameter))
                camera_params.append(self.exportProperty("focusdistance", self.focusdistance))
                camera_params.append(self.exportProperty("simpleweighting", self.simpleweighting))
                
        
        camera_params_string = ""
        for p in camera_params:
                camera_params_string += p + " "

        data.append(sampler)
        data.append(camera + " " + camera_params_string)
        data.append(integrator + " " + integrator_params )
        return data

def register():
    bpy.utils.register_class(RenderPBRTSettingsScene)
    bpy.types.Scene.pbrt = PointerProperty(type=RenderPBRTSettingsScene)
    exporter.register()
    pbrt.register()
    nodes.register()
    ui.register()

def unregister():
    exporter.unregister()
    pbrt.unregister()
    nodes.unregister()
    ui.unregister()

if __name__ == "__main__":
    register()