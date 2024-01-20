from typing import Set
import bpy
import os
import datetime
import shutil
import subprocess

from bpy.types import Context, Event
from . import my_srt
from . import utils
from . import my_settings


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
        bpy.data.objects[0].srtloarder_jimaku.jimaku_data_changed = False
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


class SrtLoaderUpdateJimakuStartFrame(bpy.types.Operator):
    bl_idname = "srt_loader.update_jimaku_startframe"
    bl_label = "字幕情報の開始フレームの更新"
    bl_description = "字幕情報の開始フレームをプレイヘッドの位置に更新する"
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
        jimaku = jimaku_list[idx]
        cur_frame = bpy.context.scene.frame_current
        jimaku.start_frame = cur_frame
        return {"FINISHED"}


class SrtLoaderUpdateJimakuFrameDuration(bpy.types.Operator):
    bl_idname = "srt_loader.update_jimaku_frameduration"
    bl_label = "字幕ストリップの長さを反映"
    bl_description = "字幕情報のストリップの長さを反映する"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        srtloarder_settings = bpy.data.objects[0].srtloarder_settings
        if not srtloarder_settings.srt_file:
            return False
        else:
            jimaku_list = bpy.data.objects[0].srtloarder_jimaku.list
            index = bpy.data.objects[0].srtloarder_jimaku.index
            jimaku = jimaku_list[index]
            target_strip = find_strip(jimaku.no)
            return len(jimaku_list) > 0 and target_strip is not None

    def execute(self, context: Context) -> Set[str] | Set[int]:
        jimaku_list = bpy.data.objects[0].srtloarder_jimaku.list
        idx = bpy.data.objects[0].srtloarder_jimaku.index
        jimaku = jimaku_list[idx]

        target_strip = find_strip(jimaku.no)
        if target_strip:
            jimaku.frame_duration = target_strip.frame_final_duration
        return {"FINISHED"}


def find_strip(no, generated_by="srt_loarder"):
    sequences = bpy.context.scene.sequence_editor.sequences
    for seq in sequences:
        if (
            seq.type == "IMAGE"
            and seq.get("generated_by") == generated_by
            and seq.get("jimaku_no") == no
        ):
            return seq


def remove_all_image_strips(generated_by="srt_loarder"):
    target_strips = []
    sequences = bpy.context.scene.sequence_editor.sequences
    for seq in sequences:
        if seq.type == "IMAGE" and seq.get("generated_by") == generated_by:
            target_strips.append(seq)

    for seq in target_strips:
        sequences.remove(seq)


def create_image_strips(generated_by="srt_loarder"):
    jimaku_data = bpy.data.objects[0].srtloarder_jimaku
    strloader_data = bpy.data.objects[0].srtloarder_settings

    channel_no = strloader_data.settings.channel_no
    offset_x = strloader_data.settings.offset_x
    offset_y = strloader_data.settings.offset_y

    jimaku_list = jimaku_data.list
    image_dir = bpy.path.abspath(strloader_data.image_dir)

    remove_all_image_strips(generated_by)

    for jimaku in jimaku_list:
        image_path = os.path.join(image_dir, f"{jimaku['no']}.png")
        if not os.path.isfile(image_path):
            next

        if jimaku.settings.useJimakuSettings:
            channel_no = jimaku.settings.channel_no
            offset_x = jimaku.settings.offset_x
            offset_y = jimaku.settings.offset_y

        img: bpy.types.ImageSequence = (
            bpy.context.scene.sequence_editor.sequences.new_image(
                os.path.basename(image_path),
                image_path,
                channel_no,
                round(jimaku.start_frame),
            )
        )
        img.frame_final_duration = round(jimaku.frame_duration)
        # 移動の基準点を画像の上辺の中心に変更
        img.transform.origin = [0.5, 1.0]
        element = img.elements[0]
        height_offset = element.orig_height * img.transform.scale_y / 2
        # オフセット分ストリップを移動
        img.transform.offset_x = offset_x
        img.transform.offset_y = offset_y - height_offset

        # カスタムプロパティーを設定
        img["generated_by"] = generated_by
        img["jimaku_no"] = jimaku.no


