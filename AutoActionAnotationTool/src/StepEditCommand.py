# StepEditCommand.py (修正版)  
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
  
        # 新しいアーキテクチャではEditWidgetManagerを使用  
        if hasattr(self.main_window, 'edit_widget_manager'):  
            # ActionEditorのUIを更新  
            step_editor = self.main_window.edit_widget_manager.get_step_editor()  
            step_editor.refresh_step_list()  
            step_editor._update_step_edit_ui()  
              
            # 全体のUIも更新  
            self.main_window.edit_widget_manager.refresh_ui()  
                    
class StepAddCommand(QUndoCommand):  
    def __init__(self, stt_data_manager, video_name, step_text, segment, main_window, description="Add Step"):  
        super().__init__(description)  
        self.stt_data_manager = stt_data_manager  
        self.video_name = video_name  
        self.step_text = step_text  
        self.segment = segment  
        self.main_window = main_window  
        self.added_step_entry = None  
          
    def redo(self):  
        # STTDataManagerを使用してステップを追加  
        success = self.stt_data_manager.add_step(self.video_name, self.step_text, self.segment)  
        if success:  
            # 追加されたステップエントリの参照を保存  
            video_data = self.stt_data_manager.stt_dataset.database[self.video_name]  
            self.added_step_entry = video_data.steps[-1]  # 最後に追加されたステップ  
        self._update_ui()  
          
    def undo(self):  
        if self.added_step_entry and self.video_name in self.stt_data_manager.stt_dataset.database:  
            video_data = self.stt_data_manager.stt_dataset.database[self.video_name]  
            if self.added_step_entry in video_data.steps:  
                video_data.steps.remove(self.added_step_entry)  
        self._update_ui()  
      
    def _update_ui(self):      
        if self.main_window:  
            self.main_window.update_display()  

        # 新しいアーキテクチャではEditWidgetManagerを使用  
        if hasattr(self.main_window, 'edit_widget_manager'):  
            # 全体のUIを更新  
            self.main_window.edit_widget_manager.refresh_ui()

            # 選択状態を復元  
            step_editor = self.main_window.edit_widget_manager.get_step_editor()  
            step_editor.select_step(  
                step_text=self.step_text, step_index=None
            )

  
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
                video_data.steps.pop(self.step_index)  
        self._update_ui()  
          
    def undo(self):  
        if self.deleted_step and self.video_name in self.stt_data_manager.stt_dataset.database:  
            video_data = self.stt_data_manager.stt_dataset.database[self.video_name]  
            video_data.steps.insert(self.step_index, self.deleted_step)  
        self._update_ui()  
      
    def _update_ui(self):      
        if self.main_window:  
            self.main_window.update_display()  
  
        # 新しいアーキテクチャではEditWidgetManagerを使用  
        if hasattr(self.main_window, 'edit_widget_manager'):  
            # 全体のUIを更新  
            self.main_window.edit_widget_manager.refresh_ui()
  
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

        # 新しいアーキテクチャではEditWidgetManagerを使用  
        if hasattr(self.main_window, 'edit_widget_manager'):  
            # 全体のUIを更新  
            self.main_window.edit_widget_manager.refresh_ui()

            # 選択状態を復元  
            step_editor = self.main_window.edit_widget_manager.get_step_editor()  
            step_editor.select_step(  
                step_text=self.new_text, step_index=None
            )