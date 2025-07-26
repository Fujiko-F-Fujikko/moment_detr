# StepEditor.py  
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,  
                            QLineEdit, QPushButton, QGroupBox, QListWidget,  
                            QListWidgetItem, QDoubleSpinBox, QApplication)  
from PyQt6.QtCore import pyqtSignal, QTimer
from typing import Optional  
  
from Results import QueryResults
from EditCommandFactory import EditCommandFactory  
from Utilities import show_call_stack
  
class StepEditor(QWidget):  
    """ステップ編集に特化したエディタークラス"""  
      
    # シグナル定義  
    stepAdded = pyqtSignal()  
    stepModified = pyqtSignal()  
    stepDeleted = pyqtSignal()  
    dataChanged = pyqtSignal()  
      
    def __init__(self, main_window=None):  
        super().__init__()  
        self.main_window = main_window  
        self.command_factory = EditCommandFactory(main_window) if main_window else None  
        self.stt_data_manager = None  
        self.current_video_name: Optional[str] = None  
        self.current_query_result: Optional[QueryResults] = None
          
        # UI要素  
        self.step_text_edit: Optional[QLineEdit] = None  
        self.add_step_btn: Optional[QPushButton] = None  
        self.step_list: Optional[QListWidget] = None  
        self.step_edit_text: Optional[QLineEdit] = None  
        self.step_start_spin: Optional[QDoubleSpinBox] = None  
        self.step_end_spin: Optional[QDoubleSpinBox] = None  
        self.delete_step_btn: Optional[QPushButton] = None  
          
        # タイマー（連続入力防止用）  
        self._step_timer: Optional[QTimer] = None  

        self._is_selecting_step = False
          
        self.setup_ui()  
      
    def setup_ui(self):  
        """UIレイアウトの設定"""  
        layout = QVBoxLayout()  
          
        # ステップ追加セクション  
        self._create_step_addition_section(layout)  
          
        # ステップリストセクション  
        self._create_step_list_section(layout)  
          
        # ステップ編集セクション  
        self._create_step_editing_section(layout)  
          
        self.setLayout(layout)  
          
        # シグナル接続  
        self._connect_signals()  
      
    def _create_step_addition_section(self, parent_layout: QVBoxLayout):  
        """ステップ追加セクションを作成"""  
        add_layout = QHBoxLayout()  
          
        self.step_text_edit = QLineEdit()  
        self.step_text_edit.setPlaceholderText("Enter step description...")  
          
        self.add_step_btn = QPushButton("Add Step")  
          
        add_layout.addWidget(QLabel("Step:"))  
        add_layout.addWidget(self.step_text_edit)  
        add_layout.addWidget(self.add_step_btn)  
          
        parent_layout.addLayout(add_layout)  
      
    def _create_step_list_section(self, parent_layout: QVBoxLayout):  
        """ステップリストセクションを作成"""  
        parent_layout.addWidget(QLabel("Steps:"))  
          
        self.step_list = QListWidget()  
        parent_layout.addWidget(self.step_list)  
      
    def _create_step_editing_section(self, parent_layout: QVBoxLayout):  
        """ステップ編集セクションを作成"""  
        edit_group = QGroupBox("Edit Selected Step")  
        edit_layout = QVBoxLayout()  
          
        # ステップテキスト編集  
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
          
        # 削除ボタン  
        button_layout = QHBoxLayout()  
        self.delete_step_btn = QPushButton("Delete Step")  
        button_layout.addWidget(self.delete_step_btn)  
        edit_layout.addLayout(button_layout)  
          
        edit_group.setLayout(edit_layout)  
        parent_layout.addWidget(edit_group)  
      
    def _connect_signals(self):  
        """シグナル接続を設定"""  
        # ボタンクリック  
        self.add_step_btn.clicked.connect(self.add_step)  
        self.delete_step_btn.clicked.connect(self.delete_step)  
          
        # リスト選択  
        self.step_list.itemClicked.connect(self.on_step_selected)  
          
        # 即時反映のためのシグナル接続  
        self.step_edit_text.textChanged.connect(self.on_step_value_changed)  
        self.step_start_spin.valueChanged.connect(self.on_step_value_changed)  
        self.step_end_spin.valueChanged.connect(self.on_step_value_changed)  
      
    def set_stt_data_manager(self, manager):  
        """STTDataManagerを設定"""  
        self.stt_data_manager = manager  
      
    def set_current_video(self, video_name: str):  
        """現在の動画を設定"""  
        self.current_video_name = video_name  
        self.refresh_step_list()  
      
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
      
    def on_step_selected(self, item: QListWidgetItem):  
        """ステップ選択時の処理"""  
        if self._is_selecting_step:  
            return  
        
        self._is_selecting_step = True  
        
        try:  
            # 既存のUI更新処理  
            index = item.data(1)  
            video_data = self.stt_data_manager.stt_dataset.database[self.current_video_name]  
            step = video_data.steps[index]  
              
            self.step_edit_text.setText(step.step)  
            if len(step.segment) >= 2:  
                self.step_start_spin.setValue(step.segment[0])  
                self.step_end_spin.setValue(step.segment[1])  
            
            # EditWidgetManagerに委譲  
            if hasattr(self.main_window, 'edit_widget_manager'):  
                self.main_window.edit_widget_manager.handle_step_selection_from_editor(  
                    step.step, step.segment[0], step.segment[1]  
                )  
        finally:  
            # シグナルを再有効化  
            self._block_signals(False)  
            self._is_selecting_step = False
      
    def _block_signals(self, block: bool):  
        """シグナルのブロック/アンブロック"""  
        widgets = [  
            self.step_edit_text,  
            self.step_start_spin,  
            self.step_end_spin  
        ]  
          
        for widget in widgets:  
            if widget:  
                widget.blockSignals(block)  
      
    def add_step(self):  
        """ステップを追加"""  
        step_text = self.step_text_edit.text().strip()  
        if not step_text or not self.stt_data_manager or not self.current_video_name or not self.command_factory:  
            return  
          
        segment = [0.0, 1.0]  
          
        success = self.command_factory.create_and_execute_step_add(  
            self.stt_data_manager, self.current_video_name, step_text, segment  
        )  
          
        if success:  
            self.step_text_edit.clear()  
            self.stepAdded.emit()  
            self.dataChanged.emit()
            # 最後に選択状態を更新
            self.select_step(step_text=step_text)  
            
    def on_step_value_changed(self):  
        """Step値が変更された時の即時処理"""  
        
        # 連続入力を防ぐため遅延処理  
        if self._step_timer and self._step_timer.isActive():  
            self._step_timer.stop()  
        
        self._step_timer = QTimer()  
        self._step_timer.setSingleShot(True)  
        self._step_timer.timeout.connect(self.apply_step_changes)  
        self._step_timer.start(500)  # 500ms後に適用  
      
    def apply_step_changes(self):  
        """ステップ変更を適用"""  
        current_item = self.step_list.currentItem()  
        if not current_item or not self.stt_data_manager or not self.current_video_name or not self.command_factory:  
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
            return  
          
        # ファクトリーを使用してコマンドを作成・実行  
        if text_changed:  
            self.command_factory.create_and_execute_step_text_modify(  
                self.stt_data_manager, self.current_video_name, index, old_text, new_text  
            )  
          
        if segment_changed:  
            # ApplicationCoordinator経由でセグメント変更を適用  
            self._apply_segment_changes(old_segment, new_segment, old_text)  
          
        # UIを即座に更新  
        self.refresh_step_list()  
        
        # シグナル発信  
        self.stepModified.emit()  
        self.dataChanged.emit() 

        # 最後に選択状態を更新
        self.select_step(step_text=new_text if text_changed else old_text, step_index=index)
      
    def _apply_segment_changes(self, old_segment: list, new_segment: list, step_text: str):  
        """セグメント変更をタイムラインに適用"""  
        if not self.main_window or not hasattr(self.main_window, 'application_coordinator'):  
            return  
          
        # ApplicationCoordinator経由でステップセグメント更新を処理  
        coordinator = self.main_window.application_coordinator  
        coordinator.handle_step_segment_update(step_text, old_segment, new_segment)

    def _update_step_edit_ui(self):  
        """Step編集UIの現在選択項目を更新"""  
        current_item = self.step_list.currentItem()  
        if current_item and self.stt_data_manager and self.current_video_name:  
            index = current_item.data(1)  
            if index < len(self.stt_data_manager.stt_dataset.database[self.current_video_name].steps):  
                step = self.stt_data_manager.stt_dataset.database[self.current_video_name].steps[index]  
                
                # シグナルを一時的に無効化  
                self._block_signals(True)  
                try:  
                    self.step_edit_text.setText(step.step)  
                    if len(step.segment) >= 2:  
                        self.step_start_spin.setValue(step.segment[0])  
                        self.step_end_spin.setValue(step.segment[1])  
                finally:  
                    # シグナルを再有効化  
                    self._block_signals(False)
      
    def delete_step(self):  
        """ステップを削除"""  
        current_item = self.step_list.currentItem()  
        if not current_item or not self.stt_data_manager or not self.current_video_name or not self.command_factory:  
            return  
          
        index = current_item.data(1)  
          
        self.command_factory.create_and_execute_step_delete(  
            self.stt_data_manager, self.current_video_name, index  
        )  
          
        # シグナル発信  
        self.stepDeleted.emit()  
        self.dataChanged.emit()  

    def set_current_query_results(self, query_result: QueryResults):  
        """現在のクエリ結果を設定"""  
        self.current_query_result = query_result  
    
    def update_interval_realtime(self, new_start: float, new_end: float):  
        """ドラッグ中のリアルタイム更新"""  
        self._block_signals(True)  
        try:  
            self.step_start_spin.setValue(new_start)  
            self.step_end_spin.setValue(new_end)  
        finally:  
            self._block_signals(False)  

    def select_step(self, step_text: str = None, step_index: int = None):  
        """テキストまたはインデックスでステップを選択"""  
        if not self.step_list:  
            print("Step list is not initialized")  
            return  
        
        for i in range(self.step_list.count()):  
            item = self.step_list.item(i)  
            if not item:  
                continue  
                
            item_index = item.data(1)  
            
            # テキストまたはインデックスで一致判定  
            match_found = False  
            if step_text and item.text() == step_text:  
                match_found = True  
            elif step_index is not None and item_index == step_index:  
                match_found = True  
                
            if match_found:  
                self.step_list.setCurrentItem(item)  
                item.setSelected(True)  
                self.step_list.scrollToItem(item, QListWidget.ScrollHint.PositionAtCenter)  
                self.on_step_selected(item)  
                break

    def get_current_state(self) -> dict:  
        """現在の編集状態を取得（デバッグ用）"""  
        current_item = self.step_list.currentItem() if self.step_list else None  
        return {  
            'has_stt_data_manager': self.stt_data_manager is not None,  
            'current_video_name': self.current_video_name,  
            'step_count': self.step_list.count() if self.step_list else 0,  
            'selected_step': current_item.text() if current_item else None  
        }