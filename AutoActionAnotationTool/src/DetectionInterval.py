from dataclasses import dataclass  
from typing import Optional  
  
@dataclass  
class DetectionInterval:  
    start_time: float  # seconds  
    end_time: float   # seconds  
    confidence_score: float  
    query_id: Optional[int] = None  
    label: Optional[str] = None
    query_result: Optional[object] = None
    interval_id: Optional[str] = None
      
    def __eq__(self, other):  
        if not isinstance(other, DetectionInterval):  
            return False  
        return (self.start_time == other.start_time and   
                self.end_time == other.end_time and  
                self.confidence_score == other.confidence_score)  
      
    def __hash__(self):  
        return hash((self.start_time, self.end_time, self.confidence_score))

    def __post_init__(self):  
        # 一意IDを自動生成（時間とconfidenceから）  
        if self.interval_id is None:  
            self.interval_id = f"{self.start_time:.3f}_{self.end_time:.3f}_{self.confidence_score:.6f}"
    @property  
    def duration(self) -> float:  
        return self.end_time - self.start_time  
      
    def overlaps_with(self, other: 'DetectionInterval') -> bool:  
        return not (self.end_time <= other.start_time or other.end_time <= self.start_time)