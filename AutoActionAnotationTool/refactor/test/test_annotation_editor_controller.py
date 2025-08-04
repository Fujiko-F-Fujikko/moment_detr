# test_annotation_editor_controller.py

import sys
import os
import logging
import unittest
from unittest.mock import MagicMock, patch

# テスト対象モジュールのインポートのためのパス設定
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from PyQt6.QtWidgets import QApplication, QTabWidget, QWidget, QDoubleSpinBox, QLineEdit, QComboBox, QTextEdit
from annotation_data_manager import AnnotationDataManager, AnnotationItem, VideoInfo
from annotation_command_manager import AnnotationCommandManager
from annotation_editor_controller import AnnotationEditorController, ActionEditor, StepEditor


class TestActionEditor(unittest.TestCase):
    """ActionEditorクラスのテスト"""
    
    def setUp(self):
        """各テストメソッドの前に実行される設定"""
        if not QApplication.instance():
            self.app = QApplication([])
        
        self.action_editor = ActionEditor()
        
        # テスト用のActionアノテーション
        self.action_annotation = AnnotationItem(
            id="test_action_001",
            start_time=10.0,
            end_time=20.0,
            confidence_score=0.9,
            annotation_type="Action",
            category="manipulation",
            hand_type="right",
            object_name="cup",
            verb="grab"
        )
    
    def test_initial_state(self):
        """初期状態のテスト"""
        assert self.action_editor.current_annotation is None
        assert isinstance(self.action_editor.start_time_spin, QDoubleSpinBox)
        assert isinstance(self.action_editor.end_time_spin, QDoubleSpinBox)
        assert isinstance(self.action_editor.confidence_spin, QDoubleSpinBox)
        assert isinstance(self.action_editor.category_edit, QLineEdit)
        assert isinstance(self.action_editor.hand_type_combo, QComboBox)
        assert isinstance(self.action_editor.object_edit, QLineEdit)
        assert isinstance(self.action_editor.verb_edit, QLineEdit)
    
    def test_set_annotation(self):
        """アノテーション設定テスト"""
        self.action_editor.set_annotation(self.action_annotation)
        
        assert self.action_editor.current_annotation == self.action_annotation
        
        # フィールドが正しく設定されることを確認
        assert self.action_editor.start_time_spin.value() == 10.0
        assert self.action_editor.end_time_spin.value() == 20.0
        assert self.action_editor.confidence_spin.value() == 0.9
        assert self.action_editor.category_edit.text() == "manipulation"
        assert self.action_editor.hand_type_combo.currentText() == "right"
        assert self.action_editor.object_edit.text() == "cup"
        assert self.action_editor.verb_edit.text() == "grab"
    
    def test_get_current_values(self):
        """現在値取得テスト"""
        self.action_editor.set_annotation(self.action_annotation)
        
        # 値を変更
        self.action_editor.start_time_spin.setValue(12.0)
        self.action_editor.end_time_spin.setValue(22.0)
        self.action_editor.confidence_spin.setValue(0.95)
        self.action_editor.category_edit.setText("navigation")
        self.action_editor.hand_type_combo.setCurrentText("left")
        self.action_editor.object_edit.setText("bottle")
        self.action_editor.verb_edit.setText("pick")
        
        values = self.action_editor.get_current_values()
        
        assert values['start_time'] == 12.0
        assert values['end_time'] == 22.0
        assert values['confidence_score'] == 0.95
        assert values['category'] == "navigation"
        assert values['hand_type'] == "left"
        assert values['object_name'] == "bottle"
        assert values['verb'] == "pick"
    
    def test_clear(self):
        """クリアテスト"""
        # まずアノテーションを設定
        self.action_editor.set_annotation(self.action_annotation)
        
        # クリア
        self.action_editor.clear()
        
        assert self.action_editor.current_annotation is None
        
        # フィールドがクリアされることを確認
        assert self.action_editor.start_time_spin.value() == 0.0
        assert self.action_editor.end_time_spin.value() == 0.0
        assert self.action_editor.confidence_spin.value() == 0.0
        assert self.action_editor.category_edit.text() == ""
        assert self.action_editor.hand_type_combo.currentIndex() == 0  # "none"
        assert self.action_editor.object_edit.text() == ""
        assert self.action_editor.verb_edit.text() == ""
    
    def test_set_enabled(self):
        """有効/無効設定テスト"""
        # 無効にする
        self.action_editor.set_enabled(False)
        
        assert not self.action_editor.start_time_spin.isEnabled()
        assert not self.action_editor.end_time_spin.isEnabled()
        assert not self.action_editor.confidence_spin.isEnabled()
        assert not self.action_editor.category_edit.isEnabled()
        assert not self.action_editor.hand_type_combo.isEnabled()
        assert not self.action_editor.object_edit.isEnabled()
        assert not self.action_editor.verb_edit.isEnabled()
        
        # 有効にする
        self.action_editor.set_enabled(True)
        
        assert self.action_editor.start_time_spin.isEnabled()
        assert self.action_editor.end_time_spin.isEnabled()
        assert self.action_editor.confidence_spin.isEnabled()
        assert self.action_editor.category_edit.isEnabled()
        assert self.action_editor.hand_type_combo.isEnabled()
        assert self.action_editor.object_edit.isEnabled()
        assert self.action_editor.verb_edit.isEnabled()


