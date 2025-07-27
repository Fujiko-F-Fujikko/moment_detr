# UnifiedInterval.py  
import uuid  
from typing import Optional, Dict, Any  
from dataclasses import dataclass  
from STTDataStructures import ActionData, ActionEntry, StepEntry  
  
@dataclass  
class UnifiedInterval:  
    """統一された時間区間データクラス"""  
      
    def __init__(self, interval_id: str = None, start_time: float = 0.0,   
                 end_time: float = 0.0, confidence_score: float = 0.0,  
                 interval_type: str = "action", content_text: str = "",  
                 action_data: Optional[ActionData] = None, video_id: str = "",  
                 category_id: int = 0):  
        self.interval_id = interval_id or str(uuid.uuid4())  
        self.start_time = start_time  
        self.end_time = end_time  
        self.confidence_score = confidence_score  
        self.interval_type = interval_type  # "action" or "step"  
        self.content_text = content_text  
        self.action_data = action_data  
        self.video_id = video_id  
        self.category_id = category_id  
      
    @classmethod  
    def create_action_interval(cls, query_text: str, start: float, end: float,   
                             confidence: float) -> 'UnifiedInterval':  
        """アクション区間を作成"""  
        print(f"Creating action interval: {query_text}, {start}-{end}, conf={confidence}")  
        return cls(  
            start_time=start,  
            end_time=end,  
            confidence_score=confidence,  
            interval_type="action",  
            content_text=query_text  
        )  
      
    @classmethod  
    def create_step_interval(cls, step_text: str, start: float, end: float) -> 'UnifiedInterval':  
        """ステップ区間を作成"""  
        print(f"Creating step interval: {step_text}, {start}-{end}")  
        return cls(  
            start_time=start,  
            end_time=end,  
            confidence_score=1.0,  # ステップは手動作成なので信頼度最大  
            interval_type="step",  
            content_text=step_text  
        )  
      
    def is_action_type(self) -> bool:  
        """アクション区間かどうか"""  
        return self.interval_type == "action"  
      
    def is_step_type(self) -> bool:  
        """ステップ区間かどうか"""  
        return self.interval_type == "step"  
      
    def get_display_text(self) -> str:  
        """表示用テキストを取得"""  
        if self.is_step_type():  
            return f"Step: {self.content_text}"  
        return self.content_text  
      
    def to_stt_action_entry(self, fps: float) -> ActionEntry:  
        """STT形式のActionEntryに変換"""  
        if not self.is_action_type():  
            raise ValueError("Cannot convert step interval to ActionEntry")  
          
        return ActionEntry(  
            id=self.category_id,  
            query=self.content_text,  
            relevant_windows=[[  
                int(self.start_time * fps),  
                int(self.end_time * fps)  
            ]]  
        )  
      
    def to_stt_step_entry(self, fps: float) -> StepEntry:  
        """STT形式のStepEntryに変換"""  
        if not self.is_step_type():  
            raise ValueError("Cannot convert action interval to StepEntry")  
          
        return StepEntry(  
            id=self.category_id,  
            step=self.content_text,  
            relevant_windows=[[  
                int(self.start_time * fps),  
                int(self.end_time * fps)  
            ]]  
        )  
      
    def overlaps_with(self, other: 'UnifiedInterval') -> bool:  
        """他の区間と重複するかチェック"""  
        return not (self.end_time <= other.start_time or other.end_time <= self.start_time)  
      
    def duration(self) -> float:  
        """区間の長さを取得"""  
        return self.end_time - self.start_time