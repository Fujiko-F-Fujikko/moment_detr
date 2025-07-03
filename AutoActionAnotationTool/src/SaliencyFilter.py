from typing import List, Tuple  
import numpy as np  

from DetectionInterval import DetectionInterval
from Results import QueryResults

class SaliencyFilter:  
    def __init__(self, threshold: float = 0.5):  
        self.threshold = threshold  
      
    def filter_by_saliency(self, query_results: QueryResults) -> List[Tuple[int, float]]:  
        """Return (clip_index, score) pairs above threshold"""  
        return [  
            (idx, score)   
            for idx, score in enumerate(query_results.saliency_scores)  
            if score >= self.threshold  
        ]  
      
    def get_salient_intervals(self, query_results: QueryResults,   
                            clip_duration: float = 2.0) -> List[DetectionInterval]:  
        """Convert salient clips to intervals"""  
        salient_clips = self.filter_by_saliency(query_results)  
        intervals = []  
          
        for clip_idx, score in salient_clips:  
            start_time = clip_idx * clip_duration  
            end_time = start_time + clip_duration  
            intervals.append(DetectionInterval(start_time, end_time, score))  
          
        return intervals  
      
    def apply_temporal_smoothing(self, saliency_scores: List[float],   
                                window_size: int = 3) -> List[float]:  
        """Apply moving average smoothing"""  
        if len(saliency_scores) < window_size:  
            return saliency_scores  
          
        smoothed = []  
        half_window = window_size // 2  
          
        for i in range(len(saliency_scores)):  
            start_idx = max(0, i - half_window)  
            end_idx = min(len(saliency_scores), i + half_window + 1)  
            window_scores = saliency_scores[start_idx:end_idx]  
            smoothed.append(sum(window_scores) / len(window_scores))  
          
        return smoothed