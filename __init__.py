import sys
import tempfile
import copy
import shutil
import bpy
import traceback
import os
from pathlib import Path
from .fast64_internal import *
from .fast64_internal.panels import SM64_Panel
from .fast64_internal.oot.oot_level import OOT_ObjectProperties

import cProfile
import pstats

# info about add on
bl_info = {
    "name": "Fast64",
    "author": "kurethedead",
    "location": "3DView",
    "description": "Plugin for exporting F3D display lists and other game data related to Super Mario 64.",
    "category": "Import-Export",
    "blender": (3, 1, 0),
}

gameEditorEnum = (
    ("SM64", "SM64", "Super Mario 64"),
    ("OOT", "OOT", "Ocarina Of Time"),
)


class ArmatureApplyWithMesh(bpy.types.Operator):
    # set bl_ properties
    bl_description = (
        "Applies current pose as default pose. Useful for "
        + "rigging an armature that is not in T/A pose. Note that when using "
        + " with an SM64 armature, you must revert to the default pose after "
        + "skinning."
    )
    bl_idname = "object.armature_apply_w_mesh"
    bl_label = "Apply As Rest Pose"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Called on demand (i.e. button press, menu item)
    # Can also be called from operator search menu (Spacebar)
    def execute(self, context):
        try:
            if context.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")

            if len(context.selected_objects) == 0:
                raise PluginError("Armature not selected.")
            elif type(context.selected_objects[0].data) is not bpy.types.Armature:
                raise PluginError("Armature not selected.")

            armatureObj = context.selected_objects[0]
            for child in armatureObj.children:
                if type(child.data) is not bpy.types.Mesh:
                    continue
                armatureModifier = None
                for modifier in child.modifiers:
                    if isinstance(modifier, bpy.types.ArmatureModifier):
                        armatureModifier = modifier
                if armatureModifier is None:
                    continue
                print(armatureModifier.name)
                bpy.ops.object.select_all(action="DESELECT")
                context.view_layer.objects.active = child
                bpy.ops.object.modifier_copy(modifier=armatureModifier.name)
                print(len(child.modifiers))
                attemptModifierApply(armatureModifier)

            bpy.ops.object.select_all(action="DESELECT")
            context.view_layer.objects.active = armatureObj
            bpy.ops.object.mode_set(mode="POSE")
            bpy.ops.pose.armature_apply()
            if context.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")
        except Exception as e:
            if context.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")
            raisePluginError(self, e)
            return {"CANCELLED"}

        self.report({"INFO"}, "Applied armature with mesh.")
        return {"FINISHED"}  # must return a set


class AddBoneGroups(bpy.types.Operator):
    # set bl_ properties
    bl_description = (
        "Add bone groups respresenting other node types in " + "SM64 geolayouts (ex. Shadow, Switch, Function)."
    )
    bl_idname = "object.add_bone_groups"
    bl_label = "Add Bone Groups"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Called on demand (i.e. button press, menu item)
    # Can also be called from operator search menu (Spacebar)
    def execute(self, context):
        try:
            if context.mode != "OBJECT" and context.mode != "POSE":
                raise PluginError("Operator can only be used in object or pose mode.")
            elif context.mode == "POSE":
                bpy.ops.object.mode_set(mode="OBJECT")

            if len(context.selected_objects) == 0:
                raise PluginError("Armature not selected.")
            elif type(context.selected_objects[0].data) is not bpy.types.Armature:
                raise PluginError("Armature not selected.")

            armatureObj = context.selected_objects[0]
            createBoneGroups(armatureObj)
        except Exception as e:
            raisePluginError(self, e)
            return {"CANCELLED"}

        self.report({"INFO"}, "Created bone groups.")
        return {"FINISHED"}  # must return a set


class CreateMetarig(bpy.types.Operator):
    # set bl_ properties
    bl_description = (
        "SM64 imported armatures are usually not good for "
        + "rigging. There are often intermediate bones between deform bones "
        + "and they don't usually point to their children. This operator "
        + "creates a metarig on armature layer 4 useful for IK."
    )
    bl_idname = "object.create_metarig"
    bl_label = "Create Animatable Metarig"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Called on demand (i.e. button press, menu item)
    # Can also be called from operator search menu (Spacebar)
    def execute(self, context):
        try:
            if context.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")

            if len(context.selected_objects) == 0:
                raise PluginError("Armature not selected.")
            elif type(context.selected_objects[0].data) is not bpy.types.Armature:
                raise PluginError("Armature not selected.")

            armatureObj = context.selected_objects[0]
            generateMetarig(armatureObj)
        except Exception as e:
            raisePluginError(self, e)
            return {"CANCELLED"}

        self.report({"INFO"}, "Created metarig.")
        return {"FINISHED"}  # must return a set


