# test_annotation_command_manager.py

import sys
import os
import unittest
import logging
from unittest.mock import MagicMock, patch

# テスト対象モジュールのインポートのためのパス設定
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QUndoStack
from PyQt6.QtCore import QObject
from annotation_data_manager import AnnotationDataManager, AnnotationItem, VideoInfo
from annotation_command_manager import (
    AnnotationCommandManager, AnnotationCommand, 
    AddAnnotationCommand, ModifyAnnotationCommand, DeleteAnnotationCommand
)


class TestAnnotationCommand(unittest.TestCase):
    """AnnotationCommandベースクラスのテスト"""
    
    def setUp(self):
        """各テストメソッドの前に実行される設定"""
        # QApplicationが必要
        if not QApplication.instance():
            self.app = QApplication([])
        
        self.data_manager = AnnotationDataManager()
        
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
    
    def test_command_base_class(self):
        """AnnotationCommandベースクラスのテスト"""
        # 具象クラスでテスト
        command = AddAnnotationCommand(
            self.data_manager,
            annotation_type="Action",
            start_time=10.0,
            end_time=20.0,
            category="manipulation",
            confidence_score=0.8
        )
        
        assert command.data_manager == self.data_manager
        assert command.text() == "Add Action annotation"


class TestAddAnnotationCommand(unittest.TestCase):
    """AddAnnotationCommandクラスのテスト"""
    
    def setUp(self):
        """各テストメソッドの前に実行される設定"""
        if not QApplication.instance():
            self.app = QApplication([])
        
        self.data_manager = AnnotationDataManager()
        
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
    
    def test_add_command_redo(self):
        """AddAnnotationCommandのredo()テスト"""
        command = AddAnnotationCommand(
            self.data_manager,
            annotation_type="Action",
            start_time=10.0,
            end_time=20.0,
            category="manipulation",
            confidence_score=0.8,
            hand_type="right",
            object_name="cup",
            verb="grab"
        )
        
        # 初期状態の確認
        assert len(self.data_manager.annotations) == 0
        
        # redoの実行
        command.redo()
        
        # アノテーションが追加されたことを確認
        assert len(self.data_manager.annotations) == 1
        assert command.annotation is not None
        assert command.index == 0
        
        annotation = command.annotation
        assert annotation.annotation_type == "Action"
        assert annotation.start_time == 10.0
        assert annotation.end_time == 20.0
        assert annotation.category == "manipulation"
        assert annotation.confidence_score == 0.8
        assert annotation.hand_type == "right"
        assert annotation.object_name == "cup"
        assert annotation.verb == "grab"
    
    def test_add_command_undo(self):
        """AddAnnotationCommandのundo()テスト"""
        command = AddAnnotationCommand(
            self.data_manager,
            annotation_type="Action",
            start_time=10.0,
            end_time=20.0,
            category="manipulation",
            confidence_score=0.8
        )
        
        # redoしてからundo
        command.redo()
        assert len(self.data_manager.annotations) == 1
        
        command.undo()
        
        # アノテーションが削除されたことを確認
        assert len(self.data_manager.annotations) == 0