class SrtLoaderGenerateImagesBase:
    _timer = None
    _proc = None

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

    def modal(self, context: Context, event: Event) -> Set[str] | Set[int]:
        if event.type == "TIMER":
            if ret := self._proc.poll() is None:
                return {"RUNNING_MODAL"}
            else:
                if ret != 0:
                    self.report(type={"ERROR"}, message="字幕画像 作成失敗")
                    print("stderr:", self._proc.stderr.read())
                else:
                    self.report(type={"INFO"}, message="字幕画像 作成成功")
                    print("stdout:", self._proc.stdout.read())
                    create_image_strips()

                context.window_manager.event_timer_remove(self._timer)
                self.dispose()
                return {"FINISHED"}
        else:
            return {"RUNNING_MODAL"}

    def dispose(self):
        self._proc.stdout.close()
        self._proc.stderr.close()
        self._timer = None
        self._proc = None

    def create_script_for_stdin(self, jimaku_data, srtloarder_settings):
        jimaku_list = jimaku_data.list
        srt_json = utils.jimakulist_to_json(jimaku_list)

        default_json = utils.settings_and_styles_to_json(
            srtloarder_settings, for_jimaku=False
        )
        default_settings_path = os.path.join(
            os.path.dirname(__file__), "default_settings.json"
        )
        default_settings = my_settings.read_config_file(default_settings_path)
        output_dir = bpy.path.abspath(srtloarder_settings.image_dir)
        return utils.create_gimp_script(
            srt_json, default_json, output_dir, default_settings
        )

    def invoke(self, context: Context, event: Event) -> Set[str] | Set[int]:
        addon_name = __name__.split(".")[0]
        prefs = context.preferences
        addon_prefs = prefs.addons[addon_name].preferences
        gimp_path = addon_prefs.gimp_path
        jimaku_data = bpy.data.objects[0].srtloarder_jimaku
        srtloarder_settings = bpy.data.objects[0].srtloarder_settings

        script = self.create_script_for_stdin(jimaku_data, srtloarder_settings)

        cmdline = utils.create_gimp_command_line(gimp_path)

        self._proc = subprocess.Popen(
            cmdline,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.send_to_stdin(script)
        print(script)

        self.report(type={"INFO"}, message="字幕画像 作成開始...")
        self._timer = context.window_manager.event_timer_add(1.0, window=context.window)
        context.window_manager.modal_handler_add(self)

        return {"RUNNING_MODAL"}

    def send_to_stdin(self, script):
        self._proc.stdin.write(script)
        self._proc.stdin.close()


class SrtLoaderGenerateAllJimakuImages(SrtLoaderGenerateImagesBase, bpy.types.Operator):
    bl_idname = "srt_loader.generate_all_jimaku_images"
    bl_label = "字幕画像の一括作成"
    bl_description = "字幕画像を一括で作成する"
    bl_options = {"REGISTER", "UNDO"}


class SrtLoaderGenerateCurrentJimakuImage(
    SrtLoaderGenerateImagesBase, bpy.types.Operator
):
    bl_idname = "srt_loader.generate_current_jimaku_image"
    bl_label = "字幕画像の作成"
    bl_description = "現在の字幕の画像を作成する"
    bl_options = {"REGISTER", "UNDO"}

    def create_script_for_stdin(self, jimaku_data, srtloarder_settings):
        print("current_jimaku!!")
        jimaku_index = jimaku_data.index
        jimaku_list = [jimaku_data.list[jimaku_index]]
        srt_json = utils.jimakulist_to_json(jimaku_list)

        default_json = utils.settings_and_styles_to_json(
            srtloarder_settings, for_jimaku=False
        )
        default_settings_path = os.path.join(
            os.path.dirname(__file__), "default_settings.json"
        )
        default_settings = my_settings.read_config_file(default_settings_path)
        output_dir = bpy.path.abspath(srtloarder_settings.image_dir)
        return utils.create_gimp_script(
            srt_json, default_json, output_dir, default_settings
        )


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
    SrtLoaderUpdateJimakuStartFrame,
    SrtLoaderUpdateJimakuFrameDuration,
    SrtLoaderGenerateAllJimakuImages,
    SrtLoaderGenerateCurrentJimakuImage,
]
