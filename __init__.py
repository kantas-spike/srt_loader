if "bpy" in locals():
    import imp

    imp.reload(my_srt)
    imp.reload(props)
    imp.reload(ops)
else:
    from . import my_srt
    from . import props
    from . import ops

import bpy


bl_info = {
    "name": ".srt Loader",
    "author": "kanta",
    "version": (0, 1),
    "blender": (3, 4, 0),
    "location": "VSE > Sidebar",
    "description": "SubRip形式の字幕ファイルと画像格納ディレクトリから、対応する字幕画像をイメージストリップとして追加する",
    "category": "Sequencer",
}


class SRTLOADER_UL_SrtFile(bpy.types.UIList):
    def draw_item(
        self,
        context,
        layout,
        data,
        item,
        icon,
        active_data,
        active_property,
        index=0,
        flt_flag=0,
    ):
        if item.srt_file:
            label = item.srt_file
        else:
            label = ""
        layout.alignment = "LEFT"
        btn = layout.operator(ops.SrtLoaderSelectItem.bl_idname, text=f"{label}")
        btn.item_index = index


class SRTLOADER_PT_SrtList(bpy.types.Panel):
    bl_label = "SRT Loader"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Subtitle Images"
    # bl_context = "objectmode"

    @classmethod
    def poll(cls, context):
        return context.space_data.view_type == "SEQUENCER"

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon="PLUGIN")

    def draw(self, context):
        layout = self.layout
        layout.label(text=".srt File")
        obj = bpy.data.objects[0]

        layout.template_list(
            "SRTLOADER_UL_SrtFile", "", obj, "srt_list", obj, "srt_index"
        )
        row = layout.row()
        row.operator(ops.SrtLoaderAddItem.bl_idname, text="追加")
        row.operator(ops.SrtLoaderRemoveItem.bl_idname, text="削除")

        if len(obj.srt_list) > 0 and obj.srt_index < len(obj.srt_list):
            srt_info = obj.srt_list[obj.srt_index]
            row = layout.row()
            row.prop(srt_info, "srt_file", text="file:")
            row = layout.row()
            row.prop(srt_info, "image_dir", text="image dir:")
            row = layout.row()
            row.prop(srt_info, "channel_no", text="Channel No.:")
            row = layout.row()
            row.prop(srt_info, "offset_x", text="Default Image Offset X")
            row = layout.row()
            row.prop(srt_info, "offset_y", text="Default Image Offset Y")
            row = layout.row()
            row.operator(ops.SrtLoaderImportImages.bl_idname, text="字幕画像を読み込む")
            row = layout.row()
            row.operator(
                ops.SrtLoaderRemoveImportedImages.bl_idname, text="インポートした字幕画像を削除"
            )


class SrtLoaderPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    gimp_path: bpy.props.StringProperty(
        name="Gimp", description="Gimpのパス", default="/usr/local/bin/gimp"
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "gimp_path", text="Gimpのパス")


def menu_fn(self, context):
    self.layout.separator()
    self.layout.operator(ops.StrLoaderGetTimestampOfPlayhead.bl_idname)


classes = (
    props.class_list
    + ops.class_list
    + [
        SRTLOADER_PT_SrtList,
        SRTLOADER_UL_SrtFile,
        SrtLoaderPreferences,
    ]
)


def add_props():
    bpy.types.Scene.srtloarder_settings = bpy.props.PointerProperty(
        type=props.SrtLoaderProperties
    )
    bpy.types.Scene.srtloarder_list = bpy.props.PointerProperty(
        type=props.SrtLoaderCurrentJimakuProperties
    )
    bpy.types.Object.srt_list = bpy.props.CollectionProperty(
        type=props.SrtLoaderProperties
    )
    bpy.types.Object.srt_index = bpy.props.IntProperty(
        name="Index of srt_list", default=0
    )


def remove_props():
    del bpy.types.Scene.srtloarder_settings
    del bpy.types.Scene.srtloarder_list
    del bpy.types.Object.srt_list
    del bpy.types.Object.srt_index


def register():
    for c in classes:
        bpy.utils.register_class(c)

    add_props()

    bpy.types.SEQUENCER_MT_context_menu.append(menu_fn)


def unregister():
    bpy.types.SEQUENCER_MT_context_menu.remove(menu_fn)
    for c in classes:
        bpy.utils.unregister_class(c)

    remove_props()


if __name__ == "__main__":
    register()
