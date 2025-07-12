# TimelineRenderer.py  
from PyQt6.QtGui import QPainter, QColor, QPen  
from PyQt6.QtCore import QRect, Qt  
from typing import List, Optional  
from DetectionInterval import DetectionInterval  
from TimelineData import TimelineData
  
class TimelineRenderer:  
    """タイムライン描画処理に特化したクラス"""  
      
    def __init__(self):  
        self.background_color = QColor(240, 240, 240)  
        self.playhead_color = QColor(255, 0, 0)  
        self.playhead_width = 3  
        self.interval_margin = 10  
        self.time_scale_color = QColor(200, 200, 200)  
        self.preview_color = QColor(0, 255, 0, 100)  
        self.preview_border_color = QColor(0, 200, 0, 200)  
      
    def render_timeline(self, painter: QPainter, rect: QRect, timeline_data: 'TimelineData'):  
        """タイムライン全体を描画"""  
        if timeline_data.video_duration <= 0:  
            return  
          
        # 背景描画  
        self.draw_background(painter, rect)  
          
        # 時間スケール描画（有効な場合）  
        if timeline_data.time_scale_enabled:  
            self.draw_time_scale(painter, rect, timeline_data.video_duration)  
          
        # Saliencyヒートマップ描画（時間スケール無効かつデータがある場合）  
        elif timeline_data.saliency_scores:  
            self.draw_saliency_heatmap(painter, rect, timeline_data)  
          
        # 区間描画  
        for interval in timeline_data.intervals:  
            self.draw_interval(painter, rect, interval, timeline_data)  
          
        # 新規区間プレビュー描画  
        if timeline_data.is_creating_new_interval and timeline_data.new_interval_preview:  
            self.draw_new_interval_preview(painter, rect, timeline_data)  
          
        # プレイヘッド描画  
        self.draw_playhead(painter, rect, timeline_data.current_position, timeline_data.video_duration)  
      
    def draw_background(self, painter: QPainter, rect: QRect):  
        """背景を描画"""  
        painter.fillRect(rect, self.background_color)  
      
    def draw_time_scale(self, painter: QPainter, rect: QRect, video_duration: float):  
        """時間目盛りを描画"""  
        if video_duration <= 0:  
            return  
          
        # 適切な目盛り間隔を計算  
        scale_interval = self._calculate_scale_interval(video_duration)  
          
        # 目盛りの描画  
        pen = QPen(self.time_scale_color)  
        painter.setPen(pen)  
          
        current_time = 0  
        while current_time <= video_duration:  
            x_pos = int((current_time / video_duration) * rect.width())  
              
            # 縦線を描画  
            painter.drawLine(x_pos, rect.top(), x_pos, rect.bottom())  
              
            # 時間ラベルを描画  
            painter.drawText(x_pos + 2, rect.top() + 15, f"{current_time:.1f}s")  
              
            current_time += scale_interval  
      
    def draw_saliency_heatmap(self, painter: QPainter, rect: QRect, timeline_data: 'TimelineData'):  
        """Saliencyスコアをヒートマップとして描画"""  
        clip_width = rect.width() * timeline_data.clip_duration / timeline_data.video_duration  
          
        for i, score in enumerate(timeline_data.saliency_scores):  
            x = i * clip_width  
            if x >= rect.width():  
                break  
              
            # スコアを0-1範囲に正規化  
            normalized_score = max(0, min(1, (score + 1) / 2))  # [-1, 1] → [0, 1]  
            alpha = int(normalized_score * 128)  # 半透明  
              
            color = QColor(255, int(255 * (1 - normalized_score)), 0, alpha)  # 赤から黄色  
            painter.fillRect(int(x), rect.top(), int(clip_width), rect.height(), color)  
      
    def draw_interval(self, painter: QPainter, rect: QRect, interval: DetectionInterval, timeline_data: 'TimelineData'):  
        """検出区間を描画"""  
        # 信頼度閾値チェック  
        if interval.confidence_score < timeline_data.confidence_threshold:  
            return  
          
        start_x = rect.width() * interval.start_time / timeline_data.video_duration  
        end_x = rect.width() * interval.end_time / timeline_data.video_duration  
        width = end_x - start_x  
          
        alpha = int(interval.confidence_score * 255)  
          
        # 状態に応じた色選択  
        color, border_color = self._get_interval_colors(interval, timeline_data, alpha)  
          
        # 区間本体を描画  
        painter.fillRect(  
            int(start_x),   
            rect.top() + self.interval_margin,   
            int(width),   
            rect.height() - 2 * self.interval_margin,   
            color  
        )  
          
        # 境界線を描画  
        painter.setPen(QPen(border_color, 2))  
        painter.drawRect(  
            int(start_x),   
            rect.top() + self.interval_margin,   
            int(width),   
            rect.height() - 2 * self.interval_margin  
        )  
      
    def draw_new_interval_preview(self, painter: QPainter, rect: QRect, timeline_data: 'TimelineData'):  
        """新規区間作成プレビューを描画"""  
        preview = timeline_data.new_interval_preview  
        start_x = rect.width() * preview.start_time / timeline_data.video_duration  
        end_x = rect.width() * preview.end_time / timeline_data.video_duration  
        width = end_x - start_x  
          
        # プレビューボックスを描画  
        painter.fillRect(  
            int(start_x),   
            rect.top() + self.interval_margin,   
            int(width),   
            rect.height() - 2 * self.interval_margin,   
            self.preview_color  
        )  
          
        # 点線の境界線を描画  
        pen = QPen(self.preview_border_color, 2, Qt.PenStyle.DashLine)  
        painter.setPen(pen)  
        painter.drawRect(  
            int(start_x),   
            rect.top() + self.interval_margin,   
            int(width),   
            rect.height() - 2 * self.interval_margin  
        )  
      
    def draw_playhead(self, painter: QPainter, rect: QRect, current_position: float, video_duration: float):  
        """プレイヘッドを描画"""  
        if current_position > 0 and video_duration > 0:  
            pos_x = rect.width() * current_position / video_duration  
            painter.setPen(QPen(self.playhead_color, self.playhead_width))  
            painter.drawLine(int(pos_x), rect.top(), int(pos_x), rect.bottom())  
      
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
      
    def _get_interval_colors(self, interval: DetectionInterval, timeline_data: 'TimelineData', alpha: int) -> tuple:  
        """区間の状態に応じた色を取得"""  
        # ドラッグ中の区間  
        if timeline_data.is_dragging and interval == timeline_data.dragging_interval:  
            if timeline_data.drag_mode == 'move':  
                return QColor(255, 165, 0, alpha), QColor(200, 0, 0)  # オレンジ  
            else:  
                return QColor(255, 0, 255, alpha), QColor(200, 0, 0)  # マゼンタ  
          
        # ハイライト対象  
        elif (timeline_data.highlighted_interval and   
              interval.start_time == timeline_data.highlighted_interval.start_time and  
              interval.end_time == timeline_data.highlighted_interval.end_time):  
            return QColor(255, 255, 0, alpha), QColor(255, 200, 0)  # 黄色  
          
        # 通常色  
        else:  
            return QColor(0, 150, 255, alpha), QColor(0, 100, 200)  # 青色  