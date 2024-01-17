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
    styles = styles.styles
    result["crop_area"] = {}
    result["crop_area"]["padding_x"] = styles.image.padding_x
    result["crop_area"]["padding_y"] = styles.image.padding_y
    result["style"] = {}
    result["style"]["text"] = {}
    result["style"]["text"]["font_family"] = styles.text.font_family
    result["style"]["text"]["size"] = styles.text.size
    result["style"]["text"]["color"] = float_vector_to_hexcolor(styles.text.color)
    result["style"]["text"]["line_space_rate"] = styles.text.line_space_rate
    result["style"]["text"]["align"] = styles.text.align
    result["number_of_borders"] = styles.borders.number_of_borders
    result["style"]["borders"] = []
    if styles.borders.number_of_borders >= 1:
        obj = border_to_json(styles.borders.style1)
        result["style"]["borders"].append(obj)
    if styles.borders.number_of_borders >= 2:
        obj = border_to_json(styles.borders.style2)
        result["style"]["borders"].append(obj)

    result["with_shadow"] = styles.shadow.enabled
    result["style"]["shadow"] = {}
    if styles.shadow.enabled:
        result["style"]["shadow"]["color"] = float_vector_to_hexcolor(
            styles.shadow.color
        )
        result["style"]["shadow"]["offset_x"] = styles.shadow.offset_x
        result["style"]["shadow"]["offset_y"] = styles.shadow.offset_y
        result["style"]["shadow"]["blur_radius"] = styles.shadow.blur_radius
        result["style"]["shadow"]["opacity"] = styles.shadow.opacity

    result["with_box"] = styles.box.enabled
    result["style"]["box"] = {}
    if styles.box.enabled:
        result["style"]["box"]["padding_x"] = styles.box.padding_x
        result["style"]["box"]["padding_y"] = styles.box.padding_y
        result["style"]["box"]["color"] = float_vector_to_hexcolor(styles.box.color)
        result["style"]["box"]["opacity"] = styles.box.opacity
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
    settings = settings.settings
    result["settings"] = {}
    result["settings"]["channel_no"] = settings.channel_no
    result["settings"]["offset_x"] = settings.offset_x
    result["settings"]["offset_y"] = settings.offset_y
    return result


def update_jimaku(jimaku, json):
    if len(json["settings"].keys()) > 0:
        jimaku.settings.useJimakuSettings = True
        jimaku.settings.settings.channel_no = json["settings"]["channel_no"]
        jimaku.settings.settings.offset_x = json["settings"]["offset_x"]
        jimaku.settings.settings.offset_y = json["settings"]["offset_y"]
    else:
        jimaku.settings.useJimakuSettings = False

    if len(json["styles"].keys()) > 0:
        jimaku.styles.useJimakuStyle = True
        jimaku.styles.styles.text.font_family = json["style"]["text"]["font_family"]
        jimaku.styles.styles.text.size = json["style"]["text"]["size"]
        jimaku.styles.styles.text.color = hex_to_floatvector(
            json["style"]["text"]["color"]
        )
        jimaku.styles.styles.text.align = json["style"]["text"]["align"]
        jimaku.styles.styles.text.line_space_rate = json["style"]["text"][
            "line_space_rate"
        ]
        jimaku.styles.styles.borders.number_of_borders = json["number_of_borders"]
        if len(json["style"]["borders"]) >= 1:
            update_border(
                jimaku.styles.styles.borders.style1, json["style"]["borders"][0]
            )
        if len(json["style"]["borders"]) >= 2:
            update_border(
                jimaku.styles.styles.borders.style2, json["style"]["borders"][1]
            )
        jimaku.styles.styles.shadow.enabled = json["with_shadow"]
        if json["with_shadow"]:
            jimaku.styles.styles.shadow.color = hex_to_floatvector(
                json["style"]["shadow"]["color"]
            )
            jimaku.styles.styles.shadow.offset_x = json["style"]["shadow"]["offset_x"]
            jimaku.styles.styles.shadow.offset_y = json["style"]["shadow"]["offset_y"]
            jimaku.styles.styles.shadow.blur_radius = json["style"]["shadow"][
                "blur_radius"
            ]
            jimaku.styles.styles.shadow.opacity = json["style"]["shadow"]["opacity"]
        jimaku.styles.styles.box.enabled = json["with_box"]
        if json["with_box"]:
            jimaku.styles.styles.box.color = hex_to_floatvector(
                json["style"]["box"]["color"]
            )
            jimaku.styles.styles.box.opacity = json["style"]["box"]["opacity"]
    elif "crop_area" in json:
        jimaku.styles.useJimakuStyle = True
        jimaku.styles.styles.image.padding_x = json["crop_area"]["padding_x"]
        jimaku.styles.styles.image.padding_y = json["crop_area"]["padding_y"]
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