class TestModifyAnnotationCommand(unittest.TestCase):
    """ModifyAnnotationCommandクラスのテスト"""
    
    def setUp(self):
        """各テストメソッドの前に実行される設定"""
        if not QApplication.instance():
            self.app = QApplication([])
        
        self.data_manager = AnnotationDataManager()
        
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
        self.annotation = self.data_manager.add_annotation(
            start_time=10.0,
            end_time=20.0,
            annotation_type="Action",
            category="manipulation",
            confidence_score=0.8,
            hand_type="right"
        )
    
    def test_modify_command_redo(self):
        """ModifyAnnotationCommandのredo()テスト"""
        # 元の値を記録
        original_start = self.annotation.start_time
        original_end = self.annotation.end_time
        original_conf = self.annotation.confidence_score
        original_hand = self.annotation.hand_type
        
        old_values = {
            "start_time": original_start,
            "end_time": original_end,
            "confidence_score": original_conf,
            "hand_type": original_hand
        }
        new_values = {
            "start_time": 12.0,
            "end_time": 22.0,
            "confidence_score": 0.9,
            "hand_type": "left"
        }
        
        command = ModifyAnnotationCommand(
            self.data_manager,
            self.annotation.id,
            old_values,
            new_values
        )
        
        # redoの実行
        command.redo()
        
        # 変更されたアノテーション（新しいオブジェクト）を取得
        modified_annotation = self.data_manager.annotations[0]
        
        # 値が変更されたことを確認
        assert modified_annotation.start_time == 12.0
        assert modified_annotation.end_time == 22.0
        assert modified_annotation.confidence_score == 0.9
        assert modified_annotation.hand_type == "left"
        
        # 古い値が保存されていることを確認
        assert command.old_values['start_time'] == original_start
        assert command.old_values['end_time'] == original_end
        assert command.old_values['confidence_score'] == original_conf
        assert command.old_values['hand_type'] == original_hand
    
    def test_modify_command_undo(self):
        """ModifyAnnotationCommandのundo()テスト"""
        # 元の値を記録
        original_start = self.annotation.start_time
        original_end = self.annotation.end_time
        original_conf = self.annotation.confidence_score
        
        old_values = {
            "start_time": original_start,
            "end_time": original_end,
            "confidence_score": original_conf
        }
        new_values = {
            "start_time": 12.0,
            "end_time": 22.0,
            "confidence_score": 0.9
        }
        
        command = ModifyAnnotationCommand(
            self.data_manager,
            self.annotation.id,
            old_values,
            new_values
        )
        
        # redoしてからundo
        command.redo()
        command.undo()
        
        # 元の値に戻ったことを確認（undo後の新しいオブジェクト）
        restored_annotation = self.data_manager.annotations[0]
        assert restored_annotation.start_time == original_start
        assert restored_annotation.end_time == original_end
        assert restored_annotation.confidence_score == original_conf


class TestDeleteAnnotationCommand(unittest.TestCase):
    """DeleteAnnotationCommandクラスのテスト"""
    
    def setUp(self):
        """各テストメソッドの前に実行される設定"""
        if not QApplication.instance():
            self.app = QApplication([])
        
        self.data_manager = AnnotationDataManager()
        
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
        self.annotation = self.data_manager.add_annotation(
            start_time=10.0,
            end_time=20.0,
            annotation_type="Action",
            category="manipulation",
            confidence_score=0.8
        )
    
    def test_delete_command_redo(self):
        """DeleteAnnotationCommandのredo()テスト"""
        command = DeleteAnnotationCommand(
            self.data_manager,
            self.annotation.id
        )
        
        # 初期状態の確認
        assert len(self.data_manager.annotations) == 1
        
        # redoの実行
        command.redo()
        
        # アノテーションが削除されたことを確認
        assert len(self.data_manager.annotations) == 0
        assert command.annotation is not None  # 削除されたアノテーションが保存されている
        assert command.index == 0  # インデックスが保存されている
    
    def test_delete_command_undo(self):
        """DeleteAnnotationCommandのundo()テスト"""
        command = DeleteAnnotationCommand(
            self.data_manager,
            self.annotation.id
        )
        
        # redoしてからundo
        command.redo()
        assert len(self.data_manager.annotations) == 0
        
        command.undo()
        
        # アノテーションが復元されたことを確認
        assert len(self.data_manager.annotations) == 1
        restored_annotation = self.data_manager.annotations[0]
        assert restored_annotation.id == self.annotation.id


