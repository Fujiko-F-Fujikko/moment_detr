# test_main_application_window.py

import sys
import os
import logging
import unittest
from unittest.mock import MagicMock, patch

# テスト対象モジュールのインポートのためのパス設定
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QMenuBar, QStatusBar, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from annotation_data_manager import AnnotationDataManager, AnnotationItem, VideoInfo
from annotation_command_manager import AnnotationCommandManager
from data_io_manager import DataIOManager
from video_controller import VideoController
from timeline_controller import TimelineController
from annotation_list_controller import AnnotationListController
from annotation_editor_controller import AnnotationEditorController
from main_application_window import MainApplicationWindow


class TestMainApplicationWindow(unittest.TestCase):
    """MainApplicationWindowクラスのテスト"""
    
    def setUp(self):
        """各テストメソッドの前に実行される設定"""
        if not QApplication.instance():
            self.app = QApplication([])
        
        self.main_window = MainApplicationWindow()
        
        # テスト用のVideoInfo
        self.video_info = VideoInfo(
            video_id="test_video",
            video_path="/test/video.mp4",
            duration=60.0,
            fps=25.0,
            width=1280,
            height=720
        )
    
    def test_initial_state(self):
        """初期状態のテスト"""
        assert isinstance(self.main_window, QMainWindow)
        assert self.main_window.current_video_path is None
        
        # 各コントローラーが正しく初期化されていることを確認
        assert isinstance(self.main_window.data_manager, AnnotationDataManager)
        assert isinstance(self.main_window.command_manager, AnnotationCommandManager)
        assert isinstance(self.main_window.io_manager, DataIOManager)
        assert isinstance(self.main_window.video_controller, VideoController)
        assert isinstance(self.main_window.timeline_controller, TimelineController)
        assert isinstance(self.main_window.list_controller, AnnotationListController)
        assert isinstance(self.main_window.editor_controller, AnnotationEditorController)
    
    def test_ui_setup(self):
        """UI設定テスト"""
        # メインウィンドウの基本設定
        assert self.main_window.windowTitle() == "Video Annotation Tool"
        assert self.main_window.width() == 1400
        assert self.main_window.height() == 900
        
        # メニューバーの存在確認
        assert isinstance(self.main_window.menuBar(), QMenuBar)
        
        # ステータスバーの存在確認
        assert isinstance(self.main_window.statusBar(), QStatusBar)
        
        # 中央ウィジェットの存在確認
        assert self.main_window.centralWidget() is not None
    
    def test_menu_creation(self):
        """メニュー作成テスト"""
        menubar = self.main_window.menuBar()
        
        # 各メニューの存在確認
        menus = [action.text() for action in menubar.actions()]
        assert "File" in menus
        assert "Edit" in menus
        assert "Help" in menus
    
    @patch('main_application_window.QFileDialog.getOpenFileName')
    def test_open_video_success(self, mock_file_dialog):
        """動画ファイル開く成功テスト"""
        # ファイルダイアログの戻り値をモック
        mock_file_dialog.return_value = ("/test/video.mp4", "Video Files (*.mp4 *.avi)")
        
        with patch.object(self.main_window, 'load_video') as mock_load:
            self.main_window.open_video()
            
            # ファイルダイアログが呼ばれたことを確認
            mock_file_dialog.assert_called_once()
            
            # load_videoが呼ばれたことを確認
            mock_load.assert_called_once_with("/test/video.mp4")
    
    @patch('main_application_window.QFileDialog.getOpenFileName')
    def test_open_video_cancel(self, mock_file_dialog):
        """動画ファイル開くキャンセルテスト"""
        # キャンセル時の戻り値をモック
        mock_file_dialog.return_value = ("", "")
        
        with patch.object(self.main_window, 'load_video') as mock_load:
            self.main_window.open_video()
            
            # load_videoが呼ばれないことを確認
            mock_load.assert_not_called()
    
    def test_load_video_success(self):
        """動画読み込み成功テスト"""
        with patch.object(self.main_window.io_manager, 'load_video_metadata') as mock_metadata, \
             patch.object(self.main_window.video_controller, 'load_video') as mock_video_load, \
             patch.object(self.main_window.data_manager, 'load_video') as mock_data_load:
            
            # メタデータ読み込みの戻り値をモック
            mock_metadata.return_value = self.video_info
            mock_video_load.return_value = True
            
            self.main_window.load_video("/test/video.mp4")
            
            assert self.main_window.current_video_path == "/test/video.mp4"
            
            # 各コンポーネントが呼ばれたことを確認
            mock_metadata.assert_called_once_with("/test/video.mp4")
            mock_video_load.assert_called_once_with("/test/video.mp4", self.video_info)
            mock_data_load.assert_called_once_with("/test/video.mp4", self.video_info)
    
    def test_load_video_metadata_failure(self):
        """動画メタデータ読み込み失敗テスト"""
        with patch.object(self.main_window.io_manager, 'load_video_metadata') as mock_metadata, \
             patch('main_application_window.QMessageBox.critical') as mock_msg:
            
            # メタデータ読み込み失敗をモック
            mock_metadata.return_value = None
            
            self.main_window.load_video("/invalid/video.mp4")
            
            # エラーメッセージが表示されることを確認
            mock_msg.assert_called_once()
            
            # current_video_pathが設定されないことを確認
            assert self.main_window.current_video_path is None
    
    @patch('main_application_window.QFileDialog.getOpenFileName')
    def test_load_inference_results_success(self, mock_file_dialog):
        """推論結果読み込み成功テスト"""
        # ファイルダイアログの戻り値をモック
        mock_file_dialog.return_value = ("/test/inference.json", "JSON Files (*.json)")
        
        with patch.object(self.main_window.io_manager, 'import_inference_results') as mock_import:
            mock_import.return_value = True
            
            self.main_window.load_inference_results()
            
            # インポートが呼ばれたことを確認
            mock_import.assert_called_once_with("/test/inference.json")
    
    @patch('main_application_window.QFileDialog.getOpenFileName')
    def test_load_inference_results_failure(self, mock_file_dialog):
        """推論結果読み込み失敗テスト"""
        # ファイルダイアログの戻り値をモック
        mock_file_dialog.return_value = ("/test/invalid.json", "JSON Files (*.json)")
        
        with patch.object(self.main_window.io_manager, 'import_inference_results') as mock_import, \
             patch('main_application_window.QMessageBox.critical') as mock_msg:
            
            # インポート失敗をモック
            mock_import.side_effect = Exception("Import failed")
            
            self.main_window.load_inference_results()
            
            # エラーメッセージが表示されることを確認
            mock_msg.assert_called_once()
    
    @patch('main_application_window.QFileDialog.getSaveFileName')
    def test_export_stt_dataset_success(self, mock_file_dialog):
        """STTデータセットエクスポート成功テスト"""
        # ファイルダイアログの戻り値をモック
        mock_file_dialog.return_value = ("/test/output.json", "JSON Files (*.json)")
        
        with patch.object(self.main_window.io_manager, 'export_to_stt_format') as mock_export:
            mock_export.return_value = True
            
            self.main_window.export_stt_dataset()
            
            # エクスポートが呼ばれたことを確認
            mock_export.assert_called_once_with("/test/output.json", 0.0)  # デフォルト閾値
    
    @patch('main_application_window.QFileDialog.getSaveFileName')
    def test_export_inference_results_success(self, mock_file_dialog):
        """推論結果エクスポート成功テスト"""
        # ファイルダイアログの戻り値をモック
        mock_file_dialog.return_value = ("/test/output.json", "JSON Files (*.json)")
        
        with patch.object(self.main_window.io_manager, 'export_inference_results') as mock_export:
            mock_export.return_value = True
            
            self.main_window.export_inference_results()
            
            # エクスポートが呼ばれたことを確認
            mock_export.assert_called_once_with("/test/output.json")
    
    def test_create_new_annotation_action(self):
        """新規Actionアノテーション作成テスト"""
        with patch.object(self.main_window.command_manager, 'execute_add_annotation') as mock_add:
            mock_add.return_value = MagicMock()  # 成功時のアノテーション
            
            self.main_window.create_new_annotation("Action")
            
            # コマンドマネージャーが呼ばれたことを確認
            mock_add.assert_called_once()
            args, kwargs = mock_add.call_args
            assert kwargs['annotation_type'] == "Action"
    
    def test_create_new_annotation_step(self):
        """新規Stepアノテーション作成テスト"""
        with patch.object(self.main_window.command_manager, 'execute_add_annotation') as mock_add:
            mock_add.return_value = MagicMock()  # 成功時のアノテーション
            
            self.main_window.create_new_annotation("Step")
            
            # コマンドマネージャーが呼ばれたことを確認
            mock_add.assert_called_once()
            args, kwargs = mock_add.call_args
            assert kwargs['annotation_type'] == "Step"
    
    def test_delete_selected_annotation(self):
        """選択中アノテーション削除テスト"""
        # テスト用のアノテーション
        test_annotation = MagicMock()
        test_annotation.id = "test_001"
        
        with patch.object(self.main_window.list_controller, 'get_selected_annotation') as mock_get, \
             patch.object(self.main_window.command_manager, 'execute_delete_annotation') as mock_delete:
            
            mock_get.return_value = test_annotation
            mock_delete.return_value = True
            
            self.main_window.delete_selected_annotation()
            
            # 削除が実行されたことを確認
            mock_delete.assert_called_once_with("test_001")
    
    def test_delete_selected_annotation_none_selected(self):
        """未選択時のアノテーション削除テスト"""
        with patch.object(self.main_window.list_controller, 'get_selected_annotation') as mock_get, \
             patch.object(self.main_window.command_manager, 'execute_delete_annotation') as mock_delete:
            
            mock_get.return_value = None  # 未選択
            
            self.main_window.delete_selected_annotation()
            
            # 削除が実行されないことを確認
            mock_delete.assert_not_called()
    
    def test_clear_selection(self):
        """選択クリアテスト"""
        with patch.object(self.main_window.list_controller.list_widget, 'clearSelection') as mock_clear, \
             patch.object(self.main_window.timeline_controller, 'clear_highlights') as mock_timeline_clear, \
             patch.object(self.main_window.editor_controller, 'clear_current_annotation') as mock_editor_clear:
            
            self.main_window.clear_selection()
            
            # 各コンポーネントの選択がクリアされたことを確認
            mock_clear.assert_called_once()
            mock_timeline_clear.assert_called_once()
            mock_editor_clear.assert_called_once()
    
    def test_undo_redo(self):
        """Undo/Redoテスト"""
        with patch.object(self.main_window.command_manager, 'undo') as mock_undo, \
             patch.object(self.main_window.command_manager, 'redo') as mock_redo:
            
            # Undoテスト
            self.main_window._undo_action()
            mock_undo.assert_called_once()
            
            # Redoテスト
            self.main_window._redo_action()
            mock_redo.assert_called_once()
    
    def test_keyboard_shortcuts(self):
        """キーボードショートカットテスト"""
        # ショートカットの存在確認（実際のキー入力テストは困難）
        shortcuts = []
        for action in self.main_window.findChildren(QAction):
            if action.shortcut().toString():
                shortcuts.append(action.shortcut().toString())
        
        # 主要なショートカットが設定されていることを確認
        assert "Ctrl+O" in shortcuts  # Open Video
        assert "Ctrl+L" in shortcuts  # Load Inference
        assert "Ctrl+Z" in shortcuts  # Undo
        assert "Ctrl+Y" in shortcuts  # Redo
        assert "Space" in shortcuts   # Play/Pause
        assert "Delete" in shortcuts  # Delete Annotation
    
    def test_signal_connections(self):
        """シグナル接続テスト"""
        # シグナル接続の確認（直接的なテストは困難）
        # 代わりに、必要なシグナルハンドラーメソッドの存在を確認
        assert hasattr(self.main_window, '_on_video_loaded')
        assert hasattr(self.main_window, '_on_annotation_selected')
        assert hasattr(self.main_window, '_on_annotation_modified')
        assert hasattr(self.main_window, '_on_annotation_deleted')
        assert hasattr(self.main_window, '_on_interval_drag_finished')
        assert hasattr(self.main_window, '_on_new_interval_created')
        assert hasattr(self.main_window, '_on_position_clicked')
        assert hasattr(self.main_window, '_on_data_imported')
        assert hasattr(self.main_window, '_on_data_exported')
        assert hasattr(self.main_window, '_on_command_executed')
    
    def test_status_bar_updates(self):
        """ステータスバー更新テスト"""
        # 動画読み込み時のステータス更新
        with patch.object(self.main_window.statusBar(), 'showMessage') as mock_status:
            self.main_window._on_video_loaded("/test/video.mp4")
            
            mock_status.assert_called()
            args = mock_status.call_args[0]
            assert "video.mp4" in args[0]
    
    def test_window_close_handling(self):
        """ウィンドウクローズハンドリングテスト"""
        # closeEventの動作テスト（保存確認など）
        with patch('main_application_window.QMessageBox.question') as mock_question:
            mock_question.return_value = QMessageBox.StandardButton.Yes
            
            # closeEventを直接呼び出すのは困難なので、関連メソッドをテスト
            # 実装に応じて適切なテストを追加
            pass


if __name__ == "__main__":
    import unittest
    
    # ログ設定
    logging.basicConfig(level=logging.DEBUG)
    
    # unittestの実行
    unittest.main()
