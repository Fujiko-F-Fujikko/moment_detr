# EditCommandFactory.py (修正版)  
from DataClasses import QueryResults, DetectionInterval  
from IntervalEditCommand import IntervalEditCommand, IntervalDeleteCommand, IntervalAddCommand
from ActionEditCommand import ActionDetailModifyCommand, StepTextModifyCommand

  
class EditCommandFactory:  
    """編集コマンドの生成を一元化するファクトリークラス"""  
      
    def __init__(self, main_window):  
        self.main_window = main_window  
      
    # === 区間操作コマンド ===  
      
    def create_interval_modify_command(self, interval: DetectionInterval,  
                                     old_start: float, old_end: float,  
                                     new_start: float, new_end: float,  
                                     description: str = "Modify Interval") -> IntervalEditCommand:  
        """区間時間変更コマンドを作成"""  
        return IntervalEditCommand(  
            interval, old_start, old_end, new_start, new_end,  
            self.main_window, description  
        )  
      
    def create_and_execute_interval_modify(self, interval, old_start, old_end, new_start, new_end):  
        """区間修正コマンドを作成・実行"""  
        command = self.create_interval_modify_command(  
            interval, old_start, old_end, new_start, new_end  
        )  
        if self.main_window and hasattr(self.main_window, 'undo_stack'):  
            self.main_window.undo_stack.push(command)  
      
    def create_interval_delete_command(self, query_result: QueryResults,  
                                    interval: DetectionInterval, index: int,  
                                    description: str = "Delete Interval") -> IntervalDeleteCommand:  
        """区間削除コマンドを作成"""  
        return IntervalDeleteCommand(  
            query_result, interval, index, self.main_window, description  
        )

    def create_and_execute_interval_delete(self, query_result: QueryResults,   
                                        interval: DetectionInterval, index: int):
        """区間削除コマンドを作成して実行"""  
        command = self.create_interval_delete_command(query_result, interval, index)  
        if self.main_window and hasattr(self.main_window, 'undo_stack'):  
            self.main_window.undo_stack.push(command)  

    def create_interval_add_command(self, query_result: QueryResults,  
                                  interval: DetectionInterval,  
                                  description: str = "Add Interval") -> IntervalAddCommand:  
        """区間追加コマンドを作成"""  
        return IntervalAddCommand(  
            query_result, interval, self.main_window, description  
        )  
      
    def create_and_execute_interval_add(self, query_result: QueryResults,  
                                      interval: DetectionInterval):  
        """区間追加コマンドを作成して実行"""  
        command = self.create_interval_add_command(query_result, interval)  
        if self.main_window and hasattr(self.main_window, 'undo_stack'):  
            self.main_window.undo_stack.push(command)


    # === アクション操作コマンド ===  
      
    def create_action_detail_modify_command(self, query_result: QueryResults,  
                                          old_query_text: str, new_query_text: str,  
                                          description: str = "Modify Action Details") -> ActionDetailModifyCommand:  
        """アクション詳細変更コマンドを作成"""  
        return ActionDetailModifyCommand(  
            query_result, old_query_text, new_query_text,  
            self.main_window, description  
        )  
      
    def create_and_execute_action_modify(self, query_result, old_text, new_text):  
        """アクション修正コマンドを作成・実行"""  
        command = self.create_action_detail_modify_command(  
            query_result, old_text, new_text  
        )  
        if self.main_window and hasattr(self.main_window, 'undo_stack'):  
            self.main_window.undo_stack.push(command)  
      
    # === ステップ操作コマンド（ResultsDataController対応版） ===  
      
    def create_and_execute_step_add_query_result(self, results_controller, query_result):  
        """ステップ用QueryResult追加コマンドを作成・実行"""  
        results_controller.add_step_query_result(query_result)  
      
    def create_and_execute_step_delete_query_result(self, results_controller, query_result):  
        """ステップ用QueryResult削除コマンドを作成・実行"""  
        results_controller.remove_step_query_result(query_result)  
      
    def create_step_text_modify_command(self, query_result: QueryResults,  
                                          old_query_text: str, new_query_text: str,  
                                          description: str = "Modify Action Details") -> ActionDetailModifyCommand:  
        """ステップテキスト変更コマンドを作成"""  
        # ApplicationCoordinatorからResultsDataControllerを取得  
        results_data_controller = None  
        if hasattr(self.main_window, 'application_coordinator'):  
            results_data_controller = self.main_window.application_coordinator.results_data_controller  

        return StepTextModifyCommand(  
            query_result, old_query_text, new_query_text,   
            results_data_controller, self.main_window  
        )  

    def create_and_execute_step_text_modify(self, query_result, old_query_text, new_query_text):  
        """Step用テキスト変更コマンドを作成・実行"""  
        print(f"[DEBUG] create_and_execute_step_text_modify called")  
        print(f"[DEBUG] query_result: {query_result}")  
        print(f"[DEBUG] old_query_text: '{old_query_text}'")  
        print(f"[DEBUG] new_query_text: '{new_query_text}'")  
          
        command = self.create_step_text_modify_command(  
            query_result, old_query_text, new_query_text  
        )
        print(f"[DEBUG] Command created: {command}")  
          
        if self.main_window and hasattr(self.main_window, 'undo_stack'):  
            self.main_window.undo_stack.push(command)  
            print(f"[DEBUG] Command pushed to undo_stack")  
        else:  
            print(f"[DEBUG] ERROR: Cannot push command - no undo_stack")