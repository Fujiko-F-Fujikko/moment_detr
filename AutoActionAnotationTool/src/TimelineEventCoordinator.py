# TimelineEventCoordinator.py  
from PyQt6.QtCore import QObject, pyqtSignal  
from typing import Dict, List, Optional, Any  
from DetectionInterval import DetectionInterval  
  
class TimelineEventCoordinator(QObject):  
    """タイムラインイベントの調整とシグナル発信を担当するクラス"""  
      
    # 統合されたシグナル定義  
    intervalClicked = pyqtSignal(DetectionInterval, object)  # interval, query_result  
    intervalDragStarted = pyqtSignal(DetectionInterval)  
    intervalDragMoved = pyqtSignal(DetectionInterval, float, float)  
    intervalDragFinished = pyqtSignal(DetectionInterval, float, float)  
    newIntervalCreated = pyqtSignal(float, float, str)  # start_time, end_time, timeline_type  
    timePositionChanged = pyqtSignal(float)  
      
    def __init__(self):  
        super().__init__()  
        self.registered_timelines: Dict[str, Any] = {}  
        self.active_timeline: Optional[str] = None  
        self.event_history: List[Dict] = []  
        self.max_history_size = 100  
      
    def register_timeline(self, timeline_id: str, timeline_widget, timeline_type: str = "default"):  
        """タイムラインを登録し、イベント接続を設定"""  
        self.registered_timelines[timeline_id] = {  
            'widget': timeline_widget,  
            'type': timeline_type,  
            'enabled': True  
        }  
          
        # タイムラインのシグナルを接続  
        self._connect_timeline_signals(timeline_id, timeline_widget, timeline_type)  
      
    def unregister_timeline(self, timeline_id: str):  
        """タイムラインの登録を解除"""  
        if timeline_id in self.registered_timelines:  
            timeline_info = self.registered_timelines[timeline_id]  
            self._disconnect_timeline_signals(timeline_info['widget'])  
            del self.registered_timelines[timeline_id]  
      
    def _connect_timeline_signals(self, timeline_id: str, timeline_widget, timeline_type: str):  
        """個別タイムラインのシグナルを接続"""  
        # 基本的なタイムラインイベント  
        if hasattr(timeline_widget, 'intervalClicked'):  
            timeline_widget.intervalClicked.connect(  
                lambda interval: self._handle_interval_clicked(timeline_id, interval, timeline_type)  
            )  
          
        if hasattr(timeline_widget, 'intervalDragStarted'):  
            timeline_widget.intervalDragStarted.connect(  
                lambda interval: self._handle_interval_drag_started(timeline_id, interval)  
            )  
          
        if hasattr(timeline_widget, 'intervalDragMoved'):  
            timeline_widget.intervalDragMoved.connect(  
                lambda interval, start, end: self._handle_interval_drag_moved(timeline_id, interval, start, end)  
            )  
          
        if hasattr(timeline_widget, 'intervalDragFinished'):  
            timeline_widget.intervalDragFinished.connect(  
                lambda interval, start, end: self._handle_interval_drag_finished(timeline_id, interval, start, end)  
            )  
          
        if hasattr(timeline_widget, 'newIntervalCreated'):  
            timeline_widget.newIntervalCreated.connect(  
                lambda start, end: self._handle_new_interval_created(timeline_id, start, end, timeline_type)  
            )  
          
        if hasattr(timeline_widget, 'timePositionChanged'):  
            timeline_widget.timePositionChanged.connect(  
                lambda time: self._handle_time_position_changed(timeline_id, time)  
            )  
      
    def _disconnect_timeline_signals(self, timeline_widget):  
        """タイムラインのシグナル接続を解除"""  
        if hasattr(timeline_widget, 'intervalClicked'):  
            timeline_widget.intervalClicked.disconnect()  
        if hasattr(timeline_widget, 'intervalDragStarted'):  
            timeline_widget.intervalDragStarted.disconnect()  
        if hasattr(timeline_widget, 'intervalDragMoved'):  
            timeline_widget.intervalDragMoved.disconnect()  
        if hasattr(timeline_widget, 'intervalDragFinished'):  
            timeline_widget.intervalDragFinished.disconnect()  
        if hasattr(timeline_widget, 'newIntervalCreated'):  
            timeline_widget.newIntervalCreated.disconnect()  
        if hasattr(timeline_widget, 'timePositionChanged'):  
            timeline_widget.timePositionChanged.disconnect()  
      
    def _handle_interval_clicked(self, timeline_id: str, interval: DetectionInterval, timeline_type: str):  
        """区間クリックイベントを処理"""  
        self.active_timeline = timeline_id  
          
        # イベント履歴に記録  
        self._record_event('interval_clicked', {  
            'timeline_id': timeline_id,  
            'timeline_type': timeline_type,  
            'interval_start': interval.start_time,  
            'interval_end': interval.end_time  
        })  
          
        # 埋め込まれたクエリ情報を取得  
        query_result = getattr(interval, 'query_result', None)  
          
        # 統合シグナルを発信  
        self.intervalClicked.emit(interval, query_result)  
          
        # 他のタイムラインに同期通知（必要に応じて）  
        self._sync_interval_selection(timeline_id, interval)  
      
    def _handle_interval_drag_started(self, timeline_id: str, interval: DetectionInterval):  
        """ドラッグ開始イベントを処理"""  
        self.active_timeline = timeline_id  
          
        self._record_event('drag_started', {  
            'timeline_id': timeline_id,  
            'interval_start': interval.start_time,  
            'interval_end': interval.end_time  
        })  
          
        self.intervalDragStarted.emit(interval)  
      
    def _handle_interval_drag_moved(self, timeline_id: str, interval: DetectionInterval,   
                                   new_start: float, new_end: float):  
        """ドラッグ移動イベントを処理"""  
        # リアルタイム更新のため履歴記録はスキップ  
        self.intervalDragMoved.emit(interval, new_start, new_end)  
      
    def _handle_interval_drag_finished(self, timeline_id: str, interval: DetectionInterval,   
                                     new_start: float, new_end: float):  
        """ドラッグ完了イベントを処理"""  
        self._record_event('drag_finished', {  
            'timeline_id': timeline_id,  
            'old_start': getattr(interval, 'original_start_time', interval.start_time),  
            'old_end': getattr(interval, 'original_end_time', interval.end_time),  
            'new_start': new_start,  
            'new_end': new_end  
        })  
          
        self.intervalDragFinished.emit(interval, new_start, new_end)  
      
    def _handle_new_interval_created(self, timeline_id: str, start_time: float,   
                                   end_time: float, timeline_type: str):  
        """新規区間作成イベントを処理"""  
        self._record_event('interval_created', {  
            'timeline_id': timeline_id,  
            'timeline_type': timeline_type,  
            'start_time': start_time,  
            'end_time': end_time  
        })  
          
        self.newIntervalCreated.emit(start_time, end_time, timeline_type)  
      
    def _handle_time_position_changed(self, timeline_id: str, time: float):  
        """時間位置変更イベントを処理"""  
        # 頻繁なイベントのため履歴記録はスキップ  
        self.timePositionChanged.emit(time)  
      
    def _sync_interval_selection(self, source_timeline_id: str, interval: DetectionInterval):  
        """他のタイムラインに区間選択を同期"""  
        for timeline_id, timeline_info in self.registered_timelines.items():  
            if timeline_id != source_timeline_id and timeline_info['enabled']:  
                timeline_widget = timeline_info['widget']  
                  
                # 同じ時間範囲の区間をハイライト  
                if hasattr(timeline_widget, 'set_highlighted_interval'):  
                    timeline_widget.set_highlighted_interval(interval)  
      
    def _record_event(self, event_type: str, event_data: Dict):  
        """イベント履歴を記録"""  
        import time  
          
        event_record = {  
            'timestamp': time.time(),  
            'type': event_type,  
            'data': event_data  
        }  
          
        self.event_history.append(event_record)  
          
        # 履歴サイズ制限  
        if len(self.event_history) > self.max_history_size:  
            self.event_history.pop(0)  
      
    def enable_timeline(self, timeline_id: str):  
        """指定タイムラインを有効化"""  
        if timeline_id in self.registered_timelines:  
            self.registered_timelines[timeline_id]['enabled'] = True  
      
    def disable_timeline(self, timeline_id: str):  
        """指定タイムラインを無効化"""  
        if timeline_id in self.registered_timelines:  
            self.registered_timelines[timeline_id]['enabled'] = False  
      
    def get_active_timeline(self) -> Optional[str]:  
        """現在アクティブなタイムラインIDを取得"""  
        return self.active_timeline  
      
    def get_registered_timelines(self) -> List[str]:  
        """登録されているタイムラインIDのリストを取得"""  
        return list(self.registered_timelines.keys())  
      
    def get_event_history(self, event_type: Optional[str] = None) -> List[Dict]:  
        """イベント履歴を取得"""  
        if event_type is None:  
            return self.event_history.copy()  
          
        return [event for event in self.event_history if event['type'] == event_type]  
      
    def clear_event_history(self):  
        """イベント履歴をクリア"""  
        self.event_history.clear()