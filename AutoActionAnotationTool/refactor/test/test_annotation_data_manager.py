# test_annotation_data_manager.py

import sys
import os
import unittest
import logging
from datetime import datetime
from unittest.mock import MagicMock, patch

# テスト対象モジュールのインポートのためのパス設定
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from PyQt6.QtCore import QObject, pyqtSignal
from annotation_data_manager import AnnotationDataManager, AnnotationItem, VideoInfo


class TestAnnotationItem(unittest.TestCase):
    """AnnotationItemデータクラスのテスト"""
    
    def test_annotation_item_creation(self):
        """基本的なAnnotationItem作成テスト"""
        item = AnnotationItem(
            id="test_001",
            start_time=10.0,
            end_time=20.0,
            confidence_score=0.8,
            annotation_type="Action",
            category="manipulation"
        )
        
        assert item.id == "test_001"
        assert item.start_time == 10.0
        assert item.end_time == 20.0
        assert item.confidence_score == 0.8
        assert item.annotation_type == "Action"
        assert item.category == "manipulation"
        assert item.hand_type is None
        assert item.object_name is None
        assert item.verb is None
        assert item.video_id is None
        assert isinstance(item.created_at, datetime)
        assert isinstance(item.modified_at, datetime)
    
    def test_annotation_item_with_optional_fields(self):
        """オプションフィールド付きのAnnotationItem作成テスト"""
        item = AnnotationItem(
            id="test_002",
            start_time=5.0,
            end_time=15.0,
            confidence_score=0.9,
            annotation_type="Action",
            category="manipulation",
            hand_type="right",
            object_name="cup",
            verb="grab",
            video_id="video_001"
        )
        
        assert item.hand_type == "right"
        assert item.object_name == "cup"
        assert item.verb == "grab"
        assert item.video_id == "video_001"
    
    def test_annotation_item_validation(self):
        """AnnotationItemのバリデーションテスト"""
        # 正常なstart_time < end_timeの場合
        item = AnnotationItem(
            id="test_003",
            start_time=10.0,
            end_time=20.0,
            confidence_score=0.8,
            annotation_type="Action",
            category="manipulation"
        )
        # __post_init__で例外が発生しないことを確認
        assert item.start_time < item.end_time
        
        # start_time >= end_timeの場合は例外が発生することを確認
        try:
            AnnotationItem(
                id="test_004",
                start_time=20.0,
                end_time=10.0,
                confidence_score=0.8,
                annotation_type="Action",
                category="manipulation"
            )
            assert False, "ValueError should have been raised"
        except ValueError:
            pass  # 期待される例外


class TestVideoInfo(unittest.TestCase):
    """VideoInfoデータクラスのテスト"""
    
    def test_video_info_creation(self):
        """VideoInfo作成テスト"""
        video_info = VideoInfo(
            video_id="video_001",
            video_path="/path/to/video.mp4",
            duration=120.5,
            fps=30.0,
            width=1920,
            height=1080
        )
        
        assert video_info.video_id == "video_001"
        assert video_info.video_path == "/path/to/video.mp4"
        assert video_info.duration == 120.5
        assert video_info.fps == 30.0
        assert video_info.width == 1920
        assert video_info.height == 1080


