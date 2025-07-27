# ApplicationCoordinator.py (リファクタリング版)  
import logging  
from typing import Optional  
from PyQt6.QtCore import QObject, pyqtSignal  
  
from UnifiedDataController import UnifiedDataController  
from VideoPlayerController import VideoPlayerController  
from TimelineDisplayManager import TimelineDisplayManager  
from UnifiedIntervalEditor import UnifiedIntervalEditor  
from DisplayManager import DisplayManager  
  
logger = logging.getLogger(__name__)  
  
class ApplicationCoordinator(QObject):  
    """アプリケーション全体のコンポーネント調整を担当するクラス"""  
      
    # シグナル定義  
    videoLoaded = pyqtSignal(str)  # video_path  
    resultsLoaded = pyqtSignal()  
    dataChanged = pyqtSignal()  
      
    def __init__(self, main_window):  
        super().__init__()  
        self.main_window = main_window  
        self.unified_data_controller: Optional[UnifiedDataController] = None  
          
        # UI管理コンポーネント  
        self.timeline_display_manager: Optional[TimelineDisplayManager] = None  
        self.unified_interval_editor: Optional[UnifiedIntervalEditor] = None  
        self.video_player_controller: Optional[VideoPlayerController] = None  
        self.display_manager: Optional[DisplayManager] = None  
          
        # 現在の状態  
        self.current_video_path: str = ""  
        self.current_video_id: str = ""  
          
        logger.info("ApplicationCoordinator initialized")  
      
    def set_unified_data_controller(self, controller: UnifiedDataController):  
        """統一データコントローラーを設定"""  
        self.unified_data_controller = controller  
          
        # データ変更シグナルを接続  
        controller.dataUpdated.connect(self.on_data_updated)  
        controller.intervalAdded.connect(self.on_interval_changed)  
        controller.intervalModified.connect(self.on_interval_changed)  
        controller.intervalDeleted.connect(self.on_interval_changed)  
          
        logger.info("UnifiedDataController set")  
      
    def set_ui_components(self, timeline_manager, interval_editor,   
                         video_controller, display_manager):  
        """UI管理コンポーネントを設定"""  
        self.timeline_display_manager = timeline_manager  
        self.unified_interval_editor = interval_editor  
        self.video_player_controller = video_controller  
        self.display_manager = display_manager  
          
        logger.info("UI components set")  
      
    def load_video(self, video_path: str):  
        """動画を読み込み"""  
        try:  
            logger.info(f"Loading video: {video_path}")  
              
            # 動画プレイヤーに読み込み  
            if self.video_player_controller:  
                self.video_player_controller.load_video(video_path)  
              
            # 現在の動画情報を更新  
            self.current_video_path = video_path  
            self.current_video_id = self._extract_video_id(video_path)  
              
            # 統一エディターに現在の動画を設定  
            if self.unified_interval_editor:  
                self.unified_interval_editor.set_current_video(self.current_video_id)  
              
            # 動画メタデータを統一データコントローラーに追加  
            # （実装は既存のロジックを参考に）  
              
            self.videoLoaded.emit(video_path)  
            logger.info(f"Video loaded successfully: {video_path}")  
              
        except Exception as e:  
            logger.error(f"Failed to load video: {e}")  
      
    def load_inference_results(self, json_path: str):  
        """推論結果を読み込み"""  
        try:  
            logger.info(f"Loading inference results: {json_path}")  
              
            if not self.unified_data_controller:  
                logger.error("UnifiedDataController not set")  
                return  
              
            success = self.unified_data_controller.load_inference_results(json_path)  
              
            if success:  
                self.resultsLoaded.emit()  
                logger.info("Inference results loaded successfully")  
            else:  
                logger.error("Failed to load inference results")  
                  
        except Exception as e:  
            logger.error(f"Error loading inference results: {e}")  
      
    def synchronize_components(self):  
        """全コンポーネントの同期"""  
        logger.info("Synchronizing components")  
          
        # タイムライン表示の更新  
        if self.timeline_display_manager:  
            self.timeline_display_manager.update_all_timelines()  
          
        # 表示管理の更新  
        if self.display_manager:  
            self.display_manager.refresh_timeline_display()  
          
        # 統一エディターの更新  
        if self.unified_interval_editor:  
            self.unified_interval_editor.refresh_interval_list()  
      
    def synchronize_video_position(self, position: float):  
        """動画位置の同期"""  
        # タイムライン上のプレイヘッド更新  
        if self.timeline_display_manager:  
            self.timeline_display_manager.update_playhead_position(position)  
          
        # 表示管理との同期  
        if self.display_manager:  
            self.display_manager.synchronize_with_video_position(position)  
      
    def synchronize_video_duration(self, duration: float):  
        """動画長さの同期"""  
        if self.timeline_display_manager:  
            self.timeline_display_manager.set_video_duration(duration)  
      
    def handle_edit_events(self, event_type: str):  
        """編集イベントの処理"""  
        logger.info(f"Handling edit event: {event_type}")  
        self.synchronize_components()  
        self.dataChanged.emit()  
      
    def handle_video_events(self, event_type: str, data=None):  
        """動画イベントの処理"""  
        logger.info(f"Handling video event: {event_type}")  
          
        if event_type == "position_changed" and data is not None:  
            self.synchronize_video_position(data)  
        elif event_type == "duration_changed" and data is not None:  
            self.synchronize_video_duration(data)  
      
    def handle_timeline_events(self, event_type: str, data=None):  
        """タイムラインイベントの処理"""  
        logger.info(f"Handling timeline event: {event_type}")  
          
        if event_type == "interval_clicked" and data is not None:  
            # 区間クリック時の処理  
            if self.unified_interval_editor:  
                self.unified_interval_editor.set_selected_interval(data)  
              
            # 動画シーク  
            if self.video_player_controller and hasattr(data, 'start_time'):  
                self.video_player_controller.seek_to_time(data.start_time)  
      
    def _extract_video_id(self, video_path: str) -> str:  
        """動画パスからIDを抽出"""  
        import os  
        return os.path.splitext(os.path.basename(video_path))[0]  
      
    def on_data_updated(self):  
        """データ更新時の処理"""  
        self.synchronize_components()  
        self.dataChanged.emit()  
      
    def on_interval_changed(self, interval_id: str = ""):  
        """区間変更時の処理"""  
        self.synchronize_components()  
        self.dataChanged.emit()  
      
    def get_current_state(self) -> dict:  
        """現在の状態を取得（デバッグ用）"""  
        return {  
            'current_video_path': self.current_video_path,  
            'current_video_id': self.current_video_id,  
            'has_unified_data_controller': self.unified_data_controller is not None,  
            'has_timeline_manager': self.timeline_display_manager is not None,  
            'has_interval_editor': self.unified_interval_editor is not None,  
            'has_video_controller': self.video_player_controller is not None,  
            'has_display_manager': self.display_manager is not None  
        }