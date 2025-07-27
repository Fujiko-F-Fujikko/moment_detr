# UnifiedEditCommand.py  
import logging  
from typing import Dict, Any  
from PyQt6.QtGui import QUndoCommand  
  
from UnifiedDataController import UnifiedDataController  
from UnifiedInterval import UnifiedInterval  
  
logger = logging.getLogger(__name__)  
  
class UnifiedEditCommand(QUndoCommand):  
    """統一された編集コマンドクラス"""  
      
    def __init__(self, command_type: str, data_controller: UnifiedDataController,  
                 interval_id: str, old_data: Dict[str, Any], new_data: Dict[str, Any],  
                 main_window, description: str = "Edit Interval"):  
        super().__init__(description)  
        self.command_type = command_type  # "modify", "add", "delete"  
        self.data_controller = data_controller  
        self.interval_id = interval_id  
        self.old_data = old_data  
        self.new_data = new_data  
        self.main_window = main_window  
          
        logger.info(f"Created {command_type} command for interval: {interval_id}")  
      
    def redo(self):  
        """コマンドを実行"""  
        try:  
            if self.command_type == "modify":  
                success = self.data_controller.modify_interval(self.interval_id, self.new_data)  
            elif self.command_type == "add":  
                # new_dataにはUnifiedIntervalオブジェクトが含まれる  
                interval = self.new_data.get('interval')  
                success = self.data_controller.add_interval(interval)  
            elif self.command_type == "delete":  
                success = self.data_controller.delete_interval(self.interval_id)  
            else:  
                logger.error(f"Unknown command type: {self.command_type}")  
                return  
              
            if success:  
                self.update_ui()  
                logger.info(f"Executed {self.command_type} command successfully")  
            else:  
                logger.error(f"Failed to execute {self.command_type} command")  
          
        except Exception as e:  
            logger.error(f"Error executing {self.command_type} command: {e}")  
      
    def undo(self):  
        """コマンドを取り消し"""  
        try:  
            if self.command_type == "modify":  
                success = self.data_controller.modify_interval(self.interval_id, self.old_data)  
            elif self.command_type == "add":  
                success = self.data_controller.delete_interval(self.interval_id)  
            elif self.command_type == "delete":  
                # old_dataにはUnifiedIntervalオブジェクトが含まれる  
                interval = self.old_data.get('interval')  
                success = self.data_controller.add_interval(interval)  
            else:  
                logger.error(f"Unknown command type: {self.command_type}")  
                return  
              
            if success:  
                self.update_ui()  
                logger.info(f"Undid {self.command_type} command successfully")  
            else:  
                logger.error(f"Failed to undo {self.command_type} command")  
          
        except Exception as e:  
            logger.error(f"Error undoing {self.command_type} command: {e}")  
      
    def update_ui(self):  
        """UI更新"""  
        if self.main_window and hasattr(self.main_window, 'update_display'):  
            self.main_window.update_display()  
          
        # ApplicationCoordinatorを通じた同期  
        if (self.main_window and   
            hasattr(self.main_window, 'application_coordinator')):  
            coordinator = self.main_window.application_coordinator  
            coordinator.synchronize_components()  
      
    @classmethod  
    def create_modify_command(cls, data_controller: UnifiedDataController,  
                            interval_id: str, old_data: Dict[str, Any],   
                            new_data: Dict[str, Any], main_window) -> 'UnifiedEditCommand':  
        """変更コマンドを作成"""  
        return cls("modify", data_controller, interval_id, old_data, new_data,   
                  main_window, "Modify Interval")  
      
    @classmethod  
    def create_add_command(cls, data_controller: UnifiedDataController,  
                          interval: UnifiedInterval, main_window) -> 'UnifiedEditCommand':  
        """追加コマンドを作成"""  
        return cls("add", data_controller, interval.interval_id,   
                  {}, {"interval": interval}, main_window, "Add Interval")  
      
    @classmethod  
    def create_delete_command(cls, data_controller: UnifiedDataController,  
                            interval: UnifiedInterval, main_window) -> 'UnifiedEditCommand':  
        """削除コマンドを作成"""  
        return cls("delete", data_controller, interval.interval_id,  
                  {"interval": interval}, {}, main_window, "Delete Interval")