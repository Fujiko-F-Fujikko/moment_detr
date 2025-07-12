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
        self.action_editor.set_current_query_results(query_result)  
          
        # ステップクエリの場合はStep編集タブに切り替え  
        if query_result and query_result.query_text.startswith("Step:"):  
            self.tab_widget.setCurrentIndex(1)  # Step Edit tab  
        else:  
            self.tab_widget.setCurrentIndex(0)  # Action Edit tab  
      
    def set_selected_interval(self, interval: DetectionInterval, index: int):  
        """選択された区間を設定"""  
        self.action_editor.set_selected_interval(interval, index)  
          
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
                    self.step_editor.select_step_by_label(interval.label)  
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
      
    def get_action_editor(self) -> ActionEditor:  
        """ActionEditorを取得"""  
        return self.action_editor  
      
    def get_step_editor(self) -> StepEditor:  
        """StepEditorを取得"""  
        return self.step_editor  
      
    def refresh_ui(self):  
        """UI全体を更新"""  
        # ステップリストを更新  
        self.step_editor.refresh_step_list()  
          
        # アクション編集UIを更新  
        self.action_editor.update_interval_ui()  
      
    def get_current_state(self) -> dict:  
        """現在の編集状態を取得（デバッグ用）"""  
        return {  
            'current_tab': self.get_current_tab_index(),  
            'action_editor_state': self.action_editor.get_current_state(),  
            'step_editor_state': self.step_editor.get_current_state(),  
            'has_command_factory': self.command_factory is not None  
        }