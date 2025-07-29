# ApplicationCoordinator.py  
from PyQt6.QtCore import QObject, pyqtSignal  
from typing import List, Optional, Dict, Any  
  
from VideoPlayerController import VideoPlayerController
from VideoDataController import VideoDataController  
from ResultsDataController import ResultsDataController  
from TimelineDisplayManager import TimelineDisplayManager  
from EditWidgetManager import EditWidgetManager  
from DataClasses import DetectionInterval, QueryResults, QueryParser, QueryValidationError
from ResultsDisplayManager import ResultsDisplayManager
from Utilities import show_call_stack  # デバッグ用スタックトレース表示
from EditCommandFactory import EditCommandFactory
  
class ApplicationCoordinator(QObject):  
    """コンポーネント間の調整とイベント処理を担当するクラス"""  
      
    # 統合シグナル定義  
    videoLoaded = pyqtSignal(str)  # video_path  
    resultsLoaded = pyqtSignal(list)  # List[QueryResults]  
    dataChanged = pyqtSignal()  
      
    def __init__(self, main_window=None):  
        super().__init__()  
        self.main_window = main_window  

        # ドラッグ状態管理を追加  
        self.drag_original_start = None  
        self.drag_original_end = None  
        self.dragging_interval = None  
          
        # データコントローラー  
        self.video_data_controller = VideoDataController()  
        self.results_data_controller = ResultsDataController()  
          
        # UI管理コンポーネント  
        self.timeline_display_manager: Optional[TimelineDisplayManager] = None  
        self.edit_widget_manager: Optional[EditWidgetManager] = None  
        self.video_player_controller: Optional[VideoPlayerController] = None  
          
        # 状態管理  
        self.current_video_path: Optional[str] = None  

        # コマンドファクトリー
        self.command_factory = EditCommandFactory(main_window) if main_window else None
          
        self.setup_connections()  
      
    def setup_connections(self):  
        """シグナル・スロット接続の設定"""  
        # データコントローラーのシグナル接続  
        self.video_data_controller.videoLoaded.connect(self.handle_video_loaded)  
        self.results_data_controller.resultsLoaded.connect(self.handle_results_loaded)  
        self.results_data_controller.resultsFiltered.connect(self.handle_results_filtered)  
      
    def set_ui_components(self, timeline_display_manager: TimelineDisplayManager,  
                         edit_widget_manager: EditWidgetManager,  
                         video_player_controller: VideoPlayerController,
                         results_display_manager: ResultsDisplayManager):  
        """UI管理コンポーネントを設定"""  
        self.timeline_display_manager = timeline_display_manager  
        self.edit_widget_manager = edit_widget_manager  
        self.video_player_controller = video_player_controller  
        self.results_display_manager = results_display_manager
          
        # UI コンポーネントのシグナル接続  
        self._connect_ui_signals()  
      
    def _connect_ui_signals(self):  
        """UI コンポーネントのシグナル接続"""  
        if self.timeline_display_manager:  
            self.timeline_display_manager.intervalClicked.connect(self.handle_timeline_interval_clicked)  
            self.timeline_display_manager.intervalDragStarted.connect(self.handle_interval_drag_started)  
            self.timeline_display_manager.intervalDragMoved.connect(self.handle_interval_drag_moved)  
            self.timeline_display_manager.intervalDragFinished.connect(self.handle_interval_drag_finished)  
            self.timeline_display_manager.newIntervalCreated.connect(self.handle_new_interval_created)  
            self.timeline_display_manager.timePositionChanged.connect(self.handle_time_position_changed)  
          
        if self.edit_widget_manager:  
            self.edit_widget_manager.intervalUpdated.connect(self.handle_interval_updated)  
            self.edit_widget_manager.intervalDeleted.connect(self.handle_interval_deleted)  
            self.edit_widget_manager.intervalAdded.connect(self.handle_interval_added)  
            self.edit_widget_manager.dataChanged.connect(self.handle_edit_data_changed)  
          
        if self.video_player_controller:  
            self.video_player_controller.positionChanged.connect(self.handle_video_position_changed)  
            self.video_player_controller.durationChanged.connect(self.handle_video_duration_changed)  
      
    def handle_video_events(self, event_type: str, **kwargs):  
        """動画関連イベントを処理"""  
        if event_type == "load_video":  
            video_path = kwargs.get('video_path')  
            self.load_video(video_path)  
          
        elif event_type == "position_changed":  
            position = kwargs.get('position')  
            self.synchronize_video_position(position)  
          
        elif event_type == "duration_changed":  
            duration = kwargs.get('duration')  
            self.synchronize_video_duration(duration)  
      
    def handle_timeline_events(self, event_type: str, **kwargs):  
        """タイムライン関連イベントを処理"""  
        if event_type == "interval_clicked":  
            interval = kwargs.get('interval')  
            query_result = kwargs.get('query_result')  
            self.handle_timeline_interval_clicked(interval, query_result)  
          
        elif event_type == "interval_drag":  
            interval = kwargs.get('interval')  
            new_start = kwargs.get('new_start')  
            new_end = kwargs.get('new_end')  
            self.handle_interval_drag_finished(interval, new_start, new_end)  
          
        elif event_type == "new_interval":  
            start_time = kwargs.get('start_time')  
            end_time = kwargs.get('end_time')  
            timeline_type = kwargs.get('timeline_type')  
            self.handle_new_interval_created(start_time, end_time, timeline_type)  
      
    def handle_edit_events(self, event_type: str, **kwargs):  
        """編集関連イベントを処理"""  
        if event_type == "interval_updated":  
            self.synchronize_timeline_updates()  
          
        elif event_type == "interval_deleted":  
            self.synchronize_timeline_updates()  
          
        elif event_type == "interval_added":  
            self.synchronize_timeline_updates()  
          
        elif event_type == "step_modified":  
            self.synchronize_step_updates()  
      
    def synchronize_components(self):  
        """全コンポーネントの同期"""  
        # 動画情報の同期  
        video_info = self.video_data_controller.get_current_video_info()  
        if video_info and self.timeline_display_manager:  
            self.timeline_display_manager.set_video_duration(video_info.duration)  
          
        # 結果データの同期  
        filtered_results = self.results_data_controller.get_filtered_results()  
        if self.timeline_display_manager:  
            self.timeline_display_manager.set_query_results(  
                filtered_results, self.results_data_controller
            )  
          
        # 編集ウィジェットの同期  
        if self.edit_widget_manager:  
            video_name = self.video_data_controller.get_video_name()  
            if video_name:  
                self.edit_widget_manager.set_current_video(video_name)  
      
    def load_video(self, video_path: str):  
        """動画を読み込み"""  
        try:  
            # 動画メタデータを読み込み  
            video_info = self.video_data_controller.load_video_metadata(video_path)  
              
            # 動画プレイヤーに読み込み  
            if self.video_player_controller:  
                self.video_player_controller.load_video(video_path)  
              
            # 編集ウィジェットに動画名を設定  
            if self.edit_widget_manager:  
                self.edit_widget_manager.set_current_video(video_info.video_id)  
              
            self.current_video_path = video_path  
            self.videoLoaded.emit(video_path)  
              
        except Exception as e:  
            print(f"Failed to load video: {e}")  
      
    def load_inference_results(self, json_path: str):  
        """推論結果を読み込み"""  
        try:  
            results = self.results_data_controller.load_inference_results(json_path)  
            
            self.current_query_results = results  
            
            # シグナル発信（修正：結果を引数として渡す）  
            self.resultsLoaded.emit(results)  
            
            # コンポーネント同期  
            self.synchronize_components()  
                        
        except Exception as e:  
            print(f"Failed to load inference results: {e}")  
      
    def handle_video_loaded(self, video_info):  
        """動画読み込み完了時の処理"""  
        if self.timeline_display_manager:  
            self.timeline_display_manager.set_video_duration(video_info.duration)  
      
    def handle_results_loaded(self, results):  
        """結果読み込み完了時の処理"""  
        self.current_query_results = results  
        self.synchronize_components()  
    
    def handle_results_filtered(self, filtered_results):  
        """結果フィルタリング時の処理"""  
      
    def handle_dataset_updated(self):  
        """データセット更新時の処理"""  
        self.synchronize_components()  
        self.dataChanged.emit()  
      
    def handle_timeline_interval_clicked(self, interval: DetectionInterval, query_result: QueryResults):  
        """タイムライン区間クリック時の処理"""  
        if self.edit_widget_manager and query_result:  
            self.edit_widget_manager.set_current_query_results(query_result)  
            
            if hasattr(query_result, 'relevant_windows'):  
                index = -1  
                for i, window in enumerate(query_result.relevant_windows):  
                    if window == interval:
                        index = i  
                        break  
                
                if index >= 0:  
                    self.edit_widget_manager.set_selected_interval(interval, index)  
                else:  
                    return

        # Detection Results一覧で対応する項目を選択  
        if hasattr(self, 'results_display_manager') and self.results_display_manager:  
            self.results_display_manager.select_interval_in_list(interval)  

        # Timeline上で区間をハイライト（古い実装と同じ順序）  
        if self.timeline_display_manager:  
            self.timeline_display_manager.set_highlighted_interval(interval)  
        
        # 動画をその位置にシーク（古い実装と同じ順序）  
        if self.video_player_controller:  
            self.video_player_controller.seek_to_time(interval.start_time)

    def handle_interval_drag_started(self, interval: DetectionInterval):  
        """区間ドラッグ開始時の処理"""  
        print(f"[DEBUG] Drag started for interval: start={interval.start_time}, end={interval.end_time}")  
          
        # ApplicationCoordinator自体に保存  
        self.drag_original_start = interval.start_time  
        self.drag_original_end = interval.end_time  
        self.dragging_interval = interval  
        print(f"[DEBUG] Saved original values: start={self.drag_original_start}, end={self.drag_original_end}")
      
    def handle_interval_drag_moved(self, interval: DetectionInterval, new_start: float, new_end: float):  
        print(f"[DEBUG] Drag moved: interval={interval}, new_start={new_start}, new_end={new_end}")  
        print(f"[DEBUG] Interval query_type: {getattr(interval, 'query_type', 'unknown')}")  
          
        if self.edit_widget_manager and hasattr(interval, 'query_result'):  
            print(f"[DEBUG] Setting current query results: {interval.query_result.query_text}")  
            self.edit_widget_manager.set_current_query_results(interval.query_result)  
              
            if interval.query_type == "step":  
                print(f"[DEBUG] Step interval detected, updating realtime")  
                step_editor = self.edit_widget_manager.get_step_editor()  
                if step_editor:  
                    step_editor.update_interval_realtime(new_start, new_end)  
                    print(f"[DEBUG] Step editor realtime update called")
      

    def handle_interval_drag_finished(self, interval: DetectionInterval, new_start: float, new_end: float):  
        """区間ドラッグ完了時の処理"""  
        print(f"[DEBUG] Drag finished: interval={interval}, new_start={new_start}, new_end={new_end}")  
        print(f"[DEBUG] Interval query_type: {getattr(interval, 'query_type', 'unknown')}")  
        if self.command_factory:  
            old_start = self.drag_original_start if self.drag_original_start is not None else interval.start_time  
            old_end = self.drag_original_end if self.drag_original_end is not None else interval.end_time  
            print(f"[DEBUG] Creating command: old_start={old_start}, old_end={old_end}, new_start={new_start}, new_end={new_end}")  
              
            self.command_factory.create_and_execute_interval_modify(  
                interval, old_start, old_end, new_start, new_end  
            )  
            print(f"[DEBUG] Command executed")
              
            # ドラッグ状態をクリア  
            self.drag_original_start = None  
            self.drag_original_end = None  
            self.dragging_interval = None
    
    def handle_new_interval_created(self, start_time: float, end_time: float, timeline_type: str):  
        """修正版：ResultsDataControllerを使用"""  
        print(f"[DEBUG] handle_new_interval_created called: start={start_time}, end={end_time}, type={timeline_type}") 
        if timeline_type == "Steps":  
            print(f"[DEBUG] Processing Steps timeline")
            # Step用の処理  
            step_editor = self.edit_widget_manager.get_step_editor()  
            if step_editor:  
                video_name = self.video_data_controller.get_video_name()  
                if video_name:  
                    steps_count = self.results_data_controller.get_steps_count()  
                    step_text = f"New Step {steps_count + 1}" if steps_count >= 0 else "New Step 1"  
                      
                    new_query_result = QueryResults(  
                        query_text=f"Step:{step_text}",  
                        video_id=video_name,  
                        relevant_windows=[],  
                        saliency_scores=[],  
                        query_id=len(self.results_data_controller.get_all_results())  
                    )  
                      
                    step_editor.add_step(new_query_result, start_time, end_time)  
        else:  
            # Action用の処理  
            action_editor = self.edit_widget_manager.get_action_editor()  
            if action_editor:  
                current_results = self.results_data_controller.get_filtered_results()  
                if current_results:  
                    # 適切なQueryResultを選択  
                    source_query_result = None  
                    for query_result in current_results:  
                        if timeline_type in query_result.query_text:  
                            source_query_result = query_result  
                            break  
                      
                    if not source_query_result:  
                        source_query_result = current_results[0]  
                      
                    if source_query_result:  
                        import copy  
                        independent_query_result = copy.deepcopy(source_query_result)  
                        action_editor.add_new_interval(independent_query_result, start_time, end_time)

    def handle_time_position_changed(self, time: float):  
        """時間位置変更時の処理"""  
        # タイムライン上でプレイヘッド位置を同期  
        if self.timeline_display_manager:  
            self.timeline_display_manager.update_playhead_position(time)  

        # 動画プレイヤーをseek  
        if self.video_player_controller:  
            self.video_player_controller.seek_to_time(time)      

    def handle_video_position_changed(self, position: float):  
        """動画位置変更時の処理"""  
        # タイムライン上でプレイヘッド位置を同期  
        if self.timeline_display_manager:  
            self.timeline_display_manager.update_playhead_position(position)  
      
    def handle_video_duration_changed(self, duration: float):  
        """動画長さ変更時の処理"""  
        # タイムラインに動画長さを設定  
        if self.timeline_display_manager:  
            self.timeline_display_manager.set_video_duration(duration)  
      
    def handle_interval_updated(self):  
        """区間更新時の処理"""  
        self.synchronize_timeline_updates() 
        self.synchronize_components() 
        self.dataChanged.emit()  
      
    def handle_interval_deleted(self):  
        """区間削除時の処理"""  
        self.synchronize_timeline_updates()  
        self.dataChanged.emit()  
      
    def handle_interval_added(self):  
        """区間追加時の処理"""  
        self.synchronize_timeline_updates()  
        self.dataChanged.emit()  
      
    def handle_edit_data_changed(self):  
        """編集データ変更時の処理"""  
        self.synchronize_components()  
        self.dataChanged.emit()  
      
    def handle_step_segment_update(self, step_text: str, new_segment: list):  
        """ステップセグメント更新の処理"""  
        # ResultsDataControllerにステップ修正メソッドを追加  
        self.results_data_controller.modify_step_segment(step_text, new_segment)

        # コンポーネント同期  
        self.synchronize_step_updates()

    def synchronize_timeline_updates(self):  
        """タイムライン更新の同期"""  
        #show_call_stack()
        if self.timeline_display_manager:  
            self.timeline_display_manager.update_all_timelines()  
      
    def synchronize_step_updates(self):  
        print(f"[DEBUG] synchronize_step_updates called")  
        if self.timeline_display_manager:  
            filtered_results = self.results_data_controller.get_filtered_results()  
            print(f"[DEBUG] Synchronizing with {len(filtered_results)} filtered results")  
            self.timeline_display_manager.set_query_results(filtered_results, self.results_data_controller)
      
    def synchronize_video_position(self, position: float):  
        """動画位置の同期"""  
        if self.timeline_display_manager:  
            self.timeline_display_manager.update_playhead_position(position)  
      
    def synchronize_video_duration(self, duration: float):  
        """動画長さの同期"""  
        if self.timeline_display_manager:  
            self.timeline_display_manager.set_video_duration(duration)  
      
    def set_confidence_threshold(self, threshold: float):  
        """信頼度閾値を設定"""  
        self.results_data_controller.set_confidence_threshold(threshold)  
        if self.timeline_display_manager:  
            self.timeline_display_manager.set_confidence_threshold(threshold)  
      
    def set_hand_type_filter(self, hand_type: str):  
        """Hand Typeフィルタを設定"""  
        self.results_data_controller.set_hand_type_filter(hand_type)  
      
    def get_video_data_controller(self) -> VideoDataController:  
        """VideoDataControllerを取得"""  
        return self.video_data_controller  
      
    def get_results_data_controller(self) -> ResultsDataController:  
        """ResultsDataControllerを取得"""  
        return self.results_data_controller  
      
    def get_current_state(self) -> Dict[str, Any]:  
        """現在の状態を取得（デバッグ用）"""  
        return {  
            'current_video_path': self.current_video_path,  
            'query_results_count': len(self.current_query_results),  
            'has_timeline_manager': self.timeline_display_manager is not None,  
            'has_edit_manager': self.edit_widget_manager is not None,  
            'has_video_controller': self.video_player_controller is not None,  
            'video_loaded': self.video_data_controller.is_video_loaded(),  
            'results_loaded': self.results_data_controller.is_results_loaded()  
        }

    def get_current_query_results(self) -> List[QueryResults]:  
        """現在のQueryResultsを取得（ResultsDataControllerから）"""  
        return self.results_data_controller.get_filtered_results()  

    def add_query_result(self, query_result: QueryResults):  
        """新しいQueryResultを追加（ResultsDataControllerに委譲）"""  
        self.results_data_controller.add_query_result(query_result)  