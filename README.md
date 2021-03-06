# io_export_blend_to_renderer

Blender addon to export Blender scene files in format for external renderers. Addon compatible with Blender 2.79.

## External Renderer

### PBRT

Export selected meshes, lamps, camera to PBRT v3 scene format. 

Components  | Features
:-----------|:-----------
Meshes      | All selected meshes are exported in .ply file in models directory and other information inside .pbrt file. Export mesh material inside pbrt scene file.
Lamps       | Selected lamps are exported in .pbrt file. Convert blender lamps types (POINT, SUN, SPOT, ...) to pbrt lamp types. **Supported** : distant, point with from and to point. Infinite. Envmap and environement color is also supported **ToDo** Spot, Area lights.
Materials   | Pbrt node in node editor pbrt material : disney, glass, kdsubsurface, matte, metal, mirror, plastic, subsurface, mixure, substrate
Textures    | Support Texture in Color channel. Copy texture file in textures folder near models export folder
Camera      | Simple perspective camera with position and look at.
Sampler     | All sampler are supported. PixelsSample can be specify. StratifiedSampler  parameters are not supported.
Intergrator | All integrators are supported with their parameter
Film        | A PNG file named "output.png" with resolution from blender render resolution

**UI**

Use node editor to define object material with PBRT Material category. 
Use basic Blender render interface to define image resolution and output path for export path

Specific UI for PBRT with sampling and integrator parameters.
Film parameters : Resolution are same value of blender render resolution. 

### Mitsuba 0.6

ToDo


