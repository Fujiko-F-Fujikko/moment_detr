# TimelineDisplayManager.py (リファクタリング版)  
import logging  
from typing import List, Optional, Dict, Any  
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea  
from PyQt6.QtCore import QObject, pyqtSignal, QTimer  
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush  
  
from UnifiedDataController import UnifiedDataController  
from UnifiedInterval import UnifiedInterval  
from VideoInfo import VideoInfo  
  
logger = logging.getLogger(__name__)  
  
class TimelineDisplayManager(QObject):  
    """タイムライン表示管理クラス（リファクタリング版）"""  
      
    # シグナル定義  
    intervalClicked = pyqtSignal(object)  # UnifiedInterval  
    playheadMoved = pyqtSignal(float)  # position in seconds  
    timelineUpdated = pyqtSignal()  
      
    def __init__(self):  
        super().__init__()  
          
        # データ参照  
        self.unified_data_controller: Optional[UnifiedDataController] = None  
          
        # タイムライン表示設定  
        self.timeline_widgets: List[QWidget] = []  
        self.current_video_duration: float = 0.0  
        self.current_playhead_position: float = 0.0  
        self.highlighted_interval: Optional[UnifiedInterval] = None  
          
        # 表示設定  
        self.pixels_per_second: float = 50.0  
        self.timeline_height: int = 60  
        self.action_timeline_color = QColor(100, 150, 255)  
        self.step_timeline_color = QColor(255, 150, 100)  
        self.playhead_color = QColor(255, 0, 0)  
          
        # 更新タイマー  
        self.update_timer = QTimer()  
        self.update_timer.setSingleShot(True)  
        self.update_timer.timeout.connect(self._perform_update)  
          
        logger.info("TimelineDisplayManager initialized (refactored)")  
      
    def set_unified_data_controller(self, controller: UnifiedDataController):  
        """統一データコントローラーを設定"""  
        self.unified_data_controller = controller  
          
        # データ変更シグナルを接続  
        controller.dataUpdated.connect(self.on_data_updated)  
        controller.intervalAdded.connect(self.on_intervals_changed)  
        controller.intervalModified.connect(self.on_intervals_changed)  
        controller.intervalDeleted.connect(self.on_intervals_changed)  
          
        logger.info("UnifiedDataController set to TimelineDisplayManager")  
      
    def create_timeline_widgets(self, parent_widget: QWidget) -> QWidget:  
        """タイムラインウィジェットを作成"""  
        main_widget = QWidget(parent_widget)  
        layout = QVBoxLayout(main_widget)  
          
        # アクションタイムライン  
        action_timeline = self._create_single_timeline("Actions", "action")  
        layout.addWidget(action_timeline)  
          
        # ステップタイムライン  
        step_timeline = self._create_single_timeline("Steps", "step")  
        layout.addWidget(step_timeline)  
          
        # スクロールエリアに配置  
        scroll_area = QScrollArea()  
        scroll_area.setWidget(main_widget)  
        scroll_area.setWidgetResizable(True)  
        scroll_area.setMinimumHeight(200)  
          
        self.timeline_widgets = [action_timeline, step_timeline]  
          
        logger.info("Timeline widgets created")  
        return scroll_area  
      
    def _create_single_timeline(self, title: str, interval_type: str) -> QWidget:  
        """単一のタイムラインウィジェットを作成"""  
        timeline_widget = TimelineWidget(title, interval_type, self)  
        timeline_widget.setMinimumHeight(self.timeline_height)  
        timeline_widget.intervalClicked.connect(self.on_interval_clicked)  
        timeline_widget.playheadMoved.connect(self.on_playhead_moved)  
          
        return timeline_widget  
      
    def update_all_timelines(self):  
        """全タイムラインを更新"""  
        logger.info("Updating all timelines")  
          
        # タイマーを使用して更新を遅延実行（連続更新を防ぐ）  
        self.update_timer.stop()  
        self.update_timer.start(50)  # 50ms後に更新  
      
    def _perform_update(self):  
        """実際の更新処理"""  
        if not self.unified_data_controller:  
            return  
          
        # 各タイムラインウィジェットを更新  
        for widget in self.timeline_widgets:  
            if hasattr(widget, 'update_display'):  
                widget.update_display()  
          
        self.timelineUpdated.emit()  
        logger.info("Timeline display updated")  
      
    def set_video_duration(self, duration: float):  
        """動画の長さを設定"""  
        self.current_video_duration = duration  
          
        # 各タイムラインウィジェットに通知  
        for widget in self.timeline_widgets:  
            if hasattr(widget, 'set_duration'):  
                widget.set_duration(duration)  
          
        logger.info(f"Video duration set to: {duration} seconds")  
      
    def update_playhead_position(self, position: float):  
        """プレイヘッド位置を更新"""  
        self.current_playhead_position = position  
          
        # 各タイムラインウィジェットのプレイヘッドを更新  
        for widget in self.timeline_widgets:  
            if hasattr(widget, 'set_playhead_position'):  
                widget.set_playhead_position(position)  
          
        # 必要に応じてスクロール位置を調整  
        self._auto_scroll_to_playhead(position)  
      
    def set_highlighted_interval(self, interval: UnifiedInterval):  
        """ハイライト表示する区間を設定"""  
        self.highlighted_interval = interval  
          
        # 各タイムラインウィジェットにハイライト情報を通知  
        for widget in self.timeline_widgets:  
            if hasattr(widget, 'set_highlighted_interval'):  
                widget.set_highlighted_interval(interval)  
          
        logger.info(f"Highlighted interval set: {interval.interval_id}")  
      
    def clear_highlighted_interval(self):  
        """ハイライト表示をクリア"""  
        self.highlighted_interval = None  
          
        for widget in self.timeline_widgets:  
            if hasattr(widget, 'clear_highlighted_interval'):  
                widget.clear_highlighted_interval()  
          
        logger.info("Highlighted interval cleared")  
      
    def _auto_scroll_to_playhead(self, position: float):  
        """プレイヘッド位置に自動スクロール"""  
        # スクロールエリアがある場合の自動スクロール処理  
        # 実装は必要に応じて追加  
        pass  
      
    def get_intervals_for_timeline(self, interval_type: str) -> List[UnifiedInterval]:  
        """指定タイプの区間を取得"""  
        if not self.unified_data_controller:  
            return []  
          
        filtered_intervals = self.unified_data_controller.get_filtered_intervals()  
        return [interval for interval in filtered_intervals   
                if interval.interval_type == interval_type]  
      
    def on_data_updated(self):  
        """データ更新時の処理"""  
        self.update_all_timelines()  
      
    def on_intervals_changed(self, interval_id: str = ""):  
        """区間変更時の処理"""  
        self.update_all_timelines()  
      
    def on_interval_clicked(self, interval: UnifiedInterval):  
        """区間クリック時の処理"""  
        logger.info(f"Interval clicked: {interval.interval_id}")  
        self.set_highlighted_interval(interval)  
        self.intervalClicked.emit(interval)  
      
    def on_playhead_moved(self, position: float):  
        """プレイヘッド移動時の処理"""  
        self.update_playhead_position(position)  
        self.playheadMoved.emit(position)  
      
    def get_current_state(self) -> Dict[str, Any]:  
        """現在の状態を取得（デバッグ用）"""  
        return {  
            'video_duration': self.current_video_duration,  
            'playhead_position': self.current_playhead_position,  
            'highlighted_interval_id': self.highlighted_interval.interval_id if self.highlighted_interval else None,  
            'timeline_widgets_count': len(self.timeline_widgets),  
            'pixels_per_second': self.pixels_per_second,  
            'has_unified_data_controller': self.unified_data_controller is not None  
        }  
  
  
