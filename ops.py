from typing import Set
import bpy
import os
import datetime
import shutil

from bpy.types import Context, Event
from . import my_srt
from . import utils


# class SrtLoaderRemoveImportedImages(bpy.types.Operator):
#     bl_idname = "srt_loader.remove_imported_images"
#     bl_label = "インポートした字幕画像を削除する"
#     bl_description = "インポートした字幕画像を削除する"
#     bl_options = {"REGISTER", "UNDO"}

#     @classmethod
#     def poll(cls, context):
#         obj = bpy.data.objects[0]
#         srt_info = obj.srt_list[obj.srt_index]
#         if not srt_info.srt_file:
#             return False
#         else:
#             return True

#     def execute(self, context):
#         obj = bpy.data.objects[0]

#         srt_info = obj.srt_list[obj.srt_index]
#         srt_uuid = srt_info.uuid
#         if srt_uuid is None:
#             return {"CANCELLED"}

#         imported_images = []
#         sequences = context.scene.sequence_editor.sequences
#         for seq in sequences:
#             if seq.type == "IMAGE" and seq.get("srt_uuid") == srt_uuid:
#                 imported_images.append(seq)

#         for seq in imported_images:
#             sequences.remove(seq)

#         return {"FINISHED"}


# class SrtLoaderImportImages(bpy.types.Operator):
#     bl_idname = "srt_loader.import_images"
#     bl_label = "字幕画像をインポートする"
#     bl_description = "画像ディレクトリから字幕画像をインポートする"
#     bl_options = {"REGISTER", "UNDO"}

#     @classmethod
#     def poll(cls, context):
#         obj = bpy.data.objects[0]
#         srt_info = obj.srt_list[obj.srt_index]
#         if (not srt_info.srt_file) or (not srt_info.image_dir):
#             return False
#         else:
#             return True

#     def load_jimaku(
#         self, srt_path, img_dir, channel_no=4, offset_x=0, offset_y=-400, srt_uuid=None
#     ):
#         abs_srt_path = bpy.path.abspath(srt_path)
#         abs_img_dir = bpy.path.abspath(img_dir)

#         fps = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base

#         items = my_srt.read_srt_file(abs_srt_path)
#         for item in items:
#             img_path = os.path.join(abs_img_dir, f"{item['no']}.png")
#             if os.path.isfile(img_path):
#                 # load image
#                 start_frame = round(item["time_info"]["start"].total_seconds() * fps)
#                 end_frame = round(item["time_info"]["end"].total_seconds() * fps)
#                 img = bpy.context.scene.sequence_editor.sequences.new_image(
#                     os.path.basename(img_path),
#                     img_path,
#                     channel_no,
#                     start_frame,
#                     fit_method="ORIGINAL",
#                 )
#                 img.frame_final_end = end_frame + 1
#                 img.transform.origin = [0.5, 1.0]
#                 element = img.elements[0]
#                 height_offset = element.orig_height * img.transform.scale_y / 2

#                 if ("json" in item["time_info"]) and (
#                     "offset_x" in item["time_info"]["json"]
#                 ):
#                     img.transform.offset_x = item["time_info"]["json"]["offset_x"]
#                 else:
#                     img.transform.offset_x = offset_x

#                 if ("json" in item["time_info"]) and (
#                     "offset_y" in item["time_info"]["json"]
#                 ):
#                     img.transform.offset_y = (
#                         item["time_info"]["json"]["offset_y"] - height_offset
#                     )
#                 else:
#                     img.transform.offset_y = offset_y - height_offset

#                 img["srt_uuid"] = srt_uuid

#     def execute(self, context):
#         obj = bpy.data.objects[0]

#         srt_info = obj.srt_list[obj.srt_index]

#         srt_path = srt_info.srt_file
#         img_dir = srt_info.image_dir
#         if not srt_path:
#             return {"CANCELLED"}
#         if not img_dir:
#             return {"CANCELLED"}

#         self.load_jimaku(
#             srt_path,
#             img_dir,
#             srt_info.channel_no,
#             srt_info.offset_x,
#             srt_info.offset_y,
#             srt_info.uuid,
#         )
#         return {"FINISHED"}


# class SrtLoaderAddItem(bpy.types.Operator):
#     bl_idname = "srt_loader.add_item"
#     bl_label = "字幕ファイルを追加する"
#     bl_description = "字幕ファイル情報を追加する"

