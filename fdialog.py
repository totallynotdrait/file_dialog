# file_dialog 3.1
# MIT lincensed

import dearpygui.dearpygui as dpg
import os
import time
import psutil
import platform
from glob import glob


class FileDialog:
    """
    Arguments:
        title:                  Sets the file dialog window name.
        tag:                    Sets the file dialog tag.
        width:                  Sets the file dialog window width.
        height:                 Sets the file dialog window height.
        min_size:               Sets the file dialog minimum size.
        dirs_only:              When true it will only list directories.
        default_path:           The default path when file_dialog starts, if it's 'cwd' it will be the current working directory.
        filter_list:            An array of different file extensions.
        file_filter:            If it's for example .py it will only list that type of files.
        callback:               When the Ok button has pressed it will call the defined function.
        show_dir_size:          When true it will list the directories with the size of the directory and its sub-directories and files (recommended to False).
        allow_drag:             When true it will allow to the user to drag the file or folder to a group.
        multi_selection:        If true it will allow the user to select multiple files and folder.
        show_shortcuts_menu:    A child window containing different shortcuts (like desktop and downloads) and of the external and internal drives.
        no_resize:              When true the window will not be able to resize.
        modal:                  A sort of popup effect (can cause problems when the file dialog is activated by a modal window).
        show_hidden_files:      Shows to the directory listing hidden files including folders.
        user_style:             Different graphical styles for file_dialog.
    Returns:
        None
    """
    # low-level functions
    def _get_all_drives(self,):
        all_drives = psutil.disk_partitions()

        drive_list = [
            drive.mountpoint for drive in all_drives if drive.mountpoint]

        if os.name == 'posix':
            for device in os.listdir('/dev'):
                if device.startswith("sd") or device.startswith("nvme"):
                    device_path = f"/dev/{device}"
                    if device_path not in drive_list:
                        drive_list.append(device_path)

        return drive_list

    def delete_table(self,):
        for child in dpg.get_item_children(self.tag+"explorer", 1):
            dpg.delete_item(child)

    def get_file_size(self, file_path):
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
            ("TB", 2**40),  # Terabyte
            ("GB", 2**30),  # Gigabyte
            ("MB", 2**20),  # Megabyte
            ("KB", 2**10),  # Kilobyte
            ("B", 1),       # Byte
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

    def on_path_enter(self, ):
        try:
            self.chdir(dpg.get_value(self.tag+"ex_path_input"))
        except FileNotFoundError:
            self.message_box("Invalid path", "No such file or directory")

    def message_box(self, title, message):
        if not self.modal:
            with dpg.mutex():
                viewport_width = dpg.get_viewport_client_width()
                viewport_height = dpg.get_viewport_client_height()
                with dpg.window(label=title, no_close=True, modal=True) as modal_id:
                    dpg.add_text(message)
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Ok", width=-1, user_data=(modal_id,
                                       True), callback=lambda: dpg.delete_item(modal_id))

            dpg.split_frame()
            width = dpg.get_item_width(modal_id)
            height = dpg.get_item_height(modal_id)
            dpg.set_item_pos(
                modal_id, [viewport_width // 2 - width // 2, viewport_height // 2 - height // 2])
        else:
            print(
                f"DEV:ERROR:{title}:\t{message}\n\t\t\tCannot display message while file_dialog is in modal")

    def return_items(self):
        dpg.hide_item(self.tag)
        if self.callback is None:
            pass
        else:
            self.callback(self.selected_files)
        self.selected_files.clear()
        self.reset_dir(default_path=self.default_path)

    def open_drive(self, sender, app_data, user_data):
        self.chdir(user_data)

    def open_file(self, sender, app_data, user_data):
        # Multi selection, Allow only when multi_select is picked
        if dpg.is_key_down(dpg.mvKey_LControl) or dpg.is_key_down(dpg.mvKey_RControl):
            if self.multi_selection:
                if dpg.get_value(sender) is True:
                    self.selected_files.append(user_data[1])
                else:
                    self.selected_files.remove(user_data[1])
        # Single selection
        else:
            if len(self.selected_files) > 0:
                self.selected_files.clear()
                if self.last_clicked_element is not None:
                    dpg.set_value(self.last_clicked_element, False)
            dpg.set_value(sender, True)

            current_time = time.time()
            if user_data is not None and user_data[1] is not None:
                #Check if two click within 0.5s proximity
                if os.path.isdir(user_data[1]):
                    if (current_time - self.last_click_time < 0.5) and (self.last_clicked_element == sender): 
                        self.chdir(user_data[1])
                        self.last_clicked_element = None #Dir changed, so reset this variable
                        dpg.set_value(self.tag+"ex_search", "")
                    else:
                        self.last_click_time = current_time
                        self.last_clicked_element = sender
                        
                    if (self.dirs_only == True): #If dirs_only == True, we now allow user to select directory then press "OK"
                        self.selected_files = [user_data[1]]
                    
                elif os.path.isfile(user_data[1]):
                    if not len(self.selected_files) > 1:
                        self.selected_files.append(user_data[1])
                    #Check if two click within 0.5s proximity
                    if (current_time - self.last_click_time < 0.5) and (self.last_clicked_element == sender): 
                        self.return_items()
                    else:
                        self.last_click_time = current_time
                        self.last_clicked_element = sender
                    return user_data[1]

    def _search(self):
        res = dpg.get_value(self.tag+"ex_search")
        self.reset_dir(default_path=os.getcwd(), file_name_filter=res)

    def get_directory_path(self, directory_name):
        try:
            # Check for Linux or MacOS
            if platform.system() in ["Linux", "Darwin"] and directory_name.lower() == "home":
                directory_path = os.path.expanduser("~")
            # Check for Windows
            elif platform.system() == "Windows" and directory_name.lower() == "home":
                directory_path = os.path.expanduser("~")
            else:
                # Attempt to join the home directory with the specified directory name
                directory_path = os.path.join(
                    os.path.expanduser("~"), directory_name)

            # Verify if the directory exists
            os.listdir(directory_path)  # Test access
        except FileNotFoundError:
            # Search for the directory in the user's home folder
            search_path = os.path.expanduser("~/*/" + directory_name)
            directory_path = glob(search_path)
            if directory_path:
                try:
                    # Test access to the found path
                    os.listdir(directory_path[0])
                    # Use the found path
                    directory_path = directory_path[0]
                except FileNotFoundError:
                    self.message_box("File dialog - Error",
                                "Could not find the selected directory")
                    return "."
            else:
                self.message_box("File dialog - Error",
                            "Could not find the selected directory")
                return "."
        except Exception as e:
            return None

        return directory_path

    def _is_hidden(self, filepath):
        name = os.path.basename(os.path.abspath(filepath))
        return name.startswith('.') or (os.name == 'nt' and self._has_hidden_attribute(filepath))

    def _has_hidden_attribute(self, filepath):
        try:
            import ctypes
            FILE_ATTRIBUTE_HIDDEN = 0x2
            attrs = ctypes.windll.kernel32.GetFileAttributesW(
                str(filepath))
            return FILE_ATTRIBUTE_HIDDEN & attrs
        except:
            return False

    def _makedir(self, item, callback, parent=None, size=False):
        if parent is None:
            parent = self.tag + "explorer"
        file_name = os.path.basename(item)

        creation_time = os.path.getctime(item)
        creation_time = time.ctime(creation_time)

        item_type = "Dir"

        item_size = self.get_file_size(item)

        kwargs_cell = {'callback': callback, 'span_columns': True, 'height': self.selec_height, 'user_data': [
            file_name, os.path.join(os.getcwd(), file_name)]}
        kwargs_file = {'tint_color': [255, 255, 255, 255]}
        with dpg.table_row(parent=parent):
            with dpg.group(horizontal=True):
                if item_type == "Dir":

                    if self._is_hidden(file_name):
                        kwargs_file = {'tint_color': [
                            255, 255, 255, self.image_transparency]}
                    else:

                        kwargs_file = {'tint_color': [255, 255, 255, 255]}

                    dpg.add_image(self.img_mini_folder, **kwargs_file)
                elif item_type == "File":
                    dpg.add_image(self.img_mini_document, **kwargs_file)

                cell_name = dpg.add_selectable(
                    label=file_name, **kwargs_cell)
            cell_time = dpg.add_selectable(
                label=creation_time, **kwargs_cell)
            cell_type = dpg.add_selectable(label=item_type, **kwargs_cell)
            cell_size = dpg.add_selectable(
                label=str(item_size), **kwargs_cell)

            if self.allow_drag is True:
                drag_payload = dpg.add_drag_payload(
                    parent=cell_name, payload_type=self.PAYLOAD_TYPE)
            dpg.bind_item_theme(cell_name, self.selec_alignt)
            dpg.bind_item_theme(cell_time, self.selec_alignt)
            dpg.bind_item_theme(cell_type, self.selec_alignt)
            dpg.bind_item_theme(cell_size, self.size_alignt)
            if self.allow_drag is True:
                if file_name.endswith((".png", ".jpg")):
                    dpg.add_image(self.img_big_picture,
                                  parent=drag_payload)
                elif item_type == "Dir":
                    dpg.add_image(self.img_folder, parent=drag_payload)
                elif item_type == "File":
                    dpg.add_image(self.img_document, parent=drag_payload)

    def _makefile(self, item, callback, parent=None):
        if parent is None:
            parent = self.tag+"explorer"
        if self.file_filter == ".*" or item.endswith(self.file_filter):
            file_name = os.path.basename(item)

            creation_time = os.path.getctime(item)
            creation_time = time.ctime(creation_time)

            item_type = "File"

            item_size = self.get_file_size(item)
            kwargs_cell = {'callback': callback, 'span_columns': True, 'height': self.selec_height, 'user_data': [
                file_name, os.path.join(os.getcwd(), file_name)]}
            kwargs_file = {'tint_color': [
                255, 255, 255, self.image_transparency]}
            with dpg.table_row(parent=parent):
                with dpg.group(horizontal=True):

                    if item_type == "Dir":
                        dpg.add_image(self.img_mini_folder, **kwargs_file)
                    elif item_type == "File":

                        if self._is_hidden(file_name):
                            kwargs_file = {'tint_color': [
                                255, 255, 255, self.image_transparency]}
                        else:
                            kwargs_file = {
                                'tint_color': [255, 255, 255, 255]}

                        if file_name.endswith((".dll", ".a", ".o", ".so", ".ko")):
                            dpg.add_image(self.img_gears, **kwargs_file)

                        elif file_name.endswith((".png", ".jpg", ".jpeg")):
                            dpg.add_image(self.img_picture, **kwargs_file)

                        elif file_name.endswith((".msi", ".exe", ".bat", ".bin", ".elf")):
                            dpg.add_image(self.img_app, **kwargs_file)

                        elif file_name.endswith(".iso"):
                            dpg.add_image(self.img_iso, **kwargs_file)

                        elif file_name.endswith((".zip", ".deb", ".rpm", ".tar.gz", ".tar", ".gz", ".lzo", ".lz4", ".7z", ".ppack")):
                            dpg.add_image(self.img_zip, **kwargs_file)

                        elif file_name.endswith((".png", ".jpg", ".jpeg")):
                            dpg.add_image(self.img_picture, **kwargs_file)

                        elif file_name.endswith((".py", ".pyo", ".pyw", ".pyi", ".pyc", ".pyz", ".pyd")):
                            dpg.add_image(self.img_python, **kwargs_file)

                        elif file_name.endswith(".c"):
                            dpg.add_image(self.img_c, **kwargs_file)
                        elif file_name.endswith((".js", ".json", ".cs", ".cpp", ".h", ".hpp", ".sh", ".pyl", ".rs", ".vbs", ".cmd")):
                            dpg.add_image(self.img_script, **kwargs_file)

                        elif file_name.endswith(".url"):
                            dpg.add_image(self.img_url, **kwargs_file)
                        elif file_name.endswith(".lnk"):
                            dpg.add_image(self.img_link, **kwargs_file)

                        elif file_name.endswith(".txt"):
                            dpg.add_image(self.img_note, **kwargs_file)
                        elif file_name.endswith((".mp3", ".ogg", ".wav")):
                            dpg.add_image(
                                self.img_music_note, **kwargs_file)

                        elif file_name.endswith((".mp4", ".mov")):
                            dpg.add_image(self.img_video, **kwargs_file)

                        elif file_name.endswith((".obj", ".fbx", ".blend")):
                            dpg.add_image(self.img_object, **kwargs_file)

                        elif file_name.endswith(".svg"):
                            dpg.add_image(self.img_vector, **kwargs_file)

                        else:
                            dpg.add_image(
                                self.img_mini_document, **kwargs_file)

                    cell_name = dpg.add_selectable(
                        label=file_name, **kwargs_cell)
                cell_time = dpg.add_selectable(
                    label=creation_time, **kwargs_cell)
                cell_type = dpg.add_selectable(
                    label=item_type, **kwargs_cell)
                cell_size = dpg.add_selectable(
                    label=str(item_size), **kwargs_cell)

                if self.allow_drag is True:
                    drag_payload = dpg.add_drag_payload(
                        parent=cell_name, payload_type=self.PAYLOAD_TYPE)
                dpg.bind_item_theme(cell_name, self.selec_alignt)
                dpg.bind_item_theme(cell_time, self.selec_alignt)
                dpg.bind_item_theme(cell_type, self.selec_alignt)
                dpg.bind_item_theme(cell_size, self.size_alignt)
                if self.allow_drag is True:
                    if file_name.endswith((".png", ".jpg")):
                        dpg.add_image(self.img_big_picture,
                                      parent=drag_payload)
                    elif item_type == "Dir":
                        dpg.add_image(self.img_folder, parent=drag_payload)
                    elif item_type == "File":
                        dpg.add_image(self.img_document,
                                      parent=drag_payload)

    def _back(self, sender, app_data, user_data):
        if dpg.is_key_down(dpg.mvKey_LControl) or dpg.is_key_down(dpg.mvKey_RControl):
            dpg.set_value(sender, False)
        else:
            dpg.set_value(sender, False)
            current_time = time.time()
            if current_time - self.last_click_time < 0.5 and self.last_clicked_element == sender:
                dpg.set_value(self.tag+"ex_search", "")
                self.chdir("..")
                self.last_click_time = 0
            self.last_click_time = current_time
            self.last_clicked_element = sender

    def filter_combo_selector(self, sender, app_data):
        filter_file = dpg.get_value(sender)
        self.file_filter = filter_file
        cwd = os.getcwd()
        self.reset_dir(default_path=cwd)

    def chdir(self, path):
        try:
            os.chdir(path)
            cwd = os.getcwd()
            self.reset_dir(default_path=cwd)
        except PermissionError as e:
            self.message_box("File dialog - PerimssionError",
                        f"Cannot open the folder because is a system folder or the access is denied\n\nMore info:\n{e}")
        except NotADirectoryError as e:
            self.message_box("File dialog - not a directory",
                        f"The selected item is not a directory, but a file.\n\nMore info:\n{e}")

    def reset_dir(self, file_name_filter=None, default_path=None):
        if default_path is None:
            default_path = self.default_path
        def internal():
            self.selected_files.clear()
            try:
                dpg.configure_item(
                    self.tag+"ex_path_input", default_value=os.getcwd())
                _dir = os.listdir(default_path)
                self.delete_table()

                # Separate directories and files
                dirs = [file for file in _dir if os.path.isdir(file)]
                files = [file for file in _dir if os.path.isfile(file)]

                # 'special directory' that sends back to the prevorius directory
                with dpg.table_row(parent=self.tag+"explorer"):
                    dpg.add_selectable(
                        label="..", callback=self._back, span_columns=True, height=self.selec_height)

                    # dir list
                    for _dir in dirs:
                        if not self._is_hidden(_dir):
                            if file_name_filter:
                                if dpg.get_value(self.tag+"ex_search") in _dir:
                                    self._makedir(_dir, self.open_file)
                            else:
                                self._makedir(_dir, self.open_file)
                        elif self._is_hidden(_dir) and self.show_hidden_files:
                            if file_name_filter:
                                if dpg.get_value(self.tag+"ex_search") in _dir:
                                    self._makedir(_dir, self.open_file)
                            else:
                                self._makedir(_dir, self.open_file)

                    # file list
                    if not self.dirs_only:
                        for file in files:
                            if not self._is_hidden(file):
                                if file_name_filter:
                                    if dpg.get_value(self.tag+"ex_search") in file:
                                        self._makefile(file, self.open_file)
                                else:
                                    self._makefile(file, self.open_file)
                            elif self._is_hidden(file) and self.show_hidden_files:
                                if file_name_filter:
                                    if dpg.get_value(self.tag+"ex_search") in file:
                                        self._makefile(file, self.open_file)
                                else:
                                    self._makefile(file, self.open_file)

            # exceptions
            except FileNotFoundError:
                print("DEV:ERROR: Invalid path : "+str(default_path))
            except Exception as e:
                #Catch all exception, so should at least print it out
                import traceback
                traceback.print_exception (type (e), e, e.__traceback__)
                self.message_box(
                    "File dialog - Error", f"An unknown error has occured when listing the items, More info:\n{e}")

        internal()
    def __init__(
        self,
        title="File dialog",
        tag="file_dialog",
        width=950,
        height=650,
        min_size=(460, 320),
        dirs_only=False,
        default_path=os.getcwd(),
        filter_list=[".*", ".exe", ".bat", ".sh", ".msi", ".apk", ".bin", ".cmd", ".com", ".jar", ".out", ".py", ".pyl", ".phs", ".js", ".json", ".java", ".c", ".cpp", ".cs", ".h", ".rs", ".vbs", ".php", ".pl", ".rb", ".go", ".swift", ".ts", ".asm", ".lua", ".sh", ".bat", ".r", ".dart", ".ps1", ".html", ".htm", ".xml", ".css", ".ini", ".yaml", ".yml", ".config", ".md", ".rst", ".txt", ".rtf", ".doc", ".docx", ".pdf", ".odt", ".tex", ".log", ".csv", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".svg", ".webp", ".ico", ".psd", ".ai", ".eps", ".tga", ".wav",
                     ".mp3", ".ogg", ".flac", ".aac", ".m4a", ".wma", ".aiff", ".mid", ".midi", ".opus", ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".mpeg", ".mpg", ".3gp", ".m4v", ".blend", ".fbx", ".obj", ".stl", ".3ds", ".dae", ".ply", ".glb", ".gltf", ".csv", ".sql", ".db", ".dbf", ".mdb", ".accdb", ".sqlite", ".xml", ".json", ".zip", ".rar", ".7z", ".tar", ".gz", ".iso", ".bz2", ".xz", ".tgz", ".cab", ".vdi", ".vmdk", ".vhd", ".vhdx", ".ova", ".ovf", ".qcow2", ".dockerfile", ".bak", ".old", ".sav", ".tmp", ".bk", ".ppack", ".mlt", ".torrent", ".ics"],
        file_filter=".*",
        callback=None,
        show_dir_size=False,
        allow_drag=True,
        multi_selection=True,
        show_shortcuts_menu=True,
        no_resize=True,
        modal=True,
        show_hidden_files=False,
        user_style=0
    ):
        #global self.chdir

        # args
        self.title = title
        self.tag = tag
        self.width = width
        self.height = height
        self.min_size = min_size
        self.dirs_only = dirs_only
        self.default_path = default_path
        self.filter_list = filter_list
        self.file_filter = file_filter
        self.callback = callback
        self.show_dir_size = show_dir_size
        self.allow_drag = allow_drag
        self.multi_selection = multi_selection
        self.show_shortcuts_menu = show_shortcuts_menu
        self.no_resize = no_resize
        self.modal = modal
        self.show_hidden_files = show_hidden_files
        self.user_style = user_style

        self.PAYLOAD_TYPE = 'ws_' + self.tag
        self.selected_files = []
        self.selec_height = 16
        self.image_transparency = 100
        self.last_click_time = 0
        self.last_clicked_element = None

        self.fd_img_path = os.path.join(os.path.dirname(__file__), "images")

        # file dialog theme

        with dpg.theme() as self.selec_alignt:
            with dpg.theme_component(dpg.mvThemeCat_Core):
                dpg.add_theme_style(
                    dpg.mvStyleVar_SelectableTextAlign, x=0, y=.5)

        with dpg.theme() as self.size_alignt:
            with dpg.theme_component(dpg.mvThemeCat_Core):
                dpg.add_theme_style(
                    dpg.mvStyleVar_SelectableTextAlign, x=1, y=.5)

        # texture loading
        diwidth, diheight, _, didata = dpg.load_image(
            os.path.join(self.fd_img_path, "document.png"))
        hwidth, hheight, _, hdata = dpg.load_image(
            os.path.join(self.fd_img_path, "home.png"))
        afiwidth, afiheight, _, afidata = dpg.load_image(
            os.path.join(self.fd_img_path, "add_folder.png"))
        afwidth, afheight, _, afdata = dpg.load_image(
            os.path.join(self.fd_img_path, "add_file.png"))
        mfwidth, mfheight, _, mfdata = dpg.load_image(
            os.path.join(self.fd_img_path, "mini_folder.png"))
        fiwidth, fiheight, _, fidata = dpg.load_image(
            os.path.join(self.fd_img_path, "folder.png"))
        mdwidth, mdheight, _, mddata = dpg.load_image(
            os.path.join(self.fd_img_path, "mini_document.png"))
        mewidth, meheight, _, medata = dpg.load_image(
            os.path.join(self.fd_img_path, "mini_error.png"))
        rwidth, rheight, _, rdata = dpg.load_image(
            os.path.join(self.fd_img_path, "refresh.png"))
        hdwidth, hdheight, _, hddata = dpg.load_image(
            os.path.join(self.fd_img_path, "hd.png"))
        pwidth, pheight, _, pdata = dpg.load_image(
            os.path.join(self.fd_img_path, "picture.png"))
        bpwidth, bpheight, _, bpdata = dpg.load_image(
            os.path.join(self.fd_img_path, "big_picture.png"))
        pfwidth, pfheight, _, pfdata = dpg.load_image(
            os.path.join(self.fd_img_path, "picture_folder.png"))
        dwidth, dheight, _, ddata = dpg.load_image(
            os.path.join(self.fd_img_path, "desktop.png"))
        vwidth, vheight, _, vdata = dpg.load_image(
            os.path.join(self.fd_img_path, "videos.png"))
        mwidth, mheight, _, mdata = dpg.load_image(
            os.path.join(self.fd_img_path, "music.png"))
        dfwidth, dfheight, _, dfdata = dpg.load_image(
            os.path.join(self.fd_img_path, "downloads.png"))
        dcfwidth, dcfheight, _, dcfdata = dpg.load_image(
            os.path.join(self.fd_img_path, "documents.png"))
        swidth, sheight, _, sdata = dpg.load_image(
            os.path.join(self.fd_img_path, "search.png"))
        bwidth, bheight, _, bdata = dpg.load_image(
            os.path.join(self.fd_img_path, "back.png"))
        cwidth, cheight, _, cdata = dpg.load_image(
            os.path.join(self.fd_img_path, "c.png"))
        gwidth, gheight, _, gdata = dpg.load_image(
            os.path.join(self.fd_img_path, "gears.png"))
        mnwidth, mnheight, _, mndata = dpg.load_image(
            os.path.join(self.fd_img_path, "music_note.png"))
        nwidth, nheight, _, ndata = dpg.load_image(
            os.path.join(self.fd_img_path, "note.png"))
        owidth, oheight, _, odata = dpg.load_image(
            os.path.join(self.fd_img_path, "object.png"))
        pywidth, pyheight, _, pydata = dpg.load_image(
            os.path.join(self.fd_img_path, "python.png"))
        scwidth, scheight, _, scdata = dpg.load_image(
            os.path.join(self.fd_img_path, "script.png"))
        vfwidth, vfheight, _, vfdata = dpg.load_image(
            os.path.join(self.fd_img_path, "video.png"))
        lwidth, lheight, _, ldata = dpg.load_image(
            os.path.join(self.fd_img_path, "link.png"))
        uwidth, uheight, _, udata = dpg.load_image(
            os.path.join(self.fd_img_path, "url.png"))
        vewidth, veheight, _, vedata = dpg.load_image(
            os.path.join(self.fd_img_path, "vector.png"))
        zwidth, zheight, _, zdata = dpg.load_image(
            os.path.join(self.fd_img_path, "zip.png"))
        awidth, aheight, _, adata = dpg.load_image(
            os.path.join(self.fd_img_path, "app.png"))
        iwidth, iheight, _, idata = dpg.load_image(
            os.path.join(self.fd_img_path, "iso.png"))

        # low-level
        self.ico_document = [diwidth, diheight, didata]
        self.ico_home = [hwidth, hheight, hdata]
        self.ico_add_folder = [afiwidth, afiheight, afidata]
        self.ico_add_file = [afwidth, afheight, afdata]
        self.ico_mini_folder = [mfwidth, mfheight, mfdata]
        self.ico_folder = [fiwidth, fiheight, fidata]
        self.ico_mini_document = [mdwidth, mdheight, mddata]
        self.ico_mini_error = [mewidth, meheight, medata]
        self.ico_refresh = [rwidth, rheight, rdata]
        self.ico_hard_disk = [hdwidth, hdheight, hddata]
        self.ico_picture = [pwidth, pheight, pdata]
        self.ico_big_picture = [bpwidth, bpheight, bpdata]
        self.ico_picture_folder = [pfwidth, pfheight, pfdata]
        self.ico_desktop = [dwidth, dheight, ddata]
        self.ico_videos = [vwidth, vheight, vdata]
        self.ico_music_folder = [mwidth, mheight, mdata]
        self.ico_downloads = [dfwidth, dfheight, dfdata]
        self.ico_document_folder = [dcfwidth, dcfheight, dcfdata]
        self.ico_search = [swidth, sheight, sdata]
        self.ico_back = [bwidth, bheight, bdata]
        self.ico_c = [cwidth, cheight, cdata]
        self.ico_gears = [gwidth, gheight, gdata]
        self.ico_music_note = [mnwidth, mnheight, mndata]
        self.ico_note = [nwidth, nheight, ndata]
        self.ico_object = [owidth, oheight, odata]
        self.ico_python = [pywidth, pyheight, pydata]
        self.ico_script = [scwidth, scheight, scdata]
        self.ico_video = [vfwidth, vfheight, vfdata]
        self.ico_link = [lwidth, lheight, ldata]
        self.ico_url = [uwidth, uheight, udata]
        self.ico_vector = [vewidth, veheight, vedata]
        self.ico_zip = [zwidth, zheight, zdata]
        self.ico_app = [awidth, aheight, adata]
        self.ico_iso = [iwidth, iheight, idata]

        # high-level
        with dpg.texture_registry():
            dpg.add_static_texture(
                width=self.ico_document[0], height=self.ico_document[1], default_value=self.ico_document[2], tag=self.tag+"ico_document")
            dpg.add_static_texture(
                width=self.ico_home[0], height=self.ico_home[1], default_value=self.ico_home[2], tag=self.tag+"ico_home")
            dpg.add_static_texture(
                width=self.ico_add_folder[0], height=self.ico_add_folder[1], default_value=self.ico_add_folder[2], tag=self.tag+"ico_add_folder")
            dpg.add_static_texture(
                width=self.ico_add_file[0], height=self.ico_add_file[1], default_value=self.ico_add_file[2], tag=self.tag+"ico_add_file")
            dpg.add_static_texture(
                width=self.ico_mini_folder[0], height=self.ico_mini_folder[1], default_value=self.ico_mini_folder[2], tag=self.tag+"ico_mini_folder")
            dpg.add_static_texture(
                width=self.ico_folder[0], height=self.ico_folder[1], default_value=self.ico_folder[2], tag=self.tag+"ico_folder")
            dpg.add_static_texture(width=self.ico_mini_document[0], height=self.ico_mini_document[1],
                                   default_value=self.ico_mini_document[2], tag=self.tag+"ico_mini_document")
            dpg.add_static_texture(
                width=self.ico_mini_error[0], height=self.ico_mini_error[1], default_value=self.ico_mini_error[2], tag=self.tag+"ico_mini_error")
            dpg.add_static_texture(
                width=self.ico_refresh[0], height=self.ico_refresh[1], default_value=self.ico_refresh[2], tag=self.tag+"ico_refresh")
            dpg.add_static_texture(
                width=self.ico_hard_disk[0], height=self.ico_hard_disk[1], default_value=self.ico_hard_disk[2], tag=self.tag+"ico_hard_disk")
            dpg.add_static_texture(
                width=self.ico_picture[0], height=self.ico_picture[1], default_value=self.ico_picture[2], tag=self.tag+"ico_picture")
            dpg.add_static_texture(
                width=self.ico_big_picture[0], height=self.ico_big_picture[1], default_value=self.ico_big_picture[2], tag=self.tag+"ico_big_picture")
            dpg.add_static_texture(width=self.ico_picture_folder[0], height=self.ico_picture_folder[1],
                                   default_value=self.ico_picture_folder[2], tag=self.tag+"ico_picture_folder")
            dpg.add_static_texture(
                width=self.ico_desktop[0], height=self.ico_desktop[1], default_value=self.ico_desktop[2], tag=self.tag+"ico_desktop")
            dpg.add_static_texture(
                width=self.ico_videos[0], height=self.ico_videos[1], default_value=self.ico_videos[2], tag=self.tag+"ico_videos")
            dpg.add_static_texture(
                width=self.ico_music_folder[0], height=self.ico_music_folder[1], default_value=self.ico_music_folder[2], tag=self.tag+"ico_music_folder")
            dpg.add_static_texture(
                width=self.ico_downloads[0], height=self.ico_downloads[1], default_value=self.ico_downloads[2], tag=self.tag+"ico_downloads")
            dpg.add_static_texture(width=self.ico_document_folder[0], height=self.ico_document_folder[1],
                                   default_value=self.ico_document_folder[2], tag=self.tag+"ico_document_folder")
            dpg.add_static_texture(
                width=self.ico_search[0], height=self.ico_search[1], default_value=self.ico_search[2], tag=self.tag+"ico_search")
            dpg.add_static_texture(
                width=self.ico_back[0], height=self.ico_back[1], default_value=self.ico_back[2], tag=self.tag+"ico_back")
            dpg.add_static_texture(
                width=self.ico_c[0], height=self.ico_c[1], default_value=self.ico_c[2], tag=self.tag+"ico_c")
            dpg.add_static_texture(
                width=self.ico_gears[0], height=self.ico_gears[1], default_value=self.ico_gears[2], tag=self.tag+"ico_gears")
            dpg.add_static_texture(
                width=self.ico_music_note[0], height=self.ico_music_note[1], default_value=self.ico_music_note[2], tag=self.tag+"ico_music_note")
            dpg.add_static_texture(
                width=self.ico_note[0], height=self.ico_note[1], default_value=self.ico_note[2], tag=self.tag+"ico_note")
            dpg.add_static_texture(
                width=self.ico_object[0], height=self.ico_object[1], default_value=self.ico_object[2], tag=self.tag+"ico_object")
            dpg.add_static_texture(
                width=self.ico_python[0], height=self.ico_python[1], default_value=self.ico_python[2], tag=self.tag+"ico_python")
            dpg.add_static_texture(
                width=self.ico_script[0], height=self.ico_script[1], default_value=self.ico_script[2], tag=self.tag+"ico_script")
            dpg.add_static_texture(
                width=self.ico_video[0], height=self.ico_video[1], default_value=self.ico_video[2], tag=self.tag+"ico_video")
            dpg.add_static_texture(
                width=self.ico_link[0], height=self.ico_link[1], default_value=self.ico_link[2], tag=self.tag+"ico_link")
            dpg.add_static_texture(
                width=self.ico_url[0], height=self.ico_url[1], default_value=self.ico_url[2], tag=self.tag+"ico_url")
            dpg.add_static_texture(
                width=self.ico_vector[0], height=self.ico_vector[1], default_value=self.ico_vector[2], tag=self.tag+"ico_vector")
            dpg.add_static_texture(
                width=self.ico_zip[0], height=self.ico_zip[1], default_value=self.ico_zip[2], tag=self.tag+"ico_zip")
            dpg.add_static_texture(
                width=self.ico_app[0], height=self.ico_app[1], default_value=self.ico_app[2], tag=self.tag+"ico_app")
            dpg.add_static_texture(
                width=self.ico_iso[0], height=self.ico_iso[1], default_value=self.ico_iso[2], tag=self.tag+"ico_iso")
            
            self.img_document= self.tag + "ico_document"
            self.img_home= self.tag + "ico_home"
            self.img_add_folder= self.tag + "ico_add_folder"
            self.img_add_file= self.tag + "ico_add_file"
            self.img_mini_folder= self.tag + "ico_mini_folder"
            self.img_folder= self.tag + "ico_folder"
            self.img_mini_document= self.tag + "ico_mini_document"
            self.img_mini_error= self.tag + "ico_mini_error"
            self.img_refresh= self.tag + "ico_refresh"
            self.img_hard_disk= self.tag + "ico_hard_disk"
            self.img_picture= self.tag + "ico_picture"
            self.img_big_picture= self.tag + "ico_big_picture"
            self.img_picture_folder= self.tag + "ico_picture_folder"
            self.img_desktop= self.tag + "ico_desktop"
            self.img_videos= self.tag + "ico_videos"
            self.img_music_folder= self.tag + "ico_music_folder"
            self.img_downloads= self.tag + "ico_downloads"
            self.img_document_folder= self.tag + "ico_document_folder"
            self.img_search= self.tag + "ico_search"
            self.img_back= self.tag + "ico_back"
            self.img_c= self.tag + "ico_c"
            self.img_gears= self.tag + "ico_gears"
            self.img_music_note= self.tag + "ico_music_note"
            self.img_note= self.tag + "ico_note"
            self.img_object= self.tag + "ico_object"
            self.img_python= self.tag + "ico_python"
            self.img_script= self.tag + "ico_script"
            self.img_video= self.tag + "ico_video"
            self.img_link = self.tag+"ico_link"
            self.img_url = self.tag+"ico_url"
            self.img_vector = self.tag+"ico_vector"
            self.img_zip = self.tag+"ico_zip"
            self.img_app = self.tag+"ico_app"
            self.img_iso = self.tag+"ico_iso"
        

        """ def explorer_order(sender, user_data):
            thingforsort = dpg.get_item_children(sender, 0).index(user_data[0][0])
            print(thingforsort)
            if (thingforsort == 0): # name
                reset_dir(os.getcwd(), witem="name", order=user_data[0][1])
            elif (thingforsort == 1): # date
                reset_dir(os.getcwd(), witem="date", order=user_data[0][1])
            elif (thingforsort == 3): # size
                reset_dir(os.getcwd(), witem="size", order=user_data[0][1])
         """

        # main file dialog header
        with dpg.window(label="File dialog", tag=self.tag, no_resize=self.no_resize, show=False, modal=self.modal, width=self.width, height=self.height, min_size=self.min_size, no_collapse=True, pos=(50, 50)):
            info_px = 50

            # horizontal group (shot_menu + dir_list)
            with dpg.group(horizontal=True):
                # shortcut menu
                if (self.user_style == 0):
                    with dpg.child_window(tag=self.tag+"shortcut_menu", width=200, resizable_x=True, show=self.show_shortcuts_menu, height=-info_px):
                        home = self.get_directory_path("Home")
                        desktop = self.get_directory_path("Desktop")
                        downloads = self.get_directory_path("Downloads")
                        images = self.get_directory_path("Pictures")
                        documents = self.get_directory_path("Documents")
                        musics = self.get_directory_path("Music")
                        videos = self.get_directory_path("Videos")

                        def _add_shortcut(icon, path, label):
                            if path is not None or os.path.exists(path):
                                with dpg.group(horizontal=True):
                                    dpg.add_image(icon)
                                    dpg.add_menu_item(label=label, callback=lambda p=path: self.chdir(p))

                        _add_shortcut(self.img_home, home, "Home")
                        _add_shortcut(self.img_desktop, desktop, "Desktop")
                        _add_shortcut(self.img_downloads, downloads, "Downloads")
                        _add_shortcut(self.img_picture_folder, images, "Images")
                        _add_shortcut(self.img_document_folder, documents, "Documents")
                        _add_shortcut(self.img_music_folder, musics, "Musics")
                        _add_shortcut(self.img_videos, videos, "Videos")

                        dpg.add_separator()

                        # i/e drives list
                        with dpg.group():
                            drives = self._get_all_drives()
                            for drive in drives:
                                with dpg.group(horizontal=True):
                                    dpg.add_image(self.img_hard_disk)
                                    dpg.add_menu_item(
                                        label=drive, user_data=drive, callback=self.open_drive)

                elif (self.user_style == 1):
                    with dpg.child_window(tag=self.tag+"shortcut_menu", width=40, show=self.show_shortcuts_menu, height=-info_px):
                        home = self.get_directory_path("Home")
                        desktop = self.get_directory_path("Desktop")
                        downloads = self.get_directory_path("Downloads")
                        images = self.get_directory_path("Pictures")
                        documents = self.get_directory_path("Documents")
                        musics = self.get_directory_path("Music")
                        videos = self.get_directory_path("Videos")

                        dpg.add_image_button(
                            self.img_home, callback=lambda: self.chdir(home))
                        dpg.add_image_button(
                            self.img_desktop, callback=lambda: self.chdir(desktop))
                        dpg.add_image_button(
                            self.img_downloads, callback=lambda: self.chdir(downloads))
                        dpg.add_image_button(
                            self.img_picture_folder, callback=lambda: self.chdir(images))
                        dpg.add_image_button(
                            self.img_document_folder, callback=lambda: self.chdir(documents))
                        dpg.add_image_button(
                            self.img_music_folder, callback=lambda: self.chdir(musics))
                        dpg.add_image_button(
                            self.img_videos, callback=lambda: self.chdir(videos))

                        dpg.add_separator()

                        with dpg.group():
                            drives = self._get_all_drives()
                            for drive in drives:
                                dpg.add_image_button(
                                    texture_tag=self.img_hard_disk, label=drive, user_data=drive, callback=self.open_drive)

                with dpg.child_window(height=-info_px):
                    # main explorer header
                    with dpg.group():

                        with dpg.group(horizontal=True):
                            dpg.add_image_button(
                                self.img_refresh, callback=lambda: self.reset_dir(default_path=os.getcwd()))
                            dpg.add_image_button(
                                self.img_back, callback=lambda: self.chdir(self.default_path))
                            dpg.add_input_text(hint="Path", on_enter=True, callback=self.on_path_enter,  default_value=os.getcwd(
                            ), width=-1, tag=self.tag+"ex_path_input")

                        with dpg.group(horizontal=True):
                            dpg.add_input_text(
                                hint="Search files", callback=self._search, tag=self.tag+"ex_search", width=-1)

                        # main explorer table header
                        with dpg.table(
                            tag=self.tag+"explorer",
                            height=-1,
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
                            dpg.add_table_column(
                                label='Name',     init_width_or_weight=iwow_name, tag=self.tag+"ex_name")
                            dpg.add_table_column(
                                label='Date',     init_width_or_weight=iwow_date, tag=self.tag+"ex_date")
                            dpg.add_table_column(
                                label='Type',     init_width_or_weight=iwow_type, tag=self.tag+"ex_type")
                            dpg.add_table_column(
                                label='Size',     init_width_or_weight=iwow_size, width=10, tag=self.tag+"ex_size")

            with dpg.group(horizontal=True):
                dpg.add_spacer(width=480)
                dpg.add_text('File type filter')
                dpg.add_combo(items=self.filter_list,
                              callback=self.filter_combo_selector, default_value=self.file_filter, width=-1)

            with dpg.group(horizontal=True) as btn_ret_grp:
                dpg.add_spacer(width=int(self.width*0.831))
                dpg.add_button(label="   OK   ", tag=self.tag + "_return", callback=self.return_items)
                dpg.add_button(label=" Cancel ",
                               callback=lambda: dpg.hide_item(self.tag))

            if self.default_path == "cwd":
                self.chdir(os.getcwd())
            else:
                self.chdir(self.default_path)

    # high-level functions
    def show_file_dialog(self):
        self.chdir(self.default_path)
        dpg.show_item(self.tag)

    def change_callback(self, callback):
        self.callback = callback
        dpg.configure_item(self.tag+"_return", callback=self.callback)
