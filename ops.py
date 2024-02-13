from typing import Set
import bpy
import os
import datetime
import shutil
import subprocess
import json
import logging

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
        logging.debug(
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
        logging.debug(utils.jimakulist_to_srtdata(srtloarder_jimaku.list))
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
        style_json_data = utils.get_default_style_json_data()
        for item in items:
            obj = jimaku_data.list.add()
            obj.no = item["no"]
            obj.text = "\n".join(item["lines"])
            obj.start_frame = utils.timedelta_to_frame(item["time_info"]["start"], fps)
            diff = item["time_info"]["end"] - item["time_info"]["start"]
            obj.frame_duration = utils.timedelta_to_frame(diff, fps)
            if "json" in item["time_info"]:
                utils.update_jimaku(obj, item["time_info"]["json"])
            else:
                utils.update_styles(obj.styles, style_json_data, False)

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
        json_data = utils.get_default_style_json_data()
        utils.update_styles(item.styles, json_data, False)
        bpy.data.objects[0].srtloarder_jimaku.index = len(jimaku_list) - 1
        bpy.ops.srt_loader.update_jimaku_startframe()
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
        target_strip = find_strip(jimaku.no)
        if target_strip is not None:
            target_strip.frame_start = cur_frame
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
            jimaku.start_frame = target_strip.frame_start
            jimaku.frame_duration = target_strip.frame_final_duration
        return {"FINISHED"}


class SrtLoaderUpdateJimakuSettings(bpy.types.Operator):
    bl_idname = "srt_loader.update_jimaku_settings"
    bl_label = "字幕ストリップの位置情報を反映"
    bl_description = "字幕情報のストリップの位置情報を反映する"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        srtloarder_settings = bpy.data.objects[0].srtloarder_settings
        if not srtloarder_settings.srt_file:
            return False
        else:
            target_strip = context.scene.sequence_editor.active_strip
            if target_strip is None:
                return False
            if target_strip.get("generated_by") != "srt_loader":
                return False

            jimaku_list = bpy.data.objects[0].srtloarder_jimaku.list
            return len(jimaku_list) > 0

    def execute(self, context: Context) -> Set[str] | Set[int]:
        jimaku_list = bpy.data.objects[0].srtloarder_jimaku.list
        idx = bpy.data.objects[0].srtloarder_jimaku.index
        jimaku = jimaku_list[idx]

        target_strip = context.scene.sequence_editor.active_strip
        if target_strip:
            jimaku.settings.channel_no = target_strip.channel
            jimaku.settings.offset_x = target_strip.transform.offset_x
            element = target_strip.elements[0]
            height_offset = element.orig_height * target_strip.transform.scale_y / 2
            jimaku.settings.offset_y = target_strip.transform.offset_y + height_offset
        return {"FINISHED"}


class SrtLoaderUpdateDefaultJimakuSettings(bpy.types.Operator):
    bl_idname = "srt_loader.update_default_jimaku_settings"
    bl_label = "字幕ストリップのデフォルト位置情報を反映"
    bl_description = "字幕情報のストリップのデフォルト位置情報を反映する"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        target_strip = context.scene.sequence_editor.active_strip
        if target_strip is None:
            return False
        else:
            return hasattr(target_strip, "transform")

    def execute(self, context: Context) -> Set[str] | Set[int]:
        srtloarder_settings = bpy.data.objects[0].srtloarder_settings
        target_strip = context.scene.sequence_editor.active_strip
        if target_strip:
            srtloarder_settings.settings.channel_no = target_strip.channel
            srtloarder_settings.settings.offset_x = target_strip.transform.offset_x
            if hasattr(target_strip, "elements"):
                element = target_strip.elements[0]
                height_offset = element.orig_height * target_strip.transform.scale_y / 2
                srtloarder_settings.settings.offset_y = (
                    target_strip.transform.offset_y + height_offset
                )
            else:
                render = bpy.data.scenes["Scene"].render
                screen_height = render.resolution_y * (
                    render.resolution_percentage / 100
                )
                height_offset = screen_height * target_strip.transform.scale_y / 2
                srtloarder_settings.settings.offset_y = (
                    target_strip.transform.offset_y + height_offset
                )
        return {"FINISHED"}


def find_jimaku(list, no):
    for jimaku in list:
        if jimaku.no == no:
            return jimaku


def find_strip(no, generated_by="srt_loader"):
    sequences = bpy.context.scene.sequence_editor.sequences
    for seq in sequences:
        if (
            seq.type == "IMAGE"
            and seq.get("generated_by") == generated_by
            and seq.get("jimaku_no") == no
        ):
            return seq


def setup_old_strips_map(oldmap, generated_by="srt_loader"):
    sequences = bpy.context.scene.sequence_editor.sequences_all
    for seq in sequences:
        if seq.type == "IMAGE" and seq.get("generated_by") == generated_by:
            if no := seq.get("jimaku_no"):
                oldmap[no] = seq


def remove_image_strips(target_no=None, generated_by="srt_loader"):
    target_strips = []
    sequences = bpy.context.scene.sequence_editor.sequences_all
    for seq in sequences:
        if seq.type == "IMAGE" and seq.get("generated_by") == generated_by:
            if target_no is None:
                target_strips.append(seq)
            elif seq.get("jimaku_no") == target_no:
                target_strips.append(seq)
                break

    changed_pm_set = set()
    for seq in target_strips:
        pm = seq.parent_meta()
        if pm:
            pm.sequences.remove(seq)
            changed_pm_set.add(pm)
        else:
            bpy.context.scene.sequence_editor.sequences.remove(seq)

    for pm in changed_pm_set:
        adjust_meta_time(pm)


def get_current_meta_strip(context):
    meta_stack = context.scene.sequence_editor.meta_stack
    if meta_stack:
        return meta_stack[-1]
    return None


def adjust_meta_time(meta_strip):
    start_list = []
    end_list = []
    for seq in meta_strip.sequences:
        start_list.append(seq.frame_start)
        end_list.append(seq.frame_final_end)

    meta_start = min(start_list)
    meta_end = max(end_list)
    meta_strip.frame_start = meta_start
    meta_strip.frame_final_end = meta_end


def create_image_strips(target_no=None, generated_by="srt_loader"):
    jimaku_data = bpy.data.objects[0].srtloarder_jimaku
    strloader_data = bpy.data.objects[0].srtloarder_settings

    channel_no = strloader_data.settings.channel_no
    offset_x = strloader_data.settings.offset_x
    offset_y = strloader_data.settings.offset_y

    image_dir = bpy.path.abspath(strloader_data.image_dir)
    jimaku_list = jimaku_data.list
    old_seq_map = {}
    if target_no is not None:
        jimaku = find_jimaku(jimaku_list, target_no)
        jimaku_list = [jimaku]
        remove_image_strips(target_no, generated_by)
    else:
        setup_old_strips_map(old_seq_map, generated_by)

    meta_strip = get_current_meta_strip(bpy.context)
    for jimaku in jimaku_list:
        image_path = os.path.join(image_dir, f"{jimaku['no']}.png")
        if not os.path.isfile(image_path):
            logging.warning(f"image file not exist: {image_path}")
            continue

        if jimaku.settings.useJimakuSettings:
            channel_no = jimaku.settings.channel_no
            offset_x = jimaku.settings.offset_x
            offset_y = jimaku.settings.offset_y

        img: bpy.types.ImageSequence = (
            bpy.context.scene.sequence_editor.sequences.new_image(
                os.path.basename(image_path),
                bpy.path.relpath(image_path),
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

        # 専用の色を設定
        img.color_tag = "COLOR_05"

        old_seq = old_seq_map.get(img.get("jimaku_no"))
        if old_seq:
            pm = old_seq.parent_meta()
            if pm:
                org_channel = old_seq.channel
                pm.sequences.remove(old_seq)
                img.move_to_meta(pm)
                adjust_meta_time(pm)
                img.channel = org_channel
            else:
                bpy.context.scene.sequence_editor.sequences.remove(old_seq)
        elif meta_strip:
            img.move_to_meta(meta_strip)
            adjust_meta_time(meta_strip)
            bpy.context.scene.sequence_editor.display_stack(meta_strip)


class SrtLoaderGenerateImagesBase:
    _timer = None
    _proc = None
    _target_no = None

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
                    logging.error(f"stderr of gimp\n{self._proc.stderr.read()}")
                else:
                    self.report(type={"INFO"}, message="字幕画像 作成成功")
                    logging.info(f"stdout of gimp\n{self._proc.stdout.read()}")
                    create_image_strips(self._target_no)

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
        logging.info(f"script: \n{script}")

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
        jimaku_index = jimaku_data.index
        jimaku = jimaku_data.list[jimaku_index]
        jimaku_list = [jimaku]

        self._target_no = jimaku.no

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


class SrtLoaderRepositionCurrentJimakuImage(bpy.types.Operator):
    bl_idname = "srt_loader.reposition_current_jimaku_image"
    bl_label = "字幕画像の再配置"
    bl_description = "現在の字幕の画像を再配置する"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context) -> Set[str] | Set[int]:
        jimaku_data = bpy.data.objects[0].srtloarder_jimaku
        jimaku = jimaku_data.list[jimaku_data.index]
        create_image_strips(jimaku.no)
        return {"FINISHED"}


class SrtLoaderRepositionAllJimakuImages(bpy.types.Operator):
    bl_idname = "srt_loader.reposition_all_jimaku_images"
    bl_label = "全字幕画像の再配置"
    bl_description = "全ての字幕の画像を再配置する"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context) -> Set[str] | Set[int]:
        create_image_strips()
        return {"FINISHED"}


class SrtLoaderRemoveAllJimakuImages(bpy.types.Operator):
    bl_idname = "srt_loader.remove_all_jimaku_images"
    bl_label = "全字幕画像の削除"
    bl_description = "全ての字幕の画像を削除する"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context) -> Set[str] | Set[int]:
        remove_image_strips()
        return {"FINISHED"}


