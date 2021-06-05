
bl_info = {
    "name": "Heightmap Baker",
    "author": "Abhishek Dey",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "3D View > UI (Right Panel) > Heightmap Baker",
    "description": ("Script to export Heightmap"),
    "warning": "",  # used for warning icon and text in addons panel
    "wiki_url": "https://github.com/obhi-d/heightmap_export/wiki",
    "tracker_url": "https://github.com/enziop/heightmap_export/issues" ,
    "category": "3D View"
}

import bpy
from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty

class HeightmapBakerPreferences(bpy.types.AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    width: bpy.props.IntProperty(
        name="Width",
        default=True)
    height: bpy.props.IntProperty(
        name="Height",
        default=True)
        
    outpath: StringProperty(
        name="Output Dir",
        subtype='FILE_PATH',
    )

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.row().prop(self, "width")
        box.row().prop(self, "height")
        box.row().prop(self, "outpath")


class OBJECT_OT_HeightmapBake(bpy.types.Operator):
    bl_idname = "heightmap_baker.bake"
    bl_label = "Export Heightmap"
    bl_description = "Export selected object as heightmap"

    def execute(self, context):
        preferences = context.preferences
        addon_prefs = preferences.addons[__name__].preferences
        if bpy.context.object == None:
            self.report({'ERROR_INVALID_INPUT'}, "Error: no object selected.")
            return{ 'CANCELLED'}
        if bpy.context.object.type != 'MESH':
            self.report({'ERROR_INVALID_INPUT'}, "Error: %s is not a Mesh." % bpy.context.object.name)
            return{ 'CANCELLED'}
            
        mesh = bpy.context.object.data
        x_mesh_width  = bpy.context.object.dimensions.x
        x_mesh_height = bpy.context.object.dimensions.y
        z_max = bpy.context.object.dimensions.z
        
        range_x_start = -x_mesh_width / 2.0
        range_x_end = x_mesh_width / 2.0
        range_y_start = -x_mesh_height / 2.0
        range_y_end = x_mesh_height / 2.0
        
        image_width  = addon_prefs.width
        image_height = addon_prefs.height
               
        scene = bpy.context.scene
        scene.render.image_settings.color_depth = '16'
        
        image = bpy.data.images.new("Heightmap", image_width, image_height)
        
        pixels = [None] * image_width * image_height * 4
        v_height = [0.0] * (image_width + 1) * (image_height + 1)
        
        for v in mesh.vertices:
            x = int(((v.co.x - range_x_start) / x_mesh_width) * image_width)
            y = int(((v.co.y - range_y_start) / x_mesh_height) * image_height)
            z = (v.co.z / z_max)
            p = (y * image_width + x)
            v_height[p] = z
        
        for x in range(image_width):
            for y in range(image_height):
                p0 = ((y + 0) * image_width + (x + 0))
                p1 = ((y + 1) * image_width + (x + 0))
                p2 = ((y + 0) * image_width + (x + 1))
                p3 = ((y + 1) * image_width + (x + 1))
                p4 = p0 * 4
                h  = (v_height[p0] + v_height[p1] + v_height[p2] + v_height[p3]) * 0.25
                pixels[p4 + 0] = h
                pixels[p4 + 1] = h
                pixels[p4 + 2] = h
                pixels[p4 + 3] = h
            
        image.pixels = pixels
        image.filepath_raw = addon_prefs.outpath
        image.file_format = 'PNG'
        image.save()
        
        return{ 'FINISHED'}


class HeightmapBAKER_VIEW_3D_PT_panel(bpy.types.Panel):
    bl_label = "Heightmap Baker"
    bl_idname = "HeightmapBAKER_VIEW_3D_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Heightmap"
    bl_description = "..."

    def draw(self, context):
        layout = self.layout
        preferences = context.preferences
        addon_prefs = preferences.addons[__name__].preferences
        box = layout.box()
        # Options for how to do the conversion
        box.row().prop(addon_prefs, "width")
        box.row().prop(addon_prefs, "height")
        box.row().prop(addon_prefs, "outpath")
        box.row().operator('heightmap_baker.bake')

classes = (
    OBJECT_OT_HeightmapBake,
    HeightmapBAKER_VIEW_3D_PT_panel,
)
#register, unregister = bpy.utils.register_classes_factory(classes)

def register():
    bpy.utils.register_class(HeightmapBakerPreferences)
    for cls in classes:
        print("Registering: " + cls.bl_idname)
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        print("Unregistering: " + cls.bl_idname)
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_class(HeightmapBakerPreferences)

if __name__ == "__main__":
    register()

        