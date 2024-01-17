import bpy
from . import utils


def update_jimaku_property(self, context):
    bpy.data.objects[0].srtloarder_jimaku.jimaku_data_changed = True


class SrtLoaderImageStyleProperties(bpy.types.PropertyGroup):
    padding_x: bpy.props.IntProperty(default=20, update=update_jimaku_property)
    padding_y: bpy.props.IntProperty(default=20, update=update_jimaku_property)


class SrtLoaderTextStyleProperties(bpy.types.PropertyGroup):
    font_family: bpy.props.StringProperty(
        default="Noto Sans JP Bold", update=update_jimaku_property
    )
    size: bpy.props.IntProperty(default=48, update=update_jimaku_property)
    color: bpy.props.FloatVectorProperty(
        subtype="COLOR",
        description="文字の前景色",
        default=utils.hex_to_floatvector("#40516a"),
        update=update_jimaku_property,
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
        update=update_jimaku_property,
    )
    line_space_rate: bpy.props.FloatProperty(
        name="行間",
        description="行間 (単位:文字サイズの比率)",
        default=-0.3,
        update=update_jimaku_property,
    )


class SrtLoaderBorderStyleProperties1(bpy.types.PropertyGroup):
    color: bpy.props.FloatVectorProperty(
        subtype="COLOR",
        min=0,
        max=1.0,
        name="色",
        description="縁取りの色",
        default=utils.hex_to_floatvector("#FFFFFF"),
        update=update_jimaku_property,
    )
    rate: bpy.props.FloatProperty(
        name="サイズ",
        description="縁取りのサイズ(単位:文字サイズの比率)",
        default=0.08,
        min=0,
        max=1,
        update=update_jimaku_property,
    )
    feather: bpy.props.FloatProperty(
        name="ぼかし幅",
        description="縁取りのぼかし幅(単位: px)。0の場合、縁取りをぼかさない",
        default=0,
        update=update_jimaku_property,
    )


class SrtLoaderBorderStyleProperties2(bpy.types.PropertyGroup):
    color: bpy.props.FloatVectorProperty(
        subtype="COLOR",
        name="色",
        description="縁取りの色",
        default=utils.hex_to_floatvector("#40516a"),
        update=update_jimaku_property,
    )
    rate: bpy.props.FloatProperty(
        name="サイズ",
        description="縁取りのサイズ(単位:文字サイズの比率)",
        default=0.08,
        min=0,
        max=1,
        update=update_jimaku_property,
    )
    feather: bpy.props.FloatProperty(
        name="ぼかし幅",
        description="縁取りのぼかし幅(単位: px)。0の場合、縁取りをぼかさない",
        default=0,
        update=update_jimaku_property,
    )


class SrtLoaderBorderListStyleProperties(bpy.types.PropertyGroup):
    number_of_borders: bpy.props.IntProperty(
        default=2, min=0, max=2, update=update_jimaku_property
    )
    style1: bpy.props.PointerProperty(type=SrtLoaderBorderStyleProperties1)
    style2: bpy.props.PointerProperty(type=SrtLoaderBorderStyleProperties2)


class SrtLoaderShadowStyleProperties(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(
        name="利用する", default=False, description="影を利用する", update=update_jimaku_property
    )
    color: bpy.props.FloatVectorProperty(
        subtype="COLOR",
        size=4,
        min=0,
        max=1.0,
        default=utils.hex_to_floatvector("#000000FF"),
        description="影の色",
        update=update_jimaku_property,
    )
    offset_x: bpy.props.IntProperty(
        name="水平オフセット",
        description="影の水平オフセット (単位: px)",
        default=10,
        update=update_jimaku_property,
    )
    offset_y: bpy.props.IntProperty(
        name="垂直オフセット",
        description="影の垂直オフセット (単位: px)",
        default=10,
        update=update_jimaku_property,
    )
    blur_radius: bpy.props.IntProperty(
        name="ぼかし半径",
        description="影のぼかし半径 (単位: px)",
        default=15,
        update=update_jimaku_property,
    )


class SrtLoaderBoxStyleProperties(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(
        name="利用する",
        default=False,
        description="ボックスを利用する",
        update=update_jimaku_property,
    )
    color: bpy.props.FloatVectorProperty(
        subtype="COLOR",
        size=4,
        min=0,
        max=1.0,
        default=utils.hex_to_floatvector("#ccccccff"),
        description="字幕の背景色",
        update=update_jimaku_property,
    )
    padding_x: bpy.props.IntProperty(
        name="Padding X",
        description="字幕画像の水平パディングサイズ(単位: px)",
        default=20,
        update=update_jimaku_property,
    )
    padding_y: bpy.props.IntProperty(
        name="Padding Y",
        description="字幕画像の垂直パディングサイズ(単位: px)",
        default=20,
        update=update_jimaku_property,
    )


class SrtLoaderJimakuSettingsPorperties(bpy.types.PropertyGroup):
    useJimakuSettings: bpy.props.BoolProperty(
        default=False, update=update_jimaku_property
    )
    channel_no: bpy.props.IntProperty(
        default=1, min=1, max=128, update=update_jimaku_property
    )
    offset_x: bpy.props.FloatProperty(default=0, update=update_jimaku_property)
    offset_y: bpy.props.FloatProperty(default=-400, update=update_jimaku_property)


class SrtLoaderJimakuStylePorperties(bpy.types.PropertyGroup):
    useJimakuStyle: bpy.props.BoolProperty(default=False, update=update_jimaku_property)
    image: bpy.props.PointerProperty(type=SrtLoaderImageStyleProperties)
    text: bpy.props.PointerProperty(type=SrtLoaderTextStyleProperties)
    borders: bpy.props.PointerProperty(type=SrtLoaderBorderListStyleProperties)
    shadow: bpy.props.PointerProperty(type=SrtLoaderShadowStyleProperties)
    box: bpy.props.PointerProperty(type=SrtLoaderBoxStyleProperties)


class SrtLoaderJimakuProperties(bpy.types.PropertyGroup):
    no: bpy.props.IntProperty(default=0, update=update_jimaku_property)
    text: bpy.props.StringProperty(default="Text", update=update_jimaku_property)
    start_frame: bpy.props.FloatProperty(
        default=1, min=1, precision=0, update=update_jimaku_property
    )
    frame_duration: bpy.props.FloatProperty(
        default=120, min=1, precision=0, update=update_jimaku_property
    )
    settings: bpy.props.PointerProperty(type=SrtLoaderJimakuSettingsPorperties)
    styles: bpy.props.PointerProperty(type=SrtLoaderJimakuStylePorperties)


class SrtLoaderCurrentJimakuProperties(bpy.types.PropertyGroup):
    index: bpy.props.IntProperty(default=0)
    list: bpy.props.CollectionProperty(type=SrtLoaderJimakuProperties)
    jimaku_editing: bpy.props.BoolProperty(default=False)
    jimaku_data_changed: bpy.props.BoolProperty(default=False)


class_list = [
    SrtLoaderImageStyleProperties,
    SrtLoaderTextStyleProperties,
    SrtLoaderBorderStyleProperties1,
    SrtLoaderBorderStyleProperties2,
    SrtLoaderBorderListStyleProperties,
    SrtLoaderShadowStyleProperties,
    SrtLoaderBoxStyleProperties,
    SrtLoaderJimakuSettingsPorperties,
    SrtLoaderJimakuStylePorperties,
    SrtLoaderJimakuProperties,
    SrtLoaderCurrentJimakuProperties,
]
