# ResultsManager.py (修正版)  
from PyQt6.QtCore import QObject, pyqtSignal  
from PyQt6.QtWidgets import QComboBox, QListWidget, QListWidgetItem, QLabel  
from typing import List, Optional  
from Results import QueryResults, DetectionInterval  
from DataHandling import InferenceResultsLoader, InferenceResultsSaver  
from STTDataStructures import QueryParser, QueryValidationError  
  
class ResultsManager(QObject):  
    intervalSelected = pyqtSignal(object, int)  # (interval, index)  
    resultsUpdated = pyqtSignal(list)  # List[QueryResults]  
      
    def __init__(self):  
        super().__init__()  
        self.all_results = []  
        self.filtered_results = []  
        self.confidence_threshold = 0.0  
        self.inference_loader = InferenceResultsLoader()  
        self.inference_saver = InferenceResultsSaver()  
          
        # UI要素  
        self._hand_type_combo_widget = None  
        self._results_list_widget = None  
          
    def set_ui_components(self, hand_type_combo: QComboBox, results_list: QListWidget):  
        """UI要素を設定（hand type filter対応）"""  
        self._hand_type_combo_widget = hand_type_combo  
        self._results_list_widget = results_list  
          
        # 結果リストのクリックイベントを接続  
        if self._results_list_widget:  
            self._results_list_widget.itemClicked.connect(self.on_result_item_clicked)  
      
    def load_inference_results(self, json_path: str):  
        """推論結果を読み込み"""  
        try:  
            inference_results = self.inference_loader.load_from_json(json_path)  
            print(f"DEBUG: Loaded {len(inference_results.results)} results from {json_path}")  
            self.all_results = inference_results.results  
            self.filtered_results = self.all_results.copy()  
            print(f"DEBUG: all_results count: {len(self.all_results)}")  
            print(f"DEBUG: filtered_results count: {len(self.filtered_results)}")  
            self.update_results_display()  
            self.resultsUpdated.emit(self.all_results)  
        except Exception as e:  
            print(f"DEBUG: Error loading results: {e}")  
            raise e
      
    def update_filtered_results(self, filtered_results: List[QueryResults]):  
        """フィルタされた結果を更新"""  
        self.filtered_results = filtered_results  
        self.update_results_display()  
      
    def update_results_display(self):  
        """結果表示を更新"""  
        print(f"DEBUG: update_results_display called")  
        if not self._results_list_widget:  
            print("DEBUG: results_list_widget is None!")  
            return  
        
        print(f"DEBUG: Clearing results list, current item count: {self._results_list_widget.count()}")  
        self._results_list_widget.clear()  
        
        grouped_results = self._group_results_by_hand_type(self.filtered_results)  
        print(f"DEBUG: Grouped results: {[(k, len(v)) for k, v in grouped_results.items()]}")  
        
        total_items_added = 0  
        for hand_type, results in grouped_results.items():  
            if not results:  
                continue  
            
            print(f"DEBUG: Adding header for {hand_type}")  
            # ヘッダー追加...  
            total_items_added += 1  
            
            for result in results:  
                for i, interval in enumerate(result.relevant_windows):  
                    if interval.confidence_score >= self.confidence_threshold:  
                        print(f"DEBUG: Adding interval {i} for query '{result.query_text}'")  
                        # アイテム追加...  
                        total_items_added += 1  
        
        print(f"DEBUG: Total items added to list: {total_items_added}")
      
    def _group_results_by_hand_type(self, results: List[QueryResults]) -> dict:  
        """結果をhand type毎にグループ化"""  
        groups = {  
            "LeftHand": [],  
            "RightHand": [],  
            "BothHands": [],  
            "Steps": []  
        }  
          
        for result in results:  
            try:  
                hand_type, _ = QueryParser.validate_and_parse_query(result.query_text)  
                if hand_type == "LeftHand":  
                    groups["LeftHand"].append(result)  
                elif hand_type == "RightHand":  
                    groups["RightHand"].append(result)  
                elif hand_type == "BothHands":  
                    groups["BothHands"].append(result)  
                else:  # None  
                    groups["Steps"].append(result)  
            except QueryValidationError:  
                groups["Steps"].append(result)  
          
        return groups  
      
    def on_result_item_clicked(self, item: QListWidgetItem):  
        """結果アイテムがクリックされた時の処理"""  
        data = item.data(1)  
        if data and data.get('type') == 'interval':  
            interval = data['interval']  
            index = data['index']  
            self.intervalSelected.emit(interval, index)  
      
    def set_confidence_threshold(self, threshold: float):  
        """信頼度閾値を設定"""  
        self.confidence_threshold = threshold  
        self.update_results_display()  
      
    def get_all_results(self) -> List[QueryResults]:  
        """全ての結果を取得"""  
        return self.all_results  
      
    def get_filtered_results(self) -> List[QueryResults]:  
        """フィルタされた結果を取得"""  
        return self.filtered_results  
      
    def save_results(self, file_path: str):  
        """結果を保存"""  
        from Results import InferenceResults  
        inference_results = InferenceResults(  
            results=self.all_results,  
            timestamp=None,  
            model_info={},  
            video_path=None,  
            total_queries=len(self.all_results)  
        )  
        self.inference_saver.save_to_json(inference_results, file_path)