class TestAnnotationDataManager(unittest.TestCase):
    """AnnotationDataManagerクラスのテスト"""
    
    def setUp(self):
        """各テストメソッドの前に実行される設定"""
        self.manager = AnnotationDataManager()
        
        # テスト用のサンプルVideoInfo
        self.sample_video_info = VideoInfo(
            video_id="test_video",
            video_path="/test/video.mp4",
            duration=60.0,
            fps=25.0,
            width=1280,
            height=720
        )
        
        # テスト用のサンプルAnnotationItem
        self.sample_annotation = AnnotationItem(
            id="test_annotation_001",
            start_time=10.0,
            end_time=20.0,
            confidence_score=0.8,
            annotation_type="Action",
            category="manipulation",
            hand_type="right",
            object_name="cup",
            verb="grab"
        )
    
    def test_initial_state(self):
        """初期状態のテスト"""
        assert self.manager.video_info is None
        assert len(self.manager.annotations) == 0
        assert self.manager.confidence_threshold == 0.0
        assert self.manager._next_id == 1
    
    def test_load_video(self):
        """動画読み込みテスト"""
        # シグナルの発信をモック
        with patch.object(self.manager, 'video_loaded') as mock_signal:
            self.manager.load_video("/test/video.mp4", self.sample_video_info)
            
            assert self.manager.video_info == self.sample_video_info
            mock_signal.emit.assert_called_once_with(self.sample_video_info)
    
    def test_add_annotation(self):
        """アノテーション追加テスト"""
        # 動画を読み込み
        self.manager.load_video("/test/video.mp4", self.sample_video_info)
        
        # シグナルの発信をモック
        with patch.object(self.manager, 'annotation_added') as mock_added, \
             patch.object(self.manager, 'data_changed') as mock_changed:
            
            annotation = self.manager.add_annotation(
                start_time=5.0,
                end_time=15.0,
                annotation_type="Action",
                category="manipulation",
                confidence_score=0.9,
                hand_type="left",
                object_name="bottle",
                verb="pick"
            )
            
            assert annotation is not None
            assert annotation.id == "Action_0001"
            assert annotation.start_time == 5.0
            assert annotation.end_time == 15.0
            assert annotation.annotation_type == "Action"
            assert annotation.category == "manipulation"
            assert annotation.confidence_score == 0.9
            assert annotation.hand_type == "left"
            assert annotation.object_name == "bottle"
            assert annotation.verb == "pick"
            assert annotation.video_id == "test_video"
            
            assert len(self.manager.annotations) == 1
            assert self.manager._next_id == 2
            
            mock_added.emit.assert_called_once_with(annotation)
            mock_changed.emit.assert_called_once()
    
    def test_add_annotation_without_video(self):
        """動画未読み込み時のアノテーション追加テスト"""
        # 動画をロードせずにアノテーションを追加
        annotation = self.manager.add_annotation(
            start_time=5.0,
            end_time=15.0,
            annotation_type="Action",
            category="manipulation",
            confidence_score=0.9
        )
        
        # アノテーションは追加されるが、video_idはNoneになる
        assert annotation is not None
        assert annotation.id == "Action_0001"
        assert annotation.video_id is None
        assert len(self.manager.annotations) == 1
    
    def test_modify_annotation(self):
        """アノテーション修正テスト"""
        # 動画読み込みとアノテーション追加
        self.manager.load_video("/test/video.mp4", self.sample_video_info)
        annotation = self.manager.add_annotation(
            start_time=5.0,
            end_time=15.0,
            annotation_type="Action",
            category="manipulation",
            confidence_score=0.9
        )
        
        # シグナルの発信をモック
        with patch.object(self.manager, 'annotation_modified') as mock_modified, \
             patch.object(self.manager, 'data_changed') as mock_changed:
            
            success = self.manager.modify_annotation(
                0,
                start_time=6.0,
                end_time=16.0,
                confidence_score=0.95,
                hand_type="right"
            )
            
            assert success is True
            
            # 修正後の新しいアノテーションを取得
            modified_annotation = self.manager.annotations[0]
            assert modified_annotation.start_time == 6.0
            assert modified_annotation.end_time == 16.0
            assert modified_annotation.confidence_score == 0.95
            assert modified_annotation.hand_type == "right"
            assert isinstance(modified_annotation.modified_at, datetime)
            
            # シグナルは old_annotation と new_annotation の両方を渡す
            mock_modified.emit.assert_called_once_with(annotation, modified_annotation)
            mock_changed.emit.assert_called_once()
    
    def test_modify_annotation_invalid_index(self):
        """無効なインデックスでのアノテーション修正テスト"""
        success = self.manager.modify_annotation(0, start_time=10.0)
        assert success is False
    
    def test_modify_annotation_invalid_time_range(self):
        """無効な時間範囲でのアノテーション修正テスト"""
        # 動画読み込みとアノテーション追加
        self.manager.load_video("/test/video.mp4", self.sample_video_info)
        self.manager.add_annotation(
            start_time=5.0,
            end_time=15.0,
            annotation_type="Action",
            category="manipulation",
            confidence_score=0.9
        )
        
        # start_time >= end_timeになる修正（現在の実装では受け入れられる）
        success = self.manager.modify_annotation(0, start_time=20.0, end_time=10.0)
        # 現在の実装では時間範囲の検証は行わないため、修正は成功する
        assert success is True
        
        # 修正後の値を確認
        modified_annotation = self.manager.annotations[0]
        assert modified_annotation.start_time == 20.0
        assert modified_annotation.end_time == 10.0
    
    def test_delete_annotation(self):
        """アノテーション削除テスト"""
        # 動画読み込みとアノテーション追加
        self.manager.load_video("/test/video.mp4", self.sample_video_info)
        annotation = self.manager.add_annotation(
            start_time=5.0,
            end_time=15.0,
            annotation_type="Action",
            category="manipulation",
            confidence_score=0.9
        )
        annotation_id = annotation.id
        
        # シグナルの発信をモック
        with patch.object(self.manager, 'annotation_deleted') as mock_deleted, \
             patch.object(self.manager, 'data_changed') as mock_changed:
            
            success = self.manager.delete_annotation(0)
            
            assert success is True
            assert len(self.manager.annotations) == 0
            
            mock_deleted.emit.assert_called_once_with(annotation)
            mock_changed.emit.assert_called_once()
    
    def test_delete_annotation_invalid_index(self):
        """無効なインデックスでのアノテーション削除テスト"""
        success = self.manager.delete_annotation(0)
        assert success is False
    
    def test_get_annotation_by_id(self):
        """IDによるアノテーション取得テスト"""
        # 動画読み込みとアノテーション追加
        self.manager.load_video("/test/video.mp4", self.sample_video_info)
        annotation = self.manager.add_annotation(
            start_time=5.0,
            end_time=15.0,
            annotation_type="Action",
            category="manipulation",
            confidence_score=0.9
        )
        
        # 正常なID
        found = self.manager.get_annotation_by_id(annotation.id)
        assert found == annotation
        
        # 存在しないID
        not_found = self.manager.get_annotation_by_id("nonexistent")
        assert not_found is None
    
    def test_get_annotations_by_type(self):
        """タイプによるアノテーション取得テスト"""
        # 動画読み込み
        self.manager.load_video("/test/video.mp4", self.sample_video_info)
        
        # 異なるタイプのアノテーションを追加
        action1 = self.manager.add_annotation(
            start_time=5.0,
            end_time=15.0,
            annotation_type="Action",
            category="manipulation",
            confidence_score=0.9
        )
        step1 = self.manager.add_annotation(
            start_time=20.0,
            end_time=30.0,
            annotation_type="Step",
            category="cooking",
            confidence_score=0.8
        )
        action2 = self.manager.add_annotation(
            start_time=35.0,
            end_time=45.0,
            annotation_type="Action",
            category="manipulation",
            confidence_score=0.7
        )
        
        # Actionタイプのアノテーション取得
        actions = self.manager.get_annotations_by_type("Action")
        assert len(actions) == 2
        assert action1 in actions
        assert action2 in actions
        assert step1 not in actions
        
        # Stepタイプのアノテーション取得
        steps = self.manager.get_annotations_by_type("Step")
        assert len(steps) == 1
        assert step1 in steps
        
        # 存在しないタイプ
        empty = self.manager.get_annotations_by_type("NonExistent")
        assert len(empty) == 0
    
    def test_get_filtered_annotations(self):
        """フィルタリングされたアノテーション取得テスト"""
        # 動画読み込み
        self.manager.load_video("/test/video.mp4", self.sample_video_info)
        
        # 異なる信頼度のアノテーションを追加
        high_conf = self.manager.add_annotation(
            start_time=5.0,
            end_time=15.0,
            annotation_type="Action",
            category="manipulation",
            confidence_score=0.9
        )
        med_conf = self.manager.add_annotation(
            start_time=20.0,
            end_time=30.0,
            annotation_type="Step",
            category="cooking",
            confidence_score=0.7
        )
        low_conf = self.manager.add_annotation(
            start_time=35.0,
            end_time=45.0,
            annotation_type="Action",
            category="manipulation",
            confidence_score=0.5
        )
        
        # 信頼度閾値を設定
        self.manager.set_confidence_threshold(0.6)
        
        # フィルタリング結果の確認
        filtered = self.manager.get_filtered_annotations()
        assert len(filtered) == 2
        assert high_conf in filtered
        assert med_conf in filtered
        assert low_conf not in filtered
    
    def test_set_confidence_threshold(self):
        """信頼度閾値設定テスト"""
        # シグナルの発信をモック
        with patch.object(self.manager, 'data_changed') as mock_changed:
            self.manager.set_confidence_threshold(0.8)
            
            assert self.manager.confidence_threshold == 0.8
            mock_changed.emit.assert_called_once()
    
    def test_get_statistics(self):
        """統計情報取得テスト"""
        # 動画読み込み
        self.manager.load_video("/test/video.mp4", self.sample_video_info)
        
        # 複数のアノテーションを追加
        self.manager.add_annotation(
            start_time=5.0,
            end_time=15.0,
            annotation_type="Action",
            category="manipulation",
            confidence_score=0.9
        )
        self.manager.add_annotation(
            start_time=20.0,
            end_time=30.0,
            annotation_type="Step",
            category="cooking",
            confidence_score=0.8
        )
        self.manager.add_annotation(
            start_time=35.0,
            end_time=45.0,
            annotation_type="Action",
            category="navigation",
            confidence_score=0.7
        )
        
        stats = self.manager.get_statistics()
        
        assert stats['total_annotations'] == 3
        assert stats['by_type']['Action'] == 2
        assert stats['by_type']['Step'] == 1
        assert stats['by_category']['manipulation'] == 1
        assert stats['by_category']['cooking'] == 1
        assert stats['by_category']['navigation'] == 1
        assert abs(stats['average_confidence'] - 0.8) < 0.01  # 0.8に近似
        assert stats['total_duration'] == 30.0  # (15-5) + (30-20) + (45-35)


if __name__ == "__main__":
    import unittest
    
    # ログ設定
    logging.basicConfig(level=logging.DEBUG)
    
    # unittestの実行
    unittest.main()
