# MultiTimelineViewer.py (修正版)  
from PyQt6.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QLabel  
from PyQt6.QtCore import pyqtSignal  
from TimelineViewer import TimelineViewer  
from STTDataStructures import QueryParser, QueryValidationError  
from DetectionInterval import DetectionInterval
  
class MultiTimelineViewer(QWidget):    
    # シグナルを定義    
    intervalClicked = pyqtSignal(object, object)  # (interval, query_result)    
    intervalDragStarted = pyqtSignal(DetectionInterval)  
    intervalDragMoved = pyqtSignal(DetectionInterval, float, float)  
    intervalDragFinished = pyqtSignal(DetectionInterval, float, float)  
    newIntervalCreated = pyqtSignal(float, float, str)  # start_time, end_time, timeline_type

    def __init__(self):    
        super().__init__()    
        self.timeline_widgets = []    
        self.scroll_area = QScrollArea()    
        self.content_widget = QWidget()    
        self.layout = QVBoxLayout()    
            
        self.content_widget.setLayout(self.layout)    
        self.scroll_area.setWidget(self.content_widget)    
        self.scroll_area.setWidgetResizable(True)    
            
        main_layout = QVBoxLayout()    
        main_layout.addWidget(self.scroll_area)    
        self.setLayout(main_layout)    
        
        self.video_duration = 0.0  
          
    def set_query_results(self, query_results_list, stt_data_manager=None, video_name=None):
        """VALID_HAND_TYPES毎にタイムラインを作成"""    
        # 現在の再生位置を保存  
        current_playhead_position = getattr(self, 'current_playhead_position', 0.0)  

        # 既存のタイムラインをクリア    
        self.clear_timelines()    

        # 1. Stepsタイムラインを最初に追加（常に表示）  
        steps_timeline = self.create_steps_timeline(stt_data_manager, video_name)  
        if steps_timeline:  
            self.timeline_widgets.append(steps_timeline)  
            self.layout.addWidget(steps_timeline)  

        # 2. 既存の手の種類別タイムライン  
        # VALID_HAND_TYPESでグループ化  
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
                # パースできない場合はNoneに分類  
                hand_type_groups['None'].append(query_result)  
          
        # 各hand typeに対してタイムラインを作成  
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
  
    def create_hand_type_timeline(self, hand_type: str, query_results: list):  
        """手の種類毎のタイムラインウィジェットを作成"""  
        container = QWidget()  
        container_layout = QVBoxLayout()  
          
        # 手の種類のラベル  
        hand_label = QLabel(f"Hand Type: {hand_type}")  
        hand_label.setStyleSheet("font-weight: bold; padding: 3px; background-color: #e0e0e0; font-size: 12px;")  
        container_layout.addWidget(hand_label)  
          
        # タイムラインビューア  
        timeline = TimelineViewer()  
        timeline.setMinimumHeight(50)  
        timeline.setMaximumHeight(75)  
          
        # 重要：新しく作成したタイムラインに動画の長さを設定  
        if self.video_duration > 0:  
            timeline.set_video_duration(self.video_duration)  
            timeline.enable_time_scale(True)  # 目盛り表示を有効化  
          
        # 全ての区間を統合（クエリ情報は既に埋め込まれている）  
        all_intervals = []  
        for query_result in query_results:  
            intervals = query_result.relevant_windows if hasattr(query_result, 'relevant_windows') else []  
            all_intervals.extend(intervals)  
          
        timeline.set_intervals(all_intervals)  
          
        container_layout.addWidget(timeline)  
          
        # クエリリストを表示（オプション）  
        query_list_label = QLabel(f"Queries: {', '.join([q.query_text for q in query_results])}")  
        query_list_label.setStyleSheet("font-size: 10px; color: #666; padding: 2px;")  
        query_list_label.setWordWrap(True)  
        container_layout.addWidget(query_list_label)  
          
        container.setLayout(container_layout)  
          
        # タイムラインのクリックイベントを接続（埋め込まれたクエリ情報を使用）  
        timeline.intervalClicked.connect(self.on_interval_clicked_with_embedded_query)  

        # ドラッグイベントの接続を追加  
        timeline.intervalDragStarted.connect(self.intervalDragStarted.emit)  
        timeline.intervalDragMoved.connect(self.intervalDragMoved.emit)  
        timeline.intervalDragFinished.connect(self.intervalDragFinished.emit)
        # 各タイムラインでの接続時にタイムライン種別を渡す
        timeline.newIntervalCreated.connect(  
            lambda start, end: self.newIntervalCreated.emit(start, end, hand_type)  
        )          

        return container  
  
    def on_interval_clicked_with_embedded_query(self, interval):  
        """区間がクリックされた時の処理（埋め込まれたクエリ情報を使用）"""  
        print(f"DEBUG: MultiTimelineViewer - Interval clicked: {interval.start_time}-{interval.end_time}")  
        
        # 区間に埋め込まれたクエリ情報を直接取得  
        if hasattr(interval, 'query_result') and interval.query_result:  
            query_result = interval.query_result  
            print(f"DEBUG: MultiTimelineViewer - Found embedded query: {query_result.query_text}")  
            # メインウィンドウに通知  
            self.intervalClicked.emit(interval, query_result)  
        else:  
            print(f"DEBUG: MultiTimelineViewer - No query information found for interval {interval}")
  
    def clear_timelines(self):  
        """既存のタイムラインをクリア"""  
        for widget in self.timeline_widgets:  
            self.layout.removeWidget(widget)  
            widget.deleteLater()  
        self.timeline_widgets.clear()  
  
    def set_video_duration(self, duration: float):    
        """動画の長さを設定し、既存の全タイムラインに適用"""    
        self.video_duration = duration    
            
        for widget in self.timeline_widgets:    
            timeline = widget.findChild(TimelineViewer)    
            if timeline:    
                timeline.set_video_duration(duration)  
                timeline.enable_time_scale(True)  # 目盛り表示を有効化  
  
    def update_playhead_position(self, position: float):  
        """プレイヘッド位置を更新"""  
        self.current_playhead_position = position  # 現在位置を保存
        for widget in self.timeline_widgets:  
            timeline = widget.findChild(TimelineViewer)  
            if timeline:  
                timeline.update_playhead_position(position)

    def set_confidence_threshold(self, threshold: float):  
        """全てのタイムラインにconfidence閾値を設定"""  
        self.confidence_threshold = threshold  
        for widget in self.timeline_widgets:  
            timeline = widget.findChild(TimelineViewer)  
            if timeline is not None:
                timeline.set_confidence_threshold(threshold)

    def create_steps_timeline(self, stt_data_manager, video_name):  
        """Stepsタイムラインウィジェットを作成（データが無くても表示）"""  
        container = QWidget()  
        container_layout = QVBoxLayout()  
        
        # Stepsラベル（常に表示）  
        steps_label = QLabel("Steps")  
        steps_label.setStyleSheet("font-weight: bold; padding: 3px; background-color: #d0e0d0; font-size: 12px;")  
        container_layout.addWidget(steps_label)  
        
        # タイムラインビューア（常に作成）  
        timeline = TimelineViewer()  
        timeline.setMinimumHeight(50)  
        timeline.setMaximumHeight(75)  
        
        # 動画の長さを設定  
        if self.video_duration > 0:  
            timeline.set_video_duration(self.video_duration)  
            timeline.enable_time_scale(True)  
        
        # Stepデータがある場合のみ区間を設定  
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
                # 重要：Steps用の疑似QueryResultsを作成して埋め込み  
                step_query_result = type('StepQueryResult', (), {  
                    'query_text': f"Step: {step.step}",  
                    'video_id': video_name,  
                    'relevant_windows': [interval]  
                })()  
                interval.query_result = step_query_result  
                step_intervals.append(interval) 

        timeline.set_intervals(step_intervals)  
        container_layout.addWidget(timeline)  

        # 重要：イベント接続を追加  
        timeline.intervalClicked.connect(self.on_interval_clicked_with_embedded_query)  
        
        # ドラッグイベントの接続を追加  
        timeline.intervalDragStarted.connect(self.intervalDragStarted.emit)  
        timeline.intervalDragMoved.connect(self.intervalDragMoved.emit)  
        timeline.intervalDragFinished.connect(self.intervalDragFinished.emit) 
        # 各タイムラインでの接続時にタイムライン種別を渡す 
        timeline.newIntervalCreated.connect(  
            lambda start, end: self.newIntervalCreated.emit(start, end, "Steps")  
        )

        # Steps一覧表示（データがある場合のみ）  
        if step_intervals:  
            steps_list_label = QLabel(f"Steps: {', '.join([interval.label for interval in step_intervals])}")  
        else:  
            steps_list_label = QLabel("Steps: No steps defined")  
        
        steps_list_label.setStyleSheet("font-size: 10px; color: #666; padding: 2px;")  
        steps_list_label.setWordWrap(True)  
        container_layout.addWidget(steps_list_label)  
        
        container.setLayout(container_layout)  
        return container