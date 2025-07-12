# FileManager.py (新アーキテクチャ版)  
import os  
from pathlib import Path  
from PyQt6.QtWidgets import QFileDialog, QMessageBox  
from PyQt6.QtCore import QObject, pyqtSignal  
from typing import Optional, List  
  
class FileManager(QObject):  
    """ファイル操作を担当するクラス（新アーキテクチャ版）"""  
      
    # シグナル定義  
    videoLoaded = pyqtSignal(str)      # 動画が読み込まれた  
    resultsLoaded = pyqtSignal(str)    # 推論結果が読み込まれた  
    resultsSaved = pyqtSignal(str)     # 結果が保存された  
    sttDatasetExported = pyqtSignal(str)  # STTデータセットがエクスポートされた  
      
    def __init__(self):  
        super().__init__()  
        self.last_video_directory = ""  
        self.last_results_directory = ""  
        self.last_export_directory = ""  
          
    def open_video_dialog(self, parent=None) -> Optional[str]:  
        """動画ファイルを開くダイアログ"""  
        start_dir = self.last_video_directory or ""  
          
        file_path, _ = QFileDialog.getOpenFileName(  
            parent,   
            "Open Video",   
            start_dir,  
            "Video Files (*.mp4 *.avi *.mov *.mkv *.webm *.flv);;All Files (*)"  
        )  
          
        if file_path:  
            self.last_video_directory = str(Path(file_path).parent)  
            if self.validate_video_file(file_path, parent):  
                self.videoLoaded.emit(file_path)  
                return file_path  
          
        return None  
          
    def load_inference_results_dialog(self, parent=None) -> Optional[str]:  
        """推論結果JSONファイルを読み込むダイアログ"""  
        start_dir = self.last_results_directory or ""  
          
        file_path, _ = QFileDialog.getOpenFileName(  
            parent,   
            "Load Inference Results",   
            start_dir,  
            "JSON Files (*.json *.jsonl);;All Files (*)"  
        )  
          
        if file_path:  
            self.last_results_directory = str(Path(file_path).parent)  
            if self.validate_json_file(file_path, parent):  
                self.resultsLoaded.emit(file_path)  
                return file_path  
          
        return None  
          
    def save_results_dialog(self, parent=None) -> Optional[str]:  
        """結果保存ダイアログ"""  
        start_dir = self.last_results_directory or ""  
          
        file_path, _ = QFileDialog.getSaveFileName(  
            parent,   
            "Save Results",   
            start_dir,  
            "JSON Files (*.json);;JSONL Files (*.jsonl);;All Files (*)"  
        )  
          
        if file_path:  
            self.last_results_directory = str(Path(file_path).parent)  
            self.resultsSaved.emit(file_path)  
            return file_path  
          
        return None  
      
    def export_stt_dataset_dialog(self, parent=None, default_name: str = "stt_dataset.json") -> Optional[str]:  
        """STTデータセットエクスポートダイアログ"""  
        start_dir = self.last_export_directory or ""  
        default_path = str(Path(start_dir) / default_name) if start_dir else default_name  
          
        file_path, _ = QFileDialog.getSaveFileName(  
            parent,  
            "Export STT Dataset",  
            default_path,  
            "JSON Files (*.json);;All Files (*)"  
        )  
          
        if file_path:  
            self.last_export_directory = str(Path(file_path).parent)  
            self.sttDatasetExported.emit(file_path)  
            return file_path  
          
        return None  
      
    def select_multiple_files_dialog(self, parent=None, file_filter: str = "All Files (*)") -> List[str]:  
        """複数ファイル選択ダイアログ"""  
        file_paths, _ = QFileDialog.getOpenFileNames(  
            parent,  
            "Select Files",  
            "",  
            file_filter  
        )  
        return file_paths  
      
    def select_directory_dialog(self, parent=None, title: str = "Select Directory") -> Optional[str]:  
        """ディレクトリ選択ダイアログ"""  
        directory = QFileDialog.getExistingDirectory(  
            parent,  
            title,  
            ""  
        )  
        return directory if directory else None  
          
    def validate_video_file(self, file_path: str, parent=None) -> bool:  
        """動画ファイルの妥当性をチェック"""  
        if not file_path:  
            return False  
              
        path = Path(file_path)  
          
        if not path.exists():  
            self.show_error_message(  
                f"Video file not found: {file_path}",  
                "File Not Found",  
                parent  
            )  
            return False  
          
        # ファイルサイズチェック  
        if path.stat().st_size == 0:  
            self.show_error_message(  
                f"Video file is empty: {file_path}",  
                "Invalid File",  
                parent  
            )  
            return False  
          
        # 拡張子チェック  
        valid_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv'}  
        if path.suffix.lower() not in valid_extensions:  
            self.show_warning_message(  
                f"Unsupported video format: {path.suffix}",  
                "Unsupported Format",  
                parent  
            )  
            # 警告だけで処理は続行  
              
        return True  
          
    def validate_json_file(self, file_path: str, parent=None) -> bool:  
        """JSONファイルの妥当性をチェック"""  
        if not file_path:  
            return False  
              
        path = Path(file_path)  
          
        if not path.exists():  
            self.show_error_message(  
                f"JSON file not found: {file_path}",  
                "File Not Found",   
                parent  
            )  
            return False  
          
        # ファイルサイズチェック  
        if path.stat().st_size == 0:  
            self.show_error_message(  
                f"JSON file is empty: {file_path}",  
                "Invalid File",  
                parent  
            )  
            return False  
          
        # 基本的なJSON形式チェック  
        try:  
            import json  
            with open(file_path, 'r', encoding='utf-8') as f:  
                json.load(f)  
        except json.JSONDecodeError as e:  
            self.show_error_message(  
                f"Invalid JSON format: {str(e)}",  
                "JSON Parse Error",  
                parent  
            )  
            return False  
        except Exception as e:  
            self.show_error_message(  
                f"Failed to read JSON file: {str(e)}",  
                "File Read Error",  
                parent  
            )  
            return False  
              
        return True  
      
    def check_file_writable(self, file_path: str, parent=None) -> bool:  
        """ファイルが書き込み可能かチェック"""  
        path = Path(file_path)  
          
        # ディレクトリが存在するかチェック  
        if not path.parent.exists():  
            self.show_error_message(  
                f"Directory does not exist: {path.parent}",  
                "Directory Not Found",  
                parent  
            )  
            return False  
          
        # ディレクトリが書き込み可能かチェック  
        if not os.access(path.parent, os.W_OK):  
            self.show_error_message(  
                f"No write permission for directory: {path.parent}",  
                "Permission Error",  
                parent  
            )  
            return False  
          
        # ファイルが既に存在する場合、上書き確認  
        if path.exists():  
            reply = QMessageBox.question(  
                parent,  
                "File Exists",  
                f"File already exists: {path.name}\\nDo you want to overwrite it?",  
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,  
                QMessageBox.StandardButton.No  
            )  
            return reply == QMessageBox.StandardButton.Yes  
          
        return True  
          
    def show_save_success_message(self, file_path: str, parent=None):  
        """保存成功メッセージを表示"""  
        QMessageBox.information(  
            parent,   
            "Success",   
            f"File saved successfully:\\n{file_path}"  
        )  
          
    def show_save_error_message(self, error_message: str, parent=None):  
        """保存エラーメッセージを表示"""  
        QMessageBox.critical(  
            parent,   
            "Save Error",   
            f"Failed to save file:\\n{error_message}"  
        )  
          
    def show_load_error_message(self, error_message: str, parent=None):  
        """読み込みエラーメッセージを表示"""  
        QMessageBox.critical(  
            parent,   
            "Load Error",   
            f"Failed to load file:\\n{error_message}"  
        )  
          
    def show_no_results_warning(self, parent=None):  
        """結果がない場合の警告を表示"""  
        QMessageBox.warning(  
            parent,   
            "No Data",   
            "No results to save!\\nPlease load inference results first."  
        )  
      
    def show_error_message(self, message: str, title: str = "Error", parent=None):  
        """汎用エラーメッセージ表示"""  
        QMessageBox.critical(parent, title, message)  
      
    def show_warning_message(self, message: str, title: str = "Warning", parent=None):  
        """汎用警告メッセージ表示"""  
        QMessageBox.warning(parent, title, message)  
      
    def show_info_message(self, message: str, title: str = "Information", parent=None):  
        """汎用情報メッセージ表示"""  
        QMessageBox.information(parent, title, message)  
      
    def get_recent_directories(self) -> dict:  
        """最近使用したディレクトリを取得"""  
        return {  
            'video': self.last_video_directory,  
            'results': self.last_results_directory,  
            'export': self.last_export_directory  
        }  
      
    def set_recent_directories(self, directories: dict):  
        """最近使用したディレクトリを設定"""  
        self.last_video_directory = directories.get('video', '')  
        self.last_results_directory = directories.get('results', '')  
        self.last_export_directory = directories.get('export', '')