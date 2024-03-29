if "bpy" in locals():
    import imp

    imp.reload(my_srt)
    imp.reload(props)
    imp.reload(props_default)
    imp.reload(ops)
    imp.reload(utils)
else:
    from . import my_srt
    from . import props
    from . import props_default
    from . import ops
    from . import utils

from typing import Any
import bpy
from bpy.types import Context, UILayout
from bpy.utils import smpte_from_frame
from bpy.app.handlers import persistent
import logging
import os


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


class SrtLoaderPanelJimakuBase:
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "SRT Loader"
    bl_parent_id = "SRTLOADER_PT_Jimaku"

    @classmethod
    def poll(cls, context):
        if context.space_data.view_type != "SEQUENCER":
            return False
        srtloarder_jimaku = bpy.data.objects[0].srtloarder_jimaku
        if len(srtloarder_jimaku.list) <= 0:
            return False
        return True


class SourcePanel(SrtLoaderPanelBase, bpy.types.Panel):
    bl_label = "Source"
    bl_idname = "SRTLOADER_PT_Source"

    def draw(self, context: Context):
        srtloarder_settings = bpy.data.objects[0].srtloarder_settings
        layout = self.layout
        layout_property_row(layout, "Srt File", srtloarder_settings, "srt_file")
        layout_property_row(layout, "Image Dir", srtloarder_settings, "image_dir")
        row = layout.row()
        row.operator(ops.SrtLoaderReadSrtFile.bl_idname, text="Srt File 読み込み")
        row.operator(ops.SrtLoaderResetSrtFile.bl_idname, text="字幕情報の破棄")
        row = layout.row()
        row.operator(ops.SrtLoaderSaveSrtFile.bl_idname, text="Srt Fileへの保存")


class JimakuPanel(SrtLoaderPanelBase, bpy.types.Panel):
    bl_label = "字幕情報"
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
        row = layout.row()
        row.operator(ops.SrtLoaderAddJimaku.bl_idname, text="追加")
        row.operator(ops.SrtLoaderRemoveJimaku.bl_idname, text="削除")

        row = layout.row()
        row.separator()
        row = layout.row()
        row.operator(ops.SrtLoaderGenerateAllJimakuImages.bl_idname, text="字幕画像の一括作成")
        row = layout.row()
        row.operator(
            ops.SrtLoaderRepositionAllJimakuImages.bl_idname, text="字幕画像の一括再配置"
        )
        row = layout.row()
        row.operator(ops.SrtLoaderRemoveAllJimakuImages.bl_idname, text="字幕画像の一括削除")


class JimakuTextAndTimePanel(SrtLoaderPanelJimakuBase, bpy.types.Panel):
    bl_label = "テキストと時間"
    bl_idname = "SRTLOADER_PT_JimakuTextAndTime"

    def draw(self, context: Context):
        srtloarder_jimaku = bpy.data.objects[0].srtloarder_jimaku
        cur_idx = srtloarder_jimaku.index
        jimaku = srtloarder_jimaku.list[cur_idx]

        layout = self.layout
        row = layout.row(align=True)
        split = row.split(factor=0.2)
        split.alignment = "RIGHT"
        split.label(text="No.")
        split = split.split()
        split.label(text=str(jimaku.no))
        row.separator()
        row = layout.row(align=True)
        split = layout.split(factor=0.2, align=True)
        col = split.column(align=True)
        col.alignment = "RIGHT"
        col.label(text="Text")
        col = split.column(align=True)
        for txt in jimaku.text.split("\n"):
            col.label(text=txt)
        split = layout.split(factor=0.2, align=True)
        _ = split.column()
        col = split.column()
        col.operator(ops.SrtLoaderEditJimaku.bl_idname)
        row = layout.row(align=True)
        row.separator()
        row = layout.row(align=True)
        row.operator(ops.SrtLoaderGenerateCurrentJimakuImage.bl_idname, text="字幕画像の作成")
        row = layout.row(align=True)
        row.separator()

        start_frame = jimaku.start_frame
        frame_duration = jimaku.frame_duration
        row = layout.row(align=True)
        split = row.split(factor=0.2)
        split.alignment = "RIGHT"
        split.label(text="Start")
        col = split.column()
        col.prop(
            jimaku,
            "start_frame",
            text=smpte_from_frame(start_frame),
        )
        row = layout.row(align=True)
        split = row.split(factor=0.2)
        split.alignment = "RIGHT"
        split.label(text="Duration")
        col = split.column()
        col.prop(
            jimaku,
            "frame_duration",
            text=smpte_from_frame(frame_duration),
        )
        row = layout.row(align=True)
        row.operator(
            ops.SrtLoaderUpdateJimakuFrameDuration.bl_idname, text="Strip→プロパティー"
        )
        row = layout.row(align=True)
        row.separator()

        row = layout.row(align=True)
        row.operator(
            ops.SrtLoaderRepositionCurrentJimakuImage.bl_idname, text="字幕画像の再配置"
        )


