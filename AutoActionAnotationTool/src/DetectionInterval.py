from dataclasses import dataclass  
from typing import Optional  
  
@dataclass  
class DetectionInterval:  
    start_time: float  # seconds  
    end_time: float   # seconds  
    confidence_score: float  
    query_id: Optional[int] = None  
    label: Optional[str] = None  
      
    @property  
    def duration(self) -> float:  
        return self.end_time - self.start_time  
      
    def overlaps_with(self, other: 'DetectionInterval') -> bool:  
        return not (self.end_time <= other.start_time or other.end_time <= self.start_time)