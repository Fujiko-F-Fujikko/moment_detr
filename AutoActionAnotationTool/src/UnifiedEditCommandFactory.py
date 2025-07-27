# UnifiedEditCommandFactory.py  
import logging  
from typing import Dict, Any  
from PyQt6.QtGui import QUndoStack  
  
from UnifiedDataController import UnifiedDataController  
from UnifiedInterval import UnifiedInterval  
from UnifiedEditCommand import UnifiedEditCommand  
  
logger = logging.getLogger(__name__)  
  
class UnifiedEditCommandFactory:  
    """統一された編集コマンドファクトリ"""  
      
    def __init__(self, data_controller: UnifiedDataController, main_window):  
        self.data_controller = data_controller  
        self.main_window = main_window  
        self.undo_stack = QUndoStack()  
          
        logger.info("UnifiedEditCommandFactory initialized")  
      
    def create_and_execute_modify(self, interval_id: str, old_data: Dict[str, Any],  
                                new_data: Dict[str, Any]) -> bool:  
        """変更コマンドを作成して実行"""  
        try:  
            command = UnifiedEditCommand.create_modify_command(  
                self.data_controller, interval_id, old_data, new_data, self.main_window  
            )  
              
            self.undo_stack.push(command)  
            logger.info(f"Executed modify command for interval: {interval_id}")  
            return True  
          
        except Exception as e:  
            logger.error(f"Failed to create/execute modify command: {e}")  
            return False  
      
    def create_and_execute_add(self, interval: UnifiedInterval) -> bool:  
        """追加コマンドを作成して実行"""  
        try:  
            command = UnifiedEditCommand.create_add_command(  
                self.data_controller, interval, self.main_window  
            )  
              
            self.undo_stack.push(command)  
            logger.info(f"Executed add command for interval: {interval.interval_id}")  
            return True  
          
        except Exception as e:  
            logger.error(f"Failed to create/execute add command: {e}")  
            return False  
      
    def create_and_execute_delete(self, interval: UnifiedInterval) -> bool:  
        """削除コマンドを作成して実行"""  
        try:  
            command = UnifiedEditCommand.create_delete_command(  
                self.data_controller, interval, self.main_window  
            )  
              
            self.undo_stack.push(command)  
            logger.info(f"Executed delete command for interval: {interval.interval_id}")  
            return True  
          
        except Exception as e:  
            logger.error(f"Failed to create/execute delete command: {e}")  
            return False  
      
    def get_undo_stack(self) -> QUndoStack:  
        """UndoStackを取得"""  
        return self.undo_stack