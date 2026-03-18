import dearpygui.dearpygui as dpg
from fdialog import FileDialog, SaveFileDialog

dpg.create_context()

def show_selected(selected_files):
    dpg.delete_item("txt_child", children_only=True)
    for file in selected_files:
        dpg.add_text(file, parent="txt_child")

def show_save_target(save_path):
    dpg.add_text(f"Save target: {save_path}", parent="txt_child")

fd = FileDialog(callback=show_selected, default_path="..")
sd = SaveFileDialog(callback=show_save_target, default_path="..")

with dpg.window(label="hi", height=480, width=600):
    dpg.add_button(label="Show file dialog", callback=fd.show_file_dialog)
    dpg.add_button(label="Show save dialog", callback=sd.show_save_dialog)
    dpg.add_child_window(width=-1, height=-1, tag="txt_child")


dpg.create_viewport(title='file_dialog example', width=700, height=520)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
