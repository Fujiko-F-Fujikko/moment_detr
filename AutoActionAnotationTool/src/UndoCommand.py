from PyQt6.QtGui import QUndoCommand  
  
class IntervalModifyCommand(QUndoCommand):  
    def __init__(self, interval, old_start, old_end, new_start, new_end, main_window, description="Modify Interval"):  
        super().__init__(description)  
        self.interval = interval  
        self.old_start = old_start  
        self.old_end = old_end  
        self.new_start = new_start  
        self.new_end = new_end  
        self.main_window = main_window  
          
    def redo(self):  
        print(f"DEBUG: IntervalModifyCommand.redo() called: {self.old_start}-{self.old_end} -> {self.new_start}-{self.new_end}")  
        self.interval.start_time = self.new_start  
        self.interval.end_time = self.new_end  
        self._update_ui()  
          
    def undo(self):  
        print(f"DEBUG: IntervalModifyCommand.undo() called: {self.new_start}-{self.new_end} -> {self.old_start}-{self.old_end}")  
        self.interval.start_time = self.old_start  
        self.interval.end_time = self.old_end  
        self._update_ui()  
      
    def _update_ui(self):  
        print(f"DEBUG: IntervalModifyCommand._update_ui() called")  
        if self.main_window:  
            self.main_window.update_display()  

class IntervalDeleteCommand(QUndoCommand):  
    def __init__(self, query_result, interval, index, description="Delete Interval"):  
        super().__init__(description)  
        self.query_result = query_result  
        self.interval = interval  
        self.index = index  
          
    def redo(self):  
        if self.interval in self.query_result.relevant_windows:  
            self.query_result.relevant_windows.remove(self.interval)  
              
    def undo(self):  
        self.query_result.relevant_windows.insert(self.index, self.interval)  
  
class IntervalAddCommand(QUndoCommand):  
    def __init__(self, query_result, interval, description="Add Interval"):  
        super().__init__(description)  
        self.query_result = query_result  
        self.interval = interval  
          
    def redo(self):  
        self.query_result.relevant_windows.append(self.interval)  
          
    def undo(self):  
        if self.interval in self.query_result.relevant_windows:  
            self.query_result.relevant_windows.remove(self.interval)