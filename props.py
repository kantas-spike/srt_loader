import bpy


def hex_to_floatvector(hex_color: str):
    hex_color = hex_color.lstrip("#")
    if len(hex_color) in [3, 4]:
        hex_color = "".join([ch * 2 for ch in hex_color])

    elm_size = len(hex_color) // 2

    return tuple(
        [int(hex_color[(i * 2) : (i * 2) + 2], 16) / 255.0 for i in range(elm_size)]
    )


class SrtLoaderSettingsProperties(bpy.types.PropertyGroup):
    channel_no: bpy.props.IntProperty(default=1, min=1, max=128)
    offset_x: bpy.props.FloatProperty(default=0)
    offset_y: bpy.props.FloatProperty(default=-400)


class SrtLoaderImageStyleProperties(bpy.types.PropertyGroup):
    padding_x: bpy.props.IntProperty(default=20)
    padding_y: bpy.props.IntProperty(default=20)


class SrtLoaderTextStyleProperties(bpy.types.PropertyGroup):
    font_family: bpy.props.StringProperty(default="Noto Sans JP Bold")
    size: bpy.props.IntProperty(default=48)
    color: bpy.props.FloatVectorProperty(
        subtype="COLOR", description="文字の前景色", default=hex_to_floatvector("#40516a")
    )
    align: bpy.props.EnumProperty(
        name="Text Align",
        description="文字揃え(left,right,center,fill)",
        items=[
            ("left", "Left", "左揃え"),
            ("center", "Center", "中央揃え"),
            ("right", "Right", "右揃え"),
        ],
        default="center",
    )
    line_space_rate: bpy.props.FloatProperty(
        name="行間", description="行間 (単位:文字サイズの比率)", default=-0.3
    )


class SrtLoaderBorderStyleProperties1(bpy.types.PropertyGroup):
    color: bpy.props.FloatVectorProperty(
        subtype="COLOR",
        min=0,
        max=1.0,
        name="色",
        description="縁取りの色",
        default=hex_to_floatvector("#FFFFFF"),
    )
    rate: bpy.props.FloatProperty(
        name="サイズ", description="縁取りのサイズ(単位:文字サイズの比率)", default=0.08, min=0, max=1
    )
    feather: bpy.props.FloatProperty(
        name="ぼかし幅", description="縁取りのぼかし幅(単位: px)。0の場合、縁取りをぼかさない", default=0
    )


class SrtLoaderBorderStyleProperties2(bpy.types.PropertyGroup):
    color: bpy.props.FloatVectorProperty(
        subtype="COLOR",
        name="色",
        description="縁取りの色",
        default=hex_to_floatvector("#40516a"),
    )
    rate: bpy.props.FloatProperty(
        name="サイズ", description="縁取りのサイズ(単位:文字サイズの比率)", default=0.08, min=0, max=1
    )
    feather: bpy.props.FloatProperty(
        name="ぼかし幅", description="縁取りのぼかし幅(単位: px)。0の場合、縁取りをぼかさない", default=0
    )


class SrtLoaderBorderListStyleProperties(bpy.types.PropertyGroup):
    number_of_borders: bpy.props.IntProperty(default=2, min=0, max=2)
    style1: bpy.props.PointerProperty(type=SrtLoaderBorderStyleProperties1)
    style2: bpy.props.PointerProperty(type=SrtLoaderBorderStyleProperties2)
    index: bpy.props.IntProperty(default=0)


class SrtLoaderShadowStyleProperties(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(name="利用する", default=False, description="影を利用する")
    color: bpy.props.FloatVectorProperty(
        subtype="COLOR",
        size=4,
        min=0,
        max=1.0,
        default=hex_to_floatvector("#000000FF"),
        description="影の色",
    )
    offset_x: bpy.props.IntProperty(
        name="水平オフセット", description="影の水平オフセット (単位: px)", default=10
    )
    offset_y: bpy.props.IntProperty(
        name="垂直オフセット", description="影の垂直オフセット (単位: px)", default=10
    )
    blur_radius: bpy.props.IntProperty(
        name="ぼかし半径", description="影のぼかし半径 (単位: px)", default=15
    )


class SrtLoaderBoxStyleProperties(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(name="利用する", default=False, description="ボックスを利用する")
    color: bpy.props.FloatVectorProperty(
        subtype="COLOR",
        size=4,
        min=0,
        max=1.0,
        default=hex_to_floatvector("#ccccccff"),
        description="字幕の背景色",
    )
    padding_x: bpy.props.IntProperty(
        name="Padding X", description="字幕画像の水平パディングサイズ(単位: px)", default=20
    )
    padding_y: bpy.props.IntProperty(
        name="Padding Y", description="字幕画像の垂直パディングサイズ(単位: px)", default=20
    )


class SrtLoaderStylesProperties(bpy.types.PropertyGroup):
    image: bpy.props.PointerProperty(type=SrtLoaderImageStyleProperties)
    text: bpy.props.PointerProperty(type=SrtLoaderTextStyleProperties)
    borders: bpy.props.PointerProperty(type=SrtLoaderBorderListStyleProperties)
    shadow: bpy.props.PointerProperty(type=SrtLoaderShadowStyleProperties)
    box: bpy.props.PointerProperty(type=SrtLoaderBoxStyleProperties)


class SrtLoaderProperties(bpy.types.PropertyGroup):
    srt_file: bpy.props.StringProperty(subtype="FILE_PATH")
    image_dir: bpy.props.StringProperty(subtype="DIR_PATH")
    settings: bpy.props.PointerProperty(type=SrtLoaderSettingsProperties)
    styles: bpy.props.PointerProperty(type=SrtLoaderStylesProperties)


class SrtLoaderJimakuSettingsPorperties(bpy.types.PropertyGroup):
    useJimakuSettings: bpy.props.BoolProperty(default=False)
    settings: bpy.props.PointerProperty(type=SrtLoaderSettingsProperties)


class SrtLoaderJimakuStylePorperties(bpy.types.PropertyGroup):
    useJimakuStyle: bpy.props.BoolProperty(default=False)
    styles: bpy.props.PointerProperty(type=SrtLoaderStylesProperties)


class SrtLoaderJimakuProperties(bpy.types.PropertyGroup):
    no: bpy.props.IntProperty(default=0)
    text: bpy.props.StringProperty(default="Text")
    start_frame: bpy.props.FloatProperty(default=1, min=1, precision=1)
    frame_duration: bpy.props.FloatProperty(default=120, min=1, precision=1)
    settings: bpy.props.PointerProperty(type=SrtLoaderJimakuSettingsPorperties)
    styles: bpy.props.PointerProperty(type=SrtLoaderJimakuStylePorperties)


class SrtLoaderCurrentJimakuProperties(bpy.types.PropertyGroup):
    index: bpy.props.IntProperty(default=0)
    list: bpy.props.CollectionProperty(type=SrtLoaderJimakuProperties)
    jimaku_editing: bpy.props.BoolProperty(default=False)


class_list = [
    SrtLoaderSettingsProperties,
    SrtLoaderImageStyleProperties,
    SrtLoaderTextStyleProperties,
    SrtLoaderBorderStyleProperties1,
    SrtLoaderBorderStyleProperties2,
    SrtLoaderBorderListStyleProperties,
    SrtLoaderShadowStyleProperties,
    SrtLoaderBoxStyleProperties,
    SrtLoaderStylesProperties,
    SrtLoaderProperties,
    SrtLoaderJimakuSettingsPorperties,
    SrtLoaderJimakuStylePorperties,
    SrtLoaderJimakuProperties,
    SrtLoaderCurrentJimakuProperties,
]
