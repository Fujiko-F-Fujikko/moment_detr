# ActionEditCommand.py (修正版)    
from PyQt6.QtGui import QUndoCommand    
    
class ActionDetailModifyCommand(QUndoCommand):    
    def __init__(self, query_result, old_query_text, new_query_text, main_window, description="Modify Action Details"):    
        super().__init__(description)    
        self.query_result = query_result    
        self.old_query_text = old_query_text    
        self.new_query_text = new_query_text    
        self.main_window = main_window    
        self.query_type = "step" if old_query_text.startswith("Step:") or new_query_text.startswith("Step:") else "action"
            
    def redo(self):    
        self.query_result.query_text = self.new_query_text    
        self._update_ui()    
            
    def undo(self):    
        self.query_result.query_text = self.old_query_text    
        self._update_ui()    
        
    def _update_ui(self):  
        if self.main_window:  
            self.main_window.update_display()  
            
        if hasattr(self.main_window, 'application_coordinator'):  
            coordinator = self.main_window.application_coordinator  
              
            if self.query_type == "step":  
                # ステップ操作の場合の同期処理  
                coordinator.synchronize_step_updates()  
                  
                # StepEditorの更新  
                if hasattr(self.main_window, 'edit_widget_manager'):  
                    step_editor = self.main_window.edit_widget_manager.get_step_editor()  
                    if step_editor:  
                        step_editor._load_step_data()  
                        step_editor.refresh_step_list()  
            else:  
                # アクション操作の場合の既存処理  
                coordinator.synchronize_timeline_updates()  
                  
                # 既存のActionEditor更新処理  
                if hasattr(self.main_window, 'edit_widget_manager'):  
                    action_editor = self.main_window.edit_widget_manager.get_action_editor()  
                    if action_editor:  
                        current_interval = action_editor.selected_interval  
                        current_index = action_editor.selected_interval_index  
                        self.main_window.edit_widget_manager.set_current_query_results(self.query_result)  
                        if current_interval:  
                            action_editor.set_selected_interval(current_interval, current_index)  
              
            # 共通の同期処理  
            results_controller = coordinator.get_results_data_controller()  
            if results_controller:  
                results_controller._apply_current_filters()  
            coordinator.synchronize_components()

class StepTextModifyCommand(QUndoCommand):  
    def __init__(self, query_result, old_query_text, new_query_text, results_data_controller, main_window, description="Modify Step Text"):  
        super().__init__(description)  
        self.query_result = query_result  
        self.old_query_text = old_query_text  
        self.new_query_text = new_query_text  
        self.results_data_controller = results_data_controller  
        self.main_window = main_window  
          
    def redo(self):  
        # ResultsDataControllerのall_results内の該当オブジェクトを直接更新  
        if self.results_data_controller:  
            for qr in self.results_data_controller.all_results:  
                if qr == self.query_result:  
                    qr.query_text = self.new_query_text  
                    break  
        self._update_ui()  
          
    def undo(self):  
        # ResultsDataControllerのall_results内の該当オブジェクトを直接更新  
        if self.results_data_controller:  
            for qr in self.results_data_controller.all_results:  
                if qr == self.query_result:  
                    qr.query_text = self.old_query_text  
                    break  
        self._update_ui()  
          
    def _update_ui(self):  
        if self.main_window:  
            self.main_window.update_display()  
              
        if self.results_data_controller:  
            # フィルタを再適用してUIを更新  
            self.results_data_controller._apply_current_filters()  
            self.results_data_controller.resultsUpdated.emit(self.results_data_controller.all_results)