# ResultsManager.py (修正版)  
from PyQt6.QtCore import Qt, QObject, pyqtSignal  
from PyQt6.QtWidgets import QComboBox, QListWidget, QListWidgetItem
from PyQt6.QtGui import QColor
from typing import List  
from Results import QueryResults  
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
        print(f"DEBUG: set_ui_components called with results_list: {results_list}")  
        self._hand_type_combo_widget = hand_type_combo    
        self._results_list_widget = results_list    
        print(f"DEBUG: After setting, self._results_list_widget: {self._results_list_widget}")           

        # 結果リストのクリックイベントを接続  
        if self._results_list_widget is not None:  
        # カスタムスタイルシートを適用  
            self._results_list_widget.setStyleSheet("""  
                QListWidget::item:selected {  
                    background-color: #3daee9;  
                    color: white;  
                    border: 2px solid #2980b9;  
                }  
                QListWidget::item:hover {  
                    background-color: #e3f2fd;  
                }  
            """)  
            print("DEBUG: Connecting itemClicked signal")  
            self._results_list_widget.itemClicked.connect(self.on_result_item_clicked)  
            print("DEBUG: Signal connected successfully")  
            # 追加：マウスプレスイベントも監視  
            self._results_list_widget.mousePressEvent = self.debug_mouse_press 
        else:  
            print("DEBUG: results_list_widget is None, cannot connect signal")
      
    def debug_mouse_press(self, event):  
        """マウスプレスイベントのデバッグ"""  
        print(f"DEBUG: Mouse press event on results list at position: {event.position()}")  
        item = self._results_list_widget.itemAt(event.position().toPoint())  
        if item:  
            print(f"DEBUG: Clicked item: {item.text()}")  
        else:  
            print("DEBUG: No item at click position")  
        # 元のイベント処理を呼び出し  
        QListWidget.mousePressEvent(self._results_list_widget, event)

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
        #print(f"DEBUG: update_results_display called")  
        
        # より詳細なチェックを追加  
        if self._results_list_widget is None:  
            print("DEBUG: results_list_widget is None!")  
            return  
        
        #print(f"DEBUG: Clearing results list, current item count: {self._results_list_widget.count()}")  
        self._results_list_widget.clear()  
        
        grouped_results = self._group_results_by_hand_type(self.filtered_results)  
        #print(f"DEBUG: Grouped results: {[(k, len(v)) for k, v in grouped_results.items()]}")  
        
        total_items_added = 0  
        for hand_type, results in grouped_results.items():  
            if not results:  
                continue  
            
            #print(f"DEBUG: Adding header for {hand_type}")  
            
            # ヘッダーアイテムを実際に追加  
            header_item = QListWidgetItem(f"=== {hand_type} ===")  
            header_item.setBackground(QColor(230, 230, 230))  
            header_item.setFlags(header_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)  
            self._results_list_widget.addItem(header_item)  
            total_items_added += 1  
            
            for result in results:  
                for i, interval in enumerate(result.relevant_windows):  
                    if interval.confidence_score >= self.confidence_threshold:  
                        #print(f"DEBUG: Adding interval {i} for query '{result.query_text}'")  
                        
                        # 区間アイテムを実際に追加  
                        item_text = f"  {i+1}: {interval.start_time:.2f}s - {interval.end_time:.2f}s (conf: {interval.confidence_score:.4f})"  
                        item = QListWidgetItem(item_text)  
                        item.setData(1, {'type': 'interval', 'interval': interval, 'index': i})  
                        self._results_list_widget.addItem(item)  
                        total_items_added += 1  
                        
                        self._results_list_widget.addItem(item)

        #print(f"DEBUG: Total items added to list: {total_items_added}")
      
    def _group_results_by_hand_type(self, results: List[QueryResults]) -> dict:  
        """結果をhand type毎にグループ化"""  
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
                else: # None  
                    groups["Other"].append(result)  
            except QueryValidationError:  
                groups["Other"].append(result)
          
        return groups  
      
    def on_result_item_clicked(self, item: QListWidgetItem):  
        """結果アイテムがクリックされた時の処理"""  
        print(f"DEBUG: ResultsManager - Item clicked: {item.text()}")  
        data = item.data(1)  
        if data and data.get('type') == 'interval':  
            interval = data['interval']  
            index = data['index']  
            print(f"DEBUG: ResultsManager - Emitting intervalSelected for interval {interval.start_time}-{interval.end_time}")  
            self.intervalSelected.emit(interval, index)

    def select_interval_in_list(self, target_interval):  
        """Detection Resultsリストで指定された区間を選択"""  
        print(f"DEBUG: ResultsManager - select_interval_in_list called for {target_interval.start_time}-{target_interval.end_time}")  
        
        # 既存の選択をクリア  
        self._results_list_widget.clearSelection()  
        
        for i in range(self._results_list_widget.count()):  
            item = self._results_list_widget.item(i)  
            data = item.data(1)  
            if data and data.get('type') == 'interval':  
                interval = data['interval']  
                if (interval.start_time == target_interval.start_time and   
                    interval.end_time == target_interval.end_time):  
                    print(f"DEBUG: ResultsManager - Found matching interval, selecting item {i}")  
                    
                    # 選択状態を設定  
                    self._results_list_widget.setCurrentItem(item)  
                    item.setSelected(True)  
                    
                    # スクロールして表示  
                    self._results_list_widget.scrollToItem(item, QListWidget.ScrollHint.PositionAtCenter)  
                    
                    # フォーカスを設定  
                    self._results_list_widget.setFocus()  
                    return
      
    print(f"DEBUG: ResultsManager - No matching interval found in list")

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