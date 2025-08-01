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
          
        # データ処理コンポーネント  
        self.inference_loader = InferenceResultsLoader()  
        self.inference_saver = InferenceResultsSaver()  

    def load_inference_results(self, json_path: str) -> List[QueryResults]:  
        """推論結果を読み込み（Step含む）"""  
        try:  
            inference_results = self.inference_loader.load_from_json(json_path)  
              
            # ActionとStepを統合し、is_stepフラグを設定  
            all_results = []  
              
            # Action結果を追加  
            for result in inference_results.results:  
                result.is_step = False  
                all_results.append(result)  
              
            # Step結果を追加（is_step=Trueに設定）  
            if hasattr(inference_results, 'steps') and inference_results.steps:  
                for step_result in inference_results.steps:  
                    step_result.is_step = True  
                    all_results.append(step_result)  
              
            self.all_results = all_results  
            self.filtered_results = self.all_results.copy()  
              
            self._apply_current_filters()  
            self.resultsLoaded.emit(self.all_results)  
              
            return self.all_results  
              
        except Exception as e:  
            raise Exception(f"Failed to load inference results: {str(e)}")
      
    def set_confidence_threshold(self, threshold: float):  
        """信頼度閾値を設定"""  
        self.confidence_threshold = threshold  
        self._apply_current_filters()  
      
    def _apply_current_filters(self):  
        """現在のフィルタ設定を適用"""  
        # 信頼度フィルタを適用  
        self.filtered_results = self._filter_by_confidence(  
            self.all_results, self.confidence_threshold  
        )  
          
        # シグナル発信  
        self.resultsFiltered.emit(self.filtered_results)  
      
    def _filter_by_confidence(self, results: List[QueryResults], threshold: float) -> List[QueryResults]:  
        """信頼度でフィルタリング"""  
        filtered_results = []  
        for result in results:  
            # saliency_scoresが存在しない場合はそのまま通す  
            if not hasattr(result, 'saliency_scores'):  
                filtered_results.append(result)  
                continue
            if result.is_step:
                # ステップクエリは信頼度フィルタを適用しない
                filtered_results.append(result)
                continue

            # 信頼度閾値を満たす区間のみを含む新しいQueryResultsを作成  
            filtered_intervals = [  
                interval for interval in result.relevant_windows  
                if interval.confidence_score >= threshold  
            ]  
            
            # 新しいQueryResultsオブジェクトを作成（video_idを追加）  
            # 信頼度閾値を満たす区間がない場合でも、空のQueryResultsを保持
            filtered_result = QueryResults(  
                query_text=result.query_text,  
                video_id=result.video_id,
                relevant_windows=filtered_intervals, # 空のリストでも保持
                saliency_scores=result.saliency_scores,  
                query_id=result.query_id  
            )  
            filtered_results.append(filtered_result)  
        
        return filtered_results 
      
    def get_all_results(self) -> List[QueryResults]:  
        """全ての結果を取得"""  
        return self.all_results  
      
    def get_filtered_results(self) -> List[QueryResults]:  
        """フィルタされた結果を取得"""  
        return self.filtered_results  
   
    def is_results_loaded(self) -> bool:  
        """結果が読み込まれているかチェック"""  
        return len(self.all_results) > 0  
      
    def clear_results(self):  
        """全ての結果をクリア"""  
        self.all_results.clear()  
        self.filtered_results.clear()  
        self.confidence_threshold = 0.0  

    def update_result(self, query_result: QueryResults) -> bool:  
        """特定の結果を更新"""  
        try:  
            # all_resultsから該当する結果を検索して更新  
            for i, result in enumerate(self.all_results):  
                if (result.query_text == query_result.query_text and   
                    result.video_id == query_result.video_id):  
                    self.all_results[i] = query_result  
                    break  
              
            # フィルタを再適用  
            self._apply_current_filters()  
              
            # シグナル発信  
            self.resultsUpdated.emit(self.all_results)  
            return True  
              
        except Exception as e:  
            raise Exception(f"Failed to update result: {str(e)}")  
      
    def save_results(self, file_path: str) -> bool:  
        """結果をファイルに保存"""  
        try:  
            inference_results = InferenceResults(  
                results=self.all_results,  
                timestamp=None,  
                model_info={},  
                video_path=None,  
                total_queries=len(self.all_results)  
            )  
            self.inference_saver.save_to_json(inference_results, file_path)  
            return True  
              
        except Exception as e:  
            raise Exception(f"Failed to save results: {str(e)}")  

      
    def save_results_with_data(self, results_data: List[QueryResults], file_path: str) -> bool:  
        """指定されたデータを保存（ActionとStepを分離）"""  
        try:  
            # ActionとStepを分離  
            action_results = []  
            step_results = []  
              
            for result in results_data:  
                if result.query_text.startswith("Step:"):  
                    step_results.append(result)  
                else:  
                    action_results.append(result)  
              
            inference_results = InferenceResults(  
                results=action_results,  # Actionのみ  
                steps=step_results,      # Step専用フィールド  
                timestamp=None,  
                model_info={},  
                video_path=None,  
                total_queries=len(action_results)  
            )  
            self.inference_saver.save_to_json(inference_results, file_path)  
            return True  
              
        except Exception as e:  
            raise Exception(f"Failed to save results: {str(e)}")

    def add_result(self, query_result: QueryResults) -> bool:  
        """新しい結果を追加"""  
        try:  
            self.all_results.append(query_result)  
            self._apply_current_filters()  
            self.resultsUpdated.emit(self.all_results)  
            return True  
              
        except Exception as e:  
            raise Exception(f"Failed to add result: {str(e)}")  
      
    def remove_result(self, query_id: str) -> bool:  
        """結果を削除"""  
        try:  
            self.all_results = [r for r in self.all_results if r.query_id != query_id]  
            self._apply_current_filters()  
            self.resultsUpdated.emit(self.all_results)  
            return True  
              
        except Exception as e:  
            raise Exception(f"Failed to remove result: {str(e)}")  
      
    def get_result_by_id(self, query_id: str) -> Optional[QueryResults]:  
        """IDで結果を取得"""  
        for result in self.all_results:  
            if result.query_id == query_id:  
                return result  
        return None  
      
    def get_current_state(self) -> Dict:  
        """現在の状態を取得（デバッグ用）"""  
        return {  
            'total_results': len(self.all_results),  
            'filtered_results': len(self.filtered_results),  
            'confidence_threshold': self.confidence_threshold,  
            'is_loaded': self.is_results_loaded()  
        }