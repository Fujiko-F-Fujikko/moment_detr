# ResultsDataController.py  
from PyQt6.QtCore import QObject, pyqtSignal  
from typing import List, Dict, Optional  
from Results import QueryResults, InferenceResults  
from DataHandling import InferenceResultsLoader, InferenceResultsSaver  
from STTDataStructures import QueryParser, QueryValidationError  
  
class ResultsDataController(QObject):  
    """推論結果データの管理を担当するクラス"""  
      
    # シグナル定義  
    resultsLoaded = pyqtSignal(list)  # List[QueryResults]  
    resultsFiltered = pyqtSignal(list)  # List[QueryResults]  
    resultsUpdated = pyqtSignal(list)  # List[QueryResults]  
      
    def __init__(self):  
        super().__init__()  
        self.all_results: List[QueryResults] = []  
        self.filtered_results: List[QueryResults] = []  
        self.confidence_threshold: float = 0.0  
        self.current_hand_type_filter: str = "All"  
          
        # データ処理コンポーネント  
        self.inference_loader = InferenceResultsLoader()  
        self.inference_saver = InferenceResultsSaver()  
      
    def load_inference_results(self, json_path: str) -> List[QueryResults]:  
        """推論結果を読み込み"""  
        try:  
            inference_results = self.inference_loader.load_from_json(json_path)  
            self.all_results = inference_results.results  
            self.filtered_results = self.all_results.copy()  
              
            # フィルタを適用  
            self._apply_current_filters()  
              
            # シグナル発信  
            self.resultsLoaded.emit(self.all_results)  
              
            return self.all_results  
              
        except Exception as e:  
            raise Exception(f"Failed to load inference results: {str(e)}")  
      
    def set_confidence_threshold(self, threshold: float):  
        """信頼度閾値を設定"""  
        self.confidence_threshold = threshold  
        self._apply_current_filters()  
      
    def set_hand_type_filter(self, hand_type: str):  
        """Hand Typeフィルタを設定"""  
        self.current_hand_type_filter = hand_type  
        self._apply_current_filters()  
      
    def _apply_current_filters(self):  
        """現在のフィルタ設定を適用"""  
        # Hand Typeフィルタを適用  
        if self.current_hand_type_filter == "All":  
            filtered_by_hand_type = self.all_results.copy()  
        else:  
            filtered_by_hand_type = self._filter_by_hand_type(  
                self.all_results, self.current_hand_type_filter  
            )  
          
        # 信頼度フィルタを適用  
        self.filtered_results = self._filter_by_confidence(  
            filtered_by_hand_type, self.confidence_threshold  
        )  
          
        # シグナル発信  
        self.resultsFiltered.emit(self.filtered_results)  
      
    def _filter_by_hand_type(self, results: List[QueryResults], hand_type: str) -> List[QueryResults]:  
        """Hand Type別にフィルタリング"""  
        if hand_type == "All":  
            return results  
          
        filtered = []  
        for result in results:  
            # Stepクエリの場合は特別処理  
            if result.query_text.startswith("Step:"):  
                if hand_type == "Other":  
                    filtered.append(result)  
                continue  
              
            try:  
                detected_hand_type, _ = QueryParser.validate_and_parse_query(result.query_text)  
                if detected_hand_type == hand_type:  
                    filtered.append(result)  
                elif hand_type == "Other" and detected_hand_type is None:  
                    filtered.append(result)  
            except QueryValidationError:  
                if hand_type == "Other":  
                    filtered.append(result)  
          
        return filtered  
      
    def _filter_by_confidence(self, results: List[QueryResults], threshold: float) -> List[QueryResults]:  
        """信頼度でフィルタリング"""  
        filtered_results = []  
        for result in results:  
            # 信頼度閾値を満たす区間のみを含む新しいQueryResultsを作成  
            filtered_intervals = [  
                interval for interval in result.relevant_windows  
                if interval.confidence_score >= threshold  
            ]  
              
            if filtered_intervals:  
                # 新しいQueryResultsオブジェクトを作成  
                filtered_result = QueryResults(  
                    query_id=result.query_id,  
                    query_text=result.query_text,  
                    relevant_windows=filtered_intervals,  
                    saliency_scores=result.saliency_scores  
                )  
                filtered_results.append(filtered_result)  
          
        return filtered_results  
      
    def group_results_by_hand_type(self, results: Optional[List[QueryResults]] = None) -> Dict[str, List[QueryResults]]:  
        """結果をHand Type毎にグループ化"""  
        if results is None:  
            results = self.filtered_results  
          
        groups = {  
            "LeftHand": [],  
            "RightHand": [],  
            "BothHands": [],  
            "Other": []  
        }  
          
        for result in results:  
            # Stepクエリの場合  
            if result.query_text.startswith("Step:"):  
                groups["Other"].append(result)  
                continue  
              
            try:  
                hand_type, _ = QueryParser.validate_and_parse_query(result.query_text)  
                if hand_type in groups:  
                    groups[hand_type].append(result)  
                else:  
                    groups["Other"].append(result)  
            except QueryValidationError:  
                groups["Other"].append(result)  
          
        return groups  
      
    def get_all_results(self) -> List[QueryResults]:  
        """全ての結果を取得"""  
        return self.all_results  
      
    def get_filtered_results(self) -> List[QueryResults]:  
        """フィルタされた結果を取得"""  
        return self.filtered_results  
      
    def save_results(self, file_path: str):  
        """結果を保存"""  
        inference_results = InferenceResults(  
            results=self.all_results,  
            timestamp=None,  
            model_info={},  
            video_path=None,  
            total_queries=len(self.all_results)  
        )  
        self.inference_saver.save_to_json(inference_results, file_path)  
      
    def update_result(self, updated_result: QueryResults):  
        """特定の結果を更新"""  
        for i, result in enumerate(self.all_results):  
            if result.query_id == updated_result.query_id:  
                self.all_results[i] = updated_result  
                break  
          
        # フィルタを再適用  
        self._apply_current_filters()  
          
        # シグナル発信  
        self.resultsUpdated.emit(self.all_results)  
      
    def is_results_loaded(self) -> bool:  
        """結果が読み込まれているかチェック"""  
        return len(self.all_results) > 0  
      
    def clear_results(self):  
        """全ての結果をクリア"""  
        self.all_results.clear()  
        self.filtered_results.clear()  
        self.confidence_threshold = 0.0  
        self.current_hand_type_filter = "All"