# DisplayManager.py  
import logging  
from typing import Optional  
from PyQt6.QtCore import QObject  
  
from UnifiedDataController import UnifiedDataController  
from UnifiedInterval import UnifiedInterval  
  
logger = logging.getLogger(__name__)  
  
class DisplayManager(QObject):  
    """表示管理クラス"""  
      
    def __init__(self, data_controller: UnifiedDataController):  
        super().__init__()  
        self.data_controller = data_controller  
        self.timeline_renderer = None  # TimelineRendererは既存クラスを使用  
          
        # データ変更の監視  
        self.data_controller.dataUpdated.connect(self.refresh_timeline_display)  
        self.data_controller.intervalAdded.connect(self.refresh_timeline_display)  
        self.data_controller.intervalModified.connect(self.refresh_timeline_display)  
        self.data_controller.intervalDeleted.connect(self.refresh_timeline_display)  
          
        logger.info("DisplayManager initialized")  
      
    def refresh_timeline_display(self):  
        """タイムライン表示を更新"""  
        if self.timeline_renderer:  
            self.timeline_renderer.update()  
            logger.info("Timeline display refreshed")  
      
    def update_interval_colors(self):  
        """区間の色を更新"""  
        # 区間タイプに応じた色分け  
        intervals = self.data_controller.get_filtered_intervals()  
          
        for interval in intervals:  
            if interval.is_action_type():  
                # アクション区間の色設定  
                pass  
            else:  
                # ステップ区間の色設定  
                pass  
          
        logger.info("Interval colors updated")  
      
    def handle_interval_selection(self, interval: UnifiedInterval):  
        """区間選択時の処理"""  
        logger.info(f"Interval selected: {interval.interval_id}")  
        # タイムライン上でハイライト表示  
        if self.timeline_renderer:  
            self.timeline_renderer.highlight_interval(interval)  
      
    def synchronize_with_video_position(self, position: float):  
        """動画位置との同期"""  
        logger.info(f"Synchronizing with video position: {position}")  
        # 現在位置に対応する区間をハイライト  
        intervals = self.data_controller.get_filtered_intervals()  
          
        for interval in intervals:  
            if interval.start_time <= position <= interval.end_time:  
                # 現在位置にある区間をハイライト  
                self.handle_interval_selection(interval)  
                break