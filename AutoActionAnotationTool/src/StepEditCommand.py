# StepEditCommand.py (修正版)  
from PyQt6.QtGui import QUndoCommand  
  
class StepEditCommand(QUndoCommand):  
    def __init__(self, interval, old_start, old_end, new_start, new_end,   
                 stt_data_controller, video_name, main_window, description="Modify Step"):  
        super().__init__(description)  
        self.interval = interval  
        self.old_start = old_start  
        self.old_end = old_end  
        self.new_start = new_start  
        self.new_end = new_end  
        self.stt_data_controller = stt_data_controller  
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
            self.video_name in self.stt_data_controller.stt_dataset.database):  
            video_data = self.stt_data_controller.stt_dataset.database[self.video_name]  
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

            # 選択状態を復元  
            self.main_window.edit_widget_manager.set_selected_interval(self.interval)  


class StepAddCommand(QUndoCommand):    
    def __init__(self, stt_data_controller, video_name, step_text, segment, main_window, description="Add Step"):    
        super().__init__(description)    
        self.stt_data_controller = stt_data_controller    
        self.video_name = video_name    
        self.step_text = step_text    
        self.segment = segment    
        self.main_window = main_window    
        self.step_index = None  # 追加されたステップのインデックスを保存  
            
    def redo(self):    
        # STTDataControllerのadd_stepメソッドを使用  
        success = self.stt_data_controller.add_step(self.video_name, self.step_text, self.segment)    
        if success:    
            # 追加されたステップのインデックスを保存（最後に追加されたもの）  
            if self.video_name in self.stt_data_controller.stt_dataset.database:  
                video_data = self.stt_data_controller.stt_dataset.database[self.video_name]  
                self.step_index = len(video_data.steps) - 1  
        self._update_ui()    
            
    def undo(self):    
        # STTDataControllerのdelete_stepメソッドを使用  
        if self.step_index is not None:  
            self.stt_data_controller.delete_step(self.video_name, self.step_index)  
        self._update_ui()    
        
    def _update_ui(self):        
        if self.main_window:    
            self.main_window.update_display()    
  
        # 新しいアーキテクチャではEditWidgetManagerを使用    
        if hasattr(self.main_window, 'edit_widget_manager'):    
            # 全体のUIを更新    
            self.main_window.edit_widget_manager.refresh_ui()  
  
            # 選択状態を復元（redoの場合のみ）  
            if self.step_index is not None:  
                step_editor = self.main_window.edit_widget_manager.get_step_editor()    
                step_editor.select_step(    
                    step_text=self.step_text, step_index=None  
                )  
  
  
class StepDeleteCommand(QUndoCommand):    
    def __init__(self, stt_data_controller, video_name, step_index, main_window, description="Delete Step"):    
        super().__init__(description)    
        self.stt_data_controller = stt_data_controller    
        self.video_name = video_name    
        self.step_index = step_index    
        self.main_window = main_window    
        self.deleted_step_text = None  
        self.deleted_step_segment = None  
        self.is_undo_operation = False  # undo操作かどうかを追跡  
            
    def redo(self):    
        # 削除前にステップ情報を保存  
        if self.video_name in self.stt_data_controller.stt_dataset.database:    
            video_data = self.stt_data_controller.stt_dataset.database[self.video_name]    
            if self.step_index < len(video_data.steps):    
                deleted_step = video_data.steps[self.step_index]  
                self.deleted_step_text = deleted_step.step  
                self.deleted_step_segment = deleted_step.segment.copy()  
          
        # STTDataControllerのdelete_stepメソッドを使用  
        self.stt_data_controller.delete_step(self.video_name, self.step_index)  
        self.is_undo_operation = False  
        self._update_ui()    
            
    def undo(self):    
        # STTDataControllerのadd_stepメソッドを使用して復元  
        if self.deleted_step_text and self.deleted_step_segment:  
            # 元の位置に挿入するため、一時的に追加してから移動  
            success = self.stt_data_controller.add_step(  
                self.video_name,   
                self.deleted_step_text,   
                self.deleted_step_segment  
            )  
              
            if success and self.video_name in self.stt_data_controller.stt_dataset.database:  
                video_data = self.stt_data_controller.stt_dataset.database[self.video_name]  
                # 最後に追加されたステップを元の位置に移動  
                if len(video_data.steps) > self.step_index:  
                    restored_step = video_data.steps.pop()  # 最後の要素を取得  
                    video_data.steps.insert(self.step_index, restored_step)  # 元の位置に挿入  
          
        self.is_undo_operation = True  
        self._update_ui()    
        
    def _update_ui(self):        
        if self.main_window:    
            self.main_window.update_display()    
    
        # 新しいアーキテクチャではEditWidgetManagerを使用    
        if hasattr(self.main_window, 'edit_widget_manager'):    
            # 全体のUIを更新    
            self.main_window.edit_widget_manager.refresh_ui()  
              
            # undoの時のみ選択状態を復元  
            if self.is_undo_operation and self.deleted_step_text:  
                step_editor = self.main_window.edit_widget_manager.get_step_editor()    
                step_editor.select_step(    
                    step_text=self.deleted_step_text, step_index=None  
                )  

class StepTextEditCommand(QUndoCommand):  
    def __init__(self, stt_data_controller, video_name, step_index, old_text, new_text, main_window, description="Modify Step Text"):  
        super().__init__(description)  
        self.stt_data_controller = stt_data_controller  
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
        # STTDataControllerのmodify_stepメソッドを使用  
        self.stt_data_controller.modify_step(  
            self.video_name,   
            self.step_index,   
            new_text=text  
        )
      
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