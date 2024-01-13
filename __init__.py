if "bpy" in locals():
    import imp

    imp.reload(my_srt)
    imp.reload(props)
    imp.reload(ops)
else:
    from . import my_srt
    from . import props
    from . import ops

from typing import Any
import bpy
from bpy.types import Context, UILayout


bl_info = {
    "name": ".srt Loader",
    "author": "kanta",
    "version": (0, 1),
    "blender": (3, 4, 0),
    "location": "VSE > Sidebar",
    "description": "SubRip形式の字幕ファイルと画像格納ディレクトリから、対応する字幕画像をイメージストリップとして追加する",
    "category": "Sequencer",
}


def layout_property_row(layout, label, obj, prop_name, alignment="RIGHT", factor=0.4):
    row = layout.row(align=True)
    split = row.split(factor=factor)
    split.alignment = alignment
    split.label(text=label)
    split.prop(obj, prop_name, text="")


class SrtLoaderPanelBase:
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "SRT Loader"

    @classmethod
    def poll(cls, context):
        return context.space_data.view_type == "SEQUENCER"


class SourcePanel(SrtLoaderPanelBase, bpy.types.Panel):
    bl_label = "Source"
    bl_idname = "SRTLOADER_PT_Source"

    def draw(self, context: Context):
        srtloarder_settings = bpy.data.objects[0].srtloarder_settings
        layout = self.layout
        layout_property_row(layout, "Srt File", srtloarder_settings, "srt_file")
        layout_property_row(layout, "Image Dir", srtloarder_settings, "image_dir")
        row = layout.row()
        row.operator(ops.SrtLoaderReadSrtFile.bl_idname, text="読み込み")


class JimakuPanel(SrtLoaderPanelBase, bpy.types.Panel):
    bl_label = "字幕"
    bl_idname = "SRTLOADER_PT_Jimaku"

    def draw(self, context: Context):
        srtloarder_jimaku = bpy.data.objects[0].srtloarder_jimaku
        layout = self.layout
        row = layout.row()
        row.template_list(
            JimakuList.bl_idname,
            "",
            srtloarder_jimaku,
            "list",
            srtloarder_jimaku,
            "index",
        )
        if len(srtloarder_jimaku.list) > 0:
            cur_idx = srtloarder_jimaku.index
            jimaku = srtloarder_jimaku.list[cur_idx]

            layout = self.layout
            layout_property_row(layout, "No.", jimaku, "no")
            row = layout.row(align=True)
            row.alignment = "LEFT"
            row.label(text="テキスト")
            for txt in jimaku.text.split("\n"):
                row = layout.split(factor=0.05)
                row.label(text="")
                row.label(text=txt)
            row = layout.row(align=True)
            row.alignment = "RIGHT"
            row.operator(ops.SrtLoaderEditJimaku.bl_idname)
            # row.prop(jimaku, "text", text="", expand=True)


class JimakuEditor(bpy.types.Panel):
    bl_space_type = "TEXT_EDITOR"
    bl_region_type = "UI"
    bl_category = "Text"
    bl_label = "字幕編集"
    bl_idname = "SRTLOADER_PT_JimakuEditor"

    @classmethod
    def poll(cls, context):
        srtloarder_jimaku = bpy.data.objects[0].srtloarder_jimaku
        return srtloarder_jimaku.jimaku_editing

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.operator(ops.SrtLoaderSaveJimaku.bl_idname)
        col.operator(ops.SrtLoaderCancelJimaku.bl_idname)


class DefaultSettingsPanel(SrtLoaderPanelBase, bpy.types.Panel):
    bl_label = "デフォルト設定"
    bl_idname = "SRTLOADER_PT_DefaultSettings"

    def draw(self, context: Context):
        srtloarder_settings = bpy.data.objects[0].srtloarder_settings
        layout = self.layout
        layout_property_row(
            layout, "Channel No.", srtloarder_settings.settings, "channel_no"
        )
        layout_property_row(
            layout, "Image Offset X", srtloarder_settings.settings, "offset_x"
        )
        layout_property_row(
            layout, "Image Offset Y", srtloarder_settings.settings, "offset_y"
        )


class DefaultStylesPanel(SrtLoaderPanelBase, bpy.types.Panel):
    bl_label = "デフォルトスタイル"
    bl_idname = "SRTLOADER_PT_DefaultStyles"

    def draw(self, context: Context):
        pass


class DefaultImageStylesPanel(SrtLoaderPanelBase, bpy.types.Panel):
    bl_label = "字幕画像スタイル"
    bl_idname = "SRTLOADER_PT_DefaultImageStyles"
    bl_parent_id = "SRTLOADER_PT_DefaultStyles"

    def draw(self, context: Context):
        srtloarder_settings = bpy.data.objects[0].srtloarder_settings
        layout = self.layout
        layout_property_row(
            layout, "padding x", srtloarder_settings.styles.image, "padding_x"
        )
        layout_property_row(
            layout, "padding y", srtloarder_settings.styles.image, "padding_y"
        )


class DefaultTextStylesPanel(SrtLoaderPanelBase, bpy.types.Panel):
    bl_label = "テキストスタイル"
    bl_idname = "SRTLOADER_PT_DefaultTextStyles"
    bl_parent_id = "SRTLOADER_PT_DefaultStyles"

    def draw(self, context: Context):
        srtloarder_settings = bpy.data.objects[0].srtloarder_settings
        layout = self.layout
        layout_property_row(
            layout, "font family", srtloarder_settings.styles.text, "font_family"
        )
        layout_property_row(
            layout, "font size", srtloarder_settings.styles.text, "size"
        )
        layout_property_row(
            layout, "font color", srtloarder_settings.styles.text, "color"
        )
        layout_property_row(
            layout, "text align", srtloarder_settings.styles.text, "align"
        )
        layout_property_row(
            layout, "line space", srtloarder_settings.styles.text, "line_space_rate"
        )


