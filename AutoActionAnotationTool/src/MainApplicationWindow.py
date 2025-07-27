# MainApplicationWindow.py (リファクタリング版)  
import sys  
import argparse  
from datetime import datetime  
import os  
  
from PyQt6.QtWidgets import QMainWindow, QApplication  
from PyQt6.QtGui import QAction, QUndoStack, QKeySequence, QShortcut  
from PyQt6.QtCore import Qt  
  
from ApplicationCoordinator import ApplicationCoordinator  
from TimelineDisplayManager import TimelineDisplayManager  
from LayoutOrchestrator import LayoutOrchestrator  
from VideoPlayerController import VideoPlayerController  
from FileManager import FileManager  
from UnifiedDataController import UnifiedDataController  
from UnifiedIntervalEditor import UnifiedIntervalEditor  
from UnifiedEditCommandFactory import UnifiedEditCommandFactory  
from DisplayManager import DisplayManager  
from ExportController import ExportController  
from Utilities import show_call_stack  
  
class MainApplicationWindow(QMainWindow):  
    """UIの初期化とメニュー設定に特化したメインウィンドウクラス"""  
      
    def __init__(self):  
        super().__init__()  
        self.setWindowTitle("Moment-DETR Video Annotation Viewer")  
        self.setGeometry(100, 100, 1600, 1000)  
          
        # 統一データコントローラーを初期化  
        self.unified_data_controller = UnifiedDataController()  
          
        # Undo/Redoスタックを初期化  
        self.undo_stack = QUndoStack(self)  
          
        # 統一編集コマンドファクトリーを初期化  
        self.edit_command_factory = UnifiedEditCommandFactory(  
            self.unified_data_controller, self  
        )  
          
        # コアコンポーネントを初期化  
        self.application_coordinator = ApplicationCoordinator(self)  
        self.timeline_display_manager = TimelineDisplayManager()  
        self.layout_orchestrator = LayoutOrchestrator(self)  
        self.video_controller = VideoPlayerController()  
        self.file_manager = FileManager()  
          
        # 統一エディターを初期化  
        self.unified_interval_editor = UnifiedIntervalEditor(self.unified_data_controller)  
          
        # 表示管理とエクスポート管理を初期化  
        self.display_manager = DisplayManager(self.unified_data_controller)  
        self.export_controller = ExportController(self.unified_data_controller)  
          
        # UIを設定  
        self.setup_ui()  
          
        # コンポーネント間の接続を設定  
        self.coordinate_components()  
          
        self.setup_connections()  
        self.setup_menus()  
      
    def coordinate_components(self):  
        """各コーディネーターへの委譲"""  
        # ApplicationCoordinatorに統一データコントローラーを設定  
        self.application_coordinator.set_unified_data_controller(self.unified_data_controller)  
          
        # ApplicationCoordinatorにUI管理コンポーネントを設定  
        self.application_coordinator.set_ui_components(  
            self.timeline_display_manager,  
            self.unified_interval_editor,  
            self.video_controller,  
            self.display_manager  
        )  
      
    def setup_ui(self):  
        """UIレイアウトの初期化"""  
        # 動画ウィジェットとコントロールを取得  
        video_widget = self.video_controller.get_video_widget()  
        controls_layout = self.video_controller.get_controls_layout()  
          
        # LayoutOrchestratorを使用してメインレイアウトを作成  
        main_splitter = self.layout_orchestrator.create_main_layout(  
            video_widget, controls_layout, self.timeline_display_manager,   
            self.unified_interval_editor  
        )  
          
        # UI要素を取得  
        ui_components = self.layout_orchestrator.get_ui_components()  
          
        # フィルタコントロールの設定  
        if 'confidence_slider' in ui_components:  
            self.confidence_slider = ui_components['confidence_slider']  
            self.confidence_value_label = ui_components['confidence_value_label']  
          
        if 'hand_type_combo' in ui_components:  
            self.hand_type_combo = ui_components['hand_type_combo']  
          
        # メインレイアウトを設定  
        self.setCentralWidget(main_splitter)  
      
    def setup_connections(self):  
        """シグナル・スロット接続の設定"""  
        # UnifiedDataControllerのシグナル接続  
        self.unified_data_controller.dataUpdated.connect(self.on_data_changed)  
        self.unified_data_controller.intervalAdded.connect(self.on_interval_added)  
        self.unified_data_controller.intervalModified.connect(self.on_interval_modified)  
        self.unified_data_controller.intervalDeleted.connect(self.on_interval_deleted)  
          
        # 動画プレイヤーコントローラーの接続  
        self.video_controller.positionChanged.connect(self.on_video_position_changed)  
        self.video_controller.durationChanged.connect(self.on_video_duration_changed)  
          
        # ファイル管理の接続  
        self.file_manager.videoLoaded.connect(self.load_video_from_path)  
        self.file_manager.resultsLoaded.connect(self.load_inference_results_from_path)  
        self.file_manager.resultsSaved.connect(self.on_results_saved)  
        self.file_manager.sttDatasetExported.connect(self.on_stt_dataset_exported)  
          
        # フィルタコントロールの接続  
        if hasattr(self, 'confidence_slider'):  
            self.confidence_slider.valueChanged.connect(self.update_confidence_filter)  
          
        if hasattr(self, 'hand_type_combo'):  
            self.hand_type_combo.currentTextChanged.connect(self.update_hand_type_filter)  
          
        # UnifiedIntervalEditorのシグナル接続  
        self.unified_interval_editor.intervalUpdated.connect(self.on_interval_updated)  
        self.unified_interval_editor.intervalDeleted.connect(self.on_interval_deleted)  
        self.unified_interval_editor.intervalAdded.connect(self.on_interval_added)  
        self.unified_interval_editor.dataChanged.connect(self.on_data_changed)  
      
    def setup_menus(self):  
        """メニューバーの設定"""  
        menubar = self.menuBar()  
          
        # ファイルメニュー  
        file_menu = menubar.addMenu('File')  
          
        open_video_action = QAction('Open Video', self)  
        open_video_action.setShortcut(QKeySequence.StandardKey.Open)  
        open_video_action.triggered.connect(lambda: self.file_manager.open_video_dialog(self))  
        file_menu.addAction(open_video_action)  
          
        load_results_action = QAction('Load Inference Results', self)  
        load_results_action.setShortcut(QKeySequence("Ctrl+L"))  
        load_results_action.triggered.connect(lambda: self.file_manager.load_inference_results_dialog(self))  
        file_menu.addAction(load_results_action)  
          
        file_menu.addSeparator()  
          
        export_stt_action = QAction('Export STT Dataset', self)  
        export_stt_action.setShortcut(QKeySequence("Ctrl+E"))  
        export_stt_action.triggered.connect(self.export_stt_dataset)  
        file_menu.addAction(export_stt_action)  
          
        save_results_action = QAction('Save Results', self)  
        save_results_action.setShortcut(QKeySequence.StandardKey.Save)  
        save_results_action.triggered.connect(self.save_results)  
        file_menu.addAction(save_results_action)  
          
        # Editメニュー  
        edit_menu = menubar.addMenu('Edit')  
          
        # Undoアクション  
        undo_action = self.edit_command_factory.get_undo_stack().createUndoAction(self, "Undo")  
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)  
        undo_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)  
        edit_menu.addAction(undo_action)  
          
        # Redoアクション  
        redo_action = self.edit_command_factory.get_undo_stack().createRedoAction(self, "Redo")  
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)  
        redo_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)  
        edit_menu.addAction(redo_action)  
          
        # ショートカット設定  
        self._setup_shortcuts()  
      
    def _setup_shortcuts(self):  
        """キーボードショートカットの設定"""  
        # 動画再生制御  
        play_pause_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Space), self)  
        play_pause_shortcut.activated.connect(self.video_controller.toggle_playback)  
          
        # 動画シーク制御  
        left_arrow_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Left), self)  
        left_arrow_shortcut.activated.connect(lambda: self.seek_relative(-0.1))  
          
        right_arrow_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Right), self)  
        right_arrow_shortcut.activated.connect(lambda: self.seek_relative(0.1))  
          
        # 編集操作  
        delete_shortcut = QShortcut(QKeySequence.StandardKey.Delete, self)  
        delete_shortcut.activated.connect(self._delete_selected_interval)  
      
    def update_display(self):  
        """表示を更新（コマンドクラスから呼び出される）"""  
        # DisplayManagerを通じて更新  
        if hasattr(self, 'display_manager'):  
            self.display_manager.refresh_timeline_display()  
          
        # TimelineDisplayManagerの更新  
        if hasattr(self, 'timeline_display_manager'):  
            self.timeline_display_manager.update_all_timelines()  
      
    def load_video_from_path(self, video_path: str):  
        """動画ファイルを読み込み"""  
        # 動画メタデータを統一データコントローラーに追加  
        # 実装は既存のロジックを参考に  
        pass  
      
    def load_inference_results_from_path(self, results_path: str):  
        """推論結果を読み込み"""  
        success = self.unified_data_controller.load_inference_results(results_path)  
        if success:  
            print(f"Loaded inference results from: {results_path}")  
      
    def export_stt_dataset(self):  
        """STTデータセットをエクスポート"""  
        file_path, _ = self.file_manager.get_save_file_path(  
            self, "Export STT Dataset", "JSON files (*.json)"  
        )  
        if file_path:  
            success = self.export_controller.export_to_stt_json(file_path)  
            if success:  
                self.file_manager.show_save_success_message(file_path, self)  
      
    def save_results(self):  
        """結果を保存"""  
        file_path, _ = self.file_manager.get_save_file_path(  
            self, "Save Results", "JSON files (*.json)"  
        )  
        if file_path:  
            filters = {  
                'confidence_threshold': self.unified_data_controller.confidence_threshold,  
                'hand_type_filter': self.unified_data_controller.hand_type_filter,  
                'interval_type_filter': self.unified_data_controller.interval_type_filter  
            }  
            success = self.export_controller.export_filtered_intervals(file_path, filters)  
            if success:  
                self.file_manager.show_save_success_message(file_path, self)  
      
    def update_confidence_filter(self, threshold: float):  
        """信頼度フィルタ更新"""  
        self.unified_data_controller.set_confidence_threshold(threshold / 100.0)  
      
    def update_hand_type_filter(self, hand_type: str):  
        """Hand Typeフィルタ更新"""  
        self.unified_data_controller.set_hand_type_filter(hand_type)  
      
    def seek_relative(self, seconds: float):  
        """現在位置から相対的にシーク"""  
        current_position = self.video_controller.get_position_seconds()  
        new_position = max(0, current_position + seconds)  
        duration = self.video_controller.get_duration_seconds()  
        if duration > 0:  
            new_position = min(new_position, duration)  
        self.video_controller.seek_to_time(new_position)  
      
    def _delete_selected_interval(self):  
        """選択された区間を削除"""  
        self.unified_interval_editor.delete_interval()  
      
    # イベントハンドラー  
    def on_video_loaded(self, video_path: str):  
        """動画読み込み完了時の処理"""  
        print(f"Video loaded: {video_path}")  
      
    def on_results_loaded(self, results):  
        """結果読み込み完了時の処理"""  
        print("Results loaded")  
      
    def on_data_changed(self):  
        """データ変更時の処理"""  
        self.update_display()  
      
    def on_interval_updated(self):  
        """区間更新時の処理"""  
        self.update_display()  
      
    def on_interval_deleted(self):  
        """区間削除時の処理"""  
        self.update_display()  
      
    def on_interval_added(self):  
        """区間追加時の処理"""  
        self.update_display()  
      
    def on_interval_modified(self, interval_id: str):  
        """区間変更時の処理"""  
        self.update_display()  
      
    def on_video_position_changed(self, position: int):  
        """動画位置変更時の処理"""  
        current_time = position / 1000.0  
        self.display_manager.synchronize_with_video_position(current_time)  
      
    def on_video_duration_changed(self, duration: int):  
        """動画長さ変更時の処理"""  
        if duration > 0:  
            duration_seconds = duration / 1000.0  
            # 必要に応じ  
            # 動画メタデータを更新  
            if hasattr(self, 'current_video_id') and self.current_video_id:  
                # 既存の動画メタデータがあれば更新  
                pass  
      
    def on_results_saved(self, file_path: str):  
        """結果保存完了時の処理"""  
        self.file_manager.show_save_success_message(file_path, self)  
  
    def on_stt_dataset_exported(self, file_path: str):  
        """STTデータセットエクスポート完了時の処理"""  
        self.file_manager.show_save_success_message(file_path, self)  
  
    def get_current_state(self) -> dict:  
        """現在のアプリケーション状態を取得（デバッグ用）"""  
        return {  
            'unified_data_controller_state': {  
                'intervals_count': len(self.unified_data_controller.all_intervals),  
                'confidence_threshold': self.unified_data_controller.confidence_threshold,  
                'hand_type_filter': self.unified_data_controller.hand_type_filter,  
                'interval_type_filter': self.unified_data_controller.interval_type_filter  
            },  
            'timeline_manager_state': self.timeline_display_manager.get_current_state() if hasattr(self.timeline_display_manager, 'get_current_state') else {},  
            'layout_state': self.layout_orchestrator.get_layout_state() if hasattr(self.layout_orchestrator, 'get_layout_state') else {},  
            'undo_stack_count': self.edit_command_factory.get_undo_stack().count(),  
            'undo_stack_index': self.edit_command_factory.get_undo_stack().index()  
        }  
  
  
def main():  
    """アプリケーションのエントリーポイント"""  
    app = QApplication(sys.argv)  
      
    # コマンドライン引数の解析  
    parser = argparse.ArgumentParser(description='Moment-DETR Video Annotation Viewer')  
    parser.add_argument('--video', type=str, help='Video file to load on startup')  
    parser.add_argument('--results', type=str, help='Inference results JSON file to load on startup')  
    args = parser.parse_args()  
      
    # メインウィンドウを作成  
    window = MainApplicationWindow()  
    window.show()  
      
    # 起動時にファイルを読み込み  
    if args.video:  
        window.load_video_from_path(args.video)  
      
    if args.results:  
        window.load_inference_results_from_path(args.results)  
      
    sys.exit(app.exec())  
  
  
if __name__ == '__main__':  
    main()