class SrtLoaderSetupAddonPresets(bpy.types.Operator):
    bl_idname = "srt_loader.setup_addon_presets"
    bl_label = "プリセットを用意する"
    bl_description = "アドオン用のプリセットをインストールする"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context) -> Set[str] | Set[int]:
        utils.setup_addon_presets()
        self.report(type={"INFO"}, message=f"プリセットをコピーしました")
        return {"FINISHED"}


class SrtLoaderSetPresetName(bpy.types.Operator):
    bl_idname = "srt_loader.set_preset_name"
    bl_label = "プリセット名を設定する"
    bl_description = "プリセット名を設定する"
    bl_options = {"REGISTER", "UNDO"}

    preset_file_path: bpy.props.StringProperty()

    def execute(self, context: Context) -> Set[str] | Set[int]:
        logging.debug(f"preset_file_path: {self.preset_file_path}")
        base_name = os.path.basename(self.preset_file_path).rstrip(".py")
        dir_name = os.path.basename(os.path.dirname(self.preset_file_path))

        if dir_name == "default_styles":
            srtloarder_settings = bpy.data.objects[0].srtloarder_settings
            srtloarder_settings.styles.preset_name = base_name
        elif dir_name == "jimaku_styles":
            list = bpy.data.objects[0].srtloarder_jimaku.list
            index = bpy.data.objects[0].srtloarder_jimaku.index
            jimaku = list[index]
            jimaku.styles.preset_name = base_name

        return {"FINISHED"}


