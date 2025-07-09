from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import QRect
from typing import List
from DetectionInterval import DetectionInterval


class TimelineViewer(QWidget):  
    intervalClicked = pyqtSignal(DetectionInterval)  
    timePositionChanged = pyqtSignal(float)  
      
    def __init__(self):  
        super().__init__()  
        self.video_duration = 0.0  
        self.current_position = 0.0  
        self.confidence_threshold = 0.0
        self.intervals = []  
        self.saliency_scores = []  
        self.highlighted_interval = None
        self.setMinimumHeight(100)  
        self.time_scale_enabled = False
          
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
              
        # Convert click position to time  
        click_time = (event.position().x() / self.width()) * self.video_duration  
          
        # Check if clicked on an interval  
        for interval in self.intervals:  
            if interval.start_time <= click_time <= interval.end_time:  
                self.intervalClicked.emit(interval)  
                return  
          
        # Otherwise, seek to clicked position  
        self.timePositionChanged.emit(click_time)

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
            
        # ハイライト対象かどうかで色を変更  
        if (self.highlighted_interval and   
            interval.start_time == self.highlighted_interval.start_time and  
            interval.end_time == self.highlighted_interval.end_time):  
            # ハイライト色（黄色）  
            alpha = int(interval.confidence_score * 255)  
            color = QColor(255, 255, 0, alpha)  # 黄色でハイライト  
            border_color = QColor(255, 200, 0)  
        else:  
            # 通常色（青色）  
            alpha = int(interval.confidence_score * 255)    
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