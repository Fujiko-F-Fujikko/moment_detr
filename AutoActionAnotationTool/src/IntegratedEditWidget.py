# IntegratedEditWidget.py  
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,   
                            QComboBox, QLineEdit, QPushButton, QGroupBox,  
                            QListWidget, QListWidgetItem, QDoubleSpinBox,  
                            QTabWidget, QMessageBox)  
from PyQt6.QtCore import pyqtSignal  

from Results import QueryResults, DetectionInterval  
from UndoCommand import IntervalModifyCommand
  
class IntegratedEditWidget(QWidget):  
    dataChanged = pyqtSignal()  
    intervalUpdated = pyqtSignal()  
    intervalDeleted = pyqtSignal()  
    intervalAdded = pyqtSignal()  
      
    def __init__(self):  
        super().__init__()  
        self.current_query_result = None  
        self.selected_interval = None  
        self.selected_interval_index = -1  
        self.stt_data_manager = None  
        self.current_video_name = None  
        self.setup_ui()  
      
    def setup_ui(self):  
        layout = QVBoxLayout()  
          
        # タブウィジェット  
        self.tab_widget = QTabWidget()  
          
        # Action編集タブ  
        self.action_tab = self.create_action_edit_tab()  
        self.tab_widget.addTab(self.action_tab, "Action Edit")  
          
        # Step編集タブ  
        self.step_tab = self.create_step_edit_tab()  
        self.tab_widget.addTab(self.step_tab, "Step Edit")  
          
        layout.addWidget(self.tab_widget)  
        self.setLayout(layout)  
      
    def create_action_edit_tab(self):  
        widget = QWidget()  
        layout = QVBoxLayout()  
          
        # 区間編集グループ  
        interval_group = QGroupBox("Edit Selected Interval")  
        interval_layout = QVBoxLayout()  
          
        # 開始・終了時間  
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
          
        # アクション詳細編集  
        action_detail_layout = QVBoxLayout()  
          
        # 手の種類  
        hand_layout = QHBoxLayout()  
        self.hand_combo = QComboBox()  
        self.hand_combo.addItems(["left_hand", "right_hand", "both_hands", "unspecified"])  
        hand_layout.addWidget(QLabel("Hand:"))  
        hand_layout.addWidget(self.hand_combo)  
        action_detail_layout.addLayout(hand_layout)  
          
        # アクション要素  
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
          
        # ボタン  
        button_layout = QHBoxLayout()  
        self.apply_button = QPushButton("Apply Changes")  
        self.delete_button = QPushButton("Delete Interval")  
        self.add_button = QPushButton("Add New Interval")  
          
        self.apply_button.clicked.connect(self.apply_interval_changes)  
        self.delete_button.clicked.connect(self.delete_interval)  
        self.add_button.clicked.connect(self.add_new_interval)  
          
        button_layout.addWidget(self.apply_button)  
        button_layout.addWidget(self.delete_button)  
        button_layout.addWidget(self.add_button)  
        interval_layout.addLayout(button_layout)  
          
        interval_group.setLayout(interval_layout)  
        layout.addWidget(interval_group)  
          
        widget.setLayout(layout)  
        return widget  
      
    def create_step_edit_tab(self):  
        widget = QWidget()  
        layout = QVBoxLayout()  
          
        # ステップ追加  
        add_layout = QHBoxLayout()  
        self.step_text_edit = QLineEdit()  
        self.step_text_edit.setPlaceholderText("Enter step description...")  
        self.add_step_btn = QPushButton("Add Step")  
        self.add_step_btn.clicked.connect(self.add_step)  
          
        add_layout.addWidget(QLabel("Step:"))  
        add_layout.addWidget(self.step_text_edit)  
        add_layout.addWidget(self.add_step_btn)  
        layout.addLayout(add_layout)  
          
        # ステップリスト  
        self.step_list = QListWidget()  
        self.step_list.itemClicked.connect(self.on_step_selected)  
        layout.addWidget(QLabel("Steps:"))  
        layout.addWidget(self.step_list)  
          
        # ステップ編集  
        edit_group = QGroupBox("Edit Selected Step")  
        edit_layout = QVBoxLayout()  
          
        self.step_edit_text = QLineEdit()  
        edit_layout.addWidget(QLabel("Step Description:"))  
        edit_layout.addWidget(self.step_edit_text)  
          
        # セグメント編集  
        segment_layout = QHBoxLayout()  
        self.step_start_spin = QDoubleSpinBox()  
        self.step_start_spin.setDecimals(2)  
        self.step_start_spin.setMaximum(9999.99)  
        self.step_end_spin = QDoubleSpinBox()  
        self.step_end_spin.setDecimals(2)  
        self.step_end_spin.setMaximum(9999.99)  
          
        segment_layout.addWidget(QLabel("Start:"))  
        segment_layout.addWidget(self.step_start_spin)  
        segment_layout.addWidget(QLabel("End:"))  
        segment_layout.addWidget(self.step_end_spin)  
        edit_layout.addLayout(segment_layout)  
          
        # ボタン  
        button_layout = QHBoxLayout()  
        self.apply_step_btn = QPushButton("Apply Changes")  
        self.apply_step_btn.clicked.connect(self.apply_step_changes)  
        self.delete_step_btn = QPushButton("Delete Step")  
        self.delete_step_btn.clicked.connect(self.delete_step)  
          
        button_layout.addWidget(self.apply_step_btn)  
        button_layout.addWidget(self.delete_step_btn)  
        edit_layout.addLayout(button_layout)  
          
        edit_group.setLayout(edit_layout)  
        layout.addWidget(edit_group)  
          
        widget.setLayout(layout)  
        return widget  
      
    def set_stt_data_manager(self, manager):  
        """STTDataManagerを設定"""  
        self.stt_data_manager = manager  
      
    def set_current_video(self, video_name: str):  
        """現在の動画を設定"""  
        self.current_video_name = video_name  
        self.refresh_step_list()  
      
    def set_current_query_results(self, query_result: QueryResults):  
        """現在のクエリ結果を設定"""  
        self.current_query_result = query_result  
        self.clear_selection()  
      
    def set_selected_interval(self, interval: DetectionInterval, index: int):  
        """選択された区間を設定"""  
        self.selected_interval = interval  
        self.selected_interval_index = index  
        self.update_interval_ui()  
      
    def clear_selection(self):  
        """選択をクリア"""  
        self.selected_interval = None  
        self.selected_interval_index = -1  
        self.update_interval_ui()  
      
    def update_interval_ui(self):  
        """区間編集UIを更新"""  
        if self.selected_interval:  
            self.start_spinbox.setValue(self.selected_interval.start_time)  
            self.end_spinbox.setValue(self.selected_interval.end_time)  
            self.confidence_label.setText(f"Confidence: {self.selected_interval.confidence_score:.3f}")  
              
            # クエリから手の種類とアクション要素を推定  
            if self.current_query_result:  
                try:  
                    from STTDataStructures import QueryParser  
                    hand_type, action_data = QueryParser.validate_and_parse_query(self.current_query_result.query_text)  
                      
                    # 手の種類を設定  
                    hand_mapping = {"LeftHand": "left_hand", "RightHand": "right_hand", "BothHands": "both_hands", "None": "unspecified"}  
                    self.hand_combo.setCurrentText(hand_mapping.get(hand_type, "unspecified"))  
                      
                    # アクション要素を設定  
                    self.action_verb_edit.setText(action_data.action_verb or "")  
                    self.manipulated_object_edit.setText(action_data.manipulated_object or "")  
                    self.target_object_edit.setText(action_data.target_object or "")  
                    self.tool_edit.setText(action_data.tool or "")  
                except:  
                    pass  
        else:  
            self.start_spinbox.setValue(0.0)  
            self.end_spinbox.setValue(0.0)  
            self.confidence_label.setText("Confidence: N/A")  
            self.action_verb_edit.clear()  
            self.manipulated_object_edit.clear()  
            self.target_object_edit.clear()  
            self.tool_edit.clear()  
      
    def apply_interval_changes(self):  
        """区間変更を適用"""  
        if not self.selected_interval or not self.current_query_result:  
            return  
          
        old_start = self.selected_interval.start_time  
        old_end = self.selected_interval.end_time  
        new_start = self.start_spinbox.value()    
        new_end = self.end_spinbox.value()  
        
        # MainApplicationWindowのundo_stackにアクセス  
        main_window = self.get_main_window()  
        if main_window:  
            command = IntervalModifyCommand(self.selected_interval, old_start, old_end, new_start, new_end)  
            main_window.undo_stack.push(command)  

        # 区間の時間を更新  
        self.selected_interval.start_time = self.start_spinbox.value()  
        self.selected_interval.end_time = self.end_spinbox.value()  
          
        self.intervalUpdated.emit()  
        self.dataChanged.emit()  

    def delete_interval(self):  
        """区間を削除"""  
        if not self.selected_interval or not self.current_query_result:  
            return  
          
        # 区間を削除  
        if self.selected_interval in self.current_query_result.relevant_windows:  
            self.current_query_result.relevant_windows.remove(self.selected_interval)  
          
        self.clear_selection()  
        self.intervalDeleted.emit()  
        self.dataChanged.emit()  
      
    def add_new_interval(self):    
        """新しい区間を追加（選択中の区間の右横に配置）"""    
        if not self.current_query_result:    
            return    
            
        if not self.start_spinbox or not self.end_spinbox:    
            return    
            
        # デフォルトの区間長  
        default_duration = 5.0  
        
        # 現在選択されている区間がある場合は、その終了時刻の直後に配置  
        if self.selected_interval:  
            start_time = self.selected_interval.end_time  
            end_time = start_time + default_duration  
        else:  
            # 選択されている区間がない場合は、既存の区間の最後の後に配置  
            existing_intervals = self.current_query_result.relevant_windows  
            if existing_intervals:  
                # 最も遅い終了時刻を見つける  
                latest_end = max(interval.end_time for interval in existing_intervals)  
                start_time = latest_end  
                end_time = start_time + default_duration  
            else:  
                # 区間が全くない場合は0秒から開始  
                start_time = 0.0  
                end_time = default_duration  
        
        # 動画の長さを超えないように調整（実際の動画長を取得する必要があります）  
        # ここでは仮に60秒としていますが、実際のアプリケーションでは  
        # self.app_controller.video_info.duration などから取得すべきです  
        video_duration = 60.0  # 実際の動画長に置き換える  
        
        if end_time > video_duration:  
            end_time = video_duration  
            start_time = max(0, end_time - default_duration)  
            
        if start_time >= end_time:  
            QMessageBox.warning(None, "Warning", "Cannot add interval: insufficient space!")  
            return  
            
        # 新しい区間を作成  
        from DetectionInterval import DetectionInterval    
        new_interval = DetectionInterval(start_time, end_time, 1.0, len(self.current_query_result.relevant_windows))    
        new_interval.query_result = self.current_query_result    
            
        self.current_query_result.relevant_windows.append(new_interval)  
        
        # UIを更新して新しい区間を選択状態にする  
        self.start_spinbox.setValue(start_time)  
        self.end_spinbox.setValue(end_time)  
        
        self.intervalAdded.emit()    
        self.dataChanged.emit()
      
    def refresh_step_list(self):  
        """ステップリストを更新"""  
        self.step_list.clear()  
        if not self.stt_data_manager or not self.current_video_name:  
            return  
          
        if self.current_video_name in self.stt_data_manager.stt_dataset.database:  
            video_data = self.stt_data_manager.stt_dataset.database[self.current_video_name]  
            for i, step in enumerate(video_data.steps):  
                item = QListWidgetItem(step.step)  
                item.setData(1, i)  
                self.step_list.addItem(item)  
      
    def on_step_selected(self, item):  
        """ステップ選択時の処理"""  
        if not self.stt_data_manager or not self.current_video_name:  
            return  
          
        index = item.data(1)  
        video_data = self.stt_data_manager.stt_dataset.database[self.current_video_name]  
        step = video_data.steps[index]  
          
        self.step_edit_text.setText(step.step)  
        if len(step.segment) >= 2:  
            self.step_start_spin.setValue(step.segment[0])  
            self.step_end_spin.setValue(step.segment[1])  
      
    def add_step(self):  
        """ステップを追加"""  
        step_text = self.step_text_edit.text().strip()  
        if not step_text or not self.stt_data_manager or not self.current_video_name:  
            return  
          
        segment = [0.0, 1.0]  
        self.stt_data_manager.add_step(self.current_video_name, step_text, segment)  
          
        self.step_text_edit.clear()  
        self.refresh_step_list()  
        self.dataChanged.emit()  
      
    def apply_step_changes(self):  
        """ステップ変更を適用"""  
        current_item = self.step_list.currentItem()  
        if not current_item or not self.stt_data_manager or not self.current_video_name:  
            return  
          
        index = current_item.data(1)  
        video_data = self.stt_data_manager.stt_dataset.database[self.current_video_name]  
        step = video_data.steps[index]  
          
        step.step = self.step_edit_text.text()  
        step.segment = [self.step_start_spin.value(), self.step_end_spin.value()]  
        fps = video_data.fps  
        step.segment_frames = [int(step.segment[0] * fps), int(step.segment[1] * fps)]  
          
        self.refresh_step_list()  
        self.dataChanged.emit()  
      
    def delete_step(self):  
        """ステップを削除"""  
        current_item = self.step_list.currentItem()  
        if not current_item or not self.stt_data_manager or not self.current_video_name:  
            return  
          
        index = current_item.data(1)  
        video_data = self.stt_data_manager.stt_dataset.database[self.current_video_name]  
        del video_data.steps[index]  
          
        self.refresh_step_list()  
        self.dataChanged.emit()

    def get_main_window(self):  
        """MainApplicationWindowを取得"""  
        parent = self.parent()  
        while parent:  
            # 文字列ベースの型チェックに変更  
            if parent.__class__.__name__ == 'MainApplicationWindow':  
                return parent  
            parent = parent.parent()  
        return None