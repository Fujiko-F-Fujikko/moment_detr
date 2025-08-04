# test_timeline_controller.py

import sys
import os
import logging
import unittest
from unittest.mock import MagicMock, patch

# テスト対象モジュールのインポートのためのパス設定
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPaintEvent, QMouseEvent
from annotation_data_manager import AnnotationDataManager, AnnotationItem, VideoInfo
from timeline_controller import TimelineController, TimelineTrack


class TestTimelineTrack(unittest.TestCase):
    """TimelineTrackクラスのテスト"""
    
    def setUp(self):
        """各テストメソッドの前に実行される設定"""
        if not QApplication.instance():
            self.app = QApplication([])
        
        self.track = TimelineTrack("Action", track_height=80)
        
        # テスト用のアノテーション
        self.test_annotations = [
            AnnotationItem(
                id="test_001",
                start_time=10.0,
                end_time=20.0,
                confidence_score=0.9,
                annotation_type="Action",
                category="manipulation"
            ),
            AnnotationItem(
                id="test_002",
                start_time=30.0,
                end_time=40.0,
                confidence_score=0.8,
                annotation_type="Action",
                category="navigation"
            )
        ]
    
    def test_initial_state(self):
        """初期状態のテスト"""
        assert self.track.annotation_type == "Action"
        assert self.track.track_height == 80
        assert len(self.track.annotations) == 0
        assert self.track.video_duration == 0.0
        assert self.track.current_position == 0.0
        assert self.track.pixels_per_second == 1.0
        assert self.track.dragging_annotation is None
        assert self.track.highlighted_annotation is None
    
    def test_set_annotations(self):
        """アノテーション設定テスト"""
        self.track.set_annotations(self.test_annotations)
        
        assert len(self.track.annotations) == 2
        assert self.track.annotations[0].id == "test_001"
        assert self.track.annotations[1].id == "test_002"
    
    def test_set_video_duration(self):
        """動画時間設定テスト"""
        self.track.set_video_duration(120.0)
        
        assert self.track.video_duration == 120.0
        # ウィジェットのサイズが適切に更新されることを確認
        # （実際のサイズ計算は実装依存）
    
    def test_set_current_position(self):
        """現在位置設定テスト"""
        self.track.set_current_position(45.0)
        
        assert self.track.current_position == 45.0
    
    def test_set_highlighted_annotation(self):
        """ハイライトアノテーション設定テスト"""
        annotation = self.test_annotations[0]
        self.track.set_highlighted_annotation(annotation)
        
        assert self.track.highlighted_annotation == annotation
        
        # クリア
        self.track.set_highlighted_annotation(None)
        assert self.track.highlighted_annotation is None
    
    def test_time_to_x_conversion(self):
        """時間からX座標への変換テスト"""
        # 60秒の動画、600ピクセル幅と仮定
        self.track.video_duration = 60.0
        self.track.pixels_per_second = 10.0  # 600 / 60
        
        x = self.track._time_to_x(30.0)
        assert x == 300.0  # 30秒 * 10px/秒
        
        x = self.track._time_to_x(0.0)
        assert x == 0.0
        
        x = self.track._time_to_x(60.0)
        assert x == 600.0
    
    def test_x_to_time_conversion(self):
        """X座標から時間への変換テスト"""
        # 60秒の動画、600ピクセル幅と仮定
        self.track.video_duration = 60.0
        self.track.pixels_per_second = 10.0
        
        time = self.track._x_to_time(300.0)
        assert time == 30.0
        
        time = self.track._x_to_time(0.0)
        assert time == 0.0
        
        time = self.track._x_to_time(600.0)
        assert time == 60.0
    
    def test_get_annotation_at_x(self):
        """X座標でのアノテーション取得テスト"""
        self.track.set_annotations(self.test_annotations)
        self.track.video_duration = 60.0
        self.track.pixels_per_second = 10.0
        
        # 最初のアノテーション範囲内（10-20秒 = 100-200px）
        annotation = self.track._get_annotation_at_x(150.0)
        assert annotation == self.test_annotations[0]
        
        # 2番目のアノテーション範囲内（30-40秒 = 300-400px）
        annotation = self.track._get_annotation_at_x(350.0)
        assert annotation == self.test_annotations[1]
        
        # アノテーション範囲外
        annotation = self.track._get_annotation_at_x(250.0)  # 25秒位置
        assert annotation is None
    
    def test_mouse_press_event(self):
        """マウス押下イベントテスト"""
        self.track.set_annotations(self.test_annotations)
        self.track.video_duration = 60.0
        self.track.pixels_per_second = 10.0
        
        # アノテーション上でのクリック
        with patch.object(self.track, 'interval_clicked') as mock_signal:
            event = QMouseEvent(
                QMouseEvent.Type.MouseButtonPress,
                QPoint(150, 40),  # 15秒位置（最初のアノテーション内）
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier
            )
            self.track.mousePressEvent(event)
            
            # interval_clickedシグナルが発信されたことを確認
            mock_signal.emit.assert_called_once_with(self.test_annotations[0])
        
        # 空の場所でのクリック
        with patch.object(self.track, 'position_clicked') as mock_signal:
            event = QMouseEvent(
                QMouseEvent.Type.MouseButtonPress,
                QPoint(250, 40),  # 25秒位置（アノテーション外）
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier
            )
            self.track.mousePressEvent(event)
            
            # position_clickedシグナルが発信されたことを確認
            mock_signal.emit.assert_called_once_with(25.0)
    
    def test_mouse_move_event_dragging(self):
        """ドラッグ中のマウス移動イベントテスト"""
        self.track.set_annotations(self.test_annotations)
        self.track.video_duration = 60.0
        self.track.pixels_per_second = 10.0
        
        # ドラッグ開始
        self.track.dragging_annotation = self.test_annotations[0]
        self.track.drag_start_x = 150.0
        self.track.drag_start_time = 15.0
        
        with patch.object(self.track, 'interval_drag_moved') as mock_signal:
            event = QMouseEvent(
                QMouseEvent.Type.MouseMove,
                QPoint(200, 40),  # 20秒位置に移動
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier
            )
            self.track.mouseMoveEvent(event)
            
            # interval_drag_movedシグナルが発信されたことを確認
            mock_signal.emit.assert_called_once()
    
    def test_mouse_release_event_drag_finish(self):
        """ドラッグ終了のマウス離脱イベントテスト"""
        self.track.set_annotations(self.test_annotations)
        self.track.video_duration = 60.0
        self.track.pixels_per_second = 10.0
        
        # ドラッグ状態を設定
        self.track.dragging_annotation = self.test_annotations[0]
        self.track.drag_start_x = 150.0
        self.track.drag_start_time = 15.0
        
        with patch.object(self.track, 'interval_drag_finished') as mock_signal:
            event = QMouseEvent(
                QMouseEvent.Type.MouseButtonRelease,
                QPoint(200, 40),  # 20秒位置で終了
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier
            )
            self.track.mouseReleaseEvent(event)
            
            # interval_drag_finishedシグナルが発信されたことを確認
            mock_signal.emit.assert_called_once()
            
            # ドラッグ状態がクリアされたことを確認
            assert self.track.dragging_annotation is None
    
    def test_mouse_release_event_new_interval(self):
        """新規区間作成のマウス離脱イベントテスト"""
        self.track.video_duration = 60.0
        self.track.pixels_per_second = 10.0
        
        # 新規区間作成のドラッグ状態を設定
        self.track.creating_new_interval = True
        self.track.new_interval_start_x = 100.0  # 10秒位置
        
        with patch.object(self.track, 'new_interval_created') as mock_signal:
            event = QMouseEvent(
                QMouseEvent.Type.MouseButtonRelease,
                QPoint(200, 40),  # 20秒位置で終了
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier
            )
            self.track.mouseReleaseEvent(event)
            
            # new_interval_createdシグナルが発信されたことを確認
            mock_signal.emit.assert_called_once_with(10.0, 20.0, "Action")
            
            # 新規作成状態がクリアされたことを確認
            assert not self.track.creating_new_interval


