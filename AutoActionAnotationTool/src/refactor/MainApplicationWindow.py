# MainApplicationWindow.py (リファクタリング版)  
import sys  
import argparse  
from pathlib import Path  
  
from PyQt6.QtWidgets import QMainWindow, QApplication, QFileDialog, QMessageBox, QDialog  
from PyQt6.QtGui import QAction, QUndoStack, QKeySequence, QShortcut  
from PyQt6.QtCore import Qt  
  
from ApplicationCoordinator import ApplicationCoordinator  
from TimelineDisplayManager import TimelineDisplayManager  
from EditWidgetManager import EditWidgetManager  
from LayoutOrchestrator import LayoutOrchestrator  
from VideoPlayerController import VideoPlayerController  
from FileManager import FileManager  
  
class MainApplicationWindow(QMainWindow):  
    """UIの初期化とメニュー設定に特化したメインウィンドウクラス"""  
      
    def __init__(self):  
        super().__init__()  
        self.setWindowTitle("Moment-DETR Video Annotation Viewer")  
        self.setGeometry(100, 100, 1600, 1000)  
          
        # Undo/Redoスタックを初期化  
        self.undo_stack = QUndoStack(self)  
          
        # コアコンポーネントを初期化  
        self.application_coordinator = ApplicationCoordinator(self)  
        self.timeline_display_manager = TimelineDisplayManager()  
        self.edit_widget_manager = EditWidgetManager(self)  
        self.layout_orchestrator = LayoutOrchestrator(self)  
        self.video_controller = VideoPlayerController()  
        self.file_manager = FileManager()  
          
        # コンポーネント間の接続を設定  
        self.coordinate_components()  
          
        # UIを設定  
        self.setup_ui()  
        self.setup_connections()  
        self.setup_menus()  
      
    def coordinate_components(self):  
        """各コーディネーターへの委譲"""  
        # ApplicationCoordinatorにUI管理コンポーネントを設定  
        self.application_coordinator.set_ui_components(  
            self.timeline_display_manager,  
            self.edit_widget_manager,  
            self.video_controller  
        )  
          
        # EditWidgetManagerにSTTDataControllerを設定  
        stt_controller = self.application_coordinator.get_stt_data_controller()  
        self.edit_widget_manager.set_stt_data_manager(stt_controller)  
      
    def setup_ui(self):  
        """UIレイアウトの初期化"""  
        # 動画ウィジェットとコントロールを取得  
        video_widget = self.video_controller.get_video_widget()  
        controls_layout = self.video_controller.get_controls_layout()  
          
        # LayoutOrchestratorを使用してメインレイアウトを作成  
        main_splitter = self.layout_orchestrator.create_main_layout(  
            video_widget, controls_layout, self.timeline_display_manager  
        )  
          
        # UI要素を取得  
        ui_components = self.layout_orchestrator.get_ui_components()  
          
        # 結果表示管理を設定  
        results_controller = self.application_coordinator.get_results_data_controller()  
        if 'results_list' in ui_components:  
            from ResultsDisplayManager import ResultsDisplayManager  
            self.results_display_manager = ResultsDisplayManager(results_controller)  
            self.results_display_manager.set_ui_components(ui_components['results_list'])  
            self.results_display_manager.intervalSelected.connect(self.on_interval_selected)  
          
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
        # ApplicationCoordinatorのシグナル接続  
        self.application_coordinator.videoLoaded.connect(self.on_video_loaded)  
        self.application_coordinator.resultsLoaded.connect(self.on_results_loaded)  
        self.application_coordinator.dataChanged.connect(self.on_data_changed)  
        self.application_coordinator.intervalSelected.connect(self.on_interval_selected)  
          
        # 動画プレイヤーコントローラーの接続  
        self.video_controller.positionChanged.connect(self.on_video_position_changed)  
        self.video_controller.durationChanged.connect(self.on_video_duration_changed)  
          
        # ファイル管理の接続  
        self.file_manager.videoLoaded.connect(self.load_video_from_path)  
        self.file_manager.resultsLoaded.connect(self.load_inference_results_from_path)  
        self.file_manager.resultsSaved.connect(self.on_results_saved)  
          
        # フィルタコントロールの接続  
        if hasattr(self, 'confidence_slider'):  
            self.confidence_slider.valueChanged.connect(self.update_confidence_filter)  
          
        if hasattr(self, 'hand_type_combo'):  
            self.hand_type_combo.currentTextChanged.connect(self.update_hand_type_filter)  
          
        # EditWidgetManagerのシグナル接続  
        self.edit_widget_manager.intervalUpdated.connect(self.on_interval_updated)  
        self.edit_widget_manager.intervalDeleted.connect(self.on_interval_deleted)  
        self.edit_widget_manager.intervalAdded.connect(self.on_interval_added)  
        self.edit_widget_manager.dataChanged.connect(self.on_data_changed)  
      
    def setup_menus(self):  
        """メニューバーの設定"""  
        menubar = self.menuBar()  
          
        # ファイルメニュー  
        file_menu = menubar.addMenu('File')  
          
        open_video_action = QAction('Open Video', self)  
        open_video_action.triggered.connect(lambda: self.file_manager.open_video_dialog(self))  
        file_menu.addAction(open_video_action)  
          
        load_results_action = QAction('Load Inference Results', self)  
        load_results_action.triggered.connect(lambda: self.file_manager.load_inference_results_dialog(self))  
        file_menu.addAction(load_results_action)  
          
        file_menu.addSeparator()  
          
        export_stt_action = QAction('Export STT Dataset', self)  
        export_stt_action.triggered.connect(self.export_stt_dataset)  
        file_menu.addAction(export_stt_action)  
          
        save_results_action = QAction('Save Results', self)  
        save_results_action.triggered.connect(self.save_results)  
        file_menu.addAction(save_results_action)  
          
        # Editメニュー  
        edit_menu = menubar.addMenu('Edit')  
          
        # Undoアクション  
        undo_action = self.undo_stack.createUndoAction(self, "Undo")  
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)  
        undo_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)  
        edit_menu.addAction(undo_action)  
          
        # Redoアクション  
        redo_action = self.undo_stack.createRedoAction(self, "Redo")  
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
          
        # タブ切り替え  
        action_tab_shortcut = QShortcut(QKeySequence("Ctrl+1"), self)  
        action_tab_shortcut.activated.connect(lambda: self.edit_widget_manager.set_current_tab_index(0))  
          
        step_tab_shortcut = QShortcut(QKeySequence("Ctrl+2"), self)  
        step_tab_shortcut.activated.connect(lambda: self.edit_widget_manager.set_current_tab_index(1))  
      
    # イベントハンドラー（ApplicationCoordinatorに委譲）  
    def on_video_loaded(self, video_path: str):  
        """動画読み込み完了時の処理"""  
        print(f"Video loaded: {video_path}")  
      
    def on_results_loaded(self, results):  
        """結果読み込み完了時の処理"""  
        print(f"Results loaded: {len(results)} queries")  
      
    def on_data_changed(self):  
        """データ変更時の処理"""  
        # ApplicationCoordinatorに委譲  
        self.application_coordinator.synchronize_components()  
      
    def on_interval_selected(self, interval, index: int):  
        """区間選択時の処理"""  
        # ApplicationCoordinatorに委譲  
        self.application_coordinator.handle_timeline_interval_clicked(interval, getattr(interval, 'query_result', None))  
      
    def on_video_position_changed(self, position: int):  
        """動画位置変更時の処理"""  
        current_time = position / 1000.0  
        self.application_coordinator.synchronize_video_position(current_time)  
      
    def on_video_duration_changed(self, duration: int):  
        """動画長さ変更時の処理"""  
        if duration > 0:  
            duration_seconds = duration / 1000.0  
            self.application_coordinator.synchronize_video_duration(duration_seconds)  
      
    def on_interval_updated(self):  
        """区間更新時の処理"""  
        self.application_coordinator.handle_edit_events("interval_updated")  
      
    def on_interval_deleted(self):  
        """区間削除時の処理"""  
        self.application_coordinator.handle_edit_events("interval_deleted")  
      
    def on_interval_added(self):  
        """区間追加時の処理"""  
        self.application_coordinator.handle_edit_events("interval_added")  
      
    def on_results_saved(self, file_path: str):  
        """結果保存完了時の処理"""  
        self.file_manager.show_save_success_message(file_path, self)  
      
    # ファイル操作（ApplicationCoordinatorに委譲）  
    def load_video_from_path(self, video_path: str):  
        """動画読み込み"""  
        self.application_coordinator.load_video(video_path)  
      
    def load_inference_results_from_path(self, json_path: str):  
        """推論結果読み込み"""  
        self.application_coordinator.load_inference_results(json_path)  
      
    def save_results(self):  
        """結果保存"""  
        results_controller = self.application_coordinator.get_results_data_controller()  
        if not results_controller.is_results_loaded():  
            self.file_manager.show_no_results_warning(self)  
            return  
          
        file_path = self.file_manager.save_results_dialog(self)  
        if file_path:  
            try:  
                results_controller.save_results(file_path)  
                self.file_manager.show_save_success_message(file_path, self)  
            except Exception as e:  
                self.file_manager.show_save_error_message(str(e), self)  
      
    def export_stt_dataset(self):  
        """STTデータセットエクスポート"""  
        stt_controller = self.application_coordinator.get_stt_data_controller()  
        dataset_info = stt_controller.get_dataset_info()  
          
        if dataset_info['total_videos'] == 0:  
            QMessageBox.warning(self, "Warning", "No video data to export.")  
            return  
          
        # エクスポートダイアログを表示  
        from STTExportDialog import STTExportDialog  
        dialog = STTExportDialog(dataset_info['videos'], self)  
          
        if dialog.exec() == QDialog.DialogCode.Accepted:  
            subset_settings = dialog.get_subset_settings()  
            for video_name, subset in subset_settings.items():  
                stt_controller.update_video_subset(video_name, subset)  
              
            file_path, _ = QFileDialog.getSaveFileName(  
                self, "Export STT Dataset", "stt_dataset.json", "JSON Files (*.json)"  
            )  
              
            if file_path:  
                try:  
                    stt_controller.export_to_json(file_path)  
                    QMessageBox.information(self, "Success", f"STT Dataset exported to {file_path}")  
                except Exception as e:  
                    QMessageBox.critical(self, "Error", f"Failed to export STT Dataset: {str(e)}")  
      
    # フィルタ操作（ApplicationCoordinatorに委譲）  
    def update_confidence_filter(self, value: int):  
        """信頼度フィルタ更新"""  
        threshold = value / 100.0  
        if hasattr(self, 'confidence_value_label'):  
            self.confidence_value_label.setText(f"{threshold:.2f}")  
        self.application_coordinator.set_confidence_threshold(threshold)  
      
    def update_hand_type_filter(self, hand_type: str):  
        """Hand Typeフィルタ更新"""  
        self.application_coordinator.set_hand_type_filter(hand_type)  
      
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
        # EditWidgetManagerの現在のエディターに委譲  
        current_tab = self.edit_widget_manager.get_current_tab_index()  
        if current_tab == 0:  # Action Edit tab  
            self.edit_widget_manager.get_action_editor().delete_interval()  
        elif current_tab == 1:  # Step Edit tab  
            self.edit_widget_manager.get_step_editor().delete_step()  
      
    def keyPressEvent(self, event):  
        """グローバルキーイベント処理"""  
        if event.key() == Qt.Key.Key_Tab:  
            # Tabキーでフォーカス移動  
            self.focusNextChild()  
            event.accept()  
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:  
            # Enterキーで決定  
            focused_widget = self.focusWidget()  
            if hasattr(focused_widget, 'click'):  
                focused_widget.click()  
            event.accept()  
        else:  
            super().keyPressEvent(event)  
      
    def get_current_state(self) -> dict:  
        """現在のアプリケーション状態を取得（デバッグ用）"""  
        return {  
            'application_coordinator_state': self.application_coordinator.get_current_state(),  
            'timeline_manager_state': self.timeline_display_manager.get_current_state(),  
            'edit_manager_state': self.edit_widget_manager.get_current_state(),  
            'layout_state': self.layout_orchestrator.get_layout_state(),  
            'undo_stack_count': self.undo_stack.count(),  
            'undo_stack_index': self.undo_stack.index()  
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