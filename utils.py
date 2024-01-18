import datetime
import bpy
import json


def get_frame_rate():
    return bpy.context.scene.render.fps / bpy.context.scene.render.fps_base


def timedelta_to_frame(delta: datetime.timedelta, frame_rate):
    seconds = max(0, delta.total_seconds())
    return seconds * frame_rate


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


def styles_to_json(styles):
    result = {}
    if not styles.useJimakuStyle:
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
    result["styles"]["shadow"] = {}
    if styles.shadow.enabled:
        result["styles"]["shadow"]["color"] = float_vector_to_hexcolor(
            styles.shadow.color
        )
        result["styles"]["shadow"]["offset_x"] = styles.shadow.offset_x
        result["styles"]["shadow"]["offset_y"] = styles.shadow.offset_y
        result["styles"]["shadow"]["blur_radius"] = styles.shadow.blur_radius
        result["styles"]["shadow"]["opacity"] = styles.shadow.opacity

    result["with_box"] = styles.box.enabled
    result["styles"]["box"] = {}
    if styles.box.enabled:
        result["styles"]["box"]["padding_x"] = styles.box.padding_x
        result["styles"]["box"]["padding_y"] = styles.box.padding_y
        result["styles"]["box"]["color"] = float_vector_to_hexcolor(styles.box.color)
        result["styles"]["box"]["opacity"] = styles.box.opacity
    return result


def border_to_json(border):
    obj = {}
    obj["color"] = float_vector_to_hexcolor(border.color)
    obj["rate"] = border.rate
    obj["feather"] = border.feather
    return obj


def settings_to_json(settings):
    result = {}
    if not settings.useJimakuSettings:
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

    if "styles" in json:
        jimaku.styles.useJimakuStyle = True
        jimaku.styles.text.font_family = json["styles"]["text"]["font_family"]
        jimaku.styles.text.size = json["styles"]["text"]["size"]
        jimaku.styles.text.color = hex_to_floatvector(json["styles"]["text"]["color"])
        jimaku.styles.text.align = json["styles"]["text"]["align"]
        jimaku.styles.text.line_space_rate = json["styles"]["text"]["line_space_rate"]
        jimaku.styles.borders.number_of_borders = json["number_of_borders"]
        if len(json["styles"]["borders"]) >= 1:
            update_border(jimaku.styles.borders.style1, json["styles"]["borders"][0])
        if len(json["styles"]["borders"]) >= 2:
            update_border(jimaku.styles.borders.style2, json["styles"]["borders"][1])
        jimaku.styles.shadow.enabled = json["with_shadow"]
        if json["with_shadow"]:
            jimaku.styles.shadow.color = hex_to_floatvector(
                json["styles"]["shadow"]["color"]
            )
            jimaku.styles.shadow.offset_x = json["styles"]["shadow"]["offset_x"]
            jimaku.styles.shadow.offset_y = json["styles"]["shadow"]["offset_y"]
            jimaku.styles.shadow.blur_radius = json["styles"]["shadow"]["blur_radius"]
            jimaku.styles.shadow.opacity = json["styles"]["shadow"]["opacity"]
        jimaku.styles.box.enabled = json["with_box"]
        if json["with_box"]:
            jimaku.styles.box.color = hex_to_floatvector(json["styles"]["box"]["color"])
            jimaku.styles.box.opacity = json["styles"]["box"]["opacity"]
    elif "crop_area" in json:
        jimaku.styles.useJimakuStyle = True
        jimaku.styles.image.padding_x = json["crop_area"]["padding_x"]
        jimaku.styles.image.padding_y = json["crop_area"]["padding_y"]
    else:
        jimaku.styles.useJimakuStyle = False


def update_border(border, json):
    border.color = hex_to_floatvector(json["color"])
    border.rate = json["rate"]
    border.feather = json["feather"]


def settings_and_styles_to_json(item):
    result = {}
    result.update(settings_to_json(item.settings))
    result.update(styles_to_json(item.styles))
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
        obj["time_info"]["json"] = settings_and_styles_to_json(item)
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
    return "#" + "".join([format(round(f * 255), "X") for f in vector])
