import dearpygui.dearpygui as dpg
from fdialog import FileDialog

dpg.create_context()

def pr(selected_files):
    dpg.delete_item("txt_child", children_only=True)
    for file in selected_files:
        dpg.add_text(file, parent="txt_child")

fd = FileDialog(callback=pr, show_dir_size=False, modal=False, allow_drag=False, default_path="..")

with dpg.window(label="hi", height=100, width=100):
    dpg.add_button(label="fd", callback=fd.show_file_dialog)
    dpg.add_child_window(width=-1, height=-1, tag="txt_child")


dpg.create_viewport(title='Test', width=300, height=50)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()