class JimakuSettingsPanel(SrtLoaderPanelJimakuBase, bpy.types.Panel):
    bl_label = "チャンネルと位置"
    bl_idname = "SRTLOADER_PT_JimakuSettings"

    def draw_header(self, context: Context):
        srtloarder_jimaku = bpy.data.objects[0].srtloarder_jimaku

        cur_idx = srtloarder_jimaku.index
        jimaku = srtloarder_jimaku.list[cur_idx]
        row = self.layout.row()
        row.prop(jimaku.settings, "useJimakuSettings", text="")

    def draw(self, context: Context):
        srtloarder_jimaku = bpy.data.objects[0].srtloarder_jimaku

        cur_idx = srtloarder_jimaku.index
        jimaku = srtloarder_jimaku.list[cur_idx]

        layout = self.layout
        layout.enabled = jimaku.settings.useJimakuSettings

        layout_property_row(layout, "Channel No.", jimaku.settings, "channel_no")
        layout_property_row(layout, "Image Offset X", jimaku.settings, "offset_x")
        layout_property_row(layout, "Image Offset Y", jimaku.settings, "offset_y")
        row = layout.row(align=True)
        row.separator()
        row = layout.row(align=True)
        row.operator(
            ops.SrtLoaderUpdateJimakuSettings.bl_idname,
            text="Selected Strip→プロパティー"
        )


class JimakuStylesPanel(SrtLoaderPanelJimakuBase, bpy.types.Panel):
    bl_label = "字幕スタイル"
    bl_idname = "SRTLOADER_PT_JimakuStyles"

    def draw_header(self, context: Context):
        srtloarder_jimaku = bpy.data.objects[0].srtloarder_jimaku

        cur_idx = srtloarder_jimaku.index
        jimaku = srtloarder_jimaku.list[cur_idx]
        row = self.layout.row()
        row.prop(jimaku.styles, "useJimakuStyle", text="")

    def draw(self, context: Context):
        srtloarder_jimaku = bpy.data.objects[0].srtloarder_jimaku
        cur_idx = srtloarder_jimaku.index
        jimaku = srtloarder_jimaku.list[cur_idx]
        preset_name = jimaku.styles.preset_name
        layout = self.layout
        layout.enabled = jimaku.styles.useJimakuStyle
        row = layout.row(align=True)
        split = row.split(factor=0.4)
        split.alignment = "RIGHT"
        split.label(text="プリセット")
        split.menu(SrtLoaderJimakuStylesPresetsMenu.bl_idname, text=preset_name)

        row = layout.row(align=True)
        btn = row.operator(ops.SrtLoaderApplyPresets.bl_idname,
                           text="プリセットの内容をスタイルに反映")
        btn.style_type = "jimaku"


class JimakuPresetControlPanel(SrtLoaderPanelJimakuBase, bpy.types.Panel):
    bl_label = "プリセットの管理"
    bl_idname = "SRTLOADER_PT_JimakuPresetControl"
    bl_parent_id = "SRTLOADER_PT_JimakuStyles"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context: Context):
        srtloarder_jimaku = bpy.data.objects[0].srtloarder_jimaku
        cur_idx = srtloarder_jimaku.index
        jimaku = srtloarder_jimaku.list[cur_idx]
        preset_name = jimaku.styles.preset_name
        layout = self.layout
        row = layout.row()

        col = row.column()
        btn = col.operator(ops.SrtLoaderRenamePresetNameWithDialog.bl_idname,
                           text="プリセット名の変更")
        btn.style_type = "jimaku"
        col.enabled = (preset_name != "default")

        col = row.column()
        btn = col.operator(ops.SrtLoaderDeletePresetWithDialog.bl_idname,
                           text="プリセットの削除")
        btn.style_type = "jimaku"
        col.enabled = (preset_name != "default")

        row = layout.row()
        row.separator()
        row = layout.row()
        btn = row.operator(ops.SrtLoaderOverwriteStyleAsPresetWithDialog.bl_idname,
                           text="現在のスタイルを上書き保存")

        btn.style_type = "jimaku"
        row = layout.row()
        btn = row.operator(ops.SrtLoaderSaveStyleAsPresetWithDialog.bl_idname,
                           text="現在のスタイルを名前を付けて保存")
        btn.style_type = "jimaku"


