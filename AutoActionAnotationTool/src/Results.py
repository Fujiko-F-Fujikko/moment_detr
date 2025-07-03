from dataclasses import dataclass  
from typing import List, Optional
from datetime import datetime
from DetectionInterval import DetectionInterval

@dataclass    
class QueryResults:    
    query_text: str    
    video_id: str    
    relevant_windows: List[DetectionInterval]    
    saliency_scores: List[float]    
    query_id: Optional[int] = None  # qidがない場合に対応  
        
    @classmethod    
    def from_moment_detr_json(cls, json_data: dict, index: int = 0) -> 'QueryResults':    
        intervals = [    
            DetectionInterval(start, end, score, index)    
            for start, end, score in json_data['pred_relevant_windows']    
        ]    
            
        return cls(    
            query_text=json_data['query'],    
            video_id=json_data['vid'],    
            relevant_windows=intervals,    
            saliency_scores=json_data['pred_saliency_scores'],  
            query_id=index  # インデックスをquery_idとして使用  
        )
  
@dataclass    
class InferenceResults:    
    results: List[QueryResults]    
    timestamp: datetime    
    model_info: dict  
    video_path: Optional[str] = None  
    total_queries: Optional[int] = None  
        
    def get_results_for_video(self, video_id: str) -> List[QueryResults]:    
        return [r for r in self.results if r.video_id == video_id]