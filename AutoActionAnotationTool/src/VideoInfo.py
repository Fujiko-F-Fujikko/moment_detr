from dataclasses import dataclass

@dataclass  
class VideoInfo:  
    video_id: str  
    file_path: str  
    duration: float  # seconds  
    fps: float  
    width: int  
    height: int  
    clip_duration: float = 2.0  # moment_detr uses 2-second clips  
      
    @property  
    def total_clips(self) -> int:  
        return int(self.duration / self.clip_duration)