class SM64_AddWaterBox(AddWaterBox):
    bl_idname = "object.sm64_add_water_box"

    scale: bpy.props.FloatProperty(default=10)
    preset: bpy.props.StringProperty(default="Shaded Solid")
    matName: bpy.props.StringProperty(default="sm64_water_mat")

    def setEmptyType(self, emptyObj):
        emptyObj.sm64_obj_type = "Water Box"


class SM64_ArmatureToolsPanel(SM64_Panel):
    bl_idname = "SM64_PT_armature_tools"
    bl_label = "SM64 Tools"

    # called every frame
    def draw(self, context):
        col = self.layout.column()
        col.operator(ArmatureApplyWithMesh.bl_idname)
        col.operator(AddBoneGroups.bl_idname)
        col.operator(CreateMetarig.bl_idname)
        col.operator(SM64_AddWaterBox.bl_idname)


class F3D_GlobalSettingsPanel(bpy.types.Panel):
    bl_idname = "F3D_PT_global_settings"
    bl_label = "F3D Global Settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Fast64"

    @classmethod
    def poll(cls, context):
        return True

    # called every frame
    def draw(self, context):
        col = self.layout.column()
        col.scale_y = 1.1  # extra padding
        prop_split(col, context.scene, "f3d_type", "F3D Microcode")
        col.prop(context.scene, "isHWv1")
        col.prop(context.scene, "saveTextures")
        col.prop(context.scene, "f3d_simple", text="Simple Material UI")
        col.prop(context.scene, "generateF3DNodeGraph", text="Generate F3D Node Graph For Materials")
        col.prop(context.scene, "decomp_compatible", invert_checkbox=True, text="Homebrew Compatibility")
        col.prop(context.scene, "ignoreTextureRestrictions")
        if context.scene.ignoreTextureRestrictions:
            col.box().label(text="Width/height must be < 1024. Must be RGBA32. Must be png format.")


class Fast64_GlobalObjectPanel(bpy.types.Panel):
    bl_label = "Global Object Inspector"
    bl_idname = "OBJECT_PT_OOT_Global_Object_Inspector"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.object.data is None

    def draw(self, context):
        box = self.layout
        prop_split(box, context.scene, "gameEditorMode", "Game")


class Fast64_GlobalSettingsPanel(bpy.types.Panel):
    bl_idname = "FAST64_PT_global_settings"
    bl_label = "Fast64 Global Settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Fast64"

    @classmethod
    def poll(cls, context):
        return True

    # called every frame
    def draw(self, context):
        col = self.layout.column()
        col.scale_y = 1.1  # extra padding
        prop_split(col, context.scene, "gameEditorMode", "Game")
        col.prop(context.scene, "exportHiddenGeometry")
        col.prop(context.scene, "fullTraceback")


class Fast64_GlobalToolsPanel(bpy.types.Panel):
    bl_idname = "FAST64_PT_global_tools"
    bl_label = "Fast64 Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Fast64"

    @classmethod
    def poll(cls, context):
        return True

    # called every frame
    def draw(self, context):
        col = self.layout.column()
        col.operator(ArmatureApplyWithMesh.bl_idname)
        # col.operator(CreateMetarig.bl_idname)

class Fast64Settings_Properties(bpy.types.PropertyGroup):
    """Settings affecting exports for all games found in scene.fast64.settings"""

    version: bpy.props.IntProperty(name="Fast64Settings_Properties Version", default=0)


class Fast64_Properties(bpy.types.PropertyGroup):
    """
    Properties in scene.fast64.
    All new properties should be children of one of these three property groups.
    """

    sm64: bpy.props.PointerProperty(type=SM64_Properties, name="SM64 Properties")
    oot: bpy.props.PointerProperty(type=OOT_Properties, name="OOT Properties")
    settings: bpy.props.PointerProperty(type=Fast64Settings_Properties, name="Fast64 Settings")
    renderSettings: bpy.props.PointerProperty(type=Fast64RenderSettings_Properties, name="Fast64 Render Settings")