class TestStepEditor(unittest.TestCase):
    """StepEditorクラスのテスト"""
    
    def setUp(self):
        """各テストメソッドの前に実行される設定"""
        if not QApplication.instance():
            self.app = QApplication([])
        
        self.step_editor = StepEditor()
        
        # テスト用のStepアノテーション
        self.step_annotation = AnnotationItem(
            id="test_step_001",
            start_time=30.0,
            end_time=45.0,
            confidence_score=0.8,
            annotation_type="Step",
            category="cooking step: chop vegetables"
        )
    
    def test_initial_state(self):
        """初期状態のテスト"""
        assert self.step_editor.current_annotation is None
        assert isinstance(self.step_editor.start_time_spin, QDoubleSpinBox)
        assert isinstance(self.step_editor.end_time_spin, QDoubleSpinBox)
        assert isinstance(self.step_editor.confidence_spin, QDoubleSpinBox)
        assert isinstance(self.step_editor.step_text_edit, QTextEdit)
    
    def test_set_annotation(self):
        """アノテーション設定テスト"""
        self.step_editor.set_annotation(self.step_annotation)
        
        assert self.step_editor.current_annotation == self.step_annotation
        
        # フィールドが正しく設定されることを確認
        assert self.step_editor.start_time_spin.value() == 30.0
        assert self.step_editor.end_time_spin.value() == 45.0
        assert self.step_editor.confidence_spin.value() == 0.8
        assert self.step_editor.step_text_edit.toPlainText() == "cooking step: chop vegetables"
    
    def test_get_current_values(self):
        """現在値取得テスト"""
        self.step_editor.set_annotation(self.step_annotation)
        
        # 値を変更
        self.step_editor.start_time_spin.setValue(32.0)
        self.step_editor.end_time_spin.setValue(47.0)
        self.step_editor.confidence_spin.setValue(0.85)
        self.step_editor.step_text_edit.setPlainText("cooking step: dice onions")
        
        values = self.step_editor.get_current_values()
        
        assert values['start_time'] == 32.0
        assert values['end_time'] == 47.0
        assert values['confidence_score'] == 0.85
        assert values['category'] == "cooking step: dice onions"
    
    def test_clear(self):
        """クリアテスト"""
        # まずアノテーションを設定
        self.step_editor.set_annotation(self.step_annotation)
        
        # クリア
        self.step_editor.clear()
        
        assert self.step_editor.current_annotation is None
        
        # フィールドがクリアされることを確認
        assert self.step_editor.start_time_spin.value() == 0.0
        assert self.step_editor.end_time_spin.value() == 0.0
        assert self.step_editor.confidence_spin.value() == 0.0
        assert self.step_editor.step_text_edit.toPlainText() == ""
    
    def test_set_enabled(self):
        """有効/無効設定テスト"""
        # 無効にする
        self.step_editor.set_enabled(False)
        
        assert not self.step_editor.start_time_spin.isEnabled()
        assert not self.step_editor.end_time_spin.isEnabled()
        assert not self.step_editor.confidence_spin.isEnabled()
        assert not self.step_editor.step_text_edit.isEnabled()
        
        # 有効にする
        self.step_editor.set_enabled(True)
        
        assert self.step_editor.start_time_spin.isEnabled()
        assert self.step_editor.end_time_spin.isEnabled()
        assert self.step_editor.confidence_spin.isEnabled()
        assert self.step_editor.step_text_edit.isEnabled()


