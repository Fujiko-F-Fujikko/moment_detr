# ResultsDisplayManager.py (修正版)  
from PyQt6.QtWidgets import QListWidget, QListWidgetItem  
from PyQt6.QtCore import QObject, pyqtSignal, Qt  
from PyQt6.QtGui import QColor
from typing import Optional, List
from ResultsDataController import ResultsDataController  
from Results import QueryResults
from STTDataStructures import QueryParser, QueryValidationError

class ResultsDisplayManager(QObject):  
    """結果表示の管理を担当するクラス"""  
      
    # シグナル定義  
    intervalSelected = pyqtSignal(object, object, int)  # query_result  
      
    def __init__(self, results_controller: ResultsDataController):  
        super().__init__()  
        self.results_controller = results_controller  
        self.results_list: Optional[QListWidget] = None  
          
        # ResultsDataControllerのシグナル接続を修正  
        self.results_controller.resultsLoaded.connect(self.update_display)  
        self.results_controller.resultsFiltered.connect(self.update_display)  
        self.results_controller.resultsUpdated.connect(self.update_display)  
      
    def set_ui_components(self, results_list: QListWidget):  
        """UI要素を設定"""  
        self.results_list = results_list  
        if self.results_list:  
            self.results_list.itemClicked.connect(self._on_item_clicked)  
              
            # 初期表示を更新（データが既に読み込まれている場合）  
            if self.results_controller.is_results_loaded():  
                self.update_display()  
      
    def update_display(self, results=None):  
        """表示を更新（古い実装仕様に合わせて修正）"""  
        if not self.results_list:  
            return  
        
        # リストをクリア  
        self.results_list.clear()  
        
        # フィルタされた結果を取得  
        if results is None:  
            filtered_results = self.results_controller.get_filtered_results()  
        else:  
            filtered_results = results  
        
        # 手の種類別にグループ化  
        grouped_results = self._group_results_by_hand_type(filtered_results)  
        
        # 各手の種類ごとに表示  
        for hand_type, results in grouped_results.items():  
            if not results:  
                continue  
            
            # ヘッダーアイテムを追加  
            header_item = QListWidgetItem(f"=== {hand_type} ===")  
            header_item.setBackground(QColor(230, 230, 230))  
            header_item.setFlags(header_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)  
            self.results_list.addItem(header_item)  
            
            # 各クエリの区間を個別に表示  
            for result in results:  
                for i, interval in enumerate(result.relevant_windows):  
                    if interval.confidence_score >= self.results_controller.confidence_threshold:  
                        # 区間の詳細情報を表示  
                        item_text = f"  {i+1}: {interval.start_time:.2f}s - {interval.end_time:.2f}s (conf: {interval.confidence_score:.4f})"  
                        item = QListWidgetItem(item_text)  
                        item.setData(Qt.ItemDataRole.UserRole, {'query_result': result, 'interval': interval, 'index': i})  
                        self.results_list.addItem(item)
      
    def _on_item_clicked(self, item: QListWidgetItem):  
        """アイテムクリック時の処理"""  
        data = item.data(Qt.ItemDataRole.UserRole)  
        if data and isinstance(data, dict):  
            query_result = data.get('query_result')  
            interval = data.get('interval')  
            index = data.get('index', 0)  
            
            if query_result and interval is not None:  
                # 実際にクリックされた区間とインデックスを渡す  
                self.intervalSelected.emit(query_result, interval, index)  
                return  
        
        # フォールバック（古い形式のデータの場合）  
        query_result = item.data(Qt.ItemDataRole.UserRole)  
        if query_result:  
            self.intervalSelected.emit(query_result, None, 0)
      
    def select_result_by_query_text(self, query_text: str):  
        """クエリテキストで結果を選択"""  
        if not self.results_list:  
            return  
          
        for i in range(self.results_list.count()):  
            item = self.results_list.item(i)  
            query_result = item.data(Qt.ItemDataRole.UserRole)  
            if query_result and query_result.query_text == query_text:  
                self.results_list.setCurrentItem(item)  
                break  
      
    def force_refresh(self):  
        """強制的に表示を更新"""  
        self.update_display()

    def _group_results_by_hand_type(self, results: List[QueryResults]) -> dict:  
        """結果をhand type毎にグループ化（古い実装仕様）"""  
        groups = {  
            "LeftHand": [],  
            "RightHand": [],  
            "BothHands": [],  
            "Other": []  
        }  
        
        for result in results:  
            # Stepクエリの場合は検証をスキップ  
            if result.query_text.startswith("Step:"):  
                groups["Other"].append(result)  
                continue  
            
            try:  
                hand_type, _ = QueryParser.validate_and_parse_query(result.query_text)  
                if hand_type == "LeftHand":  
                    groups["LeftHand"].append(result)  
                elif hand_type == "RightHand":  
                    groups["RightHand"].append(result)  
                elif hand_type == "BothHands":  
                    groups["BothHands"].append(result)  
                else:  # None  
                    groups["Other"].append(result)  
            except QueryValidationError:  
                groups["Other"].append(result)  
        
        return groups

    def select_interval_in_list(self, target_interval):  
        """Detection Resultsリストで指定された区間を選択"""  
        if not self.results_list:  
            return  
        
        # 既存の選択をクリア  
        self.results_list.clearSelection()  
        
        for i in range(self.results_list.count()):  
            item = self.results_list.item(i)  
            data = item.data(Qt.ItemDataRole.UserRole)  
            if data and isinstance(data, dict) and 'interval' in data:  
                interval = data['interval']  
                if (abs(interval.start_time - target_interval.start_time) < 0.01 and   
                    abs(interval.end_time - target_interval.end_time) < 0.01):  
                    self.results_list.setCurrentItem(item)  
                    item.setSelected(True)  
                    self.results_list.scrollToItem(item, QListWidget.ScrollHint.PositionAtCenter)  
                    self.results_list.setFocus()  
                    return