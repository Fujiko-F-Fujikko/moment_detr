# ApplicationCoordinator.py  
from PyQt6.QtCore import QObject, pyqtSignal  
from typing import Optional, Dict, Any  
  
from VideoPlayerController import VideoPlayerController
from VideoDataController import VideoDataController  
from ResultsDataController import ResultsDataController  
from STTDataController import STTDataController  
from TimelineDisplayManager import TimelineDisplayManager  
from EditWidgetManager import EditWidgetManager  
from Results import DetectionInterval, QueryResults
from ResultsDisplayManager import ResultsDisplayManager
from Utilities import show_call_stack  # デバッグ用スタックトレース表示
from STTDataStructures import QueryParser, QueryValidationError
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
          
        # データコントローラー  
        self.video_data_controller = VideoDataController()  
        self.results_data_controller = ResultsDataController()  
        self.stt_data_controller = STTDataController(self)  
          
        # UI管理コンポーネント  
        self.timeline_display_manager: Optional[TimelineDisplayManager] = None  
        self.edit_widget_manager: Optional[EditWidgetManager] = None  
        self.video_player_controller: Optional[VideoPlayerController] = None  
          
        # 状態管理  
        self.current_video_path: Optional[str] = None  
        self.current_query_results: list = []  

        # ドラッグ状態管理を追加  
        self.drag_original_start = None  
        self.drag_original_end = None  
        self.dragging_interval = None  

        # コマンドファクトリー  
        self.command_factory = EditCommandFactory(main_window) if main_window else None  
          
        self.setup_connections()  
        # 初期状態でも手の種類別タイムラインを表示するため同期を実行  
        self.synchronize_components()
      
    def setup_connections(self):  
        """シグナル・スロット接続の設定"""  
        # データコントローラーのシグナル接続  
        self.video_data_controller.videoLoaded.connect(self.handle_video_loaded)  
        self.results_data_controller.resultsLoaded.connect(self.handle_results_loaded)  
        self.results_data_controller.resultsFiltered.connect(self.handle_results_filtered)  
        self.stt_data_controller.datasetUpdated.connect(self.handle_dataset_updated)  
      
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
            self.timeline_display_manager.emptyAreaClicked.connect(self.handle_timeline_empty_area_clicked)
          
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
            video_name = self.video_data_controller.get_video_name()  
            self.timeline_display_manager.set_query_results(  
                filtered_results, self.stt_data_controller, video_name  
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
              
            # STTデータに動画を追加  
            self.stt_data_controller.add_video_data(video_info)  
              
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
            
            # STTデータに推論結果を追加  
            video_name = self.video_data_controller.get_video_name()  
            if video_name:  
                self.stt_data_controller.add_inference_results(video_name, results)  
            
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
        if self.timeline_display_manager:  
            video_name = self.video_data_controller.get_video_name()  
            self.timeline_display_manager.set_query_results(  
                filtered_results, self.stt_data_controller, video_name  
            )
      
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
        # ApplicationCoordinator内で状態管理  
        self.drag_original_start = interval.start_time  
        self.drag_original_end = interval.end_time  
        self.dragging_interval = interval  
      
    def handle_interval_drag_moved(self, interval: DetectionInterval, new_start: float, new_end: float):  
        """区間ドラッグ移動時の処理"""  
        # リアルタイムで編集ウィジェットを更新  
        if self.edit_widget_manager and hasattr(interval, 'query_result'):  
            self.edit_widget_manager.set_current_query_results(interval.query_result)  
            try:  
                index = interval.query_result.relevant_windows.index(interval)  
                self.edit_widget_manager.set_selected_interval(interval, index)  

                # Step区間の場合は追加でリアルタイム更新  
                if (hasattr(interval.query_result, 'query_text') and   
                    interval.query_result.query_text.startswith("Step:")):  
                    step_editor = self.edit_widget_manager.get_step_editor()  
                    if step_editor:  
                        step_editor.update_interval_realtime(new_start, new_end)  

            except ValueError:  
                pass  
      
    def handle_interval_drag_finished(self, interval: DetectionInterval, new_start: float, new_end: float):  
        """区間ドラッグ完了時の処理"""  
        if self.main_window and hasattr(self.main_window, 'undo_stack') and self.command_factory:  
            # ApplicationCoordinatorから直接取得  
            old_start = self.drag_original_start if self.drag_original_start is not None else interval.start_time  
            old_end = self.drag_original_end if self.drag_original_end is not None else interval.end_time  
              
            # 実際に変更があるかチェック  
            if abs(old_start - new_start) < 0.001 and abs(old_end - new_end) < 0.001:  
                print("DEBUG: No significant changes detected - skipping undo command")  
                return  

              
            # ステップかアクションかを判定  
            is_step = (hasattr(interval, 'query_result') and   
                      hasattr(interval.query_result, 'query_text') and   
                      interval.query_result.query_text.startswith("Step:"))  
              
            if is_step:  
                self.command_factory.create_and_execute_step_modify(  
                    interval, old_start, old_end, new_start, new_end,  
                    self.stt_data_controller, self.video_data_controller.get_video_name()  
                )  
            else:  
                self.command_factory.create_and_execute_interval_modify(  
                    interval, old_start, old_end, new_start, new_end  
                ) 
        else:  
            print("DEBUG: Command creation skipped - missing dependencies")
        
        # ドラッグ状態をクリア  
        self.drag_original_start = None  
        self.drag_original_end = None  
        self.dragging_interval = None
    
    def handle_new_interval_created(self, start_time: float, end_time: float, timeline_type: str):      
        """新規区間作成時の処理"""      
        print(f"New interval created: {start_time} - {end_time} ({timeline_type})")
        if timeline_type == "Steps":      
            # Step用の新規区間作成処理      
            video_name = self.video_data_controller.get_video_name()      
            if video_name and self.stt_data_controller and self.command_factory:      
                # 新しいステップを作成      
                if video_name in self.stt_data_controller.stt_dataset.database:      
                    steps_count = len(self.stt_data_controller.stt_dataset.database[video_name].steps)      
                    step_text = f"New Step {steps_count + 1}"      
                else:      
                    step_text = "New Step 1"      
                  
                # EditCommandFactoryを使用してUndoコマンドを作成      
                self.command_factory.create_and_execute_step_add(      
                    self.stt_data_controller, video_name, step_text, [start_time, end_time]      
                )      
        else:    
            # Action用の新規区間作成処理
            if self.command_factory:  
                # コマンド実行前  
                # timeline_typeを使ってクエリ文章を作成
                query_text = f"{timeline_type}_None_None_None_None"  
                print(f"DEBUG: Command factory available, creating query_text: {query_text}")  
                  
                new_query_result = QueryResults(  
                    query_text=query_text,  
                    video_id=self.video_data_controller.get_video_name() or "",  
                    relevant_windows=[],  
                    saliency_scores=[],  
                    query_id=len(self.current_query_results)  
                )  
                # QueryResults作成後  
                print(f"DEBUG: Created new_query_result with query_id: {len(self.current_query_results)}")  
                  
                # 新しい区間を作成  
                new_interval = DetectionInterval(start_time, end_time, 1.0, 0)  
                new_interval.query_result = new_query_result  
                  
                # current_query_resultsに追加  
                self.current_query_results.append(new_query_result)  
                # current_query_results追加後  
                print(f"DEBUG: Added to current_query_results, new count: {len(self.current_query_results)}")  
                self.results_data_controller.add_result(new_query_result)
                print(f"DEBUG: Added new_query_result to results_data_controller, total count: {len(self.results_data_controller.get_all_results())}")
                  
                # コマンドを実行  
                self.command_factory.create_and_execute_interval_add(  
                    new_query_result, new_interval  
                )  
            else:  
                print("DEBUG: Command factory is None!")
      
                # 新しいQueryResultsを作成後、STTDataControllerにも反映    
                stt_controller = self.get_stt_data_controller()    
                if stt_controller:    
                    # 新しいアクションカテゴリを強制的に作成    
                    stt_controller._get_or_create_action_category(new_query_result.query_text)    
                    # データセット更新シグナルを発信    
                    stt_controller.datasetUpdated.emit()  
      
                # Timeline上でハイライト表示      
                if self.timeline_display_manager:      
                    self.timeline_display_manager.set_highlighted_interval(new_interval)

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
      
    def handle_step_segment_update(self, step_text: str, old_segment: list, new_segment: list):  
        """ステップセグメント更新の処理"""  
        video_name = self.video_data_controller.get_video_name()  
        if video_name and self.stt_data_controller:  
            # 該当するステップのインデックスを見つける  
            if video_name in self.stt_data_controller.stt_dataset.database:  
                video_data = self.stt_data_controller.stt_dataset.database[video_name]  
                for i, step in enumerate(video_data.steps):  
                    if step.step == step_text:  
                        # 既存のmodify_stepメソッドを使用してセグメントを更新  
                        self.stt_data_controller.modify_step(  
                            video_name, i, new_segment=new_segment  
                        )  
                        break  
        
        # コンポーネント同期  
        self.synchronize_step_updates()

    def handle_timeline_empty_area_clicked(self, time_position: float):  
        """タイムライン空白エリアクリック時の処理"""  
        print(f"Empty area clicked at time position: {time_position}")
        # 選択状態をクリア  
        if self.edit_widget_manager:  
            self.edit_widget_manager.clear_selection()  
          
        # タイムライン上のハイライトをクリア  
        if self.timeline_display_manager:  
            self.timeline_display_manager.clear_highlighted_interval()  
          
        # 動画をクリック位置にシーク  
        if self.video_player_controller:  
            self.video_player_controller.seek_to_time(time_position)
        
        # 完全なコンポーネント同期を実行  
        self.synchronize_timeline_updates()
        self.synchronize_components()  

    def synchronize_timeline_updates(self):  
        """タイムライン更新の同期"""  
        #show_call_stack()
        if self.timeline_display_manager:  
            self.timeline_display_manager.update_all_timelines()  
      
    def synchronize_step_updates(self):  
        """ステップ更新の同期"""  
        # STTデータの変更をタイムラインに反映  
        if self.timeline_display_manager:  
            video_name = self.video_data_controller.get_video_name()  
            filtered_results = self.results_data_controller.get_filtered_results()  
            self.timeline_display_manager.set_query_results(  
                filtered_results, self.stt_data_controller, video_name  
            )  
      
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
      
    def get_video_data_controller(self) -> VideoDataController:  
        """VideoDataControllerを取得"""  
        return self.video_data_controller  
      
    def get_results_data_controller(self) -> ResultsDataController:  
        """ResultsDataControllerを取得"""  
        return self.results_data_controller  
      
    def get_stt_data_controller(self) -> STTDataController:  
        """STTDataControllerを取得"""  
        return self.stt_data_controller  
      
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