class JimakuImageStylesPanel(SrtLoaderPanelJimakuBase, bpy.types.Panel):
    bl_label = "Padding設定"
    bl_idname = "SRTLOADER_PT_JimakuImageStyles"
    bl_parent_id = "SRTLOADER_PT_JimakuStyles"

    def draw(self, context: Context):
        srtloarder_jimaku = bpy.data.objects[0].srtloarder_jimaku

        cur_idx = srtloarder_jimaku.index
        jimaku = srtloarder_jimaku.list[cur_idx]

        layout = self.layout
        layout.enabled = jimaku.styles.useJimakuStyle
        layout_property_row(layout, "padding x", jimaku.styles.image, "padding_x")
        layout_property_row(layout, "padding y", jimaku.styles.image, "padding_y")


class JimakuTextStylesPanel(SrtLoaderPanelJimakuBase, bpy.types.Panel):
    bl_label = "テキスト設定"
    bl_idname = "SRTLOADER_PT_JimakuTextStyles"
    bl_parent_id = "SRTLOADER_PT_JimakuStyles"

    def draw(self, context: Context):
        srtloarder_jimaku = bpy.data.objects[0].srtloarder_jimaku

        cur_idx = srtloarder_jimaku.index
        jimaku = srtloarder_jimaku.list[cur_idx]

        layout = self.layout
        layout.enabled = jimaku.styles.useJimakuStyle
        layout_property_row(layout, "font family", jimaku.styles.text, "font_family")
        layout_property_row(layout, "font size", jimaku.styles.text, "size")
        layout_property_row(layout, "font color", jimaku.styles.text, "color")
        layout_property_row(layout, "text align", jimaku.styles.text, "align")
        layout_property_row(layout, "line space", jimaku.styles.text, "line_space_rate")


class JimakuBordersStylesPanel(SrtLoaderPanelJimakuBase, bpy.types.Panel):
    bl_label = "縁取り設定"
    bl_idname = "SRTLOADER_PT_JimakuBordersStyles"
    bl_parent_id = "SRTLOADER_PT_JimakuStyles"

    def draw(self, context: Context):
        srtloarder_jimaku = bpy.data.objects[0].srtloarder_jimaku

        cur_idx = srtloarder_jimaku.index
        jimaku = srtloarder_jimaku.list[cur_idx]

        layout = self.layout
        layout.enabled = jimaku.styles.useJimakuStyle

        layout_property_row(
            layout,
            "縁取り数",
            jimaku.styles.borders,
            "number_of_borders",
        )


class JimakuBordersStyle1Panel(SrtLoaderPanelJimakuBase, bpy.types.Panel):
    bl_label = "縁取り1"
    bl_idname = "SRTLOADER_PT_JimakuBorder1Styles"
    bl_parent_id = "SRTLOADER_PT_JimakuBordersStyles"

    def draw(self, context: Context):
        srtloarder_jimaku = bpy.data.objects[0].srtloarder_jimaku

        cur_idx = srtloarder_jimaku.index
        jimaku = srtloarder_jimaku.list[cur_idx]
        borders = jimaku.styles.borders
        number_of_borders = borders.number_of_borders

        style = borders.style1
        layout = self.layout
        layout.enabled = jimaku.styles.useJimakuStyle and number_of_borders >= 1

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


class JimakuBordersStyle2Panel(SrtLoaderPanelJimakuBase, bpy.types.Panel):
    bl_label = "縁取り2"
    bl_idname = "SRTLOADER_PT_JimakuBorder2Styles"
    bl_parent_id = "SRTLOADER_PT_JimakuBordersStyles"

    def draw(self, context: Context):
        srtloarder_jimaku = bpy.data.objects[0].srtloarder_jimaku

        cur_idx = srtloarder_jimaku.index
        jimaku = srtloarder_jimaku.list[cur_idx]
        borders = jimaku.styles.borders
        number_of_borders = borders.number_of_borders

        style = borders.style2
        layout = self.layout
        layout.enabled = jimaku.styles.useJimakuStyle and number_of_borders >= 2

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


