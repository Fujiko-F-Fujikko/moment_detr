# EditWidgetManager.py  
from PyQt6.QtWidgets import QWidget, QTabWidget, QVBoxLayout  
from PyQt6.QtCore import pyqtSignal  
from typing import Optional  
  
from ActionEditor import ActionEditor  
from StepEditor import StepEditor  
from EditCommandFactory import EditCommandFactory  
from Results import QueryResults, DetectionInterval  
  
class EditWidgetManager(QWidget):  
    """編集ウィジェットの統合管理を担当するクラス"""  
      
    # 統合シグナル  
    dataChanged = pyqtSignal()  
    intervalUpdated = pyqtSignal()  
    intervalDeleted = pyqtSignal()  
    intervalAdded = pyqtSignal()  
    stepAdded = pyqtSignal()  
    stepModified = pyqtSignal()  
    stepDeleted = pyqtSignal()  
      
    def __init__(self, main_window=None):  
        super().__init__()  
        self.main_window = main_window  
        self.command_factory = EditCommandFactory(main_window) if main_window else None  
          
        # 個別エディター  
        self.action_editor = ActionEditor(main_window)  
        self.step_editor = StepEditor(main_window)  
          
        # UI要素  
        self.tab_widget: Optional[QTabWidget] = None  
          
        self.setup_ui()  
        self.setup_connections()  
      
    def setup_ui(self):  
        """UIレイアウトの設定"""  
        layout = QVBoxLayout()  
          
        # タブウィジェット  
        self.tab_widget = QTabWidget()  
          
        # Action編集タブ  
        self.tab_widget.addTab(self.action_editor, "Action Edit")  
          
        # Step編集タブ  
        self.tab_widget.addTab(self.step_editor, "Step Edit")  
          
        layout.addWidget(self.tab_widget)  
        self.setLayout(layout)  
      
    def setup_connections(self):  
        """シグナル接続の設定"""  
        # ActionEditorのシグナルを転送  
        self.action_editor.intervalUpdated.connect(self.intervalUpdated)  
        self.action_editor.intervalDeleted.connect(self.intervalDeleted)  
        self.action_editor.intervalAdded.connect(self.intervalAdded)  
        self.action_editor.dataChanged.connect(self.dataChanged)  
          
        # StepEditorのシグナルを転送  
        self.step_editor.stepAdded.connect(self.stepAdded)  
        self.step_editor.stepModified.connect(self.stepModified)  
        self.step_editor.stepDeleted.connect(self.stepDeleted)  
        self.step_editor.dataChanged.connect(self.dataChanged)  
      
    def set_stt_data_manager(self, manager):  
        """STTDataManagerを設定"""  
        self.step_editor.set_stt_data_manager(manager)  
      
    def set_current_video(self, video_name: str):  
        """現在の動画を設定"""  
        self.step_editor.set_current_video(video_name)  
      
    def set_current_query_results(self, query_result: QueryResults):  
        """現在のクエリ結果を設定"""  
        # StepEditorにも情報を設定（Step関連の場合）  
        if query_result and query_result.query_text.startswith("Step:"):  
            # StepEditorに必要な情報を設定  
            self.step_editor.set_current_query_results(query_result)  
        else:
            # ActionEditorに必要な情報を設定  
            self.action_editor.set_current_query_results(query_result)

        # ステップクエリの場合はStep編集タブに切り替え  
        if query_result and query_result.query_text.startswith("Step:"):  
            self.tab_widget.setCurrentIndex(1)  # Step Edit tab  
        else:  
            self.tab_widget.setCurrentIndex(0)  # Action Edit tab  
      
    def set_selected_interval(self, interval: DetectionInterval, index: int):  
        """選択された区間を設定"""  
        # ActionEditorに設定  
        self.action_editor.set_selected_interval(interval, index)  
        
        # StepEditorにも情報を渡す（Step区間の場合）  
        if hasattr(interval, 'query_result') and interval.query_result:  
            if interval.query_result.query_text.startswith("Step:"):  
                # Step区間の場合、StepEditorで該当ステップを選択  
                if hasattr(interval, 'label') and interval.label:  
                    self.step_editor.select_step(step_text=interval.label)
                    
        # 区間の種類に応じて適切なタブに切り替え  
        self.switch_to_appropriate_tab(interval)
      
    def switch_to_appropriate_tab(self, interval: DetectionInterval):  
        """区間の種類に応じて適切なタブに切り替える"""  
        if hasattr(interval, 'query_result') and interval.query_result:  
            query_text = interval.query_result.query_text  
              
            # Stepの区間かどうかを判定  
            if query_text.startswith("Step:"):  
                # Step Editタブに切り替え  
                self.tab_widget.setCurrentIndex(1)  
                # クリックされたステップを選択状態にする  
                if hasattr(interval, 'label'):  
                    self.step_editor.select_step(step_text=interval.label)  
            else:  
                # Action Editタブに切り替え  
                self.tab_widget.setCurrentIndex(0)  
      
    def clear_selection(self):  
        """選択をクリア"""  
        self.action_editor.clear_selection()  
      
    def get_command_factory(self) -> Optional[EditCommandFactory]:  
        """コマンドファクトリーを取得"""  
        return self.command_factory  
      
    def get_current_tab_index(self) -> int:  
        """現在のタブインデックスを取得"""  
        return self.tab_widget.currentIndex() if self.tab_widget else 0  
      
    def set_current_tab_index(self, index: int):  
        """現在のタブインデックスを設定"""  
        if self.tab_widget and 0 <= index < self.tab_widget.count():  
            self.tab_widget.setCurrentIndex(index)  
     
    def get_action_editor(self):  
        """ActionEditorを取得"""  
        if hasattr(self, 'action_editor'):  
            return self.action_editor  
        return None  
      
    def get_step_editor(self):  
        """StepEditorを取得"""  
        if hasattr(self, 'step_editor'):  
            return self.step_editor  
        return None  
      
    def refresh_ui(self):  
        """全体のUIを更新"""  
        # ActionEditorの更新  
        action_editor = self.get_action_editor()  
        if action_editor:  
            action_editor.update_interval_ui()  
          
        # StepEditorの更新  
        step_editor = self.get_step_editor()  
        if step_editor:  
            step_editor.refresh_step_list()  
            step_editor._update_step_edit_ui()
          
        # その他のUI更新処理  
        self.update()  
      
    def update_display(self):  
        """表示を更新（MainApplicationWindowから呼び出される）"""  
        self.refresh_ui()

    def get_current_state(self) -> dict:  
        """現在の編集状態を取得（デバッグ用）"""  
        return {  
            'current_tab': self.get_current_tab_index(),  
            'action_editor_state': self.action_editor.get_current_state(),  
            'step_editor_state': self.step_editor.get_current_state(),  
            'has_command_factory': self.command_factory is not None  
        }

    def handle_step_selection_from_editor(self, step_text: str, start_time: float, end_time: float):  
        """StepEditorからのStep選択を処理"""  
        if self.main_window and hasattr(self.main_window, 'application_coordinator'):  
            app_coordinator = self.main_window.application_coordinator  
            timeline_manager = app_coordinator.timeline_display_manager  
            
            # StepsタイムラインのTimelineDataを取得  
            steps_timeline_widget = timeline_manager.get_timeline_by_type("Steps")  
            if steps_timeline_widget and hasattr(steps_timeline_widget, 'timeline_data'):  
                timeline_data = steps_timeline_widget.timeline_data  
                
                # 該当するDetectionIntervalを検索  
                found_interval = None  
                for interval in timeline_data.intervals:  
                    if (interval.label == step_text and   
                        interval.start_time == start_time and   
                        interval.end_time == end_time):  
                        found_interval = interval  
                        break  
                
                if found_interval:  
                    app_coordinator.handle_timeline_interval_clicked(  
                        found_interval, found_interval.query_result  
                    )