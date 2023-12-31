![pre](https://github.com/totallynotdrait/file_dialog/assets/108739871/9fa6e4b2-adb0-4000-98fe-1e5f7c273abe)

# file_dialog
file_dialog is a beautiful file dialog add-on for DearPyGui applications

example:
```python
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
```
Note: The file dialog callback can be changed by using ```change_callback()```

# Installation
- Download the zip file and extract it
- Move the file_dialog folder into your project and then import fdialog.py or the FileDialog class

# Features
- Nice and beautiful interface
- Modern icons for different file exstensions
- Shortcut menu with also a list of external and internal drives
- Complete customization of the file dialog window and it's features
- Can be used at all time by using ```show_file_dialog()``` function
- Display hidden files and folders
- Dragging items

# Requirements
- DearPyGui
- psutil

# Credits
icons8 - for the 3D Fluency icons - https://icons8.it/icons/3d-fluency
