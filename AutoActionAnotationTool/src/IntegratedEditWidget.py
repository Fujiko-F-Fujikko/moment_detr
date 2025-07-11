# IntegratedEditWidget.py  
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,   
                            QComboBox, QLineEdit, QPushButton, QGroupBox,  
                            QListWidget, QListWidgetItem, QDoubleSpinBox,  
                            QTabWidget, QMessageBox)  
from PyQt6.QtCore import pyqtSignal, QTimer, Qt

from Results import QueryResults, DetectionInterval  
from TimelineViewer import TimelineViewer
from IntervalModifyCommand import IntervalModifyCommand, IntervalDeleteCommand, IntervalAddCommand
from StepModifyCommand import StepModifyCommand, StepDeleteCommand, StepAddCommand, StepTextModifyCommand
from ActionEditCommand import ActionDetailModifyCommand
from STTDataStructures import QueryParser  

  
class IntegratedEditWidget(QWidget):  
    dataChanged = pyqtSignal()  
    intervalUpdated = pyqtSignal()  
    intervalDeleted = pyqtSignal()  
    intervalAdded = pyqtSignal()  
      
    def __init__(self, main_window=None):  
        super().__init__()  
        self.current_query_result = None  
        self.selected_interval = None  
        self.selected_interval_index = -1  
        self.stt_data_manager = None  
        self.current_video_name = None  
        self.main_window = main_window
        print("IntegratedEditWidget initialized. main_window:", main_window)
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

        # 即時反映のためのシグナル接続を追加  
        self.start_spinbox.valueChanged.connect(self.on_action_value_changed)  
        self.end_spinbox.valueChanged.connect(self.on_action_value_changed)  
        self.hand_combo.currentTextChanged.connect(self.on_action_value_changed)  
        self.action_verb_edit.textChanged.connect(self.on_action_value_changed)  
        self.manipulated_object_edit.textChanged.connect(self.on_action_value_changed)  
        self.target_object_edit.textChanged.connect(self.on_action_value_changed)  
        self.tool_edit.textChanged.connect(self.on_action_value_changed)         
          
        interval_layout.addLayout(action_detail_layout)  
          
        # ボタン  
        button_layout = QHBoxLayout()  
        self.add_button = QPushButton("Add New Interval")  
        self.delete_button = QPushButton("Delete Interval")  
          
        self.add_button.clicked.connect(self.add_new_interval)  
        self.delete_button.clicked.connect(self.delete_interval)  
          
        button_layout.addWidget(self.add_button)  
        button_layout.addWidget(self.delete_button)  
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

        # 即時反映のためのシグナル接続を追加  
        self.step_edit_text.textChanged.connect(self.on_step_value_changed)  

        # セグメント編集  
        segment_layout = QHBoxLayout()  
        self.step_start_spin = QDoubleSpinBox()  
        self.step_start_spin.setDecimals(2)  
        self.step_start_spin.setMaximum(9999.99)  
        self.step_end_spin = QDoubleSpinBox()  
        self.step_end_spin.setDecimals(2)  
        self.step_end_spin.setMaximum(9999.99)  

        # 即時反映のためのシグナル接続を追加  
        self.step_start_spin.valueChanged.connect(self.on_step_value_changed)  
        self.step_end_spin.valueChanged.connect(self.on_step_value_changed)

        segment_layout.addWidget(QLabel("Start:"))  
        segment_layout.addWidget(self.step_start_spin)  
        segment_layout.addWidget(QLabel("End:"))  
        segment_layout.addWidget(self.step_end_spin)  
        edit_layout.addLayout(segment_layout)  
          
        # ボタン  
        button_layout = QHBoxLayout()  
        self.delete_step_btn = QPushButton("Delete Step")  
        self.delete_step_btn.clicked.connect(self.delete_step)  
          
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
            # シグナルを一時的に無効化  
            self.start_spinbox.blockSignals(True)  
            self.end_spinbox.blockSignals(True)  
            
            self.start_spinbox.setValue(self.selected_interval.start_time)  
            self.end_spinbox.setValue(self.selected_interval.end_time)  
            self.confidence_label.setText(f"Confidence: {self.selected_interval.confidence_score:.3f}")  
            
            # Stepクエリの場合はAction編集フィールドの更新をスキップ  
            if self.current_query_result and not self.current_query_result.query_text.startswith("Step:"):  
                # Action編集フィールドのシグナルも無効化  
                self.hand_combo.blockSignals(True)  
                self.action_verb_edit.blockSignals(True)  
                self.manipulated_object_edit.blockSignals(True)  
                self.target_object_edit.blockSignals(True)  
                self.tool_edit.blockSignals(True)  
                
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
                finally:  
                    # Action編集フィールドのシグナルを再有効化  
                    self.hand_combo.blockSignals(False)  
                    self.action_verb_edit.blockSignals(False)  
                    self.manipulated_object_edit.blockSignals(False)  
                    self.target_object_edit.blockSignals(False)  
                    self.tool_edit.blockSignals(False)  
            
            # 時間編集フィールドのシグナルを再有効化  
            self.start_spinbox.blockSignals(False)  
            self.end_spinbox.blockSignals(False)  
        else:  
            # Action編集フィールドのシグナルを無効化  
            self.hand_combo.blockSignals(True)  
            self.action_verb_edit.blockSignals(True)  
            self.manipulated_object_edit.blockSignals(True)  
            self.target_object_edit.blockSignals(True)  
            self.tool_edit.blockSignals(True)  
            
            self.start_spinbox.setValue(0.0)    
            self.end_spinbox.setValue(0.0)    
            self.confidence_label.setText("Confidence: N/A")    
            self.action_verb_edit.clear()    
            self.manipulated_object_edit.clear()    
            self.target_object_edit.clear()    
            self.tool_edit.clear()  
            
            # Action編集フィールドのシグナルを再有効化  
            self.hand_combo.blockSignals(False)  
            self.action_verb_edit.blockSignals(False)  
            self.manipulated_object_edit.blockSignals(False)  
            self.target_object_edit.blockSignals(False)  
            self.tool_edit.blockSignals(False)

    def apply_interval_changes(self):  
        """区間変更を適用"""  
        if not self.selected_interval or not self.current_query_result:  
            return  

        # Stepクエリの場合は何もしない  
        if self.current_query_result.query_text.startswith("Step:"):  
            print("DEBUG: Skipping apply_interval_changes for Step query")  
            return

        # 現在の値を取得  
        old_start = self.selected_interval.start_time  
        old_end = self.selected_interval.end_time  
        new_start = self.start_spinbox.value()  
        new_end = self.end_spinbox.value()  
        
        old_query_text = self.current_query_result.query_text  
        new_query_text = self._build_new_query_text()  
        
        # 実際に変更があるかチェック（浮動小数点の比較を考慮）  
        time_changed = (abs(old_start - new_start) > 0.01 or abs(old_end - new_end) > 0.01)  
        query_changed = (old_query_text != new_query_text)  
        
        # 変更がない場合は何もしない  
        if not time_changed and not query_changed:  
            print("DEBUG: No actual changes detected, skipping command creation")  
            return  
        
        main_window = self.main_window  
        if main_window:  
            # デバッグ：変更前のスタック状態  
            main_window.debug_undo_stack("BEFORE apply_interval_changes")  

            # 実際に変更がある場合のみコマンドを作成  
            if time_changed:  
                time_command = IntervalModifyCommand(self.selected_interval, old_start, old_end, new_start, new_end, main_window)  
                main_window.undo_stack.push(time_command)  
            
            if query_changed:  
                action_command = ActionDetailModifyCommand(self.current_query_result, old_query_text, new_query_text, main_window)  
                main_window.undo_stack.push(action_command)

        # UIを即座に更新（新規追加）  
        self.update_interval_ui()  
        
        # シグナルを発火  
        self.intervalUpdated.emit()  
        self.dataChanged.emit()

    def _build_new_query_text(self):  
        """入力フィールドから新しいクエリテキストを構築"""  
        hand_mapping = {"left_hand": "LeftHand", "right_hand": "RightHand", "both_hands": "BothHands", "unspecified": "None"}  
        hand_type = hand_mapping.get(self.hand_combo.currentText(), "None")  
        
        action_verb = self.action_verb_edit.text().strip() or "None"  
        manipulated_object = self.manipulated_object_edit.text().strip() or "None"  
        target_object = self.target_object_edit.text().strip() or "None"  
        tool = self.tool_edit.text().strip() or "None"  
        
        return f"{hand_type}_{action_verb}_{manipulated_object}_{target_object}_{tool}"

    def delete_interval(self):  
        """区間を削除"""  
        if not self.selected_interval or not self.current_query_result:  
            return  
        
        # 区間のインデックスを取得  
        index = self.current_query_result.relevant_windows.index(self.selected_interval)  
        
        main_window = self.main_window  
        if main_window:  
            command = IntervalDeleteCommand(self.current_query_result, self.selected_interval, index, main_window)  
            main_window.undo_stack.push(command)  
    
    def add_new_interval(self):  
        """新しい区間を追加"""  
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
        new_interval = DetectionInterval(start_time, end_time, 1.0, len(self.current_query_result.relevant_windows))  
        new_interval.query_result = self.current_query_result  
        
        main_window = self.main_window  
        if main_window:  
            command = IntervalAddCommand(self.current_query_result, new_interval, main_window)  
            main_window.undo_stack.push(command)  
      
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
        print(f"DEBUG: on_step_selected called for item: {item.text()}")  
        
        if not self.stt_data_manager or not self.current_video_name:    
            return    
        
        # デバッグ：選択前のスタック状態  
        if self.main_window:  
            self.main_window.debug_undo_stack("BEFORE on_step_selected")  
        
        index = item.data(1)    
        video_data = self.stt_data_manager.stt_dataset.database[self.current_video_name]    
        step = video_data.steps[index]    
        
        # シグナルを一時的に無効化  
        print("DEBUG: Blocking signals for step UI components")  
        self.step_edit_text.blockSignals(True)  
        self.step_start_spin.blockSignals(True)  
        self.step_end_spin.blockSignals(True)  
        
        self.step_edit_text.setText(step.step)    
        if len(step.segment) >= 2:    
            self.step_start_spin.setValue(step.segment[0])    
            self.step_end_spin.setValue(step.segment[1])    
        
        # シグナルを再有効化  
        print("DEBUG: Unblocking signals for step UI components")  
        self.step_edit_text.blockSignals(False)  
        self.step_start_spin.blockSignals(False)  
        self.step_end_spin.blockSignals(False)  
        
        # デバッグ：選択後のスタック状態  
        if self.main_window:  
            self.main_window.debug_undo_stack("AFTER on_step_selected")

    def add_step(self):  
        """ステップを追加"""  
        step_text = self.step_text_edit.text().strip()  
        if not step_text or not self.stt_data_manager or not self.current_video_name:  
            return  
        
        segment = [0.0, 1.0]  
        main_window = self.main_window  
        if main_window:  
            command = StepAddCommand(self.stt_data_manager, self.current_video_name, step_text, segment, main_window)  
            main_window.undo_stack.push(command)  
            # 追加されたステップを選択状態にする（新規追加）  
            self._select_newly_added_step(step_text)      

    def _select_newly_added_step(self, step_text):  
        """新しく追加されたステップを選択状態にする"""  
        # ステップリストを更新  
        self.refresh_step_list()  
        
        # 追加されたステップを検索して選択  
        for i in range(self.step_list.count()):  
            item = self.step_list.item(i)  
            if item.text() == step_text:  
                # アイテムを選択状態にする  
                self.step_list.setCurrentItem(item)  
                item.setSelected(True)  
                
                # スクロールして表示  
                self.step_list.scrollToItem(item, QListWidget.ScrollHint.PositionAtCenter)  
                
                # 編集フィールドに値を設定  
                self.on_step_selected(item)  
                break

    def apply_step_changes(self):  
        """ステップ変更を適用"""  
        current_item = self.step_list.currentItem()  
        if not current_item or not self.stt_data_manager or not self.current_video_name:  
            return  
        
        index = current_item.data(1)  
        video_data = self.stt_data_manager.stt_dataset.database[self.current_video_name]  
        step = video_data.steps[index]  
        
        old_text = step.step  
        old_segment = step.segment.copy()  
        new_text = self.step_edit_text.text()  
        new_segment = [self.step_start_spin.value(), self.step_end_spin.value()]  
        
        # 実際に変更があるかチェック  
        text_changed = (old_text != new_text)  
        segment_changed = (abs(old_segment[0] - new_segment[0]) > 0.01 or   
                        abs(old_segment[1] - new_segment[1]) > 0.01)  
        
        # 変更がない場合は何もしない  
        if not text_changed and not segment_changed:  
            print("DEBUG: No actual step changes detected, skipping command creation")  
            return  

        main_window = self.main_window  
        if main_window:  
            # テキスト変更のコマンド  
            if old_text != new_text:  
                text_command = StepTextModifyCommand(self.stt_data_manager, self.current_video_name, index, old_text, new_text, main_window)  
                main_window.undo_stack.push(text_command)  
            
            # セグメント変更のコマンド（該当するDetectionIntervalを見つける必要がある）  
            if old_segment != new_segment:  
                # Stepsタイムラインから該当するintervalを見つける  
                for timeline_widget in main_window.multi_timeline_viewer.timeline_widgets:  
                    timeline = timeline_widget.findChild(TimelineViewer)  
                    if timeline:  
                        for interval in timeline.intervals:  
                            if hasattr(interval, 'label') and interval.label == old_text:  
                                step_command = StepModifyCommand(interval, old_segment[0], old_segment[1],   
                                                            new_segment[0], new_segment[1],   
                                                            self.stt_data_manager, self.current_video_name, main_window)  
                                main_window.undo_stack.push(step_command)  
                                break  

        # UIを即座に更新（新規追加）  
        self.refresh_step_list()  
        self._restore_step_selection(new_text, index)  
        self._update_step_edit_ui()  
        
        # シグナルを発火  
        self.dataChanged.emit()

    def _update_step_edit_ui(self):  
        """Step編集UIの現在選択項目を更新"""  
        current_item = self.step_list.currentItem()  
        if current_item and self.stt_data_manager and self.current_video_name:  
            index = current_item.data(1)  
            if index < len(self.stt_data_manager.stt_dataset.database[self.current_video_name].steps):  
                step = self.stt_data_manager.stt_dataset.database[self.current_video_name].steps[index]  
                self.step_edit_text.setText(step.step)  
                if len(step.segment) >= 2:  
                    self.step_start_spin.setValue(step.segment[0])  
                    self.step_end_spin.setValue(step.segment[1])

    def delete_step(self):  
        """ステップを削除"""  
        current_item = self.step_list.currentItem()  
        if not current_item or not self.stt_data_manager or not self.current_video_name:  
            return  
        
        index = current_item.data(1)  
        main_window = self.main_window  
        if main_window:  
            command = StepDeleteCommand(self.stt_data_manager, self.current_video_name, index, main_window)  
            main_window.undo_stack.push(command)

    def switch_to_appropriate_tab(self, interval):    
        """区間の種類に応じて適切なタブに切り替える"""    
        if hasattr(interval, 'query_result') and interval.query_result:    
            query_text = interval.query_result.query_text    
            print(f"DEBUG: switch_to_appropriate_tab called with query: {query_text}")  
            
            # Stepの区間かどうかを判定    
            if query_text.startswith("Step:"):    
                print("DEBUG: Switching to Step Edit tab")  
                # Step Editタブに切り替え    
                self.tab_widget.setCurrentIndex(1)  # Step Editタブのインデックス    
                # クリックされたステップを選択状態にする    
                self._select_step_by_label(interval.label)    
            else:    
                print("DEBUG: Switching to Action Edit tab")  
                # Action Editタブに切り替え    
                self.tab_widget.setCurrentIndex(0)  # Action Editタブのインデックス

    def _select_step_by_label(self, step_label):  
        """ステップラベルに基づいてステップリストで該当項目を選択"""  
        if not step_label or not self.step_list:  
            return  
        
        # ステップリストから該当するアイテムを検索  
        for i in range(self.step_list.count()):  
            item = self.step_list.item(i)  
            if item.text() == step_label:  
                # アイテムを選択状態にする  
                self.step_list.setCurrentItem(item)  
                item.setSelected(True)  
                
                # スクロールして表示  
                self.step_list.scrollToItem(item, QListWidget.ScrollHint.PositionAtCenter)  
                
                # 編集フィールドに値を設定  
                self.on_step_selected(item)  
                break

    def on_action_value_changed(self):  
        """Action値が変更された時の即時処理"""          
        # 少し遅延を入れて連続入力を防ぐ  
        if hasattr(self, '_action_timer'):  
            if self._action_timer.isActive():  
                print(f"DEBUG: Stopping existing timer")  
            self._action_timer.stop()  
        
        self._action_timer = QTimer()  
        self._action_timer.setSingleShot(True)  
        self._action_timer.timeout.connect(self.apply_interval_changes)  
        self._action_timer.start(500)  # 500ms後に適用

    def on_step_value_changed(self):    
        """Step値が変更された時の即時処理"""    
        print("DEBUG: on_step_value_changed called")  
        
        # 少し遅延を入れて連続入力を防ぐ    
        if hasattr(self, '_step_timer'):    
            if self._step_timer.isActive():  
                print("DEBUG: Stopping existing step timer")  
            self._step_timer.stop()    
        
        print("DEBUG: Starting new step timer (500ms)")  
        from PyQt6.QtCore import QTimer    
        self._step_timer = QTimer()    
        self._step_timer.setSingleShot(True)    
        self._step_timer.timeout.connect(self.apply_step_changes)    
        self._step_timer.start(500)  # 500ms後に適用

    def _restore_step_selection(self, step_text, original_index):  
        """ステップの選択状態を復元"""  
        # 更新されたステップテキストまたは元のインデックスで検索  
        for i in range(self.step_list.count()):  
            item = self.step_list.item(i)  
            item_index = item.data(1)  
            
            # インデックスが一致するか、テキストが一致する場合に選択  
            if item_index == original_index or item.text() == step_text:  
                self.step_list.setCurrentItem(item)  
                item.setSelected(True)  
                self.step_list.scrollToItem(item, QListWidget.ScrollHint.PositionAtCenter)  
                self.on_step_selected(item)  
                break

    def keyPressEvent(self, event):  
        """統合編集ウィジェットのキーイベント処理"""  
        if event.key() == Qt.Key.Key_Tab:  
            # タブ内でのフォーカス移動  
            current_tab = self.tab_widget.currentIndex()  
            if current_tab == 0:  # Action Edit  
                self._focus_next_action_widget()  
            elif current_tab == 1:  # Step Edit  
                self._focus_next_step_widget()  
            event.accept()  
        elif event.key() == Qt.Key.Key_Return:  
            # Enterキーでの決定処理  
            self._handle_enter_key()  
            event.accept()  
        else:  
            super().keyPressEvent(event)  
    
    def _focus_next_action_widget(self):  
        """Action Editタブ内でのフォーカス移動"""  
        focus_order = [  
            self.start_spinbox, self.end_spinbox, self.hand_combo,  
            self.action_verb_edit, self.manipulated_object_edit,  
            self.target_object_edit, self.tool_edit,  
            self.add_button, self.delete_button  
        ]  
        current_widget = self.focusWidget()  
        try:  
            current_index = focus_order.index(current_widget)  
            next_index = (current_index + 1) % len(focus_order)  
            focus_order[next_index].setFocus()  
        except ValueError:  
            focus_order[0].setFocus()  
    
    def _handle_enter_key(self):  
        """Enterキーでの決定処理"""  
        focused_widget = self.focusWidget()  
        if focused_widget == self.add_button:  
            self.add_new_interval()  
        elif focused_widget == self.delete_button:  
            self.delete_interval()  
        elif focused_widget == self.add_step_btn:  
            self.add_step()  
        elif focused_widget == self.delete_step_btn:  
            self.delete_step()