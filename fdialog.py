#[[
#
#       Copyright (C) Workspace Desktop Interface
#       Developed and created by Arthur - Ionut Turcan (AKA Dr. AIT)
#
#   INFO:
#   None
#   
#   
#
#
#]]

"""
File Dialog is a File Dialog specificaly designed for Workspace Desktop Interface
It 'Returns' the selected files or folders.
"""



import dearpygui.dearpygui as dpg
import os
import time
import shutil
import psutil

# will check if the module 'send2trash' is installed, if not it will install with pip3
try:
    import send2trash
except ModuleNotFoundError:
    os.system("pip3 install send2trash")

import threading


last_click_time = 0


class FileDialog:
    """
    Arguments:
        width:                  Sets the File dialog window width
        height:                 Sets the File dialog window height
        dirs_only:              When true it will only list directories
        default_path:           The default path when File dialog starts, if it's cwd it will be the current working directory
        file_filter:            If it's for example .py it will only list that type of files
        callback:               When the Ok button has pressed it will call the defined function
        show_dir_size:          When true it will list the directories with the size of the directory and its sub-directories and files (reccomended to False)
        allow_drag:             When true it will allow to the user to drag the file or folder to a group
        multi_selction:         If true it will allow the user to select multiple files and folder
        show_shortcuts_menu:    A child window containing different shortcuts (like desktop and downloads) and of the esternal and internal drives
        no_resize:              When true the window will not be able to resize
        modal:                  A sort of popup effect (can cause problems when the file dialog is activated by a modal window)
    Returns:
        Window
    """
    def __init__(
        self,
        width=950,
        height=650,
        dirs_only=False,
        default_path="cwd",
        file_filter=".*",
        callback=None,
        show_dir_size=False, # NOTE: This argument is reccomended to set it to False, because it can take a while, probably hours or days, to calculate the size of the folder and it's sub-directories
        allow_drag=True,
        multi_selection=True,
        show_shortcuts_menu=True,
        no_resize=True,
        modal=True,
    ):
        
        self.width = width
        self.height = height
        self.dirs_only = dirs_only
        self.default_path = default_path
        self.file_filter = file_filter
        self.callback = callback
        self.show_dir_size = show_dir_size
        self.allow_drag = allow_drag
        self.multi_selection = multi_selection
        self.show_shortcuts_menu = show_shortcuts_menu
        self.no_resize = no_resize
        self.modal = modal

        selected_files = []
        self.selected_files = selected_files
        
        with dpg.theme() as selec_alignt:
            with dpg.theme_component(dpg.mvThemeCat_Core):
                dpg.add_theme_style(dpg.mvStyleVar_SelectableTextAlign, x=0, y=.5)

        with dpg.theme() as size_alignt:
            with dpg.theme_component(dpg.mvThemeCat_Core):
                dpg.add_theme_style(dpg.mvStyleVar_SelectableTextAlign, x=1, y=.5)

        def return_items():
            dpg.hide_item("file_dialog")
            if callback == None:
                pass
            else:
                self.callback(self.selected_files)
            selected_files.clear()
            reset_dir(".")



        big_icons = True
        PAYLOAD_TYPE = 'file_dialog'



        # adds the icons
        # DO NOT CHANGE THE PATH OR DELETE THE FILES
        diwidth, diheight, dichannels, didata = dpg.load_image("images/document.png")
        afiwidth, afiheight, afichannels, afidata = dpg.load_image("images/add_folder.png")
        afwidth, afheight, afchannels, afdata = dpg.load_image("images/add_file.png")
        mfwidth, mfheight, mfchannels, mfdata = dpg.load_image("images/mini_folder.png")
        fiwidth, fiheight, fichannels, fidata = dpg.load_image("images/folder.png")
        mdwidth, mdheight, mdchannels, mddata = dpg.load_image("images/mini_document.png")
        mewidth, meheight, mechannels, medata = dpg.load_image("images/mini_error.png")
        rwidth, rheight, rchannels, rdata = dpg.load_image("images/refresh.png")
        hdwidth, hdheight, hdchannels, hddata = dpg.load_image("images/hd.png")
        pwidth, pheight, pchannels, pdata = dpg.load_image("images/picture.png")
        bpwidth, bpheight, bpchannels, bpdata = dpg.load_image("images/big_picture.png")
        pfwidth, pfheight, pfchannels, pfdata = dpg.load_image("images/picture_folder.png")
        dwidth, dheight, dchannels, ddata = dpg.load_image("images/desktop.png")
        vwidth, vheight, vchannels, vdata = dpg.load_image("images/videos.png")
        mwidth, mheight, mchannels, mdata = dpg.load_image("images/music.png")
        dfwidth, dfheight, dfchannels, dfdata = dpg.load_image("images/downloads.png")
        dcfwidth, dcfheight, dcfchannels, dcfdata = dpg.load_image("images/documents.png")
        swidth, sheight, schannels, sdata = dpg.load_image("images/search.png")

        with dpg.texture_registry():
            dpg.add_static_texture(width=diwidth, height=diheight, default_value=didata, tag="document_icon")
            dpg.add_static_texture(width=afiwidth, height=afiheight, default_value=afidata, tag="add_folder_icon")
            dpg.add_static_texture(width=afwidth, height=afheight, default_value=afdata, tag="add_file_icon")
            dpg.add_static_texture(width=mfwidth, height=mfheight, default_value=mfdata, tag="mini_folder")
            dpg.add_static_texture(width=fiwidth, height=fiheight, default_value=fidata, tag="folder_icon")
            dpg.add_static_texture(width=mdwidth, height=mdheight, default_value=mddata, tag="mini_document")
            dpg.add_static_texture(width=mewidth, height=meheight, default_value=medata, tag="mini_error")
            dpg.add_static_texture(width=rwidth, height=rheight, default_value=rdata, tag="refresh")
            dpg.add_static_texture(width=hdwidth, height=hdheight, default_value=hddata, tag="harddisk")
            dpg.add_static_texture(width=pwidth, height=pheight, default_value=pdata, tag="picture")
            dpg.add_static_texture(width=bpwidth, height=bpheight, default_value=bpdata, tag="big_picture")
            dpg.add_static_texture(width=pfwidth, height=pfheight, default_value=pfdata, tag="picture_folder")
            dpg.add_static_texture(width=dwidth, height=dheight, default_value=ddata, tag="desktop")
            dpg.add_static_texture(width=vwidth, height=vheight, default_value=vdata, tag="videos")
            dpg.add_static_texture(width=mwidth, height=mheight, default_value=mdata, tag="music")
            dpg.add_static_texture(width=dfwidth, height=dfheight, default_value=dfdata, tag="downloads")
            dpg.add_static_texture(width=dcfwidth, height=dcfheight, default_value=dcfdata, tag="documents")
            dpg.add_static_texture(width=swidth, height=sheight, default_value=sdata, tag="search")

        
        #the main function that lists the files and folders
        def reset_dir(dirpath=self.default_path, dirs_only=self.dirs_only, ffilter=self.file_filter):
            global internal
            def internal():
                global count, selected_files_int
                count = 0
                path = os.getcwd()
                selected_files.clear()
                try:
                    dirlist = os.listdir(path)

                    if list:
                        def dir_back():
                            global last_click_time
                            current_time = time.time()
                            if current_time - last_click_time < 0.5:  # adjust the time as needed
                                chdir("..")
                                last_click_time = 0

                        delete_table()
                        selec_height = 16
                        count = 0
                        # Get the file name
                        with dpg.table_row(parent="explorer"):
                            dpg.add_selectable(label="..", callback=dir_back, span_columns=True, height=selec_height)
                        if dirs_only:
                            for item in dirlist:
                                if os.path.isdir(item):
                                    count += 1
                                    selected_files_int = 0
                                    file_name = os.path.basename(item)
                                    
                                    # Get the creation time and format it
                                    creation_time = os.path.getctime(item)
                                    creation_time = time.ctime(creation_time)

                                    # Get the type of the item
                                    item_type = "Dir" if os.path.isdir(item) else "File"

                                    # Get the size of the item
                                    item_size = get_file_size(item)

                                    # Add a row to the table

                                    
                                    with dpg.table_row(parent="explorer"):
                                        with dpg.group(horizontal=True):
                                            if file_name.endswith((".png", ".jpg")):
                                                dpg.add_image("picture")
                                            elif item_type == "Dir":
                                                dpg.add_image("mini_folder")
                                            elif item_type == "File":
                                                dpg.add_image("mini_document")
                                            
                                            cell_name = dpg.add_selectable(label=file_name, callback=print_file, height=selec_height, span_columns=True, user_data=[file_name, path+"\\"+file_name])
                                        cell_time = dpg.add_selectable(label=creation_time, callback=print_file, span_columns=True, height=selec_height, user_data=[file_name, path+"\\"+file_name])
                                        cell_type = dpg.add_selectable(label=item_type, callback=print_file, span_columns=True, height=selec_height, user_data=[file_name, path+"\\"+file_name])
                                        cell_size = dpg.add_selectable(label=str(item_size), callback=print_file, span_columns=True, height=selec_height, user_data=[file_name, path+"\\"+file_name])
                                        
                                        if self.allow_drag == True:
                                            drag_payload = dpg.add_drag_payload(parent=cell_name, payload_type=PAYLOAD_TYPE)
                                        dpg.bind_item_theme(cell_name, selec_alignt)
                                        dpg.bind_item_theme(cell_time, selec_alignt)
                                        dpg.bind_item_theme(cell_type, selec_alignt)
                                        dpg.bind_item_theme(cell_size, size_alignt)
                                        if self.allow_drag == True:
                                            if file_name.endswith((".png", ".jpg")):
                                                dpg.add_image("big_picture", parent=drag_payload)
                                            elif item_type == "Dir":
                                                dpg.add_image("folder_icon", parent=drag_payload)
                                            elif item_type == "File":
                                                dpg.add_image("document_icon", parent=drag_payload)
                        else:
                            for item in dirlist:
                                if os.path.isdir(item):
                                    count += 1
                                    selected_files_int = 0
                                    file_name = os.path.basename(item)
                                    
                                    # Get the creation time and format it
                                    creation_time = os.path.getctime(item)
                                    creation_time = time.ctime(creation_time)

                                    # Get the type of the item
                                    item_type = "Dir" if os.path.isdir(item) else "File"

                                    # Get the size of the item
                                    item_size = get_file_size(item)

                                    # Add a row to the table

                                    
                                    with dpg.table_row(parent="explorer"):
                                        with dpg.group(horizontal=True):
                                            if file_name.endswith((".png", ".jpg")):
                                                dpg.add_image("picture")
                                            elif item_type == "Dir":
                                                dpg.add_image("mini_folder")
                                            elif item_type == "File":
                                                dpg.add_image("mini_document")
                                            
                                            cell_name = dpg.add_selectable(label=file_name, callback=print_file, height=selec_height, span_columns=True, user_data=[file_name, path+"\\"+file_name])
                                        cell_time = dpg.add_selectable(label=creation_time, callback=print_file, span_columns=True, height=selec_height, user_data=[file_name, path+"\\"+file_name])
                                        cell_type = dpg.add_selectable(label=item_type, callback=print_file, span_columns=True, height=selec_height, user_data=[file_name, path+"\\"+file_name])
                                        cell_size = dpg.add_selectable(label=str(item_size), callback=print_file, span_columns=True, height=selec_height, user_data=[file_name, path+"\\"+file_name])

                                        if self.allow_drag == True:
                                            drag_payload = dpg.add_drag_payload(parent=cell_name, payload_type=PAYLOAD_TYPE)
                                        dpg.bind_item_theme(cell_name, selec_alignt)
                                        dpg.bind_item_theme(cell_time, selec_alignt)
                                        dpg.bind_item_theme(cell_type, selec_alignt)
                                        dpg.bind_item_theme(cell_size, size_alignt)
                                        if self.allow_drag == True:
                                            if file_name.endswith((".png", ".jpg")):
                                                dpg.add_image("big_picture", parent=drag_payload)
                                            elif item_type == "Dir":
                                                dpg.add_image("folder_icon", parent=drag_payload)
                                            elif item_type == "File":
                                                dpg.add_image("document_icon", parent=drag_payload)
                            for item in dirlist:
                                if os.path.isfile(item):
                                    if self.file_filter == ".*" or item.endswith(self.file_filter):  
                                        count += 1
                                        selected_files_int = 0
                                        file_name = os.path.basename(item)
                                        
                                        # Get the creation time and format it
                                        creation_time = os.path.getctime(item)
                                        creation_time = time.ctime(creation_time)

                                        # Get the type of the item
                                        item_type = "Dir" if os.path.isdir(item) else "File"

                                        # Get the size of the item
                                        item_size = get_file_size(item)

                                        # Add a row to the table

                                        
                                        with dpg.table_row(parent="explorer"):
                                            with dpg.group(horizontal=True):
                                                if file_name.endswith((".png", ".jpg", ".jpeg")):
                                                    dpg.add_image("picture")
                                                elif item_type == "Dir":
                                                    dpg.add_image("mini_folder")
                                                elif item_type == "File":
                                                    dpg.add_image("mini_document")
                                                
                                                cell_name = dpg.add_selectable(label=file_name, callback=print_file, height=selec_height, span_columns=True, user_data=[file_name, path+"\\"+file_name])
                                            cell_time = dpg.add_selectable(label=creation_time, callback=print_file, span_columns=True, height=selec_height, user_data=[file_name, path+"\\"+file_name])
                                            cell_type = dpg.add_selectable(label=item_type, callback=print_file, span_columns=True, height=selec_height, user_data=[file_name, path+"\\"+file_name])
                                            cell_size = dpg.add_selectable(label=str(item_size), callback=print_file, span_columns=True, height=selec_height, user_data=[file_name, path+"\\"+file_name])

                                            if self.allow_drag == True:
                                                drag_payload = dpg.add_drag_payload(parent=cell_name, payload_type=PAYLOAD_TYPE)
                                            dpg.bind_item_theme(cell_name, selec_alignt)
                                            dpg.bind_item_theme(cell_time, selec_alignt)
                                            dpg.bind_item_theme(cell_type, selec_alignt)
                                            dpg.bind_item_theme(cell_size, size_alignt)
                                            if self.allow_drag == True:
                                                if file_name.endswith((".png", ".jpg")):
                                                    dpg.add_image("big_picture", parent=drag_payload)
                                                elif item_type == "Dir":
                                                    dpg.add_image("folder_icon", parent=drag_payload)
                                                elif item_type == "File":
                                                    dpg.add_image("document_icon", parent=drag_payload)
                        dpg.configure_item("ex_path_input", default_value=os.getcwd())
                        
                    else:
                        print("DEV:ERROR: path is not defined or not true")
                except FileNotFoundError:
                    print("DEV:ERROR: Invalid path : "+str(dirpath))
                except Exception as e:
                    message_box("File dialog - Error", f"An unknown error has occured when listing the items,\nplease restart the application.\n\nMore info:\n{e}")

            previous_contents = set(os.listdir(os.getcwd()))

            thread = threading.Thread(target=internal, args=(), daemon=True)
            thread.start() # this is used to make sure the program continues to work while the internal function is still working
        
        
        # checks if there are any changes to the directory
        def check_dir():
            global previous_contents
            directory_to_monitor = os.getcwd()
            current_contents = set(os.listdir(directory_to_monitor))
            new_items = current_contents - previous_contents
            if new_items:
                reset_dir(os.getcwd())

            deleted_items = previous_contents - current_contents
            if deleted_items:
                reset_dir(os.getcwd())

            previous_contents = current_contents

        def delete_table():
            for child in dpg.get_item_children("explorer", 1):
                dpg.delete_item(child)

        def message_box(title, message):
            with dpg.mutex():
                viewport_width = dpg.get_viewport_client_width()
                viewport_height = dpg.get_viewport_client_height()
                with dpg.window(label=title, no_close=True) as modal_id:
                    dpg.add_text(message)
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Ok", width=-1, user_data=(modal_id, True), callback=lambda:dpg.delete_item(modal_id))

            dpg.split_frame()
            width = dpg.get_item_width(modal_id)
            height = dpg.get_item_height(modal_id)
            dpg.set_item_pos(modal_id, [viewport_width // 2 - width // 2, viewport_height // 2 - height // 2])

        def chdir(path):
            try:
                cwd = os.getcwd()
                os.chdir(path)
                reset_dir(cwd)
            except PermissionError as e:
                message_box("Explorer - PerimssionError", f"Cannot open the folder because is a system folder or the access is denied\n\nMore info:\n{e}")

        

        def print_file(sender, app_data, user_data):
            global last_click_time
        
            #print("dclick")
            if dpg.is_key_down(dpg.mvKey_Control):
                if dpg.get_value(sender) == True:
                    selected_files.append(user_data[1])
                else:
                    selected_files.remove(user_data[1])
            else:
                dpg.set_value(sender, False)

                current_time = time.time()
                if current_time - last_click_time < 0.5:  # adjust the time as needed
                    #print(f"Selectable {sender} has been double clicked")
                    if user_data is not None and user_data[1] is not None:
                        if os.path.isdir(user_data[1]):
                            #print(f"Content:{dpg.get_item_label(sender)}, files: {user_data}")
                            chdir(user_data[1])
                        elif os.path.isfile(user_data[1]):
                            selected_files.append(user_data[1])
                            return_items()
                            return user_data[1]
                last_click_time = current_time
                
                            

        def get_all_drives():
            all_drives = psutil.disk_partitions()
            drive_list = [drive.device for drive in all_drives if drive.device]
            return drive_list

        def get_file_size(file_path):
            # Get the file size in bytes
            
            if os.path.isdir(file_path):
                if self.show_dir_size:
                    total = 0
                    for path, dirs, files in os.walk(file_path):
                        for f in files:
                            fp = os.path.join(path, f)
                            total += os.path.getsize(fp)
                    file_size_bytes = total
                else:
                    file_size_bytes = "-"
            elif os.path.isfile(file_path):
                file_size_bytes = os.path.getsize(file_path)

            # Define the units and their respective sizes
            size_units = [
                ("TB", 2**40),  # Tebibyte
                ("GB", 2**30),  # Gibibyte
                ("MB", 2**20),  # Mebibyte
                ("KB", 2**10),  # Kibibyte
                ("B", 1),        # Byte
            ]

            # Determine the appropriate unit for formatting
            if not file_size_bytes == "-":
                for unit, size_limit in size_units:
                    if file_size_bytes >= size_limit:
                        # Calculate the size in the selected unit
                        file_size = file_size_bytes / size_limit
                        # Return the formatted size with the unit
                        return f"{file_size:.0f} {unit}"
            else:
                return "-"

            # If the file size is smaller than 1 byte or unknown
            return "0 B"  # or "Unknown" or any other desired default



        def new_dir():
            with dpg.window(label="New directory", width=350, no_close=True, no_collapse=True, pos=(50, 50)) as nd:
                dpg.add_input_text(default_value=os.getcwd(), width=-1, hint="Path", tag="ex_nd_path")
                with dpg.group(horizontal=True):
                    dpg.add_button(label="Create", width=80, callback=lambda:(os.mkdir(dpg.get_value("ex_nd_path")), reset_dir(os.getcwd()), dpg.delete_item(nd)))
                    dpg.add_button(label="Cancel", width=80, callback=lambda:dpg.delete_item(nd))

        def new_file():
            with dpg.window(label="New file", width=350, no_close=True, no_collapse=True, pos=(50, 50)) as nd:
                dpg.add_input_text(default_value=os.getcwd(), width=-1, hint="Path", tag="ex_nf_file")
                with dpg.group(horizontal=True):
                    dpg.add_button(label="Create", width=80, callback=lambda:(open(dpg.get_value("ex_nf_file"), "w"), reset_dir(os.getcwd()), dpg.delete_item(nd)))
                    dpg.add_button(label="Cancel", width=80, callback=lambda:dpg.delete_item(nd))


        def ddf():
            with dpg.window(label="Delete directory or file", width=350, no_close=True, no_collapse=True, pos=(50, 50)) as nd:
                dpg.add_input_text(default_value=os.getcwd(), width=-1, hint="Path", tag="ex_ddf")
                with dpg.group(horizontal=True):
                    def delete():
                        try:
                            if os.path.isdir(dpg.get_value("ex_ddf")):
                                shutil.rmtree(dpg.get_value("ex_ddf"))
                            elif os.path.isfile(dpg.get_value("ex_ddf")):
                                os.remove(dpg.get_value("ex_ddf"))
                        except FileNotFoundError:
                            message_box("Invalid path", "No such file or directory")
                        except PermissionError:
                            chdir("..")
                            if os.path.isdir(dpg.get_value("ex_ddf")):
                                shutil.rmtree(dpg.get_value("ex_ddf"))
                            elif os.path.isfile(dpg.get_value("ex_ddf")):
                                os.remove(dpg.get_value("ex_ddf"))

                    dpg.add_button(label="Delete", width=80, callback=lambda:(delete(), reset_dir(os.getcwd()), dpg.delete_item(nd)))
                    dpg.add_button(label="Cancel", width=80, callback=lambda:dpg.delete_item(nd))

        
        with dpg.window(label="File dialog", tag="file_dialog", no_resize=self.no_resize, show=False, modal=self.modal, width=self.width, height=self.height, min_size=(460, 320)):
            info_px = 50

            with dpg.group(horizontal=True):
                with dpg.child_window(tag="ex_shortcut", width=200, show=self.show_shortcuts_menu, height=-info_px):

                    def selec_drive(sender, app_data, user_data):
                        chdir(user_data)

                    drives = get_all_drives()
                    desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
                    downloads = os.path.join(os.environ['USERPROFILE'], 'Downloads')
                    images = os.path.join(os.environ['USERPROFILE'], 'Images')
                    documents = os.path.join(os.environ['USERPROFILE'], 'Documents')
                    musics = os.path.join(os.environ['USERPROFILE'], 'Musics')
                    videos = os.path.join(os.environ['USERPROFILE'], 'Videos')
                    with dpg.group(horizontal=True):
                        dpg.add_image("desktop")
                        dpg.add_menu_item(label="Desktop", callback=lambda:chdir(desktop))

                    with dpg.group(horizontal=True):
                        dpg.add_image("downloads")
                        dpg.add_menu_item(label="Downloads", callback=lambda:chdir(downloads))
                    with dpg.group(horizontal=True):
                        dpg.add_image("picture_folder")
                        dpg.add_menu_item(label="Images", callback=lambda:chdir(images))
                    with dpg.group(horizontal=True):
                        dpg.add_image("documents")
                        dpg.add_menu_item(label="Documents", callback=lambda:chdir(documents))
                    with dpg.group(horizontal=True):
                        dpg.add_image("music")    
                        dpg.add_menu_item(label="Musics", callback=lambda:chdir(musics))
                    with dpg.group(horizontal=True):
                        dpg.add_image("videos")
                        dpg.add_menu_item(label="Videos", callback=lambda:chdir(videos))
                    dpg.add_separator()
                    with dpg.group(tag="ex_drives"):
                        for drive in drives:
                            with dpg.group(horizontal=True):
                                dpg.add_image("harddisk")
                                dpg.add_menu_item(label=drive, user_data=drive, callback=selec_drive)


                with dpg.group():
                    def on_path_enter():
                        try:
                            chdir(dpg.get_value("ex_path_input"))
                        except FileNotFoundError:
                            message_box("Invalid path", "No such file or directory")

                    with dpg.group(horizontal=True):
                        dpg.add_image_button("refresh", tag="ex_refresh", callback=lambda:reset_dir(os.getcwd()))
                        dpg.add_input_text(hint="Path", on_enter=True, callback=on_path_enter,  default_value=os.getcwd(), width=-1, height=20, tag="ex_path_input")
                        

                        with dpg.tooltip("ex_refresh"):
                            dpg.add_text("Refresh the current working directory")

                    with dpg.group(horizontal=True):
                        dpg.add_input_text(hint="Search files", width=-34, height=16)
                        dpg.add_image_button("search", callback=lambda:print("Not implemented yet!"))

                    with dpg.table(
                        tag=f'explorer',
                        height=-info_px,
                        width=-1,
                        resizable=True, 
                        policy=dpg.mvTable_SizingStretchProp, 
                        borders_innerV=True, 
                        reorderable=True, 
                        hideable=True,
                        sortable=True,
                        scrollX=True,
                        scrollY=True,
                        ):
                        iwow_name = 100
                        iwow_date = 50
                        iwow_type = 10
                        iwow_size = 10
                        dpg.add_table_column(label='Name',     init_width_or_weight=iwow_name, tag="ex_name")
                        dpg.add_table_column(label='Date',     init_width_or_weight=iwow_date, tag="ex_date")
                        dpg.add_table_column(label='Type',     init_width_or_weight=iwow_type, tag="ex_type")
                        dpg.add_table_column(label='Size',     init_width_or_weight=iwow_size, width=10, tag="ex_size")

            def filter_combo_selector(sender, app_data):
                global file_filter
                filter_file = dpg.get_value(sender)
                file_filter = filter_file
                self.file_filter = filter_file
                reset_dir(".", ffilter=file_filter)

            with dpg.group(horizontal=True):
                dpg.add_spacer(width=50)
                dpg.add_text('File type filter')
                dpg.add_combo(items=[".*", ".exe", ".py", ".png", ".jpg", ".jpeg", ".wav", ".mp3", ".ogg", ".mp4", ".txt", ".c", ".cpp", ".cs", ".h", ".pyl", ".phs", ".js", "json", ".rs", ".vbs", ".ini", ".ppack", ".fbx", ".obj", ".mlt", ".bat", ".sh"], callback=filter_combo_selector, default_value=".*", width=-1)
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=self.width*0.82)
                dpg.add_button(label="   OK   ", callback=return_items)
                dpg.add_button(label=" Cancel ", callback=lambda:dpg.hide_item("file_dialog"))
                
            if self.default_path == "cwd":
                reset_dir(os.getcwd())
            else:
                reset_dir(self.default_path)

        def del_files(title, message):
            #[[
            # 
            # This function will delete the selected files
            # but not completely delete those files,
            # it will only move them in the recycle bin using send2trash, theoratically
            # 
            # ]]
            def fdel():
                for file in selected_files:
                    if os.path.isdir(file):
                        #shutil.rmtree(file)
                        send2trash.send2trash(file)
                    elif os.path.isfile(file):
                        #os.remove(file)
                        send2trash.send2trash(file)
                    else:
                        message_box("Error - Explorer", f"Error on deleteing {file}, not a directory or file")
                        return 1
                return 0
            with dpg.mutex():
                viewport_width = dpg.get_viewport_client_width()
                viewport_height = dpg.get_viewport_client_height()
                with dpg.window(label=title, modal=True, no_close=False) as modal_id:
                    dpg.add_text(message)
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Ok", width=18, user_data=(modal_id, True), callback=lambda:(fdel(), reset_dir(".."), dpg.delete_item(modal_id)))

        def del_item_with_del():
            if dpg.is_key_down(dpg.mvKey_Delete):
                if selected_files != None:
                    message_box("Explorer", f"Delete the following Items?\n{selected_files}")
                
            

        with dpg.handler_registry():
            dpg.add_mouse_click_handler(button=dpg.mvMouseButton_X1, callback=lambda:chdir(".."))
            dpg.add_key_press_handler(callback=del_item_with_del)
            dpg.add_mouse_double_click_handler(callback=print_file)

    def change_callback(self, callback):
        self.callback = callback

    def show_file_dialog(*args):
        if len(args) > 0:
            pass
        dpg.show_item("file_dialog")

    def change_args(self,
                    width=None, height=None, dirs_only=None, default_path=None,
                    file_filter=None, callback=None, show_dir_size=None,
                    allow_drag=None, multi_selection=None):
        if width is not None:
            dpg.set_item_width("file_dialog", width)
        if height is not None:
            dpg.set_item_width("file_dialog", height)
        if dirs_only is not None:
            self.dirs_only = dirs_only
        if default_path is not None:
            self.default_path = default_path
        if file_filter is not None:
            self.file_filter = file_filter
        if callback is not None:
            self.callback = callback
        if show_dir_size is not None:
            self.show_dir_size = show_dir_size
        if allow_drag is not None:
            self.allow_drag = allow_drag
        if multi_selection is not None:
            self.multi_selection = multi_selection