class SrtLoaderPresetsBase():

    style_type: bpy.props.EnumProperty(
        name="設定先のスタイル",
        description="スタイルの種類(default,jimaku)",
        items=[
            ("default", "Default", "デフォルトスタイル"),
            ("jimaku", "Jimaku", "字幕のスタイル"),
        ],
        default="default",
    )

    def get_target_styles(self):
        if self.style_type == "default":
            return bpy.data.objects[0].srtloarder_settings.styles
        else:
            list = bpy.data.objects[0].srtloarder_jimaku.list
            index = bpy.data.objects[0].srtloarder_jimaku.index
            return list[index].styles


class SrtLoaderApplyPresets(SrtLoaderPresetsBase, bpy.types.Operator):
    bl_idname = "srt_loader.apply_presets"
    bl_label = "プリセットを設定する"
    bl_description = "プリセットを設定する"
    bl_options = {"REGISTER"}

    def execute(self, context: Context) -> Set[str] | Set[int]:
        target_styles = bpy.data.objects[0].srtloarder_settings.styles
        logging.debug(f"self.style_type: {self.style_type}")
        if self.style_type == "jimaku":
            list = bpy.data.objects[0].srtloarder_jimaku.list
            index = bpy.data.objects[0].srtloarder_jimaku.index
            jimaku = list[index]
            target_styles = jimaku.styles

        json_path = utils.get_style_json_from_presets(target_styles.preset_name)
        if json_path is None:
            self.report(
                type={"Error"}, message=f"該当するプリセット({target_styles.preset_name})はありません"
            )
        logging.debug(f"type: {self.style_type}, json_file: {json_path}")
        with open(json_path) as f:
            json_data = json.load(f)
            target_styles = self.get_target_styles()
            utils.update_styles(target_styles, json_data)

        self.report(type={"INFO"}, message=f"プリセットの内容にスタイルを更新しました")
        return {"FINISHED"}


