import os
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal


class FileManager(QObject):
    """ファイル操作を担当するクラス"""
    
    # シグナル定義
    videoLoaded = pyqtSignal(str)      # 動画が読み込まれた
    resultsLoaded = pyqtSignal(str)    # 推論結果が読み込まれた
    resultsSaved = pyqtSignal(str)     # 結果が保存された
    
    def __init__(self):
        super().__init__()
        
    def open_video_dialog(self, parent=None):
        """動画ファイルを開くダイアログ"""
        file_path, _ = QFileDialog.getOpenFileName(
            parent, "Open Video", "", "Video Files (*.mp4 *.avi *.mov *.mkv)"
        )
        if file_path:
            self.videoLoaded.emit(file_path)
        return file_path
        
    def load_inference_results_dialog(self, parent=None):
        """推論結果JSONファイルを読み込むダイアログ"""
        file_path, _ = QFileDialog.getOpenFileName(
            parent, "Load Inference Results", "", "JSON Files (*.json)"
        )
        if file_path:
            self.resultsLoaded.emit(file_path)
        return file_path
        
    def save_results_dialog(self, parent=None):
        """結果保存ダイアログ"""
        file_path, _ = QFileDialog.getSaveFileName(
            parent, "Save Results", "", "JSON Files (*.json *.jsonl)"
        )
        if file_path:
            self.resultsSaved.emit(file_path)
        return file_path
        
    def validate_video_file(self, file_path: str) -> bool:
        """動画ファイルの妥当性をチェック"""
        if not file_path:
            return False
            
        if not os.path.exists(file_path):
            QMessageBox.critical(None, "Error", f"Video file not found: {file_path}")
            return False
            
        return True
        
    def validate_json_file(self, file_path: str) -> bool:
        """JSONファイルの妥当性をチェック"""
        if not file_path:
            return False
            
        if not os.path.exists(file_path):
            QMessageBox.critical(None, "Error", f"JSON file not found: {file_path}")
            return False
            
        return True
        
    def show_save_success_message(self, file_path: str, parent=None):
        """保存成功メッセージを表示"""
        QMessageBox.information(parent, "Success", f"Results saved to {file_path}")
        
    def show_save_error_message(self, error_message: str, parent=None):
        """保存エラーメッセージを表示"""
        QMessageBox.critical(parent, "Error", f"Failed to save results: {error_message}")
        
    def show_load_error_message(self, error_message: str, parent=None):
        """読み込みエラーメッセージを表示"""
        QMessageBox.critical(parent, "Error", f"Failed to load file: {error_message}")
        
    def show_no_results_warning(self, parent=None):
        """結果がない場合の警告を表示"""
        QMessageBox.warning(parent, "Warning", "No results to save!")
