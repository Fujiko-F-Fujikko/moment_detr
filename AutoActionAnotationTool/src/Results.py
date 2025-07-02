from dataclasses import dataclass  
from typing import List  
from datetime import datetime
from DetectionInterval import DetectionInterval

@dataclass  
class QueryResults:  
    query_id: int  
    query_text: str  
    video_id: str  
    relevant_windows: List[DetectionInterval]  
    saliency_scores: List[float]  # Per 2-second clip  
      
    @classmethod  
    def from_moment_detr_json(cls, json_data: dict) -> 'QueryResults':  
        intervals = [  
            DetectionInterval(start, end, score, json_data.get('qid'))  
            for start, end, score in json_data['pred_relevant_windows']  
        ]  
          
        return cls(  
            query_id=json_data['qid'],  
            query_text=json_data['query'],  
            video_id=json_data['vid'],  
            relevant_windows=intervals,  
            saliency_scores=json_data['pred_saliency_scores']  
        )  
  
@dataclass  
class InferenceResults:  
    results: List[QueryResults]  
    timestamp: datetime  
    model_info: dict  
      
    def get_results_for_video(self, video_id: str) -> List[QueryResults]:  
        return [r for r in self.results if r.video_id == video_id]