class DefaultBordersStylesPanel(SrtLoaderPanelBase, bpy.types.Panel):
    bl_label = "縁取りスタイル"
    bl_idname = "SRTLOADER_PT_DefaultBordersStyles"
    bl_parent_id = "SRTLOADER_PT_DefaultStyles"

    def draw(self, context: Context):
        borders = bpy.data.objects[0].srtloarder_settings.styles.borders
        layout = self.layout
        layout_property_row(
            layout,
            "縁取り数",
            borders,
            "number_of_borders",
        )


class DefaultBordersStyle1Panel(SrtLoaderPanelBase, bpy.types.Panel):
    bl_label = "縁取り1"
    bl_idname = "SRTLOADER_PT_DefaultBorder1Styles"
    bl_parent_id = "SRTLOADER_PT_DefaultBordersStyles"

    def draw(self, context: Context):
        borders = bpy.data.objects[0].srtloarder_settings.styles.borders
        number_of_borders = borders.number_of_borders
        style = borders.style1
        layout = self.layout
        if number_of_borders < 1:
            layout.enabled = False
        layout_property_row(
            layout,
            "縁取り色",
            style,
            "color",
        )
        layout_property_row(
            layout,
            "縁取りサイズ",
            style,
            "rate",
        )
        layout_property_row(
            layout,
            "ぼかし幅",
            style,
            "feather",
        )


class DefaultBordersStyle2Panel(SrtLoaderPanelBase, bpy.types.Panel):
    bl_label = "縁取り2"
    bl_idname = "SRTLOADER_PT_DefaultBorder2Styles"
    bl_parent_id = "SRTLOADER_PT_DefaultBordersStyles"

    def draw(self, context: Context):
        borders = bpy.data.objects[0].srtloarder_settings.styles.borders
        number_of_borders = borders.number_of_borders
        style = borders.style2
        layout = self.layout

        if number_of_borders < 2:
            layout.enabled = False
        layout_property_row(
            layout,
            "縁取り色",
            style,
            "color",
        )
        layout_property_row(
            layout,
            "縁取りサイズ",
            style,
            "rate",
        )
        layout_property_row(
            layout,
            "ぼかし幅",
            style,
            "feather",
        )


class DefaultShadowStylesPanel(SrtLoaderPanelBase, bpy.types.Panel):
    bl_label = "影スタイル"
    bl_idname = "SRTLOADER_PT_DefaultShadowStyles"
    bl_parent_id = "SRTLOADER_PT_DefaultStyles"

    def draw_header(self, context: Context):
        shadow = bpy.data.objects[0].srtloarder_settings.styles.shadow
        self.layout.prop(shadow, "enabled", text="")

    def draw(self, context: Context):
        shadow = bpy.data.objects[0].srtloarder_settings.styles.shadow
        layout = self.layout
        layout.enabled = shadow.enabled
        layout_property_row(
            layout,
            "影の色",
            shadow,
            "color",
        )
        layout_property_row(
            layout,
            "Offset X",
            shadow,
            "offset_x",
        )
        layout_property_row(
            layout,
            "Offset Y",
            shadow,
            "offset_y",
        )
        layout_property_row(
            layout,
            "ぼかし半径",
            shadow,
            "blur_radius",
        )


class DefaultBoxStylesPanel(SrtLoaderPanelBase, bpy.types.Panel):
    bl_label = "BOXスタイル"
    bl_idname = "SRTLOADER_PT_DefaultBoxStyles"
    bl_parent_id = "SRTLOADER_PT_DefaultStyles"

    def draw_header(self, context: Context):
        box = bpy.data.objects[0].srtloarder_settings.styles.box
        self.layout.prop(box, "enabled", text="")

    def draw(self, context: Context):
        box = bpy.data.objects[0].srtloarder_settings.styles.box
        layout = self.layout
        layout.enabled = box.enabled
        layout_property_row(
            layout,
            "BOXの色",
            box,
            "color",
        )
        layout_property_row(
            layout,
            "Padding X",
            box,
            "padding_x",
        )
        layout_property_row(
            layout,
            "Padding Y",
            box,
            "padding_y",
        )


class JimakuList(bpy.types.UIList):
    bl_idname = "SRTLOADER_UL_Jimaku"

    def draw_item(
        self,
        context: Context | None,
        layout: UILayout,
        data: Any | None,
        item: Any | None,
        icon: int | None,
        active_data: Any,
        active_property: str,
        index: Any | None = 0,
        flt_flag: Any | None = 0,
    ):
        layout.alignment = "LEFT"
        layout.label(text=f"{'{:>2}'.format(item.no)}:  {item.text}")


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
        SourcePanel,
        JimakuPanel,
        JimakuEditor,
        SrtLoaderPreferences,
        DefaultSettingsPanel,
        DefaultStylesPanel,
        DefaultImageStylesPanel,
        DefaultTextStylesPanel,
        DefaultBordersStylesPanel,
        DefaultBordersStyle1Panel,
        DefaultBordersStyle2Panel,
        DefaultShadowStylesPanel,
        DefaultBoxStylesPanel,
        JimakuList,
    ]
)


def add_props():
    bpy.types.Object.srtloarder_settings = bpy.props.PointerProperty(
        type=props.SrtLoaderProperties
    )
    bpy.types.Object.srtloarder_jimaku = bpy.props.PointerProperty(
        type=props.SrtLoaderCurrentJimakuProperties
    )
    # print(len(bpy.data.objects))
    # print(settings)


def remove_props():
    del bpy.types.Object.srtloarder_settings
    del bpy.types.Object.srtloarder_jimaku


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