class TimelineWidget(QWidget):  
    """個別のタイムラインウィジェット"""  
      
    intervalClicked = pyqtSignal(object)  # UnifiedInterval  
    playheadMoved = pyqtSignal(float)  # position  
      
    def __init__(self, title: str, interval_type: str, manager: TimelineDisplayManager):  
        super().__init__()  
        self.title = title  
        self.interval_type = interval_type  
        self.manager = manager  
          
        # 表示状態  
        self.duration = 0.0  
        self.playhead_position = 0.0  
        self.highlighted_interval: Optional[UnifiedInterval] = None  
          
        # 描画設定  
        self.background_color = QColor(240, 240, 240)  
        self.interval_color = manager.action_timeline_color if interval_type == "action" else manager.step_timeline_color  
        self.highlight_color = QColor(255, 255, 0, 100)  
          
        self.setMinimumHeight(manager.timeline_height)  
          
        logger.info(f"TimelineWidget created: {title} ({interval_type})")  
      
    def set_duration(self, duration: float):  
        """動画の長さを設定"""  
        self.duration = duration  
        self.update()  
      
    def set_playhead_position(self, position: float):  
        """プレイヘッド位置を設定"""  
        self.playhead_position = position  
        self.update()  
      
    def set_highlighted_interval(self, interval: UnifiedInterval):  
        """ハイライト区間を設定"""  
        if interval.interval_type == self.interval_type:  
            self.highlighted_interval = interval  
            self.update()  
      
    def clear_highlighted_interval(self):  
        """ハイライトをクリア"""  
        self.highlighted_interval = None  
        self.update()  
      
    def update_display(self):  
        """表示を更新"""  
        self.update()  
      
    def paintEvent(self, event):  
        """描画イベント"""  
        painter = QPainter(self)  
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)  
          
        # 背景を描画  
        painter.fillRect(self.rect(), self.background_color)  
          
        # タイトルを描画  
        painter.setPen(QPen(QColor(0, 0, 0)))  
        painter.drawText(10, 20, self.title)  
          
        if self.duration <= 0:  
            return  
          
        # 区間を描画  
        self._draw_intervals(painter)  
          
        # プレイヘッドを描画  
        self._draw_playhead(painter)  
          
        # ハイライト区間を描画  
        if self.highlighted_interval:  
            self._draw_highlighted_interval(painter)  
      
    def _draw_intervals(self, painter: QPainter):  
        """区間を描画"""  
        if not self.manager.unified_data_controller:  
            return  
          
        intervals = self.manager.get_intervals_for_timeline(self.interval_type)  
          
        painter.setPen(QPen(self.interval_color, 2))  
        painter.setBrush(QBrush(self.interval_color))  
          
        timeline_y = 30  
        timeline_height = 20  
          
        for interval in intervals:  
            start_x = self._time_to_pixel(interval.start_time)  
            end_x = self._time_to_pixel(interval.end_time)  
            width = max(end_x - start_x, 2)  # 最小幅2ピクセル  
              
            # 区間の矩形を描画  
            painter.drawRect(start_x, timeline_y, width, timeline_height)  
              
            # 信頼度に応じて透明度を調整  
            alpha = int(255 * interval.confidence_score)  
            color_with_alpha = QColor(self.interval_color)  
            color_with_alpha.setAlpha(alpha)  
            painter.setBrush(QBrush(color_with_alpha))  
      
    def _draw_playhead(self, painter: QPainter):  
        """プレイヘッドを描画"""  
        playhead_x = self._time_to_pixel(self.playhead_position)  
          
        painter.setPen(QPen(self.manager.playhead_color, 2))  
        painter.drawLine(playhead_x, 0, playhead_x, self.height())  
      
    def _draw_highlighted_interval(self, painter: QPainter):  
        """ハイライト区間を描画"""  
        if not self.highlighted_interval:  
            return  
          
        start_x = self._time_to_pixel(self.highlighted_interval.start_time)  
        end_x = self._time_to_pixel(self.highlighted_interval.end_time)  
        width = max(end_x - start_x, 2)  
          
        painter.setPen(QPen(self.highlight_color, 3))  
        painter.setBrush(QBrush(self.highlight_color))  
        painter.drawRect(start_x, 25, width, 30)  
      
    def _time_to_pixel(self, time_seconds: float) -> int:  
        """時間をピクセル座標に変換"""  
        return int(time_seconds * self.manager.pixels_per_second)  
      
    def _pixel_to_time(self, pixel_x: int) -> float:  
        """ピクセル座標を時間に変換"""  
        return pixel_x / self.manager.pixels_per_second  
      
    def mousePressEvent(self, event):  
        """マウスクリックイベント"""  
        click_time = self._pixel_to_time(event.position().x())  
          
        # クリックされた区間を検索  
        clicked_interval = self._find_interval_at_position(click_time)  
          
        if clicked_interval:  
            self.intervalClicked.emit(clicked_interval)  
        else:  
            # 空白領域クリック時はプレイヘッド移動  
            self.playheadMoved.emit(click_time)  
      
    def _find_interval_at_position(self, time: float) -> Optional[UnifiedInterval]:  
        """指定時間位置にある区間を検索"""  
        if not self.manager.unified_data_controller:  
            return None  
          
        intervals = self.manager.get_intervals_for_timeline(self.interval_type)  
          
        for interval in intervals:  
            if interval.start_time <= time <= interval.end_time:  
                return interval  
          
        return None  
      
    def mouseMoveEvent(self, event):  
        """マウス移動イベント"""  
        # ホバー処理やドラッグ処理を実装  
        pass  
      
    def mouseReleaseEvent(self, event):  
        """マウスリリースイベント"""  
        # ドラッグ終了処理を実装  
        pass

    def set_query_results(self, query_results_list=None, stt_data_manager=None, video_name: str = None):  
        """既存のインターフェースとの互換性を保つメソッド"""  
        # 既存のコードとの互換性のため、このメソッドは残すが内部的には統一データコントローラーを使用  
        logger.info("set_query_results called (compatibility method)")  
          
        if self.unified_data_controller:  
            # 統一データコントローラーが設定されている場合は、そちらのデータを使用  
            self.update_all_timelines()  
        else:  
            logger.warning("UnifiedDataController not set, cannot update timelines")  
      
    def clear_timelines(self):  
        """タイムラインをクリア"""  
        for widget in self.timeline_widgets:  
            widget.deleteLater()  
          
        self.timeline_widgets.clear()  
        logger.info("Timelines cleared")  
      
    def create_steps_timeline(self, stt_data_manager=None, video_name: str = None) -> Optional[QWidget]:  
        """ステップタイムライン作成（互換性メソッド）"""  
        # 統一データコントローラーからステップデータを取得  
        if not self.unified_data_controller:  
            return None  
          
        return self._create_single_timeline("Steps", "step")  
      
    def _group_results_by_hand_type(self, query_results_list) -> Dict[str, List]:  
        """手タイプ別グループ化（互換性メソッド）"""  
        # 統一データコントローラーを使用する場合は不要だが、互換性のため残す  
        return {"All": []}  
      
    def set_confidence_threshold(self, threshold: float):  
        """信頼度閾値設定"""  
        if self.unified_data_controller:  
            self.unified_data_controller.set_confidence_threshold(threshold)  
          
        # 各タイムラインウィジェットに通知  
        for widget in self.timeline_widgets:  
            if hasattr(widget, 'set_confidence_threshold'):  
                widget.set_confidence_threshold(threshold)  
      
    def _update_widget_cursor(self, cursor):  
        """ウィジェットカーソル更新"""  
        for widget in self.timeline_widgets:  
            widget.setCursor(cursor)