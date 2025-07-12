# VideoPlayerController.py (新アーキテクチャ版)  
import os  
from PyQt6.QtWidgets import QPushButton, QSlider, QLabel, QHBoxLayout, QVBoxLayout, QMessageBox  
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QObject  
from PyQt6.QtMultimedia import QMediaPlayer  
from PyQt6.QtMultimediaWidgets import QVideoWidget  
  
class VideoPlayerController(QObject):  
    """動画プレイヤーの制御を担当するクラス（新アーキテクチャ版）"""  
      
    # シグナル定義  
    positionChanged = pyqtSignal(int)  # 再生位置が変更された  
    durationChanged = pyqtSignal(int)  # 動画の長さが変更された  
    playbackStateChanged = pyqtSignal(int)  # 再生状態が変更された  
      
    def __init__(self):  
        super().__init__()  
        self.current_video_path = None  
        self.setup_player()  
          
    def setup_player(self):  
        """プレイヤーとUIコンポーネントを初期化"""  
        # 動画プレイヤー  
        self.video_player = QMediaPlayer()  
        self.video_widget = QVideoWidget()  
        self.video_player.setVideoOutput(self.video_widget)  
          
        # コントロール要素  
        self.play_button = QPushButton("▶")  
        self.play_button.setMaximumWidth(50)  
        self.position_slider = QSlider(Qt.Orientation.Horizontal)  
        self.time_label = QLabel("00:00 / 00:00")  
          
        # シグナル接続  
        self.setup_connections()  
          
    def setup_connections(self):  
        """シグナル・スロット接続"""  
        self.play_button.clicked.connect(self.toggle_playback)  
        self.video_player.positionChanged.connect(self.update_position)  
        self.video_player.durationChanged.connect(self.update_duration)  
        self.video_player.playbackStateChanged.connect(self.on_playback_state_changed)  
        self.position_slider.sliderMoved.connect(self.set_position)  
          
    def get_video_widget(self):  
        """動画ウィジェットを取得"""  
        return self.video_widget  
          
    def get_controls_layout(self):  
        """コントロールレイアウトを取得"""  
        controls_layout = QHBoxLayout()  
        controls_layout.addWidget(self.play_button)  
        controls_layout.addWidget(self.position_slider)  
        controls_layout.addWidget(self.time_label)  
        return controls_layout  
          
    def load_video(self, video_path: str):  
        """動画ファイルを読み込む"""  
        if not os.path.exists(video_path):  
            raise FileNotFoundError(f"Video file not found: {video_path}")  
              
        try:  
            self.current_video_path = video_path  
            self.video_player.setSource(QUrl.fromLocalFile(video_path))  
            print(f"Loaded video: {video_path}")  
        except Exception as e:  
            raise Exception(f"Failed to load video: {str(e)}")  
              
    def toggle_playback(self):  
        """再生/一時停止の切り替え"""  
        if self.video_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:  
            self.video_player.pause()  
        else:  
            self.video_player.play()  
              
    def on_playback_state_changed(self, state):  
        """再生状態変更時の処理"""  
        if state == QMediaPlayer.PlaybackState.PlayingState:  
            self.play_button.setText("⏸")  
        else:  
            self.play_button.setText("▶")  
          
        # 外部に状態変更を通知  
        self.playbackStateChanged.emit(state)  
              
    def update_position(self, position: int):  
        """再生位置の更新"""  
        self.position_slider.setValue(position)  
        self.update_time_label(position, self.video_player.duration())  
        # 外部に位置変更を通知  
        self.positionChanged.emit(position)  
          
    def update_duration(self, duration: int):  
        """動画の長さが取得された時の処理"""  
        self.position_slider.setRange(0, duration)  
        self.update_time_label(self.video_player.position(), duration)  
        # 外部に長さ変更を通知  
        self.durationChanged.emit(duration)  
          
    def set_position(self, position: int):  
        """スライダーから再生位置を設定"""  
        self.video_player.setPosition(position)  
          
    def seek_to_time(self, time_seconds: float):  
        """指定した時間（秒）にシーク"""  
        position_ms = int(time_seconds * 1000)  
        self.video_player.setPosition(position_ms)  
          
    def get_duration_seconds(self):  
        """動画の長さを秒で取得"""  
        return self.video_player.duration() / 1000.0 if self.video_player.duration() > 0 else 0  
          
    def get_position_seconds(self):  
        """現在の再生位置を秒で取得"""  
        return self.video_player.position() / 1000.0  
          
    def update_time_label(self, position: int, duration: int):  
        """時間表示ラベルの更新"""  
        def format_time(ms):  
            seconds = ms // 1000  
            minutes = seconds // 60  
            seconds = seconds % 60  
            return f"{minutes:02d}:{seconds:02d}"  
              
        current_time = format_time(position)  
        total_time = format_time(duration)  
        self.time_label.setText(f"{current_time} / {total_time}")  
          
    def play(self):  
        """再生開始"""  
        self.video_player.play()  
          
    def pause(self):  
        """一時停止"""  
        self.video_player.pause()  
          
    def stop(self):  
        """停止"""  
        self.video_player.stop()  
          
    def is_playing(self) -> bool:  
        """再生中かどうかを判定"""  
        return self.video_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState  
          
    def get_current_video_path(self) -> str:  
        """現在の動画パスを取得"""  
        return self.current_video_path  
          
    def set_volume(self, volume: float):  
        """音量を設定（0.0-1.0）"""  
        audio_output = self.video_player.audioOutput()  
        if audio_output:  
            audio_output.setVolume(volume)  
              
    def get_volume(self) -> float:  
        """現在の音量を取得"""  
        audio_output = self.video_player.audioOutput()  
        if audio_output:  
            return audio_output.volume()  
        return 0.0  
          
    def get_playback_state(self):  
        """現在の再生状態を取得"""  
        return self.video_player.playbackState()  
          
    def clear_video(self):  
        """動画をクリア"""  
        self.video_player.stop()  
        self.video_player.setSource(QUrl())  
        self.current_video_path = None  
        self.position_slider.setValue(0)  
        self.time_label.setText("00:00 / 00:00")  
        self.play_button.setText("▶")