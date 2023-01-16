import bpy
from bpy.props import StringProperty, IntProperty, FloatProperty
import os
from . import my_srt

bl_info = {
    "name": "SubRip形式の字幕ファイルを読み込み、VSEに字幕を追加するアドオン",
    "author": "kanta",
    "version": (0, 1),
    "blender": (3, 4, 0),
    "location": "VSE > Sidebar",
    "description": "SubRip形式の字幕ファイルを読み込み、VSEに字幕を追加するアドオン",
    "category": "Object"
}


class SrtLoaderImportImages(bpy.types.Operator):
    bl_idname = "srt_loader.import_images"
    bl_label = "字幕画像をインポートする"
    bl_description = "画像ディレクトリから字幕画像をインポートする"
    bl_options = {'REGISTER', 'UNDO'}

    def load_jimaku(self, srt_path, img_dir, channel_no=4, offset_x=0, offset_y=-400):
        abs_srt_path = bpy.path.abspath(srt_path)
        abs_img_dir = bpy.path.abspath(img_dir)

        fps = round(bpy.context.scene.render.fps / bpy.context.scene.render.fps_base)

        items = my_srt.read_srt_file(abs_srt_path)
        for item in items:
            img_path = os.path.join(abs_img_dir, f"{item['no']}.png")
            if os.path.isfile(img_path):
                # load image
                start_frame = int(
                    item["time_info"]["start"].total_seconds() * fps)
                end_frame = int(
                    item["time_info"]["end"].total_seconds() * fps)

                img = bpy.context.scene.sequence_editor.sequences.new_image(
                    os.path.basename(img_path), img_path, channel_no, start_frame, fit_method="ORIGINAL")
                img.frame_final_end = end_frame
                img.transform.offset_y = offset_y

    def execute(self, context):
        srt_path = bpy.data.objects[0].srt_loader.srt_file
        img_dir = bpy.data.objects[0].srt_loader.image_dir
        if srt_path is None:
            return {'CANCELLED'}
        if img_dir is None:
            return {'CANCELLED'}

        self.load_jimaku(srt_path, img_dir,
                         bpy.data.objects[0].srt_loader.channel_no,
                         bpy.data.objects[0].srt_loader.offset_x,
                         bpy.data.objects[0].srt_loader.offset_y)
        return {'FINISHED'}


class SrtLoaderPanel(bpy.types.Panel):
    bl_label = "SRT Loader"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "字幕画像"
    # bl_context = "objectmode"

    @classmethod
    def poll(cls, context):
        return context.space_data.view_type == 'SEQUENCER'

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon='PLUGIN')

    def draw(self, context):
        layout = self.layout
        layout.label(text="srt file")
        layout.prop(bpy.data.objects[0].srt_loader, 'srt_file', text='file:')
        layout.prop(bpy.data.objects[0].srt_loader,
                    'image_dir', text='image dir:')
        layout.prop(bpy.data.objects[0].srt_loader,
                    'channel_no', text='Channel No.:')
        layout.prop(bpy.data.objects[0].srt_loader,
                    'offset_x', text='Default Image Offset X')
        layout.prop(bpy.data.objects[0].srt_loader,
                    'offset_y', text='Default Image Offset Y')
        layout.operator(SrtLoaderImportImages.bl_idname, text="字幕画像を読み込む")


class SrtLoaderProperties(bpy.types.PropertyGroup):
    srt_file: bpy.props.StringProperty(subtype="FILE_PATH")
    image_dir: bpy.props.StringProperty(subtype="DIR_PATH")
    channel_no: bpy.props.IntProperty(default=1, min=1, max=128)
    offset_x: bpy.props.FloatProperty(default=0)
    offset_y: bpy.props.FloatProperty(default=-400)


classes = [SrtLoaderPanel, SrtLoaderProperties, SrtLoaderImportImages]


def register():
    for c in classes:
        bpy.utils.register_class(c)

    # bpy.types.
    bpy.types.Object.srt_loader = bpy.props.PointerProperty(
        type=SrtLoaderProperties)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

    del bpy.types.Object.srt_loader


if __name__ == "__main__":
    register()
