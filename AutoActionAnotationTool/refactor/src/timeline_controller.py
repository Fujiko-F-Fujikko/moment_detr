# timeline_controller.py
"""
タイムラインコントロールクラス
タイムライン表示とインタラクション制御
"""

from PyQt6.QtCore import QObject, pyqtSignal, Qt, QPointF, QRectF
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QFontMetrics
import logging
from typing import List, Optional, Dict, Any, Tuple

from annotation_data_manager import AnnotationDataManager, AnnotationItem


class TimelineTrack(QWidget):
    """タイムライントラック（1つのアノテーションタイプ用）"""
    
    interval_clicked = pyqtSignal(object)  # AnnotationItem
    interval_drag_started = pyqtSignal(object)  # AnnotationItem
    interval_drag_moved = pyqtSignal(object, float, float)  # AnnotationItem, start, end
    interval_drag_finished = pyqtSignal(object, float, float)  # AnnotationItem, start, end
    new_interval_created = pyqtSignal(float, float, str)  # start, end, annotation_type
    position_clicked = pyqtSignal(float)  # time_position
    
    def __init__(self, annotation_type: str, track_height: int = 60):
        super().__init__()
        self.annotation_type = annotation_type
        self.track_height = track_height
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{annotation_type}")
        
        # 表示設定
        self.setFixedHeight(track_height)
        self.setMinimumWidth(800)
        
        # データ
        self.annotations: List[AnnotationItem] = []
        self.video_duration = 0.0
        self.current_position = 0.0
        self.pixels_per_second = 100.0
        
        # インタラクション状態
        self.dragging_annotation: Optional[AnnotationItem] = None
        self.drag_start_pos = None
        self.drag_edge = None  # 'left', 'right', 'center'
        self.highlighted_annotation: Optional[AnnotationItem] = None
        self.creating_interval = False
        self.creation_start_pos = None
        
        # 色設定
        self.colors = {
            'action': QColor(100, 150, 255, 180),
            'step': QColor(255, 150, 100, 180),
            'background': QColor(40, 40, 40),
            'grid': QColor(80, 80, 80),
            'playhead': QColor(255, 255, 0),
            'highlight': QColor(255, 255, 255, 100)
        }
        
        self.setMouseTracking(True)
        self.logger.info(f"TimelineTrack created for {annotation_type}")
    
    def set_annotations(self, annotations: List[AnnotationItem]):
        """アノテーション設定"""
        self.annotations = [ann for ann in annotations if ann.annotation_type.lower() == self.annotation_type.lower()]
        self.logger.debug(f"Set {len(self.annotations)} {self.annotation_type} annotations")
        self.update()
    
    def set_video_duration(self, duration: float):
        """動画長さ設定"""
        self.video_duration = duration
        self._update_width()
        self.update()
    
    def set_current_position(self, position: float):
        """現在位置設定"""
        self.current_position = position
        self.update()
    
    def set_highlighted_annotation(self, annotation: Optional[AnnotationItem]):
        """ハイライトアノテーション設定"""
        self.highlighted_annotation = annotation
        self.update()
    
    def _update_width(self):
        """ウィジェット幅更新"""
        if self.video_duration > 0:
            width = int(self.video_duration * self.pixels_per_second) + 100
            self.setMinimumWidth(width)
    
    def _time_to_x(self, time: float) -> float:
        """時間をX座標に変換"""
        return time * self.pixels_per_second + 50  # 50pxのマージン
    
    def _x_to_time(self, x: float) -> float:
        """X座標を時間に変換"""
        return max(0, (x - 50) / self.pixels_per_second)
    
    def paintEvent(self, event):
        """描画処理"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 背景
        painter.fillRect(self.rect(), self.colors['background'])
        
        # グリッド線描画
        self._draw_grid(painter)
        
        # アノテーション描画
        self._draw_annotations(painter)
        
        # プレイヘッド描画
        self._draw_playhead(painter)
        
        # トラックラベル描画
        self._draw_track_label(painter)
    
    def _draw_grid(self, painter: QPainter):
        """グリッド線描画"""
        if self.video_duration <= 0:
            return
        
        painter.setPen(QPen(self.colors['grid'], 1))
        
        # 秒単位のグリッド
        second_interval = 1.0
        if self.pixels_per_second < 50:
            second_interval = 10.0
        elif self.pixels_per_second < 20:
            second_interval = 30.0
        
        for second in range(0, int(self.video_duration) + 1, int(second_interval)):
            x = self._time_to_x(second)
            painter.drawLine(int(x), 0, int(x), self.height())
    
    def _draw_annotations(self, painter: QPainter):
        """アノテーション描画"""
        for annotation in self.annotations:
            self._draw_annotation(painter, annotation)
    
    def _draw_annotation(self, painter: QPainter, annotation: AnnotationItem):
        """単一アノテーション描画"""
        start_x = self._time_to_x(annotation.start_time)
        end_x = self._time_to_x(annotation.end_time)
        width = end_x - start_x
        
        if width < 2:  # 最小幅
            width = 2
            end_x = start_x + width
        
        # 色選択
        color = self.colors.get(annotation.annotation_type, self.colors['action'])
        
        # ハイライト表示
        if annotation == self.highlighted_annotation:
            highlight_color = QColor(color)
            highlight_color.setAlpha(255)
            painter.setBrush(QBrush(highlight_color))
            painter.setPen(QPen(self.colors['highlight'], 2))
        else:
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color.darker(), 1))
        
        # 矩形描画
        rect = QRectF(start_x, 10, width, self.height() - 20)
        painter.drawRoundedRect(rect, 3, 3)
        
        # テキスト描画
        self._draw_annotation_text(painter, annotation, rect)
    
    def _draw_annotation_text(self, painter: QPainter, annotation: AnnotationItem, rect: QRectF):
        """アノテーションテキスト描画"""
        if rect.width() < 30:  # 幅が狭すぎる場合はテキストを描画しない
            return
        
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        
        # テキスト内容
        text = annotation.category
        if len(text) > 20:
            text = text[:17] + "..."
        
        # テキスト描画
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
    
    def _draw_playhead(self, painter: QPainter):
        """プレイヘッド描画"""
        if self.video_duration <= 0:
            return
        
        x = self._time_to_x(self.current_position)
        painter.setPen(QPen(self.colors['playhead'], 2))
        painter.drawLine(int(x), 0, int(x), self.height())
    
    def _draw_track_label(self, painter: QPainter):
        """トラックラベル描画"""
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        
        # ラベルテキスト
        label = self.annotation_type.capitalize()
        
        # 背景矩形
        fm = QFontMetrics(font)
        text_rect = fm.boundingRect(label)
        bg_rect = QRectF(5, 5, text_rect.width() + 10, text_rect.height() + 6)
        
        painter.fillRect(bg_rect, QColor(0, 0, 0, 150))
        painter.drawText(bg_rect, Qt.AlignmentFlag.AlignCenter, label)
    
    def mousePressEvent(self, event):
        """マウスプレス処理"""
        if event.button() == Qt.MouseButton.LeftButton:
            time_pos = self._x_to_time(event.position().x())
            annotation = self._get_annotation_at_position(event.position())
            
            if annotation:
                self._start_drag(annotation, event.position())
                self.interval_clicked.emit(annotation)
            elif event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                # Ctrl+クリックで新規区間作成開始
                self._start_interval_creation(event.position())
            else:
                # 空白エリアクリック
                self.position_clicked.emit(time_pos)
    
    def mouseMoveEvent(self, event):
        """マウス移動処理"""
        if self.dragging_annotation:
            self._handle_drag_move(event.position())
        elif self.creating_interval:
            self._handle_interval_creation_move(event.position())
    
    def mouseReleaseEvent(self, event):
        """マウスリリース処理"""
        if self.dragging_annotation:
            self._finish_drag(event.position())
        elif self.creating_interval:
            self._finish_interval_creation(event.position())
    
    def _get_annotation_at_position(self, pos: QPointF) -> Optional[AnnotationItem]:
        """位置にあるアノテーション取得"""
        time_pos = self._x_to_time(pos.x())
        
        for annotation in self.annotations:
            if annotation.start_time <= time_pos <= annotation.end_time:
                return annotation
        return None
    
    def _start_drag(self, annotation: AnnotationItem, pos: QPointF):
        """ドラッグ開始"""
        self.dragging_annotation = annotation
        self.drag_start_pos = pos
        
        # エッジ判定
        start_x = self._time_to_x(annotation.start_time)
        end_x = self._time_to_x(annotation.end_time)
        
        if abs(pos.x() - start_x) < 10:
            self.drag_edge = 'left'
        elif abs(pos.x() - end_x) < 10:
            self.drag_edge = 'right'
        else:
            self.drag_edge = 'center'
        
        self.interval_drag_started.emit(annotation)
        self.logger.debug(f"Started dragging {annotation.id} ({self.drag_edge})")
    
    def _handle_drag_move(self, pos: QPointF):
        """ドラッグ移動処理"""
        if not self.dragging_annotation:
            return
        
        time_pos = self._x_to_time(pos.x())
        annotation = self.dragging_annotation
        
        if self.drag_edge == 'left':
            new_start = max(0, time_pos)
            new_end = annotation.end_time
            if new_start >= new_end:
                new_start = new_end - 0.1
        elif self.drag_edge == 'right':
            new_start = annotation.start_time
            new_end = min(self.video_duration, time_pos)
            if new_end <= new_start:
                new_end = new_start + 0.1
        else:  # center
            duration = annotation.end_time - annotation.start_time
            new_start = max(0, time_pos - duration / 2)
            new_end = new_start + duration
            if new_end > self.video_duration:
                new_end = self.video_duration
                new_start = new_end - duration
        
        self.interval_drag_moved.emit(annotation, new_start, new_end)
    
    def _finish_drag(self, pos: QPointF):
        """ドラッグ終了"""
        if not self.dragging_annotation:
            return
        
        time_pos = self._x_to_time(pos.x())
        annotation = self.dragging_annotation
        
        # 最終位置計算（_handle_drag_moveと同じロジック）
        if self.drag_edge == 'left':
            new_start = max(0, time_pos)
            new_end = annotation.end_time
            if new_start >= new_end:
                new_start = new_end - 0.1
        elif self.drag_edge == 'right':
            new_start = annotation.start_time
            new_end = min(self.video_duration, time_pos)
            if new_end <= new_start:
                new_end = new_start + 0.1
        else:  # center
            duration = annotation.end_time - annotation.start_time
            new_start = max(0, time_pos - duration / 2)
            new_end = new_start + duration
            if new_end > self.video_duration:
                new_end = self.video_duration
                new_start = new_end - duration
        
        self.interval_drag_finished.emit(annotation, new_start, new_end)
        
        # ドラッグ状態リセット
        self.dragging_annotation = None
        self.drag_start_pos = None
        self.drag_edge = None
        
        self.logger.debug(f"Finished dragging {annotation.id}")
    
    def _start_interval_creation(self, pos: QPointF):
        """区間作成開始"""
        self.creating_interval = True
        self.creation_start_pos = pos
        self.logger.debug("Started interval creation")
    
    def _handle_interval_creation_move(self, pos: QPointF):
        """区間作成移動処理"""
        # 作成中の区間をプレビュー表示（実装簡略化のため省略）
        pass
    
    def _finish_interval_creation(self, pos: QPointF):
        """区間作成終了"""
        if not self.creating_interval or not self.creation_start_pos:
            return
        
        start_time = self._x_to_time(self.creation_start_pos.x())
        end_time = self._x_to_time(pos.x())
        
        if start_time > end_time:
            start_time, end_time = end_time, start_time
        
        if end_time - start_time < 0.1:  # 最小長さ
            end_time = start_time + 0.1
        
        self.new_interval_created.emit(start_time, end_time, self.annotation_type)
        
        # 作成状態リセット
        self.creating_interval = False
        self.creation_start_pos = None
        
        self.logger.debug(f"Created new {self.annotation_type} interval: {start_time:.2f}-{end_time:.2f}")


class TimelineController(QObject):
    """タイムラインコントロールクラス"""
    
    interval_clicked = pyqtSignal(object)      # AnnotationItem
    interval_drag_started = pyqtSignal(object) # AnnotationItem
    interval_drag_moved = pyqtSignal(object, float, float)  # AnnotationItem, start, end
    interval_drag_finished = pyqtSignal(object, float, float)  # AnnotationItem, start, end
    new_interval_created = pyqtSignal(float, float, str)  # start, end, annotation_type
    position_clicked = pyqtSignal(float)  # time_position
    
    def __init__(self, data_manager: AnnotationDataManager):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.data_manager = data_manager
        
        # UIコンポーネント
        self.timeline_widget = None
        self.tracks: Dict[str, TimelineTrack] = {}
        
        # 状態
        self.video_duration = 0.0
        self.current_position = 0.0
        
        self._setup_timeline_widget()
        self._connect_data_manager()
        
        self.logger.info("TimelineController initialized")
    
    def _setup_timeline_widget(self):
        """タイムラインウィジェット設定"""
        self.timeline_widget = QWidget()
        layout = QVBoxLayout(self.timeline_widget)
        
        # スクロールエリア
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # トラックコンテナ
        tracks_container = QWidget()
        tracks_layout = QVBoxLayout(tracks_container)
        
        # アクショントラック
        action_track = TimelineTrack('action')
        self.tracks['action'] = action_track
        self._connect_track_signals(action_track)
        tracks_layout.addWidget(action_track)
        
        # ステップトラック
        step_track = TimelineTrack('step')
        self.tracks['step'] = step_track
        self._connect_track_signals(step_track)
        tracks_layout.addWidget(step_track)
        
        tracks_layout.addStretch()
        
        scroll_area.setWidget(tracks_container)
        layout.addWidget(scroll_area)
    
    def _connect_track_signals(self, track: TimelineTrack):
        """トラックシグナル接続"""
        track.interval_clicked.connect(self.interval_clicked.emit)
        track.interval_drag_started.connect(self.interval_drag_started.emit)
        track.interval_drag_moved.connect(self.interval_drag_moved.emit)
        track.interval_drag_finished.connect(self.interval_drag_finished.emit)
        track.new_interval_created.connect(self.new_interval_created.emit)
        track.position_clicked.connect(self.position_clicked.emit)
    
    def _connect_data_manager(self):
        """データマネージャーとの接続"""
        self.data_manager.data_changed.connect(self.update_timeline)
        self.data_manager.annotation_added.connect(self.update_timeline)
        self.data_manager.annotation_modified.connect(self.update_timeline)
        self.data_manager.annotation_deleted.connect(self.update_timeline)
        self.data_manager.video_loaded.connect(self._on_video_loaded)
    
    def _on_video_loaded(self, video_info):
        """動画読み込み時の処理"""
        self.set_video_duration(video_info.duration)
    
    def set_video_duration(self, duration: float):
        """動画長さ設定"""
        self.logger.info(f"Setting video duration: {duration} seconds")
        self.video_duration = duration
        
        for track in self.tracks.values():
            track.set_video_duration(duration)
    
    def set_current_position(self, position: float):
        """現在位置設定"""
        self.logger.debug(f"Setting current position: {position} seconds")
        self.current_position = position
        
        for track in self.tracks.values():
            track.set_current_position(position)
    
    def set_highlighted_annotation(self, annotation: Optional[AnnotationItem]):
        """ハイライトアノテーション設定"""
        for track in self.tracks.values():
            track.set_highlighted_annotation(annotation)
    
    def update_timeline(self):
        """タイムライン更新"""
        self.logger.debug("Updating timeline")
        annotations = self.data_manager.get_filtered_annotations()
        
        for annotation_type, track in self.tracks.items():
            track.set_annotations(annotations)
    
    def get_timeline_widget(self) -> QWidget:
        """タイムラインウィジェット取得"""
        return self.timeline_widget
    
    def clear_highlights(self):
        """ハイライトクリア"""
        self.set_highlighted_annotation(None)
