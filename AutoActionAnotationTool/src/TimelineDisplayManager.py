# TimelineDisplayManager.py (Phase 3修正版)  
from PyQt6.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QLabel    
from PyQt6.QtCore import pyqtSignal    
from typing import List, Dict, Optional    
    
from TimelineRenderer import TimelineRenderer    
from TimelineInteractionHandler import TimelineInteractionHandler    
from TimelineEventCoordinator import TimelineEventCoordinator    
from TimelineData import TimelineData  
from DetectionInterval import DetectionInterval    
from Results import QueryResults    
from STTDataStructures import QueryParser, QueryValidationError    
    
class TimelineDisplayManager(QWidget):    
    """複数タイムラインの管理を担当するクラス"""    
        
    # 統合シグナル定義    
    intervalClicked = pyqtSignal(object, object)  # (interval, query_result)    
    intervalDragStarted = pyqtSignal(DetectionInterval)    
    intervalDragMoved = pyqtSignal(DetectionInterval, float, float)    
    intervalDragFinished = pyqtSignal(DetectionInterval, float, float)    
    newIntervalCreated = pyqtSignal(float, float, str)  # start_time, end_time, timeline_type    
    timePositionChanged = pyqtSignal(float)    
        
    def __init__(self):    
        super().__init__()    
            
        # コンポーネント初期化    
        self.renderer = TimelineRenderer()    
        self.interaction_handler = TimelineInteractionHandler()    
        self.event_coordinator = TimelineEventCoordinator()    
            
        # UI要素    
        self.timeline_widgets: List[QWidget] = []    
        self.scroll_area = QScrollArea()    
        self.content_widget = QWidget()    
        self.layout = QVBoxLayout()    
            
        # 状態管理    
        self.video_duration = 0.0    
        self.current_playhead_position = 0.0    
        self.confidence_threshold = 0.0    
            
        self.setup_ui()    
        self.setup_connections()    
        
    def setup_ui(self):    
        """UIレイアウトの設定"""    
        self.content_widget.setLayout(self.layout)    
        self.scroll_area.setWidget(self.content_widget)    
        self.scroll_area.setWidgetResizable(True)    
            
        main_layout = QVBoxLayout()    
        main_layout.addWidget(self.scroll_area)    
        self.setLayout(main_layout)    
        
    def setup_connections(self):    
        """シグナル接続の設定"""    
        # TimelineEventCoordinatorのシグナルを転送    
        self.event_coordinator.intervalClicked.connect(self.intervalClicked)    
        self.event_coordinator.intervalDragStarted.connect(self.intervalDragStarted)    
        self.event_coordinator.intervalDragMoved.connect(self.intervalDragMoved)    
        self.event_coordinator.intervalDragFinished.connect(self.intervalDragFinished)    
        self.event_coordinator.newIntervalCreated.connect(self.newIntervalCreated)    
        self.event_coordinator.timePositionChanged.connect(self.timePositionChanged)    
    
    def interaction_handler_connections(self, _interaction_handler: TimelineInteractionHandler):    
        """インタラクションハンドラのシグナル接続を設定"""    
        _interaction_handler.intervalClicked.connect(    
            lambda interval: self.event_coordinator._handle_interval_clicked("main", interval, "default")    
        )    
        _interaction_handler.intervalDragStarted.connect(    
            lambda interval: self.event_coordinator._handle_interval_drag_started("main", interval)    
        )    
        _interaction_handler.intervalDragMoved.connect(    
            lambda interval, start, end: self.event_coordinator._handle_interval_drag_moved("main", interval, start, end)    
        )    
        _interaction_handler.intervalDragFinished.connect(    
            lambda interval, start, end: self.event_coordinator._handle_interval_drag_finished("main", interval, start, end)    
        )    
        _interaction_handler.timePositionChanged.connect(    
            lambda time: self.event_coordinator._handle_time_position_changed("main", time)    
        )    
        _interaction_handler.newIntervalCreated.connect(  
            lambda start, end, timeline_type: self.event_coordinator._handle_new_interval_created("main", start, end, timeline_type)  
        )
        _interaction_handler.cursorChanged.connect(  
            lambda cursor: self._update_widget_cursor(cursor)  
        )

    def set_query_results(self, query_results_list: List[QueryResults],     
                         stt_data_manager=None, video_name: str = None):    
        """クエリ結果を設定してタイムラインを作成"""    
        # 現在の再生位置を保存    
        current_playhead_position = getattr(self, 'current_playhead_position', 0.0)    
            
        # 既存のタイムラインをクリア    
        self.clear_timelines()    
            
        # 1. Stepsタイムラインを最初に追加    
        steps_timeline = self.create_steps_timeline(stt_data_manager, video_name)    
        if steps_timeline:    
            self.timeline_widgets.append(steps_timeline)    
            self.layout.addWidget(steps_timeline)    
            
        # 2. 手の種類別タイムライン    
        hand_type_groups = self._group_results_by_hand_type(query_results_list)    
            
        for hand_type, queries in hand_type_groups.items():    
            if queries:  # クエリがある場合のみタイムラインを作成    
                timeline_widget = self.create_hand_type_timeline(hand_type, queries)    
                self.timeline_widgets.append(timeline_widget)    
                self.layout.addWidget(timeline_widget)    
            
        # 動画の長さが既に設定されている場合は、全タイムラインに適用    
        if self.video_duration > 0:    
            self.set_video_duration(self.video_duration)    
            # 保存していた再生位置を復元    
            if current_playhead_position > 0:    
                self.update_playhead_position(current_playhead_position)    
        
    def create_hand_type_timeline(self, hand_type: str, query_results: List[QueryResults]) -> QWidget:    
        """手の種類毎のタイムラインウィジェットを作成"""    
        container = QWidget()    
        container_layout = QVBoxLayout()    
            
        # 手の種類のラベル    
        hand_label = QLabel(f"Hand Type: {hand_type}")    
        hand_label.setStyleSheet("font-weight: bold; padding: 3px; background-color: #e0e0e0; font-size: 12px;")    
        container_layout.addWidget(hand_label)    
            
        # タイムラインビューア（新しいアーキテクチャ）    
        timeline_widget = self._create_timeline_widget(hand_type, query_results)    
        container_layout.addWidget(timeline_widget)    
            
        # クエリリスト表示    
        # タイムライン上のすべてのIntervalからquery_textを収集  
        all_intervals = []  
        for query_result in query_results:  
            intervals = query_result.relevant_windows if hasattr(query_result, 'relevant_windows') else []  
            all_intervals.extend(intervals)  
        
        # 各Intervalの独立したquery_textを収集  
        unique_query_texts = set()  
        for interval in all_intervals:  
            if hasattr(interval, 'query_result') and hasattr(interval.query_result, 'query_text'):  
                unique_query_texts.add(interval.query_result.query_text)  
        
        query_list_label = QLabel(f"Queries: {', '.join(sorted(unique_query_texts))}")
        query_list_label.setStyleSheet("font-size: 10px; color: #666; padding: 2px;")    
        query_list_label.setWordWrap(True)    
        container_layout.addWidget(query_list_label)    
            
        container.setLayout(container_layout)    
            
        # イベントコーディネーターに登録    
        timeline_id = f"hand_type_{hand_type}"    
        self.event_coordinator.register_timeline(timeline_id, timeline_widget, hand_type)    
            
        return container    
        
    def create_steps_timeline(self, stt_data_manager, video_name: str) -> Optional[QWidget]:    
        """Stepsタイムラインウィジェットを作成"""    
        container = QWidget()    
        container_layout = QVBoxLayout()    
            
        # Stepsラベル    
        steps_label = QLabel("Steps")    
        steps_label.setStyleSheet("font-weight: bold; padding: 3px; background-color: #d0e0d0; font-size: 12px;")    
        container_layout.addWidget(steps_label)    
            
        # ステップデータを取得    
        step_intervals = self._get_step_intervals(stt_data_manager, video_name)    
            
        # タイムラインウィジェット作成    
        timeline_widget = self._create_timeline_widget("Steps", [], step_intervals)    
        container_layout.addWidget(timeline_widget)    
            
        # Steps一覧表示 各Intervalのquery_textから生成  
        if step_intervals:  
            query_texts = []  
            for interval in step_intervals:  
                if hasattr(interval, 'query_result') and hasattr(interval.query_result, 'query_text'):  
                    query_texts.append(interval.query_result.query_text)  
            steps_list_label = QLabel(f"Steps: {', '.join(query_texts)}")  
        else:  
            steps_list_label = QLabel("Steps: No steps defined")
            
        steps_list_label.setStyleSheet("font-size: 10px; color: #666; padding: 2px;")    
        steps_list_label.setWordWrap(True)    
        container_layout.addWidget(steps_list_label)    
            
        container.setLayout(container_layout)    
            
        # イベントコーディネーターに登録    
        self.event_coordinator.register_timeline("steps", timeline_widget, "Steps")    
            
        return container    
        
    def _create_timeline_widget(self, timeline_type: str, query_results: List[QueryResults] = None,     
                               step_intervals: List[DetectionInterval] = None) -> QWidget:    
        """新しいアーキテクチャでタイムラインウィジェットを作成"""    
        from PyQt6.QtWidgets import QWidget    
        from PyQt6.QtGui import QPaintEvent    

        # TimelineInteractionHandlerにタイムライン種別を渡す  
        interaction_handler = TimelineInteractionHandler(timeline_type) 
        # 個別にシグナル接続を設定
        self.interaction_handler_connections(interaction_handler)

        class TimelineWidget(QWidget):    
            def __init__(self, parent_manager, timeline_type, query_results=None, step_intervals=None):    
                super().__init__()    
                self.parent_manager = parent_manager    
                self.timeline_type = timeline_type    
                self.timeline_data = TimelineData()
                self.timeline_type = timeline_type
                self.interaction_handler = interaction_handler
                    
                # データ設定    
                if step_intervals:    
                    self.timeline_data.intervals = step_intervals    
                elif query_results:  
                    all_intervals = []  
                    for query_result in query_results:  
                        intervals = query_result.relevant_windows if hasattr(query_result, 'relevant_windows') else []  
                        # 各Intervalが独立したQueryResultsを持つことを確認  
                        for interval in intervals:  
                            if hasattr(interval, 'query_result') and interval.query_result:  
                                # Intervalが独立したQueryResultsを持っている場合はそのまま使用  
                                all_intervals.append(interval)  
                            else:  
                                # 古い形式の場合は、独立したQueryResultsを作成  
                                import copy  
                                independent_query_result = copy.deepcopy(query_result)  
                                independent_query_result.relevant_windows = [interval]  
                                interval.query_result = independent_query_result  
                                all_intervals.append(interval)  
                    self.timeline_data.intervals = all_intervals
                    
                self.setMinimumHeight(50)    
                self.setMaximumHeight(75)    
                self.setMouseTracking(True)    
                    
                # 動画の長さを設定    
                if parent_manager.video_duration > 0:    
                    self.timeline_data.video_duration = parent_manager.video_duration    
                    self.timeline_data.time_scale_enabled = True    
                    
                self.timeline_data.confidence_threshold = parent_manager.confidence_threshold    
                
            def paintEvent(self, event: QPaintEvent):    
                from PyQt6.QtGui import QPainter    
                painter = QPainter(self)    
                rect = self.rect()    
                self.parent_manager.renderer.render_timeline(painter, rect, self.timeline_data)    
                
            def mousePressEvent(self, event):    
                self.interaction_handler.handle_mouse_press(    
                    event, self.timeline_data, self.width()    
                )    
                self.update()    
                
            def mouseMoveEvent(self, event):    
                self.interaction_handler.handle_mouse_move(    
                    event, self.timeline_data, self.width()    
                )    
                self.update()    
                
            def mouseReleaseEvent(self, event):  
                self.interaction_handler.handle_mouse_release(  
                    event, self.timeline_data, self.width()  
                )  
                self.update()
                
            def set_video_duration(self, duration: float):    
                self.timeline_data.video_duration = duration    
                self.timeline_data.time_scale_enabled = True    
                self.update()    
                
            def update_playhead_position(self, position: float):    
                self.timeline_data.current_position = position    
                self.update()    
                
            def set_confidence_threshold(self, threshold: float):    
                self.timeline_data.confidence_threshold = threshold    
                self.update()    
                
            def set_highlighted_interval(self, interval: DetectionInterval):    
                self.timeline_data.highlighted_interval = interval    
                self.update()    
            
        return TimelineWidget(self, timeline_type, query_results, step_intervals)    
        
    def _group_results_by_hand_type(self, query_results_list: List[QueryResults]) -> Dict[str, List[QueryResults]]:    
        """結果をHand Type毎にグループ化"""    
        hand_type_groups = {    
            'LeftHand': [],    
            'RightHand': [],    
            'BothHands': [],    
            'None': []    
        }    
            
        for query_result in query_results_list:    
            try:    
                hand_type, _ = QueryParser.validate_and_parse_query(query_result.query_text)    
                if hand_type in hand_type_groups:    
                    hand_type_groups[hand_type].append(query_result)    
            except QueryValidationError:    
                hand_type_groups['None'].append(query_result)    
            
        return hand_type_groups    
        
    def _get_step_intervals(self, stt_data_manager, video_name: str) -> List[DetectionInterval]:    
        """STTデータからステップ区間を取得"""    
        step_intervals = []    
        if (stt_data_manager and video_name and     
            video_name in stt_data_manager.stt_dataset.database):    
            video_data = stt_data_manager.stt_dataset.database[video_name]    
            for step in video_data.steps:    
                if len(step.segment) >= 2:    
                    interval = DetectionInterval(    
                        start_time=step.segment[0],    
                        end_time=step.segment[1],    
                        confidence_score=1.0,    
                        label=step.step    
                    )    
                    # Steps用の疑似QueryResultsを作成して埋め込み    
                    step_query_result = type('StepQueryResult', (), {    
                        'query_text': f"Step: {step.step}",
                        'video_id': video_name,    
                        'relevant_windows': [interval]    
                    })()    
                    interval.query_result = step_query_result    
                    step_intervals.append(interval)    
            
        return step_intervals    
  
    def clear_timelines(self):    
        """既存のタイムラインをクリア"""    
        for widget in self.timeline_widgets:    
            self.layout.removeWidget(widget)    
            widget.deleteLater()    
        self.timeline_widgets.clear()    
        # イベントコーディネーターもクリア    
        for timeline_id in list(self.event_coordinator.registered_timelines.keys()):    
            self.event_coordinator.unregister_timeline(timeline_id)    
        
    def set_video_duration(self, duration: float):    
        """動画の長さを設定し、既存の全タイムラインに適用"""    
        self.video_duration = duration    
            
        for widget in self.timeline_widgets:    
            timeline = self._find_timeline_widget(widget)    
            if timeline:    
                timeline.set_video_duration(duration)    
        
    def update_playhead_position(self, position: float):    
        """プレイヘッド位置を更新"""    
        self.current_playhead_position = position    
            
        for widget in self.timeline_widgets:    
            timeline = self._find_timeline_widget(widget)    
            if timeline:    
                timeline.update_playhead_position(position)    
        
    def set_confidence_threshold(self, threshold: float):    
        """全てのタイムラインにconfidence閾値を設定"""    
        self.confidence_threshold = threshold    
            
        for widget in self.timeline_widgets:    
            timeline = self._find_timeline_widget(widget)    
            if timeline:    
                timeline.set_confidence_threshold(threshold)    
        
    def set_highlighted_interval(self, interval: DetectionInterval):    
        """指定された区間をハイライト"""    
        for widget in self.timeline_widgets:    
            timeline = self._find_timeline_widget(widget)    
            if timeline:    
                timeline.set_highlighted_interval(interval)    
      
    # Phase 3で追加された機能拡張メソッド  
    def on_interval_clicked_with_embedded_query(self, interval, timeline_type: str = None):  
        """区間クリック時の埋め込みクエリ処理（古いMultiTimelineViewerの機能移行）"""  
        # 区間に埋め込まれたクエリ結果を取得  
        embedded_query_result = None  
          
        if hasattr(interval, 'query_result'):  
            embedded_query_result = interval.query_result  
        elif timeline_type == "Steps":  
            # Stepsタイムラインの場合、疑似QueryResultsを作成  
            embedded_query_result = type('StepQueryResult', (), {  
                'query_text': f"Step: {interval.label}",  
                'video_id': getattr(interval, 'video_id', 'unknown'),  
                'relevant_windows': [interval]  
            })()  
          
        # 通常の区間クリックシグナルを発信  
        self.intervalClicked.emit(interval, embedded_query_result)  
          
        # 特殊な処理が必要な場合のフック  
        self._handle_special_interval_click(interval, embedded_query_result, timeline_type)  
      
    def _handle_special_interval_click(self, interval, query_result, timeline_type: str):  
        """特殊な区間クリック処理（拡張ポイント）"""  
        # ステップ区間の場合の特別処理  
        if timeline_type == "Steps":  
            self._handle_step_interval_click(interval, query_result)  
          
        # その他の特殊処理をここに追加可能  
      
    def _handle_step_interval_click(self, interval, query_result):  
        """ステップ区間クリック時の特別処理"""  
        # ステップ編集モードへの切り替えなど  
        if hasattr(self.parent(), 'edit_widget_manager'):  
            edit_manager = self.parent().edit_widget_manager  
            if hasattr(edit_manager, 'switch_to_step_tab'):  
                edit_manager.switch_to_step_tab()  
      
    def clear_highlighted_intervals(self):  
        """全てのハイライトをクリア"""  
        for widget in self.timeline_widgets:  
            timeline = self._find_timeline_widget(widget)  
            if timeline and hasattr(timeline, 'set_highlighted_interval'):  
                timeline.set_highlighted_interval(None)  
      
    def get_timeline_by_type(self, timeline_type: str):  
        """タイプ別にタイムラインを取得"""  
        for widget in self.timeline_widgets:  
            # コンテナ内の実際のTimelineWidgetを検索  
            timeline_widget = self._find_timeline_widget(widget)  
            if timeline_widget and hasattr(timeline_widget, 'timeline_type') and timeline_widget.timeline_type == timeline_type:  
                return timeline_widget  
        return None
      
    def update_timeline_data(self, timeline_type: str, data):  
        """特定のタイムラインのデータを更新"""  
        timeline = self.get_timeline_by_type(timeline_type)  
        if timeline:  
            timeline_widget = self._find_timeline_widget(timeline)  
            if timeline_widget and hasattr(timeline_widget, 'timeline_data'):  
                if timeline_type == "Steps":  
                    timeline_widget.timeline_data.intervals = data  
                else:  
                    # クエリ結果の場合  
                    all_intervals = []  
                    for query_result in data:  
                        intervals = query_result.relevant_windows if hasattr(query_result, 'relevant_windows') else []  
                        all_intervals.extend(intervals)  
                    timeline_widget.timeline_data.intervals = all_intervals  
                  
                timeline_widget.update()  
        
    def _find_timeline_widget(self, container_widget: QWidget):    
        """コンテナウィジェット内のTimelineWidgetを検索"""    
        # コンテナの子ウィジェットからTimelineWidgetを探す    
        for child in container_widget.findChildren(QWidget):    
            if hasattr(child, 'timeline_data'):    
                return child    
        return None    
        
    def get_timeline_count(self) -> int:    
        """現在のタイムライン数を取得"""    
        return len(self.timeline_widgets)    
        
    def get_event_coordinator(self) -> TimelineEventCoordinator:    
        """イベントコーディネーターを取得"""    
        return self.event_coordinator    
        
    def get_renderer(self) -> TimelineRenderer:    
        """レンダラーを取得"""    
        return self.renderer    
        
    def get_interaction_handler(self) -> TimelineInteractionHandler:    
        """インタラクションハンドラーを取得"""    
        return self.interaction_handler    
        
    def update_all_timelines(self):    
        """全てのタイムラインを更新"""    
        for widget in self.timeline_widgets:    
            timeline = self._find_timeline_widget(widget)    
            if timeline:    
                timeline.update()    
        
    def handle_timeline_events(self, event_type: str, **kwargs):    
        """タイムラインイベントを処理"""    
        if event_type == "interval_clicked":    
            interval = kwargs.get('interval')    
            query_result = kwargs.get('query_result')    
            self.intervalClicked.emit(interval, query_result)    
            
        elif event_type == "interval_drag_started":    
            interval = kwargs.get('interval')    
            self.intervalDragStarted.emit(interval)    
            
        elif event_type == "interval_drag_moved":    
            interval = kwargs.get('interval')    
            start = kwargs.get('start')    
            end = kwargs.get('end')    
            self.intervalDragMoved.emit(interval, start, end)    
            
        elif event_type == "interval_drag_finished":    
            interval = kwargs.get('interval')    
            start = kwargs.get('start')    
            end = kwargs.get('end')    
            self.intervalDragFinished.emit(interval, start, end)    
            
        elif event_type == "new_interval_created":    
            start = kwargs.get('start')    
            end = kwargs.get('end')    
            timeline_type = kwargs.get('timeline_type', 'default')    
            self.newIntervalCreated.emit(start, end, timeline_type)    
            
        elif event_type == "time_position_changed":    
            time = kwargs.get('time')    
            self.timePositionChanged.emit(time)    

    def _update_widget_cursor(self, cursor):  
        """ウィジェットのカーソルを更新"""  
        for widget in self.timeline_widgets:  
            timeline_widget = self._find_timeline_widget(widget)  
            if timeline_widget:  
                timeline_widget.setCursor(cursor)

    # 各タイムラインの種別を管理  
    def setup_timeline_connections(self, timeline_widget, timeline_type):  
        timeline_widget.newIntervalCreated.connect(  
            lambda start, end: self.event_coordinator._handle_new_interval_created(  
                "main", start, end, timeline_type  
            )  
        )

    def get_current_state(self) -> dict:    
        """現在の状態を取得（デバッグ用）"""    
        return {    
            'timeline_count': len(self.timeline_widgets),    
            'video_duration': self.video_duration,    
            'current_playhead_position': self.current_playhead_position,    
            'confidence_threshold': self.confidence_threshold,    
            'registered_timelines': list(self.event_coordinator.registered_timelines.keys()),    
            'active_timeline': self.event_coordinator.get_active_timeline()    
        }