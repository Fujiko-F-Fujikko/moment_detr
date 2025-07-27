from dataclasses import dataclass, field  
from typing import List, Optional, Dict, Any, Tuple  
from datetime import datetime  
  
@dataclass  
class ActionData:  
    action_verb: str  
    manipulated_object: Optional[str] = None  
    target_object: Optional[str] = None  
    tool: Optional[str] = None  
  
@dataclass  
class ActionEntry:  
    action: ActionData  
    ids: List[int] = field(default_factory=list)  
    id: int = 0  
    segment: List[float] = field(default_factory=list)  
    segment_frames: List[int] = field(default_factory=list)  
  
@dataclass  
class StepEntry:  
    step: str  
    id: int  
    segment: List[float] = field(default_factory=list)  
    segment_frames: List[int] = field(default_factory=list)  
  
@dataclass  
class VideoData:  
    subset: str = "train"  # "train", "validation", "test"  
    duration: float = 0.0  
    fps: float = 0.0  
    actions: Dict[str, List[ActionEntry]] = field(default_factory=lambda: {  
        "left_hand": [],   
        "right_hand": [],   
        "both_hands": [],  # 新しく追加  
        "unspecified": []  # 新しく追加  
    })  
    steps: List[StepEntry] = field(default_factory=list)  

@dataclass  
class ActionCategory:  
    id: int  
    interaction: str  
  
@dataclass  
class StepCategory:  
    id: int  
    step: str  
  
@dataclass  
class STTDataset:  
    info: Dict[str, Any] = field(default_factory=lambda: {  
        "description": "STT Dataset 2025",  
        "version": 1.0,  
        "data_created": datetime.now().strftime("%Y/%m/%d")  
    })  
    database: Dict[str, VideoData] = field(default_factory=dict)  
    action_categories: List[ActionCategory] = field(default_factory=list)  
    step_categories: List[StepCategory] = field(default_factory=list)  