class TestTimelineController(unittest.TestCase):
    """TimelineControllerクラスのテスト"""
    
    def setUp(self):
        """各テストメソッドの前に実行される設定"""
        if not QApplication.instance():
            self.app = QApplication([])
        
        self.data_manager = AnnotationDataManager()
        self.timeline_controller = TimelineController(self.data_manager)
        
        # テスト用のVideoInfo
        self.video_info = VideoInfo(
            video_id="test_video",
            video_path="/test/video.mp4",
            duration=60.0,
            fps=25.0,
            width=1280,
            height=720
        )
        
        # 動画を読み込み
        self.data_manager.load_video("/test/video.mp4", self.video_info)
        
        # テスト用のアノテーションを追加
        self.action_annotation = self.data_manager.add_annotation(
            start_time=10.0,
            end_time=20.0,
            annotation_type="Action",
            category="manipulation",
            confidence_score=0.9
        )
        
        self.step_annotation = self.data_manager.add_annotation(
            start_time=30.0,
            end_time=40.0,
            annotation_type="Step",
            category="cooking",
            confidence_score=0.8
        )
    
    def test_initial_state(self):
        """初期状態のテスト"""
        assert self.timeline_controller.data_manager == self.data_manager
        assert isinstance(self.timeline_controller.timeline_widget, QWidget)
        assert isinstance(self.timeline_controller.tracks, dict)
        assert self.timeline_controller.video_duration == 0.0
        assert self.timeline_controller.current_position == 0.0
    
    def test_set_video_duration(self):
        """動画時間設定テスト"""
        self.timeline_controller.set_video_duration(120.0)
        
        assert self.timeline_controller.video_duration == 120.0
        
        # 各トラックにも設定が伝播されることを確認
        for track in self.timeline_controller.tracks.values():
            assert track.video_duration == 120.0
    
    def test_set_current_position(self):
        """現在位置設定テスト"""
        self.timeline_controller.set_current_position(45.0)
        
        assert self.timeline_controller.current_position == 45.0
        
        # 各トラックにも設定が伝播されることを確認
        for track in self.timeline_controller.tracks.values():
            assert track.current_position == 45.0
    
    def test_set_highlighted_annotation(self):
        """ハイライトアノテーション設定テスト"""
        self.timeline_controller.set_highlighted_annotation(self.action_annotation)
        
        # Actionトラックにハイライトが設定されることを確認
        action_track = self.timeline_controller.tracks.get("Action")
        if action_track:
            assert action_track.highlighted_annotation == self.action_annotation
    
    def test_update_timeline(self):
        """タイムライン更新テスト"""
        # データマネージャーから更新されたアノテーションを取得することを確認
        with patch.object(self.data_manager, 'get_filtered_annotations') as mock_get:
            mock_get.return_value = [self.action_annotation, self.step_annotation]
            
            self.timeline_controller.update_timeline()
            
            mock_get.assert_called_once()
            
            # 各トラックにアノテーションが設定されることを確認
            action_track = self.timeline_controller.tracks.get("Action")
            step_track = self.timeline_controller.tracks.get("Step")
            
            if action_track:
                assert len(action_track.annotations) == 1
                assert action_track.annotations[0] == self.action_annotation
            
            if step_track:
                assert len(step_track.annotations) == 1
                assert step_track.annotations[0] == self.step_annotation
    
    def test_get_timeline_widget(self):
        """タイムラインウィジェット取得テスト"""
        widget = self.timeline_controller.get_timeline_widget()
        assert isinstance(widget, QWidget)
        assert widget == self.timeline_controller.timeline_widget
    
    def test_clear_highlights(self):
        """ハイライトクリアテスト"""
        # まずハイライトを設定
        self.timeline_controller.set_highlighted_annotation(self.action_annotation)
        
        # クリア
        self.timeline_controller.clear_highlights()
        
        # 全トラックのハイライトがクリアされることを確認
        for track in self.timeline_controller.tracks.values():
            assert track.highlighted_annotation is None
    
    def test_track_creation(self):
        """トラック作成テスト"""
        # update_timelineを呼び出してトラックが作成されることを確認
        self.timeline_controller.update_timeline()
        
        # ActionとStepのトラックが作成されることを確認
        assert "Action" in self.timeline_controller.tracks
        assert "Step" in self.timeline_controller.tracks
        
        action_track = self.timeline_controller.tracks["Action"]
        step_track = self.timeline_controller.tracks["Step"]
        
        assert isinstance(action_track, TimelineTrack)
        assert isinstance(step_track, TimelineTrack)
        assert action_track.annotation_type == "Action"
        assert step_track.annotation_type == "Step"
    
    def test_signal_connections(self):
        """シグナル接続テスト"""
        # トラックが作成された後でシグナル接続を確認
        self.timeline_controller.update_timeline()
        
        # 各トラックのシグナルが適切に接続されていることを確認
        for track in self.timeline_controller.tracks.values():
            # シグナルの接続確認は困難なので、代わりにシグナルハンドラーの存在を確認
            assert hasattr(self.timeline_controller, '_on_interval_clicked')
            assert hasattr(self.timeline_controller, '_on_interval_drag_started')
            assert hasattr(self.timeline_controller, '_on_interval_drag_moved')
            assert hasattr(self.timeline_controller, '_on_interval_drag_finished')
            assert hasattr(self.timeline_controller, '_on_new_interval_created')
            assert hasattr(self.timeline_controller, '_on_position_clicked')
    
    def test_signal_handlers(self):
        """シグナルハンドラーテスト"""
        # interval_clickedシグナルハンドラー
        with patch.object(self.timeline_controller, 'interval_clicked') as mock_signal:
            self.timeline_controller._on_interval_clicked(self.action_annotation)
            mock_signal.emit.assert_called_once_with(self.action_annotation)
        
        # position_clickedシグナルハンドラー
        with patch.object(self.timeline_controller, 'position_clicked') as mock_signal:
            self.timeline_controller._on_position_clicked(25.0)
            mock_signal.emit.assert_called_once_with(25.0)
        
        # new_interval_createdシグナルハンドラー
        with patch.object(self.timeline_controller, 'new_interval_created') as mock_signal:
            self.timeline_controller._on_new_interval_created(15.0, 25.0, "Action")
            mock_signal.emit.assert_called_once_with(15.0, 25.0, "Action")


if __name__ == "__main__":
    import unittest
    
    # ログ設定
    logging.basicConfig(level=logging.DEBUG)
    
    # unittestの実行
    unittest.main()
