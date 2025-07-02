from typing import List
from PyQt6.QtWidgets import QDoubleSpinBox, QPushButton, QLabel, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal

from DetectionInterval import DetectionInterval


class IntervalEditController(QObject):
    """区間編集機能を担当するクラス"""
    
    # シグナル定義
    intervalUpdated = pyqtSignal()  # 区間が更新された
    intervalDeleted = pyqtSignal()  # 区間が削除された
    intervalAdded = pyqtSignal()    # 区間が追加された
    
    def __init__(self):
        super().__init__()
        self.selected_interval_index = None
        self.current_query_results = None
        
        # UI要素（外部で作成されたものを設定）
        self.start_spinbox = None
        self.end_spinbox = None
        self.confidence_label = None
        self.apply_button = None
        self.delete_button = None
        self.add_button = None
        
    def set_ui_components(self, start_spinbox: QDoubleSpinBox, end_spinbox: QDoubleSpinBox, 
                         confidence_label: QLabel, apply_button: QPushButton, 
                         delete_button: QPushButton, add_button: QPushButton):
        """UI要素を設定"""
        self.start_spinbox = start_spinbox
        self.end_spinbox = end_spinbox
        self.confidence_label = confidence_label
        self.apply_button = apply_button
        self.delete_button = delete_button
        self.add_button = add_button
        
        # シグナル接続
        self.apply_button.clicked.connect(self.apply_interval_changes)
        self.delete_button.clicked.connect(self.delete_interval)
        self.add_button.clicked.connect(self.add_new_interval)
        
    def set_current_query_results(self, query_results):
        """現在のクエリ結果を設定"""
        self.current_query_results = query_results
        
    def set_selected_interval(self, interval, index: int):
        """選択された区間を設定"""
        if not self.start_spinbox or not self.end_spinbox or not self.confidence_label:
            return
            
        self.selected_interval_index = index
        
        # エディタに値を設定
        self.start_spinbox.setValue(interval.start_time)
        self.end_spinbox.setValue(interval.end_time)
        
        # 信頼度ラベルを更新
        self.confidence_label.setText(f"{interval.confidence_score:.4f}")
        
    def apply_interval_changes(self):
        """区間の変更を適用"""
        if self.selected_interval_index is None or not self.current_query_results:
            return
            
        if not self.start_spinbox or not self.end_spinbox:
            return
            
        # 新しい値を取得
        new_start = self.start_spinbox.value()
        new_end = self.end_spinbox.value()
        
        # バリデーション
        if new_start >= new_end:
            QMessageBox.warning(None, "Warning", "Start time must be less than end time!")
            return
            
        # 結果を更新
        self.update_interval_in_results(self.selected_interval_index, new_start, new_end)
        self.intervalUpdated.emit()
        
    def delete_interval(self):
        """選択された区間を削除"""
        if self.selected_interval_index is None or not self.current_query_results:
            return
            
        reply = QMessageBox.question(
            None, "Confirm Delete", 
            "Are you sure you want to delete this interval?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.remove_interval_from_results(self.selected_interval_index)
            self.selected_interval_index = None
            self.intervalDeleted.emit()
            
    def add_new_interval(self):
        """新しい区間を追加"""
        if not self.current_query_results:
            return
            
        if not self.start_spinbox or not self.end_spinbox:
            return
            
        start_time = self.start_spinbox.value()
        end_time = self.end_spinbox.value()
        
        if start_time >= end_time:
            QMessageBox.warning(None, "Warning", "Start time must be less than end time!")
            return
            
        # 新しい区間を追加
        new_interval = [start_time, end_time, 1.0]  # デフォルト信頼度
        self.add_interval_to_results(new_interval)
        self.intervalAdded.emit()
        
    def update_interval_in_results(self, interval_index: int, new_start: float, new_end: float):
        """結果内の区間を更新"""
        if not self.current_query_results:
            return
            
        relevant_windows = self.current_query_results.relevant_windows
        if 0 <= interval_index < len(relevant_windows):
            interval = relevant_windows[interval_index]
            # DetectionIntervalオブジェクトの属性を更新
            interval.start_time = new_start
            interval.end_time = new_end
            # 信頼度は保持される
            
    def remove_interval_from_results(self, interval_index: int):
        """結果から区間を削除"""
        if not self.current_query_results:
            return
            
        relevant_windows = self.current_query_results.relevant_windows
        if 0 <= interval_index < len(relevant_windows):
            del relevant_windows[interval_index]
            
    def add_interval_to_results(self, new_interval: List[float]):
        """結果に新しい区間を追加"""
        if not self.current_query_results:
            return
            
        # 新しいDetectionIntervalオブジェクトを作成
        new_detection_interval = DetectionInterval(
            new_interval[0], new_interval[1], new_interval[2]
        )
        self.current_query_results.relevant_windows.append(new_detection_interval)
        
        # 信頼度でソート
        self.current_query_results.relevant_windows.sort(
            key=lambda x: x.confidence_score, reverse=True
        )
        
    def clear_selection(self):
        """選択状態をクリア"""
        self.selected_interval_index = None
        if self.start_spinbox:
            self.start_spinbox.setValue(0.0)
        if self.end_spinbox:
            self.end_spinbox.setValue(0.0)
        if self.confidence_label:
            self.confidence_label.setText("0.0000")