class Fast64_BoneProperties(bpy.types.PropertyGroup):
    """
    Properties in bone.fast64 (bpy.types.Bone)
    All new bone properties should be children of this property group.
    """

    sm64: bpy.props.PointerProperty(type=SM64_BoneProperties, name="SM64 Properties")


class Fast64_ObjectProperties(bpy.types.PropertyGroup):
    """
    Properties in object.fast64 (bpy.types.Object)
    All new object properties should be children of this property group.
    """

    sm64: bpy.props.PointerProperty(type=SM64_ObjectProperties, name="SM64 Object Properties")
    oot: bpy.props.PointerProperty(type=OOT_ObjectProperties, name="OOT Object Properties")

class UpgradeF3DMaterialsDialog(bpy.types.Operator):
    bl_idname = "dialog.upgrade_f3d_materials"
    bl_label = "Upgrade F3D Materials"
    bl_options = {'REGISTER', 'UNDO'}
    
    done = False

    def draw(self, context):
        layout = self.layout
        if self.done:
            layout.label(text="Success!")
            box = layout.box()
            box.label(text="Materials were successfully upgraded.")
            box.label(text="Please purge your remaining materials.")

            purge_box = box.box()
            purge_box.scale_y = 0.25
            purge_box.separator(factor=0.5)
            purge_box.label(text="How to purge:")
            purge_box.separator(factor=0.5)
            purge_box.label(text='Go to the outliner, change the display mode')
            purge_box.label(text='to "Orphan Data" (broken heart icon)')
            purge_box.separator(factor=0.25)
            purge_box.label(text='Click "Purge" in the top right corner.')
            purge_box.separator(factor=0.25)
            purge_box.label(text='Purge multiple times until the node groups')
            purge_box.label(text='are gone.')
            layout.separator(factor=0.25)
            layout.label(text="You may click anywhere to close this dialog.")
            return
        layout.alert = True
        box = layout.box()
        box.label(text="Your project contains F3D materials that need to be upgraded in order to continue!")
        box.label(text="Before upgrading, make sure to create a duplicate of this blend file before continuing.")
        box.separator()

        col = box.column()
        col.alignment = 'CENTER'
        col.alert = True
        col.label(text="Upgrade F3D Materials?")
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=600)

    def execute(self, context: 'bpy.types.Context'):
        if context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        upgradeF3DVersionAll(
            [obj for obj in bpy.data.objects if isinstance(obj.data, bpy.types.Mesh)],
            bpy.data.armatures,
            MatUpdateConvert.version,
        )
        self.done = True
        return {'FINISHED'}

# def updateGameEditor(scene, context):
# 	if scene.currentGameEditorMode == 'SM64':
# 		sm64_panel_unregister()
# 	elif scene.currentGameEditorMode == 'Z64':
# 		oot_panel_unregister()
# 	else:
# 		raise PluginError("Unhandled game editor mode " + str(scene.currentGameEditorMode))
#
# 	if scene.gameEditorMode == 'SM64':
# 		sm64_panel_register()
# 	elif scene.gameEditorMode == 'Z64':
# 		oot_panel_register()
# 	else:
# 		raise PluginError("Unhandled game editor mode " + str(scene.gameEditorMode))
#
# 	scene.currentGameEditorMode = scene.gameEditorMode

classes = (
    Fast64Settings_Properties,
    Fast64RenderSettings_Properties,
    Fast64_Properties,
    Fast64_BoneProperties,
    Fast64_ObjectProperties,
    ArmatureApplyWithMesh,
    AddBoneGroups,
    CreateMetarig,
    SM64_AddWaterBox,
    # Fast64_GlobalObjectPanel,
    F3D_GlobalSettingsPanel,
    Fast64_GlobalSettingsPanel,
    SM64_ArmatureToolsPanel,
    Fast64_GlobalToolsPanel,
    UpgradeF3DMaterialsDialog,
)


def upgrade_changed_props():
    """Set scene properties after a scene loads, used for migrating old properties"""
    SM64_Properties.upgrade_changed_props()
    SM64_ObjectProperties.upgrade_changed_props()