def popup_menu_draw_empty_input(menu, context):
    menu.layout.label(text="プリセット名を指定してください")


def popup_menu_draw_name_exists(menu, context):
    menu.layout.label(text="指定されたプリセット名は登録済です。別の名前を指定してください。")


def popup_menu_draw_invalid_name(menu, context):
    menu.layout.label(text="不正なプリセット名が指定されました。")


def popup_menu_draw_failure(menu, context):
    menu.layout.label(text="処理に失敗しました。")


DEFAULT_PRESET_NAME = "NEW_STYLE"


class SrtLoaderOverwriteStyleAsPresetWithDialog(SrtLoaderPresetsBase,
                                                bpy.types.Operator):
    bl_idname = "srt_loader.overwrite_style_as_preset_with_dialog"
    bl_label = "現在のスタイルをプリセットに上書き保存する"
    bl_description = "現在のスタイルをプリセットに上書き保存する"
    bl_options = {"REGISTER"}

    preset_name: bpy.props.StringProperty(name=DEFAULT_PRESET_NAME)

    def execute(self, context: Context) -> Set[str] | Set[int]:
        print("preset_name", self.preset_name)
        bpy.ops.srt_loader.save_style_as_preset('INVOKE_DEFAULT',
                                                preset_name=self.preset_name,
                                                style_type=self.style_type)

        return {"FINISHED"}

    def invoke(self, context: Context, event: Event) -> Set[str] | Set[int]:
        styles = self.get_target_styles()
        self.preset_name = styles.preset_name
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context: Context):
        layout = self.layout
        row = layout.row()
        row.label(text=f"プリセット: {self.preset_name} に上書き保存しますか?")


