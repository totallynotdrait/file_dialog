# file_dialog 3.2
# MIT licensed

from dataclasses import dataclass
from glob import glob
import os
import platform
import psutil
import time

import dearpygui.dearpygui as dpg


DEFAULT_FILTER_LIST = [
    ".*", ".exe", ".bat", ".sh", ".msi", ".apk", ".bin", ".cmd", ".com",
    ".jar", ".out", ".py", ".pyl", ".phs", ".js", ".json", ".java", ".c",
    ".cpp", ".cs", ".h", ".rs", ".vbs", ".php", ".pl", ".rb", ".go",
    ".swift", ".ts", ".asm", ".lua", ".sh", ".bat", ".r", ".dart", ".ps1",
    ".html", ".htm", ".xml", ".css", ".ini", ".yaml", ".yml", ".config",
    ".md", ".rst", ".txt", ".rtf", ".doc", ".docx", ".pdf", ".odt", ".tex",
    ".log", ".csv", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff",
    ".svg", ".webp", ".ico", ".psd", ".ai", ".eps", ".tga", ".wav", ".mp3",
    ".ogg", ".flac", ".aac", ".m4a", ".wma", ".aiff", ".mid", ".midi",
    ".opus", ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm",
    ".mpeg", ".mpg", ".3gp", ".m4v", ".blend", ".fbx", ".obj", ".stl",
    ".3ds", ".dae", ".ply", ".glb", ".gltf", ".csv", ".sql", ".db", ".dbf",
    ".mdb", ".accdb", ".sqlite", ".xml", ".json", ".zip", ".rar", ".7z",
    ".tar", ".gz", ".iso", ".bz2", ".xz", ".tgz", ".cab", ".vdi", ".vmdk",
    ".vhd", ".vhdx", ".ova", ".ovf", ".qcow2", ".dockerfile", ".bak", ".old",
    ".sav", ".tmp", ".bk", ".ppack", ".mlt", ".torrent", ".ics",
]


@dataclass
class _FileEntry:
    name: str
    path: str
    is_dir: bool
    hidden: bool
    timestamp: float
    display_date: str
    item_type: str
    size_bytes: int | None
    display_size: str


