from PyQt6.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QLabel
from TimelineViewer import TimelineViewer
from DetectionInterval import DetectionInterval

class MultiTimelineViewer(QWidget):  
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
        
    def set_query_results(self, query_results_list):  
        """複数のクエリ結果を設定して、それぞれのタイムラインを作成"""  
        # 既存のタイムラインをクリア  
        self.clear_timelines()  
          
        for query_result in query_results_list:  
            timeline_widget = self.create_query_timeline(query_result)  
            self.timeline_widgets.append(timeline_widget)  
            self.layout.addWidget(timeline_widget)  
          
        # 動画の長さが既に設定されている場合は、全タイムラインに適用  
        if self.video_duration > 0:  
            self.set_video_duration(self.video_duration)
      
    def create_query_timeline(self, query_result):  
        """単一クエリ用のタイムラインウィジェットを作成"""  
        container = QWidget()  
        container_layout = QVBoxLayout()  
          
        # クエリ名ラベル  
        query_text = query_result.get('query', f"Query {query_result.get('qid', 'Unknown')}")  
        query_label = QLabel(f"Query: {query_text}")  
        query_label.setStyleSheet("font-weight: bold; padding: 5px; background-color: #f0f0f0;")  
        container_layout.addWidget(query_label)  
          
        # タイムラインビューア  
        timeline = TimelineViewer()  
        timeline.setMinimumHeight(80)  
        timeline.setMaximumHeight(120)  
          
        # 重要：新しく作成したタイムラインに動画の長さを設定  
        if self.video_duration > 0:  
            timeline.set_video_duration(self.video_duration)  
            print(f"Set duration {self.video_duration} to new timeline")  
          
        # データを設定  
        pred_windows = query_result.get('pred_relevant_windows', [])  
        intervals = []  
        for window in pred_windows:  
            if len(window) >= 3:  
                start_time, end_time, confidence = window[:3]  
                intervals.append(DetectionInterval(start_time, end_time, confidence))  
          
        timeline.set_intervals(intervals)  
        timeline.set_saliency_scores(query_result.get('pred_saliency_scores', []))  
          
        container_layout.addWidget(timeline)  
        container.setLayout(container_layout)  
          
        return container
      
    def clear_timelines(self):  
        """既存のタイムラインをクリア"""  
        for widget in self.timeline_widgets:  
            widget.deleteLater()  
        self.timeline_widgets.clear()  
      
    def parse_intervals(self, pred_windows):  
        """pred_relevant_windowsをDetectionIntervalオブジェクトに変換"""  
        intervals = []  
        for window in pred_windows:  
            if len(window) >= 3:  
                start_time, end_time, confidence = window[:3]  
                intervals.append(DetectionInterval(start_time, end_time, confidence))  
        return intervals  
      
    def update_playhead_position(self, position):  
        """全てのタイムラインの再生位置を更新"""  
        for widget in self.timeline_widgets:  
            timeline = widget.findChild(TimelineViewer)  
            if timeline:  
                timeline.update_playhead_position(position)

    def set_video_duration(self, duration: float):  
        """動画の長さを設定し、既存の全タイムラインに適用"""  
        self.video_duration = duration  
        print(f"MultiTimelineViewer: Setting video duration to {duration}")  
          
        for widget in self.timeline_widgets:  
            timeline = widget.findChild(TimelineViewer)  
            if timeline:  
                timeline.set_video_duration(duration)  
                print(f"Applied duration {duration} to timeline")