class SrtLoaderSaveStyleAsPresetWithDialog(SrtLoaderPresetsBase, bpy.types.Operator):
    bl_idname = "srt_loader.save_style_as_preset_with_dialog"
    bl_label = "現在のスタイルをプリセットとして保存する"
    bl_description = "現在のスタイルをプリセットとして保存する"
    bl_options = {"REGISTER"}

    preset_name: bpy.props.StringProperty(name=DEFAULT_PRESET_NAME)

    def execute(self, context: Context) -> Set[str] | Set[int]:
        wm = context.window_manager
        print("preset_name", self.preset_name)
        preset_name = self.preset_name.strip()
        if len(preset_name) == 0:
            wm.popup_menu(popup_menu_draw_empty_input, title="プリセット名が未指定", icon="ERROR")
            return {"CANCELLED"}

        file_name = None
        try:
            file_name = utils.get_valid_file_name(preset_name)
        except ValueError:
            wm.popup_menu(popup_menu_draw_invalid_name, title="プリセット名が不正", icon="ERROR")
            return {"CANCELLED"}

        preset_name_set = utils.get_nameset_of_src_preset()
        print(preset_name_set)
        if file_name in preset_name_set:
            wm.popup_menu(popup_menu_draw_name_exists, title="プリセット名が登録済", icon="ERROR")
            return {"CANCELLED"}

        bpy.ops.srt_loader.save_style_as_preset('INVOKE_DEFAULT', preset_name=file_name, style_type=self.style_type)

        return {"FINISHED"}

    def invoke(self, context: Context, event: Event) -> Set[str] | Set[int]:
        self.preset_name = DEFAULT_PRESET_NAME
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context: Context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "preset_name", text="プリセット名")


class SrtLoaderSaveStyleAsPreset(SrtLoaderPresetsBase, bpy.types.Operator):
    bl_idname = "srt_loader.save_style_as_preset"
    bl_label = "現在のスタイルをプリセットとして保存する"
    bl_description = "現在のスタイルをプリセットとして保存する"
    bl_options = {"REGISTER"}

    preset_name: bpy.props.StringProperty(name=DEFAULT_PRESET_NAME)

    def modal(self, context: Context, event: Event) -> Set[str] | Set[int]:
        print("preset_name", self.preset_name)

        styles = self.get_target_styles()
        utils.save_style_as_preset(self.preset_name, styles,
                                   self.style_type == "jimaku")
        styles.preset_name = self.preset_name

        self.report(
            type={"INFO"},
            message=f"preset saved: {self.preset_name}",
        )
        return {"FINISHED"}

    def invoke(self, context: Context, event: Event) -> Set[str] | Set[int]:
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}


class SrtLoaderRenamePresetNameWithDialog(SrtLoaderPresetsBase, bpy.types.Operator):
    bl_idname = "srt_loader.rename_preset_name_with_dialog"
    bl_label = "現在のプリセット名を変更する"
    bl_description = "現在のプリセット名を変更する"
    bl_options = {"REGISTER"}

    preset_name: bpy.props.StringProperty(name=DEFAULT_PRESET_NAME)

    def execute(self, context: Context) -> Set[str] | Set[int]:
        wm = context.window_manager
        print("preset_name", self.preset_name)
        preset_name = self.preset_name.strip()
        if len(preset_name) == 0:
            wm.popup_menu(popup_menu_draw_empty_input, title="プリセット名が未指定", icon="ERROR")
            return {"CANCELLED"}

        file_name = None
        try:
            file_name = utils.get_valid_file_name(preset_name)
        except ValueError:
            wm.popup_menu(popup_menu_draw_invalid_name, title="プリセット名が不正", icon="ERROR")
            return {"CANCELLED"}

        preset_name_set = utils.get_nameset_of_src_preset()
        if file_name in preset_name_set:
            wm.popup_menu(popup_menu_draw_name_exists, title="プリセット名が登録済", icon="ERROR")
            return {"CANCELLED"}

        bpy.ops.srt_loader.rename_preset_name('INVOKE_DEFAULT', preset_name=file_name,
                                              style_type=self.style_type)

        # wm.popup_menu(popup_menu_draw, title="test", icon="ERROR")
        self.report(
            type={"INFO"},
            message=f"preset saved: {file_name}",
        )
        return {"FINISHED"}

    def invoke(self, context: Context, event: Event) -> Set[str] | Set[int]:
        styles = self.get_target_styles()
        self.preset_name = styles.preset_name
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context: Context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "preset_name", text="プリセット名")