class JimakuShadowStylesPanel(SrtLoaderPanelJimakuBase, bpy.types.Panel):
    bl_label = "Shadow設定"
    bl_idname = "SRTLOADER_PT_JimakuShadowStyles"
    bl_parent_id = "SRTLOADER_PT_JimakuStyles"

    def draw_header(self, context: Context):
        srtloarder_jimaku = bpy.data.objects[0].srtloarder_jimaku

        cur_idx = srtloarder_jimaku.index
        jimaku = srtloarder_jimaku.list[cur_idx]
        shadow = jimaku.styles.shadow
        layout = self.layout
        layout.enabled = jimaku.styles.useJimakuStyle
        layout.prop(shadow, "enabled", text="")

    def draw(self, context: Context):
        srtloarder_jimaku = bpy.data.objects[0].srtloarder_jimaku

        cur_idx = srtloarder_jimaku.index
        jimaku = srtloarder_jimaku.list[cur_idx]
        shadow = jimaku.styles.shadow
        layout = self.layout
        layout.enabled = jimaku.styles.useJimakuStyle and shadow.enabled
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


class JimakuBoxStylesPanel(SrtLoaderPanelJimakuBase, bpy.types.Panel):
    bl_label = "Box設定"
    bl_idname = "SRTLOADER_PT_JimakuBoxStyles"
    bl_parent_id = "SRTLOADER_PT_JimakuStyles"

    def draw_header(self, context: Context):
        srtloarder_jimaku = bpy.data.objects[0].srtloarder_jimaku

        cur_idx = srtloarder_jimaku.index
        jimaku = srtloarder_jimaku.list[cur_idx]
        box = jimaku.styles.box
        layout = self.layout
        layout.enabled = jimaku.styles.useJimakuStyle
        self.layout.prop(box, "enabled", text="")

    def draw(self, context: Context):
        srtloarder_jimaku = bpy.data.objects[0].srtloarder_jimaku

        cur_idx = srtloarder_jimaku.index
        jimaku = srtloarder_jimaku.list[cur_idx]
        box = jimaku.styles.box
        layout = self.layout
        layout.enabled = jimaku.styles.useJimakuStyle and box.enabled
        layout_property_row(
            layout,
            "Boxの色",
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
    bl_label = "デフォルトのチャンネルと位置"
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
        row = layout.row()
        row.separator()
        row = layout.row(align=True)
        row.operator(
            ops.SrtLoaderUpdateDefaultJimakuSettings.bl_idname,
            text="Selected Strip→プロパティー"
        )


class DefaultStylesPanel(SrtLoaderPanelBase, bpy.types.Panel):
    bl_label = "デフォルトのスタイル"
    bl_idname = "SRTLOADER_PT_DefaultStyles"

    def draw(self, context: Context):
        layout = self.layout
        srtloarder_settings = bpy.data.objects[0].srtloarder_settings
        preset_name = srtloarder_settings.styles.preset_name
        row = layout.row(align=True)
        split = row.split(factor=0.4)
        split.alignment = "RIGHT"
        split.label(text="プリセット")
        split.menu(SrtLoaderDefaultStylesPresetsMenu.bl_idname, text=preset_name)
        row = layout.row(align=True)
        btn = row.operator(ops.SrtLoaderApplyPresets.bl_idname, text="プリセットの内容をスタイルに反映")
        btn.style_type = "default"


class DefaultPresetControlPanel(SrtLoaderPanelBase, bpy.types.Panel):
    bl_label = "プリセットの管理"
    bl_idname = "SRTLOADER_PT_DefaultPresetControl"
    bl_parent_id = "SRTLOADER_PT_DefaultStyles"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context: Context):
        srtloarder_settings = bpy.data.objects[0].srtloarder_settings
        preset_name = srtloarder_settings.styles.preset_name
        layout = self.layout
        row = layout.row()

        col = row.column()
        btn = col.operator(ops.SrtLoaderRenamePresetNameWithDialog.bl_idname,
                     text="プリセット名の変更")
        btn.style_type = "default"
        col.enabled = (preset_name != "default")

        col = row.column()
        btn = col.operator(ops.SrtLoaderDeletePresetWithDialog.bl_idname,
                     text="プリセットの削除")
        btn.style_type = "default"
        col.enabled = (preset_name != "default")

        row = layout.row()
        row.separator()
        row = layout.row()
        btn = row.operator(ops.SrtLoaderOverwriteStyleAsPresetWithDialog.bl_idname,
                     text="現在のスタイルを上書き保存")
        btn.style_type = "default"

        row = layout.row()
        btn = row.operator(ops.SrtLoaderSaveStyleAsPresetWithDialog.bl_idname,
                     text="現在のスタイルを名前を付けて保存")
        btn.style_type = "default"


