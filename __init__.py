
bl_info = {
    "name": "Heightmap Baker",
    "author": "Abhishek Dey",
    "version": (1, 0, 1),
    "blender": (2, 80, 0),
    "location": "3D View > UI (Right Panel) > Heightmap Baker",
    "description": ("Script to export Heightmap"),
    "warning": "",  # used for warning icon and text in addons panel
    "wiki_url": "https://github.com/obhi-d/heightmap_export/wiki",
    "tracker_url": "https://github.com/enziop/heightmap_export/issues" ,
    "category": "3D View"
}

import bpy
import math
import array
from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty, FloatProperty, EnumProperty

class HeightmapBakerPreferences(bpy.types.AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    range_x : IntProperty(name="Range X", default=True)
    range_y : IntProperty(name="Range Y", default=True)
        
    edge_falloff_active: BoolProperty(name="Edge Falloff Active", default=False)
    single_heightmap   : BoolProperty(name="Single Heightmap", default=True)
    outpath            : StringProperty(name="Output Dir", subtype='FILE_PATH',)

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Streaming")
        box.row().prop(self, "range_x")
        box.row().prop(self, "range_y")
        box.row().prop(self, "edge_falloff_active")
        box.row().prop(self, "single_heightmap")
        box.row().prop(self, "outpath")
        

class Heightmap:

    def __init__(self, width, height, cell_width, cell_height):
        self.size = [width, height]
        self.cell_size = [cell_width, cell_height]
        self.cell = [0, 0]
        self.pixels = [None] * width * height
        self.offset_x = 0
        self.offset_y = 0
        print("Heightmap dim: " + str(self.size))

    def set_cell(self, cell_x, cell_y):
        self.cell[0] = cell_x
        self.cell[1] = cell_y
        self.offset_x = (self.cell_size[0] - 1) * self.cell[0]
        self.offset_y = (self.cell_size[1] - 1) * self.cell[1]

    def set(self, x, y, z):
        px = x + self.offset_x
        py = y + self.offset_y

        p = (py * self.size[0]  + px)
        self.pixels[p] = int(z * 65535.0)

    def save(self, path, cell_x = None, cell_y = None):
        raw16 = array.array('H', self.pixels)
        if cell_x != None and cell_y != None:
            filepath_raw = path + '_x' + str(cell_x) + '_y' + str(cell_y) + '.png'
        else:
            filepath_raw = path + '.r16'

        with open(filepath_raw, "wb") as f:
            raw16.tofile(f)
        

class OBJECT_OT_HeightmapBake(bpy.types.Operator):
    bl_idname = "heightmap_baker.bake"
    bl_label = "Export Heightmap"
    bl_description = "Export selected object as heightmap"

    @classmethod
    def poll(cls, context):
        ob = bpy.context.active_object
        return (ob.ant_landscape and not ob.ant_landscape.sphere_mesh)


    def export_mesh(self, addon_prefs, prop, mesh_size, hm):
                
        from ant_landscape.ant_noise import noise_gen
                
        x_start = -mesh_size[0] / 2.0
        x_step  = mesh_size[0] / hm.cell_size[0]
        y_start = -mesh_size[1] / 2.0
        y_step  = mesh_size[1] / hm.cell_size[1]
        
        for y in range(hm.cell_size[1]):
            for x in range(hm.cell_size[0]):
                co = [x_start + x * x_step, y_start + y * y_step, 0]
                z = noise_gen(co, prop)
                hm.set(x, y, z)


    def execute(self, context):
                
        preferences = context.preferences
        addon_prefs = preferences.addons[__name__].preferences
        if bpy.context.object == None:
            self.report({'ERROR_INVALID_INPUT'}, "Error: no object selected.")
            return{ 'CANCELLED'}
        if bpy.context.object.type != 'MESH':
            self.report({'ERROR_INVALID_INPUT'}, "Error: %s is not a Mesh." % bpy.context.object.name)
            return{ 'CANCELLED'}

        obj = bpy.context.object
        
        
        path           = addon_prefs.outpath
        noise_offset_x = obj.ant_landscape.noise_offset_x
        noise_offset_y = obj.ant_landscape.noise_offset_y
        mesh_size_x    = obj.ant_landscape.mesh_size_x
        mesh_size_y    = obj.ant_landscape.mesh_size_y
        noise_size_x   = mesh_size_x / (obj.ant_landscape.noise_size * obj.ant_landscape.noise_size_x)
        noise_size_y   = mesh_size_y / (obj.ant_landscape.noise_size * obj.ant_landscape.noise_size_y)
        image_width    = obj.ant_landscape.subdivision_x
        image_height   = obj.ant_landscape.subdivision_y
        edge_falloff   = addon_prefs.edge_falloff_active
        single_hm      = addon_prefs.single_heightmap
        edgeoff_orig   = obj.ant_landscape.edge_falloff
        
        ob   = obj.ant_landscape
        keys = ob.keys()
        if not keys:
            return { 'FINISHED'}
        prop = []
        for key in keys:
            prop.append(getattr(ob, key))

        hm = None
        if single_hm:
            hm = Heightmap((image_width - 1) * addon_prefs.range_x + 1, (image_height - 1) * addon_prefs.range_y + 1, image_width, image_height)

        for y in range(addon_prefs.range_y):
            for x in range(addon_prefs.range_x):
                if not single_hm:
                    hm = Heightmap(image_width, image_height, image_width, image_height)
                else:
                    hm.set_cell(x, y)

                noffset_x = noise_offset_x + (x * noise_size_x)
                noffset_y = noise_offset_y + (y * noise_size_y)
                
                prop[14] = noffset_x
                prop[15] = noffset_y

                eoff = "0"
                if (edge_falloff):
                    if x == 0 and 0 == (addon_prefs.range_x-1) and y == 0 and 0 == (addon_prefs.range_y-1):
                        eoff = "11"  #x y
                    elif x == 0 and 0 == (addon_prefs.range_x-1):
                        eoff = "1"  #x
                    elif y == 0 and 0 == (addon_prefs.range_y-1):
                        eoff = "4"  #y
                    elif x == 0 and y == 0:
                        eoff = "7"  #-x +y
                    elif x == 0 and y == (addon_prefs.range_y-1):
                        eoff = "8"  #-x -y
                    elif x == (addon_prefs.range_x-1) and y == 0:
                        eoff = "10"  #+x +y
                    elif x == (addon_prefs.range_x-1) and y == (addon_prefs.range_y-1):
                        eoff = "9"  #+x -y
                    elif x == 0:
                        eoff = "2"  #-x
                    elif y == 0:
                        eoff = "5"  #+y
                    elif x == (addon_prefs.range_x-1):
                        eoff = "3"  #+x
                    elif y == (addon_prefs.range_y-1):
                        eoff = "6"  #-y

                prop[41] = eoff

                # redraw verts
                self.export_mesh(addon_prefs, prop, [mesh_size_x, mesh_size_y], hm)

                if not single_hm:
                    hm.save(path, x, y)

        if single_hm:
            hm.save(path)
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
        box.row().prop(addon_prefs, "range_x")
        box.row().prop(addon_prefs, "range_y")
        box.row().prop(addon_prefs, "edge_falloff_active")
        box.row().prop(addon_prefs, "single_heightmap")
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

        