class SrtLoaderRenamePresetName(SrtLoaderPresetsBase, bpy.types.Operator):
    bl_idname = "srt_loader.rename_preset_name"
    bl_label = "現在のプリセット名を変更する"
    bl_description = "現在のプリセット名を変更する"
    bl_options = {"REGISTER"}

    preset_name: bpy.props.StringProperty(name=DEFAULT_PRESET_NAME)

    def modal(self, context: Context, event: Event) -> Set[str] | Set[int]:
        print("preset_name", self.preset_name)
        wm = context.window_manager
        styles = self.get_target_styles()
        try:
            utils.rename_preset(styles.preset_name, self.preset_name)
        except FileExistsError as e:
            logging.error(e)
            wm.popup_menu(popup_menu_draw_failure, title="プリセットの名前変更に失敗しました",
                          icon="ERROR")
            return {"CANCELLED"}

        styles.preset_name = self.preset_name

        self.report(
            type={"INFO"},
            message=f"preset renamed: {self.preset_name}",
        )
        return {"FINISHED"}

    def invoke(self, context: Context, event: Event) -> Set[str] | Set[int]:
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}


class SrtLoaderDeletePresetWithDialog(SrtLoaderPresetsBase, bpy.types.Operator):
    bl_idname = "srt_loader.delete_preset_with_dialog"
    bl_label = "現在のスタイルプリセットを削除する"
    bl_description = "現在のスタイルプリセットを削除する"
    bl_options = {"REGISTER"}

    def execute(self, context: Context) -> Set[str] | Set[int]:
        styles = self.get_target_styles()
        preset_name = styles.preset_name

        bpy.ops.srt_loader.delete_preset("INVOKE_DEFAULT", style_type=self.style_type)

        self.report(
            type={"INFO"},
            message=f"preset deleted: {preset_name}",
        )
        return {"FINISHED"}

    def invoke(self, context: Context, event: Event) -> Set[str] | Set[int]:
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context: Context):
        styles = self.get_target_styles()
        preset_name = styles.preset_name

        layout = self.layout
        col = layout.column()
        col.label(text=f"プリセット: {preset_name} を削除しますか?")


class SrtLoaderDeletePreset(SrtLoaderPresetsBase, bpy.types.Operator):
    bl_idname = "srt_loader.delete_preset"
    bl_label = "現在のスタイルプリセットを削除する"
    bl_description = "現在のスタイルプリセットを削除する"
    bl_options = {"REGISTER"}

    def modal(self, context: Context, event: Event) -> Set[str] | Set[int]:
        styles = self.get_target_styles()
        preset_name = styles.preset_name
        if preset_name == "default":
            self.report(
                type={"ERROR"},
                message="defaultプリセットは削除できません",
            )
            return {"CANCELLED"}

        utils.delete_preset(styles.preset_name)
        styles.preset_name = "default"

        # wm.popup_menu(popup_menu_draw, title="test", icon="ERROR")
        self.report(
            type={"INFO"},
            message=f"preset deleted: {preset_name}",
        )
        return {"FINISHED"}

    def invoke(self, context: Context, event: Event) -> Set[str] | Set[int]:
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}


class_list = [
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
    SrtLoaderUpdateJimakuSettings,
    SrtLoaderUpdateDefaultJimakuSettings,
    SrtLoaderGenerateAllJimakuImages,
    SrtLoaderGenerateCurrentJimakuImage,
    SrtLoaderRepositionCurrentJimakuImage,
    SrtLoaderRepositionAllJimakuImages,
    SrtLoaderRemoveAllJimakuImages,
    SrtLoaderSetupAddonPresets,
    SrtLoaderSetPresetName,
    SrtLoaderApplyPresets,
    SrtLoaderSaveStyleAsPreset,
    SrtLoaderSaveStyleAsPresetWithDialog,
    SrtLoaderOverwriteStyleAsPresetWithDialog,
    SrtLoaderRenamePresetName,
    SrtLoaderRenamePresetNameWithDialog,
    SrtLoaderDeletePreset,
    SrtLoaderDeletePresetWithDialog,
]
