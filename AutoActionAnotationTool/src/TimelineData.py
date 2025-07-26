# TimelineData.py (データ構造)  
from dataclasses import dataclass  
from typing import List, Optional  

from DetectionInterval import DetectionInterval
  
@dataclass  
class NewIntervalPreview:  
    start_time: float  
    end_time: float  
  
@dataclass  
class TimelineData:  
    """タイムライン描画に必要なデータを格納"""  
    video_duration: float = 0.0  
    current_position: float = 0.0  
    confidence_threshold: float = 0.0  
    intervals: List[DetectionInterval] = None  
    saliency_scores: List[float] = None  
    highlighted_interval: Optional[DetectionInterval] = None  
    time_scale_enabled: bool = False  
    clip_duration: float = 2.0  
      
    # ドラッグ関連  
    is_dragging: bool = False  
    dragging_interval: Optional[DetectionInterval] = None  
    drag_mode: Optional[str] = None  # 'move', 'resize_start', 'resize_end'  
      
    # 新規区間作成関連  
    is_creating_new_interval: bool = False  
    new_interval_preview: Optional[NewIntervalPreview] = None  
      
    def __post_init__(self):  
        if self.intervals is None:  
            self.intervals = []  
        if self.saliency_scores is None:  
            self.saliency_scores = []