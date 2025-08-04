# video_controller.py
"""
ビデオコントロールクラス
動画の再生、シーク、制御を管理
"""

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QUrl
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import Qt
import logging
from typing import Optional

from annotation_data_manager import VideoInfo


class VideoController(QObject):
    """ビデオコントロールクラス"""
    
    video_loaded = pyqtSignal(object)     # VideoInfo
    position_changed = pyqtSignal(float)  # seconds
    duration_changed = pyqtSignal(float)  # seconds
    playback_state_changed = pyqtSignal(bool)  # is_playing
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.current_video_path: str = ""
        self.current_video_info: Optional[VideoInfo] = None
        
        # メディアプレイヤー設定
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        # ビデオウィジェット
        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)
        
        # コントロールパネル
        self.control_widget = None
        self.position_slider = None
        self.play_button = None
        self.position_label = None
        self.duration_label = None
        
        # タイマー（位置更新用）
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self._update_position)
        self.position_timer.start(100)  # 100ms間隔
        
        self._setup_video_player()
        self._create_control_panel()
        
        self.logger.info("VideoController initialized")
    
    def _setup_video_player(self):
        """ビデオプレイヤーセットアップ"""
        # シグナル接続
        self.media_player.positionChanged.connect(self._on_position_changed)
        self.media_player.durationChanged.connect(self._on_duration_changed)
        self.media_player.playbackStateChanged.connect(self._on_playback_state_changed)
        
        # 初期設定
        self.media_player.setPlaybackRate(1.0)
        self.audio_output.setVolume(0.5)
    
    def _create_control_panel(self):
        """コントロールパネル作成"""
        self.control_widget = QWidget()
        layout = QVBoxLayout(self.control_widget)
        
        # 位置スライダー
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setMinimum(0)
        self.position_slider.setMaximum(1000)
        self.position_slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self.position_slider)
        
        # コントロールボタン
        control_layout = QHBoxLayout()
        
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.toggle_playback)
        control_layout.addWidget(self.play_button)
        
        # 位置表示
        self.position_label = QLabel("00:00")
        control_layout.addWidget(self.position_label)
        
        control_layout.addWidget(QLabel("/"))
        
        self.duration_label = QLabel("00:00")
        control_layout.addWidget(self.duration_label)
        
        control_layout.addStretch()
        
        # シーク制御ボタン
        seek_back_button = QPushButton("-10s")
        seek_back_button.clicked.connect(lambda: self.seek_relative(-10.0))
        control_layout.addWidget(seek_back_button)
        
        seek_forward_button = QPushButton("+10s")
        seek_forward_button.clicked.connect(lambda: self.seek_relative(10.0))
        control_layout.addWidget(seek_forward_button)
        
        layout.addLayout(control_layout)
    
    def load_video(self, video_path: str, video_info: Optional[VideoInfo] = None) -> bool:
        """動画読み込み"""
        self.logger.info(f"Loading video: {video_path}")
        try:
            self.current_video_path = video_path
            self.current_video_info = video_info
            
            # メディアプレイヤーに動画を設定
            media_url = QUrl.fromLocalFile(video_path)
            self.media_player.setSource(media_url)
            
            self.logger.info(f"Video loaded successfully: {video_path}")
            if video_info:
                self.video_loaded.emit(video_info)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load video: {e}")
            return False
    
    def play(self):
        """再生"""
        self.logger.debug("Starting playback")
        self.media_player.play()
    
    def pause(self):
        """一時停止"""
        self.logger.debug("Pausing playback")
        self.media_player.pause()
    
    def stop(self):
        """停止"""
        self.logger.debug("Stopping playback")
        self.media_player.stop()
    
    def toggle_playback(self):
        """再生/一時停止切り替え"""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.pause()
        else:
            self.play()
    
    def seek_to_time(self, seconds: float):
        """指定時間にシーク"""
        self.logger.debug(f"Seeking to: {seconds} seconds")
        position_ms = int(seconds * 1000)
        self.media_player.setPosition(position_ms)
    
    def seek_relative(self, seconds: float):
        """相対シーク"""
        current_position = self.get_position_seconds()
        new_position = max(0, current_position + seconds)
        
        duration = self.get_duration_seconds()
        if duration > 0:
            new_position = min(new_position, duration)
        
        self.seek_to_time(new_position)
    
    def get_position_seconds(self) -> float:
        """現在位置取得（秒）"""
        return self.media_player.position() / 1000.0
    
    def get_duration_seconds(self) -> float:
        """動画長さ取得（秒）"""
        return self.media_player.duration() / 1000.0
    
    def is_playing(self) -> bool:
        """再生中かどうか"""
        return self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
    
    def set_playback_rate(self, rate: float):
        """再生レート設定"""
        self.logger.debug(f"Setting playback rate: {rate}")
        self.media_player.setPlaybackRate(rate)
    
    def set_volume(self, volume: float):
        """音量設定（0.0-1.0）"""
        self.logger.debug(f"Setting volume: {volume}")
        self.audio_output.setVolume(volume)
    
    def get_video_widget(self) -> QVideoWidget:
        """ビデオウィジェット取得"""
        return self.video_widget
    
    def get_control_widget(self) -> QWidget:
        """コントロールウィジェット取得"""
        return self.control_widget
    
    def _on_position_changed(self, position_ms: int):
        """位置変更時の処理"""
        seconds = position_ms / 1000.0
        self.position_changed.emit(seconds)
        
        # スライダー更新
        if self.position_slider and not self.position_slider.isSliderDown():
            duration = self.media_player.duration()
            if duration > 0:
                slider_value = int((position_ms / duration) * 1000)
                self.position_slider.setValue(slider_value)
        
        # 位置ラベル更新
        if self.position_label:
            self.position_label.setText(self._format_time(seconds))
    
    def _on_duration_changed(self, duration_ms: int):
        """動画長さ変更時の処理"""
        seconds = duration_ms / 1000.0
        self.duration_changed.emit(seconds)
        
        # 長さラベル更新
        if self.duration_label:
            self.duration_label.setText(self._format_time(seconds))
    
    def _on_playback_state_changed(self, state):
        """再生状態変更時の処理"""
        is_playing = state == QMediaPlayer.PlaybackState.PlayingState
        self.playback_state_changed.emit(is_playing)
        
        # ボタンテキスト更新
        if self.play_button:
            self.play_button.setText("Pause" if is_playing else "Play")
    
    def _on_slider_changed(self, value: int):
        """スライダー変更時の処理"""
        if self.position_slider.isSliderDown():
            duration = self.media_player.duration()
            if duration > 0:
                position = int((value / 1000) * duration)
                self.media_player.setPosition(position)
    
    def _update_position(self):
        """位置更新（タイマー用）"""
        # 必要に応じて追加の更新処理
        pass
    
    def _format_time(self, seconds: float) -> str:
        """時間フォーマット"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_current_video_info(self) -> Optional[VideoInfo]:
        """現在の動画情報取得"""
        return self.current_video_info
