# annotation_command_manager.py
"""
Undo/Redo管理クラス
アノテーション操作のコマンドパターン実装
"""

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QUndoStack, QUndoCommand
from typing import Dict, Any, Optional
import logging

from annotation_data_manager import AnnotationDataManager, AnnotationItem


class AnnotationCommand(QUndoCommand):
    """アノテーション操作コマンド基底クラス"""
    
    def __init__(self, data_manager: AnnotationDataManager, description: str):
        super().__init__(description)
        self.data_manager = data_manager
        self.logger = logging.getLogger(self.__class__.__name__)


class AddAnnotationCommand(AnnotationCommand):
    """アノテーション追加コマンド"""
    
    def __init__(self, data_manager: AnnotationDataManager, annotation_type: str, 
                 start_time: float, end_time: float, category: str, 
                 confidence_score: float = 1.0, **kwargs):
        super().__init__(data_manager, f"Add {annotation_type} annotation")
        self.annotation_type = annotation_type
        self.start_time = start_time
        self.end_time = end_time
        self.category = category
        self.confidence_score = confidence_score
        self.kwargs = kwargs
        self.annotation: Optional[AnnotationItem] = None
        self.index = -1
    
    def redo(self):
        self.logger.info(f"Redo: Adding {self.annotation_type} annotation")
        if self.annotation is None:
            # 初回実行
            self.annotation = self.data_manager.add_annotation(
                self.annotation_type, self.start_time, self.end_time, 
                self.category, self.confidence_score, **self.kwargs
            )
            self.index = len(self.data_manager.annotations) - 1
        else:
            # 再実行
            self.data_manager.annotations.insert(self.index, self.annotation)
            self.data_manager.annotation_added.emit(self.annotation)
            self.data_manager.data_changed.emit()
    
    def undo(self):
        self.logger.info(f"Undo: Removing {self.annotation_type} annotation")
        if self.annotation in self.data_manager.annotations:
            self.index = self.data_manager.annotations.index(self.annotation)
            self.data_manager.annotations.remove(self.annotation)
            self.data_manager.annotation_deleted.emit(self.annotation)
            self.data_manager.data_changed.emit()


class ModifyAnnotationCommand(AnnotationCommand):
    """アノテーション修正コマンド"""
    
    def __init__(self, data_manager: AnnotationDataManager, annotation_id: str, 
                 old_values: Dict[str, Any], new_values: Dict[str, Any]):
        super().__init__(data_manager, f"Modify annotation {annotation_id}")
        self.annotation_id = annotation_id
        self.old_values = old_values
        self.new_values = new_values
    
    def redo(self):
        self.logger.info(f"Redo: Modifying annotation {self.annotation_id}")
        annotation = self.data_manager.get_annotation_by_id(self.annotation_id)
        if annotation:
            index = self.data_manager.annotations.index(annotation)
            self.data_manager.modify_annotation(index, **self.new_values)
    
    def undo(self):
        self.logger.info(f"Undo: Restoring annotation {self.annotation_id}")
        annotation = self.data_manager.get_annotation_by_id(self.annotation_id)
        if annotation:
            index = self.data_manager.annotations.index(annotation)
            self.data_manager.modify_annotation(index, **self.old_values)


class DeleteAnnotationCommand(AnnotationCommand):
    """アノテーション削除コマンド"""
    
    def __init__(self, data_manager: AnnotationDataManager, annotation_id: str):
        super().__init__(data_manager, f"Delete annotation {annotation_id}")
        self.annotation_id = annotation_id
        self.annotation: Optional[AnnotationItem] = None
        self.index = -1
    
    def redo(self):
        self.logger.info(f"Redo: Deleting annotation {self.annotation_id}")
        annotation = self.data_manager.get_annotation_by_id(self.annotation_id)
        if annotation:
            self.annotation = annotation
            self.index = self.data_manager.annotations.index(annotation)
            self.data_manager.delete_annotation(self.index)
    
    def undo(self):
        self.logger.info(f"Undo: Restoring annotation {self.annotation_id}")
        if self.annotation:
            self.data_manager.annotations.insert(self.index, self.annotation)
            self.data_manager.annotation_added.emit(self.annotation)
            self.data_manager.data_changed.emit()


