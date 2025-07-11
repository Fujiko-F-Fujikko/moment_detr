from pathlib import Path
from typing import List
import cv2

from PyQt6.QtCore import QObject, pyqtSignal

from VideoInfo import VideoInfo
from DetectionInterval import DetectionInterval
from Results import QueryResults
from DataHandling import InferenceResultsLoader, InferenceResultsSaver

class ApplicationController(QObject):  
    def __init__(self):  
        super().__init__()  
        self.video_info = None  
        self.inference_results = None  
        self.current_query_results = None  
          
        # Components  
        self.loader = InferenceResultsLoader()  
        self.saver = InferenceResultsSaver()  
          
    def load_video(self, video_path: str) -> VideoInfo:  
        """Load video and extract metadata"""  
        # Use OpenCV or similar to get video info  
        cap = cv2.VideoCapture(video_path)  
          
        fps = cap.get(cv2.CAP_PROP_FPS)  
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)  
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))  
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))  
        duration = frame_count / fps  
          
        cap.release()  
          
        video_id = Path(video_path).stem  
        self.video_info = VideoInfo(video_id, video_path, duration, fps, width, height)  
        return self.video_info  
      
    def load_inference_results(self, results_path: str):  
        """Load moment_detr inference results"""  
        if results_path.endswith('.jsonl'):  
            self.inference_results = self.loader.load_from_jsonl(results_path)  
        else:  
            self.inference_results = self.loader.load_from_json(results_path)  
      
    def get_results_for_current_video(self) -> List[QueryResults]:  
        """Get inference results for currently loaded video"""  
        if not self.video_info or not self.inference_results:  
            return []  
          
        return self.inference_results.get_results_for_video(self.video_info.video_id)  
        
class IntervalModificationController(QObject):  
    intervalChanged = pyqtSignal(DetectionInterval, DetectionInterval)  
      
    def __init__(self, app_controller: ApplicationController):  
        super().__init__()  
        self.app_controller = app_controller  
      
    def modify_interval(self, old_interval: DetectionInterval,   
                       new_start: float, new_end: float, new_label: str = None):  
        """Modify an existing interval"""  
        new_interval = DetectionInterval(  
            new_start, new_end, old_interval.confidence_score,  
            old_interval.query_id, new_label  
        )  
          
        # Update in current results  
        if self.app_controller.current_query_results:  
            intervals = self.app_controller.current_query_results.relevant_windows  
            if old_interval in intervals:  
                index = intervals.index(old_interval)  
                intervals[index] = new_interval  
                self.intervalChanged.emit(old_interval, new_interval)  
  
class FilterController(QObject):  
    filtersChanged = pyqtSignal()  
      
    def __init__(self, app_controller: ApplicationController):  
        super().__init__()  
        self.app_controller = app_controller  
        self.confidence_threshold = 0.1  
      
    def set_confidence_threshold(self, threshold: float):  
        self.confidence_threshold = threshold  
        self.filtersChanged.emit()  