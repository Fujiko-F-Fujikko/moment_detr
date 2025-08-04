# annotation_editor_controller.py
"""
アノテーション編集タブコントロールクラス
ActionとStepの編集UI管理
"""

from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                           QFormLayout, QLineEdit, QDoubleSpinBox, QComboBox, 
                           QPushButton, QLabel, QTextEdit, QSpinBox, QGroupBox)
from PyQt6.QtGui import QFont
import logging
from typing import Optional, Dict, Any

from annotation_data_manager import AnnotationDataManager, AnnotationItem
from annotation_command_manager import AnnotationCommandManager


class ActionEditor(QWidget):
    """アクション編集ウィジェット"""
    
    # シグナル定義
    changes_applied = pyqtSignal(object, dict)  # annotation, new_values
    deletion_requested = pyqtSignal(object)  # annotation
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_annotation: Optional[AnnotationItem] = None
        
        self.setup_ui()
        self.logger.info("ActionEditor initialized")
    
    def setup_ui(self):
        """UI設定"""
        layout = QVBoxLayout(self)
        
        # タイトル
        title_label = QLabel("Action Annotation Editor")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 基本情報グループ
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        self.start_time_spin = QDoubleSpinBox()
        self.start_time_spin.setMinimum(0.0)
        self.start_time_spin.setMaximum(99999.0)
        self.start_time_spin.setDecimals(2)
        self.start_time_spin.setSuffix(" sec")
        basic_layout.addRow("Start Time:", self.start_time_spin)
        
        self.end_time_spin = QDoubleSpinBox()
        self.end_time_spin.setMinimum(0.0)
        self.end_time_spin.setMaximum(99999.0)
        self.end_time_spin.setDecimals(2)
        self.end_time_spin.setSuffix(" sec")
        basic_layout.addRow("End Time:", self.end_time_spin)
        
        self.confidence_spin = QDoubleSpinBox()
        self.confidence_spin.setMinimum(0.0)
        self.confidence_spin.setMaximum(1.0)
        self.confidence_spin.setDecimals(3)
        self.confidence_spin.setSingleStep(0.01)
        basic_layout.addRow("Confidence:", self.confidence_spin)
        
        layout.addWidget(basic_group)
        
        # アクション詳細グループ
        action_group = QGroupBox("Action Details")
        action_layout = QFormLayout(action_group)
        
        self.category_edit = QLineEdit()
        action_layout.addRow("Category:", self.category_edit)
        
        self.hand_type_combo = QComboBox()
        self.hand_type_combo.addItems(["", "left", "right", "both"])
        self.hand_type_combo.setEditable(True)
        action_layout.addRow("Hand Type:", self.hand_type_combo)
        
        self.object_edit = QLineEdit()
        action_layout.addRow("Object:", self.object_edit)
        
        self.verb_edit = QLineEdit()
        action_layout.addRow("Verb:", self.verb_edit)
        
        layout.addWidget(action_group)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("Apply Changes")
        self.apply_button.clicked.connect(self.apply_changes)
        button_layout.addWidget(self.apply_button)
        
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_fields)
        button_layout.addWidget(self.reset_button)
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_annotation)
        self.delete_button.setStyleSheet("QPushButton { color: red; }")
        button_layout.addWidget(self.delete_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        layout.addStretch()
        
        # 初期状態では無効化
        self.set_enabled(False)
    
    def set_annotation(self, annotation: AnnotationItem):
        """アノテーション設定"""
        if annotation.annotation_type != 'action':
            self.logger.warning(f"Received non-action annotation: {annotation.annotation_type}")
            return
        
        self.current_annotation = annotation
        self.update_fields()
        self.set_enabled(True)
        
        self.logger.debug(f"Set action annotation: {annotation.id}")
    
    def update_fields(self):
        """フィールド更新"""
        if not self.current_annotation:
            return
        
        self.start_time_spin.setValue(self.current_annotation.start_time)
        self.end_time_spin.setValue(self.current_annotation.end_time)
        self.confidence_spin.setValue(self.current_annotation.confidence_score)
        self.category_edit.setText(self.current_annotation.category or "")
        
        # 手の種類設定
        hand_type = self.current_annotation.hand_type or ""
        index = self.hand_type_combo.findText(hand_type)
        if index >= 0:
            self.hand_type_combo.setCurrentIndex(index)
        else:
            self.hand_type_combo.setCurrentText(hand_type)
        
        self.object_edit.setText(self.current_annotation.object_name or "")
        self.verb_edit.setText(self.current_annotation.verb or "")
    
    def get_current_values(self) -> Dict[str, Any]:
        """現在の値取得"""
        hand_type = self.hand_type_combo.currentText().strip()
        if not hand_type:
            hand_type = None
        
        object_name = self.object_edit.text().strip()
        if not object_name:
            object_name = None
        
        verb = self.verb_edit.text().strip()
        if not verb:
            verb = None
        
        return {
            'start_time': self.start_time_spin.value(),
            'end_time': self.end_time_spin.value(),
            'confidence_score': self.confidence_spin.value(),
            'category': self.category_edit.text().strip(),
            'hand_type': hand_type,
            'object_name': object_name,
            'verb': verb
        }
    
    def apply_changes(self):
        """変更適用"""
        if not self.current_annotation:
            return
        
        new_values = self.get_current_values()
        self.logger.info(f"Applying changes to action annotation: {self.current_annotation.id}")
        
        # 変更通知（シグナルエミット）
        self.changes_applied.emit(self.current_annotation, new_values)
    
    def reset_fields(self):
        """フィールドリセット"""
        if self.current_annotation:
            self.update_fields()
            self.logger.debug("Fields reset to original values")
    
    def delete_annotation(self):
        """アノテーション削除"""
        if not self.current_annotation:
            return
        
        self.logger.info(f"Deleting action annotation: {self.current_annotation.id}")
        
        # 削除通知（シグナルエミット）
        self.deletion_requested.emit(self.current_annotation)
    
    def clear(self):
        """クリア"""
        self.current_annotation = None
        self.set_enabled(False)
        
        # フィールドクリア
        self.start_time_spin.setValue(0.0)
        self.end_time_spin.setValue(0.0)
        self.confidence_spin.setValue(1.0)
        self.category_edit.clear()
        self.hand_type_combo.setCurrentIndex(0)
        self.object_edit.clear()
        self.verb_edit.clear()
    
    def set_enabled(self, enabled: bool):
        """有効/無効設定"""
        self.start_time_spin.setEnabled(enabled)
        self.end_time_spin.setEnabled(enabled)
        self.confidence_spin.setEnabled(enabled)
        self.category_edit.setEnabled(enabled)
        self.hand_type_combo.setEnabled(enabled)
        self.object_edit.setEnabled(enabled)
        self.verb_edit.setEnabled(enabled)
        self.apply_button.setEnabled(enabled)
        self.reset_button.setEnabled(enabled)
        self.delete_button.setEnabled(enabled)


class StepEditor(QWidget):
    """ステップ編集ウィジェット"""
    
    # シグナル定義
    changes_applied = pyqtSignal(object, dict)  # annotation, new_values
    deletion_requested = pyqtSignal(object)  # annotation
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_annotation: Optional[AnnotationItem] = None
        
        self.setup_ui()
        self.logger.info("StepEditor initialized")
    
    def setup_ui(self):
        """UI設定"""
        layout = QVBoxLayout(self)
        
        # タイトル
        title_label = QLabel("Step Annotation Editor")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 基本情報グループ
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        self.start_time_spin = QDoubleSpinBox()
        self.start_time_spin.setMinimum(0.0)
        self.start_time_spin.setMaximum(99999.0)
        self.start_time_spin.setDecimals(2)
        self.start_time_spin.setSuffix(" sec")
        basic_layout.addRow("Start Time:", self.start_time_spin)
        
        self.end_time_spin = QDoubleSpinBox()
        self.end_time_spin.setMinimum(0.0)
        self.end_time_spin.setMaximum(99999.0)
        self.end_time_spin.setDecimals(2)
        self.end_time_spin.setSuffix(" sec")
        basic_layout.addRow("End Time:", self.end_time_spin)
        
        self.confidence_spin = QDoubleSpinBox()
        self.confidence_spin.setMinimum(0.0)
        self.confidence_spin.setMaximum(1.0)
        self.confidence_spin.setDecimals(3)
        self.confidence_spin.setSingleStep(0.01)
        basic_layout.addRow("Confidence:", self.confidence_spin)
        
        layout.addWidget(basic_group)
        
        # ステップ詳細グループ
        step_group = QGroupBox("Step Details")
        step_layout = QFormLayout(step_group)
        
        self.step_text_edit = QTextEdit()
        self.step_text_edit.setMaximumHeight(100)
        step_layout.addRow("Step Description:", self.step_text_edit)
        
        layout.addWidget(step_group)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("Apply Changes")
        self.apply_button.clicked.connect(self.apply_changes)
        button_layout.addWidget(self.apply_button)
        
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_fields)
        button_layout.addWidget(self.reset_button)
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_annotation)
        self.delete_button.setStyleSheet("QPushButton { color: red; }")
        button_layout.addWidget(self.delete_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        layout.addStretch()
        
        # 初期状態では無効化
        self.set_enabled(False)
    
    def set_annotation(self, annotation: AnnotationItem):
        """アノテーション設定"""
        if annotation.annotation_type != 'step':
            self.logger.warning(f"Received non-step annotation: {annotation.annotation_type}")
            return
        
        self.current_annotation = annotation
        self.update_fields()
        self.set_enabled(True)
        
        self.logger.debug(f"Set step annotation: {annotation.id}")
    
    def update_fields(self):
        """フィールド更新"""
        if not self.current_annotation:
            return
        
        self.start_time_spin.setValue(self.current_annotation.start_time)
        self.end_time_spin.setValue(self.current_annotation.end_time)
        self.confidence_spin.setValue(self.current_annotation.confidence_score)
        self.step_text_edit.setPlainText(self.current_annotation.category or "")
    
    def get_current_values(self) -> Dict[str, Any]:
        """現在の値取得"""
        return {
            'start_time': self.start_time_spin.value(),
            'end_time': self.end_time_spin.value(),
            'confidence_score': self.confidence_spin.value(),
            'category': self.step_text_edit.toPlainText().strip()
        }
    
    def apply_changes(self):
        """変更適用"""
        if not self.current_annotation:
            return
        
        new_values = self.get_current_values()
        self.logger.info(f"Applying changes to step annotation: {self.current_annotation.id}")
        
        # 変更通知（シグナルエミット）
        self.changes_applied.emit(self.current_annotation, new_values)
    
    def reset_fields(self):
        """フィールドリセット"""
        if self.current_annotation:
            self.update_fields()
            self.logger.debug("Fields reset to original values")
    
    def delete_annotation(self):
        """アノテーション削除"""
        if not self.current_annotation:
            return
        
        self.logger.info(f"Deleting step annotation: {self.current_annotation.id}")
        
        # 削除通知（シグナルエミット）
        self.deletion_requested.emit(self.current_annotation)
    
    def clear(self):
        """クリア"""
        self.current_annotation = None
        self.set_enabled(False)
        
        # フィールドクリア
        self.start_time_spin.setValue(0.0)
        self.end_time_spin.setValue(0.0)
        self.confidence_spin.setValue(1.0)
        self.step_text_edit.clear()
    
    def set_enabled(self, enabled: bool):
        """有効/無効設定"""
        self.start_time_spin.setEnabled(enabled)
        self.end_time_spin.setEnabled(enabled)
        self.confidence_spin.setEnabled(enabled)
        self.step_text_edit.setEnabled(enabled)
        self.apply_button.setEnabled(enabled)
        self.reset_button.setEnabled(enabled)
        self.delete_button.setEnabled(enabled)


class AnnotationEditorController(QObject):
    """アノテーション編集タブコントロールクラス"""
    
    annotation_modified = pyqtSignal(object, dict, dict)  # annotation, old_values, new_values
    annotation_deleted = pyqtSignal(object)  # annotation
    
    def __init__(self, data_manager: AnnotationDataManager, command_manager: AnnotationCommandManager):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.data_manager = data_manager
        self.command_manager = command_manager
        
        self.tab_widget = None
        self.action_editor = None
        self.step_editor = None
        self.current_annotation: Optional[AnnotationItem] = None
        
        self._setup_editor_tabs()
        self.logger.info("AnnotationEditorController initialized")
    
    def _setup_editor_tabs(self):
        """編集タブ設定"""
        self.tab_widget = QTabWidget()
        
        # アクション編集タブ
        self.action_editor = ActionEditor()
        self.tab_widget.addTab(self.action_editor, "Action Edit")
        
        # ステップ編集タブ  
        self.step_editor = StepEditor()
        self.tab_widget.addTab(self.step_editor, "Step Edit")
        
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        # シグナル接続
        self.action_editor.changes_applied.connect(self.apply_annotation_changes)
        self.step_editor.changes_applied.connect(self.apply_annotation_changes)
        self.action_editor.deletion_requested.connect(self.delete_current_annotation)
        self.step_editor.deletion_requested.connect(self.delete_current_annotation)
    
    def set_current_annotation(self, annotation: AnnotationItem):
        """現在のアノテーション設定"""
        self.logger.info(f"Setting current annotation: {annotation.id}")
        self.current_annotation = annotation
        
        # 適切なタブに切り替え
        if annotation.annotation_type == 'step':
            self.tab_widget.setCurrentIndex(1)  # Step Edit
            self.step_editor.set_annotation(annotation)
            self.action_editor.clear()
        else:
            self.tab_widget.setCurrentIndex(0)  # Action Edit
            self.action_editor.set_annotation(annotation)
            self.step_editor.clear()
    
    def clear_current_annotation(self):
        """現在のアノテーションクリア"""
        self.logger.debug("Clearing current annotation")
        self.current_annotation = None
        self.action_editor.clear()
        self.step_editor.clear()
    
    def get_editor_widget(self) -> QTabWidget:
        """編集ウィジェット取得"""
        return self.tab_widget
    
    def apply_annotation_changes(self, annotation: AnnotationItem, new_values: Dict[str, Any]):
        """アノテーション変更適用"""
        if not annotation:
            return
        
        # 現在の値を取得（old_values作成）
        old_values = {
            'start_time': annotation.start_time,
            'end_time': annotation.end_time,
            'confidence_score': annotation.confidence_score,
            'category': annotation.category,
            'hand_type': annotation.hand_type,
            'object_name': annotation.object_name,
            'verb': annotation.verb
        }
        
        # 変更があるかチェック
        has_changes = False
        for key, new_value in new_values.items():
            old_value = old_values.get(key)
            if old_value != new_value:
                has_changes = True
                break
        
        if not has_changes:
            self.logger.debug("No changes detected")
            return
        
        self.logger.info(f"Applying changes to annotation {annotation.id}")
        
        # コマンドマネージャーで変更実行
        self.command_manager.execute_modify_annotation(
            annotation.id, old_values, new_values
        )
        
        # シグナル発信
        self.annotation_modified.emit(annotation, old_values, new_values)
    
    def delete_current_annotation(self):
        """現在のアノテーション削除"""
        if not self.current_annotation:
            return
        
        self.logger.info(f"Deleting annotation: {self.current_annotation.id}")
        
        # コマンドマネージャーで削除実行
        self.command_manager.execute_delete_annotation(self.current_annotation.id)
        
        # シグナル発信
        self.annotation_deleted.emit(self.current_annotation)
        
        # 編集フィールドクリア
        self.clear_current_annotation()
    
    def _on_tab_changed(self, index: int):
        """タブ変更時の処理"""
        tab_names = ["Action", "Step"]
        if 0 <= index < len(tab_names):
            self.logger.debug(f"Tab changed to: {tab_names[index]}")
        
        # 現在のアノテーションがある場合、新しいタブに応じて設定
        if self.current_annotation:
            if index == 0 and self.current_annotation.annotation_type == 'action':
                self.action_editor.set_annotation(self.current_annotation)
            elif index == 1 and self.current_annotation.annotation_type == 'step':
                self.step_editor.set_annotation(self.current_annotation)
    
    def get_current_tab_type(self) -> str:
        """現在のタブタイプ取得"""
        current_index = self.tab_widget.currentIndex()
        return "action" if current_index == 0 else "step"
