from PyQt6.QtGui import QUndoCommand

class StepModifyCommand(QUndoCommand):  
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
        """UI更新処理"""  
        if self.main_window:  
            # Stepsタイムラインを含む全体表示を更新  
            self.main_window.update_display()  
            # Step editタブのUIも更新  
            self.main_window.integrated_edit_widget.refresh_step_list()