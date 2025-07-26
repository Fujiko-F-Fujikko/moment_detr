# MainApplicationWindow.py (修正版)  
import sys  
import argparse  
from pathlib import Path  
  
from PyQt6.QtWidgets import QMainWindow, QWidget, QApplication, QFileDialog, QMessageBox, QDialog, QComboBox, QPushButton
from PyQt6.QtGui import QAction, QUndoStack, QAction, QKeySequence, QShortcut
from PyQt6.QtCore import Qt
  
from MultiTimelineViewer import MultiTimelineViewer  
from ApplicationController import ApplicationController, FilterController  
from VideoPlayerController import VideoPlayerController  
from ResultsManager import ResultsManager  
from FileManager import FileManager  
from UILayoutManager import UILayoutManager  
from TimelineViewer import TimelineViewer
from STTDataStructures import VideoData
from IntervalModifyCommand import IntervalModifyCommand
from StepModifyCommand import StepModifyCommand
  
# STT関連の新しいクラスをインポート  
from STTDataManager import STTDataManager  
  
class MainApplicationWindow(QMainWindow):  
    def __init__(self):  
        super().__init__()  
        self.setWindowTitle("Moment-DETR Video Annotation Viewer")  
        self.setGeometry(100, 100, 1600, 1000)  

        # Undo/Redoスタックを初期化  
        self.undo_stack = QUndoStack(self)

        # コントローラーを初期化  
        self.video_controller = VideoPlayerController()  
        self.results_manager = ResultsManager()  
        self.file_manager = FileManager()  
        self.ui_layout_manager = UILayoutManager(self)  
        self.app_controller = ApplicationController()  
        self.filter_controller = FilterController(self.app_controller)  
          
        # STT関連の新しいコンポーネント  
        self.stt_data_manager = STTDataManager()  
        self.hand_type_filter_manager = self.ui_layout_manager.hand_type_filter_manager  
        self.integrated_edit_widget = self.ui_layout_manager.integrated_edit_widget  
          
        # STT関連の設定  
        self.integrated_edit_widget.set_stt_data_manager(self.stt_data_manager)  
          
        # UIコンポーネントを設定  
        self.setup_ui()  
        self.setup_connections()  
        self.setup_menus()  
      
    def setup_ui(self):  
        """UIレイアウトの初期化"""  
        # 左パネル（動画プレイヤーとタイムライン）  
        left_panel = self.create_left_panel()  
          
        # 右パネル（コントロールと編集）  
        right_panel, ui_components = self.create_right_panel()  
          
        # UI要素を各コントローラーに設定  
        self.setup_controller_ui_components(ui_components)  
          
        # メインレイアウト（スプリッター使用）  
        main_splitter = self.ui_layout_manager.create_main_layout(left_panel, right_panel)  
          
        # スプリッターを直接セントラルウィジェットに設定  
        self.setCentralWidget(main_splitter)  
      
    def create_left_panel(self) -> QWidget:  
        """左パネル（動画プレイヤーとタイムライン）の作成"""  
        # 複数タイムラインビューア  
        self.multi_timeline_viewer = MultiTimelineViewer()  
          
        # 動画コントローラーからUIコンポーネントを取得  
        video_widget = self.video_controller.get_video_widget()  
        controls_layout = self.video_controller.get_controls_layout()  
          
        return self.ui_layout_manager.create_left_panel(  
            video_widget, controls_layout, self.multi_timeline_viewer  
        )  
      
    def create_right_panel(self) -> tuple[QWidget, dict]:  
        """右パネル（コントロールと編集）の作成"""  
        return self.ui_layout_manager.create_right_panel()  

    def setup_controller_ui_components(self, ui_components: dict):  
        """各コントローラーにUI要素を設定"""  
        print(f"DEBUG: UI components keys: {list(ui_components.keys())}")  
        
        if 'results_list' in ui_components:  
            print("DEBUG: Setting results_list for ResultsManager")  
            print(f"DEBUG: results_list: {ui_components.get('results_list')}")

            self.results_manager.set_ui_components(  
                ui_components.get('hand_type_combo'),  
                ui_components.get('results_list')
            )  
        else:  
            print("DEBUG: results_list not found in ui_components!")
          
        # IntegratedEditWidgetにUI要素を設定  
        self.integrated_edit_widget.set_stt_data_manager(self.stt_data_manager)  
          
        # フィルタ関連のUI要素を保存（Saliency Threshold削除）  
        if 'confidence_slider' in ui_components:  
            self.confidence_slider = ui_components['confidence_slider']  
            self.confidence_value_label = ui_components['confidence_value_label']  
          
        # Hand Type Filter Managerとの接続  
        self.hand_type_filter_manager.filterChanged.connect(self.on_hand_type_filter_changed)  
            
    def setup_connections(self):  
        """シグナル・スロット接続の設定"""  
        # 動画プレイヤーコントローラーの接続  
        self.video_controller.positionChanged.connect(self.on_video_position_changed)  
        self.video_controller.durationChanged.connect(self.on_video_duration_changed)  
    
        # Hand Type Filter Managerの接続  
        self.hand_type_filter_manager.filterChanged.connect(self.on_hand_type_filter_changed)  
    
        # 結果管理の接続（hand type filter対応）  
        self.results_manager.intervalSelected.connect(self.on_interval_selected)  
        self.results_manager.resultsUpdated.connect(self.on_results_updated)  
    
        # 統合編集ウィジェットの接続  
        self.integrated_edit_widget.intervalUpdated.connect(self.on_interval_updated)  
        self.integrated_edit_widget.intervalDeleted.connect(self.on_interval_deleted)  
        self.integrated_edit_widget.intervalAdded.connect(self.on_interval_added)  
        self.integrated_edit_widget.dataChanged.connect(self.on_stt_data_changed)  
    
        # ファイル管理の接続  
        self.file_manager.videoLoaded.connect(self.load_video_from_path)  
        self.file_manager.resultsLoaded.connect(self.load_inference_results_from_path)  
        self.file_manager.resultsSaved.connect(self.on_results_saved)  
    
        # 信頼度フィルタ接続（Saliency Threshold削除）  
        if hasattr(self, 'confidence_slider'):  
            self.confidence_slider.valueChanged.connect(self.update_confidence_filter)  
            self.confidence_slider.valueChanged.connect(  
                lambda v: self.filter_controller.set_confidence_threshold(v / 100.0)  
            )  
    
        # 複数タイムラインからの区間クリックを接続  
        self.multi_timeline_viewer.intervalClicked.connect(self.on_timeline_interval_clicked)
  
        # タイムラインドラッグイベントの接続を追加  
        self.multi_timeline_viewer.intervalClicked.connect(self.on_timeline_interval_clicked)  
        
        # 新しいドラッグイベントの接続（MultiTimelineViewerに伝播させる）  
        self.multi_timeline_viewer.intervalDragStarted.connect(self.on_interval_drag_started)  
        self.multi_timeline_viewer.intervalDragMoved.connect(self.on_interval_drag_moved)  
        self.multi_timeline_viewer.intervalDragFinished.connect(self.on_interval_drag_finished)  
        self.multi_timeline_viewer.newIntervalCreated.connect(self.on_new_interval_created)

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
        save_results_action = QAction('Save Results', self)    
        save_results_action.triggered.connect(self.save_results)    
  

        file_menu.addAction(export_stt_action)  
        file_menu.addAction(save_results_action)  
          
        # Editメニュー
        edit_menu = menubar.addMenu('Edit')  
        
        # Undoアクション  
        undo_action = self.undo_stack.createUndoAction(self, "Undo")  
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)  # Ctrl+Z 
        undo_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut) 
        edit_menu.addAction(undo_action)  
        
        # Redoアクション    
        redo_action = self.undo_stack.createRedoAction(self, "Redo")  
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)  # Ctrl+Y 
        redo_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut) 
        edit_menu.addAction(redo_action)  
        
        edit_menu.addSeparator()  

        # ファイル操作のショートカット  
        open_video_action.setShortcut(QKeySequence.StandardKey.Open)  
        save_results_action.setShortcut(QKeySequence.StandardKey.Save)  
        
        # カスタムショートカット          
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
        delete_shortcut.activated.connect(self.integrated_edit_widget.delete_interval) 
        
        # タブ切り替え  
        action_tab_shortcut = QShortcut(QKeySequence("Ctrl+1"), self)  
        action_tab_shortcut.activated.connect(lambda: self.integrated_edit_widget.tab_widget.setCurrentIndex(0))
        step_tab_shortcut = QShortcut(QKeySequence("Ctrl+2"), self)  
        step_tab_shortcut.activated.connect(lambda: self.integrated_edit_widget.tab_widget.setCurrentIndex(1))

    # 新しいイベントハンドラー  
    def on_video_position_changed(self, position: int):  
        """動画位置が変更された時の処理"""  
        current_time = position / 1000.0  
        self.multi_timeline_viewer.update_playhead_position(current_time)  
          
    def on_video_duration_changed(self, duration: int):  
        """動画の長さが変更された時の処理"""  
        if duration > 0:  
            duration_seconds = duration / 1000.0  
            self.multi_timeline_viewer.set_video_duration(duration_seconds)  
            if self.results_manager.get_all_results():  
                self.update_timeline_with_steps(self.results_manager.get_all_results())
                
    def highlight_interval_on_timeline(self, interval):  
        """タイムライン上で指定された区間をハイライト"""  
        # 全てのタイムラインで該当する区間をハイライト  
        for widget in self.multi_timeline_viewer.timeline_widgets:  
            timeline = widget.findChild(TimelineViewer)  
            if timeline:  
                timeline.set_highlighted_interval(interval)

    def on_interval_updated(self):  
        """区間が更新された時の処理"""  
        self.results_manager.update_results_display()  
        self.update_display()  
          
    def on_interval_deleted(self):  
        """区間が削除された時の処理"""  
        self.results_manager.update_results_display()  
        self.update_display()  
          
    def on_interval_added(self):  
        """区間が追加された時の処理"""  
        self.results_manager.update_results_display()  
        self.update_display()  
          
    def on_results_saved(self, file_path: str):  
        """結果が保存された時の処理"""  
        self.file_manager.show_save_success_message(file_path, self)  
      
    def on_stt_data_changed(self):  
        """STTデータが変更された時の処理"""  
        # Timelineを更新してStepsの変更を反映  
        self.update_timeline_with_steps(self.results_manager.get_all_results())

    def save_results(self):    
        """編集された結果を保存"""    
        if not self.results_manager.get_all_results():    
            self.file_manager.show_no_results_warning(self)  
            return    
                
        file_path = self.file_manager.save_results_dialog(self)  
        if file_path:    
            try:    
                self.results_manager.save_results(file_path)  
                self.file_manager.show_save_success_message(file_path, self)  
                    
            except Exception as e:    
                self.file_manager.show_save_error_message(str(e), self)  
      
    def export_stt_dataset(self):  
        """STT Dataset形式でエクスポート（ダイアログ付き）"""  
        if not self.stt_data_manager.stt_dataset.database:  
            QMessageBox.warning(self, "Warning", "No video data to export.")  
            return  
          
        # エクスポートダイアログを表示  
        from STTExportDialog import STTExportDialog  
        video_names = list(self.stt_data_manager.stt_dataset.database.keys())  
        dialog = STTExportDialog(video_names, self)  
          
        if dialog.exec() == QDialog.DialogCode.Accepted:  
            # ダイアログで設定されたsubset情報を適用  
            subset_settings = dialog.get_subset_settings()  
            for video_name, subset in subset_settings.items():  
                self.stt_data_manager.update_video_subset(video_name, subset)  
              
            # ファイル保存ダイアログ  
            file_path, _ = QFileDialog.getSaveFileName(  
                self,   
                "Export STT Dataset",   
                "stt_dataset.json",   
                "JSON Files (*.json)"  
            )  
              
            if file_path:  
                try:  
                    self.stt_data_manager.export_to_json(file_path)  
                    QMessageBox.information(self, "Success", f"STT Dataset exported to {file_path}")  
                except Exception as e:  
                    QMessageBox.critical(self, "Error", f"Failed to export STT Dataset: {str(e)}")  
  
    def load_video_from_path(self, video_path: str):    
        """指定されたパスから動画を読み込む"""    
        if not self.file_manager.validate_video_file(video_path):  
            return  
        try:    
            self.video_controller.load_video(video_path)  
            # ApplicationControllerにも動画情報を設定  
            video_info = self.app_controller.load_video(video_path)  
              
            # STTデータマネージャーに動画データを追加  
            if video_info:  
                self.stt_data_manager.add_video_data(video_info)  
                video_name = Path(video_path).stem  
                self.integrated_edit_widget.set_current_video(video_name)  
                  
        except Exception as e:    
            self.file_manager.show_load_error_message(str(e), self)  
      
    def load_inference_results_from_path(self, json_path: str):      
        """指定されたパスから推論結果を読み込む"""      
        if not self.file_manager.validate_json_file(json_path):  
            return  
        try:      
            self.results_manager.load_inference_results(json_path)  
            # 動画の長さが既に取得されている場合のみ設定      
            duration_seconds = self.video_controller.get_duration_seconds()  
            if duration_seconds > 0:      
                self.multi_timeline_viewer.set_video_duration(duration_seconds)      
        except Exception as e:      
            self.file_manager.show_load_error_message(str(e), self)  
    
    def apply_filters(self):    
        """フィルタを適用して表示を更新"""    
        if not self.results_manager.get_all_results():    
            return    
          
        # フィルタされた結果を取得してタイムラインビューアに設定  
        filtered_results = self.results_manager.get_filtered_results()  
        self.update_timeline_with_steps(filtered_results)
  
    def update_display(self):    
        """表示を更新"""    
        if hasattr(self, 'multi_timeline_viewer') and self.results_manager.get_all_results():      
            # 現在の動画再生位置を取得  
            current_position = self.video_controller.get_position_seconds()  
            
            # 全ての推論結果を再設定してタイムラインを更新      
            self.update_timeline_with_steps(self.results_manager.get_all_results())
                
            # 動画の長さも再設定      
            duration_seconds = self.video_controller.get_duration_seconds()    
            if duration_seconds > 0:      
                self.multi_timeline_viewer.set_video_duration(duration_seconds)  
                
            # 再生位置を復元  
            if current_position > 0:  
                self.multi_timeline_viewer.update_playhead_position(current_position)
      
    def on_hand_type_filter_changed(self):  
        """Hand Typeフィルタが変更された時の処理"""  
        filtered_results = self.hand_type_filter_manager.get_filtered_results()  
        self.results_manager.update_filtered_results(filtered_results)  
        self.update_timeline_with_steps(filtered_results)
      
    def on_interval_selected(self, interval, index: int):    
        """区間が選択された時の処理（統合編集ウィジェット対応）"""    
        # 統合編集ウィジェットに選択された区間を設定    
        if hasattr(interval, 'query_result') and interval.query_result:    
            self.integrated_edit_widget.set_current_query_results(interval.query_result)    
            self.integrated_edit_widget.set_selected_interval(interval, index)    
        
        # Timeline上で区間をハイライト
        self.highlight_interval_on_timeline(interval)  
            
        # 動画をその位置にシーク    
        self.video_controller.seek_to_time(interval.start_time)

    def get_current_video_name(self):  
        """現在のビデオ名を取得"""  
        if self.app_controller.video_info:  
            return Path(self.app_controller.video_info.file_path).stem  
        return None  
    
    def update_timeline_with_steps(self, results):  
        """Stepsデータとともにタイムラインを更新"""  
        if hasattr(self, 'multi_timeline_viewer') and results: 
            video_name = self.get_current_video_name()  
            self.multi_timeline_viewer.set_query_results(  
                results,   
                self.stt_data_manager,   
                video_name  
            )
        else:  
            print("DEBUG: multi_timeline_viewer or results is None, skipping update")

    def on_results_updated(self, results):  
        """結果が更新された時の処理（Hand Type Filter対応）"""  
        # Hand Type Filter Managerに結果を設定  
        self.hand_type_filter_manager.set_results(results)  
        
        self.update_timeline_with_steps(results)

        # STTデータマネージャーに推論結果を追加  
        if self.app_controller.video_info:  
            video_name = Path(self.app_controller.video_info.file_path).stem  
            self.stt_data_manager.add_inference_results(video_name, results)  
            self.integrated_edit_widget.set_current_video(video_name)  
      
    def on_timeline_interval_clicked(self, interval, query_result):    
        """タイムライン上の区間がクリックされた時の処理（統合編集ウィジェット対応）"""    
        print(f"DEBUG: Timeline interval clicked - query_text: {query_result.query_text}")  
        
        # Stepかどうかを判定  
        if hasattr(query_result, 'query_text') and query_result.query_text.startswith("Step:"):  
            print("DEBUG: This is a Step interval click")  
            self.debug_undo_stack("BEFORE Step interval click processing")  
        
        # 統合編集ウィジェットに選択された区間を設定    
        self.integrated_edit_widget.set_current_query_results(query_result)              

        # 区間のインデックスを特定  
        if hasattr(query_result, 'relevant_windows'):  
            try:  
                index = query_result.relevant_windows.index(interval)  
                self.integrated_edit_widget.set_selected_interval(interval, index)  
            except ValueError:  
                self.integrated_edit_widget.set_selected_interval(interval, 0)  

        # 適切なタブに自動切り替え（ステップ選択も含む） 
        self.integrated_edit_widget.switch_to_appropriate_tab(interval)            

        # Detection Resultsリストで該当する区間を選択  
        self.results_manager.select_interval_in_list(interval)

        # Timeline上で区間をハイライト
        self.highlight_interval_on_timeline(interval) 
        # Detection Resultsリストで該当する区間を選択
        self.results_manager.select_interval_in_list(interval)  

        # 動画をその位置にシーク  
        self.video_controller.seek_to_time(interval.start_time)  
      
    def update_confidence_filter(self, value: int):        
        """信頼度フィルタを更新（Saliency Threshold削除対応）"""        
        # 1. まずHand Type Filter Managerの結果を適用    
        filtered_results = self.hand_type_filter_manager.get_filtered_results()    
        self.results_manager.update_filtered_results(filtered_results)  
        self.update_timeline_with_steps(filtered_results)
 
        # 2. 次に信頼度フィルタを適用(Timelineインスタンスがが再生成されたあとに適用)
        threshold = value / 100.0        
        if hasattr(self, 'confidence_value_label'):    
            self.confidence_value_label.setText(f"{threshold:.2f}")      
        self.results_manager.set_confidence_threshold(threshold)    
        self.multi_timeline_viewer.set_confidence_threshold(threshold)

    def on_timeline_interval_drag_finished(self, interval, new_start, new_end):  
        """タイムライン上でのドラッグ完了時の処理"""  
        print(f"DEBUG: MainApp - Interval drag finished: {interval.start_time}-{interval.end_time} -> {new_start}-{new_end}")  
        
        # 区間データを更新  
        interval.start_time = new_start  
        interval.end_time = new_end  
        
        # IntegratedEditWidgetに変更を通知  
        if hasattr(interval, 'query_result') and interval.query_result:  
            self.integrated_edit_widget.set_current_query_results(interval.query_result)  
            # 区間のインデックスを特定  
            if hasattr(interval.query_result, 'relevant_windows'):  
                try:  
                    index = interval.query_result.relevant_windows.index(interval)  
                    self.integrated_edit_widget.set_selected_interval(interval, index)  
                except ValueError:  
                    pass  
        
        # 表示を更新  
        self.update_display()

    def on_interval_drag_started(self, interval):  
        """ドラッグ開始時の処理"""  
        print(f"DEBUG: MainApp - Drag started for interval {interval.start_time}-{interval.end_time}")  
        
        # Store original values for undo functionality  
        self.drag_original_start = interval.start_time  
        self.drag_original_end = interval.end_time  
        self.dragging_interval = interval

    def on_interval_drag_moved(self, interval, new_start, new_end):  
        """ドラッグ中の処理"""  
        # リアルタイムでIntegratedEditWidgetのスピンボックスを更新  
        if hasattr(interval, 'query_result') and interval.query_result:  
            self.integrated_edit_widget.set_current_query_results(interval.query_result)  
            try:  
                index = interval.query_result.relevant_windows.index(interval)  
                self.integrated_edit_widget.set_selected_interval(interval, index)  
            except ValueError:  
                pass  
        # Stepの区間の場合は、Step Editタブのスピンボックスも更新  
        if (hasattr(interval.query_result, 'query_text') and   
            interval.query_result.query_text.startswith("Step:")):  
            # Step Editタブのスピンボックスを直接更新  
            self.integrated_edit_widget.step_start_spin.setValue(new_start)  
            self.integrated_edit_widget.step_end_spin.setValue(new_end)

    def on_interval_drag_finished(self, interval, new_start, new_end):  
        """ドラッグ完了時の処理"""  
        print(f"DEBUG: MainApp - Drag finished: {interval.start_time}-{interval.end_time} -> {new_start}-{new_end}")  

        # デバッグ：変更前のスタック状態  
        self.debug_undo_stack("BEFORE drag finished")  

        # Use the stored original values instead of current values  
        old_start = getattr(self, 'drag_original_start', interval.start_time)  
        old_end = getattr(self, 'drag_original_end', interval.end_time)  
        
        print(f"DEBUG: Using original values: {old_start}-{old_end} -> {new_start}-{new_end}")  
        
        # Rest of the existing code...  
        if (hasattr(interval, 'query_result') and   
            hasattr(interval.query_result, 'query_text') and   
            interval.query_result.query_text.startswith("Step:")):  
            
            print(f"DEBUG: Creating StepModifyCommand")  
            command = StepModifyCommand(interval, old_start, old_end, new_start, new_end,   
                                    self.stt_data_manager, self.get_current_video_name(), self)  
            self.undo_stack.push(command)  
            self.debug_undo_stack("AFTER StepModifyCommand")  
        else:  
            print(f"DEBUG: Creating IntervalModifyCommand")  
            command = IntervalModifyCommand(interval, old_start, old_end, new_start, new_end, self)  
            self.undo_stack.push(command)  
            self.debug_undo_stack("AFTER IntervalModifyCommand")
        
        # Clean up stored values  
        self.drag_original_start = None  
        self.drag_original_end = None  
        self.dragging_interval = None

    def on_new_interval_created(self, start_time: float, end_time: float, timeline_type: str):  
        """新規区間作成時の処理"""  
        print(f"DEBUG: MainApp - New interval created: {start_time}-{end_time} on {timeline_type} timeline")  
        
        # タイムライン種別に応じて適切なクエリ結果を選択  
        current_query_result = None  
        
        if timeline_type == "Steps":  
            # Stepsタイムラインの場合の処理  
            video_name = self.get_current_video_name()  
            if not video_name or not self.stt_data_manager:  
                print("DEBUG: No video or STT data manager available for step creation")  
                return  
            
            # デフォルトのステップテキストを生成  
            step_text = f"New Step {len(self.stt_data_manager.stt_dataset.database.get(video_name, VideoData()).steps) + 1}"  
            segment = [start_time, end_time]  
            
            # StepAddCommandを使用してUndo/Redo対応で追加  
            from StepModifyCommand import StepAddCommand  
            command = StepAddCommand(self.stt_data_manager, video_name, step_text, segment, self)  
            self.undo_stack.push(command)  
            return  
        else:  
            # 手の種類に対応するクエリ結果を検索  
            all_results = self.results_manager.get_all_results()  
            for result in all_results:  
                try:  
                    from STTDataStructures import QueryParser  
                    hand_type, _ = QueryParser.validate_and_parse_query(result.query_text)  
                    if hand_type == timeline_type:  
                        current_query_result = result  
                        break  
                except:  
                    continue  
        
        if not current_query_result:  
            print(f"DEBUG: No query result found for timeline type: {timeline_type}")  
            return  
        
        # 新しい区間を作成  
        from DetectionInterval import DetectionInterval  
        new_interval = DetectionInterval(  
            start_time=start_time,  
            end_time=end_time,  
            confidence_score=1.0,  
            query_id=current_query_result.query_id  
        )  
        new_interval.query_result = current_query_result  
        
        # Undoコマンドを作成してスタックにプッシュ  
        from IntervalModifyCommand import IntervalAddCommand  
        command = IntervalAddCommand(current_query_result, new_interval, self)  
        self.undo_stack.push(command)

    def seek_relative(self, seconds: float):  
        """現在位置から相対的にシーク"""  
        current_position = self.video_controller.get_position_seconds()  
        new_position = max(0, current_position + seconds)  
        duration = self.video_controller.get_duration_seconds()  
        if duration > 0:  
            new_position = min(new_position, duration)  
        self.video_controller.seek_to_time(new_position)

    def keyPressEvent(self, event):  
        """グローバルキーイベント処理"""  
        if event.key() == Qt.Key.Key_Tab:  
            # Tabキーでフォーカス移動  
            self.focusNextChild()  
            event.accept()  
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:  
            # Enterキーで決定  
            focused_widget = self.focusWidget()  
            if isinstance(focused_widget, QPushButton):  
                focused_widget.click()  
            elif isinstance(focused_widget, QComboBox):  
                # コンボボックスの場合はドロップダウンを開く  
                focused_widget.showPopup()  
            event.accept()  
        else:  
            super().keyPressEvent(event)

    def debug_undo_stack(self, operation_name=""):  
        """Undo/Redoスタックの状態をデバッグ出力"""  
        print(f"\n=== UNDO STACK DEBUG ({operation_name}) ===")  
        print(f"Stack count: {self.undo_stack.count()}")  
        print(f"Current index: {self.undo_stack.index()}")  
        print(f"Can undo: {self.undo_stack.canUndo()}")  
        print(f"Can redo: {self.undo_stack.canRedo()}")  
        
        # スタック内の全コマンドを表示  
        for i in range(self.undo_stack.count()):  
            command = self.undo_stack.command(i)  
            status = "CURRENT" if i == self.undo_stack.index() else "DONE" if i < self.undo_stack.index() else "UNDONE"  
            print(f"  [{i}] {status}: {command.text()} ({type(command).__name__})")  
        print("=" * 50)

def parse_arguments():    
    """コマンドライン引数を解析"""    
    parser = argparse.ArgumentParser(description='Moment-DETR Video Annotation Viewer')    
    parser.add_argument('--video', type=str, help='Path to video file')    
    parser.add_argument('--json', type=str, help='Path to inference results JSON file')    
    return parser.parse_args()    
    
if __name__ == '__main__':    
    app = QApplication(sys.argv)    
        
    # コマンドライン引数を解析    
    args = parse_arguments()    
        
    window = MainApplicationWindow()    
    window.show()  # ウィンドウを表示してからファイルを読み込む    
        
    # UI初期化完了後にファイルを読み込み    
    if args.video:    
        window.load_video_from_path(args.video)    
        
    if args.json:    
        window.load_inference_results_from_path(args.json)    
        
    sys.exit(app.exec())