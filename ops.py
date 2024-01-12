from typing import Set
import bpy
import os
import uuid
import datetime

from bpy.types import Context
from . import my_srt


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

    def format_srt_timestamp(self, delta):
        m, s = divmod(delta.seconds, 60)
        h, m = divmod(m, 60)
        return "{:02}:{:02}:{:02},{:03}".format(
            h, m, s, round(delta.microseconds / 1000)
        )

    def execute(self, context):
        frame_rate = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
        cur_frame = bpy.context.scene.frame_current
        delta = datetime.timedelta(seconds=(cur_frame / frame_rate))
        timestamp = self.format_srt_timestamp(delta)
        print(
            f"frame_rate: {frame_rate}, cur_frame: {cur_frame}, timestamp: {timestamp}"
        )
        self.report({"INFO"}, timestamp)
        context.window_manager.clipboard = timestamp
        return {"FINISHED"}


class_list = [
    # SrtLoaderImportImages,
    # SrtLoaderRemoveImportedImages,
    # SrtLoaderAddItem,
    # SrtLoaderRemoveItem,
    # SrtLoaderSelectItem,
    StrLoaderGetTimestampOfPlayhead,
]
