from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QListWidget, QListWidgetItem
from typing import List
from ResultsDataController import ResultsDataController
from Results import QueryResults


# ResultsDisplayManager.py (UI表示専用)  
class ResultsDisplayManager(QObject):  
    """推論結果の表示管理を担当するクラス"""  
      
    intervalSelected = pyqtSignal(object, int)  # (interval, index)  
      
    def __init__(self, results_data_controller: ResultsDataController):  
        super().__init__()  
        self.data_controller = results_data_controller  
        self._results_list_widget = None  
          
        # データコントローラーのシグナルに接続  
        self.data_controller.resultsFiltered.connect(self.update_display)  
      
    def set_ui_components(self, results_list: QListWidget):  
        """UI要素を設定"""  
        self._results_list_widget = results_list  
        if results_list:  
            results_list.itemClicked.connect(self.on_result_item_clicked)  
      
    def update_display(self, filtered_results: List[QueryResults]):  
        """表示を更新"""  
        if not self._results_list_widget:  
            return  
          
        self._results_list_widget.clear()  
        grouped_results = self.data_controller.group_results_by_hand_type(filtered_results)  
          
        for hand_type, results in grouped_results.items():  
            if not results:  
                continue  
              
            # ヘッダー追加  
            header_item = QListWidgetItem(f"=== {hand_type} ===")  
            header_item.setBackground(QColor(230, 230, 230))  
            header_item.setFlags(header_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)  
            self._results_list_widget.addItem(header_item)  
              
            # 区間アイテム追加  
            for result in results:  
                for i, interval in enumerate(result.relevant_windows):  
                    item_text = f"  {i+1}: {interval.start_time:.2f}s - {interval.end_time:.2f}s (conf: {interval.confidence_score:.4f})"  
                    item = QListWidgetItem(item_text)  
                    item.setData(1, {'type': 'interval', 'interval': interval, 'index': i})  
                    self._results_list_widget.addItem(item)  
      
    def on_result_item_clicked(self, item: QListWidgetItem):  
        """結果アイテムクリック処理"""  
        data = item.data(1)  
        if data and data.get('type') == 'interval':  
            interval = data['interval']  
            index = data['index']  
            self.intervalSelected.emit(interval, index)