class TestAnnotationCommandManager(unittest.TestCase):
    """AnnotationCommandManagerクラスのテスト"""
    
    def setUp(self):
        """各テストメソッドの前に実行される設定"""
        if not QApplication.instance():
            self.app = QApplication([])
        
        self.data_manager = AnnotationDataManager()
        self.command_manager = AnnotationCommandManager(self.data_manager)
        
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
    
    def test_initial_state(self):
        """初期状態のテスト"""
        assert self.command_manager.data_manager == self.data_manager
        assert isinstance(self.command_manager.undo_stack, QUndoStack)
        assert not self.command_manager.undo_stack.canUndo()
        assert not self.command_manager.undo_stack.canRedo()
    
    def test_execute_add_annotation(self):
        """アノテーション追加コマンドの実行テスト"""
        with patch.object(self.command_manager, 'command_executed') as mock_signal:
            annotation = self.command_manager.execute_add_annotation(
                annotation_type="Action",
                start_time=10.0,
                end_time=20.0,
                category="manipulation",
                confidence_score=0.8
            )
            
            # アノテーションが追加されたことを確認
            assert annotation is not None
            assert len(self.data_manager.annotations) == 1
            assert annotation == self.data_manager.annotations[0]
            
            # Undoが可能になったことを確認
            assert self.command_manager.undo_stack.canUndo()
            
            # シグナルが発信されたことを確認
            mock_signal.emit.assert_called_once()
    
    def test_execute_modify_annotation(self):
        """アノテーション修正コマンドの実行テスト"""
        # まずアノテーションを追加
        annotation = self.command_manager.execute_add_annotation(
            annotation_type="Action",
            start_time=10.0,
            end_time=20.0,
            category="manipulation",
            confidence_score=0.8
        )
        
        with patch.object(self.command_manager, 'command_executed') as mock_signal:
            # 修正前の値
            old_values = {
                'start_time': annotation.start_time,
                'confidence_score': annotation.confidence_score
            }
            # 修正後の値
            new_values = {
                'start_time': 12.0,
                'confidence_score': 0.9
            }
            
            self.command_manager.execute_modify_annotation(
                annotation_id=annotation.id,
                old_values=old_values,
                new_values=new_values
            )
            
            # シグナルが発信されたことを確認
            mock_signal.emit.assert_called_once()
    
    def test_execute_delete_annotation(self):
        """アノテーション削除コマンドの実行テスト"""
        # まずアノテーションを追加
        annotation = self.command_manager.execute_add_annotation(
            annotation_type="Action",
            start_time=10.0,
            end_time=20.0,
            category="manipulation",
            confidence_score=0.8
        )
        annotation_id = annotation.id
        
        with patch.object(self.command_manager, 'command_executed') as mock_signal:
            success = self.command_manager.execute_delete_annotation(annotation_id)
            
            # 削除が成功したことを確認
            assert success is True
            assert len(self.data_manager.annotations) == 0
            
            # シグナルが発信されたことを確認
            mock_signal.emit.assert_called_once()
    
    def test_undo_redo(self):
        """Undo/Redoテスト"""
        # アノテーションを追加
        annotation = self.command_manager.execute_add_annotation(
            annotation_type="Action",
            start_time=10.0,
            end_time=20.0,
            category="manipulation",
            confidence_score=0.8
        )
        
        # Undo
        self.command_manager.undo()
        assert len(self.data_manager.annotations) == 0
        assert self.command_manager.undo_stack.canRedo()
        
        # Redo
        self.command_manager.redo()
        assert len(self.data_manager.annotations) == 1
        assert self.command_manager.undo_stack.canUndo()
    
    def test_clear(self):
        """履歴クリアテスト"""
        # いくつかのコマンドを実行
        self.command_manager.execute_add_annotation(
            annotation_type="Action",
            start_time=10.0,
            end_time=20.0,
            category="manipulation",
            confidence_score=0.8
        )
        
        assert self.command_manager.undo_stack.canUndo()
        
        # 履歴をクリア
        self.command_manager.clear()
        
        assert not self.command_manager.undo_stack.canUndo()
        assert not self.command_manager.undo_stack.canRedo()
    
    def test_get_undo_stack(self):
        """UndoStackの取得テスト"""
        stack = self.command_manager.get_undo_stack()
        assert isinstance(stack, QUndoStack)
        assert stack == self.command_manager.undo_stack


if __name__ == "__main__":
    import unittest
    
    # ログ設定
    logging.basicConfig(level=logging.DEBUG)
    
    # unittestの実行
    unittest.main()
