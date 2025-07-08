from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,   
                            QComboBox, QLineEdit, QPushButton, QGroupBox,  
                            QListWidget, QListWidgetItem, QDoubleSpinBox,  
                            QTextEdit, QTabWidget)  
from PyQt6.QtCore import pyqtSignal  
from STTDataStructures import ActionEntry, StepEntry  
  
class STTEditWidget(QWidget):  
    dataChanged = pyqtSignal()  
      
    def __init__(self):  
        super().__init__()  
        self.current_video_name = None  
        self.stt_data_manager = None  
        self.setup_ui()  
      
    def setup_ui(self):  
        layout = QVBoxLayout()  
          
        # タブウィジェット  
        self.tab_widget = QTabWidget()  
          
        # 動画設定タブ  
        self.video_tab = self.create_video_settings_tab()  
        self.tab_widget.addTab(self.video_tab, "Video Settings")  
          
        # アクション編集タブ  
        self.action_tab = self.create_action_edit_tab()  
        self.tab_widget.addTab(self.action_tab, "Actions")  
          
        # ステップ編集タブ  
        self.step_tab = self.create_step_edit_tab()  
        self.tab_widget.addTab(self.step_tab, "Steps")  
          
        layout.addWidget(self.tab_widget)  
        self.setLayout(layout)  
      
    def create_video_settings_tab(self):  
        widget = QWidget()  
        layout = QVBoxLayout()  
          
        # サブセット選択  
        subset_group = QGroupBox("Dataset Subset")  
        subset_layout = QHBoxLayout()  
          
        self.subset_combo = QComboBox()  
        self.subset_combo.addItems(["train", "validation", "test"])  
        self.subset_combo.currentTextChanged.connect(self.on_subset_changed)  
          
        subset_layout.addWidget(QLabel("Subset:"))  
        subset_layout.addWidget(self.subset_combo)  
        subset_group.setLayout(subset_layout)  
          
        layout.addWidget(subset_group)  
        widget.setLayout(layout)  
        return widget  
      
    def create_action_edit_tab(self):  
        widget = QWidget()  
        layout = QHBoxLayout()  
          
        # アクションリスト  
        left_layout = QVBoxLayout()  
        left_layout.addWidget(QLabel("Actions:"))  
          
        self.action_list = QListWidget()  
        self.action_list.itemClicked.connect(self.on_action_selected)  
        left_layout.addWidget(self.action_list)  
          
        # アクション編集  
        right_layout = QVBoxLayout()  
        right_layout.addWidget(QLabel("Edit Action:"))  
          
        # 手の種類  
        hand_layout = QHBoxLayout()  
        hand_layout.addWidget(QLabel("Hand:"))  
        self.hand_combo = QComboBox()  
        self.hand_combo.addItems(["left_hand", "right_hand", "both_hands", "unspecified"])  
        hand_layout.addWidget(self.hand_combo)  
        right_layout.addLayout(hand_layout)            
        # アクション要素  
        self.action_verb_edit = QLineEdit()  
        self.manipulated_object_edit = QLineEdit()  
        self.target_object_edit = QLineEdit()  
        self.tool_edit = QLineEdit()  
          
        right_layout.addWidget(QLabel("Action Verb:"))  
        right_layout.addWidget(self.action_verb_edit)  
        right_layout.addWidget(QLabel("Manipulated Object:"))  
        right_layout.addWidget(self.manipulated_object_edit)  
        right_layout.addWidget(QLabel("Target Object:"))  
        right_layout.addWidget(self.target_object_edit)  
        right_layout.addWidget(QLabel("Tool:"))  
        right_layout.addWidget(self.tool_edit)  
          
        # セグメント編集  
        segment_layout = QHBoxLayout()  
        self.start_time_spin = QDoubleSpinBox()  
        self.start_time_spin.setDecimals(2)  
        self.start_time_spin.setMaximum(9999.99)  
        self.end_time_spin = QDoubleSpinBox()  
        self.end_time_spin.setDecimals(2)  
        self.end_time_spin.setMaximum(9999.99)  
          
        segment_layout.addWidget(QLabel("Start:"))  
        segment_layout.addWidget(self.start_time_spin)  
        segment_layout.addWidget(QLabel("End:"))  
        segment_layout.addWidget(self.end_time_spin)  
        right_layout.addLayout(segment_layout)  
          
        # ボタン  
        button_layout = QHBoxLayout()  
        self.apply_action_btn = QPushButton("Apply Changes")  
        self.apply_action_btn.clicked.connect(self.apply_action_changes)  
        button_layout.addWidget(self.apply_action_btn)  
        right_layout.addLayout(button_layout)  
          
        left_widget = QWidget()  
        left_widget.setLayout(left_layout)  
        right_widget = QWidget()  
        right_widget.setLayout(right_layout)  
          
        layout.addWidget(left_widget)  
        layout.addWidget(right_widget)  
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
        self.refresh_ui()  
      
    def refresh_ui(self):  
        """UIを更新"""  
        if not self.stt_data_manager or not self.current_video_name:  
            return  
              
        # サブセット設定を更新  
        if self.current_video_name in self.stt_data_manager.stt_dataset.database:  
            video_data = self.stt_data_manager.stt_dataset.database[self.current_video_name]  
            self.subset_combo.setCurrentText(video_data.subset)  
              
            # アクションリストを更新  
            self.refresh_action_list()  
              
            # ステップリストを更新  
            self.refresh_step_list()  
      
    def refresh_action_list(self):  
        """アクションリストを更新"""  
        self.action_list.clear()  
        if not self.stt_data_manager or not self.current_video_name:  
            return  
              
        video_data = self.stt_data_manager.stt_dataset.database[self.current_video_name]  
          
        for hand_type, actions in video_data.actions.items():  
            for i, action in enumerate(actions):  
                item_text = f"{hand_type}: {action.action.action_verb}"  
                if action.action.manipulated_object:  
                    item_text += f" - {action.action.manipulated_object}"  
                item = QListWidgetItem(item_text)  
                item.setData(1, (hand_type, i))  # hand_type and index  
                self.action_list.addItem(item)  
      
    def refresh_step_list(self):  
        """ステップリストを更新"""  
        self.step_list.clear()  
        if not self.stt_data_manager or not self.current_video_name:  
            return  
              
        video_data = self.stt_data_manager.stt_dataset.database[self.current_video_name]  
          
        for i, step in enumerate(video_data.steps):  
            item = QListWidgetItem(step.step)  
            item.setData(1, i)  # step index  
            self.step_list.addItem(item)  
      
    def on_subset_changed(self, subset: str):  
        """サブセット変更時の処理"""  
        if self.stt_data_manager and self.current_video_name:  
            self.stt_data_manager.update_video_subset(self.current_video_name, subset)  
            self.dataChanged.emit()  
      
    def on_action_selected(self, item):  
        """アクション選択時の処理"""  
        if not self.stt_data_manager or not self.current_video_name:  
            return  
              
        hand_type, index = item.data(1)  
        video_data = self.stt_data_manager.stt_dataset.database[self.current_video_name]  
        action = video_data.actions[hand_type][index]  
          
        # UI要素を更新  
        self.hand_combo.setCurrentText(hand_type)  
        self.action_verb_edit.setText(action.action.action_verb)  
        self.manipulated_object_edit.setText(action.action.manipulated_object or "")  
        self.target_object_edit.setText(action.action.target_object or "")  
        self.tool_edit.setText(action.action.tool or "")  
          
        if len(action.segment) >= 2:  
            self.start_time_spin.setValue(action.segment[0])  
            self.end_time_spin.setValue(action.segment[1])  
      
    def on_step_selected(self, item):  
        """ステップ選択時の処理"""  
        if not self.stt_data_manager or not self.current_video_name:  
            return  
              
        index = item.data(1)  
        video_data = self.stt_data_manager.stt_dataset.database[self.current_video_name]  
        step = video_data.steps[index]  
          
        # UI要素を更新  
        self.step_edit_text.setText(step.step)  
        if len(step.segment) >= 2:  
            self.step_start_spin.setValue(step.segment[0])  
            self.step_end_spin.setValue(step.segment[1])  
      
    def apply_action_changes(self):  
        """アクション変更を適用"""  
        current_item = self.action_list.currentItem()  
        if not current_item or not self.stt_data_manager or not self.current_video_name:  
            return  
              
        hand_type, index = current_item.data(1)  
        video_data = self.stt_data_manager.stt_dataset.database[self.current_video_name]  
        action = video_data.actions[hand_type][index]  
          
        # アクションデータを更新  
        action.action.action_verb = self.action_verb_edit.text()  
        action.action.manipulated_object = self.manipulated_object_edit.text() or None  
        action.action.target_object = self.target_object_edit.text() or None  
        action.action.tool = self.tool_edit.text() or None  
          
        # セグメントを更新  
        action.segment = [self.start_time_spin.value(), self.end_time_spin.value()]  
        fps = video_data.fps  
        action.segment_frames = [int(action.segment[0] * fps), int(action.segment[1] * fps)]  
          
        self.refresh_action_list()  
        self.dataChanged.emit()  
      
    def add_step(self):  
        """ステップを追加"""  
        step_text = self.step_text_edit.text().strip()  
        if not step_text or not self.stt_data_manager or not self.current_video_name:  
            return  
              
        # デフォルトセグメント（0-1秒）  
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
          
        # ステップデータを更新  
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
          
        # ステップを削除  
        del video_data.steps[index]  
          
        self.refresh_step_list()  
        self.dataChanged.emit()