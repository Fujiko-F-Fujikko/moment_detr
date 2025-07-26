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
        query_result = cls(      
            query_text=json_data['query'],      
            video_id=json_data['vid'],      
            relevant_windows=[],  # 後で設定  
            saliency_scores=json_data['pred_saliency_scores'],    
            query_id=index  
        )  
        
        # 区間を作成し、クエリ情報を埋め込む  
        intervals = []  
        for i, (start, end, score) in enumerate(json_data['pred_relevant_windows']):  
            interval = DetectionInterval(start, end, score, index)  
            interval.query_result = query_result  # クエリ情報を埋め込み  
            interval.interval_id = f"{query_result.query_id}_{i}"  # 新規追加：クエリ内でのインデックス  
            intervals.append(interval)
        query_result.relevant_windows = intervals  
        return query_result
  
@dataclass    
class InferenceResults:    
    results: List[QueryResults]    
    timestamp: datetime    
    model_info: dict  
    video_path: Optional[str] = None  
    total_queries: Optional[int] = None  
        
    def get_results_for_video(self, video_id: str) -> List[QueryResults]:    
        return [r for r in self.results if r.video_id == video_id]