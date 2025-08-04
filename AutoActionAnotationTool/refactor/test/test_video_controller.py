# test_video_controller.py

import sys
import os
import logging
import unittest
from unittest.mock import MagicMock, patch

# テスト対象モジュールのインポートのためのパス設定
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from PyQt6.QtWidgets import QApplication, QWidget, QSlider, QPushButton
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import QTimer, QUrl
from annotation_data_manager import VideoInfo
from video_controller import VideoController


class TestVideoController(unittest.TestCase):
    """VideoControllerクラスのテスト"""
    
    def setUp(self):
        """各テストメソッドの前に実行される設定"""
        if not QApplication.instance():
            self.app = QApplication([])
        
        self.video_controller = VideoController()
        
        # テスト用のVideoInfo
        self.video_info = VideoInfo(
            video_id="test_video",
            video_path="/test/video.mp4",
            duration=60.0,
            fps=25.0,
            width=1280,
            height=720
        )
    
    def test_initial_state(self):
        """初期状態のテスト"""
        assert self.video_controller.current_video_path == ""
        assert self.video_controller.current_video_info is None
        assert isinstance(self.video_controller.media_player, QMediaPlayer)
        assert isinstance(self.video_controller.audio_output, QAudioOutput)
        assert isinstance(self.video_controller.video_widget, QVideoWidget)
        assert isinstance(self.video_controller.control_widget, QWidget)
        assert isinstance(self.video_controller.position_slider, QSlider)
        assert isinstance(self.video_controller.play_button, QPushButton)
        assert isinstance(self.video_controller.position_timer, QTimer)
    
    def test_load_video_success(self):
        """動画読み込み成功テスト"""
        with patch.object(self.video_controller, 'video_loaded') as mock_signal:
            success = self.video_controller.load_video("/test/video.mp4", self.video_info)
            
            assert success is True
            assert self.video_controller.current_video_path == "/test/video.mp4"
            assert self.video_controller.current_video_info == self.video_info
            
            # シグナルが発信されたことを確認
            mock_signal.emit.assert_called_once_with("/test/video.mp4")
    
    def test_load_video_without_info(self):
        """VideoInfo無しでの動画読み込みテスト"""
        with patch.object(self.video_controller, 'video_loaded') as mock_signal:
            success = self.video_controller.load_video("/test/video.mp4", None)
            
            assert success is True
            assert self.video_controller.current_video_path == "/test/video.mp4"
            assert self.video_controller.current_video_info is None
            
            # シグナルが発信されたことを確認
            mock_signal.emit.assert_called_once_with("/test/video.mp4")
    
    def test_media_player_setup(self):
        """MediaPlayerの設定テスト"""
        # MediaPlayerの基本設定が正しいことを確認
        assert self.video_controller.media_player.audioOutput() == self.video_controller.audio_output
        assert self.video_controller.media_player.videoOutput() == self.video_controller.video_widget
    
    def test_play_pause_stop(self):
        """再生・一時停止・停止テスト"""
        # 動画を読み込み
        self.video_controller.load_video("/test/video.mp4", self.video_info)
        
        # MediaPlayerのplayメソッドをモック
        with patch.object(self.video_controller.media_player, 'play') as mock_play:
            self.video_controller.play()
            mock_play.assert_called_once()
        
        # MediaPlayerのpauseメソッドをモック
        with patch.object(self.video_controller.media_player, 'pause') as mock_pause:
            self.video_controller.pause()
            mock_pause.assert_called_once()
        
        # MediaPlayerのstopメソッドをモック
        with patch.object(self.video_controller.media_player, 'stop') as mock_stop:
            self.video_controller.stop()
            mock_stop.assert_called_once()
    
    def test_toggle_playback(self):
        """再生切り替えテスト"""
        # 動画を読み込み
        self.video_controller.load_video("/test/video.mp4", self.video_info)
        
        # 停止状態から再生への切り替え
        with patch.object(self.video_controller.media_player, 'playbackState') as mock_state, \
             patch.object(self.video_controller.media_player, 'play') as mock_play:
            mock_state.return_value = QMediaPlayer.PlaybackState.StoppedState
            
            self.video_controller.toggle_playback()
            mock_play.assert_called_once()
        
        # 再生状態から一時停止への切り替え
        with patch.object(self.video_controller.media_player, 'playbackState') as mock_state, \
             patch.object(self.video_controller.media_player, 'pause') as mock_pause:
            mock_state.return_value = QMediaPlayer.PlaybackState.PlayingState
            
            self.video_controller.toggle_playback()
            mock_pause.assert_called_once()
    
    def test_seek_to_time(self):
        """時間指定シークテスト"""
        # 動画を読み込み
        self.video_controller.load_video("/test/video.mp4", self.video_info)
        
        with patch.object(self.video_controller.media_player, 'setPosition') as mock_set_position:
            # 正常な時間でのシーク
            self.video_controller.seek_to_time(30.0)
            mock_set_position.assert_called_with(30000)  # ミリ秒に変換
            
            # 0秒でのシーク
            self.video_controller.seek_to_time(0.0)
            mock_set_position.assert_called_with(0)
            
            # 動画時間を超える時間でのシーク（制限されるはず）
            self.video_controller.seek_to_time(100.0)
            mock_set_position.assert_called_with(60000)  # 動画時間の60秒に制限
    
    def test_seek_relative(self):
        """相対シークテスト"""
        # 動画を読み込み
        self.video_controller.load_video("/test/video.mp4", self.video_info)
        
        # 現在位置を30秒に設定
        with patch.object(self.video_controller.media_player, 'position', return_value=30000):
            with patch.object(self.video_controller.media_player, 'setPosition') as mock_set_position:
                # 5秒進む
                self.video_controller.seek_relative(5.0)
                mock_set_position.assert_called_with(35000)
                
                # 10秒戻る
                self.video_controller.seek_relative(-10.0)
                mock_set_position.assert_called_with(20000)
    
    def test_get_position_seconds(self):
        """現在位置取得テスト"""
        with patch.object(self.video_controller.media_player, 'position', return_value=25000):
            position = self.video_controller.get_position_seconds()
            assert position == 25.0
    
    def test_get_duration_seconds(self):
        """動画時間取得テスト"""
        # VideoInfo有りの場合
        self.video_controller.load_video("/test/video.mp4", self.video_info)
        duration = self.video_controller.get_duration_seconds()
        assert duration == 60.0
        
        # VideoInfo無しの場合
        self.video_controller.current_video_info = None
        with patch.object(self.video_controller.media_player, 'duration', return_value=45000):
            duration = self.video_controller.get_duration_seconds()
            assert duration == 45.0
    
    def test_widget_access(self):
        """ウィジェット取得テスト"""
        video_widget = self.video_controller.get_video_widget()
        control_widget = self.video_controller.get_control_widget()
        
        assert isinstance(video_widget, QVideoWidget)
        assert isinstance(control_widget, QWidget)
        assert video_widget == self.video_controller.video_widget
        assert control_widget == self.video_controller.control_widget
    
    def test_position_slider_update(self):
        """位置スライダー更新テスト"""
        # 動画を読み込み
        self.video_controller.load_video("/test/video.mp4", self.video_info)
        
        # 位置変更をシミュレート
        with patch.object(self.video_controller, 'position_changed') as mock_signal:
            # _on_position_changedメソッドを直接呼び出し
            self.video_controller._on_position_changed(30000)  # 30秒
            
            # スライダーの値が更新されたことを確認
            assert self.video_controller.position_slider.value() == 30
            
            # シグナルが発信されたことを確認
            mock_signal.emit.assert_called_once_with(30.0)
    
    def test_duration_changed_handling(self):
        """動画時間変更ハンドリングテスト"""
        with patch.object(self.video_controller, 'duration_changed') as mock_signal:
            # _on_duration_changedメソッドを直接呼び出し
            self.video_controller._on_duration_changed(120000)  # 120秒
            
            # スライダーの最大値が更新されたことを確認
            assert self.video_controller.position_slider.maximum() == 120
            
            # シグナルが発信されたことを確認
            mock_signal.emit.assert_called_once_with(120.0)
    
    def test_playback_state_changed_handling(self):
        """再生状態変更ハンドリングテスト"""
        with patch.object(self.video_controller, 'playback_state_changed') as mock_signal:
            # 再生状態変更をシミュレート
            state = QMediaPlayer.PlaybackState.PlayingState
            self.video_controller._on_playback_state_changed(state)
            
            # ボタンテキストが更新されたことを確認
            assert self.video_controller.play_button.text() == "⏸"
            
            # シグナルが発信されたことを確認
            mock_signal.emit.assert_called_once_with(state)
        
        # 停止状態のテスト
        with patch.object(self.video_controller, 'playback_state_changed') as mock_signal:
            state = QMediaPlayer.PlaybackState.StoppedState
            self.video_controller._on_playback_state_changed(state)
            
            assert self.video_controller.play_button.text() == "▶"
            mock_signal.emit.assert_called_once_with(state)
    
    def test_position_timer(self):
        """位置タイマーテスト"""
        # タイマーが設定されていることを確認
        assert self.video_controller.position_timer.interval() == 100
        
        # タイマーが接続されていることを確認（モックでテスト）
        with patch.object(self.video_controller, '_update_position') as mock_update:
            # タイマーのタイムアウトシグナルを手動で発火
            self.video_controller.position_timer.timeout.emit()
            # 実際にはタイマーが動作していないので、この方法では検証困難
            # 代わりに_update_positionメソッドを直接テスト
    
    def test_update_position(self):
        """位置更新テスト"""
        # 動画を読み込み
        self.video_controller.load_video("/test/video.mp4", self.video_info)
        
        with patch.object(self.video_controller.media_player, 'position', return_value=15000):
            # _update_positionメソッドを直接呼び出し
            self.video_controller._update_position()
            
            # スライダーの値が更新されたことを確認
            assert self.video_controller.position_slider.value() == 15
    
    def test_slider_seek(self):
        """スライダーシークテスト"""
        # 動画を読み込み
        self.video_controller.load_video("/test/video.mp4", self.video_info)
        
        with patch.object(self.video_controller.media_player, 'setPosition') as mock_set_position:
            # スライダー値変更をシミュレート
            self.video_controller._on_slider_seek(45)  # 45秒
            
            mock_set_position.assert_called_with(45000)
    
    def test_play_button_click(self):
        """再生ボタンクリックテスト"""
        # 動画を読み込み
        self.video_controller.load_video("/test/video.mp4", self.video_info)
        
        with patch.object(self.video_controller, 'toggle_playback') as mock_toggle:
            # ボタンクリックをシミュレート
            self.video_controller._on_play_button_clicked()
            
            mock_toggle.assert_called_once()


if __name__ == "__main__":
    import unittest
    
    # ログ設定
    logging.basicConfig(level=logging.DEBUG)
    
    # unittestの実行
    unittest.main()