#     def execute(self, context):
#         obj = bpy.data.objects[0]
#         item = obj.srt_list.add()
#         item.uuid = str(uuid.uuid4())
#         print("add:", len(obj.srt_list), obj.srt_index, item.uuid)
#         return {"FINISHED"}


# class SrtLoaderRemoveItem(bpy.types.Operator):
#     bl_idname = "srt_loader.remove_item"
#     bl_label = "字幕ファイルを削除する"
#     bl_description = "字幕ファイル情報を削除する"

#     @classmethod
#     def poll(cls, context):
#         return bpy.data.objects[0].srt_list

#     def execute(self, context):
#         obj = bpy.data.objects[0]
#         index = obj.srt_index
#         obj.srt_list.remove(index)
#         if index > 0:
#             obj.srt_index -= 1
#         print("remove:", len(obj.srt_list), obj.srt_index)
#         return {"FINISHED"}

# class SrtLoaderSelectItem(bpy.types.Operator):
#     bl_idname = "srt_loader.select_item"
#     bl_label = "字幕ファイル情報を選択する"
#     bl_description = "字幕ファイル情報を選択する"

#     item_index: bpy.props.IntProperty(name="item index")

#     def execute(self, context):
#         obj = bpy.data.objects[0]
#         obj.srt_index = self.item_index
#         print("select:", len(obj.srt_list), obj.srt_index)
#         return {"FINISHED"}


class StrLoaderGetTimestampOfPlayhead(bpy.types.Operator):
    bl_idname = "srt_loader.copy_timestamp_of_playhead"
    bl_label = "Copy playhead timestamp"
    bl_description = "Playheadのタイムスタンプを取得する"

    @classmethod
    def poll(cls, context):
        return context.space_data.view_type == "SEQUENCER"

    def execute(self, context):
        frame_rate = utils.get_frame_rate()
        cur_frame = bpy.context.scene.frame_current
        delta = datetime.timedelta(seconds=(cur_frame / frame_rate))
        timestamp = utils.format_srt_timestamp(delta)
        print(
            f"frame_rate: {frame_rate}, cur_frame: {cur_frame}, timestamp: {timestamp}"
        )
        self.report({"INFO"}, timestamp)
        context.window_manager.clipboard = timestamp
        return {"FINISHED"}


class SrtLoaderResetSrtFile(bpy.types.Operator):
    bl_idname = "srt_loader.reset_srt"
    bl_label = "字幕情報の破棄"
    bl_description = "字幕情報を破棄する"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        srtloarder_settings = bpy.data.objects[0].srtloarder_settings
        if not srtloarder_settings.srt_file:
            return False
        else:
            return len(bpy.data.objects[0].srtloarder_jimaku.list) > 0

    def execute(self, context: Context) -> Set[str] | Set[int]:
        jimaku_list = bpy.data.objects[0].srtloarder_jimaku.list
        srtloarder_settings = bpy.data.objects[0].srtloarder_settings
        if len(jimaku_list) > 0:
            jimaku_list.clear()
        srtloarder_settings.srt_file = ""
        return {"FINISHED"}


