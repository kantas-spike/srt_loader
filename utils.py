import datetime
import bpy


def get_frame_rate():
    return bpy.context.scene.render.fps / bpy.context.scene.render.fps_base


def timedelta_to_frame(delta: datetime.timedelta, frame_rate):
    seconds = max(0, delta.total_seconds())
    return seconds * frame_rate
