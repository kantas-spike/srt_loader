import datetime
import bpy
import json
import os
import glob
import shutil
import logging


def get_frame_rate():
    return bpy.context.scene.render.fps / bpy.context.scene.render.fps_base


def timedelta_to_frame(delta: datetime.timedelta, frame_rate):
    seconds = max(0, delta.total_seconds())
    return seconds * frame_rate


def rgb_and_opacity_to_rgba(hex_rgb, opacity=1.0):
    return hex_rgb + "{:02x}".format(round(opacity * 255))


def hex_to_floatvector(hex_color: str):
    hex_color = hex_color.lstrip("#")
    if len(hex_color) in [3, 4]:
        hex_color = "".join([ch * 2 for ch in hex_color])

    elm_size = len(hex_color) // 2

    return tuple(
        [int(hex_color[(i * 2) : (i * 2) + 2], 16) / 255.0 for i in range(elm_size)]
    )


def format_srt_timestamp(delta):
    m, s = divmod(delta.seconds, 60)
    h, m = divmod(m, 60)
    return "{:02}:{:02}:{:02},{:03}".format(h, m, s, round(delta.microseconds / 1000))


def styles_to_json(styles, for_jimaku=True):
    result = {}
    if for_jimaku and not styles.useJimakuStyle:
        return result
    result["crop_area"] = {}
    result["crop_area"]["padding_x"] = styles.image.padding_x
    result["crop_area"]["padding_y"] = styles.image.padding_y
    result["styles"] = {}
    result["styles"]["text"] = {}
    result["styles"]["text"]["font_family"] = styles.text.font_family
    result["styles"]["text"]["size"] = styles.text.size
    result["styles"]["text"]["color"] = float_vector_to_hexcolor(styles.text.color)
    result["styles"]["text"]["line_space_rate"] = styles.text.line_space_rate
    result["styles"]["text"]["align"] = styles.text.align
    result["number_of_borders"] = styles.borders.number_of_borders
    result["styles"]["borders"] = []
    if styles.borders.number_of_borders >= 1:
        obj = border_to_json(styles.borders.style1)
        result["styles"]["borders"].append(obj)
    if styles.borders.number_of_borders >= 2:
        obj = border_to_json(styles.borders.style2)
        result["styles"]["borders"].append(obj)

    result["with_shadow"] = styles.shadow.enabled
    if styles.shadow.enabled:
        result["styles"]["shadow"] = {}
        rgb_vector = styles.shadow.color[0:-1]
        result["styles"]["shadow"]["color"] = float_vector_to_hexcolor(rgb_vector)
        result["styles"]["shadow"]["opacity"] = styles.shadow.color[-1]
        result["styles"]["shadow"]["offset_x"] = styles.shadow.offset_x
        result["styles"]["shadow"]["offset_y"] = styles.shadow.offset_y
        result["styles"]["shadow"]["blur_radius"] = styles.shadow.blur_radius
    result["with_box"] = styles.box.enabled
    if styles.box.enabled:
        result["styles"]["box"] = {}
        rgb_vector = styles.box.color[0:-1]
        result["styles"]["box"]["color"] = float_vector_to_hexcolor(rgb_vector)
        result["styles"]["box"]["opacity"] = styles.box.color[-1]
        result["styles"]["box"]["padding_x"] = styles.box.padding_x
        result["styles"]["box"]["padding_y"] = styles.box.padding_y
    return result


def border_to_json(border):
    obj = {}
    obj["color"] = float_vector_to_hexcolor(border.color)
    obj["rate"] = border.rate
    obj["feather"] = border.feather
    return obj


def settings_to_json(settings, for_jimaku=True):
    result = {}
    if for_jimaku and not settings.useJimakuSettings:
        return result
    result["settings"] = {}
    result["settings"]["channel_no"] = settings.channel_no
    result["settings"]["offset_x"] = settings.offset_x
    result["settings"]["offset_y"] = settings.offset_y
    return result


def update_jimaku(jimaku, json):
    if "settings" in json:
        jimaku.settings.useJimakuSettings = True
        jimaku.settings.channel_no = json["settings"]["channel_no"]
        jimaku.settings.offset_x = json["settings"]["offset_x"]
        jimaku.settings.offset_y = json["settings"]["offset_y"]
    else:
        jimaku.settings.useJimakuSettings = False

    update_styles(jimaku.styles, json)


def get_default_style_json_data():
    json_path = get_style_json_from_presets("default")
    with open(json_path) as f:
        return json.load(f)


def update_styles(styles, json, use_jimaku=True):
    target_type = "default"
    if hasattr(styles, "useJimakuStyle"):
        target_type = "jimaku"

    if target_type == "jimaku":
        styles.useJimakuStyle = use_jimaku

    if "styles" in json:
        styles.text.font_family = json["styles"]["text"]["font_family"]
        styles.text.size = json["styles"]["text"]["size"]
        styles.text.color = hex_to_floatvector(json["styles"]["text"]["color"])
        styles.text.align = json["styles"]["text"]["align"]
        styles.text.line_space_rate = json["styles"]["text"]["line_space_rate"]
        styles.borders.number_of_borders = json["number_of_borders"]
        if len(json["styles"]["borders"]) >= 1:
            update_border(styles.borders.style1, json["styles"]["borders"][0])
        if len(json["styles"]["borders"]) >= 2:
            update_border(styles.borders.style2, json["styles"]["borders"][1])
        styles.shadow.enabled = json["with_shadow"]
        if json["with_shadow"]:
            rgba = rgb_and_opacity_to_rgba(
                json["styles"]["shadow"]["color"], json["styles"]["shadow"]["opacity"]
            )
            styles.shadow.color = hex_to_floatvector(rgba)
            styles.shadow.offset_x = json["styles"]["shadow"]["offset_x"]
            styles.shadow.offset_y = json["styles"]["shadow"]["offset_y"]
            styles.shadow.blur_radius = json["styles"]["shadow"]["blur_radius"]
        styles.box.enabled = json["with_box"]
        if json["with_box"]:
            rgba = rgb_and_opacity_to_rgba(
                json["styles"]["box"]["color"], json["styles"]["box"]["opacity"]
            )
            styles.box.color = hex_to_floatvector(rgba)
    elif "crop_area" in json:
        styles.image.padding_x = json["crop_area"]["padding_x"]
        styles.image.padding_y = json["crop_area"]["padding_y"]


