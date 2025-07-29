# ActionEditor.py    
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,    
                            QComboBox, QLineEdit, QPushButton, QGroupBox,    
                            QDoubleSpinBox, QMessageBox)    
from PyQt6.QtCore import pyqtSignal, QTimer, Qt    
from typing import Optional    
    
from ResultsDataController import ResultsDataController  
from DataClasses import QueryResults, DetectionInterval, QueryParser  
from EditCommandFactory import EditCommandFactory    
from Utilities import show_call_stack  # デバッグ用スタックトレース表示  
  
class ActionEditor(QWidget):    
    """アクション編集に特化したエディタークラス"""    
        
    # シグナル定義    
    intervalUpdated = pyqtSignal()    
    intervalDeleted = pyqtSignal()    
    intervalAdded = pyqtSignal()    
    dataChanged = pyqtSignal()    
        
    def __init__(self, main_window=None):    
        super().__init__()    
        self.main_window = main_window    
        self.command_factory = EditCommandFactory(main_window) if main_window else None  
        self.results_data_controller = None  # ResultsDataControllerへの参照  
        self.selected_interval: Optional[DetectionInterval] = None    
        self.selected_interval_index: int = -1    
            
        # タイマー（連続入力防止用）    
        self._action_timer: Optional[QTimer] = None    
            
        # 初期化状態フラグ    
        self._is_initializing = True    
        self._signals_connected = False    
        # 編集状態フラグ  
        self._editing_in_progress = False  
  
        # UIを構築    
        self._build_ui()    
            
        # 初期化完了    
        self._is_initializing = False    
        
    def _build_ui(self):    
        """UI全体を構築"""    
        layout = QVBoxLayout()    
            
        # 区間編集グループ    
        interval_group = QGroupBox("Edit Selected Interval")    
        interval_layout = QVBoxLayout()    
            
        # 時間編集セクション    
        time_layout = QHBoxLayout()    
            
        self.start_spinbox = QDoubleSpinBox()    
        self.start_spinbox.setDecimals(2)    
        self.start_spinbox.setMaximum(9999.99)    
            
        self.end_spinbox = QDoubleSpinBox()    
        self.end_spinbox.setDecimals(2)    
        self.end_spinbox.setMaximum(9999.99)    
            
        time_layout.addWidget(QLabel("Start:"))    
        time_layout.addWidget(self.start_spinbox)    
        time_layout.addWidget(QLabel("End:"))    
        time_layout.addWidget(self.end_spinbox)    
            
        interval_layout.addLayout(time_layout)    
            
        # 信頼度表示    
        self.confidence_label = QLabel("Confidence: N/A")    
        interval_layout.addWidget(self.confidence_label)    
            
        # アクション詳細編集セクション    
        action_detail_layout = QVBoxLayout()    
            
        # 手の種類選択    
        hand_layout = QHBoxLayout()    
        self.hand_combo = QComboBox()    
        self.hand_combo.addItems(["left_hand", "right_hand", "both_hands", "unspecified"])    
        hand_layout.addWidget(QLabel("Hand:"))    
        hand_layout.addWidget(self.hand_combo)    
        action_detail_layout.addLayout(hand_layout)    
            
        # アクション要素編集フィールド    
        self.action_verb_edit = QLineEdit()    
        self.manipulated_object_edit = QLineEdit()    
        self.target_object_edit = QLineEdit()    
        self.tool_edit = QLineEdit()    
            
        action_detail_layout.addWidget(QLabel("Action Verb:"))    
        action_detail_layout.addWidget(self.action_verb_edit)    
        action_detail_layout.addWidget(QLabel("Manipulated Object:"))    
        action_detail_layout.addWidget(self.manipulated_object_edit)    
        action_detail_layout.addWidget(QLabel("Target Object:"))    
        action_detail_layout.addWidget(self.target_object_edit)    
        action_detail_layout.addWidget(QLabel("Tool:"))    
        action_detail_layout.addWidget(self.tool_edit)    
            
        interval_layout.addLayout(action_detail_layout)    
            
        # ボタンセクション    
        button_layout = QHBoxLayout()    
        self.add_button = QPushButton("Add New Interval")    
        self.delete_button = QPushButton("Delete Interval")    
        button_layout.addWidget(self.add_button)    
        button_layout.addWidget(self.delete_button)    
        interval_layout.addLayout(button_layout)    
            
        interval_group.setLayout(interval_layout)    
        layout.addWidget(interval_group)    
        self.setLayout(layout)    
            
        # シグナル接続（UI構築後に実行）    
        self._connect_signals()    
        
    def _connect_signals(self):    
        """シグナル接続を設定"""    
        if self._signals_connected:    
            return    
            
        try:    
            # 即時反映のためのシグナル接続    
            self.start_spinbox.valueChanged.connect(self.on_action_value_changed)    
            self.end_spinbox.valueChanged.connect(self.on_action_value_changed)    
            self.hand_combo.currentTextChanged.connect(self.on_action_value_changed)    
            self.action_verb_edit.textChanged.connect(self.on_action_value_changed)    
            self.manipulated_object_edit.textChanged.connect(self.on_action_value_changed)    
            self.target_object_edit.textChanged.connect(self.on_action_value_changed)    
            self.tool_edit.textChanged.connect(self.on_action_value_changed)    
                
            # ボタンクリック    
            # 修正：ラムダ関数を使用して引数なしで呼び出し  
            self.add_button.clicked.connect(lambda: self.add_new_interval())    
            self.delete_button.clicked.connect(self.delete_interval)    
                
            self._signals_connected = True    
        except Exception as e:    
            print(f"Error connecting signals: {e}")    
        
    def set_results_data_controller(self, controller: ResultsDataController):    
        """ResultsDataControllerを設定"""    
        self.results_data_controller = controller   
  
    def get_current_query_result(self) -> Optional[QueryResults]:    
        """現在のQueryResultを取得（ResultsDataControllerから）"""    
        if not self.results_data_controller:    
            return None    
        filtered_results = self.results_data_controller.get_filtered_results()    
        # 現在選択されているintervalに基づいて適切なQueryResultを返す    
        if self.selected_interval and hasattr(self.selected_interval, 'query_result'):    
            return self.selected_interval.query_result    
        return filtered_results[0] if filtered_results else None  
  
    def set_current_query_results(self, query_result: QueryResults):    
        """現在のクエリ結果を設定"""    
        if self._is_initializing:    
            return    
          
        # 重要：同じQueryResultで既に編集中の場合は上書きしない    
        current_query_result = self.get_current_query_result()  # 修正箇所  
        if (current_query_result and     
            current_query_result == query_result and    
            hasattr(self, '_editing_in_progress') and self._editing_in_progress):    
            return    
          
        self.clear_selection()  
        
    def set_selected_interval(self, interval: DetectionInterval, index: int):    
        """選択された区間を設定"""    
        if self._is_initializing:    
            return    
            
        self.selected_interval = interval    
        self.selected_interval_index = index    
        # デバッグ情報を追加    
  
        #show_call_stack()  
        self.update_interval_ui()    
        
    def clear_selection(self):    
        """選択をクリア"""    
        if self._is_initializing:    
            return    
            
        self.selected_interval = None    
        self.selected_interval_index = -1    
        self.update_interval_ui()    
        
    def update_interval_ui(self):    
        """区間編集UIを更新"""    
        if self._is_initializing:    
            return    
            
        if self.selected_interval:    
            self._update_ui_with_interval_data()    
        else:    
            self._clear_ui_fields()    
        
    def _update_ui_with_interval_data(self):    
        """区間データでUIを更新"""    
        if self._is_initializing:    
            return    
            
        # シグナルを一時的に無効化    
        self._block_signals(True)    
            
        try:    
            # 時間情報を設定    
            self.start_spinbox.setValue(self.selected_interval.start_time)    
            self.end_spinbox.setValue(self.selected_interval.end_time)    
            self.confidence_label.setText(f"Confidence: {self.selected_interval.confidence_score:.3f}")    
                
            # Stepクエリの場合はアクション編集フィールドの更新をスキップ    
            current_query_result = self.get_current_query_result()  # 修正箇所  
            if current_query_result and not current_query_result.query_text.startswith("Step:"):    
                self._update_action_fields()    
            
        finally:    
            # シグナルを再有効化    
            self._block_signals(False)    
        
    def _update_action_fields(self):    
        """アクション編集フィールドを更新"""    
        if self._is_initializing:    
            return    
            
        try:    
            current_query_result = self.get_current_query_result()  # 修正箇所  
            if not current_query_result:  
                return  
                  
            hand_type, action_data = QueryParser.validate_and_parse_query(current_query_result.query_text)    
                
            # 手の種類を設定    
            hand_mapping = {    
                "LeftHand": "left_hand",     
                "RightHand": "right_hand",     
                "BothHands": "both_hands",     
                "None": "unspecified"    
            }    
            self.hand_combo.setCurrentText(hand_mapping.get(hand_type, "unspecified"))    
                
            # アクション要素を設定    
            self.action_verb_edit.setText(action_data.action_verb or "")    
            self.manipulated_object_edit.setText(action_data.manipulated_object or "")    
            self.target_object_edit.setText(action_data.target_object or "")    
            self.tool_edit.setText(action_data.tool or "")    
        except:    
            pass    
        
    def _clear_ui_fields(self):    
        """UIフィールドをクリア"""    
        if self._is_initializing:    
            return    
            
        # シグナルを一時的に無効化    
        self._block_signals(True)    
            
        try:    
            self.start_spinbox.setValue(0.0)    
            self.end_spinbox.setValue(0.0)    
            self.confidence_label.setText("Confidence: N/A")    
            self.action_verb_edit.clear()    
            self.manipulated_object_edit.clear()    
            self.target_object_edit.clear()    
            self.tool_edit.clear()    
            
        finally:    
            # シグナルを再有効化    
            self._block_signals(False)    
        
    def _block_signals(self, block: bool):    
        """シグナルのブロック/アンブロック"""    
        if self._is_initializing or not self._signals_connected:    
            return    
            
        widgets = [    
            self.start_spinbox, self.end_spinbox, self.hand_combo,    
            self.action_verb_edit, self.manipulated_object_edit,    
            self.target_object_edit, self.tool_edit    
        ]    
            
        for widget in widgets:    
            try:    
                widget.blockSignals(block)    
            except:    
                continue    
        
    def on_action_value_changed(self):    
        """アクション値が変更された時の即時処理"""    
        if self._is_initializing:    
            return    
            
        # 編集中フラグを設定    
        self._editing_in_progress = True    
  
        # 連続入力を防ぐため遅延処理    
        if self._action_timer and self._action_timer.isActive():    
            self._action_timer.stop()    
            
        self._action_timer = QTimer()    
        self._action_timer.setSingleShot(True)    
        self._action_timer.timeout.connect(self.apply_action_changes)    
        self._action_timer.start(500)  # 500ms後に適用    
        
    def apply_action_changes(self):    
        """区間変更を適用"""    
        current_query_result = self.get_current_query_result()  # 修正箇所  
        if (self._is_initializing or not self.selected_interval or     
            not current_query_result or not self.command_factory):    
            return    
            
        # Stepクエリの場合は何もしない    
        if current_query_result.query_text.startswith("Step:"):    
            return    
            
        # 変更内容を取得    
        old_start = self.selected_interval.start_time    
        old_end = self.selected_interval.end_time    
        new_start = self.start_spinbox.value()    
        new_end = self.end_spinbox.value()    
            
        old_query_text = current_query_result.query_text    
        new_query_text = self._build_new_query_text()    
            
        # 実際に変更があるかチェック    
        time_changed = (abs(old_start - new_start) > 0.01 or abs(old_end - new_end) > 0.01)    
        query_changed = (old_query_text != new_query_text)    
            
        if not time_changed and not query_changed:    
            return    
            
        # ファクトリーを使用してコマンドを作成・実行    
        if time_changed:    
            self.command_factory.create_and_execute_interval_modify(    
                self.selected_interval, old_start, old_end, new_start, new_end    
            )    
            
        if query_changed:    
            self.command_factory.create_and_execute_action_modify(    
                current_query_result, old_query_text, new_query_text  # 修正箇所  
            )    
            
        # コマンド実行後、UIを即座に更新（古い実装と同様）    
        self.update_interval_ui()   
  
        # シグナル発信    
        self.intervalUpdated.emit()    
        self.dataChanged.emit()    
  
        # Timeline同期を実行  
        self.main_window.application_coordinator.synchronize_timeline_updates()  
  
    def _build_new_query_text(self) -> str:    
        """入力フィールドから新しいクエリテキストを構築"""    
        hand_mapping = {    
            "left_hand": "LeftHand",     
            "right_hand": "RightHand",     
            "both_hands": "BothHands",     
            "unspecified": "None"    
        }    
        hand_type = hand_mapping.get(self.hand_combo.currentText(), "None")    
            
        action_verb = self.action_verb_edit.text().strip() or "None"    
        manipulated_object = self.manipulated_object_edit.text().strip() or "None"    
        target_object = self.target_object_edit.text().strip() or "None"    
        tool = self.tool_edit.text().strip() or "None"    
            
        return f"{hand_type}_{action_verb}_{manipulated_object}_{target_object}_{tool}"    
      
    def delete_interval(self):  
        """区間を削除"""  
        current_query_result = self.get_current_query_result()  
        if (self._is_initializing or not self.selected_interval or   
            not current_query_result or not self.command_factory):  
            print("DEBUG: Early return due to missing conditions")  
            return  
          
        # interval_idまたは時間範囲で一致する区間を検索  
        index = -1  
        for i, interval in enumerate(current_query_result.relevant_windows):  
            # interval_idが存在する場合はそれで比較  
            if (hasattr(self.selected_interval, 'interval_id') and   
                hasattr(interval, 'interval_id') and  
                self.selected_interval.interval_id == interval.interval_id):  
                index = i  
                break  
            # interval_idがない場合は時間範囲で比較  
            elif (abs(interval.start_time - self.selected_interval.start_time) < 0.01 and  
                  abs(interval.end_time - self.selected_interval.end_time) < 0.01):  
                index = i  
                break  
          
        if index == -1:  
            print("DEBUG: Selected interval not found in current query result")  
            return  
          
        # 実際のリスト内のオブジェクトを使用  
        actual_interval = current_query_result.relevant_windows[index]  
          
        self.command_factory.create_and_execute_interval_delete(  
            current_query_result, actual_interval, index  
        )  
          
        # シグナル発信  
        self.intervalDeleted.emit()  
        self.dataChanged.emit()
    
    def add_new_interval(self, query_result: Optional[QueryResults] = None, start_time: Optional[float] = None, end_time: Optional[float] = None):    
        """修正版：ResultsDataControllerを使用"""    
        if self._is_initializing or not self.command_factory or not self.results_data_controller:    
            return    
                
        if query_result is None:    
            current_query_result = self.get_current_query_result()    
            if not current_query_result:    
                return    
                
            import copy    
            query_result = copy.deepcopy(current_query_result)    
            query_result.relevant_windows = []    
            
        # 時間計算ロジック（既存と同じ）    
        if start_time is not None and end_time is not None:    
            calculated_start = start_time    
            calculated_end = end_time    
        else:    
            # デフォルト時間計算    
            default_duration = 1.0    
            current_query_result = self.get_current_query_result()    
                
            if self.selected_interval:    
                calculated_start = self.selected_interval.end_time    
                calculated_end = calculated_start + default_duration    
            else:    
                existing_intervals = current_query_result.relevant_windows if current_query_result else []    
                if existing_intervals:    
                    latest_end = max(interval.end_time for interval in existing_intervals)    
                    calculated_start = latest_end    
                    calculated_end = calculated_start + default_duration    
                else:    
                    calculated_start = 0.0    
                    calculated_end = default_duration    
            
        # 動画長さ調整（既存と同じ）    
        video_duration = self._get_video_duration()    
        if calculated_end > video_duration:    
            calculated_end = video_duration    
            calculated_start = max(0, calculated_end - (calculated_end - calculated_start))    
                
        if calculated_start >= calculated_end:    
            QMessageBox.warning(None, "Warning", "Cannot add interval: insufficient space!")    
            return    
            
        # 新しい区間を作成
        print(f"new_interval: {query_result}, type: {type(query_result)}")
        new_interval = DetectionInterval(calculated_start, calculated_end, 1.0, 0, query_type="action")    
        new_interval.query_result = query_result    
            
        # ResultsDataControllerに追加    
        self.results_data_controller.add_query_result(query_result)    
        
        self.command_factory.create_and_execute_interval_add(query_result, new_interval)    
            
        self.intervalAdded.emit()    
        self.dataChanged.emit()  
  
    
    def _get_video_duration(self) -> float:    
        """動画の長さを取得"""    
        if self.main_window and hasattr(self.main_window, 'video_controller'):    
            return self.main_window.video_controller.get_duration_seconds()    
        return 60.0  # デフォルト値    
        
    def is_step_query(self) -> bool:    
        """現在のクエリがステップクエリかどうかを判定"""    
        current_query_result = self.get_current_query_result()  # 修正箇所  
        return (current_query_result and     
                current_query_result.query_text.startswith("Step:"))    
        
    def get_current_state(self) -> dict:    
        """現在の編集状態を取得（デバッグ用）"""    
        current_query_result = self.get_current_query_result()  # 修正箇所  
        return {    
            'has_query_result': current_query_result is not None,    
            'has_selected_interval': self.selected_interval is not None,    
            'selected_interval_index': self.selected_interval_index,    
            'is_step_query': self.is_step_query(),    
            'is_initializing': self._is_initializing    
        }
