# ActionEditCommand.py (新規)  
from PyQt6.QtGui import QUndoCommand  
  
class ActionDetailModifyCommand(QUndoCommand):  
    def __init__(self, query_result, old_query_text, new_query_text, main_window, description="Modify Action Details"):  
        super().__init__(description)  
        self.query_result = query_result  
        self.old_query_text = old_query_text  
        self.new_query_text = new_query_text  
        self.main_window = main_window  
          
    def redo(self):  
        self.query_result.query_text = self.new_query_text  
        self._update_ui()  
          
    def undo(self):  
        self.query_result.query_text = self.old_query_text  
        self._update_ui()  
      
    def _update_ui(self):  
        if self.main_window:  
            self.main_window.update_display()

        # IntegratedEditWidgetのUIも更新  
        if hasattr(self.main_window, 'integrated_edit_widget'):  
            self.main_window.integrated_edit_widget.update_interval_ui()