import os
import json
import sys
import requests
import re
import shutil
from datetime import datetime
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPoint
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, \
                             QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, \
                             QTextEdit, QLabel, QFileDialog, QMessageBox, QSplitter,\
                             QLineEdit, QColorDialog, QMenu, QAbstractItemView, QInputDialog, QDialog)
from PyQt6.QtGui import QPixmap, QImage, QColor, QBrush, QAction, QDropEvent

# --- 🌐 全域簡繁體 UI 字典 ---
LANG_DICT = {
    "zh-TW": {
        "title": "流放者柯南 終極防衝突模組管理器 (V9.3.5 拔除自動掃描·絕對純淨版)",
        "select_dir": "選擇 Mods 資料夾 / modlist.txt",
        "current_file": "目前檔案: ",
        "save_btn": "儲存目前狀態與排序",
        "launch_btn": "🚀 啟動遊戲",
        "set_exe_btn": "⚙️ 設定遊戲路徑",
        "scan_btn": "🔍 掃描工作坊新模組 (手動同步)",
        "up_btn": "▲ 上移",
        "down_btn": "▼ 下移",
        "export_btn": "📤 匯出排序設定",
        "import_btn": "📥 匯入排序設定",
        "search_placeholder": "🔍 輸入關鍵字搜尋模組... (可搜標籤、檔名或群組)",
        "tag_lbl": "🛠️ 全域標籤庫管理 (文字與顏色):",
        "tag_placeholder": "輸入標籤文字...",
        "color_btn": "🎨 選擇顏色",
        "add_tag_btn": "➕ 新增/更新至標籤庫",
        "del_tag_btn": "❌ 從標籤庫刪除",
        "apply_tag_btn": "📌 套用選中標籤至目前模組",
        "clear_tag_btn": "🧹 清除目前模組標籤",
        "mod_detail_title": "詳情面板",
        "mod_info_lbl": "📄 模組詳細資訊與說明對照:",
        "success": "成功",
        "error": "錯誤",
        "save_success": "模組清單與安全防護設定儲存成功！",
        "import_success": "排序與防護狀態匯入成功！",
        "import_fail": "匯入失敗",
        "no_select_mod": "請先選擇一個模組！",
        "no_select_tag": "請先在標籤庫中選擇一個標籤！",
        "ui_toggle_btn": "🌐 切換介面語系 (繁體)",
        "archive_btn": "💾 存檔管理庫"
    },
    "zh-CN": {
        "title": "流放者柯南 终极防冲突模组管理器 (V9.3.5 拔除自动扫描·绝对纯净版)",
        "select_dir": "选择 Mods 文件夹 / modlist.txt",
        "current_file": "当前文件: ",
        "save_btn": "保存当前状态与排序",
        "launch_btn": "🚀 启动游戏",
        "set_exe_btn": "⚙️ 设置游戏路径",
        "scan_btn": "🔍 扫描创意工坊新模组 (手动同步)",
        "up_btn": "▲ 上移",
        "down_btn": "▼ 下移",
        "export_btn": "导出排序设置",
        "import_btn": "📥 导入排序设置",
        "search_placeholder": "🔍 输入关键字搜索模组... (可搜标签、文件名 or 群组)",
        "tag_lbl": "🛠️ 全局标签库管理 (文字与颜色):",
        "tag_placeholder": "输入标签文字...",
        "color_btn": "🎨 选择颜色",
        "add_tag_btn": "➕ 新增/更新至标签库",
        "del_tag_btn": "❌ 从标签库删除",
        "apply_tag_btn": "📌 套用选中标签至当前模组",
        "clear_tag_btn": "🧹 清除当前模组标签",
        "mod_detail_title": "详情面板",
        "mod_info_lbl": "📄 模组详细资讯与说明对照:",
        "success": "成功",
        "error": "错误",
        "save_success": "模组清单与安全防护设置保存成功！",
        "import_success": "排序与防护状态导入成功！",
        "import_fail": "导入失败",
        "no_select_mod": "请先选择一个模组！",
        "no_select_tag": "请先在标签库中选择一个标签！",
        "ui_toggle_btn": "🌐 切换界面语系 (简体)",
        "archive_btn": "💾 存档管理库"
    }
}

class SteamWorkshopThread(QThread):
    info_fetched = pyqtSignal(str, dict)

    def __init__(self, item_id, clean_path):
        super().__init__()
        self.item_id = item_id
        self.clean_path = clean_path

    def run(self):
        result = {
            "title": f"Workshop {self.item_id}",
            "description_zh_zh-CN": "無詳細說明",
            "img_path": "",
            "time_updated": "未知"
        }
        try:
            url = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
            data = {"itemcount": 1, "publishedfileids[0]": int(self.item_id)}
            resp = requests.post(url, data=data, timeout=8)
            if resp.status_code == 200:
                details = resp.json().get("response", {}).get("publishedfiledetails", [{}])[0]
                if details.get("result") == 1:
                    result["title"] = details.get("title", result["title"])
                    result["description_zh_zh-CN"] = details.get("description", "無詳細說明")
                    
                    utime = details.get("time_updated", 0)
                    if utime:
                        result["time_updated"] = datetime.fromtimestamp(utime).strftime('%Y-%m-%d %H:%M')
                    
                    img_url = details.get("preview_url")
                    if img_url:
                        img_resp = requests.get(img_url, timeout=10)
                        if img_resp.status_code == 200:
                            os.makedirs("mod_images", exist_ok=True)
                            local_img = os.path.join("mod_images", f"{self.item_id}.jpg")
                            with open(local_img, "wb") as f:
                                f.write(img_resp.content)
                            result["img_path"] = local_img
        except Exception:
            pass
        self.info_fetched.emit(self.clean_path, result)


class ProtectedListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = None  

    def dropEvent(self, event: QDropEvent):
        if not self.main_window:
            super().dropEvent(event)
            return

        active_item = self.currentItem()
        if not active_item:
            super().dropEvent(event)
            return

        path_curr = active_item.data(Qt.ItemDataRole.UserRole)
        
        if self.main_window.mod_data_map.get(path_curr, {}).get("is_locked"):
            QMessageBox.warning(self.main_window, "禁止拖拽移動", "該模組已被【鎖定保護】，禁止使用滑鼠拖拽改變排序！")
            event.ignore()
            return

        target_item = self.itemAt(event.position().toPoint())
        if target_item and target_item != active_item:
            path_targ = target_item.data(Qt.ItemDataRole.UserRole)
            if self.main_window.mod_data_map.get(path_targ, {}).get("is_locked"):
                QMessageBox.warning(self.main_window, "禁止跨越鎖定模組", "目標位置模組處於【鎖定保護】狀態，禁止將其它模組塞入其上方或下方！")
                event.ignore()
                return

        super().dropEvent(event)
        self.main_window.refresh_all_items_numbers()


