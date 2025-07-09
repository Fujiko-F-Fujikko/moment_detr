# MainApplicationWindow.py (修正版)  
import sys  
import os  
import argparse  
from pathlib import Path  
  
from PyQt6.QtWidgets import QMainWindow, QWidget, QApplication, QFileDialog, QMessageBox, QDialog
from PyQt6.QtGui import QAction  
from PyQt6.QtCore import pyqtSlot  
  
from MultiTimelineViewer import MultiTimelineViewer  
from ApplicationController import ApplicationController, FilterController  
  
# 新しく分離したクラスをインポート  
from VideoPlayerController import VideoPlayerController  
from ResultsManager import ResultsManager  
from FileManager import FileManager  
from UILayoutManager import UILayoutManager  
  
# STT関連の新しいクラスをインポート  
from STTDataManager import STTDataManager  
from HandTypeFilterManager import HandTypeFilterManager  
from IntegratedEditWidget import IntegratedEditWidget  
  
class MainApplicationWindow(QMainWindow):  
    def __init__(self):  
        super().__init__()  
        self.setWindowTitle("Moment-DETR Video Annotation Viewer")  
        self.setGeometry(100, 100, 1600, 1000)  
          
        # コントローラーを初期化  
        self.video_controller = VideoPlayerController()  
        self.results_manager = ResultsManager()  
        self.file_manager = FileManager()  
        self.ui_layout_manager = UILayoutManager()  
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
            
        save_results_action = QAction('Save Results', self)    
        save_results_action.triggered.connect(self.save_results)    
        file_menu.addAction(save_results_action)  
          
        # STTメニュー  
        stt_menu = menubar.addMenu('STT Dataset')  
          
        export_stt_action = QAction('Export STT Dataset', self)  
        export_stt_action.triggered.connect(self.export_stt_dataset)  
        stt_menu.addAction(export_stt_action)  
          
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
                self.multi_timeline_viewer.set_query_results(self.results_manager.get_all_results())  
      
    def on_hand_type_filter_changed(self):  
        """Hand Typeフィルタが変更された時の処理"""  
        filtered_results = self.hand_type_filter_manager.get_filtered_results()  
        self.results_manager.update_filtered_results(filtered_results)  
        self.multi_timeline_viewer.set_query_results(filtered_results)  
          
    def on_interval_selected(self, interval, index: int):  
        """区間が選択された時の処理"""  
        print(f"DEBUG: MainApp - on_interval_selected called with interval {interval.start_time}-{interval.end_time}")  
        
        # 統合編集ウィジェットに選択された区間を設定  
        if hasattr(interval, 'query_result') and interval.query_result:  
            print(f"DEBUG: MainApp - Setting query result: {interval.query_result.query_text}")  
            self.integrated_edit_widget.set_current_query_results(interval.query_result)  
            self.integrated_edit_widget.set_selected_interval(interval, index)  
        
        # 動画をその位置にシーク  
        print(f"DEBUG: MainApp - Seeking to time: {interval.start_time}")  
        self.video_controller.seek_to_time(interval.start_time)

    def highlight_interval_on_timeline(self, interval, query_result):  
        """タイムライン上で指定された区間をハイライト"""  
        # MultiTimelineViewerに選択状態を通知  
        if hasattr(self.multi_timeline_viewer, 'highlight_interval'):  
            self.multi_timeline_viewer.highlight_interval(interval, query_result)

    def on_results_updated(self, results):  
        """結果が更新された時の処理"""  
        # Hand Type Filter Managerに結果を設定  
        self.hand_type_filter_manager.set_results(results)  
          
        # タイムラインビューアを更新  
        self.multi_timeline_viewer.set_query_results(results)  
          
        # STTデータマネージャーに推論結果を追加  
        if self.app_controller.video_info:  
            video_name = Path(self.app_controller.video_info.video_path).stem  
            self.stt_data_manager.add_inference_results(video_name, results)  
            self.integrated_edit_widget.set_current_video(video_name)  
          
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
        # 必要に応じて他のUIコンポーネントを更新  
        pass  
  
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
  
    def update_confidence_filter(self, value: int):      
        """信頼度フィルタを更新"""      
        threshold = value / 100.0      
        if hasattr(self, 'confidence_value_label'):  
            self.confidence_value_label.setText(f"{threshold:.2f}")    
        self.results_manager.set_confidence_threshold(threshold)  
        self.apply_filters()  
  
    def apply_filters(self):    
        """フィルタを適用して表示を更新"""    
        if not self.results_manager.get_all_results():    
            return    
          
        # フィルタされた結果を取得してタイムラインビューアに設定  
        filtered_results = self.results_manager.get_filtered_results()  
        self.multi_timeline_viewer.set_query_results(filtered_results)  
  
    def update_display(self):    
        """表示を更新"""    
        if hasattr(self, 'multi_timeline_viewer') and self.results_manager.get_all_results():    
            # 全ての推論結果を再設定してタイムラインを更新    
            self.multi_timeline_viewer.set_query_results(self.results_manager.get_all_results())    
                
            # 動画の長さも再設定    
            duration_seconds = self.video_controller.get_duration_seconds()  
            if duration_seconds > 0:    
                self.multi_timeline_viewer.set_video_duration(duration_seconds)  
  
    def on_timeline_interval_clicked(self, interval, query_result):  
        """タイムライン上の区間がクリックされた時の処理"""  
        print(f"DEBUG: MainApp - Timeline interval clicked: {interval.start_time}-{interval.end_time}")  
        print(f"DEBUG: MainApp - Query result: {query_result.query_text if hasattr(query_result, 'query_text') else 'No query_text'}")  
        
        # 統合編集ウィジェットに選択された区間を設定  
        self.integrated_edit_widget.set_current_query_results(query_result)  
        
        # 区間のインデックスを特定  
        if hasattr(query_result, 'relevant_windows'):  
            try:  
                index = query_result.relevant_windows.index(interval)  
                print(f"DEBUG: MainApp - Found interval at index: {index}")  
                self.integrated_edit_widget.set_selected_interval(interval, index)  
            except ValueError:  
                print(f"DEBUG: MainApp - Interval not found in relevant_windows, using index 0")  
                self.integrated_edit_widget.set_selected_interval(interval, 0)  
        
        # 動画をその位置にシーク  
        self.video_controller.seek_to_time(interval.start_time)

    def setup_connections(self):    
        """シグナル・スロット接続の設定（第2段階）"""    
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
      
    def on_hand_type_filter_changed(self):  
        """Hand Typeフィルタが変更された時の処理"""  
        filtered_results = self.hand_type_filter_manager.get_filtered_results()  
        self.results_manager.update_filtered_results(filtered_results)  
        self.multi_timeline_viewer.set_query_results(filtered_results)  
      
    def on_interval_selected(self, interval, index: int):  
        """区間が選択された時の処理（統合編集ウィジェット対応）"""  
        # 統合編集ウィジェットに選択された区間を設定  
        if hasattr(interval, 'query_result') and interval.query_result:  
            self.integrated_edit_widget.set_current_query_results(interval.query_result)  
            self.integrated_edit_widget.set_selected_interval(interval, index)  
          
        # 動画をその位置にシーク  
        self.video_controller.seek_to_time(interval.start_time)  
      
    def on_results_updated(self, results):  
        """結果が更新された時の処理（Hand Type Filter対応）"""  
        # Hand Type Filter Managerに結果を設定  
        self.hand_type_filter_manager.set_results(results)  
          
        # タイムラインビューアを更新  
        self.multi_timeline_viewer.set_query_results(results)  
          
        # STTデータマネージャーに推論結果を追加  
        if self.app_controller.video_info:  
            video_name = Path(self.app_controller.video_info.file_path).stem  
            self.stt_data_manager.add_inference_results(video_name, results)  
            self.integrated_edit_widget.set_current_video(video_name)  
      
    def on_timeline_interval_clicked(self, interval, query_result):    
        """タイムライン上の区間がクリックされた時の処理（統合編集ウィジェット対応）"""    
        # 統合編集ウィジェットに選択された区間を設定  
        self.integrated_edit_widget.set_current_query_results(query_result)  
          
        # 区間のインデックスを特定  
        if hasattr(query_result, 'relevant_windows'):  
            try:  
                index = query_result.relevant_windows.index(interval)  
                self.integrated_edit_widget.set_selected_interval(interval, index)  
            except ValueError:  
                self.integrated_edit_widget.set_selected_interval(interval, 0)  
          
        # 動画をその位置にシーク  
        self.video_controller.seek_to_time(interval.start_time)  
      
    def update_confidence_filter(self, value: int):      
        """信頼度フィルタを更新（Saliency Threshold削除対応）"""      
        threshold = value / 100.0      
        if hasattr(self, 'confidence_value_label'):  
            self.confidence_value_label.setText(f"{threshold:.2f}")    
        self.results_manager.set_confidence_threshold(threshold)  
          
        # Hand Type Filter Managerの結果を再適用  
        filtered_results = self.hand_type_filter_manager.get_filtered_results()  
        self.results_manager.update_filtered_results(filtered_results)

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