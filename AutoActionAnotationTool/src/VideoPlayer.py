from PyQt6.QtMultimedia import QMediaPlayer, QMediaContent, QUrl  
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel, QVideoWidget
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

from DetectionInterval import DetectionInterval

class VideoPlayer(QWidget):  
    positionChanged = pyqtSignal(int)  # milliseconds  
    durationChanged = pyqtSignal(int)  # milliseconds  
    intervalSelected = pyqtSignal(DetectionInterval)  
      
    def __init__(self):  
        super().__init__()  
        self.media_player = QMediaPlayer()  
        self.video_widget = QVideoWidget()  
        self.media_player.setVideoOutput(self.video_widget)  
          
        self.setup_ui()  
        self.setup_connections()  
          
    def setup_ui(self):  
        layout = QVBoxLayout()  
          
        # Video display  
        layout.addWidget(self.video_widget)  
          
        # Controls  
        controls_layout = QHBoxLayout()  
          
        self.play_button = QPushButton("Play")  
        self.position_slider = QSlider(Qt.Horizontal)  
        self.time_label = QLabel("00:00 / 00:00")  
          
        controls_layout.addWidget(self.play_button)  
        controls_layout.addWidget(self.position_slider)  
        controls_layout.addWidget(self.time_label)  
          
        layout.addLayout(controls_layout)  
        self.setLayout(layout)  
      
    def setup_connections(self):  
        self.play_button.clicked.connect(self.toggle_playback)  
        self.media_player.positionChanged.connect(self.update_position)  
        self.media_player.durationChanged.connect(self.update_duration)  
        self.position_slider.sliderMoved.connect(self.set_position)  
      
    def load_video(self, video_path: str):  
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(video_path)))  
      
    def play_interval(self, interval: DetectionInterval):  
        """Play specific interval"""  
        start_ms = int(interval.start_time * 1000)  
        end_ms = int(interval.end_time * 1000)  
          
        self.media_player.setPosition(start_ms)  
        self.media_player.play()  
          
        # Set up timer to stop at end  
        QTimer.singleShot(int(interval.duration * 1000), self.media_player.pause)