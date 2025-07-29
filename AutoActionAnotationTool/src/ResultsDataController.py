# ResultsDataController.py (完全版)  
from PyQt6.QtCore import QObject, pyqtSignal  
from typing import List, Dict, Optional  
import json  
import os  
  
from DataClasses import QueryResults, InferenceResults, QueryParser, QueryValidationError, STTDataset, VideoData, ActionData, StepEntry, ActionCategory
from InferenceResultsLoaderSaver import InferenceResultsLoader, InferenceResultsSaver  
from Utilities import show_call_stack
  
class ResultsDataController(QObject):  
    """推論結果データの管理を担当するクラス（STTDataController機能統合版）"""  
      
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
        self.current_video_path: Optional[str] = None  
          
        # データ処理コンポーネント  
        self.inference_loader = InferenceResultsLoader()  
        self.inference_saver = InferenceResultsSaver()  
      
    # === 基本的なデータ管理機能 ===  
      
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
      
    def save_results(self, file_path: str):  
        """結果を保存"""  
        try:  
            inference_results = InferenceResults(results=self.all_results)  
            self.inference_saver.save_to_json(inference_results, file_path)  
        except Exception as e:  
            raise Exception(f"Failed to save results: {str(e)}")  
      
    def is_results_loaded(self) -> bool:  
        """結果が読み込まれているかチェック"""  
        return len(self.all_results) > 0  
      
    def get_filtered_results(self) -> List[QueryResults]:  
        """フィルタリングされた結果を取得"""  
        return self.filtered_results  
      
    def get_all_results(self) -> List[QueryResults]:  
        """全ての結果を取得"""  
        return self.all_results  
      
    # === フィルタリング機能 ===  
      
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
        filtered = []  
        for result in results:  
            # Stepクエリの場合は特別処理  
            if result.query_text.startswith("Step:"):  
                # Stepクエリは除外
                continue  
              
            try:  
                detected_hand_type, _ = QueryParser.validate_and_parse_query(result.query_text)  
                if detected_hand_type == hand_type or hand_type == "All":  
                    filtered.append(result)  
                elif hand_type == "Other" and detected_hand_type == "None":  
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
      
    # === ステップ管理機能 ===  
      
    def get_steps_count(self) -> int:  
        """指定された動画のステップ数を取得"""  
        step_results = [qr for qr in self.all_results   
                       if qr.query_text.startswith("Step:")]  
        return len(step_results)  
      
    def add_step_query_result(self, query_result: QueryResults):  
        """新しいステップ用QueryResultsを追加"""  
        self.all_results.append(query_result)  
        self._apply_current_filters()  
        self.resultsUpdated.emit(self.all_results)  
      
    def remove_step_query_result(self, query_result: QueryResults):  
        """ステップ用QueryResultsを削除"""  
        if query_result in self.all_results:  
            self.all_results.remove(query_result)  
            self._apply_current_filters()  
            self.resultsUpdated.emit(self.all_results)  
      
    def modify_step_segment(self, step_text: str, new_segment: list):  
        """ステップセグメントを修正"""  
        target_query_text = f"Step:{step_text}"  
          
        for query_result in self.all_results:  
            if query_result.query_text == target_query_text:  
                if query_result.relevant_windows:  
                    interval = query_result.relevant_windows[0]  
                    interval.start_time = new_segment[0]  
                    interval.end_time = new_segment[1]  
                    break  
          
        self._apply_current_filters()  
        self.resultsUpdated.emit(self.all_results)  
      
    def get_step_query_results(self) -> List[QueryResults]:  
        """ステップ用のQueryResultsを取得"""  
        return [qr for qr in self.all_results if qr.query_text.startswith("Step:")]  
      
    # === STTデータ変換・エクスポート機能 ===  
      
    def convert_to_stt_format(self) -> dict:  
        """現在のアノテーションデータをSTTデータ形式に変換"""  
        stt_dataset = STTDataset()  
          
        if not self.current_video_path:  
            return stt_dataset.__dict__  
          
        # 動画データの作成  
        video_name = os.path.basename(self.current_video_path)  
        video_data = VideoData()  
          
        # アクションデータの変換  
        action_results = [qr for qr in self.all_results if not qr.query_text.startswith("Step:")]  
        for query_result in action_results:  
            for interval in query_result.relevant_windows:  
                action_data = ActionData(  
                    action=query_result.query_text,  
                    id=query_result.query_id,  
                    segment=[interval.start_time, interval.end_time],  
                    segment_frames=[int(interval.start_time * 30), int(interval.end_time * 30)]  # 30fps仮定  
                )  
                video_data.actions.append(action_data)  
          
        # ステップデータの変換  
        step_results = [qr for qr in self.all_results if qr.query_text.startswith("Step:")]  
        for i, query_result in enumerate(step_results):  
            step_text = query_result.query_text.replace("Step:", "").strip()  
            segment = [0.0, 1.0]  # デフォルト値  
              
            if query_result.relevant_windows:  
                interval = query_result.relevant_windows[0]  
                segment = [interval.start_time, interval.end_time]  
              
            step_entry = StepEntry(  
                step=step_text,  
                id=i,  
                segment=segment,  
                segment_frames=[int(segment[0] * 30), int(segment[1] * 30)]  # 30fps仮定  
            )  
            video_data.steps.append(step_entry)  
          
        # データベースに追加  
        stt_dataset.database[video_name] = video_data  
          
        # カテゴリ情報の抽出（簡略化）  
        action_categories = set()  
        for query_result in action_results:  
            try:  
                hand_type, action = QueryParser.validate_and_parse_query(query_result.query_text)  
                action_categories.add(action)  
            except QueryValidationError:  
                action_categories.add(query_result.query_text)  
          
        # アクションカテゴリの設定  
        for i, category in enumerate(sorted(action_categories)):  
            stt_dataset.action_categories.append(  
                ActionCategory(id=i, name=category)  
            )  
          
        return stt_dataset.__dict__  
      
    def export_stt_data(self, file_path: str, stt_data: dict):  
        """STTデータをJSONファイルにエクスポート"""  
        try:  
            with open(file_path, 'w', encoding='utf-8') as f:  
                json.dump(stt_data, f, ensure_ascii=False, indent=2)  
        except Exception as e:  
            raise Exception(f"Failed to export STT data: {str(e)}")  
      
    # === 動画パス管理 ===  
      
    def set_current_video_path(self, video_path: str):  
        """現在の動画パスを設定"""  
        self.current_video_path = video_path  
      
    def get_current_video_path(self) -> Optional[str]:  
        """現在の動画パスを取得"""  
        return self.current_video_path  
      
    # === データ操作機能 ===  
      
    def add_query_result(self, query_result: QueryResults):  
        """新しいQueryResultを追加"""  
        self.all_results.append(query_result)  
        self._apply_current_filters()  
        self.resultsUpdated.emit(self.all_results)  
      
    def remove_query_result(self, query_result: QueryResults):  
        """QueryResultを削除"""  
        if query_result in self.all_results:  
            self.all_results.remove(query_result)  
            self._apply_current_filters()  
            self.resultsUpdated.emit(self.all_results)  
      
    def update_query_result(self, query_result: QueryResults):  
        """QueryResultを更新"""  
        # 既存のQueryResultを更新（参照渡しなので自動的に更新される）  
        self._apply_current_filters()  
        self.resultsUpdated.emit(self.all_results)  
      
    # === デバッグ・状態取得機能 ===  
      
    def get_current_state(self) -> dict:  
        """現在の状態を取得（デバッグ用）"""  
        return {  
            'total_results': len(self.all_results),  
            'filtered_results': len(self.filtered_results),  
            'confidence_threshold': self.confidence_threshold,  
            'hand_type_filter': self.current_hand_type_filter,  
            'current_video_path': self.current_video_path,  
            'step_count': len([qr for qr in self.all_results if qr.query_text.startswith("Step:")])  
        }