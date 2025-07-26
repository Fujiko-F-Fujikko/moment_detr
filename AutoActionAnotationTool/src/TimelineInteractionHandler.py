# TimelineInteractionHandler.py  
from PyQt6.QtCore import QObject, pyqtSignal, QPointF  
from PyQt6.QtGui import QCursor, QMouseEvent  
from PyQt6.QtCore import Qt  
from typing import List, Optional  

from DetectionInterval import DetectionInterval  
from TimelineData import NewIntervalPreview, TimelineData
from Utilities import show_call_stack
  
class TimelineInteractionHandler(QObject):  
    """タイムラインのマウスインタラクション処理に特化したクラス"""  
      
    # シグナル定義  
    intervalClicked = pyqtSignal(DetectionInterval)  
    timePositionChanged = pyqtSignal(float)  
    intervalDragStarted = pyqtSignal(DetectionInterval)  
    intervalDragMoved = pyqtSignal(DetectionInterval, float, float)  
    intervalDragFinished = pyqtSignal(DetectionInterval, float, float)  
    newIntervalCreated = pyqtSignal(float, float, str)  # start_time, end_time, timeline_type  
    cursorChanged = pyqtSignal(object)  # QCursor  
      
    def __init__(self, timeline_type: str = "default"):  
        super().__init__()  
        self.timeline_type = timeline_type
        self.resize_edge_threshold = 10  # ピクセル単位でのリサイズエッジの幅  
        self.min_drag_distance = 5  # 最小ドラッグ距離  
        self.min_interval_duration = 0.1  # 最小区間長  
          
        # 状態管理  
        self.is_dragging = False  
        self.is_creating_new_interval = False  
        self.dragging_interval: Optional[DetectionInterval] = None  
        self.potential_dragging_interval: Optional[DetectionInterval] = None  
        self.drag_start_pos: Optional[QPointF] = None  
        self.drag_start_time: Optional[float] = None  
        self.drag_mode: Optional[str] = None  # 'move', 'resize_start', 'resize_end'  
        self.original_start_time: Optional[float] = None  
        self.original_end_time: Optional[float] = None  
          
        # 新規区間作成関連  
        self.new_interval_start_time: Optional[float] = None  
        self.new_interval_start_pos: Optional[float] = None  
        self.new_interval_end_time: Optional[float] = None  
          
        # ホバー状態管理  
        self.last_hovered_interval: Optional[DetectionInterval] = None  
      
    def handle_mouse_press(self, event: QMouseEvent, timeline_data: 'TimelineData', widget_width: int) -> bool:  
        """マウスプレスイベントを処理"""  
        if timeline_data.video_duration <= 0:  
            return False  
          
        click_time = (event.position().x() / widget_width) * timeline_data.video_duration  
        click_x = event.position().x()  
          
        # クリックされた区間を検索  
        clicked_interval = self._find_interval_at_position(  
            click_time, timeline_data.intervals, timeline_data.confidence_threshold  
        )  
          
        if clicked_interval:  
            # 区間がクリックされた場合  
            self._handle_interval_click(clicked_interval, click_x, click_time, timeline_data, widget_width)  
            self.intervalClicked.emit(clicked_interval)  
            return True  
        else:  
            # 空白領域での新規区間作成開始  
            self._start_new_interval_creation(click_time, click_x, timeline_data)  
            self.timePositionChanged.emit(click_time)  
            return True  
      
    def handle_mouse_move(self, event: QMouseEvent, timeline_data: 'TimelineData', widget_width: int) -> bool:  
        """マウス移動イベントを処理"""  
        if timeline_data.video_duration <= 0:  
            return False  
          
        current_time = (event.position().x() / widget_width) * timeline_data.video_duration  
          
        # 新規区間作成中の処理  
        if self.is_creating_new_interval:  
            self._update_new_interval_preview(current_time, timeline_data)  
            return True  
          
        # ドラッグ準備状態からの移行チェック  
        if self._check_drag_start_threshold(event):  
            return True  
          
        # ホバー処理  
        if not self.is_dragging:  
            self._handle_hover_events(event, timeline_data, widget_width)  
            return True  
          
        # ドラッグ中の処理  
        if self.is_dragging and self.dragging_interval:  
            self._handle_drag_move(current_time, timeline_data, widget_width)  
            return True  
          
        return False  
      
    def handle_mouse_release(self, event: QMouseEvent, timeline_data: 'TimelineData', widget_width: int) -> bool:  
        """マウスリリースイベントを処理"""  
        # 新規区間作成完了（ドラッグ距離チェック付き）  
        if self.is_creating_new_interval:  
            # 実際にドラッグが行われた場合のみ新規区間を作成  
            if (self.new_interval_end_time is not None and   
                hasattr(self, 'new_interval_start_pos') and   
                self.new_interval_start_pos is not None):  
                
                # 最小ドラッグ距離をチェック  
                distance = abs(event.position().x() - self.new_interval_start_pos)  
                if distance >= self.min_drag_distance:  # 5ピクセル以上のドラッグ
                    self.newIntervalCreated.emit(self.new_interval_start_time, self.new_interval_end_time, self.timeline_type)

            self._reset_new_interval_state(timeline_data)
            return True
          
        # ドラッグ完了  
        if self.is_dragging and self.dragging_interval:  
            new_start = self.dragging_interval.start_time  
            new_end = self.dragging_interval.end_time  
            self.intervalDragFinished.emit(self.dragging_interval, new_start, new_end)  
            self._reset_drag_state()  
            return True  
          
        # 状態リセット  
        self._reset_all_states(timeline_data)  
        return False  
      
    def _find_interval_at_position(self, click_time: float, intervals: List[DetectionInterval],   
                                 confidence_threshold: float) -> Optional[DetectionInterval]:  
        """指定位置にある区間を検索"""  
        for interval in intervals:  
            if (interval.confidence_score >= confidence_threshold and  
                interval.start_time <= click_time <= interval.end_time):  
                return interval  
        return None  
      
    def _handle_interval_click(self, interval: DetectionInterval, click_x: float, click_time: float,  
                             timeline_data: 'TimelineData', widget_width: int):  
        """区間クリック時の処理"""  
        start_x = widget_width * interval.start_time / timeline_data.video_duration  
        end_x = widget_width * interval.end_time / timeline_data.video_duration  
          
        # ドラッグモードを決定  
        if abs(click_x - start_x) <= self.resize_edge_threshold:  
            self.drag_mode = 'resize_start'  
            self.cursorChanged.emit(QCursor(Qt.CursorShape.SizeHorCursor))  
        elif abs(click_x - end_x) <= self.resize_edge_threshold:  
            self.drag_mode = 'resize_end'  
            self.cursorChanged.emit(QCursor(Qt.CursorShape.SizeHorCursor))  
        else:  
            self.drag_mode = 'move'  
            self.cursorChanged.emit(QCursor(Qt.CursorShape.ClosedHandCursor))  
            self.original_start_time = interval.start_time  
            self.original_end_time = interval.end_time  
          
        # ドラッグ準備情報を保存  
        self.potential_dragging_interval = interval  
        self.drag_start_pos = QPointF(click_x, 0)  
        self.drag_start_time = click_time  
      
    def _start_new_interval_creation(self, click_time: float, click_x: float, timeline_data: 'TimelineData'):  
        """新規区間作成を開始"""  
        self.is_creating_new_interval = True  
        timeline_data.is_creating_new_interval = True
        self.new_interval_start_time = click_time  
        self.new_interval_start_pos = click_x  
        self.cursorChanged.emit(QCursor(Qt.CursorShape.CrossCursor))  
      
    def _update_new_interval_preview(self, current_time: float, timeline_data: 'TimelineData'):  
        """新規区間プレビューを更新"""  
        if self.new_interval_start_time is not None:  
            self.new_interval_end_time = max(current_time, self.new_interval_start_time + self.min_interval_duration)  
            # ここでtimeline_dataのnew_interval_previewを更新  
            timeline_data.new_interval_preview = NewIntervalPreview(  
                start_time=min(self.new_interval_start_time, self.new_interval_end_time),  
                end_time=max(self.new_interval_start_time, self.new_interval_end_time)  
            )
            # 動画seek用のシグナルを発信  
            self.timePositionChanged.emit(current_time)

    def _check_drag_start_threshold(self, event: QMouseEvent) -> bool:  
        """ドラッグ開始閾値をチェック"""  
        if (self.potential_dragging_interval and not self.is_dragging and self.drag_start_pos):  
            distance = ((event.position().x() - self.drag_start_pos.x()) ** 2 +  
                       (event.position().y() - self.drag_start_pos.y()) ** 2) ** 0.5  
              
            if distance >= self.min_drag_distance:  
                # 実際のドラッグ開始  
                self.is_dragging = True  
                self.dragging_interval = self.potential_dragging_interval  
                self.intervalDragStarted.emit(self.dragging_interval)  
                return True  
        return False  
      
    def _handle_hover_events(self, event: QMouseEvent, timeline_data: 'TimelineData', widget_width: int):  
        """ホバーイベントを処理"""  
        current_time = (event.position().x() / widget_width) * timeline_data.video_duration  
        current_hovered_interval = self._find_interval_at_position(  
            current_time, timeline_data.intervals, timeline_data.confidence_threshold  
        )  
          
        # ホバー状態の変更をチェック  
        if current_hovered_interval != self.last_hovered_interval:  
            self.last_hovered_interval = current_hovered_interval  
          
        # カーソル形状を更新  
        self._update_cursor_for_position(event.position(), timeline_data, widget_width)  
      
    def _handle_drag_move(self, current_time: float, timeline_data: 'TimelineData', widget_width: int):  
        """ドラッグ移動を処理"""  
        if not self.dragging_interval:  
            return  
          
        new_start = self.dragging_interval.start_time  
        new_end = self.dragging_interval.end_time  
          
        if self.drag_mode == 'move':  
            # 現在のマウス位置から開始位置への差分を計算  
            current_x = (current_time / timeline_data.video_duration) * widget_width  
            pixel_delta = current_x - self.drag_start_pos.x()  
            
            # ピクセル差分を時間差分に変換  
            time_delta = (pixel_delta / widget_width) * timeline_data.video_duration  
            
            # 元の区間位置に時間差分を適用  
            new_start = max(0, self.original_start_time + time_delta)  
            new_end = min(timeline_data.video_duration, self.original_end_time + time_delta)  
            
            # 区間の長さを保持  
            duration = self.original_end_time - self.original_start_time  
            if new_end - new_start != duration:  
                if new_start == 0:  
                    new_end = duration  
                elif new_end == timeline_data.video_duration:  
                    new_start = timeline_data.video_duration - duration 
          
        elif self.drag_mode == 'resize_start':  
            # 開始時間リサイズ  
            new_start = max(0, min(current_time, self.dragging_interval.end_time - self.min_interval_duration))  
            new_start = self._find_snap_position(new_start, timeline_data)  
          
        elif self.drag_mode == 'resize_end':  
            # 終了時間リサイズ  
            new_end = min(timeline_data.video_duration,   
                         max(current_time, self.dragging_interval.start_time + self.min_interval_duration))  
            new_end = self._find_snap_position(new_end, timeline_data)  
          
        # 重複チェック  
        if self._check_overlap_constraints(new_start, new_end, self.dragging_interval, timeline_data.intervals):  
            self.dragging_interval.start_time = new_start  
            self.dragging_interval.end_time = new_end  
            self.intervalDragMoved.emit(self.dragging_interval, new_start, new_end)  
            # 動画seek用のシグナルを発信  
            self.timePositionChanged.emit(current_time)
        else:  
            self.cursorChanged.emit(QCursor(Qt.CursorShape.ForbiddenCursor))  
      
    def _find_snap_position(self, target_time: float, timeline_data: 'TimelineData',   
                           snap_threshold: float = 0.2) -> float:  
        """スナップ位置を検索"""  
        snap_positions = []  
          
        # 他の区間の境界を追加  
        for interval in timeline_data.intervals:  
            if interval != self.dragging_interval:  
                snap_positions.extend([interval.start_time, interval.end_time])  
          
        # 時間目盛りの位置を追加  
        if timeline_data.time_scale_enabled:  
            scale_interval = self._calculate_scale_interval(timeline_data.video_duration)  
            current_time = 0  
            while current_time <= timeline_data.video_duration:  
                snap_positions.append(current_time)  
                current_time += scale_interval  
          
        # 最も近いスナップ位置を検索  
        for snap_pos in snap_positions:  
            if abs(target_time - snap_pos) <= snap_threshold:  
                return snap_pos  
          
        return target_time  
      
    def _check_overlap_constraints(self, new_start: float, new_end: float,   
                                 exclude_interval: DetectionInterval,   
                                 intervals: List[DetectionInterval]) -> bool:  
        """他の区間との重複をチェック"""  
        for interval in intervals:  
            if interval == exclude_interval:  
                continue  
              
            # 重複チェック  
            if not (new_end <= interval.start_time or new_start >= interval.end_time):  
                return False  # 重複あり  
        return True  # 重複なし  

    def _update_cursor_for_position(self, pos: QPointF, timeline_data: 'TimelineData', widget_width: int):  
        """マウス位置に応じてカーソル形状を更新"""  
        if timeline_data.video_duration <= 0:  
            return  
          
        click_time = (pos.x() / widget_width) * timeline_data.video_duration  
        click_x = pos.x()  
          
        cursor_set = False  
        for interval in timeline_data.intervals:  
            if (interval.confidence_score >= timeline_data.confidence_threshold and  
                interval.start_time <= click_time <= interval.end_time):  
                  
                start_x = widget_width * interval.start_time / timeline_data.video_duration  
                end_x = widget_width * interval.end_time / timeline_data.video_duration  
                  
                if (abs(click_x - start_x) <= self.resize_edge_threshold or   
                    abs(click_x - end_x) <= self.resize_edge_threshold):  
                    self.cursorChanged.emit(QCursor(Qt.CursorShape.SizeHorCursor))  
                else:  
                    self.cursorChanged.emit(QCursor(Qt.CursorShape.OpenHandCursor))  
                cursor_set = True  
                break  
          
        if not cursor_set:  
            self.cursorChanged.emit(QCursor(Qt.CursorShape.ArrowCursor))  
      
    def _calculate_scale_interval(self, duration: float) -> float:  
        """動画の長さに基づいて適切な目盛り間隔を計算"""  
        if duration <= 10:  
            return 1.0  # 1秒間隔  
        elif duration <= 60:  
            return 5.0  # 5秒間隔  
        elif duration <= 300:  
            return 10.0  # 10秒間隔  
        elif duration <= 600:  
            return 30.0  # 30秒間隔  
        else:  
            return 60.0  # 1分間隔  
      
    def _reset_new_interval_state(self, timeline_data: 'TimelineData'):  
        """新規区間作成状態をリセット"""  
        self.is_creating_new_interval = False  
        timeline_data.is_creating_new_interval = False
        self.new_interval_start_time = None  
        self.new_interval_start_pos = None  
        self.new_interval_end_time = None  
        timeline_data.new_interval_preview = None
        self.cursorChanged.emit(QCursor(Qt.CursorShape.ArrowCursor))  
      
    def _reset_drag_state(self):  
        """ドラッグ状態をリセット"""  
        self.is_dragging = False  
        self.dragging_interval = None  
        self.potential_dragging_interval = None  
        self.drag_start_pos = None  
        self.drag_start_time = None  
        self.drag_mode = None  
        self.original_start_time = None  
        self.original_end_time = None  
        self.cursorChanged.emit(QCursor(Qt.CursorShape.ArrowCursor))  
      
    def _reset_all_states(self, timeline_data: 'TimelineData'):  
        """全ての状態をリセット"""  
        self._reset_new_interval_state(timeline_data)  
        self._reset_drag_state()  
      
    def get_current_state(self) -> dict:  
        """現在のインタラクション状態を取得（デバッグ用）"""  
        return {  
            'is_dragging': self.is_dragging,  
            'is_creating_new_interval': self.is_creating_new_interval,  
            'drag_mode': self.drag_mode,  
            'dragging_interval': self.dragging_interval,  
            'new_interval_start_time': self.new_interval_start_time,  
            'new_interval_end_time': self.new_interval_end_time  
        }