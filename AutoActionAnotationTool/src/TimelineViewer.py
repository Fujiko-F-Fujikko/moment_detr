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
        self.intervals = []  
        self.saliency_scores = []  
        self.setMinimumHeight(100)  
          
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
          
        # Draw saliency heatmap  
        if self.saliency_scores:  
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
      
    def draw_interval(self, painter: QPainter, rect: QRect, interval: DetectionInterval):  
        """Draw detection interval as colored bar"""  
        start_x = rect.width() * interval.start_time / self.video_duration  
        end_x = rect.width() * interval.end_time / self.video_duration  
        width = end_x - start_x  
          
        # Color based on confidence  
        alpha = int(interval.confidence_score * 255)  
        color = QColor(0, 150, 255, alpha)  # Blue with varying transparency  
          
        painter.fillRect(int(start_x), rect.top() + 10, int(width), rect.height() - 20, color)  
          
        # Draw border  
        painter.setPen(QPen(QColor(0, 100, 200), 2))  
        painter.drawRect(int(start_x), rect.top() + 10, int(width), rect.height() - 20)  
      
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