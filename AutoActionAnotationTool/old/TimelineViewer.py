from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QCursor
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QRect
from typing import List
from DetectionInterval import DetectionInterval


class TimelineViewer(QWidget):  
    intervalClicked = pyqtSignal(DetectionInterval)  
    timePositionChanged = pyqtSignal(float)  
    intervalDragStarted = pyqtSignal(DetectionInterval)  
    intervalDragMoved = pyqtSignal(DetectionInterval, float, float)  # interval, new_start, new_end  
    intervalDragFinished = pyqtSignal(DetectionInterval, float, float) 
    newIntervalCreated = pyqtSignal(float, float)  # start_time, end_time
    def __init__(self):  
        super().__init__()  
        # マウストラッキングを有効にする  
        self.setMouseTracking(True)  

        self.video_duration = 0.0  
        self.current_position = 0.0  
        self.confidence_threshold = 0.0
        self.intervals = []  
        self.saliency_scores = []  
        self.highlighted_interval = None
        self.setMinimumHeight(100)  
        self.time_scale_enabled = False

        # ドラッグ関連の状態管理を追加  
        self.is_dragging = False  
        self.is_creating_new_interval = False
        self.dragging_interval = None  
        self.drag_start_pos = None  
        self.drag_start_time = None  
        self.drag_mode = None  # None, 'move', 'resize_start', 'resize_end'  
        self.resize_edge_threshold = 10  # ピクセル単位でのリサイズエッジの幅  

    def set_video_duration(self, duration: float):  
        self.video_duration = duration  
        self.update()  
      
    def set_intervals(self, intervals: List[DetectionInterval]):  
        self.intervals = intervals  
        self.update()  
      
    def set_saliency_scores(self, scores: List[float], clip_duration: float = 2.0):  
        self.saliency_scores = scores  
        self.clip_duration = clip_duration  
        self.update()  
      
    def paintEvent(self, event):  
        if self.video_duration <= 0:  
            return  
            
        painter = QPainter(self)  
        rect = self.rect()  
        
        # Draw timeline background  
        painter.fillRect(rect, QColor(240, 240, 240))  
        
        # Draw time scale if enabled  
        if self.time_scale_enabled:  
            self.draw_time_scale(painter, rect.width(), rect.height())  
        
        # Draw saliency heatmap (if not using time scale)  
        elif self.saliency_scores:  
            self.draw_saliency_heatmap(painter, rect)  
        
        # Draw intervals  
        for interval in self.intervals:  
            self.draw_interval(painter, rect, interval)  
        
        # Draw new interval preview
        if self.is_creating_new_interval and hasattr(self, 'new_interval_end_time'):  
            self.draw_new_interval_preview(painter, rect)  

        # Draw current position  
        self.draw_current_position(painter, rect)
      
    def draw_saliency_heatmap(self, painter: QPainter, rect: QRect):  
        """Draw saliency scores as heatmap background"""  
        clip_width = rect.width() * self.clip_duration / self.video_duration  
          
        for i, score in enumerate(self.saliency_scores):  
            x = i * clip_width  
            if x >= rect.width():  
                break  
                  
            # Normalize score to 0-1 range for color mapping  
            normalized_score = max(0, min(1, (score + 1) / 2))  # Assuming scores in [-1, 1]  
            alpha = int(normalized_score * 128)  # Semi-transparent  
              
            color = QColor(255, int(255 * (1 - normalized_score)), 0, alpha)  # Red to yellow  
            painter.fillRect(int(x), rect.top(), int(clip_width), rect.height(), color)  
            
    def mousePressEvent(self, event):      
        if self.video_duration <= 0:      
            return      
        
        click_time = (event.position().x() / self.width()) * self.video_duration    
        click_x = event.position().x()   
    
        # クリックされた区間を検索    
        clicked_interval = None    
        for interval in self.intervals:    
            if interval.start_time <= click_time <= interval.end_time:    
                self.intervalClicked.emit(interval)    
                clicked_interval = interval  
                break  
                
        if clicked_interval:    
            # ドラッグの準備のみ行い、実際のドラッグ状態は設定しない  
            start_x = self.width() * clicked_interval.start_time / self.video_duration    
            end_x = self.width() * clicked_interval.end_time / self.video_duration    
                    
            # ドラッグモードを決定    
            if abs(click_x - start_x) <= self.resize_edge_threshold:    
                self.drag_mode = 'resize_start'    
                self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))    
            elif abs(click_x - end_x) <= self.resize_edge_threshold:    
                self.drag_mode = 'resize_end'    
                self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))    
            else:    
                self.drag_mode = 'move'    
                self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))    
                self.original_start_time = clicked_interval.start_time    
                self.original_end_time = clicked_interval.end_time    
                    
            # ドラッグの準備情報のみ保存（is_dragging は設定しない）  
            self.potential_dragging_interval = clicked_interval    
            self.drag_start_pos = event.position()    
            self.drag_start_time = click_time    
            return    
        else:    
            # 空白領域での新規区間作成開始    
            self.is_creating_new_interval = True    
            self.new_interval_start_time = click_time    
            self.new_interval_start_pos = click_x    
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))  
                
        # 区間外のクリックの場合は既存の処理    
        self.timePositionChanged.emit(click_time)  

    def find_snap_position(self, target_time, snap_threshold=0.2):  
        """スナップ位置を検索"""  
        snap_positions = []  
        
        # 他の区間の境界を追加  
        for interval in self.intervals:  
            if interval != self.dragging_interval:  
                snap_positions.extend([interval.start_time, interval.end_time])  
        
        # 時間目盛りの位置を追加  
        if self.time_scale_enabled:  
            scale_interval = self.calculate_scale_interval(self.video_duration)  
            current_time = 0  
            while current_time <= self.video_duration:  
                snap_positions.append(current_time)  
                current_time += scale_interval  
        
        # 最も近いスナップ位置を検索  
        for snap_pos in snap_positions:  
            if abs(target_time - snap_pos) <= snap_threshold:  
                return snap_pos  
        
        return target_time 

    def check_overlap_constraints(self, new_start, new_end, exclude_interval):  
        """他の区間との重複をチェック"""  
        for interval in self.intervals:  
            if interval == exclude_interval:  
                continue  
                
            # 重複チェック  
            if not (new_end <= interval.start_time or new_start >= interval.end_time):  
                return False  # 重複あり  
        return True  # 重複なし  

    def mouseMoveEvent(self, event):  

        # 新規区間作成中の処理
        if self.is_creating_new_interval:  
            current_time = (event.position().x() / self.width()) * self.video_duration  
            self.new_interval_end_time = max(current_time, self.new_interval_start_time + 0.1)  
            self.update()  # プレビュー表示のため再描画  
            return  

        # ドラッグ準備状態からの移行チェック  
        if (hasattr(self, 'potential_dragging_interval') and   
            self.potential_dragging_interval and   
            not self.is_dragging):  
            
            # 最小移動距離を設定（例：5ピクセル）  
            min_drag_distance = 5  
            if hasattr(self, 'drag_start_pos'):  
                distance = ((event.position().x() - self.drag_start_pos.x()) ** 2 +   
                        (event.position().y() - self.drag_start_pos.y()) ** 2) ** 0.5  
                
                if distance >= min_drag_distance:  
                    # 実際のドラッグ開始  
                    self.is_dragging = True  
                    self.dragging_interval = self.potential_dragging_interval  
                    self.intervalDragStarted.emit(self.dragging_interval)  
                    print(f"DEBUG: Actual drag started after {distance:.1f}px movement")  

        # ホバー中の処理
        if not self.is_dragging:  
            # 現在ホバーしている区間を特定  
            current_hovered_interval = self.get_interval_at_position(event.position())  
            
            # 前回ホバーしていた区間と比較  
            if current_hovered_interval != getattr(self, 'last_hovered_interval', None):  
                # leaveEvent相当の処理  
                if hasattr(self, 'last_hovered_interval') and self.last_hovered_interval:  
                    self.on_interval_leave(self.last_hovered_interval)  
                
                # enterEvent相当の処理  
                if current_hovered_interval:  
                    self.on_interval_enter(current_hovered_interval)  
                
                self.last_hovered_interval = current_hovered_interval  
            
            self.updateCursorForPosition(event.position())  
            return  
              
        # ドラッグ中の処理
        current_time = max(0, min(self.video_duration,   
                                (event.position().x() / self.width()) * self.video_duration))            

        # 新しい開始・終了時間を計算  
        new_start = self.dragging_interval.start_time  
        new_end = self.dragging_interval.end_time  
        min_duration = 0.1  # 最小区間長
          
        if self.drag_mode == 'move':  
            # ピクセル単位で差分を計算  
            pixel_delta = event.position().x() - self.drag_start_pos.x()  
            
            # ピクセル差分を時間差分に変換  
            time_delta = (pixel_delta / self.width()) * self.video_duration  
            
            # 元の区間位置に時間差分を適用（修正）  
            new_start = max(0, self.original_start_time + time_delta)  
            new_end = min(self.video_duration, self.original_end_time + time_delta)              

            # 区間の長さを保持  
            duration = self.dragging_interval.end_time - self.dragging_interval.start_time  
            if new_end - new_start != duration:  
                if new_start == 0:  
                    new_end = duration  
                elif new_end == self.video_duration:  
                    new_start = self.video_duration - duration
                      
        elif self.drag_mode == 'resize_start':  
            # 開始時間を変更  
            new_start = max(0, min(current_time, self.dragging_interval.end_time - min_duration))  
            new_start = self.find_snap_position(new_start)   

        elif self.drag_mode == 'resize_end':  
            # 終了時間を変更  
            new_end = min(self.video_duration, max(current_time, self.dragging_interval.start_time + min_duration))  
            new_end = self.find_snap_position(new_end)

        # 重複チェックを追加  
        if self.check_overlap_constraints(new_start, new_end, self.dragging_interval):  
            # 重複がない場合のみ更新  
            self.dragging_interval.start_time = new_start  
            self.dragging_interval.end_time = new_end  
            self.update()  
            self.intervalDragMoved.emit(self.dragging_interval, new_start, new_end)  
        else:  
            # 重複がある場合は視覚的フィードバックを提供  
            self.setCursor(QCursor(Qt.CursorShape.ForbiddenCursor))
  
    def mouseReleaseEvent(self, event):  

        # 新規区間作成中の処理
        if self.is_creating_new_interval:  
            if hasattr(self, 'new_interval_end_time'):  
                # 新規区間作成シグナルを発火  
                self.newIntervalCreated.emit(self.new_interval_start_time, self.new_interval_end_time)  
        elif self.is_dragging and self.dragging_interval is not None:
            # 最終的な開始・終了時間を計算  
            new_start = self.dragging_interval.start_time  
            new_end = self.dragging_interval.end_time  
            
            print(f"DEBUG: Drag finished - mode: {self.drag_mode}, new interval: {new_start}-{new_end}")  
            
            # ドラッグ終了シグナルを発火  
            self.intervalDragFinished.emit(self.dragging_interval, new_start, new_end)  
        else:
            # ドラッグが終了したが、区間がない場合は何もしない  
            print("DEBUG: mouseReleaseEvent  but nothing to do...")

        # ドラッグ状態をリセット  
        self.is_dragging = False  
        self.is_creating_new_interval = False
        self.dragging_interval = None 
        self.potential_dragging_interval = None 
        self.drag_start_pos = None  
        self.drag_start_time = None  
        self.drag_mode = None  
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))  
  
    def updateCursorForPosition(self, pos):  
        """マウス位置に応じてカーソル形状を更新"""  
        if self.video_duration <= 0:  
            return  
              
        click_time = (pos.x() / self.width()) * self.video_duration  
        click_x = pos.x()  
          
        # カーソル形状をリセット  
        cursor_set = False  
          
        for interval in self.intervals:  
            if interval.start_time <= click_time <= interval.end_time:  
                start_x = self.width() * interval.start_time / self.video_duration  
                end_x = self.width() * interval.end_time / self.video_duration  
                  
                if abs(click_x - start_x) <= self.resize_edge_threshold or abs(click_x - end_x) <= self.resize_edge_threshold:  
                    self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))  
                else:  
                    self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))  
                cursor_set = True  
                break  
                  
        if not cursor_set:  
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def draw_current_position(self, painter: QPainter, rect: QRect):  
        """現在の再生位置を描画"""  
        if self.current_position > 0 and self.video_duration > 0:  
            pos_x = rect.width() * self.current_position / self.video_duration  
            painter.setPen(QPen(QColor(255, 0, 0), 3))  
            painter.drawLine(int(pos_x), rect.top(), int(pos_x), rect.bottom())

    def update_playhead_position(self, position: float):  
        """再生ヘッドの位置を更新"""  
        self.current_position = position  
        self.update()  # 再描画をトリガー

    def draw_time_scale(self, painter, widget_width, widget_height):  
        """動画の長さに基づいて時間目盛りを描画"""  
        if self.video_duration <= 0:  
            return  
        
        # 適切な目盛り間隔を計算  
        scale_interval = self.calculate_scale_interval(self.video_duration)  
        
        # 目盛りの描画  
        pen = QPen(QColor(200, 200, 200))  
        painter.setPen(pen)  
        
        current_time = 0  
        while current_time <= self.video_duration:  
            x_pos = int((current_time / self.video_duration) * widget_width)  
            
            # 縦線を描画  
            painter.drawLine(x_pos, 0, x_pos, widget_height)  
            
            # 時間ラベルを描画  
            painter.drawText(x_pos + 2, 15, f"{current_time:.1f}s")  
            
            current_time += scale_interval  
    
    def calculate_scale_interval(self, duration):  
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

    def enable_time_scale(self, enabled: bool):  
        """時間目盛り表示を有効/無効にする"""  
        self.time_scale_enabled = enabled  
        self.update()  # 再描画をトリガー

    def set_highlighted_interval(self, interval):  
        """ハイライトする区間を設定"""  
        self.highlighted_interval = interval  
        self.update()  # 再描画をトリガー  
    
    def draw_interval(self, painter: QPainter, rect: QRect, interval: DetectionInterval):    
        """Draw detection interval as colored bar"""    
        # 信頼度が閾値未満の場合は描画しない
        if interval.confidence_score < self.confidence_threshold:  
            print(f"DEBUG: Skipping interval {interval.start_time}-{interval.end_time} due to low confidence ({interval.confidence_score})")
            return  

        start_x = rect.width() * interval.start_time / self.video_duration    
        end_x = rect.width() * interval.end_time / self.video_duration    
        width = end_x - start_x    

        alpha = int(interval.confidence_score * 255)    
        # ドラッグ中の区間は特別な色で表示  
        if self.is_dragging and interval == self.dragging_interval:  
            if self.drag_mode == 'move':  
                color = QColor(255, 165, 0, alpha)  # オレンジ色で移動中を表示  
            else:  
                color = QColor(255, 0, 255, alpha)  # マゼンタ色でリサイズ中を表示  
            border_color = QColor(200, 0, 0)  
        # ハイライト対象かどうかで色を変更  
        elif (self.highlighted_interval and   
            interval.start_time == self.highlighted_interval.start_time and  
            interval.end_time == self.highlighted_interval.end_time):  
            # ハイライト色（黄色）  
            color = QColor(255, 255, 0, alpha)  # 黄色でハイライト  
            border_color = QColor(255, 200, 0)  
        else:  
            # 通常色（青色）  
            color = QColor(0, 150, 255, alpha)  # Blue with varying transparency    
            border_color = QColor(0, 100, 200)  
            
        painter.fillRect(int(start_x), rect.top() + 10, int(width), rect.height() - 20, color)    
            
        # Draw border    
        painter.setPen(QPen(border_color, 2))    
        painter.drawRect(int(start_x), rect.top() + 10, int(width), rect.height() - 20)

    def set_confidence_threshold(self, threshold: float):  
        """confidence閾値を設定し、表示を更新"""  
        self.confidence_threshold = threshold  
        self.update()  # 再描画をトリガー

    def get_interval_at_position(self, pos):  
        """指定位置にある区間を取得"""  
        if self.video_duration <= 0:  
            return None  
        
        click_time = (pos.x() / self.width()) * self.video_duration  
        
        for interval in self.intervals:  
            if (interval.confidence_score >= self.confidence_threshold and  
                interval.start_time <= click_time <= interval.end_time):  
                return interval  
        return None

    def on_interval_enter(self, interval):  
        """区間にマウスが入った時の処理"""  
        #print(f"Entered interval: {interval.start_time}-{interval.end_time}")  
        # 区間のハイライト表示  
        self.highlighted_interval = interval  
        self.update()  
    
    def on_interval_leave(self, interval):  
        """区間からマウスが出た時の処理"""  
        #print(f"Left interval: {interval.start_time}-{interval.end_time}")  
        # ハイライト解除  
        if self.highlighted_interval == interval:  
            self.highlighted_interval = None  
            self.update()

    def draw_new_interval_preview(self, painter: QPainter, rect: QRect):  
        """新規区間作成中のプレビューを描画"""  
        start_x = rect.width() * self.new_interval_start_time / self.video_duration  
        end_x = rect.width() * self.new_interval_end_time / self.video_duration  
        width = end_x - start_x  
        
        # プレビュー用の半透明色（緑色）  
        preview_color = QColor(0, 255, 0, 100)  # 半透明の緑  
        border_color = QColor(0, 200, 0, 200)   # 濃い緑の境界線  
        
        # プレビューボックスを描画  
        painter.fillRect(int(start_x), rect.top() + 10, int(width), rect.height() - 20, preview_color)  
        
        # 点線の境界線を描画  
        pen = QPen(border_color, 2, Qt.PenStyle.DashLine)  
        painter.setPen(pen)  
        painter.drawRect(int(start_x), rect.top() + 10, int(width), rect.height() - 20)

    def keyPressEvent(self, event):  
        """タイムラインのキーイベント処理"""  
        if event.key() == Qt.Key.Key_Delete:  
            # 選択された区間を削除  
            if self.highlighted_interval:  
                self.intervalClicked.emit(self.highlighted_interval)  
        elif event.key() == Qt.Key.Key_Left:  
            # 前の区間に移動  
            self._select_previous_interval()  
        elif event.key() == Qt.Key.Key_Right:  
            # 次の区間に移動  
            self._select_next_interval()  
        else:  
            super().keyPressEvent(event)