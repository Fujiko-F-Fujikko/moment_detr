from PyQt6.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QLabel
from PyQt6.QtCore import pyqtSignal
from TimelineViewer import TimelineViewer
from DetectionInterval import DetectionInterval

class MultiTimelineViewer(QWidget):  

    # シグナルを定義  
    intervalClicked = pyqtSignal(object, object)  # (interval, query_result)  

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
        """VALID_HAND_TYPES毎にタイムラインを作成"""  
        # 既存のタイムラインをクリア  
        self.clear_timelines()  
        
        # VALID_HAND_TYPESでグループ化  
        from STTDataStructures import QueryParser  
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
            except:  
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
                timeline.enable_time_scale(True)  # 目盛り表示を有効化  
                print(f"Applied duration {duration} to timeline with time scale")

    def on_interval_clicked(self, interval, query_result):  
        """区間がクリックされた時の処理"""  
        # メインウィンドウに通知  
        self.intervalClicked.emit(interval, query_result)

    def create_hand_type_timeline(self, hand_type: str, query_results: list):  
        """手の種類毎のタイムラインウィジェットを作成"""  
        container = QWidget()  
        container_layout = QVBoxLayout()  
        
        # 手の種類のラベル  
        hand_label = QLabel(f"Hand Type: {hand_type}")  
        hand_label.setStyleSheet("font-weight: bold; padding: 5px; background-color: #e0e0e0; font-size: 14px;")  
        container_layout.addWidget(hand_label)  
        
        # タイムラインビューア  
        timeline = TimelineViewer()  
        timeline.setMinimumHeight(100)  
        timeline.setMaximumHeight(150)  
        
        # 動画の長さを設定し、目盛り表示を有効化  
        if self.video_duration > 0:  
            timeline.set_video_duration(self.video_duration)  
            timeline.enable_time_scale(True)  
        
        # 全ての区間を統合（クエリ情報は既に埋め込まれている）  
        all_intervals = []  
        for query_result in query_results:  
            intervals = query_result.relevant_windows if hasattr(query_result, 'relevant_windows') else []  
            all_intervals.extend(intervals)  
        
        timeline.set_intervals(all_intervals)  
        
        container_layout.addWidget(timeline)  
        container.setLayout(container_layout)  
        
        # タイムラインのクリックイベントを接続（簡素化版）  
        timeline.intervalClicked.connect(self.on_interval_clicked_with_embedded_query)  
        
        return container

    def on_interval_clicked_with_embedded_query(self, interval):  
        """区間がクリックされた時の処理（埋め込まれたクエリ情報を使用）"""  
        # 区間に埋め込まれたクエリ情報を直接取得  
        if hasattr(interval, 'query_result') and interval.query_result:  
            query_result = interval.query_result  
            # メインウィンドウに通知  
            self.intervalClicked.emit(interval, query_result)  
        else:  
            print(f"Warning: No query information found for interval {interval}")