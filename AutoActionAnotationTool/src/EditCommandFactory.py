# EditCommandFactory.py  
from PyQt6.QtGui import QUndoCommand  
  
from Results import QueryResults, DetectionInterval  
from IntervalEditCommand import IntervalEditCommand, IntervalDeleteCommand, IntervalAddCommand  
from ActionEditCommand import ActionDetailModifyCommand  
from StepEditCommand import StepEditCommand, StepDeleteCommand, StepAddCommand, StepTextEditCommand  
  
class EditCommandFactory:  
    """編集コマンドの生成を一元化するファクトリークラス"""  
      
    def __init__(self, main_window):  
        self.main_window = main_window  
      
    def create_interval_modify_command(self, interval: DetectionInterval,   
                                     old_start: float, old_end: float,  
                                     new_start: float, new_end: float,  
                                     description: str = "Modify Interval") -> IntervalEditCommand:  
        """区間時間変更コマンドを作成"""  
        return IntervalEditCommand(  
            interval, old_start, old_end, new_start, new_end,   
            self.main_window, description  
        )  
      
    def create_interval_delete_command(self, query_result: QueryResults,  
                                     interval: DetectionInterval, index: int,  
                                     description: str = "Delete Interval") -> IntervalDeleteCommand:  
        """区間削除コマンドを作成"""  
        return IntervalDeleteCommand(  
            query_result, interval, index, self.main_window, description  
        )  
      
    def create_interval_add_command(self, query_result: QueryResults,  
                                  interval: DetectionInterval,  
                                  description: str = "Add Interval") -> IntervalAddCommand:  
        """区間追加コマンドを作成"""  
        return IntervalAddCommand(  
            query_result, interval, self.main_window, description  
        )  
      
    def create_action_detail_modify_command(self, query_result: QueryResults,  
                                          old_query_text: str, new_query_text: str,  
                                          description: str = "Modify Action Details") -> ActionDetailModifyCommand:  
        """アクション詳細変更コマンドを作成"""  
        return ActionDetailModifyCommand(  
            query_result, old_query_text, new_query_text,   
            self.main_window, description  
        )  
      
    def create_step_modify_command(self, interval: DetectionInterval,  
                                 old_start: float, old_end: float,  
                                 new_start: float, new_end: float,  
                                 stt_data_manager, video_name: str,  
                                 description: str = "Modify Step") -> StepEditCommand:  
        """ステップ時間変更コマンドを作成"""  
        return StepEditCommand(  
            interval, old_start, old_end, new_start, new_end,  
            stt_data_manager, video_name, self.main_window, description  
        )  
      
    def create_step_add_command(self, stt_data_manager, video_name: str,  
                              step_text: str, segment: list,  
                              description: str = "Add Step") -> StepAddCommand:  
        """ステップ追加コマンドを作成"""  
        return StepAddCommand(  
            stt_data_manager, video_name, step_text, segment,  
            self.main_window, description  
        )  
      
    def create_step_delete_command(self, stt_data_manager, video_name: str,  
                                 step_index: int,  
                                 description: str = "Delete Step") -> StepDeleteCommand:  
        """ステップ削除コマンドを作成"""  
        return StepDeleteCommand(  
            stt_data_manager, video_name, step_index,  
            self.main_window, description  
        )  
      
    def create_step_text_modify_command(self, stt_data_manager, video_name: str,  
                                      step_index: int, old_text: str, new_text: str,  
                                      description: str = "Modify Step Text") -> StepTextEditCommand:  
        """ステップテキスト変更コマンドを作成"""  
        return StepTextEditCommand(  
            stt_data_manager, video_name, step_index, old_text, new_text,  
            self.main_window, description  
        )  
      
    def create_composite_command(self, commands: list,   
                               description: str = "Composite Edit") -> 'CompositeEditCommand':  
        """複数のコマンドを組み合わせた複合コマンドを作成"""  
        return CompositeEditCommand(commands, description)  
      
    def execute_command(self, command: QUndoCommand):  
        """コマンドを実行してUndoスタックにプッシュ"""  
        if self.main_window and hasattr(self.main_window, 'undo_stack'):  
            self.main_window.undo_stack.push(command)  
      
    def create_and_execute_interval_modify(self, interval: DetectionInterval,  
                                         old_start: float, old_end: float,  
                                         new_start: float, new_end: float) -> bool:  
        """区間変更コマンドを作成して実行"""  
        try:  
            command = self.create_interval_modify_command(  
                interval, old_start, old_end, new_start, new_end  
            )  
            self.execute_command(command)  
            return True  
        except Exception as e:  
            print(f"Failed to execute interval modify command: {e}")  
            return False  
      
    def create_and_execute_action_modify(self, query_result: QueryResults,  
                                       old_query_text: str, new_query_text: str) -> bool:  
        """アクション変更コマンドを作成して実行"""  
        try:  
            command = self.create_action_detail_modify_command(  
                query_result, old_query_text, new_query_text  
            )  
            self.execute_command(command)  
            return True  
        except Exception as e:  
            print(f"Failed to execute action modify command: {e}")  
            return False  
      
    def create_and_execute_step_add(self, stt_data_manager, video_name: str,  
                                  step_text: str, segment: list) -> bool:  
        """ステップ追加コマンドを作成して実行"""  
        try:  
            command = self.create_step_add_command(  
                stt_data_manager, video_name, step_text, segment  
            )  
            self.execute_command(command)  
            return True  
        except Exception as e:  
            print(f"Failed to execute step add command: {e}")  
            return False  

    def create_and_execute_step_text_modify(self, stt_data_manager, video_name: str,  
                                        step_index: int, old_text: str, new_text: str) -> bool:  
        """ステップテキスト変更コマンドを作成して実行"""  
        try:  
            command = self.create_step_text_modify_command(  
                stt_data_manager, video_name, step_index, old_text, new_text  
            )  
            self.execute_command(command)  
            return True  
        except Exception as e:  
            print(f"Failed to execute step text modify command: {e}")  
            return False  

    def create_and_execute_interval_delete(self, query_result: QueryResults,  
                                        interval: DetectionInterval, index: int) -> bool:  
        """区間削除コマンドを作成して実行"""  
        try:  
            command = self.create_interval_delete_command(query_result, interval, index)  
            self.execute_command(command)  
            return True  
        except Exception as e:  
            print(f"Failed to execute interval delete command: {e}")  
            return False  
    
    def create_and_execute_interval_add(self, query_result: QueryResults,  
                                    interval: DetectionInterval) -> bool:  
        """区間追加コマンドを作成して実行"""  
        try:  
            command = self.create_interval_add_command(query_result, interval)  
            self.execute_command(command)  
            return True  
        except Exception as e:  
            print(f"Failed to execute interval add command: {e}")  
            return False  
    
    def create_and_execute_step_modify(self, interval: DetectionInterval,  
                                    old_start: float, old_end: float,  
                                    new_start: float, new_end: float,  
                                    stt_data_manager, video_name: str) -> bool:  
        """ステップ変更コマンドを作成して実行"""  
        try:  
            command = self.create_step_modify_command(  
                interval, old_start, old_end, new_start, new_end,  
                stt_data_manager, video_name  
            )  
            self.execute_command(command)  
            return True  
        except Exception as e:  
            print(f"Failed to execute step modify command: {e}")  
            return False  
    
    def create_and_execute_step_delete(self, stt_data_manager, video_name: str,  
                                    step_index: int) -> bool:  
        """ステップ削除コマンドを作成して実行"""  
        try:  
            command = self.create_step_delete_command(stt_data_manager, video_name, step_index)  
            self.execute_command(command)  
            return True  
        except Exception as e:  
            print(f"Failed to execute step delete command: {e}")  
            return False

class CompositeEditCommand(QUndoCommand):  
    """複数のコマンドを組み合わせた複合コマンド"""  
      
    def __init__(self, commands: list, description: str = "Composite Edit"):  
        super().__init__(description)  
        self.commands = commands  
      
    def redo(self):  
        """全てのコマンドを順番に実行"""  
        for command in self.commands:  
            command.redo()  
      
    def undo(self):  
        """全てのコマンドを逆順でアンドゥ"""  
        for command in reversed(self.commands):  
            command.undo()