def upgrade_scene_props_node():
    '''update f3d materials with SceneProperties node'''
    has_old_f3d_mats = bool(len([
        mat for mat in bpy.data.materials if mat.is_f3d and mat.mat_ver < MatUpdateConvert.version
    ]))
    if has_old_f3d_mats:
        bpy.ops.dialog.upgrade_f3d_materials('INVOKE_DEFAULT')

    # upgradeF3DVersionAll(
    #     [obj for obj in bpy.data.objects if isinstance(obj.data, bpy.types.Mesh)],
    #     bpy.data.armatures,
    #     MatUpdateConvert.version,
    # )
        
    # for mat in bpy.data.materials:
    #     if mat.is_f3d and hasNodeGraph(mat):
    #         node_tree: bpy.types.NodeTree = mat.node_tree
    #         for node in node_tree.nodes:
    #             if node.name == 'SceneProperties':
    #                 continue
    #             try:
    #                 node_tree.nodes.remove(node.name)
    #             except:
    #                 print('ERROR: could not remove', node.name)
    #         createScenePropertiesForMaterial(mat)
    #         update_preset_manual(mat, bpy.context)
            

@bpy.app.handlers.persistent
def after_load(_a, _b):
    # link_f3d_material_library()
    upgrade_changed_props()
    upgrade_scene_props_node()


# called on add-on enabling
# register operators and panels here
# append menu layout drawing function to an existing window
def register():
    mat_register()
    render_engine_register()
    bsdf_conv_register()
    sm64_register(True)
    oot_register(True)

    for cls in classes:
        register_class(cls)

    bsdf_conv_panel_regsiter()
    f3d_writer_register()
    f3d_parser_register()

    # ROM

    bpy.types.Scene.decomp_compatible = bpy.props.BoolProperty(name="Decomp Compatibility", default=True)
    bpy.types.Scene.ignoreTextureRestrictions = bpy.props.BoolProperty(
        name="Ignore Texture Restrictions (Breaks CI Textures)"
    )
    bpy.types.Scene.fullTraceback = bpy.props.BoolProperty(name="Show Full Error Traceback", default=False)
    bpy.types.Scene.gameEditorMode = bpy.props.EnumProperty(name="Game", default="SM64", items=gameEditorEnum)
    bpy.types.Scene.saveTextures = bpy.props.BoolProperty(name="Save Textures As PNGs (Breaks CI Textures)")
    bpy.types.Scene.generateF3DNodeGraph = bpy.props.BoolProperty(name="Generate F3D Node Graph", default=True)
    bpy.types.Scene.exportHiddenGeometry = bpy.props.BoolProperty(name="Export Hidden Geometry", default=True)
    bpy.types.Scene.blenderF3DScale = bpy.props.FloatProperty(name="F3D Blender Scale", default=100, update=on_update_render_settings)

    bpy.types.Scene.fast64 = bpy.props.PointerProperty(type=Fast64_Properties, name="Fast64 Properties")
    bpy.types.Bone.fast64 = bpy.props.PointerProperty(type=Fast64_BoneProperties, name="Fast64 Bone Properties")
    bpy.types.Object.fast64 = bpy.props.PointerProperty(type=Fast64_ObjectProperties, name="Fast64 Object Properties")

    bpy.types.Scene.alreadyLinkedMaterialNodes = bpy.props.BoolProperty(name="Already Linked New Material Nodes", default=False)

    bpy.app.handlers.load_post.append(after_load)


# called on add-on disabling
def unregister():
    f3d_writer_unregister()
    f3d_parser_unregister()
    sm64_unregister(True)
    oot_unregister(True)
    mat_unregister()
    bsdf_conv_unregister()
    bsdf_conv_panel_unregsiter()
    render_engine_unregister()

    del bpy.types.Scene.fullTraceback
    del bpy.types.Scene.decomp_compatible
    del bpy.types.Scene.ignoreTextureRestrictions
    del bpy.types.Scene.saveTextures
    del bpy.types.Scene.gameEditorMode
    del bpy.types.Scene.generateF3DNodeGraph
    del bpy.types.Scene.exportHiddenGeometry
    del bpy.types.Scene.blenderF3DScale

    del bpy.types.Scene.fast64
    del bpy.types.Bone.fast64
    del bpy.types.Object.fast64

    for cls in classes:
        unregister_class(cls)

    bpy.app.handlers.load_post.remove(after_load)