class SrtLoaderSaveSrtFile(bpy.types.Operator):
    bl_idname = "srt_loader.save_srt"
    bl_label = "字幕ファイルを保存"
    bl_description = "字幕ファイルを保存する"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        srtloarder_settings = bpy.data.objects[0].srtloarder_settings
        jimaku_data = bpy.data.objects[0].srtloarder_jimaku
        if not srtloarder_settings.srt_file:
            return False
        else:
            return jimaku_data.jimaku_data_changed

    def execute(self, context: Context) -> Set[str] | Set[int]:
        srtloarder_jimaku = bpy.data.objects[0].srtloarder_jimaku
        print(utils.jimakulist_to_srtdata(srtloarder_jimaku.list))
        srtloarder_settings = bpy.data.objects[0].srtloarder_settings
        output_path = bpy.path.abspath(srtloarder_settings.srt_file)
        dir_path = os.path.dirname(output_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        if os.path.exists(output_path):
            # backup
            shutil.copyfile(output_path, output_path + ".bk")

        with open(output_path, mode="w") as f:
            srt_data = utils.jimakulist_to_srtdata(srtloarder_jimaku.list)
            for data in srt_data:
                f.write(f"{data}\n")

        self.report(
            type={"INFO"},
            message=f"srt_file saved: {output_path}",
        )
        return {"FINISHED"}


class SrtLoaderReadSrtFile(bpy.types.Operator):
    bl_idname = "srt_loader.read_srt"
    bl_label = "字幕ファイルを読み込む"
    bl_description = "字幕ファイルを読み込む"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        srtloarder_settings = bpy.data.objects[0].srtloarder_settings
        if not srtloarder_settings.srt_file:
            return False
        else:
            return True

    def load_jimaku(self, srt_path, jimaku_data):
        jimaku_data.list.clear()
        items = my_srt.read_srt_file(srt_path)
        fps = utils.get_frame_rate()
        for item in items:
            obj = jimaku_data.list.add()
            obj.no = item["no"]
            obj.text = "\n".join(item["lines"])
            obj.start_frame = utils.timedelta_to_frame(item["time_info"]["start"], fps)
            diff = item["time_info"]["end"] - item["time_info"]["start"]
            obj.frame_duration = utils.timedelta_to_frame(diff, fps)
            if "json" in item["time_info"]:
                utils.update_jimaku(obj, item["time_info"]["json"])

    def execute(self, context: Context) -> Set[str] | Set[int]:
        srt_file = bpy.data.objects[0].srtloarder_settings.srt_file
        if not srt_file:
            self.report(
                type={"WARNING"},
                message="srtファイルが未指定",
            )
            return {"CANCELLED"}
        srt_path = bpy.path.abspath(srt_file)
        if not os.path.isfile(srt_path):
            self.report(
                type={"WARNING"},
                message=f"srtファイル({srt_path})が存在しません",
            )
            return {"CANCELLED"}

        srtloarder_jimaku = bpy.data.objects[0].srtloarder_jimaku
        self.load_jimaku(srt_path, srtloarder_jimaku)
        srtloarder_jimaku.jimaku_data_changed = False
        return {"FINISHED"}


class SrtLoaderEditJimaku(bpy.types.Operator):
    bl_idname = "srt_loader.edit_jimaku"
    bl_label = "編集"
    bl_description = "字幕テキストを編集する"
    bl_options = {"REGISTER", "UNDO"}

    win_count: bpy.props.IntProperty(name="window counts", default=1)
    textdata_name = "edit_jimaku"

    def modal(self, context: Context, event: Event) -> Set[str] | Set[int]:
        if len(context.window_manager.windows) < self.win_count:
            srtloarder_jimaku = bpy.data.objects[0].srtloarder_jimaku
            srtloarder_jimaku.jimaku_editing = False
            return {"FINISHED"}
        return {"RUNNING_MODAL"}

    def invoke(self, context: Context, event: Event) -> Set[str] | Set[int]:
        srtloarder_jimaku = bpy.data.objects[0].srtloarder_jimaku
        context.window_manager.modal_handler_add(self)

        bpy.ops.wm.window_new()
        new_win = context.window_manager.windows[-1]
        area = new_win.screen.areas[-1]
        area.type = "TEXT_EDITOR"

        self.win_count = len(context.window_manager.windows)

        if self.textdata_name in bpy.data.texts.keys():
            area.spaces[0].text = bpy.data.texts[self.textdata_name]
        else:
            area.spaces[0].text = bpy.data.texts.new(name=self.textdata_name)
        cur_idx = srtloarder_jimaku.index
        jimaku = srtloarder_jimaku.list[cur_idx]
        area.spaces[0].text.from_string(jimaku.text)
        with bpy.context.temp_override(area=area):
            print(
                f"bpy.context.space_data.show_region_ui: {bpy.context.space_data.show_region_ui}"
            )
            bpy.ops.text.jump(line=1)
            bpy.context.space_data.show_region_ui = True
        srtloarder_jimaku.jimaku_editing = True
        return {"RUNNING_MODAL"}


class SrtLoaderSaveJimaku(bpy.types.Operator):
    bl_idname = "srt_loader.save_jimaku"
    bl_label = "保存"
    bl_description = "字幕テキストを保存する"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.space_data.type == "TEXT_EDITOR"

    def execute(self, context: Context) -> Set[str] | Set[int]:
        win = context.window
        area = win.screen.areas[-1]
        srtloarder_jimaku = bpy.data.objects[0].srtloarder_jimaku
        cur_idx = srtloarder_jimaku.index
        jimaku = srtloarder_jimaku.list[cur_idx]
        jimaku.text = area.spaces[0].text.as_string()
        srtloarder_jimaku.jimaku_editing = False
        bpy.ops.wm.window_close()
        return {"FINISHED"}


class SrtLoaderCancelJimaku(bpy.types.Operator):
    bl_idname = "srt_loader.cancel_jimaku"
    bl_label = "キャンセル"
    bl_description = "字幕テキストを保存しない"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.space_data.type == "TEXT_EDITOR"

    def execute(self, context: Context) -> Set[str] | Set[int]:
        srtloarder_jimaku = bpy.data.objects[0].srtloarder_jimaku
        srtloarder_jimaku.jimaku_editing = False
        bpy.ops.wm.window_close()
        return {"FINISHED"}


class SrtLoaderAddJimaku(bpy.types.Operator):
    bl_idname = "srt_loader.add_jimaku"
    bl_label = "字幕情報の追加"
    bl_description = "字幕情報を追加する"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        srtloarder_settings = bpy.data.objects[0].srtloarder_settings
        if not srtloarder_settings.srt_file:
            return False
        else:
            return True

    def execute(self, context: Context) -> Set[str] | Set[int]:
        jimaku_list = bpy.data.objects[0].srtloarder_jimaku.list
        item = jimaku_list.add()
        item.no = len(jimaku_list)
        bpy.data.objects[0].srtloarder_jimaku.jimaku_data_changed = True
        return {"FINISHED"}


class SrtLoaderRemoveJimaku(bpy.types.Operator):
    bl_idname = "srt_loader.remove_jimaku"
    bl_label = "字幕情報の削除"
    bl_description = "字幕情報を削除する"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        srtloarder_settings = bpy.data.objects[0].srtloarder_settings
        if not srtloarder_settings.srt_file:
            return False
        else:
            jimaku_list = bpy.data.objects[0].srtloarder_jimaku.list
            return len(jimaku_list) > 0

    def execute(self, context: Context) -> Set[str] | Set[int]:
        jimaku_list = bpy.data.objects[0].srtloarder_jimaku.list
        idx = bpy.data.objects[0].srtloarder_jimaku.index
        jimaku_list.remove(idx)
        bpy.data.objects[0].srtloarder_jimaku.index = min(len(jimaku_list) - 1, idx)
        bpy.data.objects[0].srtloarder_jimaku.jimaku_data_changed = True
        return {"FINISHED"}


class SrtLoaderGenerateAllJimakuImages(bpy.types.Operator):
    bl_idname = "srt_loader.generate_all_jimaku_images"
    bl_label = "字幕画像の一括作成"
    bl_description = "字幕画像を一括で作成する"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        srtloarder_settings = bpy.data.objects[0].srtloarder_settings
        if not srtloarder_settings.srt_file:
            return False
        elif not srtloarder_settings.image_dir:
            return False
        else:
            jimaku_list = bpy.data.objects[0].srtloarder_jimaku.list
            return len(jimaku_list) > 0

    def execute(self, context: Context) -> Set[str] | Set[int]:
        addon_name = __name__.split(".")[0]
        prefs = context.preferences
        addon_prefs = prefs.addons[addon_name].preferences
        gimp_path = addon_prefs.gimp_path
        print(gimp_path)
        # TODO 実装
        return {"FINISHED"}


class SrtLoaderGenerateCurrentJimakuImage(bpy.types.Operator):
    bl_idname = "srt_loader.generate_current_jimaku_image"
    bl_label = "字幕画像の作成"
    bl_description = "現在の字幕の画像を作成する"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        srtloarder_settings = bpy.data.objects[0].srtloarder_settings
        if not srtloarder_settings.srt_file:
            return False
        elif not srtloarder_settings.image_dir:
            return False
        else:
            jimaku_list = bpy.data.objects[0].srtloarder_jimaku.list
            return len(jimaku_list) > 0

    def execute(self, context: Context) -> Set[str] | Set[int]:
        # TODO 実装
        return {"FINISHED"}


class_list = [
    # SrtLoaderImportImages,
    # SrtLoaderRemoveImportedImages,
    # SrtLoaderAddItem,
    # SrtLoaderRemoveItem,
    # SrtLoaderSelectItem,
    StrLoaderGetTimestampOfPlayhead,
    SrtLoaderResetSrtFile,
    SrtLoaderReadSrtFile,
    SrtLoaderSaveSrtFile,
    SrtLoaderEditJimaku,
    SrtLoaderSaveJimaku,
    SrtLoaderCancelJimaku,
    SrtLoaderAddJimaku,
    SrtLoaderRemoveJimaku,
    SrtLoaderGenerateAllJimakuImages,
    SrtLoaderGenerateCurrentJimakuImage,
]
