# DataStructures.py  
from dataclasses import dataclass  
  
@dataclass  
class VideoMetadata:  
    """動画メタデータ"""  
    video_id: str  
    subset: str  
    duration: float  
    fps: float  
    file_path: str  
      
    def __post_init__(self):  
        """初期化後の検証"""  
        if self.duration <= 0:  
            raise ValueError("Duration must be positive")  
        if self.fps <= 0:  
            raise ValueError("FPS must be positive")  
  
@dataclass   
class CategoryInfo:  
    """カテゴリ情報"""  
    id: int  
    content_text: str  
    category_type: str  # "action" or "step"  
      
    def __post_init__(self):  
        """初期化後の検証"""  
        if self.category_type not in ["action", "step"]:  
            raise ValueError("Category type must be 'action' or 'step'")  
        if not self.content_text.strip():  
            raise ValueError("Content text cannot be empty")