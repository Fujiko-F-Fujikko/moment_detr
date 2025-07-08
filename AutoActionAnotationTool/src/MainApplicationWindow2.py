import sys    
import argparse  
from pathlib import Path
  
from PyQt6.QtWidgets import QMainWindow, QWidget, QApplication, QFileDialog, QMessageBox, QDialog
from PyQt6.QtGui import QAction  
  
from MultiTimelineViewer import MultiTimelineViewer  
from ApplicationController import ApplicationController, FilterController  
  
from VideoPlayerController import VideoPlayerController  
from ResultsManager import ResultsManager  
from IntervalEditController import IntervalEditController  
from FileManager import FileManager  
from UILayoutManager import UILayoutManager  
  
from STTDataManager import STTDataManager  
from STTEditWidget import STTEditWidget  
from STTExportDialog import STTExportDialog
  
class MainApplicationWindow(QMainWindow):    
    def __init__(self):    
        super().__init__()    
        self.setWindowTitle("Moment-DETR Video Annotation Viewer")    
        self.setGeometry(100, 100, 1600, 1000)  # ウィンドウサイズを拡大  
            
        # コントローラーを初期化    
        self.video_controller = VideoPlayerController()    
        self.results_manager = ResultsManager()    
        self.interval_edit_controller = IntervalEditController()    
        self.file_manager = FileManager()    
        self.ui_layout_manager = UILayoutManager()    
        self.app_controller = ApplicationController()    
        self.filter_controller = FilterController(self.app_controller)    
          
        # STT関連の新しいコンポーネント  
        self.stt_data_manager = STTDataManager()  
        self.stt_edit_widget = STTEditWidget()  
        self.stt_edit_widget.set_stt_data_manager(self.stt_data_manager)  
            
        # UIコンポーネントを設定（これを先に完了させる）    
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
        
        # 3パネル構成のスプリッターを作成  
        main_splitter = self.ui_layout_manager.create_main_layout(  
            left_panel, right_panel, self.stt_edit_widget  
        )  
        
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
        # UI要素の存在確認  
        if 'query_combo' not in ui_components:  
            return  
        if 'results_list' not in ui_components:  
            return  
        if 'confidence_label' not in ui_components:  
            return  
        # ResultsManagerにUI要素を設定  
        self.results_manager.set_ui_components(  
            ui_components['query_combo'],  
            ui_components['results_list'],  
            ui_components['confidence_label']  
        )  
        # IntervalEditControllerにUI要素を設定  
        self.interval_edit_controller.set_ui_components(  
            ui_components['start_spinbox'],  
            ui_components['end_spinbox'],  
            ui_components['confidence_label'],  
            ui_components['apply_button'],  
            ui_components['delete_button'],  
            ui_components['add_button']  
        )  
        # フィルタ関連のUI要素を保存  
        self.confidence_slider = ui_components['confidence_slider']  
        self.confidence_value_label = ui_components['confidence_value_label']  
        self.threshold_slider = ui_components['threshold_slider']  
        self.threshold_value_label = ui_components['threshold_value_label']  
            
    def setup_connections(self):    
        """シグナル・スロット接続の設定"""    
        # 動画プレイヤーコントローラーの接続  
        self.video_controller.positionChanged.connect(self.on_video_position_changed)  
        self.video_controller.durationChanged.connect(self.on_video_duration_changed)  
          
        # 結果管理の接続  
        self.results_manager.querySelected.connect(self.on_query_selected)  
        self.results_manager.intervalSelected.connect(self.on_interval_selected)  
        self.results_manager.resultsUpdated.connect(self.on_results_updated)  
          
        # 区間編集の接続  
        self.interval_edit_controller.intervalUpdated.connect(self.on_interval_updated)  
        self.interval_edit_controller.intervalDeleted.connect(self.on_interval_deleted)  
        self.interval_edit_controller.intervalAdded.connect(self.on_interval_added)  
          
        # ファイル管理の接続  
        self.file_manager.videoLoaded.connect(self.load_video_from_path)  
        self.file_manager.resultsLoaded.connect(self.load_inference_results_from_path)  
        self.file_manager.resultsSaved.connect(self.on_results_saved)  
            
        # 閾値スライダー    
        self.threshold_slider.valueChanged.connect(self.update_saliency_threshold)    
        self.confidence_slider.valueChanged.connect(self.update_confidence_filter)    
          
        # フィルタ接続    
        self.threshold_slider.valueChanged.connect(    
            lambda v: self.filter_controller.set_saliency_threshold(v / 100.0)    
        )  
        self.confidence_slider.valueChanged.connect(    
            lambda v: self.filter_controller.set_confidence_threshold(v / 100.0)    
        )  
  
        # 複数タイムラインからの区間クリックを接続    
        self.multi_timeline_viewer.intervalClicked.connect(self.on_timeline_interval_clicked)  
          
        # STT関連の接続  
        self.stt_edit_widget.dataChanged.connect(self.on_stt_data_changed)  
  
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
          
        # STTメニューを追加  
        stt_menu = menubar.addMenu('STT Dataset')  
          
        export_stt_action = QAction('Export STT Dataset', self)  
        export_stt_action.triggered.connect(self.export_stt_dataset)  
        stt_menu.addAction(export_stt_action)  
          
    # 新しいイベントハンドラー（分離されたコントローラーからのシグナル用）  
    def on_video_position_changed(self, position: int):  
        """動画位置が変更された時の処理"""  
        # 複数タイムラインビューアの位置も更新  
        current_time = position / 1000.0  # ミリ秒から秒に変換  
        self.multi_timeline_viewer.update_playhead_position(current_time)  
          
    def on_video_duration_changed(self, duration: int):  
        """動画の長さが変更された時の処理"""  
        # 複数タイムラインビューアーに動画の長さを設定  
        if duration > 0:  
            duration_seconds = duration / 1000.0  
            self.multi_timeline_viewer.set_video_duration(duration_seconds)  
            # 既に推論結果が読み込まれている場合は、タイムラインを更新  
            if self.results_manager.get_all_results():  
                self.multi_timeline_viewer.set_query_results(self.results_manager.get_all_results())  
          
    def on_query_selected(self, query_result):  
        """クエリが選択された時の処理"""  
        # IntervalEditControllerに現在のクエリ結果を設定  
        self.interval_edit_controller.set_current_query_results(query_result)  
          
    def on_interval_selected(self, interval, index: int):  
        """区間が選択された時の処理"""  
        # IntervalEditControllerに選択された区間を設定  
        self.interval_edit_controller.set_selected_interval(interval, index)  
        # 動画をその位置にシーク  
        self.video_controller.seek_to_time(interval.start_time)  
          
    def on_results_updated(self, results):  
        """結果が更新された時の処理"""  
        # タイムラインビューアを更新  
        self.multi_timeline_viewer.set_query_results(results)  
          
        # STTデータマネージャーに推論結果を追加  
        if self.app_controller.video_info:  
            video_name = Path(self.app_controller.video_info.file_path).stem  
            self.stt_data_manager.add_inference_results(video_name, results)  
            self.stt_edit_widget.set_current_video(video_name)  
          
        # フィルタを初期化（閾値を0に設定してすべて表示）  
        if self.confidence_slider.value() == 0 and self.threshold_slider.value() == 0:  
            # 初回読み込み時はフィルタを適用しない  
            pass  
        else:  
            # フィルタを適用  
            self.apply_filters()  
          
    def on_interval_updated(self):  
        """区間が更新された時の処理"""  
        # ResultsManagerに変更を通知  
        self.results_manager.update_results_display()  
        self.update_display()  
          
    def on_interval_deleted(self):  
        """区間が削除された時の処理"""  
        # ResultsManagerに変更を通知  
        self.results_manager.update_results_display()  
        self.update_display()  
          
    def on_interval_added(self):  
        """区間が追加された時の処理"""  
        # ResultsManagerに変更を通知  
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
                self.stt_edit_widget.set_current_video(video_name)  
                  
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
  
    def update_saliency_threshold(self, value: int):    
        """顕著性閾値を更新"""    
        threshold = value / 100.0    
        self.threshold_value_label.setText(f"{threshold:.2f}")    
        self.results_manager.set_saliency_threshold(threshold)  
        self.apply_filters()    
            
    def update_confidence_filter(self, value: int):      
        """信頼度フィルタを更新"""      
        threshold = value / 100.0      
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
        # タイムラインビューアを更新    
        if hasattr(self, 'multi_timeline_viewer') and self.results_manager.get_all_results():    
            # 全ての推論結果を再設定してタイムラインを更新    
            self.multi_timeline_viewer.set_query_results(self.results_manager.get_all_results())    
                
            # 動画の長さも再設定    
            duration_seconds = self.video_controller.get_duration_seconds()  
            if duration_seconds > 0:    
                self.multi_timeline_viewer.set_video_duration(duration_seconds)  
  
    def on_timeline_interval_clicked(self, interval, query_result):    
        """タイムライン上の区間がクリックされた時の処理"""    
        # 1. 該当するクエリをコンボボックスで選択    
        if hasattr(query_result, 'query_text'):    
            query_text = query_result.query_text    
        else:    
            query_text = query_result.get('query', '')    
          
        # ResultsManagerを通してクエリを選択  
        # クエリコンボボックスのインデックスを見つけて設定  
        query_combo = self.results_manager._query_combo_widget  
        if query_combo:  
            for i in range(query_combo.count()):  
                if query_combo.itemText(i) == query_text:  
                    query_combo.setCurrentIndex(i)  
                    break  
            
        # 2. 結果リストで該当する区間を選択    
        self.results_manager.select_interval_in_list(interval, query_result)  
  
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