class _BaseFileDialog:
    def __init__(
        self,
        *,
        title="File dialog",
        tag="file_dialog",
        width=950,
        height=650,
        min_size=(460, 320),
        dirs_only=False,
        default_path=None,
        filter_list=None,
        file_filter=".*",
        callback=None,
        show_dir_size=False,
        allow_drag=True,
        multi_selection=True,
        show_shortcuts_menu=True,
        no_resize=True,
        modal=True,
        show_hidden_files=False,
        user_style=0,
        mode="open",
        confirm_label="OK",
        filename_placeholder="File name",
    ):
        self.title = title
        self.tag = tag
        self.width = width
        self.height = height
        self.min_size = min_size
        self.dirs_only = dirs_only
        self.default_path = self._normalize_directory(default_path)
        self.filter_list = list(filter_list or DEFAULT_FILTER_LIST)
        self.file_filter = file_filter
        self.callback = callback
        self.show_dir_size = show_dir_size
        self.allow_drag = allow_drag
        self.multi_selection = multi_selection if mode == "open" else False
        self.show_shortcuts_menu = show_shortcuts_menu
        self.no_resize = no_resize
        self.modal = modal
        self.show_hidden_files = show_hidden_files
        self.user_style = user_style
        self.mode = mode
        self.confirm_label = confirm_label
        self.filename_placeholder = filename_placeholder

        self.PAYLOAD_TYPE = "ws_" + self.tag
        self.selec_height = 16
        self.image_transparency = 100
        self.last_click_time = 0.0
        self.last_clicked_path = None
        self.last_back_click_time = 0.0
        self.last_back_widget = None

        self.current_path = self.default_path
        self.search_query = ""
        self.sort_column = "name"
        self.sort_ascending = True
        self.entries = []
        self.entry_rows = {}
        self.entry_lookup = {}
        self.selected_files = []
        self.current_filename = ""
        self.pending_save_path = None

        self.fd_img_path = os.path.join(os.path.dirname(__file__), "images")

        self._build_themes()
        self._load_textures()
        self._build_window()
        self.refresh_entries()
        self._update_action_button_state()

    def _normalize_directory(self, path):
        if path in (None, "cwd"):
            return os.getcwd()

        normalized = os.path.abspath(path)
        return normalized if os.path.isdir(normalized) else os.getcwd()

    def _normalize_target_path(self, path):
        if path is None:
            return None
        if path == "..":
            return os.path.abspath(os.path.join(self.current_path, ".."))
        if os.path.isabs(path):
            return os.path.abspath(path)
        return os.path.abspath(os.path.join(self.current_path, path))

    def _build_themes(self):
        with dpg.theme() as self.selec_alignt:
            with dpg.theme_component(dpg.mvThemeCat_Core):
                dpg.add_theme_style(
                    dpg.mvStyleVar_SelectableTextAlign, x=0, y=0.5
                )

        with dpg.theme() as self.size_alignt:
            with dpg.theme_component(dpg.mvThemeCat_Core):
                dpg.add_theme_style(
                    dpg.mvStyleVar_SelectableTextAlign, x=1, y=0.5
                )

    def _load_textures(self):
        diwidth, diheight, _, didata = dpg.load_image(
            os.path.join(self.fd_img_path, "document.png")
        )
        hwidth, hheight, _, hdata = dpg.load_image(
            os.path.join(self.fd_img_path, "home.png")
        )
        afiwidth, afiheight, _, afidata = dpg.load_image(
            os.path.join(self.fd_img_path, "add_folder.png")
        )
        afwidth, afheight, _, afdata = dpg.load_image(
            os.path.join(self.fd_img_path, "add_file.png")
        )
        mfwidth, mfheight, _, mfdata = dpg.load_image(
            os.path.join(self.fd_img_path, "mini_folder.png")
        )
        fiwidth, fiheight, _, fidata = dpg.load_image(
            os.path.join(self.fd_img_path, "folder.png")
        )
        mdwidth, mdheight, _, mddata = dpg.load_image(
            os.path.join(self.fd_img_path, "mini_document.png")
        )
        mewidth, meheight, _, medata = dpg.load_image(
            os.path.join(self.fd_img_path, "mini_error.png")
        )
        rwidth, rheight, _, rdata = dpg.load_image(
            os.path.join(self.fd_img_path, "refresh.png")
        )
        hdwidth, hdheight, _, hddata = dpg.load_image(
            os.path.join(self.fd_img_path, "hd.png")
        )
        pwidth, pheight, _, pdata = dpg.load_image(
            os.path.join(self.fd_img_path, "picture.png")
        )
        bpwidth, bpheight, _, bpdata = dpg.load_image(
            os.path.join(self.fd_img_path, "big_picture.png")
        )
        pfwidth, pfheight, _, pfdata = dpg.load_image(
            os.path.join(self.fd_img_path, "picture_folder.png")
        )
        dwidth, dheight, _, ddata = dpg.load_image(
            os.path.join(self.fd_img_path, "desktop.png")
        )
        vwidth, vheight, _, vdata = dpg.load_image(
            os.path.join(self.fd_img_path, "videos.png")
        )
        mwidth, mheight, _, mdata = dpg.load_image(
            os.path.join(self.fd_img_path, "music.png")
        )
        dfwidth, dfheight, _, dfdata = dpg.load_image(
            os.path.join(self.fd_img_path, "downloads.png")
        )
        dcfwidth, dcfheight, _, dcfdata = dpg.load_image(
            os.path.join(self.fd_img_path, "documents.png")
        )
        swidth, sheight, _, sdata = dpg.load_image(
            os.path.join(self.fd_img_path, "search.png")
        )
        bwidth, bheight, _, bdata = dpg.load_image(
            os.path.join(self.fd_img_path, "back.png")
        )
        cwidth, cheight, _, cdata = dpg.load_image(
            os.path.join(self.fd_img_path, "c.png")
        )
        gwidth, gheight, _, gdata = dpg.load_image(
            os.path.join(self.fd_img_path, "gears.png")
        )
        mnwidth, mnheight, _, mndata = dpg.load_image(
            os.path.join(self.fd_img_path, "music_note.png")
        )
        nwidth, nheight, _, ndata = dpg.load_image(
            os.path.join(self.fd_img_path, "note.png")
        )
        owidth, oheight, _, odata = dpg.load_image(
            os.path.join(self.fd_img_path, "object.png")
        )
        pywidth, pyheight, _, pydata = dpg.load_image(
            os.path.join(self.fd_img_path, "python.png")
        )
        scwidth, scheight, _, scdata = dpg.load_image(
            os.path.join(self.fd_img_path, "script.png")
        )
        vfwidth, vfheight, _, vfdata = dpg.load_image(
            os.path.join(self.fd_img_path, "video.png")
        )
        lwidth, lheight, _, ldata = dpg.load_image(
            os.path.join(self.fd_img_path, "link.png")
        )
        uwidth, uheight, _, udata = dpg.load_image(
            os.path.join(self.fd_img_path, "url.png")
        )
        vewidth, veheight, _, vedata = dpg.load_image(
            os.path.join(self.fd_img_path, "vector.png")
        )
        zwidth, zheight, _, zdata = dpg.load_image(
            os.path.join(self.fd_img_path, "zip.png")
        )
        awidth, aheight, _, adata = dpg.load_image(
            os.path.join(self.fd_img_path, "app.png")
        )
        iwidth, iheight, _, idata = dpg.load_image(
            os.path.join(self.fd_img_path, "iso.png")
        )

        with dpg.texture_registry():
            dpg.add_static_texture(
                width=diwidth,
                height=diheight,
                default_value=didata,
                tag=self.tag + "ico_document",
            )
            dpg.add_static_texture(
                width=hwidth,
                height=hheight,
                default_value=hdata,
                tag=self.tag + "ico_home",
            )
            dpg.add_static_texture(
                width=afiwidth,
                height=afiheight,
                default_value=afidata,
                tag=self.tag + "ico_add_folder",
            )
            dpg.add_static_texture(
                width=afwidth,
                height=afheight,
                default_value=afdata,
                tag=self.tag + "ico_add_file",
            )
            dpg.add_static_texture(
                width=mfwidth,
                height=mfheight,
                default_value=mfdata,
                tag=self.tag + "ico_mini_folder",
            )
            dpg.add_static_texture(
                width=fiwidth,
                height=fiheight,
                default_value=fidata,
                tag=self.tag + "ico_folder",
            )
            dpg.add_static_texture(
                width=mdwidth,
                height=mdheight,
                default_value=mddata,
                tag=self.tag + "ico_mini_document",
            )
            dpg.add_static_texture(
                width=mewidth,
                height=meheight,
                default_value=medata,
                tag=self.tag + "ico_mini_error",
            )
            dpg.add_static_texture(
                width=rwidth,
                height=rheight,
                default_value=rdata,
                tag=self.tag + "ico_refresh",
            )
            dpg.add_static_texture(
                width=hdwidth,
                height=hdheight,
                default_value=hddata,
                tag=self.tag + "ico_hard_disk",
            )
            dpg.add_static_texture(
                width=pwidth,
                height=pheight,
                default_value=pdata,
                tag=self.tag + "ico_picture",
            )
            dpg.add_static_texture(
                width=bpwidth,
                height=bpheight,
                default_value=bpdata,
                tag=self.tag + "ico_big_picture",
            )
            dpg.add_static_texture(
                width=pfwidth,
                height=pfheight,
                default_value=pfdata,
                tag=self.tag + "ico_picture_folder",
            )
            dpg.add_static_texture(
                width=dwidth,
                height=dheight,
                default_value=ddata,
                tag=self.tag + "ico_desktop",
            )
            dpg.add_static_texture(
                width=vwidth,
                height=vheight,
                default_value=vdata,
                tag=self.tag + "ico_videos",
            )
            dpg.add_static_texture(
                width=mwidth,
                height=mheight,
                default_value=mdata,
                tag=self.tag + "ico_music_folder",
            )
            dpg.add_static_texture(
                width=dfwidth,
                height=dfheight,
                default_value=dfdata,
                tag=self.tag + "ico_downloads",
            )
            dpg.add_static_texture(
                width=dcfwidth,
                height=dcfheight,
                default_value=dcfdata,
                tag=self.tag + "ico_document_folder",
            )
            dpg.add_static_texture(
                width=swidth,
                height=sheight,
                default_value=sdata,
                tag=self.tag + "ico_search",
            )
            dpg.add_static_texture(
                width=bwidth,
                height=bheight,
                default_value=bdata,
                tag=self.tag + "ico_back",
            )
            dpg.add_static_texture(
                width=cwidth,
                height=cheight,
                default_value=cdata,
                tag=self.tag + "ico_c",
            )
            dpg.add_static_texture(
                width=gwidth,
                height=gheight,
                default_value=gdata,
                tag=self.tag + "ico_gears",
            )
            dpg.add_static_texture(
                width=mnwidth,
                height=mnheight,
                default_value=mndata,
                tag=self.tag + "ico_music_note",
            )
            dpg.add_static_texture(
                width=nwidth,
                height=nheight,
                default_value=ndata,
                tag=self.tag + "ico_note",
            )
            dpg.add_static_texture(
                width=owidth,
                height=oheight,
                default_value=odata,
                tag=self.tag + "ico_object",
            )
            dpg.add_static_texture(
                width=pywidth,
                height=pyheight,
                default_value=pydata,
                tag=self.tag + "ico_python",
            )
            dpg.add_static_texture(
                width=scwidth,
                height=scheight,
                default_value=scdata,
                tag=self.tag + "ico_script",
            )
            dpg.add_static_texture(
                width=vfwidth,
                height=vfheight,
                default_value=vfdata,
                tag=self.tag + "ico_video",
            )
            dpg.add_static_texture(
                width=lwidth,
                height=lheight,
                default_value=ldata,
                tag=self.tag + "ico_link",
            )
            dpg.add_static_texture(
                width=uwidth,
                height=uheight,
                default_value=udata,
                tag=self.tag + "ico_url",
            )
            dpg.add_static_texture(
                width=vewidth,
                height=veheight,
                default_value=vedata,
                tag=self.tag + "ico_vector",
            )
            dpg.add_static_texture(
                width=zwidth,
                height=zheight,
                default_value=zdata,
                tag=self.tag + "ico_zip",
            )
            dpg.add_static_texture(
                width=awidth,
                height=aheight,
                default_value=adata,
                tag=self.tag + "ico_app",
            )
            dpg.add_static_texture(
                width=iwidth,
                height=iheight,
                default_value=idata,
                tag=self.tag + "ico_iso",
            )

        self.img_document = self.tag + "ico_document"
        self.img_home = self.tag + "ico_home"
        self.img_add_folder = self.tag + "ico_add_folder"
        self.img_add_file = self.tag + "ico_add_file"
        self.img_mini_folder = self.tag + "ico_mini_folder"
        self.img_folder = self.tag + "ico_folder"
        self.img_mini_document = self.tag + "ico_mini_document"
        self.img_mini_error = self.tag + "ico_mini_error"
        self.img_refresh = self.tag + "ico_refresh"
        self.img_hard_disk = self.tag + "ico_hard_disk"
        self.img_picture = self.tag + "ico_picture"
        self.img_big_picture = self.tag + "ico_big_picture"
        self.img_picture_folder = self.tag + "ico_picture_folder"
        self.img_desktop = self.tag + "ico_desktop"
        self.img_videos = self.tag + "ico_videos"
        self.img_music_folder = self.tag + "ico_music_folder"
        self.img_downloads = self.tag + "ico_downloads"
        self.img_document_folder = self.tag + "ico_document_folder"
        self.img_search = self.tag + "ico_search"
        self.img_back = self.tag + "ico_back"
        self.img_c = self.tag + "ico_c"
        self.img_gears = self.tag + "ico_gears"
        self.img_music_note = self.tag + "ico_music_note"
        self.img_note = self.tag + "ico_note"
        self.img_object = self.tag + "ico_object"
        self.img_python = self.tag + "ico_python"
        self.img_script = self.tag + "ico_script"
        self.img_video = self.tag + "ico_video"
        self.img_link = self.tag + "ico_link"
        self.img_url = self.tag + "ico_url"
        self.img_vector = self.tag + "ico_vector"
        self.img_zip = self.tag + "ico_zip"
        self.img_app = self.tag + "ico_app"
        self.img_iso = self.tag + "ico_iso"

    def _build_window(self):
        info_px = 90 if self.mode == "save" else 50

        with dpg.window(
            label=self.title,
            tag=self.tag,
            no_resize=self.no_resize,
            show=False,
            modal=self.modal,
            width=self.width,
            height=self.height,
            min_size=self.min_size,
            no_collapse=True,
            pos=(50, 50),
        ):
            with dpg.group(horizontal=True):
                self._build_shortcut_menu(info_px)

                with dpg.child_window(height=-info_px):
                    with dpg.group():
                        with dpg.group(horizontal=True):
                            dpg.add_image_button(
                                self.img_refresh,
                                callback=lambda: self.refresh_entries(),
                            )
                            dpg.add_image_button(
                                self.img_back,
                                callback=lambda: self.chdir(self.default_path),
                            )
                            dpg.add_input_text(
                                hint="Path",
                                on_enter=True,
                                callback=self.on_path_enter,
                                default_value=self.current_path,
                                width=-1,
                                tag=self.tag + "ex_path_input",
                            )

                        with dpg.group(horizontal=True):
                            dpg.add_input_text(
                                hint="Search files",
                                callback=self._search,
                                tag=self.tag + "ex_search",
                                width=-1,
                            )

                        with dpg.table(
                            tag=self.tag + "explorer",
                            callback=self._on_table_sort,
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
                            dpg.add_table_column(
                                label="Name",
                                init_width_or_weight=100,
                                tag=self.tag + "ex_name",
                                default_sort=True,
                            )
                            dpg.add_table_column(
                                label="Date",
                                init_width_or_weight=50,
                                tag=self.tag + "ex_date",
                            )
                            dpg.add_table_column(
                                label="Type",
                                init_width_or_weight=10,
                                tag=self.tag + "ex_type",
                            )
                            dpg.add_table_column(
                                label="Size",
                                init_width_or_weight=10,
                                tag=self.tag + "ex_size",
                                width=10,
                            )

            with dpg.group(horizontal=True):
                dpg.add_spacer(width=480)
                dpg.add_text("File type filter")
                dpg.add_combo(
                    items=self.filter_list,
                    callback=self.filter_combo_selector,
                    default_value=self.file_filter,
                    width=-1,
                    tag=self.tag + "_filter_combo",
                )

            if self.mode == "save":
                with dpg.group(horizontal=True):
                    dpg.add_text("Save as")
                    dpg.add_input_text(
                        hint=self.filename_placeholder,
                        callback=self._on_filename_changed,
                        width=-1,
                        tag=self.tag + "_save_name",
                    )

            with dpg.group(horizontal=True):
                dpg.add_spacer(width=int(self.width * 0.79))
                dpg.add_button(
                    label=self.confirm_label,
                    tag=self.tag + "_action",
                    callback=self._on_action_pressed,
                )
                dpg.add_button(
                    label="Cancel",
                    callback=lambda: dpg.hide_item(self.tag),
                )

            if self.mode == "save":
                with dpg.group(tag=self.tag + "_overwrite_prompt", show=False):
                    dpg.add_separator()
                    dpg.add_text("", tag=self.tag + "_overwrite_text", wrap=self.width - 40)
                    with dpg.group(horizontal=True):
                        dpg.add_button(
                            label="Overwrite",
                            callback=self._confirm_pending_save,
                        )
                        dpg.add_button(
                            label="Keep editing",
                            callback=self._hide_overwrite_prompt,
                        )

    def _build_shortcut_menu(self, info_px):
        if self.user_style == 0:
            with dpg.child_window(
                tag=self.tag + "shortcut_menu",
                width=200,
                resizable_x=True,
                show=self.show_shortcuts_menu,
                height=-info_px,
            ):
                self._build_shortcut_menu_items(compact=False)
        elif self.user_style == 1:
            with dpg.child_window(
                tag=self.tag + "shortcut_menu",
                width=40,
                show=self.show_shortcuts_menu,
                height=-info_px,
            ):
                self._build_shortcut_menu_items(compact=True)

    def _build_shortcut_menu_items(self, compact):
        home = self.get_directory_path("Home")
        desktop = self.get_directory_path("Desktop")
        downloads = self.get_directory_path("Downloads")
        images = self.get_directory_path("Pictures")
        documents = self.get_directory_path("Documents")
        musics = self.get_directory_path("Music")
        videos = self.get_directory_path("Videos")

        shortcuts = [
            (self.img_home, home, "Home"),
            (self.img_desktop, desktop, "Desktop"),
            (self.img_downloads, downloads, "Downloads"),
            (self.img_picture_folder, images, "Images"),
            (self.img_document_folder, documents, "Documents"),
            (self.img_music_folder, musics, "Musics"),
            (self.img_videos, videos, "Videos"),
        ]

        for icon, path, label in shortcuts:
            if not path or not os.path.exists(path):
                continue

            if compact:
                dpg.add_image_button(
                    icon,
                    user_data=path,
                    callback=lambda s, a, u: self.chdir(u),
                )
            else:
                with dpg.group(horizontal=True):
                    dpg.add_image(icon)
                    dpg.add_menu_item(
                        label=label,
                        user_data=path,
                        callback=lambda s, a, u: self.chdir(u),
                    )

        dpg.add_separator()

        drives = self._get_all_drives()
        for drive in drives:
            if compact:
                dpg.add_image_button(
                    texture_tag=self.img_hard_disk,
                    label=drive,
                    user_data=drive,
                    callback=self.open_drive,
                )
            else:
                with dpg.group(horizontal=True):
                    dpg.add_image(self.img_hard_disk)
                    dpg.add_menu_item(
                        label=drive,
                        user_data=drive,
                        callback=self.open_drive,
                    )

    def _get_all_drives(self):
        all_drives = psutil.disk_partitions()
        drive_list = [drive.mountpoint for drive in all_drives if drive.mountpoint]

        if os.name == "posix":
            for device in os.listdir("/dev"):
                if device.startswith("sd") or device.startswith("nvme"):
                    device_path = f"/dev/{device}"
                    if device_path not in drive_list:
                        drive_list.append(device_path)

        return drive_list

    def delete_table(self):
        if not dpg.does_item_exist(self.tag + "explorer"):
            return

        for child in dpg.get_item_children(self.tag + "explorer", 1):
            dpg.delete_item(child)

        self.entry_rows.clear()

    def _format_file_size(self, file_size_bytes):
        size_units = [
            ("TB", 2**40),
            ("GB", 2**30),
            ("MB", 2**20),
            ("KB", 2**10),
            ("B", 1),
        ]

        for unit, size_limit in size_units:
            if file_size_bytes >= size_limit:
                file_size = file_size_bytes / size_limit
                return f"{file_size:.0f} {unit}"

        return "0 B"

    def _get_size_info(self, file_path):
        if os.path.isdir(file_path):
            if not self.show_dir_size:
                return "-", None

            total = 0
            for path, _, files in os.walk(file_path):
                for file_name in files:
                    file_full_path = os.path.join(path, file_name)
                    try:
                        total += os.path.getsize(file_full_path)
                    except OSError:
                        continue
            return self._format_file_size(total), total

        try:
            file_size_bytes = os.path.getsize(file_path)
        except OSError:
            return "0 B", 0

        return self._format_file_size(file_size_bytes), file_size_bytes

    def on_path_enter(self, sender=None, app_data=None, user_data=None):
        try:
            self.chdir(dpg.get_value(self.tag + "ex_path_input"))
        except FileNotFoundError:
            self.message_box("Invalid path", "No such file or directory")

    def message_box(self, title, message):
        modal_id = self.tag + "_message_box"
        if dpg.does_item_exist(modal_id):
            dpg.delete_item(modal_id)

        with dpg.mutex():
            viewport_width = dpg.get_viewport_client_width()
            viewport_height = dpg.get_viewport_client_height()
            with dpg.window(
                label=title,
                tag=modal_id,
                no_resize=True,
                no_collapse=True,
                modal=False,
                no_saved_settings=True,
            ):
                dpg.add_text(message, wrap=max(200, self.width - 60))
                dpg.add_button(
                    label="Ok",
                    width=-1,
                    callback=lambda: dpg.delete_item(modal_id),
                )

        dpg.split_frame()
        width = dpg.get_item_width(modal_id)
        height = dpg.get_item_height(modal_id)
        dpg.set_item_pos(
            modal_id,
            [viewport_width // 2 - width // 2, viewport_height // 2 - height // 2],
        )

    def _clear_selection(self, keep_path=None):
        selected = list(self.selected_files)
        self.selected_files.clear()

        for path in selected:
            if path == keep_path:
                self.selected_files.append(path)
                continue
            self._set_row_selected(path, False)

        self._update_action_button_state()

    def _set_row_selected(self, path, selected):
        for widget in self.entry_rows.get(path, []):
            if dpg.does_item_exist(widget):
                dpg.set_value(widget, selected)

    def _select_single_path(self, path):
        self._clear_selection()
        self.selected_files = [path]
        self._set_row_selected(path, True)
        self._update_action_button_state()

    def _toggle_selected_path(self, path, selected):
        if selected:
            if path not in self.selected_files:
                self.selected_files.append(path)
        elif path in self.selected_files:
            self.selected_files.remove(path)

        self._set_row_selected(path, selected)
        self._update_action_button_state()

    def _clear_state_for_refresh(self):
        self.last_clicked_path = None
        self.last_click_time = 0.0
        self._clear_selection()
        self._hide_overwrite_prompt()

    def _finalize_and_hide(self, payload):
        dpg.hide_item(self.tag)
        if self.callback is not None:
            self.callback(payload)

        self.selected_files.clear()
        self.current_filename = ""
        self.pending_save_path = None
        self.current_path = self.default_path
        self.search_query = ""

        if dpg.does_item_exist(self.tag + "ex_search"):
            dpg.set_value(self.tag + "ex_search", "")
        if dpg.does_item_exist(self.tag + "_save_name"):
            dpg.set_value(self.tag + "_save_name", "")

        self.refresh_entries()
        self._update_action_button_state()

    def return_items(self, sender=None, app_data=None, user_data=None):
        self._finalize_and_hide(list(self.selected_files))

    def open_drive(self, sender, app_data, user_data):
        self.chdir(user_data)

    def _on_entry_activated(self, sender, app_data, user_data):
        entry = user_data
        path = entry.path
        ctrl_down = dpg.is_key_down(dpg.mvKey_LControl) or dpg.is_key_down(dpg.mvKey_RControl)
        current_time = time.time()
        double_clicked = (
            self.last_clicked_path == path and current_time - self.last_click_time < 0.5
        )

        if self.mode == "open" and ctrl_down and self.multi_selection:
            self._toggle_selected_path(path, dpg.get_value(sender))
            self.last_clicked_path = path
            self.last_click_time = current_time
            return

        self._select_single_path(path)

        if entry.is_dir:
            if self.dirs_only:
                self.selected_files = [path]
            if double_clicked:
                if dpg.does_item_exist(self.tag + "ex_search"):
                    dpg.set_value(self.tag + "ex_search", "")
                self.search_query = ""
                self.chdir(path)
                return
        else:
            if self.mode == "save":
                self._set_save_filename(entry.name)
                if double_clicked:
                    self._trigger_save()
                    return
            elif double_clicked:
                self.return_items()
                return

        self.last_clicked_path = path
        self.last_click_time = current_time

    def _search(self, sender=None, app_data=None, user_data=None):
        self.search_query = dpg.get_value(self.tag + "ex_search")
        self.refresh_entries(clear_selection=True)

    def get_directory_path(self, directory_name):
        try:
            if platform.system() in ["Linux", "Darwin"] and directory_name.lower() == "home":
                directory_path = os.path.expanduser("~")
            elif platform.system() == "Windows" and directory_name.lower() == "home":
                directory_path = os.path.expanduser("~")
            else:
                directory_path = os.path.join(os.path.expanduser("~"), directory_name)

            os.listdir(directory_path)
        except FileNotFoundError:
            search_path = os.path.expanduser("~/*/" + directory_name)
            directory_path = glob(search_path)
            if directory_path:
                try:
                    os.listdir(directory_path[0])
                    directory_path = directory_path[0]
                except FileNotFoundError:
                    self.message_box("File dialog - Error", "Could not find the selected directory")
                    return "."
            else:
                self.message_box("File dialog - Error", "Could not find the selected directory")
                return "."
        except Exception:
            return None

        return directory_path

    def _is_hidden(self, filepath):
        name = os.path.basename(os.path.abspath(filepath))
        return name.startswith(".") or (
            os.name == "nt" and self._has_hidden_attribute(filepath)
        )

    def _has_hidden_attribute(self, filepath):
        try:
            import ctypes

            file_attribute_hidden = 0x2
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(filepath))
            return file_attribute_hidden & attrs
        except Exception:
            return False

    def _build_entry(self, full_path):
        entry_name = os.path.basename(full_path)
        is_dir = os.path.isdir(full_path)
        timestamp = os.path.getctime(full_path)
        display_date = time.ctime(timestamp)
        item_type = "Dir" if is_dir else "File"
        display_size, size_bytes = self._get_size_info(full_path)

        return _FileEntry(
            name=entry_name,
            path=full_path,
            is_dir=is_dir,
            hidden=self._is_hidden(full_path),
            timestamp=timestamp,
            display_date=display_date,
            item_type=item_type,
            size_bytes=size_bytes,
            display_size=display_size,
        )

    def _matches_filters(self, entry):
        if entry.hidden and not self.show_hidden_files:
            return False

        if self.search_query and self.search_query.lower() not in entry.name.lower():
            return False

        if entry.is_dir:
            return True

        if self.dirs_only:
            return False

        if self.file_filter == ".*":
            return True

        entry_name = entry.name.casefold()
        filters = [part.strip().casefold() for part in str(self.file_filter).split("|") if part.strip()]
        if not filters:
            return True

        return any(entry_name.endswith(file_filter) for file_filter in filters)

    def _sort_key(self, entry):
        if self.sort_column == "date":
            return (entry.timestamp, entry.name.casefold())
        if self.sort_column == "type":
            type_key = entry.item_type.casefold()
            extension = os.path.splitext(entry.name)[1].casefold()
            return (type_key, extension, entry.name.casefold())
        if self.sort_column == "size":
            return (entry.size_bytes is None, entry.size_bytes or 0, entry.name.casefold())
        return entry.name.casefold()

    def _sort_entries(self, entries):
        directories = [entry for entry in entries if entry.is_dir]
        files = [entry for entry in entries if not entry.is_dir]

        directories = sorted(
            directories,
            key=self._sort_key,
            reverse=not self.sort_ascending,
        )
        files = sorted(
            files,
            key=self._sort_key,
            reverse=not self.sort_ascending,
        )

        return directories + files

    def _collect_entries(self):
        collected_entries = []
        self.entry_lookup.clear()

        with os.scandir(self.current_path) as items:
            for item in items:
                full_path = item.path
                entry = self._build_entry(full_path)
                if not self._matches_filters(entry):
                    continue
                collected_entries.append(entry)
                self.entry_lookup[entry.path] = entry

        self.entries = self._sort_entries(collected_entries)

    def _row_tint(self, entry):
        return [255, 255, 255, self.image_transparency] if entry.hidden else [255, 255, 255, 255]

    def _icon_for_entry(self, entry):
        if entry.is_dir:
            return self.img_mini_folder

        file_name = entry.name.lower()
        if file_name.endswith((".dll", ".a", ".o", ".so", ".ko")):
            return self.img_gears
        if file_name.endswith((".png", ".jpg", ".jpeg")):
            return self.img_picture
        if file_name.endswith((".msi", ".exe", ".bat", ".bin", ".elf")):
            return self.img_app
        if file_name.endswith(".iso"):
            return self.img_iso
        if file_name.endswith((".zip", ".deb", ".rpm", ".tar.gz", ".tar", ".gz", ".lzo", ".lz4", ".7z", ".ppack")):
            return self.img_zip
        if file_name.endswith((".py", ".pyo", ".pyw", ".pyi", ".pyc", ".pyz", ".pyd")):
            return self.img_python
        if file_name.endswith(".c"):
            return self.img_c
        if file_name.endswith((".js", ".json", ".cs", ".cpp", ".h", ".hpp", ".sh", ".pyl", ".rs", ".vbs", ".cmd")):
            return self.img_script
        if file_name.endswith(".url"):
            return self.img_url
        if file_name.endswith(".lnk"):
            return self.img_link
        if file_name.endswith(".txt"):
            return self.img_note
        if file_name.endswith((".mp3", ".ogg", ".wav")):
            return self.img_music_note
        if file_name.endswith((".mp4", ".mov")):
            return self.img_video
        if file_name.endswith((".obj", ".fbx", ".blend")):
            return self.img_object
        if file_name.endswith(".svg"):
            return self.img_vector
        return self.img_mini_document

    def _add_drag_payload(self, entry, cell_name):
        if not self.allow_drag:
            return

        drag_payload = dpg.add_drag_payload(parent=cell_name, payload_type=self.PAYLOAD_TYPE)
        if entry.name.lower().endswith((".png", ".jpg", ".jpeg")):
            dpg.add_image(self.img_big_picture, parent=drag_payload)
        elif entry.is_dir:
            dpg.add_image(self.img_folder, parent=drag_payload)
        else:
            dpg.add_image(self.img_document, parent=drag_payload)

    def _render_parent_row(self):
        with dpg.table_row(parent=self.tag + "explorer"):
            dpg.add_selectable(
                label="..",
                callback=self._back,
                span_columns=True,
                height=self.selec_height,
            )

    def _render_entry(self, entry):
        kwargs_cell = {
            "callback": self._on_entry_activated,
            "span_columns": True,
            "height": self.selec_height,
            "user_data": entry,
            "default_value": entry.path in self.selected_files,
        }

        with dpg.table_row(parent=self.tag + "explorer"):
            with dpg.group(horizontal=True):
                dpg.add_image(self._icon_for_entry(entry), tint_color=self._row_tint(entry))
                cell_name = dpg.add_selectable(label=entry.name, **kwargs_cell)

            cell_time = dpg.add_selectable(label=entry.display_date, **kwargs_cell)
            cell_type = dpg.add_selectable(label=entry.item_type, **kwargs_cell)
            cell_size = dpg.add_selectable(label=entry.display_size, **kwargs_cell)

        self.entry_rows[entry.path] = [cell_name, cell_time, cell_type, cell_size]

        dpg.bind_item_theme(cell_name, self.selec_alignt)
        dpg.bind_item_theme(cell_time, self.selec_alignt)
        dpg.bind_item_theme(cell_type, self.selec_alignt)
        dpg.bind_item_theme(cell_size, self.size_alignt)
        self._add_drag_payload(entry, cell_name)

    def _render_entries(self):
        self.delete_table()
        self._render_parent_row()
        for entry in self.entries:
            self._render_entry(entry)

        dpg.set_value(self.tag + "ex_path_input", self.current_path)
        self._update_action_button_state()

    def _map_sort_column(self, column_tag):
        return {
            self.tag + "ex_name": "name",
            self.tag + "ex_date": "date",
            self.tag + "ex_type": "type",
            self.tag + "ex_size": "size",
        }.get(column_tag, "name")

    def _sort_direction_is_ascending(self, direction):
        if isinstance(direction, str):
            return "desc" not in direction.lower()
        if isinstance(direction, bool):
            return direction
        if isinstance(direction, (int, float)):
            return direction >= 0
        return True

    def _on_table_sort(self, sender, app_data, user_data):
        sort_specs = app_data or user_data or []
        if not sort_specs:
            return

        sort_spec = sort_specs[0]
        if len(sort_spec) < 2:
            return

        self.sort_column = self._map_sort_column(sort_spec[0])
        self.sort_ascending = self._sort_direction_is_ascending(sort_spec[1])
        self.refresh_entries(clear_selection=False)

    def _back(self, sender, app_data, user_data):
        dpg.set_value(sender, False)
        current_time = time.time()
        if (
            current_time - self.last_back_click_time < 0.5
            and self.last_back_widget == sender
        ):
            if dpg.does_item_exist(self.tag + "ex_search"):
                dpg.set_value(self.tag + "ex_search", "")
            self.search_query = ""
            self.chdir("..")
            self.last_back_click_time = 0.0
            self.last_back_widget = None
            return

        self.last_back_click_time = current_time
        self.last_back_widget = sender

    def filter_combo_selector(self, sender, app_data):
        self.file_filter = dpg.get_value(sender)
        self.refresh_entries(clear_selection=True)

    def chdir(self, path):
        destination = self._normalize_target_path(path)
        if destination is None:
            self.message_box(
                "File dialog - invalid path",
                "The selected shortcut does not point to a valid directory.",
            )
            return

        try:
            if not os.path.isdir(destination):
                raise NotADirectoryError(destination)

            self.current_path = destination
            self.refresh_entries(clear_selection=True)
        except PermissionError as error:
            self.message_box(
                "File dialog - PermissionError",
                "Cannot open the folder because it is a system folder or the access is denied\n\n"
                f"More info:\n{error}",
            )
        except NotADirectoryError as error:
            self.message_box(
                "File dialog - not a directory",
                f"The selected item is not a directory, but a file.\n\nMore info:\n{error}",
            )

    def refresh_entries(self, clear_selection=True):
        if clear_selection:
            self._clear_state_for_refresh()

        try:
            self._collect_entries()
            self._render_entries()
        except FileNotFoundError:
            print("DEV:ERROR: Invalid path : " + str(self.current_path))
        except Exception as error:
            import traceback

            traceback.print_exception(type(error), error, error.__traceback__)
            self.message_box(
                "File dialog - Error",
                f"An unknown error has occured when listing the items.\n\nMore info:\n{error}",
            )

    def reset_dir(self, file_name_filter=None, default_path=None):
        if default_path is not None:
            self.current_path = self._normalize_directory(default_path)
        if file_name_filter is not None:
            self.search_query = file_name_filter
            if dpg.does_item_exist(self.tag + "ex_search"):
                dpg.set_value(self.tag + "ex_search", file_name_filter)

        self.refresh_entries(clear_selection=True)

    def _set_save_filename(self, filename):
        self.current_filename = filename
        if dpg.does_item_exist(self.tag + "_save_name"):
            dpg.set_value(self.tag + "_save_name", filename)
        self._update_action_button_state()

    def _on_filename_changed(self, sender, app_data):
        self.current_filename = dpg.get_value(sender)
        self._hide_overwrite_prompt()
        self._update_action_button_state()

    def _update_action_button_state(self):
        if not dpg.does_item_exist(self.tag + "_action"):
            return

        if self.mode == "save":
            enabled = bool(self.current_filename.strip())
        else:
            enabled = bool(self.selected_files)

        dpg.configure_item(self.tag + "_action", enabled=enabled)

    def _hide_overwrite_prompt(self):
        self.pending_save_path = None
        if self.mode == "save" and dpg.does_item_exist(self.tag + "_overwrite_prompt"):
            dpg.hide_item(self.tag + "_overwrite_prompt")

    def _show_overwrite_prompt(self, path):
        self.pending_save_path = path
        dpg.set_value(
            self.tag + "_overwrite_text",
            f'"{path}" already exists. Overwrite it?',
        )
        dpg.show_item(self.tag + "_overwrite_prompt")

    def _confirm_pending_save(self):
        if not self.pending_save_path:
            return

        save_path = self.pending_save_path
        self.pending_save_path = None
        self._hide_overwrite_prompt()
        self._finalize_and_hide(save_path)

    def _trigger_save(self):
        file_name = self.current_filename.strip()
        if not file_name:
            self.message_box("Save dialog", "Please enter a file name before saving.")
            return

        save_path = os.path.abspath(os.path.join(self.current_path, file_name))
        if os.path.isdir(save_path):
            self.message_box(
                "Save dialog",
                "The selected path is a directory. Please enter a file name.",
            )
            return

        if os.path.exists(save_path):
            self._show_overwrite_prompt(save_path)
            return

        self._finalize_and_hide(save_path)

    def _on_action_pressed(self, sender=None, app_data=None, user_data=None):
        if self.mode == "save":
            self._trigger_save()
        else:
            self.return_items()

    def show_file_dialog(self, sender=None, app_data=None, user_data=None):
        self.current_path = self.default_path
        self.search_query = ""
        self.selected_files.clear()
        self.current_filename = ""
        self.pending_save_path = None

        if dpg.does_item_exist(self.tag + "ex_search"):
            dpg.set_value(self.tag + "ex_search", "")
        if dpg.does_item_exist(self.tag + "_save_name"):
            dpg.set_value(self.tag + "_save_name", "")

        self.refresh_entries(clear_selection=True)
        dpg.show_item(self.tag)

    def show_save_dialog(self, sender=None, app_data=None, user_data=None):
        self.show_file_dialog()

    def change_callback(self, callback):
        self.callback = callback


class OpenFileDialog(_BaseFileDialog):
    """
    Open dialog with sortable Name, Date, Type and Size columns.
    """

    def __init__(
        self,
        title="File dialog",
        tag="file_dialog",
        width=950,
        height=650,
        min_size=(460, 320),
        dirs_only=False,
        default_path=None,
        filter_list=None,
        file_filter=".*",
        callback=None,
        show_dir_size=False,
        allow_drag=True,
        multi_selection=True,
        show_shortcuts_menu=True,
        no_resize=True,
        modal=True,
        show_hidden_files=False,
        user_style=0,
    ):
        super().__init__(
            title=title,
            tag=tag,
            width=width,
            height=height,
            min_size=min_size,
            dirs_only=dirs_only,
            default_path=default_path,
            filter_list=filter_list,
            file_filter=file_filter,
            callback=callback,
            show_dir_size=show_dir_size,
            allow_drag=allow_drag,
            multi_selection=multi_selection,
            show_shortcuts_menu=show_shortcuts_menu,
            no_resize=no_resize,
            modal=modal,
            show_hidden_files=show_hidden_files,
            user_style=user_style,
            mode="open",
            confirm_label="OK",
        )


class SaveFileDialog(_BaseFileDialog):
    """
    Save dialog with the same sortable browser plus a file name field.
    """

    def __init__(
        self,
        title="Save file",
        tag="save_file_dialog",
        width=950,
        height=650,
        min_size=(460, 320),
        default_path=None,
        filter_list=None,
        file_filter=".*",
        callback=None,
        show_dir_size=False,
        allow_drag=True,
        show_shortcuts_menu=True,
        no_resize=True,
        modal=True,
        show_hidden_files=False,
        user_style=0,
        filename_placeholder="File name",
    ):
        super().__init__(
            title=title,
            tag=tag,
            width=width,
            height=height,
            min_size=min_size,
            dirs_only=False,
            default_path=default_path,
            filter_list=filter_list,
            file_filter=file_filter,
            callback=callback,
            show_dir_size=show_dir_size,
            allow_drag=allow_drag,
            multi_selection=False,
            show_shortcuts_menu=show_shortcuts_menu,
            no_resize=no_resize,
            modal=modal,
            show_hidden_files=show_hidden_files,
            user_style=user_style,
            mode="save",
            confirm_label="Save",
            filename_placeholder=filename_placeholder,
        )


class FileDialog(OpenFileDialog):
    """
    Backward-compatible alias for the open dialog.
    """


__all__ = ["FileDialog", "OpenFileDialog", "SaveFileDialog"]