class TestAnnotationEditorController(unittest.TestCase):
    """AnnotationEditorControllerクラスのテスト"""
    
    def setUp(self):
        """各テストメソッドの前に実行される設定"""
        if not QApplication.instance():
            self.app = QApplication([])
        
        self.data_manager = AnnotationDataManager()
        self.command_manager = AnnotationCommandManager(self.data_manager)
        self.editor_controller = AnnotationEditorController(self.data_manager, self.command_manager)
        
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
        
        # テスト用のアノテーション
        self.action_annotation = self.data_manager.add_annotation(
            start_time=10.0,
            end_time=20.0,
            annotation_type="Action",
            category="manipulation",
            confidence_score=0.9,
            hand_type="right"
        )
        
        self.step_annotation = self.data_manager.add_annotation(
            start_time=30.0,
            end_time=45.0,
            annotation_type="Step",
            category="cooking step",
            confidence_score=0.8
        )
    
    def test_initial_state(self):
        """初期状態のテスト"""
        assert self.editor_controller.data_manager == self.data_manager
        assert self.editor_controller.command_manager == self.command_manager
        assert isinstance(self.editor_controller.tab_widget, QTabWidget)
        assert isinstance(self.editor_controller.action_editor, ActionEditor)
        assert isinstance(self.editor_controller.step_editor, StepEditor)
        assert self.editor_controller.current_annotation is None
    
    def test_set_current_annotation_action(self):
        """Actionアノテーション設定テスト"""
        self.editor_controller.set_current_annotation(self.action_annotation)
        
        assert self.editor_controller.current_annotation == self.action_annotation
        
        # Actionタブがアクティブになることを確認
        assert self.editor_controller.tab_widget.currentIndex() == 0
        
        # ActionEditorにアノテーションが設定されることを確認
        assert self.editor_controller.action_editor.current_annotation == self.action_annotation
    
    def test_set_current_annotation_step(self):
        """Stepアノテーション設定テスト"""
        self.editor_controller.set_current_annotation(self.step_annotation)
        
        assert self.editor_controller.current_annotation == self.step_annotation
        
        # Stepタブがアクティブになることを確認
        assert self.editor_controller.tab_widget.currentIndex() == 1
        
        # StepEditorにアノテーションが設定されることを確認
        assert self.editor_controller.step_editor.current_annotation == self.step_annotation
    
    def test_clear_current_annotation(self):
        """現在アノテーションクリアテスト"""
        # まずアノテーションを設定
        self.editor_controller.set_current_annotation(self.action_annotation)
        
        # クリア
        self.editor_controller.clear_current_annotation()
        
        assert self.editor_controller.current_annotation is None
        assert self.editor_controller.action_editor.current_annotation is None
        assert self.editor_controller.step_editor.current_annotation is None
    
    def test_get_editor_widget(self):
        """エディターウィジェット取得テスト"""
        widget = self.editor_controller.get_editor_widget()
        assert isinstance(widget, QTabWidget)
        assert widget == self.editor_controller.tab_widget
    
    def test_apply_annotation_changes_action(self):
        """Actionアノテーション変更適用テスト"""
        # Actionアノテーションを設定
        self.editor_controller.set_current_annotation(self.action_annotation)
        
        # 変更データ
        new_values = {
            'start_time': 12.0,
            'end_time': 22.0,
            'confidence_score': 0.95,
            'category': 'navigation'
        }
        
        with patch.object(self.editor_controller, 'annotation_modified') as mock_signal:
            self.editor_controller.apply_annotation_changes(self.action_annotation, new_values)
            
            # シグナルが発信されたことを確認
            mock_signal.emit.assert_called_once_with(self.action_annotation, new_values)
    
    def test_apply_annotation_changes_step(self):
        """Stepアノテーション変更適用テスト"""
        # Stepアノテーションを設定
        self.editor_controller.set_current_annotation(self.step_annotation)
        
        # 変更データ
        new_values = {
            'start_time': 32.0,
            'end_time': 47.0,
            'category': 'cooking step: dice onions'
        }
        
        with patch.object(self.editor_controller, 'annotation_modified') as mock_signal:
            self.editor_controller.apply_annotation_changes(self.step_annotation, new_values)
            
            # シグナルが発信されたことを確認
            mock_signal.emit.assert_called_once_with(self.step_annotation, new_values)
    
    def test_delete_current_annotation(self):
        """現在アノテーション削除テスト"""
        # アノテーションを設定
        self.editor_controller.set_current_annotation(self.action_annotation)
        
        with patch.object(self.editor_controller, 'annotation_deleted') as mock_signal:
            self.editor_controller.delete_current_annotation()
            
            # シグナルが発信されたことを確認
            mock_signal.emit.assert_called_once_with(self.action_annotation.id)
            
            # 現在アノテーションがクリアされることを確認
            assert self.editor_controller.current_annotation is None
    
    def test_delete_current_annotation_none(self):
        """現在アノテーション未設定時の削除テスト"""
        # アノテーション未設定状態
        self.editor_controller.clear_current_annotation()
        
        with patch.object(self.editor_controller, 'annotation_deleted') as mock_signal:
            self.editor_controller.delete_current_annotation()
            
            # シグナルが発信されないことを確認
            mock_signal.emit.assert_not_called()
    
    def test_get_current_tab_type(self):
        """現在タブタイプ取得テスト"""
        # Actionタブを選択
        self.editor_controller.tab_widget.setCurrentIndex(0)
        assert self.editor_controller.get_current_tab_type() == "Action"
        
        # Stepタブを選択
        self.editor_controller.tab_widget.setCurrentIndex(1)
        assert self.editor_controller.get_current_tab_type() == "Step"
    
    def test_action_editor_signals(self):
        """ActionEditorシグナル連携テスト"""
        # Actionアノテーションを設定
        self.editor_controller.set_current_annotation(self.action_annotation)
        
        with patch.object(self.editor_controller, 'apply_annotation_changes') as mock_apply:
            # ActionEditorからのapply_changesシグナルをシミュレート
            self.editor_controller.action_editor.apply_changes()
            
            # apply_annotation_changesが呼ばれることを期待
            # （実際の実装では、ActionEditorにapply_changesシグナルが必要）
    
    def test_step_editor_signals(self):
        """StepEditorシグナル連携テスト"""
        # Stepアノテーションを設定
        self.editor_controller.set_current_annotation(self.step_annotation)
        
        with patch.object(self.editor_controller, 'apply_annotation_changes') as mock_apply:
            # StepEditorからのapply_changesシグナルをシミュレート
            self.editor_controller.step_editor.apply_changes()
            
            # apply_annotation_changesが呼ばれることを期待
            # （実際の実装では、StepEditorにapply_changesシグナルが必要）
    
    def test_data_changed_handling(self):
        """データ変更ハンドリングテスト"""
        # アノテーションを設定
        self.editor_controller.set_current_annotation(self.action_annotation)
        
        # データ変更シグナルをシミュレート
        with patch.object(self.editor_controller.action_editor, 'update_fields') as mock_update:
            self.editor_controller._on_data_changed()
            
            # フィールド更新が呼ばれることを確認
            mock_update.assert_called_once()
    
    def test_tab_change_handling(self):
        """タブ変更ハンドリングテスト"""
        # 現在のアノテーションタイプと異なるタブに変更した場合の処理
        self.editor_controller.set_current_annotation(self.action_annotation)
        
        # Stepタブに変更
        self.editor_controller.tab_widget.setCurrentIndex(1)
        
        # タブ変更時の処理をシミュレート
        self.editor_controller._on_tab_changed(1)
        
        # 適切な処理が行われることを確認
        # （実装によってはアノテーションをクリアするか、警告を表示するなど）


if __name__ == "__main__":
    import unittest
    
    # ログ設定
    logging.basicConfig(level=logging.DEBUG)
    
    # unittestの実行
    unittest.main()
