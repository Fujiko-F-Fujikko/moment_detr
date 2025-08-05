# main_application_window.py
"""
メインアプリケーションウィンドウ
エントリポイントとUI統合
"""

from PyQt6.QtWidgets import (QMainWindow, QApplication, QSplitter, QVBoxLayout, 
                           QWidget, QMenuBar, QStatusBar, QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QAction, QKeySequence, QShortcut
import sys
import logging
from pathlib import Path
from typing import Optional

from annotation_data_manager import AnnotationDataManager, VideoInfo
from annotation_command_manager import AnnotationCommandManager
from data_io_manager import DataIOManager
from video_controller import VideoController
from timeline_controller import TimelineController
from annotation_list_controller import AnnotationListController
from annotation_editor_controller import AnnotationEditorController


class MainApplicationWindow(QMainWindow):
    """メインアプリケーションウィンドウ"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # ログ設定
        self._setup_logging()
        
        # コアコンポーネント初期化
        self.data_manager = AnnotationDataManager()
        self.command_manager = AnnotationCommandManager(self.data_manager)
        self.io_manager = DataIOManager(self.data_manager)
        self.video_controller = VideoController()
        self.timeline_controller = TimelineController(self.data_manager)
        self.list_controller = AnnotationListController(self.data_manager)
        self.editor_controller = AnnotationEditorController(self.data_manager, self.command_manager)
        
        # UI設定
        self._setup_ui()
        self._setup_connections()
        self._setup_menus()
        self._setup_shortcuts()
        
        # 初期状態
        self.current_video_path: Optional[str] = None
        
        self.logger.info("MainApplicationWindow initialized")
    
    def _setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _setup_ui(self):
        """UI設定"""
        self.setWindowTitle("Moment-DETR Video Annotation Viewer")
        self.setGeometry(100, 100, 1600, 1000)
        
        # メインレイアウト
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # 水平スプリッター
        h_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左パネル（ビデオ + タイムライン）
        left_panel = self._create_left_panel()
        h_splitter.addWidget(left_panel)
        
        # 右パネル（リスト + 編集）
        right_panel = self._create_right_panel()
        h_splitter.addWidget(right_panel)
        
        # 初期サイズ比率
        h_splitter.setSizes([1000, 600])
        
        main_layout.addWidget(h_splitter)
        
        # ステータスバー
        self.statusBar().showMessage("Ready")
    
    def _create_left_panel(self) -> QWidget:
        """左パネル作成"""
        left_panel = QWidget()
        layout = QVBoxLayout(left_panel)
        layout.setContentsMargins(0, 0, 0, 0)  # 左パネルの余白を完全に削除
        
        # 垂直スプリッター
        v_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # ビデオコンテナ
        video_container = QWidget()
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)  # 上下左右の余白を0に
        video_layout.setSpacing(0)  # 要素間の間隔を0に
        video_layout.addWidget(self.video_controller.get_video_widget())
        video_layout.addWidget(self.video_controller.get_control_widget())
        
        v_splitter.addWidget(video_container)
        v_splitter.addWidget(self.timeline_controller.get_timeline_widget())
        
        # 初期サイズ比率
        v_splitter.setSizes([400, 300])
        
        layout.addWidget(v_splitter)
        return left_panel
    
    def _create_right_panel(self) -> QWidget:
        """右パネル作成"""
        right_panel = QWidget()
        layout = QVBoxLayout(right_panel)
        
        # 垂直スプリッター
        v_splitter = QSplitter(Qt.Orientation.Vertical)
        
        v_splitter.addWidget(self.list_controller.get_list_widget())
        v_splitter.addWidget(self.editor_controller.get_editor_widget())
        
        # 初期サイズ比率
        v_splitter.setSizes([400, 400])
        
        layout.addWidget(v_splitter)
        return right_panel
    
    def _setup_connections(self):
        """シグナル接続設定"""
        # ビデオコントローラー
        self.video_controller.video_loaded.connect(self._on_video_loaded)
        self.video_controller.position_changed.connect(self.timeline_controller.set_current_position)
        
        # タイムラインコントローラー
        self.timeline_controller.interval_clicked.connect(self._on_annotation_selected_from_timeline)
        self.timeline_controller.interval_drag_finished.connect(self._on_interval_drag_finished)
        self.timeline_controller.new_interval_created.connect(self._on_new_interval_created)
        self.timeline_controller.position_clicked.connect(self.video_controller.seek_to_time)
        
        # リストコントローラー
        self.list_controller.annotation_selected.connect(self._on_annotation_selected_from_list)
        
        # 編集コントローラー
        self.editor_controller.annotation_modified.connect(self._on_annotation_modified)
        self.editor_controller.annotation_deleted.connect(self._on_annotation_deleted)
        
        # データマネージャー
        self.data_manager.data_changed.connect(self._on_data_changed)
        self.data_manager.annotation_added.connect(self._on_annotation_added)
        
        # IOマネージャー
        self.io_manager.data_imported.connect(self._on_data_imported)
        self.io_manager.data_exported.connect(self._on_data_exported)
        
        # コマンドマネージャー
        self.command_manager.command_executed.connect(self._on_command_executed)
        
        self.logger.info("Signal connections established")
    
    def _setup_menus(self):
        """メニュー設定"""
        menubar = self.menuBar()
        
        # ファイルメニュー
        file_menu = menubar.addMenu('File')
        
        # 動画を開く
        open_video_action = QAction('Open Video', self)
        open_video_action.setShortcut(QKeySequence.StandardKey.Open)
        open_video_action.triggered.connect(self.open_video)
        file_menu.addAction(open_video_action)
        
        # 推論結果を読み込み
        load_results_action = QAction('Load Inference Results', self)
        load_results_action.setShortcut(QKeySequence("Ctrl+L"))
        load_results_action.triggered.connect(self.load_inference_results)
        file_menu.addAction(load_results_action)
        
        file_menu.addSeparator()
        
        # エクスポート
        export_stt_action = QAction('Export STT Dataset', self)
        export_stt_action.setShortcut(QKeySequence("Ctrl+E"))
        export_stt_action.triggered.connect(self.export_stt_dataset)
        file_menu.addAction(export_stt_action)
        
        export_results_action = QAction('Export Inference Results', self)
        export_results_action.setShortcut(QKeySequence("Ctrl+Shift+E"))
        export_results_action.triggered.connect(self.export_inference_results)
        file_menu.addAction(export_results_action)
        
        # 編集メニュー
        edit_menu = menubar.addMenu('Edit')
        
        # Undo/Redo
        undo_action = self.command_manager.get_undo_stack().createUndoAction(self, "Undo")
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        edit_menu.addAction(undo_action)
        
        redo_action = self.command_manager.get_undo_stack().createRedoAction(self, "Redo")
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        # 新規アノテーション
        new_action_action = QAction('New Action Annotation', self)
        new_action_action.setShortcut(QKeySequence("Ctrl+Shift+A"))
        new_action_action.triggered.connect(lambda: self.create_new_annotation('action'))
        edit_menu.addAction(new_action_action)
        
        new_step_action = QAction('New Step Annotation', self)
        new_step_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        new_step_action.triggered.connect(lambda: self.create_new_annotation('step'))
        edit_menu.addAction(new_step_action)
        
        # 表示メニュー
        view_menu = menubar.addMenu('View')
        
        clear_selection_action = QAction('Clear Selection', self)
        clear_selection_action.setShortcut(QKeySequence("Escape"))
        clear_selection_action.triggered.connect(self.clear_selection)
        view_menu.addAction(clear_selection_action)
    
    def _setup_shortcuts(self):
        """ショートカット設定"""
        # 動画制御
        play_pause_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        play_pause_shortcut.activated.connect(self.video_controller.toggle_playback)
        
        # フレーム単位シーク（1フレーム）
        left_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        left_shortcut.activated.connect(lambda: self.video_controller.seek_frame(-1))
        
        right_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        right_shortcut.activated.connect(lambda: self.video_controller.seek_frame(1))
        
        # 10フレーム単位シーク
        shift_left_shortcut = QShortcut(QKeySequence("Shift+Left"), self)
        shift_left_shortcut.activated.connect(lambda: self.video_controller.seek_frame(-10))
        
        shift_right_shortcut = QShortcut(QKeySequence("Shift+Right"), self)
        shift_right_shortcut.activated.connect(lambda: self.video_controller.seek_frame(10))
        
        # 秒単位シーク
        ctrl_left_shortcut = QShortcut(QKeySequence("Ctrl+Left"), self)
        ctrl_left_shortcut.activated.connect(lambda: self.video_controller.seek_relative(-1.0))
        
        ctrl_right_shortcut = QShortcut(QKeySequence("Ctrl+Right"), self)
        ctrl_right_shortcut.activated.connect(lambda: self.video_controller.seek_relative(1.0))
        
        # 削除
        delete_shortcut = QShortcut(QKeySequence.StandardKey.Delete, self)
        delete_shortcut.activated.connect(self.delete_selected_annotation)
    
    # ===== ファイル操作 =====
    
    @pyqtSlot()
    def open_video(self):
        """動画を開く"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Video File", "", 
            "Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*)"
        )
        
        if file_path:
            self.load_video(file_path)
    
    def load_video(self, video_path: str):
        """動画読み込み"""
        try:
            # 動画メタデータ読み込み
            video_info = self.io_manager.load_video_metadata(video_path)
            if not video_info:
                QMessageBox.warning(self, "Error", "Failed to load video metadata")
                return
            
            # データマネージャーに設定
            self.data_manager.load_video(video_path, video_info)
            
            # ビデオコントローラーに読み込み
            self.video_controller.load_video(video_path, video_info)
            
            self.current_video_path = video_path
            self.statusBar().showMessage(f"Video loaded: {Path(video_path).name}")
            
            self.logger.info(f"Video loaded: {video_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to load video: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load video:\n{e}")
    
    @pyqtSlot()
    def load_inference_results(self):
        """推論結果読み込み"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Inference Results", "", 
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            success = self.io_manager.import_inference_results(file_path)
            if success:
                self.statusBar().showMessage(f"Inference results loaded: {Path(file_path).name}")
            else:
                QMessageBox.warning(self, "Error", "Failed to load inference results")
    
    @pyqtSlot()
    def export_stt_dataset(self):
        """STTデータセットエクスポート"""
        if not self.data_manager.get_video_info():
            QMessageBox.warning(self, "Warning", "No video loaded")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export STT Dataset", "", 
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            threshold = self.data_manager.confidence_threshold
            success = self.io_manager.export_to_stt_format(file_path, threshold)
            if success:
                self.statusBar().showMessage(f"STT dataset exported: {Path(file_path).name}")
            else:
                QMessageBox.warning(self, "Error", "Failed to export STT dataset")
    
    @pyqtSlot()
    def export_inference_results(self):
        """推論結果エクスポート"""
        if not self.data_manager.get_video_info():
            QMessageBox.warning(self, "Warning", "No video loaded")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Inference Results", "", 
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            success = self.io_manager.export_inference_results(file_path)
            if success:
                self.statusBar().showMessage(f"Inference results exported: {Path(file_path).name}")
            else:
                QMessageBox.warning(self, "Error", "Failed to export inference results")
    
    # ===== アノテーション操作 =====
    
    def create_new_annotation(self, annotation_type: str):
        """新規アノテーション作成"""
        current_time = self.video_controller.get_position_seconds()
        start_time = current_time
        end_time = start_time + 2.0  # デフォルト2秒
        
        # カテゴリ名
        if annotation_type.lower() == 'action':
            category = "New Action"
        else:
            category = "New Step"
        
        # コマンドで追加
        self.command_manager.execute_add_annotation(
            annotation_type, start_time, end_time, category
        )
        
        self.logger.info(f"Created new {annotation_type} annotation")
    
    @pyqtSlot()
    def delete_selected_annotation(self):
        """選択中のアノテーション削除"""
        selected_annotation = self.list_controller.get_selected_annotation()
        if selected_annotation:
            self.command_manager.execute_delete_annotation(selected_annotation.id)
    
    @pyqtSlot()
    def clear_selection(self):
        """選択クリア"""
        self.list_controller._clear_selection()
        self.timeline_controller.clear_highlights()
        self.editor_controller.clear_current_annotation()
    
    # ===== イベントハンドラー =====
    
    def _on_video_loaded(self, video_info: VideoInfo):
        """動画読み込み完了時の処理"""
        self.timeline_controller.set_video_duration(video_info.duration)
    
    def _on_annotation_selected_from_timeline(self, annotation):
        """タイムラインからアノテーション選択"""
        self.logger.info(f"Timeline selection: {annotation.id} (type: {annotation.annotation_type})")
        self.list_controller.select_annotation(annotation)
        self.editor_controller.set_current_annotation(annotation)
        self.timeline_controller.set_highlighted_annotation(annotation)
        
        # 動画シーク
        self.video_controller.seek_to_time(annotation.start_time)
    
    def _on_annotation_selected_from_list(self, annotation, index):
        """リストからアノテーション選択"""
        self.editor_controller.set_current_annotation(annotation)
        self.timeline_controller.set_highlighted_annotation(annotation)
        
        # 動画シーク
        self.video_controller.seek_to_time(annotation.start_time)
    
    def _on_interval_drag_finished(self, annotation, new_start, new_end):
        """区間ドラッグ完了時の処理"""
        old_values = {
            'start_time': annotation.start_time,
            'end_time': annotation.end_time
        }
        new_values = {
            'start_time': new_start,
            'end_time': new_end
        }
        
        self.command_manager.execute_modify_annotation(
            annotation.id, old_values, new_values
        )
    
    def _on_new_interval_created(self, start_time, end_time, annotation_type_with_hand):
        """新規区間作成時の処理"""
        # annotation_type_with_handは "action_left", "action_right", "action_both", "step" などの形式
        parts = annotation_type_with_hand.split('_')
        annotation_type = parts[0]
        hand_type = parts[1] if len(parts) > 1 and parts[1] != 'other' else None
        
        if annotation_type.lower() == 'action':
            if hand_type:
                category = f"New {hand_type.capitalize()} Hand Action"
            else:
                category = "New Action"
        else:
            category = "New Step"
        
        # アノテーション追加時にhand_typeも含める
        kwargs = {}
        if hand_type:
            kwargs['hand_type'] = hand_type
        
        annotation = self.command_manager.execute_add_annotation(
            annotation_type, start_time, end_time, category, **kwargs
        )
    
    def _on_annotation_modified(self, annotation, old_values, new_values):
        """アノテーション修正時の処理"""
        self.logger.debug(f"Annotation modified: {annotation.id}")
    
    def _on_annotation_deleted(self, annotation):
        """アノテーション削除時の処理"""
        self.logger.debug(f"Annotation deleted: {annotation.id}")
        self.clear_selection()
    
    def _on_data_changed(self):
        """データ変更時の処理"""
        stats = self.data_manager.get_statistics()
        action_count = stats['by_type'].get('Action', 0)
        step_count = stats['by_type'].get('Step', 0)
        status_text = f"Actions: {action_count}, Steps: {step_count}, Total: {stats['total_annotations']}"
        self.statusBar().showMessage(status_text)
    
    def _on_annotation_added(self, annotation):
        """アノテーション追加時の処理"""
        self.logger.debug(f"Annotation added: {annotation.id}")
        # 新しく追加されたアノテーションを選択
        self.list_controller.select_annotation(annotation)
        self.editor_controller.set_current_annotation(annotation)
        self.timeline_controller.set_highlighted_annotation(annotation)
    
    def _on_data_imported(self, annotations):
        """データインポート時の処理"""
        count = len(annotations)
        self.statusBar().showMessage(f"Imported {count} annotations")
        
        if count > 0:
            QMessageBox.information(self, "Import Complete", f"Successfully imported {count} annotations")
    
    def _on_data_exported(self, file_path):
        """データエクスポート時の処理"""
        self.logger.info(f"Data exported to: {file_path}")
    
    def _on_command_executed(self, command_description):
        """コマンド実行時の処理"""
        self.logger.debug(f"Command executed: {command_description}")


def main():
    """アプリケーションエントリーポイント"""
    import argparse
    
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='Video Annotation Tool')
    parser.add_argument('--video', type=str, help='Path to video file to load')
    parser.add_argument('--results', type=str, help='Path to inference results JSON file to load')
    args = parser.parse_args()
    
    app = QApplication(sys.argv)
    
    # アプリケーション情報
    app.setApplicationName("Moment-DETR Video Annotation Viewer")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Annotation Tools")
    
    # メインウィンドウ作成・表示
    window = MainApplicationWindow()
    window.show()
    
    # プロジェクトルートディレクトリを取得
    # スクリプトファイルから3階層上がプロジェクトルート
    # refactor/src/main_application_window.py -> refactor -> AutoActionAnotationTool -> moment_detr-fork
    script_dir = Path(__file__).parent  # refactor/src/
    project_root = script_dir.parent.parent.parent  # moment_detr-fork/
    
    # コマンドライン引数で指定されたファイルを読み込み
    if args.video:
        # 動画ファイルを読み込み
        video_path = Path(args.video)
        
        # 相対パスの場合はプロジェクトルートからの相対パスとして解決
        if not video_path.is_absolute():
            video_path = project_root / video_path
        
        if video_path.exists():
            window.logger.info(f"Loading video from command line: {video_path}")
            window.load_video(str(video_path))
        else:
            window.logger.error(f"Video file not found: {video_path}")
            # 現在のディレクトリも表示してデバッグを支援
            window.logger.error(f"Current working directory: {Path.cwd()}")
            window.logger.error(f"Project root directory: {project_root}")
            QMessageBox.critical(window, "Error", f"Video file not found: {video_path}")
    
    if args.results:
        # 推論結果ファイルを読み込み
        results_path = Path(args.results)
        
        # 相対パスの場合はプロジェクトルートからの相対パスとして解決
        if not results_path.is_absolute():
            results_path = project_root / results_path
        
        if results_path.exists():
            window.logger.info(f"Loading inference results from command line: {results_path}")
            try:
                window.io_manager.import_inference_results(str(results_path))
            except Exception as e:
                window.logger.error(f"Failed to load inference results: {e}")
                QMessageBox.critical(window, "Error", f"Failed to load inference results: {e}")
        else:
            window.logger.error(f"Results file not found: {results_path}")
            # 現在のディレクトリも表示してデバッグを支援
            window.logger.error(f"Current working directory: {Path.cwd()}")
            window.logger.error(f"Project root directory: {project_root}")
            QMessageBox.critical(window, "Error", f"Results file not found: {results_path}")
    
    # 終了
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