class DefaultImageStylesPanel(SrtLoaderPanelBase, bpy.types.Panel):
    bl_label = "Padding設定"
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
    bl_label = "テキスト設定"
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
    bl_label = "縁取り設定"
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
    bl_label = "Shadow設定"
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
    bl_label = "Box設定"
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
            "Boxの色",
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
        row = layout.row()
        row.separator()
        row = layout.row()
        row.label(text="プリセット")
        row = layout.row()
        row.operator(ops.SrtLoaderSetupAddonPresets.bl_idname, text="デフォルトプリセットを初期値に戻す")


class SrtLoaderDefaultStylesPresetsMenu(bpy.types.Menu):
    bl_idname = "SRTLOADER_MT_DefaultStylesPresets"
    bl_label = "Default Style Presets"
    preset_subdir = "srt_loader/default_styles"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class SrtLoaderJimakuStylesPresetsMenu(bpy.types.Menu):
    bl_idname = "SRTLOADER_MT_JimakuStylesPresets"
    bl_label = "Default Style Presets"
    preset_subdir = "srt_loader/jimaku_styles"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


def menu_fn(self, context):
    self.layout.separator()
    self.layout.operator(ops.StrLoaderGetTimestampOfPlayhead.bl_idname)


classes = (
    props.class_list
    + props_default.class_list
    + ops.class_list
    + [
        SourcePanel,
        JimakuPanel,
        JimakuTextAndTimePanel,
        JimakuSettingsPanel,
        JimakuStylesPanel,
        JimakuPresetControlPanel,
        JimakuTextStylesPanel,
        JimakuBordersStylesPanel,
        JimakuBordersStyle1Panel,
        JimakuBordersStyle2Panel,
        JimakuShadowStylesPanel,
        JimakuBoxStylesPanel,
        JimakuImageStylesPanel,
        JimakuEditor,
        DefaultSettingsPanel,
        DefaultStylesPanel,
        DefaultPresetControlPanel,
        DefaultTextStylesPanel,
        DefaultBordersStylesPanel,
        DefaultBordersStyle1Panel,
        DefaultBordersStyle2Panel,
        DefaultShadowStylesPanel,
        DefaultBoxStylesPanel,
        DefaultImageStylesPanel,
        JimakuList,
        SrtLoaderDefaultStylesPresetsMenu,
        SrtLoaderJimakuStylesPresetsMenu,
        SrtLoaderPreferences,
    ]
)


def add_props():
    bpy.types.Object.srtloarder_settings = bpy.props.PointerProperty(
        type=props_default.SrtLoaderProperties
    )
    bpy.types.Object.srtloarder_jimaku = bpy.props.PointerProperty(
        type=props.SrtLoaderCurrentJimakuProperties
    )


@persistent
def initialize_styles(dummy):
    w = bpy.context.window_manager.windows[0]
    obj = w.scene.camera
    if not obj.srtloarder_settings.initialized:
        print("initialize styles")
        target_styles = obj.srtloarder_settings.styles
        json_data = utils.get_default_style_json_data()
        utils.update_styles(target_styles, json_data)
        obj.srtloarder_settings.initialized = True
    else:
        print("skip initialize styles")


def remove_props():
    del bpy.types.Object.srtloarder_settings
    del bpy.types.Object.srtloarder_jimaku


def setup_logger():
    logging.basicConfig(
        format="%(asctime)s:%(levelname)s:%(funcName)s:%(message)s", level=logging.DEBUG
    )


setup_logger()

preset_dir = utils.get_srtloader_preset_path()
if os.path.exists(preset_dir):
    logging.info(f"preset_dirはセットアップ済み: {preset_dir}")
else:
    logging.info(f"preset_dirは未セットアップ: {preset_dir}")
    utils.setup_addon_presets()

bpy.app.handlers.load_post.append(initialize_styles)


def register():
    for c in classes:
        bpy.utils.register_class(c)

    add_props()
    bpy.types.SEQUENCER_MT_context_menu.append(menu_fn)


def unregister():
    bpy.types.SEQUENCER_MT_context_menu.remove(menu_fn)
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

    remove_props()


if __name__ == "__main__":
    register()
