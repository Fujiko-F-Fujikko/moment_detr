# VideoDataController.py  
import cv2  
from pathlib import Path  
from typing import Optional  
from PyQt6.QtCore import QObject, pyqtSignal  
  
from VideoInfo import VideoInfo  
  
class VideoDataController(QObject):  
    """動画データの管理を担当するクラス"""  
      
    # シグナル定義  
    videoLoaded = pyqtSignal(VideoInfo)  
    videoInfoChanged = pyqtSignal(VideoInfo)  
      
    def __init__(self):  
        super().__init__()  
        self.current_video_info: Optional[VideoInfo] = None  
        self.current_video_path: Optional[str] = None  
      
    def load_video_metadata(self, video_path: str) -> VideoInfo:  
        """動画ファイルからメタデータを抽出"""  
        if not Path(video_path).exists():  
            raise FileNotFoundError(f"Video file not found: {video_path}")  
          
        try:  
            # OpenCVを使用してメタデータを取得  
            cap = cv2.VideoCapture(video_path)  
              
            if not cap.isOpened():  
                raise ValueError(f"Cannot open video file: {video_path}")  
              
            fps = cap.get(cv2.CAP_PROP_FPS)  
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)  
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))  
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))  
            duration = frame_count / fps if fps > 0 else 0  
              
            cap.release()  
              
            video_id = Path(video_path).stem  
            video_info = VideoInfo(video_id, video_path, duration, fps, width, height)  
              
            # 内部状態を更新  
            self.current_video_info = video_info  
            self.current_video_path = video_path  
              
            # シグナル発信  
            self.videoLoaded.emit(video_info)  
              
            return video_info  
              
        except Exception as e:  
            raise Exception(f"Failed to extract video metadata: {str(e)}")  
      
    def get_current_video_info(self) -> Optional[VideoInfo]:  
        """現在の動画情報を取得"""  
        return self.current_video_info  
      
    def get_current_video_path(self) -> Optional[str]:  
        """現在の動画パスを取得"""  
        return self.current_video_path  
      
    def get_video_name(self) -> Optional[str]:  
        """現在の動画名を取得"""  
        if self.current_video_path:  
            return Path(self.current_video_path).stem  
        return None  
      
    def is_video_loaded(self) -> bool:  
        """動画が読み込まれているかチェック"""  
        return self.current_video_info is not None  
      
    def clear_video_data(self):  
        """動画データをクリア"""  
        self.current_video_info = None  
        self.current_video_path = None