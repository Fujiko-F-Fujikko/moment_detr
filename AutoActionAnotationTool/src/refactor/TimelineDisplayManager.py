# TimelineDisplayManager.py  
from PyQt6.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QLabel  
from PyQt6.QtCore import pyqtSignal, QObject  
from typing import List, Dict, Optional, Any  
  
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
          
        # TimelineInteractionHandlerのシグナル接続  
        self.interaction_handler.intervalClicked.connect(  
            lambda interval: self.event_coordinator._handle_interval_clicked("main", interval, "default")  
        )  
        self.interaction_handler.intervalDragStarted.connect(  
            lambda interval: self.event_coordinator._handle_interval_drag_started("main", interval)  
        )  
        self.interaction_handler.intervalDragMoved.connect(  
            lambda interval, start, end: self.event_coordinator._handle_interval_drag_moved("main", interval, start, end)  
        )  
        self.interaction_handler.intervalDragFinished.connect(  
            lambda interval, start, end: self.event_coordinator._handle_interval_drag_finished("main", interval, start, end)  
        )  
        self.interaction_handler.newIntervalCreated.connect(  
            lambda start, end: self.event_coordinator._handle_new_interval_created("main", start, end, "default")  
        )  
        self.interaction_handler.timePositionChanged.connect(  
            lambda time: self.event_coordinator._handle_time_position_changed("main", time)  
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
        query_list_label = QLabel(f"Queries: {', '.join([q.query_text for q in query_results])}")  
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
          
        # Steps一覧表示  
        if step_intervals:  
            steps_list_label = QLabel(f"Steps: {', '.join([interval.label for interval in step_intervals])}")  
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
        from PyQt6.QtCore import Qt  
          
        class TimelineWidget(QWidget):  
            def __init__(self, parent_manager, timeline_type, query_results=None, step_intervals=None):  
                super().__init__()  
                self.parent_manager = parent_manager  
                self.timeline_type = timeline_type  
                self.timeline_data = TimelineData()  
                  
                # データ設定  
                if step_intervals:  
                    self.timeline_data.intervals = step_intervals  
                elif query_results:  
                    all_intervals = []  
                    for query_result in query_results:  
                        intervals = query_result.relevant_windows if hasattr(query_result, 'relevant_windows') else []  
                        all_intervals.extend(intervals)  
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
                self.parent_manager.interaction_handler.handle_mouse_press(  
                    event, self.timeline_data, self.width()  
                )  
                self.update()  
              
            def mouseMoveEvent(self, event):  
                self.parent_manager.interaction_handler.handle_mouse_move(  
                    event, self.timeline_data, self.width()  
                )  
                self.update()  
              
            def mouseReleaseEvent(self, event):  
                self.parent_manager.interaction_handler.handle_mouse_release(  
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