class AnnotationCommandManager(QObject):
    """Undo/Redo管理クラス"""
    
    command_executed = pyqtSignal(str)  # command_description
    undo_available = pyqtSignal(bool)
    redo_available = pyqtSignal(bool)
    
    def __init__(self, data_manager: AnnotationDataManager):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.data_manager = data_manager
        self.undo_stack = QUndoStack()
        
        # シグナル接続
        self.undo_stack.indexChanged.connect(self._on_stack_changed)
        self.undo_stack.canUndoChanged.connect(self.undo_available.emit)
        self.undo_stack.canRedoChanged.connect(self.redo_available.emit)
        
        self.logger.info("AnnotationCommandManager initialized")
    
    def __del__(self):
        """デストラクタ"""
        try:
            if hasattr(self, 'undo_stack') and self.undo_stack is not None:
                # シグナル切断
                self.undo_stack.indexChanged.disconnect()
                self.undo_stack.canUndoChanged.disconnect()
                self.undo_stack.canRedoChanged.disconnect()
        except (RuntimeError, AttributeError):
            # オブジェクトが既に削除されている場合は無視
            pass
    
    def execute_add_annotation(self, annotation_type: str, start_time: float, 
                             end_time: float, category: str, 
                             confidence_score: float = 1.0, **kwargs):
        """アノテーション追加コマンド実行"""
        self.logger.info(f"Executing add {annotation_type} annotation command")
        command = AddAnnotationCommand(
            self.data_manager, annotation_type, start_time, end_time, 
            category, confidence_score, **kwargs
        )
        self.undo_stack.push(command)
        self.command_executed.emit(command.text())
        return command.annotation
    
    def execute_modify_annotation(self, annotation_id: str, 
                                old_values: Dict[str, Any], 
                                new_values: Dict[str, Any]):
        """アノテーション修正コマンド実行"""
        self.logger.info(f"Executing modify annotation command: {annotation_id}")
        command = ModifyAnnotationCommand(
            self.data_manager, annotation_id, old_values, new_values
        )
        self.undo_stack.push(command)
        self.command_executed.emit(command.text())
    
    def execute_delete_annotation(self, annotation_id: str):
        """アノテーション削除コマンド実行"""
        self.logger.info(f"Executing delete annotation command: {annotation_id}")
        command = DeleteAnnotationCommand(self.data_manager, annotation_id)
        self.undo_stack.push(command)
        self.command_executed.emit(command.text())
        return True
    
    def undo(self):
        """Undo実行"""
        try:
            if self.undo_stack is not None and self.undo_stack.canUndo():
                self.logger.info("Executing undo")
                self.undo_stack.undo()
        except RuntimeError:
            pass
    
    def redo(self):
        """Redo実行"""
        try:
            if self.undo_stack is not None and self.undo_stack.canRedo():
                self.logger.info("Executing redo")
                self.undo_stack.redo()
        except RuntimeError:
            pass
    
    def clear(self):
        """コマンド履歴クリア"""
        try:
            if self.undo_stack is not None:
                self.logger.info("Clearing command history")
                self.undo_stack.clear()
        except RuntimeError:
            pass
    
    def get_undo_stack(self) -> QUndoStack:
        """UndoStackを取得（メニューアクション作成用）"""
        if self.undo_stack is None:
            # 新しいスタックを作成（エラー回避）
            self.undo_stack = QUndoStack()
        return self.undo_stack
    
    def _on_stack_changed(self, index: int):
        """スタック変更時の処理"""
        try:
            if self.undo_stack is None:
                return
            self.logger.debug(f"Undo stack index changed to: {index}")
            self.logger.debug(f"Can undo: {self.undo_stack.canUndo()}")
            self.logger.debug(f"Can redo: {self.undo_stack.canRedo()}")
        except RuntimeError:
            # QUndoStackが削除されている場合は無視
            pass
    
    def get_command_count(self) -> int:
        """コマンド数取得"""
        try:
            if self.undo_stack is None:
                return 0
            return self.undo_stack.count()
        except RuntimeError:
            return 0
    
    def get_current_index(self) -> int:
        """現在のインデックス取得"""
        try:
            if self.undo_stack is None:
                return 0
            return self.undo_stack.index()
        except RuntimeError:
            return 0
