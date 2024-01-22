import bpy
import os

base_name = os.path.basename(__file__).rstrip(".py")
dir_name = os.path.basename(os.path.dirname(__file__))

if dir_name == "default_styles":
    srtloarder_settings = bpy.data.objects[0].srtloarder_settings
    srtloarder_settings.styles.preset_name = base_name
elif dir_name == "jimaku_styles":
    list = bpy.data.objects[0].srtloarder_jimaku.list
    index = bpy.data.objects[0].srtloarder_jimaku.index
    jimaku = list[index]
    jimaku.styles.preset_name = base_name
