# StepModifyCommand.py (拡張版)  
from PyQt6.QtGui import QUndoCommand  
  
class StepEditCommand(QUndoCommand):  
    def __init__(self, interval, old_start, old_end, new_start, new_end,   
                 stt_data_manager, video_name, main_window, description="Modify Step"):  
        super().__init__(description)  
        self.interval = interval  
        self.old_start = old_start  
        self.old_end = old_end  
        self.new_start = new_start  
        self.new_end = new_end  
        self.stt_data_manager = stt_data_manager  
        self.video_name = video_name  
        self.main_window = main_window  
          
    def redo(self):  
        self.interval.start_time = self.new_start  
        self.interval.end_time = self.new_end  
        self._update_stt_data(self.new_start, self.new_end)  
        self._update_ui()  
          
    def undo(self):  
        self.interval.start_time = self.old_start  
        self.interval.end_time = self.old_end  
        self._update_stt_data(self.old_start, self.old_end)  
        self._update_ui()  
      
    def _update_stt_data(self, start_time, end_time):  
        if (self.video_name and   
            self.video_name in self.stt_data_manager.stt_dataset.database):  
            video_data = self.stt_data_manager.stt_dataset.database[self.video_name]  
            step_text = self.interval.label  
            for step in video_data.steps:  
                if step.step == step_text:  
                    step.segment = [start_time, end_time]  
                    fps = video_data.fps  
                    step.segment_frames = [int(start_time * fps), int(end_time * fps)]  
                    break  
      
    def _update_ui(self):    
        if self.main_window:    
            self.main_window.update_display()    
            if hasattr(self.main_window, 'integrated_edit_widget'):    
                # リストを更新  
                self.main_window.integrated_edit_widget.refresh_step_list()  
                
                # 選択状態を復元  
                self.main_window.integrated_edit_widget._restore_step_selection(  
                    self.interval.label, None  
                )  
                
                self.main_window.integrated_edit_widget.update_interval_ui()

class StepAddCommand(QUndoCommand):  
    def __init__(self, stt_data_manager, video_name, step_text, segment, main_window, description="Add Step"):  
        super().__init__(description)  
        self.stt_data_manager = stt_data_manager  
        self.video_name = video_name  
        self.step_text = step_text  
        self.segment = segment  
        self.main_window = main_window  
        self.step_entry = None  
          
    def redo(self):  
        self.stt_data_manager.add_step(self.video_name, self.step_text, self.segment)  
        # 追加されたステップエントリを保存  
        if self.video_name in self.stt_data_manager.stt_dataset.database:  
            video_data = self.stt_data_manager.stt_dataset.database[self.video_name]  
            self.step_entry = video_data.steps[-1]  # 最後に追加されたもの  
        self._update_ui()  
          
    def undo(self):  
        if (self.step_entry and self.video_name in self.stt_data_manager.stt_dataset.database):  
            video_data = self.stt_data_manager.stt_dataset.database[self.video_name]  
            if self.step_entry in video_data.steps:  
                video_data.steps.remove(self.step_entry)  
        self._update_ui()  
      
    def _update_ui(self):    
        if self.main_window:    
            self.main_window.update_display()    
            if hasattr(self.main_window, 'integrated_edit_widget'):    
                self.main_window.integrated_edit_widget.refresh_step_list()  
                # StepAddCommandでは step_text を使用  
                self.main_window.integrated_edit_widget._restore_step_selection(  
                    self.step_text, len(self.main_window.integrated_edit_widget.step_list) - 1  
                )  
                self.main_window.integrated_edit_widget.update_interval_ui()

class StepDeleteCommand(QUndoCommand):  
    def __init__(self, stt_data_manager, video_name, step_index, main_window, description="Delete Step"):  
        super().__init__(description)  
        self.stt_data_manager = stt_data_manager  
        self.video_name = video_name  
        self.step_index = step_index  
        self.main_window = main_window  
        self.deleted_step = None  
          
    def redo(self):  
        if self.video_name in self.stt_data_manager.stt_dataset.database:  
            video_data = self.stt_data_manager.stt_dataset.database[self.video_name]  
            if self.step_index < len(video_data.steps):  
                self.deleted_step = video_data.steps[self.step_index]  
                del video_data.steps[self.step_index]  
        self._update_ui()  
          
    def undo(self):  
        if (self.deleted_step and self.video_name in self.stt_data_manager.stt_dataset.database):  
            video_data = self.stt_data_manager.stt_dataset.database[self.video_name]  
            video_data.steps.insert(self.step_index, self.deleted_step)  
        self._update_ui()  
      
    def _update_ui(self):    
        if self.main_window:    
            self.main_window.update_display()    
            if hasattr(self.main_window, 'integrated_edit_widget'):    
                self.main_window.integrated_edit_widget.refresh_step_list()  
                # StepDeleteCommandでは削除後なので選択復元は不要  
                self.main_window.integrated_edit_widget.update_interval_ui()

class StepTextEditCommand(QUndoCommand):  
    def __init__(self, stt_data_manager, video_name, step_index, old_text, new_text, main_window, description="Modify Step Text"):  
        super().__init__(description)  
        self.stt_data_manager = stt_data_manager  
        self.video_name = video_name  
        self.step_index = step_index  
        self.old_text = old_text  
        self.new_text = new_text  
        self.main_window = main_window  
          
    def redo(self):  
        self._set_step_text(self.new_text)  
        self._update_ui()  
          
    def undo(self):  
        self._set_step_text(self.old_text)  
        self._update_ui()  
      
    def _set_step_text(self, text):  
        if self.video_name in self.stt_data_manager.stt_dataset.database:  
            video_data = self.stt_data_manager.stt_dataset.database[self.video_name]  
            if self.step_index < len(video_data.steps):  
                video_data.steps[self.step_index].step = text  
      
    def _update_ui(self):    
        if self.main_window:    
            self.main_window.update_display()    
            if hasattr(self.main_window, 'integrated_edit_widget'):    
                # リストを更新  
                self.main_window.integrated_edit_widget.refresh_step_list()  
                
                # 選択状態を復元  
                self.main_window.integrated_edit_widget._restore_step_selection(  
                    self.new_text, self.step_index  
                )  
                
                self.main_window.integrated_edit_widget.update_interval_ui()