def update_border(border, json):
    border.color = hex_to_floatvector(json["color"])
    border.rate = json["rate"]
    border.feather = json["feather"]


def settings_and_styles_to_json(item, for_jimaku=True):
    result = {}
    result.update(settings_to_json(item.settings, for_jimaku))
    result.update(styles_to_json(item.styles, for_jimaku))
    return result


def jimakulist_to_json(list):
    results = []
    for item in list:
        obj = {}
        obj["no"] = item.no
        obj["time_info"] = {}
        obj["time_info"]["start"] = bpy.utils.time_from_frame(item.start_frame)
        obj["time_info"]["end"] = bpy.utils.time_from_frame(
            item.start_frame + item.frame_duration
        )
        json = settings_and_styles_to_json(item)
        if len(json) > 0:
            obj["time_info"]["json"] = json
        obj["lines"] = item.text.split("\n")
        results.append(obj)

    return results


def jimakulist_to_srtdata(list):
    results = []
    for item in list:
        results.append(f"{item.no}")
        start_time = format_srt_timestamp(bpy.utils.time_from_frame(item.start_frame))
        end_time = format_srt_timestamp(
            bpy.utils.time_from_frame(item.start_frame + item.frame_duration)
        )
        json_data = settings_and_styles_to_json(item)
        if len(json_data) == 0:
            results.append(f"{start_time} --> {end_time}")
        else:
            results.append(f"{start_time} --> {end_time} JSON:{json.dumps(json_data)}")
        results.append(item.text)
        results.append("")

    return results


def float_vector_to_hexcolor(vector):
    return "#" + "".join(["{:02X}".format(round(f * 255)) for f in vector])


def get_addon_directory():
    return os.path.dirname(os.path.abspath(__file__))


def create_gimp_command_line(gimp_path, debug=False):
    option = "-dsc" if debug else "-ids"
    cmd = f"{gimp_path} {option} --batch-interpreter python-fu-eval --batch '-'"
    return cmd


def create_gimp_script(
    subtitles,
    config,
    output_path,
    default_config,
    additional_sys_path=get_addon_directory(),
    debug=False,
):
    script = f"""# -*- coding: utf-8 -*-
import json
import datetime
import sys
sys.path=[{repr(additional_sys_path)}]+sys.path
import subtitle_creator

subtitles = {repr(subtitles)}
config = {repr(config)}
default_config = {repr(default_config)}
output_path = {repr(output_path)}
debug = {debug}

subtitle_creator.run(subtitles, config, output_path, default_config, debug)
"""
    return script


def get_src_preset_dirpath(subdir=None):
    preset_dirname = "presets"
    if subdir:
        preset_dirname = os.path.join(preset_dirname, subdir)

    return os.path.join(os.path.dirname(__file__), preset_dirname)


def get_style_json_from_presets(preset_name):
    user_script_path = bpy.utils.script_path_user()
    if user_script_path is None:
        logging.error("bpy.utils.script_path_user() is None!!")
        return
    style_json_dir = os.path.join(user_script_path, "presets/srt_loader/styles_json")
    style_json_path = os.path.join(style_json_dir, f"{preset_name}.json")
    if not os.path.isfile(style_json_path):
        logging.error(
            f"style json file of {preset_name} not exists!!: {style_json_path}"
        )
        return
    return style_json_path


def setup_styles_json():
    user_script_path = bpy.utils.script_path_user()
    if user_script_path is None:
        logging.error("bpy.utils.script_path_user() is None!!")
        return
    style_json_dir = os.path.join(user_script_path, "presets/srt_loader/styles_json")
    if not os.path.isdir(style_json_dir):
        os.makedirs(style_json_dir)
        logging.info(f"make style json dir: {style_json_dir} ...")

    src_files = os.path.join(get_src_preset_dirpath("styles_json"), "*.json")
    for f in glob.glob(src_files):
        shutil.copy(f, style_json_dir)


def setup_styles_preset_from_base_styles_presets(target_subdir):
    user_script_path = bpy.utils.script_path_user()
    if user_script_path is None:
        logging.error("bpy.utils.script_path_user() is None!!")
        return
    style_preset_dir = os.path.join(
        user_script_path, f"presets/srt_loader/{target_subdir}"
    )
    if not os.path.isdir(style_preset_dir):
        os.makedirs(style_preset_dir)
        logging.info(f"make style json dir: {style_preset_dir} ...")

    src_files = os.path.join(get_src_preset_dirpath("base_styles_presets"), "*.py")
    for f in glob.glob(src_files):
        shutil.copy(f, style_preset_dir)


def setup_addon_presets():
    setup_styles_json()
    setup_styles_preset_from_base_styles_presets("default_styles")
    setup_styles_preset_from_base_styles_presets("jimaku_styles")
