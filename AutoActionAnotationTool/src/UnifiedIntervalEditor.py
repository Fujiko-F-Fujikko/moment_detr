# UnifiedIntervalEditor.py  
import logging  
from typing import Optional, List  
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,   
                            QDoubleSpinBox, QComboBox, QLineEdit, QPushButton,  
                            QListWidget, QListWidgetItem, QGroupBox, QFormLayout)  
from PyQt6.QtCore import QTimer, pyqtSignal, QObject  
from PyQt6.QtGui import QFont  
  
from UnifiedDataController import UnifiedDataController  
from UnifiedInterval import UnifiedInterval  
  
logger = logging.getLogger(__name__)  
  
class UnifiedIntervalEditor(QWidget):  
    """統一された区間編集エディタ"""  
      
    # シグナル定義  
    intervalUpdated = pyqtSignal()  
    intervalDeleted = pyqtSignal()  
    intervalAdded = pyqtSignal()  
    dataChanged = pyqtSignal()  
      
    def __init__(self, data_controller: UnifiedDataController):  
        super().__init__()  
        self.data_controller = data_controller  
        self.current_interval: Optional[UnifiedInterval] = None  
        self.current_video_id: str = ""  
        self.is_initializing = False  
        self.editing_in_progress = False  
          
        # 値変更タイマー（連続変更を防ぐ）  
        self.value_change_timer = QTimer()  
        self.value_change_timer.setSingleShot(True)  
        self.value_change_timer.timeout.connect(self.apply_changes)  
          
        self.setup_ui()  
        self.setup_connections()  
          
        logger.info("UnifiedIntervalEditor initialized")  
      
    def setup_ui(self):  
        """UIを設定"""  
        layout = QVBoxLayout(self)  
          
        # 区間リスト  
        list_group = QGroupBox("区間リスト")  
        list_layout = QVBoxLayout(list_group)  
          
        self.interval_list = QListWidget()  
        list_layout.addWidget(self.interval_list)  
          
        layout.addWidget(list_group)  
          
        # 編集フォーム  
        edit_group = QGroupBox("区間編集")  
        form_layout = QFormLayout(edit_group)  
          
        # 区間タイプ選択  
        self.interval_type_combo = QComboBox()  
        self.interval_type_combo.addItems(["action", "step"])  
        form_layout.addRow("タイプ:", self.interval_type_combo)  
          
        # 時間設定  
        self.start_spinbox = QDoubleSpinBox()  
        self.start_spinbox.setRange(0.0, 9999.0)  
        self.start_spinbox.setDecimals(2)  
        self.start_spinbox.setSuffix(" 秒")  
        form_layout.addRow("開始時間:", self.start_spinbox)  
          
        self.end_spinbox = QDoubleSpinBox()  
        self.end_spinbox.setRange(0.0, 9999.0)  
        self.end_spinbox.setDecimals(2)  
        self.end_spinbox.setSuffix(" 秒")  
        form_layout.addRow("終了時間:", self.end_spinbox)  
          
        # 信頼度表示  
        self.confidence_label = QLabel("0.00")  
        form_layout.addRow("信頼度:", self.confidence_label)  
          
        # コンテンツテキスト  
        self.content_text_edit = QLineEdit()  
        form_layout.addRow("テキスト:", self.content_text_edit)  
          
        # アクション専用フィールド  
        self.action_fields_group = QGroupBox("アクション詳細")  
        action_form = QFormLayout(self.action_fields_group)  
          
        self.hand_combo = QComboBox()  
        self.hand_combo.addItems(["left", "right", "both"])  
        action_form.addRow("手:", self.hand_combo)  
          
        self.action_verb_edit = QLineEdit()  
        action_form.addRow("動作:", self.action_verb_edit)  
          
        self.manipulated_object_edit = QLineEdit()  
        action_form.addRow("操作対象:", self.manipulated_object_edit)  
          
        self.target_object_edit = QLineEdit()  
        action_form.addRow("目標:", self.target_object_edit)  
          
        self.tool_edit = QLineEdit()  
        action_form.addRow("道具:", self.tool_edit)  
          
        form_layout.addRow(self.action_fields_group)  
          
        layout.addWidget(edit_group)  
          
        # ボタン  
        button_layout = QHBoxLayout()  
          
        self.add_button = QPushButton("追加")  
        self.delete_button = QPushButton("削除")  
          
        button_layout.addWidget(self.add_button)  
        button_layout.addWidget(self.delete_button)  
          
        layout.addLayout(button_layout)  
          
        # 初期状態では編集フィールドを無効化  
        self.set_editing_enabled(False)  
      
    def setup_connections(self):  
        """シグナル・スロット接続を設定"""  
        # データコントローラーからの更新  
        self.data_controller.dataUpdated.connect(self.refresh_interval_list)  
        self.data_controller.intervalAdded.connect(self.refresh_interval_list)  
        self.data_controller.intervalModified.connect(self.refresh_interval_list)  
        self.data_controller.intervalDeleted.connect(self.refresh_interval_list)  
          
        # UI要素の変更  
        self.interval_type_combo.currentTextChanged.connect(self.on_interval_type_changed)  
        self.start_spinbox.valueChanged.connect(self.on_value_changed)  
        self.end_spinbox.valueChanged.connect(self.on_value_changed)  
        self.content_text_edit.textChanged.connect(self.on_value_changed)  
          
        # アクション詳細フィールド  
        self.hand_combo.currentTextChanged.connect(self.on_value_changed)  
        self.action_verb_edit.textChanged.connect(self.on_value_changed)  
        self.manipulated_object_edit.textChanged.connect(self.on_value_changed)  
        self.target_object_edit.textChanged.connect(self.on_value_changed)  
        self.tool_edit.textChanged.connect(self.on_value_changed)  
          
        # リスト選択  
        self.interval_list.itemClicked.connect(self.on_interval_selected)  
          
        # ボタン  
        self.add_button.clicked.connect(self.add_new_interval)  
        self.delete_button.clicked.connect(self.delete_interval)  
      
    def set_current_video(self, video_id: str):  
        """現在の動画を設定"""  
        self.current_video_id = video_id  
        logger.info(f"Set current video: {video_id}")  
        self.refresh_interval_list()  
      
    def set_selected_interval(self, interval: UnifiedInterval):  
        """選択された区間を設定"""  
        self.current_interval = interval  
        self.load_interval_to_ui(interval)  
        self.set_editing_enabled(True)  
        logger.info(f"Selected interval: {interval.interval_id}")  
      
    def clear_selection(self):  
        """選択をクリア"""  
        self.current_interval = None  
        self.clear_ui_fields()  
        self.set_editing_enabled(False)  
        logger.info("Cleared interval selection")  
      
    def refresh_interval_list(self):  
        """区間リストを更新"""  
        if not self.current_video_id:  
            return  
          
        self.interval_list.clear()  
        intervals = self.data_controller.get_intervals_for_video(self.current_video_id)  
          
        for interval in intervals:  
            item_text = f"[{interval.interval_type}] {interval.get_display_text()} ({interval.start_time:.2f}-{interval.end_time:.2f})"  
            item = QListWidgetItem(item_text)  
            item.setData(1, interval.interval_id)  # interval_idを保存  
            self.interval_list.addItem(item)  
          
        logger.info(f"Refreshed interval list: {len(intervals)} intervals")  
      
    def on_interval_type_changed(self):  
        """区間タイプ変更時の処理"""  
        if self.is_initializing:  
            return  
          
        interval_type = self.interval_type_combo.currentText()  
        self.update_ui_for_interval_type(interval_type)  
        self.on_value_changed()  
      
    def on_value_changed(self):  
        """値変更時の処理"""  
        if self.is_initializing or not self.current_interval:  
            return  
          
        # タイマーをリセットして遅延実行  
        self.value_change_timer.stop()  
        self.value_change_timer.start(500)  # 500ms後に適用  
      
    def apply_changes(self):  
        """変更を適用"""  
        if not self.current_interval or self.editing_in_progress:  
            return  
          
        self.editing_in_progress = True  
          
        try:  
            # UIから新しいデータを収集  
            new_data = {  
                'start_time': self.start_spinbox.value(),  
                'end_time': self.end_spinbox.value(),  
                'interval_type': self.interval_type_combo.currentText(),  
                'content_text': self.build_query_text_from_fields()  
            }  
              
            # データコントローラーに変更を送信  
            success = self.data_controller.modify_interval(  
                self.current_interval.interval_id, new_data  
            )  
              
            if success:  
                logger.info(f"Applied changes to interval: {self.current_interval.interval_id}")  
                self.intervalUpdated.emit()  
                self.dataChanged.emit()  
            else:  
                logger.error("Failed to apply changes")  
          
        except Exception as e:  
            logger.error(f"Error applying changes: {e}")  
          
        finally:  
            self.editing_in_progress = False  
      
    def add_new_interval(self):  
        """新しい区間を追加"""  
        if not self.current_video_id:  
            return  
          
        try:  
            interval_type = self.interval_type_combo.currentText()  
            start_time = self.start_spinbox.value()  
            end_time = self.end_spinbox.value()  
            content_text = self.build_query_text_from_fields()  
              
            if interval_type == "action":  
                interval = UnifiedInterval.create_action_interval(  
                    content_text, start_time, end_time, 1.0  
                )  
            else:  
                interval = UnifiedInterval.create_step_interval(  
                    content_text, start_time, end_time  
                )  
              
            interval.video_id = self.current_video_id  
              
            success = self.data_controller.add_interval(interval)  
              
            if success:  
                logger.info(f"Added new interval: {interval.interval_id}")  
                self.intervalAdded.emit()  
                self.dataChanged.emit()  
            else:  
                logger.error("Failed to add new interval")  
          
        except Exception as e:  
            logger.error(f"Error adding new interval: {e}")  
      
    def delete_interval(self):  
        """区間を削除"""  
        if not self.current_interval:  
            return  
          
        try:  
            success = self.data_controller.delete_interval(self.current_interval.interval_id)  
              
            if success:  
                logger.info(f"Deleted interval: {self.current_interval.interval_id}")  
                self.clear_selection()  
                self.intervalDeleted.emit()  
                self.dataChanged.emit()  
            else:  
                logger.error("Failed to delete interval")  
          
        except Exception as e:  
            logger.error(f"Error deleting interval: {e}")  
      
    def build_query_text_from_fields(self) -> str:  
        """フィールドからクエリテキストを構築"""  
        interval_type = self.interval_type_combo.currentText()  
          
        if interval_type == "step":  
            return self.content_text_edit.text()  
        # アクションの場合、各フィールドから構築  
        hand = self.hand_combo.currentText()  
        verb = self.action_verb_edit.text().strip()  
        manipulated = self.manipulated_object_edit.text().strip()  
        target = self.target_object_edit.text().strip()  
        tool = self.tool_edit.text().strip()  
          
        # 既存のクエリ形式に合わせて構築  
        parts = []  
        if hand:  
            parts.append(hand)  
        if verb:  
            parts.append(verb)  
        if manipulated:  
            parts.append(manipulated)  
        if target:  
            parts.append(f"to {target}")  
        if tool:  
            parts.append(f"with {tool}")  
          
        return " ".join(parts) if parts else self.content_text_edit.text()  
      
    def parse_query_text_to_fields(self, query_text: str):  
        """クエリテキストをフィールドに分解"""  
        if not query_text:  
            return  
          
        # 簡単なパース（既存のロジックを参考に）  
        text_lower = query_text.lower()  
          
        # 手の判定  
        if "left" in text_lower:  
            self.hand_combo.setCurrentText("left")  
        elif "right" in text_lower:  
            self.hand_combo.setCurrentText("right")  
        else:  
            self.hand_combo.setCurrentText("both")  
          
        # その他のフィールドは基本的にテキストフィールドに設定  
        self.content_text_edit.setText(query_text)  
      
    def update_ui_for_interval_type(self, interval_type: str):  
        """区間タイプに応じてUIを更新"""  
        if interval_type == "action":  
            self.action_fields_group.setVisible(True)  
        else:  
            self.action_fields_group.setVisible(False)  
      
    def load_interval_to_ui(self, interval: UnifiedInterval):  
        """区間データをUIに読み込み"""  
        self.is_initializing = True  
          
        try:  
            self.start_spinbox.setValue(interval.start_time)  
            self.end_spinbox.setValue(interval.end_time)  
            self.confidence_label.setText(f"{interval.confidence_score:.2f}")  
            self.interval_type_combo.setCurrentText(interval.interval_type)  
              
            # 区間タイプに応じてUI更新  
            self.update_ui_for_interval_type(interval.interval_type)  
              
            # テキストフィールドを設定  
            if interval.is_step_type():  
                self.content_text_edit.setText(interval.content_text)  
            else:  
                self.parse_query_text_to_fields(interval.content_text)  
          
        finally:  
            self.is_initializing = False  
      
    def clear_ui_fields(self):  
        """UIフィールドをクリア"""  
        self.is_initializing = True  
          
        try:  
            self.start_spinbox.setValue(0.0)  
            self.end_spinbox.setValue(0.0)  
            self.confidence_label.setText("0.00")  
            self.content_text_edit.clear()  
            self.action_verb_edit.clear()  
            self.manipulated_object_edit.clear()  
            self.target_object_edit.clear()  
            self.tool_edit.clear()  
            self.hand_combo.setCurrentIndex(0)  
          
        finally:  
            self.is_initializing = False  
      
    def set_editing_enabled(self, enabled: bool):  
        """編集フィールドの有効/無効を設定"""  
        self.start_spinbox.setEnabled(enabled)  
        self.end_spinbox.setEnabled(enabled)  
        self.interval_type_combo.setEnabled(enabled)  
        self.content_text_edit.setEnabled(enabled)  
        self.action_fields_group.setEnabled(enabled)  
        self.delete_button.setEnabled(enabled)  
      
    def on_interval_selected(self, item: QListWidgetItem):  
        """リストアイテム選択時の処理"""  
        interval_id = item.data(1)  
          
        # 対応する区間を検索  
        for interval in self.data_controller.get_intervals_for_video(self.current_video_id):  
            if interval.interval_id == interval_id:  
                self.set_selected_interval(interval)  
                break  
      
    def block_signals(self, block: bool):  
        """シグナルをブロック"""  
        self.start_spinbox.blockSignals(block)  
        self.end_spinbox.blockSignals(block)  
        self.interval_type_combo.blockSignals(block)  
        self.content_text_edit.blockSignals(block)  
        self.hand_combo.blockSignals(block)  
        self.action_verb_edit.blockSignals(block)  
        self.manipulated_object_edit.blockSignals(block)  
        self.target_object_edit.blockSignals(block)  
        self.tool_edit.blockSignals(block)        