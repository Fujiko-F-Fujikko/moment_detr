# StepEditor.py (STTデータ非依存版)  
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,  
                            QLineEdit, QPushButton, QGroupBox, QListWidget,  
                            QListWidgetItem, QDoubleSpinBox, QApplication)  
from PyQt6.QtCore import pyqtSignal, QTimer  
from typing import Optional, List  
  
from DataClasses import QueryResults, DetectionInterval
from EditCommandFactory import EditCommandFactory  
from ResultsDataController import ResultsDataController
from Utilities import show_call_stack  
  
class StepEditor(QWidget):  
    """ステップ編集に特化したエディタークラス（STTデータ非依存）"""  
      
    # シグナル定義  
    stepAdded = pyqtSignal()  
    stepModified = pyqtSignal()  
    stepDeleted = pyqtSignal()  
    dataChanged = pyqtSignal()  
      
    def __init__(self, main_window=None):  
        super().__init__()  
        self.main_window = main_window  
        self.command_factory = EditCommandFactory(main_window) if main_window else None
        self.results_data_controller = None  
        self.current_video_name: Optional[str] = None  
        self.step_query_results: List[QueryResults] = []  # ステップ用のQueryResults  
          
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
        """シグナル接続の設定"""  
        # 修正：ラムダ関数を使用して引数なしで呼び出し  
        self.add_step_btn.clicked.connect(lambda: self.add_step())
        
        self.step_list.itemClicked.connect(self.on_step_selected)  
      
        self.delete_step_btn.clicked.connect(self.delete_step)  
        
        # 編集フィールドの変更検知  
        self.step_edit_text.textChanged.connect(self._on_step_text_changed)  
      
        self.step_start_spin.valueChanged.connect(self._on_segment_changed)  
      
        self.step_end_spin.valueChanged.connect(self._on_segment_changed)  
      
    def set_results_data_controller(self, controller: ResultsDataController):  
        """ResultsDataControllerを設定"""  
        self.results_data_controller = controller 
        self._load_step_data()  
      
    def set_current_video(self, video_name: str):  
        """現在の動画を設定"""  
        self.current_video_name = video_name  
        self._load_step_data()  
        self.refresh_step_list()  
      
    def _load_step_data(self):  
        if self.results_data_controller is None:  
            print(f"[DEBUG] ERROR: results_data_controller is None in _load_step_data!")  
            return  
          
        all_results = self.results_data_controller.get_filtered_results()  
         
        self.step_query_results = [qr for qr in all_results if qr.query_text.startswith("Step:")]  

    def refresh_step_list(self):            
        if self.step_list is None:  
            print(f"[DEBUG] ERROR: step_list is None!")  
            return  
        if self.results_data_controller is None:  
            print(f"[DEBUG] ERROR: results_data_controller is None!")  
            return
          
        self.step_list.clear()  
        step_query_results = self.get_step_query_results()  
          
        for i, query_result in enumerate(step_query_results):  
            step_text = query_result.query_text.replace("Step:", "").strip()  
            item = QListWidgetItem(step_text)  
            item.setData(1, i)  
            self.step_list.addItem(item)  
      
    def on_step_selected(self, item: QListWidgetItem):  
        """ステップ選択時の処理"""  
        if self._is_selecting_step:  
            return  
          
        self._is_selecting_step = True  
          
        try:  
            index = item.data(1)  
            if index < len(self.step_query_results):  
                query_result = self.step_query_results[index]  
                step_text = query_result.query_text.replace("Step:", "").strip()  
                  
                self.step_edit_text.setText(step_text)  
                  
                # 最初の区間の時間を表示（ステップには通常1つの区間）  
                if query_result.relevant_windows:  
                    interval = query_result.relevant_windows[0]  
                    self.step_start_spin.setValue(interval.start_time)  
                    self.step_end_spin.setValue(interval.end_time)  
                  
                # EditWidgetManagerに委譲  
                if hasattr(self.main_window, 'edit_widget_manager'):  
                    self.main_window.edit_widget_manager.handle_step_selection_from_editor(  
                        step_text,   
                        interval.start_time if query_result.relevant_windows else 0.0,  
                        interval.end_time if query_result.relevant_windows else 0.0  
                    )  
        finally:  
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
      
    def add_step(self, query_result: Optional[QueryResults] = None, start_time: Optional[float] = None, end_time: Optional[float] = None):  
        """新しいステップを追加"""  
        if self.results_data_controller is None:  
            print(f"[DEBUG] ERROR: results_data_controller is None!")  
            return  
          
        if query_result is None:  
            # ボタンクリック時のデフォルト処理  
            if self.step_text_edit is None:  
                return  
            step_text = self.step_text_edit.text().strip()  
            if step_text is None:  
                return  
                  
            # 新しいQueryResultを作成  
            query_result = QueryResults(  
                query_text=f"Step:{step_text}",  
                video_id=self.current_video_name or "unknown",  
                relevant_windows=[],  
                saliency_scores=[],  
                query_id=len(self.step_query_results)  
            )  
              
            self.step_text_edit.clear()  
          
        # 時間設定  
        if start_time is not None and end_time is not None:  
            calculated_start = start_time  
            calculated_end = end_time  
        else:  
            default_duration = 1.0
            calculated_start = 0.0  
            calculated_end = calculated_start + default_duration
          
        # デフォルトの区間を作成  
        print(f"query_result: {query_result}, type: {type(query_result)}")
        default_interval = DetectionInterval(  
            start_time=calculated_start,  
            end_time=calculated_end,  
            confidence_score=1.0,  
            query_id=query_result.query_id,
            query_type="step"
        )  
        default_interval.query_result = query_result  
        query_result.relevant_windows.append(default_interval)  
          
        self.command_factory.create_and_execute_step_add_query_result(  
            self.results_data_controller, query_result  
        )  
          
        self._load_step_data()  
        self.refresh_step_list()  
        self.stepAdded.emit()  
        self.dataChanged.emit()
        
    def _on_step_text_changed(self):  
        """ステップテキスト変更時の処理（遅延実行）"""  
        print(f"[DEBUG] _on_step_text_changed called, new text: {self.step_edit_text.text()}")  
        if self._step_timer is None:  
            self._step_timer = QTimer()  
            self._step_timer.timeout.connect(self.apply_step_changes)  
          
        self._step_timer.stop()  
        self._step_timer.setSingleShot(True)  
        self._step_timer.start(500)  
        print(f"[DEBUG] Timer started for 500ms")
      
    def _on_segment_changed(self):  
        """セグメント変更時の処理（遅延実行）"""  
        self._on_step_text_changed()  # 同じタイマーを使用  
      
    def apply_step_changes(self):  
        """ステップ変更を適用"""  
        print(f"[DEBUG] apply_step_changes called")  
        current_item = self.step_list.currentItem()  
        if current_item is None:  
            print(f"[DEBUG] ERROR: current_item is None")  
            return  
        if self.results_data_controller is None:  
            print(f"[DEBUG] ERROR: results_data_controller is None")  
            return  
        if self.command_factory is None:  
            print(f"[DEBUG] ERROR: command_factory is None")  
            return  
      
        index = current_item.data(1)  
        print(f"[DEBUG] Selected item index: {index}")  
      
        if index >= len(self.step_query_results):  
            print(f"[DEBUG] ERROR: index {index} >= step_query_results length {len(self.step_query_results)}")  
            return  
      
        query_result = self.step_query_results[index]  
        old_text = query_result.query_text.replace("Step:", "").strip()  
        new_text = self.step_edit_text.text()  
      
        print(f"[DEBUG] Text comparison - old: '{old_text}', new: '{new_text}'")  
        print(f"[DEBUG] Text changed: {old_text != new_text}")  
      
        # 時間変更の確認  
        time_changed = False  
        old_start = 0.0  
        old_end = 0.0  
        new_start = self.step_start_spin.value()  
        new_end = self.step_end_spin.value()  
      
        if query_result.relevant_windows:  
            interval = query_result.relevant_windows[0]  
            old_start = interval.start_time  
            old_end = interval.end_time  
            time_changed = (abs(old_start - new_start) > 0.01 or abs(old_end - new_end) > 0.01)  
      
        print(f"[DEBUG] Time comparison - old: start={old_start}, end={old_end}")  
        print(f"[DEBUG] Time comparison - new: start={new_start}, end={new_end}")  
        print(f"[DEBUG] Time changed: {time_changed}")  
      
        # テキスト変更の確認  
        text_changed = (old_text != new_text)  
      
        # 実際に変更があるかチェック  
        if not time_changed and not text_changed:  
            print(f"[DEBUG] No changes detected, returning early")  
            return  
      
        # テキスト変更の処理  
        if text_changed:  
            old_query_text = query_result.query_text  
            new_query_text = f"Step:{new_text}"  
            print(f"[DEBUG] Executing text modify command: '{old_query_text}' -> '{new_query_text}'")  
      
            if self.command_factory:  
                self.command_factory.create_and_execute_step_text_modify(  
                    query_result, old_query_text, new_query_text  
                )  
                print(f"[DEBUG] Text modify command executed")  
            else:  
                print(f"[DEBUG] ERROR: command_factory is None during text modify")  
      
        # セグメント変更の処理  
        if time_changed and query_result.relevant_windows:  
            interval = query_result.relevant_windows[0]  
            print(f"[DEBUG] Executing interval modify command: {old_start}->{new_start}, {old_end}->{new_end}")  
      
            if self.command_factory:  
                self.command_factory.create_and_execute_interval_modify(  
                    interval, old_start, old_end, new_start, new_end  
                )  
                print(f"[DEBUG] Interval modify command executed")  
            else:  
                print(f"[DEBUG] ERROR: command_factory is None during interval modify")  
      
        # 変更があった場合のみUI更新とシグナル発信  
        print(f"[DEBUG] Starting data refresh...")  
        self._load_step_data()  
        print(f"[DEBUG] _load_step_data completed, step_query_results count: {len(self.step_query_results)}")  
      
        self.refresh_step_list()  
        print(f"[DEBUG] refresh_step_list completed, step_list count: {self.step_list.count()}")  
      
        # 更新後のクエリテキストを確認  
        if index < len(self.step_query_results):  
            updated_query_result = self.step_query_results[index]  
            print(f"[DEBUG] Updated query_text: '{updated_query_result.query_text}'")  
        else:  
            print(f"[DEBUG] WARNING: index {index} out of range after refresh")  
      
        self.stepModified.emit()  
        self.dataChanged.emit()  
        print(f"[DEBUG] Signals emitted")
      
    def delete_step(self):  
        """選択されたステップを削除"""  
        current_item = self.step_list.currentItem()  
        if current_item is None or self.results_data_controller is None:  
            return  
          
        index = current_item.data(1)  
        if index >= len(self.step_query_results):  
            return  
          
        query_result = self.step_query_results[index]  
          
        if self.command_factory:  
            self.command_factory.create_and_execute_step_delete_query_result(  
                self.results_data_controller, query_result  
            )  
          
        self._load_step_data()  
        self.refresh_step_list()  
        self.stepDeleted.emit()  
        self.dataChanged.emit()  
      
    def select_step(self, step_text: str = None, step_index: int = None):  
        """指定されたステップを選択"""  
        if self.step_list is None:  
            return  
          
        for i in range(self.step_list.count()):  
            item = self.step_list.item(i)  
            if item is None:  
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
      
    def update_interval_realtime(self, new_start: float, new_end: float):  
        """ドラッグ中のリアルタイム更新"""  
        self._block_signals(True)  
        try:  
            self.step_start_spin.setValue(new_start)  
            self.step_end_spin.setValue(new_end)  
        finally:  
            self._block_signals(False)
      
    def get_step_query_results(self) -> List[QueryResults]:  
        """ステップ用QueryResultsを取得（ResultsDataControllerから）"""  
        if self.results_data_controller is None:  
            return []  
        return self.results_data_controller.get_step_query_results()  

    def set_current_query_results(self, query_result: QueryResults):  
        """現在のクエリ結果を設定（ResultsDataController設計に対応）"""  
        # Step用のQueryResultの場合のみ処理  
        if query_result and query_result.query_text.startswith("Step:"):  
            # 該当するステップを選択状態にする  
            step_text = query_result.query_text.replace("Step:", "").strip()  
            self.select_step(step_text=step_text)