class SaveBackupDialog(QDialog):
    def __init__(self, parent, game_exe, lang_code):
        super().__init__(parent)
        self.main_win = parent
        self.game_exe = game_exe
        self.lang_code = lang_code
        self.save_dir_path = ""
        self.backup_root = os.path.join(os.getcwd(), "Game_Save_Backups")
        os.makedirs(self.backup_root, exist_ok=True)
        
        self.init_ui()
        self.auto_detect_save_path()
        self.refresh_backup_list()

    def init_ui(self):
        self.setWindowTitle("💾 遊戲存檔智慧備份與還原防禦庫" if self.lang_code == "zh-TW" else "💾 游戏存档智能备份与还原防御库")
        self.resize(650, 450)
        layout = QVBoxLayout(self)

        path_layout = QHBoxLayout()
        self.lbl_path = QLabel("存檔路徑 (Saved): 未指定")
        self.lbl_path.setWordWrap(True)
        self.btn_browse_save = QPushButton("📂 變更存檔路徑")
        self.btn_browse_save.clicked.connect(self.browse_save_dir)
        path_layout.addWidget(self.lbl_path, 1)
        path_layout.addWidget(self.btn_browse_save)
        layout.addLayout(path_layout)

        op_layout = QHBoxLayout()
        self.btn_do_backup = QPushButton("📸 建立全新時間戳記備份")
        self.btn_do_backup.setStyleSheet("background-color: #2E4053; color: white; font-weight: bold; padding: 6px;")
        self.btn_do_backup.clicked.connect(self.create_backup)
        
        self.btn_open_backup_dir = QPushButton("📂 開啟備份資料夾")
        self.btn_open_backup_dir.clicked.connect(self.open_backup_folder)
        
        op_layout.addWidget(self.btn_do_backup, 1)
        op_layout.addWidget(self.btn_open_backup_dir)
        layout.addLayout(op_layout)

        layout.addWidget(QLabel("歷史備份清單 (雙擊項目可直接覆蓋還原)：" if self.lang_code == "zh-TW" else "历史备份清单 (双击项目可直接覆盖还原)："))

        self.list_backups = QListWidget()
        self.list_backups.itemDoubleClicked.connect(self.restore_backup)
        layout.addWidget(self.list_backups)

        bottom_layout = QHBoxLayout()
        self.btn_restore = QPushButton("⏪ 覆蓋並還原選中存檔")
        self.btn_restore.setStyleSheet("background-color: #C0392B; color: white; font-weight: bold;")
        self.btn_restore.clicked.connect(lambda: self.restore_backup(self.list_backups.currentItem()))
        
        self.btn_delete = QPushButton("❌ 刪除此備份")
        self.btn_delete.clicked.connect(self.delete_backup)
        
        bottom_layout.addWidget(self.btn_restore, 1)
        bottom_layout.addWidget(self.btn_delete)
        layout.addLayout(bottom_layout)

    def auto_detect_save_path(self):
        if self.game_exe and os.path.exists(self.game_exe) and not self.game_exe.startswith("steam://"):
            root_dir = os.path.abspath(os.path.join(os.path.dirname(self.game_exe), "..", "..", "Saved"))
            if os.path.exists(root_dir):
                self.save_dir_path = root_dir
                self.lbl_path.setText(f"偵測到存檔路徑: {self.save_dir_path}")
                return
        
        cache_path = os.path.join(os.getcwd(), "global_tags.json")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    if "last_save_dir" in cfg and os.path.exists(cfg["last_save_dir"]):
                        self.save_dir_path = cfg["last_save_dir"]
                        self.lbl_path.setText(f"已讀取快取路徑: {self.save_dir_path}")
                        return
            except Exception:
                pass
        self.lbl_path.setText("❌ 未偵測到存檔路徑，請手動指定遊戲 Saved 資料夾！")

    def browse_save_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "選擇流放者柯南的 Saved 資料夾", self.save_dir_path)
        if dir_path:
            self.save_dir_path = dir_path
            self.lbl_path.setText(f"手動路徑: {self.save_dir_path}")
            self.save_save_dir_to_config()

    def save_save_dir_to_config(self):
        cache_path = os.path.join(os.getcwd(), "global_tags.json")
        cfg = {}
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            except Exception: pass
        cfg["last_save_dir"] = self.save_dir_path
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=4)
        except Exception: pass

    def refresh_backup_list(self):
        self.list_backups.clear()
        if not os.path.exists(self.backup_root): return
        
        dirs = [d for d in os.listdir(self.backup_root) if os.path.isdir(os.path.join(self.backup_root, d))]
        dirs.sort(reverse=True)
        
        for d in dirs:
            item = QListWidgetItem(f"📦 備份排程：{d}")
            item.setData(Qt.ItemDataRole.UserRole, d)
            self.list_backups.addItem(item)

    def create_backup(self):
        if not self.save_dir_path or not os.path.exists(self.save_dir_path):
            QMessageBox.warning(self, "錯誤", "請先設定正確的 Saved 存檔資料夾路徑！")
            return
        
        note, ok = QInputDialog.getText(self, "新增存檔備份", "請輸入此備份的備忘備註 (可留空):")
        if not ok: return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"{timestamp}_{note.strip()}" if note.strip() else timestamp
        target_path = os.path.join(self.backup_root, folder_name)
        
        try:
            os.makedirs(target_path, exist_ok=True)
            for item in os.listdir(self.save_dir_path):
                s = os.path.join(self.save_dir_path, item)
                d = os.path.join(target_path, item)
                if os.path.isdir(s):
                    if item.lower() in ["logs", "crashreportclient"]: continue 
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    if s.endswith(".db") or s.endswith(".ini") or s.endswith(".txt"):
                        shutil.copy2(s, d)
                        
            QMessageBox.information(self, "備份成功", f"遊戲存檔已安全備份至：\n{folder_name}")
            self.refresh_backup_list()
        except Exception as e:
            QMessageBox.critical(self, "備份失敗", f"備份過程中發生錯誤：\n{str(e)}")

    def restore_backup(self, item):
        if not item: return
        if not self.save_dir_path or not os.path.exists(self.save_dir_path):
            QMessageBox.warning(self, "錯誤", "找不到原遊戲存檔 Saved 資料夾，無法執行覆蓋還原！")
            return
            
        b_folder = item.data(Qt.ItemDataRole.UserRole)
        source_backup_dir = os.path.join(self.backup_root, b_folder)
        
        confirm = QMessageBox.question(
            self, "⚠️ 強制覆蓋警告", 
            f"您確定要將目前的遊戲存檔【完全覆蓋還原】為以下備份嗎？\n\n【{b_folder}】\n\n※此操作不可逆，目前的進度將被完全蓋除！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                for item_name in os.listdir(source_backup_dir):
                    s = os.path.join(source_backup_dir, item_name)
                    d = os.path.join(self.save_dir_path, item_name)
                    if os.path.isdir(s):
                        shutil.copytree(s, d, dirs_exist_ok=True)
                    else:
                        shutil.copy2(s, d)
                QMessageBox.information(self, "還原成功", "存檔覆蓋還原成功！請重新啟動遊戲確認。")
            except Exception as e:
                QMessageBox.critical(self, "還原失敗", f"還原存檔時發生衝突錯誤：\n{str(e)}")

    def delete_backup(self):
        item = self.list_backups.currentItem()
        if not item: return
        b_folder = item.data(Qt.ItemDataRole.UserRole)
        
        confirm = QMessageBox.question(self, "刪除確認", f"確定要徹底刪除此備份檔案嗎？\n{b_folder}", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                shutil.rmtree(os.path.join(self.backup_root, b_folder))
                self.refresh_backup_list()
            except Exception as e:
                QMessageBox.critical(self, "錯誤", f"刪除失敗：{str(e)}")

    def open_backup_folder(self):
        os.startfile(self.backup_root)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_lang_code = "zh-TW"
        self.strings = LANG_DICT[self.current_lang_code]
        
        self.setWindowTitle(self.strings["title"])
        self.setGeometry(100, 100, 1400, 900)

        self.current_modlist_path = ""
        self.mods_directory = ""
        self.mod_data_map = {}          
        self.global_tag_library = {}     
        self.current_mod_index = -1      
        self.selected_tag_color = "#ffffff"
        self.active_threads = []
        self.game_exe_path = "steam://rungameid/440900"

        self.init_ui()
        self.load_global_tags()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        top_layout = QHBoxLayout()
        
        self.btn_ui_toggle = QPushButton(self.strings["ui_toggle_btn"])
        self.btn_ui_toggle.setStyleSheet("background-color: #7D6608; color: white; font-weight: bold;")
        self.btn_ui_toggle.clicked.connect(self.toggle_ui_language)
        
        self.btn_select = QPushButton(self.strings["select_dir"])
        self.btn_select.clicked.connect(self.select_modlist_file)
        self.lbl_current_file = QLabel(self.strings["current_file"] + "未選擇")
        
        self.btn_set_exe = QPushButton(self.strings["set_exe_btn"])
        self.btn_set_exe.setStyleSheet("background-color: #5D6D7E; color: white;")
        self.btn_set_exe.clicked.connect(self.set_custom_game_exe)

        self.btn_archive_mgr = QPushButton(self.strings["archive_btn"])
        self.btn_archive_mgr.setStyleSheet("background-color: #2471A3; color: white; font-weight: bold;")
        self.btn_archive_mgr.clicked.connect(self.open_save_backup_manager)

        self.btn_save = QPushButton(self.strings["save_btn"])
        self.btn_save.clicked.connect(self.save_modlist)
        self.btn_launch = QPushButton(self.strings["launch_btn"])
        self.btn_launch.setStyleSheet("background-color: #1E8449; color: white; font-weight: bold;")
        self.btn_launch.clicked.connect(self.launch_conan_exiles)
        self.btn_scan = QPushButton(self.strings["scan_btn"])
        self.btn_scan.clicked.connect(self.scan_workshop_mods)

        top_layout.addWidget(self.btn_ui_toggle)
        top_layout.addWidget(self.btn_select)
        top_layout.addWidget(self.lbl_current_file, 1)
        top_layout.addWidget(self.btn_set_exe)
        top_layout.addWidget(self.btn_archive_mgr)
        top_layout.addWidget(self.btn_scan)
        top_layout.addWidget(self.btn_save)
        top_layout.addWidget(self.btn_launch)
        main_layout.addLayout(top_layout)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.strings["search_placeholder"])
        self.search_input.textChanged.connect(self.filter_mods)
        
        self.btn_up = QPushButton(self.strings["up_btn"])
        self.btn_up.clicked.connect(lambda: self.move_mod(-1))
        self.btn_down = QPushButton(self.strings["down_btn"])
        self.btn_down.clicked.connect(lambda: self.move_mod(1))
        self.btn_export = QPushButton(self.strings["export_btn"])
        self.btn_export.clicked.connect(self.export_mod_settings)
        self.btn_import = QPushButton(self.strings["import_btn"])
        self.btn_import.clicked.connect(self.import_mod_settings)

        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(self.btn_up)
        search_layout.addWidget(self.btn_down)
        search_layout.addWidget(self.btn_export)
        search_layout.addWidget(self.btn_import)
        main_layout.addLayout(search_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter, 1)

        self.mod_list_widget = ProtectedListWidget()
        self.mod_list_widget.main_window = self  
        self.mod_list_widget.setDragEnabled(True)
        self.mod_list_widget.setAcceptDrops(True)
        self.mod_list_widget.setDropIndicatorShown(True)
        self.mod_list_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.mod_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        self.mod_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.mod_list_widget.customContextMenuRequested.connect(self.show_left_list_context_menu)
        self.mod_list_widget.currentRowChanged.connect(self.on_mod_selection_changed)
        self.mod_list_widget.itemChanged.connect(self.on_item_checked_changed) 
        self.mod_list_widget.model().rowsMoved.connect(self.refresh_all_items_numbers)
        splitter.addWidget(self.mod_list_widget)

        mid_widget = QWidget()
        mid_layout = QVBoxLayout(mid_widget)
        mid_layout.setContentsMargins(5, 5, 5, 5)

        self.lbl_tag_title = QLabel(self.strings["tag_lbl"])
        mid_layout.addWidget(self.lbl_tag_title)
        self.tag_library_list = QListWidget()
        self.tag_library_list.currentItemChanged.connect(self.on_library_tag_selected)
        mid_layout.addWidget(self.tag_library_list, 1)

        tag_input_layout = QHBoxLayout()
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText(self.strings["tag_placeholder"])
        self.btn_pick_color = QPushButton(self.strings["color_btn"])
        self.btn_pick_color.clicked.connect(self.pick_library_tag_color)
        tag_input_layout.addWidget(self.tag_input, 1)
        tag_input_layout.addWidget(self.btn_pick_color)
        mid_layout.addLayout(tag_input_layout)

        tag_op_layout = QHBoxLayout()
        self.btn_add_library_tag = QPushButton(self.strings["add_tag_btn"])
        self.btn_add_library_tag.clicked.connect(self.add_or_update_tag_library)
        self.btn_del_library_tag = QPushButton(self.strings["del_tag_btn"])
        self.btn_del_library_tag.clicked.connect(self.delete_from_tag_library)
        tag_op_layout.addWidget(self.btn_add_library_tag)
        tag_op_layout.addWidget(self.btn_del_library_tag)
        mid_layout.addLayout(tag_op_layout)

        self.lbl_mod_op_sep = QLabel("--- 模組標籤操作 ---")
        mid_layout.addWidget(self.lbl_mod_op_sep)
        self.btn_apply_tag = QPushButton(self.strings["apply_tag_btn"])
        self.btn_apply_tag.clicked.connect(self.apply_selected_library_tag_to_current_mod)
        self.btn_clear_tag = QPushButton(self.strings["clear_tag_btn"])
        self.btn_clear_tag.clicked.connect(self.clear_current_mod_tag)
        mid_widget.layout().addWidget(self.btn_apply_tag)
        mid_widget.layout().addWidget(self.btn_clear_tag)
        splitter.addWidget(mid_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        detail_top_bar = QHBoxLayout()
        self.lbl_mod_info = QLabel(self.strings["mod_info_lbl"])
        detail_top_bar.addWidget(self.lbl_mod_info)
        right_layout.addLayout(detail_top_bar)
        
        self.lbl_mod_img = QLabel("【無預覽圖】")
        self.lbl_mod_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_mod_img.setFixedSize(200, 200)
        self.lbl_mod_img.setStyleSheet("border: 1px solid #555;")
        right_layout.addWidget(self.lbl_mod_img, 0, Qt.AlignmentFlag.AlignCenter)

        self.protection_group = QWidget()
        prot_layout = QVBoxLayout(self.protection_group)
        prot_layout.setContentsMargins(0, 5, 0, 5)
        
        lbl_prot_title = QLabel("🛡️ 模組安全狀態防護設定 :")
        lbl_prot_title.setStyleSheet("font-weight: bold; color: #E74C3C;")
        prot_layout.addWidget(lbl_prot_title)
        
        btn_layout = QHBoxLayout()
        self.btn_panel_lock = QPushButton("🔒 切換 鎖定狀態")
        self.btn_panel_lock.setStyleSheet("background-color: #7B2CBF; color: white; font-weight: bold;")
        self.btn_panel_lock.clicked.connect(self.toggle_current_mod_lock)
        
        self.btn_panel_mutex = QPushButton("⚔️ 設定 互斥群組")
        self.btn_panel_mutex.setStyleSheet("background-color: #D68910; color: white; font-weight: bold;")
        self.btn_panel_mutex.clicked.connect(self.set_current_mod_mutex)
        
        btn_layout.addWidget(self.btn_panel_lock)
        btn_layout.addWidget(self.btn_panel_mutex)
        prot_layout.addLayout(btn_layout)
        
        right_layout.addWidget(self.protection_group)

        self.txt_mod_details = QTextEdit()
        self.txt_mod_details.setReadOnly(True)
        right_layout.addWidget(self.txt_mod_details, 1)
        splitter.addWidget(right_widget)

        splitter.setSizes([550, 220, 430])

    def open_save_backup_manager(self):
        dialog = SaveBackupDialog(self, self.game_exe_path, self.current_lang_code)
        dialog.exec()

    def toggle_ui_language(self):
        self.current_lang_code = "zh-CN" if self.current_lang_code == "zh-TW" else "zh-TW"
        self.strings = LANG_DICT[self.current_lang_code]
        
        self.setWindowTitle(self.strings["title"])
        self.btn_ui_toggle.setText(self.strings["ui_toggle_btn"])
        self.btn_select.setText(self.strings["select_dir"])
        self.btn_save.setText(self.strings["save_btn"])
        self.btn_launch.setText(self.strings["launch_btn"])
        self.btn_set_exe.setText(self.strings["set_exe_btn"])
        self.btn_archive_mgr.setText(self.strings["archive_btn"])
        self.btn_scan.setText(self.strings["scan_btn"])
        self.search_input.setPlaceholderText(self.strings["search_placeholder"])
        self.btn_up.setText(self.strings["up_btn"])
        self.btn_down.setText(self.strings["down_btn"])
        self.btn_export.setText(self.strings["export_btn"])
        self.btn_import.setText(self.strings["import_btn"])
        self.lbl_tag_title.setText(self.strings["tag_lbl"])
        self.tag_input.setPlaceholderText(self.strings["tag_placeholder"])
        self.btn_pick_color.setText(self.strings["color_btn"])
        self.btn_add_library_tag.setText(self.strings["add_tag_btn"])
        self.btn_del_library_tag.setText(self.strings["del_tag_btn"])
        self.btn_apply_tag.setText(self.strings["apply_tag_btn"])
        self.btn_clear_tag.setText(self.strings["clear_tag_btn"])
        self.lbl_mod_info.setText(self.strings["mod_info_lbl"])
        
        if self.current_modlist_path:
            self.lbl_current_file.setText(self.strings["current_file"] + self.current_modlist_path)
        else:
            self.lbl_current_file.setText(self.strings["current_file"] + ("未选择" if self.current_lang_code == "zh-CN" else "未選擇"))
            
        if self.current_mod_index != -1:
            self.on_mod_selection_changed(self.current_mod_index)

    def clean_html_tags(self, text):
        if not text: return ""
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\[\/?[a-zA-Z0-9]+(=[^\]]+)?\]', '', text)
        lines = [line.strip() for line in text.splitlines()]
        return "\n".join([l for l in lines if l])

    def get_smart_translation(self, text, clean_path, target_lang):
        if not text or text in ["無詳細說明", "无详细说明"]: 
            return "無詳細說明" if target_lang == "zh-TW" else "无详细说明"
        
        mdata = self.mod_data_map.get(clean_path, {})
        if target_lang == "zh-TW" and "translated_cache_tw" in mdata and mdata["translated_cache_tw"]:
            return mdata["translated_cache_tw"]
        if target_lang == "zh-CN" and "translated_cache_cn" in mdata and mdata["translated_cache_cn"]:
            return mdata["translated_cache_cn"]

        translated_result = ""
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {"client": "gtx", "sl": "auto", "tl": "zh-TW", "dt": "t", "q": text}
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                res_json = resp.json()
                translated_result = "".join([part[0] for part in res_json[0] if part[0]])
        except Exception:
            translated_result = text

        tw_style = {"模组":"模組","数据":"資料","文件":"檔案","说明":"說明","未知":"未知","无":"擺"}
        cn_style = {"模組":"模组","資料":"数据","檔案":"文件","說明":"说明"}

        if target_lang == "zh-TW":
            for k, v in tw_style.items():
                translated_result = translated_result.replace(k, v)
            if clean_path in self.mod_data_map:
                self.mod_data_map[clean_path]["translated_cache_tw"] = translated_result
            return translated_result
        else:
            cn_result = translated_result
            for k, v in cn_style.items():
                cn_result = cn_result.replace(k, v)
            sc_map = {"個":"个","這":"这","📂":"📂","📋":"📋"}
            for k, v in sc_map.items():
                cn_result = cn_result.replace(k, v)
            if clean_path in self.mod_data_map:
                self.mod_data_map[clean_path]["translated_cache_cn"] = cn_result
            return cn_result

    def set_custom_game_exe(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "選擇遊戲主程式執行檔", "", "Executable Files (*.exe);;All Files (*)")
        if file_path:
            self.game_exe_path = file_path
            self.save_global_tags()
            QMessageBox.information(self, self.strings["success"], f"遊戲啟動路徑已設定為:\n{file_path}")

    def select_modlist_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "選擇 modlist.txt 或 Mods 資料夾", "", "Conan Modlist (modlist.txt);;All Files (*)")
        if file_path:
            if os.path.isdir(file_path):
                self.mods_directory = file_path
                self.current_modlist_path = os.path.join(file_path, "modlist.txt")
            else:
                self.current_modlist_path = file_path
                self.mods_directory = os.path.dirname(file_path)
            
            self.lbl_current_file.setText(self.strings["current_file"] + self.current_modlist_path)
            self.load_modlist()

    def load_modlist(self):
        if not os.path.exists(self.current_modlist_path):
            return
        
        self.mod_list_widget.blockSignals(True)
        self.mod_list_widget.clear()
        self.current_mod_index = -1
        self.mod_list_widget.blockSignals(False)
        
        db_path = os.path.join(self.mods_directory, "mod_enhanced_data.json")
        if os.path.exists(db_path):
            try:
                with open(db_path, "r", encoding="utf-8") as f:
                    self.mod_data_map.update(json.load(f))
            except Exception:
                pass

        try:
            with open(self.current_modlist_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            existing_filenames_lower = set()
            row_counter = 1
            
            self.mod_list_widget.blockSignals(True) 
            
            # 🚀【終極修正】：只讀取 modlist.txt 內的既有排序，徹底移除非必要的自動硬碟掃描！
            for line in lines:
                line = line.strip()
                if not line: continue
                
                is_enabled = True
                raw_path = line
                if raw_path.startswith("*") or raw_path.startswith("#"):
                    is_enabled = False
                    while raw_path and (raw_path.startswith("*") or raw_path.startswith("#")):
                        raw_path = raw_path[1:]
                
                if not raw_path: continue
                
                filename = os.path.basename(raw_path)
                fname_lower = filename.lower()
                
                if fname_lower in existing_filenames_lower:
                    continue
                existing_filenames_lower.add(fname_lower)
                
                final_path_key = raw_path
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, final_path_key)
                
                mdata = self.mod_data_map.get(final_path_key, {})
                if mdata.get("is_locked", False):
                    item.setCheckState(Qt.CheckState.Checked)
                else:
                    item.setCheckState(Qt.CheckState.Checked if is_enabled else Qt.CheckState.Unchecked)
                
                self.update_item_display_style(item, final_path_key, filename, row_counter)
                self.mod_list_widget.addItem(item)
                row_counter += 1

            self.mod_list_widget.blockSignals(False)
            self.refresh_all_items_numbers()
                
        except Exception as e:
            self.mod_list_widget.blockSignals(False)
            QMessageBox.critical(self, self.strings["error"], f"讀取清單失敗:\n{str(e)}")

    def update_item_display_style(self, item, clean_path, filename, row_idx=None):
        if row_idx is None:
            row_idx = self.mod_list_widget.row(item) + 1
            if row_idx <= 0: row_idx = 1
            
        mdata = self.mod_data_map.get(clean_path, {})
        
        prefix_icons = ""
        if mdata.get("is_locked", False):
            prefix_icons += "🔒"
        if mdata.get("mutex_group"):
            prefix_icons += "⚔️"

        display_text = f"[{row_idx:02d}] {prefix_icons}{filename}"
        custom_color = mdata.get("custom_color")
        
        if custom_color:
            item.setBackground(QBrush(QColor(custom_color)))
            c = QColor(custom_color)
            if (c.red()*0.299 + c.green()*0.587 + c.blue()*0.114) < 128:
                item.setForeground(QBrush(QColor("#ffffff")))
            else:
                item.setForeground(QBrush(QColor("#000000")))
        else:
            item.setBackground(QBrush(Qt.GlobalColor.transparent))
            item.setForeground(QBrush(QApplication.palette().text().color()))

        tag = mdata.get("tag", "")
        title = mdata.get("title", "")
        mutex = mdata.get("mutex_group", "")
        
        if tag: display_text = f"[{row_idx:02d}] {prefix_icons}{tag} {filename}"
        if mutex: display_text = f"{display_text} <群組: {mutex}>"
        if title and title != filename: display_text = f"{display_text} ({title})"
            
        item.setText(display_text)

    def refresh_all_items_numbers(self):
        for i in range(self.mod_list_widget.count()):
            item = self.mod_list_widget.item(i)
            if item:
                c_path = item.data(Qt.ItemDataRole.UserRole)
                if c_path:
                    self.update_item_display_style(item, c_path, os.path.basename(c_path), i + 1)

    def on_item_checked_changed(self, item):
        clean_path = item.data(Qt.ItemDataRole.UserRole)
        if not clean_path: return
        
        mdata = self.mod_data_map.get(clean_path, {})
        
        if mdata.get("is_locked", False) and item.checkState() == Qt.CheckState.Unchecked:
            self.mod_list_widget.blockSignals(True)
            item.setCheckState(Qt.CheckState.Checked)
            self.mod_list_widget.blockSignals(False)
            QMessageBox.warning(self, "保護中", "該模組已被鎖定保護，無法變更為不啟用！")
            return

        if item.checkState() == Qt.CheckState.Checked:
            mutex_group = mdata.get("mutex_group")
            if mutex_group:
                self.mod_list_widget.blockSignals(True)
                for i in range(self.mod_list_widget.count()):
                    other_item = self.mod_list_widget.item(i)
                    if other_item == item: continue
                    
                    other_path = other_item.data(Qt.ItemDataRole.UserRole)
                    other_data = self.mod_data_map.get(other_path, {})
                    if other_data.get("mutex_group") == mutex_group:
                        other_item.setCheckState(Qt.CheckState.Unchecked)
                self.mod_list_widget.blockSignals(False)

    def toggle_current_mod_lock(self):
        if self.current_mod_index == -1: return
        item = self.mod_list_widget.item(self.current_mod_index)
        clean_path = item.data(Qt.ItemDataRole.UserRole)
        
        if clean_path not in self.mod_data_map:
            self.mod_data_map[clean_path] = {}
            
        current_state = self.mod_data_map[clean_path].get("is_locked", False)
        new_state = not current_state
        self.mod_data_map[clean_path]["is_locked"] = new_state
        
        if new_state:
            item.setCheckState(Qt.CheckState.Checked) 
            
        self.update_item_display_style(item, clean_path, os.path.basename(clean_path), self.current_mod_index + 1)
        self.on_mod_selection_changed(self.current_mod_index)

    def set_current_mod_mutex(self):
        if self.current_mod_index == -1: return
        item = self.mod_list_widget.item(self.current_mod_index)
        clean_path = item.data(Qt.ItemDataRole.UserRole)
        
        if clean_path not in self.mod_data_map:
            self.mod_data_map[clean_path] = {}
            
        current_group = self.mod_data_map[clean_path].get("mutex_group", "")
        
        group_name, ok = QInputDialog.getText(
            self, "設定互斥群組", 
            f"目前群組: {current_group if current_group else '無'}\n請輸入群組代號（留空則代表清除互斥）:",
            QLineEdit.EchoMode.Normal, current_group
        )
        
        if ok:
            group_name = group_name.strip()
            self.mod_data_map[clean_path]["mutex_group"] = group_name if group_name else ""
            self.update_item_display_style(item, clean_path, os.path.basename(clean_path), self.current_mod_index + 1)
            self.on_mod_selection_changed(self.current_mod_index)
            self.on_item_checked_changed(item)

    def save_modlist(self):
        if not self.current_modlist_path: return
        try:
            with open(self.current_modlist_path, "w", encoding="utf-8") as f:
                for i in range(self.mod_list_widget.count()):
                    item = self.mod_list_widget.item(i)
                    clean_path = item.data(Qt.ItemDataRole.UserRole)
                    prefix = "" if item.checkState() == Qt.CheckState.Checked else "*#"
                    f.write(f"{prefix}{clean_path}\n")

            db_path = os.path.join(self.mods_directory, "mod_enhanced_data.json")
            with open(db_path, "w", encoding="utf-8") as f:
                json.dump(self.mod_data_map, f, ensure_ascii=False, indent=4)

            QMessageBox.information(self, self.strings["success"], self.strings["save_success"])
            self.refresh_all_items_numbers()
        except Exception as e:
            QMessageBox.critical(self, self.strings["error"], f"儲存失敗:\n{str(e)}")

    def launch_conan_exiles(self):
        self.save_modlist()
        try:
            if self.game_exe_path.startswith("steam://"):
                os.startfile(self.game_exe_path)
            else:
                os.startfile(self.game_exe_path, cwd=os.path.dirname(self.game_exe_path))
        except Exception as e:
            QMessageBox.critical(self, self.strings["error"], f"無法啟動遊戲，請重新檢查設定路徑！\n錯誤: {str(e)}")

    def move_mod(self, steps):
        curr_row = self.mod_list_widget.currentRow()
        if curr_row == -1: return
        target_row = curr_row + steps
        
        if 0 <= target_row < self.mod_list_widget.count():
            item_curr = self.mod_list_widget.item(curr_row)
            item_targ = self.mod_list_widget.item(target_row)
            
            path_curr = item_curr.data(Qt.ItemDataRole.UserRole)
            path_targ = item_targ.data(Qt.ItemDataRole.UserRole)
            
            if self.mod_data_map.get(path_curr, {}).get("is_locked") or self.mod_data_map.get(path_targ, {}).get("is_locked"):
                QMessageBox.warning(self, "禁止更動排序", "偵測到移動路徑上存在【鎖定保護】的模組，已自動拒絕排序變更！")
                return
                
            item = self.mod_list_widget.takeItem(curr_row)
            self.mod_list_widget.insertItem(target_row, item)
            self.mod_list_widget.setCurrentRow(target_row)
            self.refresh_all_items_numbers()

    def filter_mods(self, txt):
        txt = txt.lower().strip()
        for i in range(self.mod_list_widget.count()):
            item = self.mod_list_widget.item(i)
            clean_path = item.data(Qt.ItemDataRole.UserRole)
            mdata = self.mod_data_map.get(clean_path, {})
            filename = os.path.basename(clean_path).lower()
            tag = mdata.get("tag", "").lower()
            title = mdata.get("title", "").lower()
            mutex = mdata.get("mutex_group", "").lower()

            if txt in filename or txt in tag or txt in title or txt in mutex:
                item.setHidden(False)
            else:
                item.setHidden(True)

    def load_global_tags(self):
        old_config_path = "mod_config.json"
        if os.path.exists(old_config_path):
            try:
                with open(old_config_path, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                    if "global_settings" in old_data and "tag_library" in old_data["global_settings"]:
                        self.global_tag_library.update(old_data["global_settings"]["tag_library"])
                    if "global_settings" in old_data and "last_game_exe" in old_data["global_settings"]:
                        self.game_exe_path = old_data["global_settings"]["last_game_exe"]
                    for k, v in old_data.items():
                        if k != "global_settings" and isinstance(v, dict):
                            self.mod_data_map[k] = v
            except Exception:
                pass

        tag_path = "global_tags.json"
        if os.path.exists(tag_path):
            try:
                with open(tag_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    if isinstance(cfg, dict):
                        if "tags" in cfg:
                            self.global_tag_library.update(cfg["tags"])
                        if "game_exe_path" in cfg:
                            self.game_exe_path = cfg["game_exe_path"]
            except Exception:
                pass
        self.refresh_tag_library_ui()

    def save_global_tags(self):
        try:
            cfg_data = {
                "tags": self.global_tag_library,
                "game_exe_path": self.game_exe_path
            }
            with open("global_tags.json", "w", encoding="utf-8") as f:
                json.dump(cfg_data, f, ensure_ascii=False, indent=4)
                
            old_backup = {
                "global_settings": {
                    "tag_library": self.global_tag_library,
                    "last_game_exe": self.game_exe_path
                }
            }
            old_backup.update(self.mod_data_map)
            with open("mod_config.json", "w", encoding="utf-8") as f:
                json.dump(old_backup, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def refresh_tag_library_ui(self):
        self.tag_library_list.clear()
        for tag_text, color_hex in self.global_tag_library.items():
            item = QListWidgetItem(tag_text)
            item.setBackground(QBrush(QColor(color_hex)))
            c = QColor(color_hex)
            if (c.red()*0.299 + c.green()*0.587 + c.blue()*0.114) < 128:
                item.setForeground(QBrush(QColor("#ffffff")))
            else:
                item.setForeground(QBrush(QColor("#000000")))
            self.tag_library_list.addItem(item)

    def pick_library_tag_color(self):
        color = QColorDialog.getColor(QColor(self.selected_tag_color), self, "選擇標籤顏色")
        if color.isValid():
            self.selected_tag_color = color.name()
            self.btn_pick_color.setStyleSheet(f"background-color: {self.selected_tag_color};")

    def add_or_update_tag_library(self):
        tag_text = self.tag_input.text().strip()
        if not tag_text: return
        self.global_tag_library[tag_text] = self.selected_tag_color
        self.save_global_tags()
        self.refresh_tag_library_ui()
        self.tag_input.clear()

    def delete_from_tag_library(self):
        curr_item = self.tag_library_list.currentItem()
        if not curr_item: return
        tag_text = curr_item.text()
        if tag_text in self.global_tag_library:
            del self.global_tag_library[tag_text]
            self.save_global_tags()
            self.refresh_tag_library_ui()

    def on_library_tag_selected(self, current, previous):
        if current:
            tag_text = current.text()
            self.tag_input.setText(tag_text)
            self.selected_tag_color = self.global_tag_library.get(tag_text, "#ffffff")
            self.btn_pick_color.setStyleSheet(f"background-color: {self.selected_tag_color};")

    def apply_selected_library_tag_to_current_mod(self):
        if self.current_mod_index == -1:
            QMessageBox.warning(self, self.strings["error"], self.strings["no_select_mod"])
            return
        curr_tag_item = self.tag_library_list.currentItem()
        if not curr_tag_item:
            QMessageBox.warning(self, self.strings["error"], self.strings["no_select_tag"])
            return
        tag_text = curr_tag_item.text()
        self.apply_tag_by_name(self.current_mod_index, tag_text)

    def apply_tag_by_name(self, row_idx, tag_text):
        color_hex = self.global_tag_library.get(tag_text, "#ffffff")
        list_item = self.mod_list_widget.item(row_idx)
        if not list_item: return
        
        clean_path = list_item.data(Qt.ItemDataRole.UserRole)
        if clean_path not in self.mod_data_map:
            self.mod_data_map[clean_path] = {}

        self.mod_data_map[clean_path]["tag"] = tag_text
        self.mod_data_map[clean_path]["custom_color"] = color_hex

        self.update_item_display_style(list_item, clean_path, os.path.basename(clean_path), row_idx + 1)
        self.on_mod_selection_changed(row_idx)

    def clear_current_mod_tag(self):
        if self.current_mod_index == -1: return
        list_item = self.mod_list_widget.item(self.current_mod_index)
        clean_path = list_item.data(Qt.ItemDataRole.UserRole)

        if clean_path in self.mod_data_map:
            self.mod_data_map[clean_path]["tag"] = ""
            self.mod_data_map[clean_path]["custom_color"] = ""

        self.update_item_display_style(list_item, clean_path, os.path.basename(clean_path), self.current_mod_index + 1)
        self.on_mod_selection_changed(self.current_mod_index)

    def on_mod_selection_changed(self, row):
        self.current_mod_index = row  
        if row == -1:
            self.lbl_mod_img.setPixmap(QPixmap())
            self.txt_mod_details.clear()
            return

        item = self.mod_list_widget.item(row)
        if not item: return
            
        clean_path = item.data(Qt.ItemDataRole.UserRole)
        filename = os.path.basename(clean_path)
        mdata = self.mod_data_map.get(clean_path, {})
        
        is_locked = mdata.get("is_locked", False)
        mutex_group = mdata.get("mutex_group", "")
        self.btn_panel_lock.setText("🔓 解除鎖定保護" if is_locked else "🔒 開啟鎖定保護")
        self.btn_panel_mutex.setText(f"⚔️ 互斥: {mutex_group}" if mutex_group else "⚔️ 設定互斥群組")

        raw_description = mdata.get('description_zh_zh-CN', '無詳細說明')
        cleaned_original = self.clean_html_tags(raw_description)
        smart_translation = self.get_smart_translation(cleaned_original, clean_path, self.current_lang_code)

        header_lang = {
            "zh-TW": {"curr_id": "目前編號", "status": "安全狀態", "mutex": "互斥群組", "path": "完整路徑", "tag": "自訂標籤", "title": "工作坊標題", "update": "最後更新", "trans": "翻譯說明", "orig": "英文原文"},
            "zh-CN": {"curr_id": "当前编号", "status": "安全状态", "mutex": "互斥群组", "path": "完整路径", "tag": "自订标签", "title": "工作坊标题", "update": "最后更新", "trans": "翻译说明", "orig": "英文原文"}
        }[self.current_lang_code]

        lock_desc = "🔒 核心鎖定保護中（不可更動與停用）" if is_locked else "正常"
        if self.current_lang_code == "zh-CN" and is_locked:
            lock_desc = "🔒 核心锁定保护中（不可更动与停用）"

        details = (
            f"【{header_lang['curr_id']}】: {row + 1:02d}\n"
            f"【{header_lang['status']}】: {lock_desc}\n"
            f"【{header_lang['mutex']}】: { f'⚔️ {mutex_group}' if mutex_group else '無' }\n"
            f"【{header_lang['path']}】: {clean_path}\n"
            f"【{header_lang['tag']}】: {mdata.get('tag', '無')}\n"
            f"【{header_lang['title']}】: {mdata.get('title', '未知')}\n"
            f"【{header_lang['update']}】: {mdata.get('time_updated', '未知')}\n"
            f"========================================\n\n"
            f"📂 📋 【 {header_lang['trans']} 】：\n"
            f"{smart_translation}\n\n"
            f"========================================\n\n"
            f"【 {header_lang['orig']} 】：\n"
            f"{cleaned_original}"
        )
        self.txt_mod_details.setText(details)

        img_path = mdata.get("img_path", "")
        local_img_path = mdata.get("local_img_path", "")
        target_path = local_img_path if local_img_path else img_path
        full_img_path = ""
        
        if target_path:
            if os.path.isabs(target_path) and os.path.exists(target_path):
                full_img_path = target_path
            else:
                p1 = os.path.join(os.getcwd(), target_path)
                p2 = os.path.join(self.mods_directory, target_path) if self.mods_directory else ""
                if os.path.exists(p1): full_img_path = p1
                elif p2 and os.path.exists(p2): full_img_path = p2

        if full_img_path:
            pixmap = QPixmap(full_img_path)
            self.lbl_mod_img.setPixmap(pixmap.scaled(self.lbl_mod_img.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.lbl_mod_img.setText("【無預覽圖】")

    def scan_workshop_mods(self):
        # 🚀【手動掃描安全機制】：只有當你手動點擊按鈕時，才會去硬碟捕捉不在列表裡的新模組
        existing_filenames_lower = set()
        for i in range(self.mod_list_widget.count()):
            item = self.mod_list_widget.item(i)
            if item:
                c_path = item.data(Qt.ItemDataRole.UserRole)
                if c_path:
                    existing_filenames_lower.add(os.path.basename(c_path).lower())

        local_disk_map = {}
        if os.path.exists(self.mods_directory):
            for root, dirs, files in os.walk(self.mods_directory):
                for file in files:
                    if file.endswith(".pak"):
                        full_path = os.path.join(root, file).replace("\\", "/")
                        local_disk_map[file.lower()] = full_path

        detected_new_mods = []
        for fname_lower, full_abs_path in local_disk_map.items():
            if fname_lower not in existing_filenames_lower:
                detected_new_mods.append(full_abs_path)
                existing_filenames_lower.add(fname_lower)

        if detected_new_mods:
            self.mod_list_widget.blockSignals(True)
            row_counter = self.mod_list_widget.count() + 1
            for new_mod_path in detected_new_mods:
                filename = os.path.basename(new_mod_path)
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, new_mod_path)
                item.setCheckState(Qt.CheckState.Checked)
                self.update_item_display_style(item, new_mod_path, filename, row_counter)
                self.mod_list_widget.addItem(item)
                row_counter += 1
            self.mod_list_widget.blockSignals(False)
            self.refresh_all_items_numbers()
            QMessageBox.information(self, "掃描成功", f"🔍 發現並手動同步了 {len(detected_new_mods)} 個全新未加入的模組！")
        
        self.active_threads.clear()
        scan_count = 0
        
        for i in range(self.mod_list_widget.count()):
            item = self.mod_list_widget.item(i)
            if not item: continue
            clean_path = item.data(Qt.ItemDataRole.UserRole)
            if not clean_path: continue
            
            mdata = self.mod_data_map.get(clean_path, {})
            if mdata.get("title") and mdata.get("description_zh_zh-CN") and mdata.get("description_zh_zh-CN") != "無詳細說明":
                continue
            
            match = re.search(r"content[\\/]440900[\\/](\d+)", clean_path, re.IGNORECASE)
            if match:
                item_id = match.group(1)
                thread = SteamWorkshopThread(item_id, clean_path)
                thread.info_fetched.connect(self.on_workshop_info_fetched)
                self.active_threads.append(thread)
                thread.start()
                scan_count += 1
                
        if scan_count == 0 and not detected_new_mods:
            QMessageBox.information(self, self.strings["success"], "所有模組皆已擁有本地說明快取，已自動跳過重複下載！")

    def on_workshop_info_fetched(self, clean_path, result):
        if clean_path not in self.mod_data_map:
            self.mod_data_map[clean_path] = {}
        
        old_tag = self.mod_data_map[clean_path].get("tag", "")
        old_color = self.mod_data_map[clean_path].get("custom_color", "")
        old_lock = self.mod_data_map[clean_path].get("is_locked", False)
        old_mutex = self.mod_data_map[clean_path].get("mutex_group", "")
        
        if "translated_cache_tw" in self.mod_data_map[clean_path]:
            del self.mod_data_map[clean_path]["translated_cache_tw"]
        if "translated_cache_cn" in self.mod_data_map[clean_path]:
            del self.mod_data_map[clean_path]["translated_cache_cn"]
            
        self.mod_data_map[clean_path].update(result)
        
        self.mod_data_map[clean_path]["tag"] = old_tag
        self.mod_data_map[clean_path]["custom_color"] = old_color
        self.mod_data_map[clean_path]["is_locked"] = old_lock
        self.mod_data_map[clean_path]["mutex_group"] = old_mutex

        for i in range(self.mod_list_widget.count()):
            item = self.mod_list_widget.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == clean_path:
                self.update_item_display_style(item, clean_path, os.path.basename(clean_path), i + 1)
                if i == self.current_mod_index:
                    self.on_mod_selection_changed(i)
                break

    def show_left_list_context_menu(self, pos):
        item = self.mod_list_widget.itemAt(pos)
        if not item: return
        row_idx = self.mod_list_widget.row(item)
        clean_path = item.data(Qt.ItemDataRole.UserRole)
        mdata = self.mod_data_map.get(clean_path, {})
        
        menu = QMenu()
        
        action_enable = QAction("啟用此模組", self)
        action_disable = QAction("停用此模組", self)
        action_enable.triggered.connect(lambda: item.setCheckState(Qt.CheckState.Checked))
        action_disable.triggered.connect(lambda: item.setCheckState(Qt.CheckState.Unchecked))
        menu.addAction(action_enable)
        menu.addAction(action_disable)
        
        menu.addSeparator()
        
        is_locked = mdata.get("is_locked", False)
        action_lock = QAction("🔓 解除鎖定保護" if is_locked else "🔒 開啟鎖定保護", self)
        action_lock.triggered.connect(self.toggle_current_mod_lock)
        menu.addAction(action_lock)
        
        action_mutex = QAction("⚔️ 設定/修改 互斥群組", self)
        action_mutex.triggered.connect(self.set_current_mod_mutex)
        menu.addAction(action_mutex)
        
        menu.addSeparator()
        tag_submenu = menu.addMenu("📌 快速套用全域標籤")
        if self.global_tag_library:
            for tag_name in self.global_tag_library.keys():
                tag_action = QAction(tag_name, self)
                tag_action.triggered.connect(lambda checked, t=tag_name: self.apply_tag_by_name(row_idx, t))
                tag_submenu.addAction(tag_action)
        else:
            tag_submenu.addAction("（目前標籤庫為空）").setEnabled(False)
            
        action_clear = QAction(self.strings["clear_tag_btn"], self)
        action_clear.triggered.connect(self.clear_current_mod_tag)
        menu.addAction(action_clear)
        
        menu.exec(self.mod_list_widget.mapToGlobal(pos))

    def export_mod_settings(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "匯出備份 JSON", "", "JSON Files (*.json)")
        if file_path:
            try:
                export_data = {
                    "backup_version": "9.3",
                    "global_tags": self.global_tag_library,
                    "mod_data_map": self.mod_data_map, 
                    "order_list": []
                }
                for i in range(self.mod_list_widget.count()):
                    item = self.mod_list_widget.item(i)
                    clean_path = item.data(Qt.ItemDataRole.UserRole)
                    export_data["order_list"].append({
                        "filename": os.path.basename(clean_path),
                        "enabled": item.checkState() == Qt.CheckState.Checked,
                        "clean_path": clean_path
                    })
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=4)
                QMessageBox.information(self, self.strings["success"], "匯出防護與排序成功！")
            except Exception as e:
                QMessageBox.critical(self, self.strings["error"], f"匯出失敗:\n{str(e)}")

    def import_mod_settings(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "匯入備份 JSON", "", "JSON Files (*.json)")
        if not file_path: return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                import_data = json.load(f)
            
            if "global_tags" in import_data:
                self.global_tag_library.update(import_data["global_tags"])
                self.save_global_tags()
                self.refresh_tag_library_ui()
                
            if "mod_data_map" in import_data:
                self.mod_data_map.update(import_data["mod_data_map"])

            order_list = import_data.get("order_list", [])
            ui_items_map = {}
            for i in range(self.mod_list_widget.count()):
                item = self.mod_list_widget.item(i)
                if item:
                    c_path = item.data(Qt.ItemDataRole.UserRole)
                    if c_path:
                        ui_items_map[os.path.basename(c_path).lower()] = {
                            "clean_path": c_path,
                            "checked": item.checkState()
                        }

            self.mod_list_widget.blockSignals(True)
            self.mod_list_widget.clear()

            for x in order_list:
                fname_lower = x["filename"].lower()
                if fname_lower in ui_items_map:
                    target_info = ui_items_map.pop(fname_lower)
                    item = QListWidgetItem()
                    item.setData(Qt.ItemDataRole.UserRole, target_info["clean_path"])
                    item.setCheckState(Qt.CheckState.Checked if x["enabled"] else Qt.CheckState.Unchecked)
                    self.mod_list_widget.addItem(item)
            
            for fname_lower, info in ui_items_map.items():
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, info["clean_path"])
                item.setCheckState(info["checked"])
                self.mod_list_widget.addItem(item)

            self.mod_list_widget.blockSignals(False)
            self.current_mod_index = -1
            
            self.refresh_all_items_numbers()
            QMessageBox.information(self, self.strings["success"], self.strings["import_success"])
        except Exception as e:
            self.mod_list_widget.blockSignals(False)
            QMessageBox.critical(self, self.strings["error"], f"{self.strings['import_fail']}\n{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())