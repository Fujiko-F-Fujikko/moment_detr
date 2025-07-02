from typing import List, Dict, Optional
from datetime import datetime
from PyQt6.QtWidgets import QComboBox, QListWidget, QLabel, QListWidgetItem
from PyQt6.QtCore import QObject, pyqtSignal

from DetectionInterval import DetectionInterval
from DataHandling import InferenceResultsLoader, InferenceResultsSaver


class ResultsManager(QObject):
    """推論結果の管理と表示を担当するクラス"""
    
    # シグナル定義
    querySelected = pyqtSignal(object)  # クエリが選択された
    intervalSelected = pyqtSignal(object, int)  # 区間が選択された（interval, index）
    resultsUpdated = pyqtSignal(list)  # 結果が更新された
    
    def __init__(self):
        super().__init__()
        self.inference_results = None
        self.current_query_results = None
        self.confidence_threshold = 0.0
        self.saliency_threshold = 0.0
        
        # データハンドリング
        self.inference_loader = InferenceResultsLoader()
        self.inference_saver = InferenceResultsSaver()
        
        # UI要素（外部で作成されたものを設定）
        self._query_combo_widget = None
        self._results_list_widget = None
        self._confidence_label_widget = None
        
    def set_ui_components(self, query_combo: QComboBox, results_list: QListWidget, confidence_label: QLabel):
        """UI要素を設定"""
        self._query_combo_widget = query_combo
        self._results_list_widget = results_list
        self._confidence_label_widget = confidence_label

        # シグナル接続
        if self._query_combo_widget is not None:
            try:
                self._query_combo_widget.currentTextChanged.connect(self.on_query_selected)
            except Exception:
                pass
        if self._results_list_widget is not None:
            try:
                self._results_list_widget.itemClicked.connect(self.on_result_selected)
            except Exception:
                pass
                
    @property
    def query_combo(self):
        """クエリコンボボックスのプロパティ"""
        return self._query_combo_widget
        
    @property
    def results_list(self):
        """結果リストのプロパティ"""
        return self._results_list_widget
        
    @property
    def confidence_label(self):
        """信頼度ラベルのプロパティ"""
        return self._confidence_label_widget
        
    def load_inference_results(self, json_path: str):  
        """推論結果を読み込む"""  
        # UI要素が設定されているかチェック  
        if self._query_combo_widget is None or self._results_list_widget is None:  
            return None  
              
        inference_results_obj = self.inference_loader.load_from_json(json_path)  
        self.inference_results = inference_results_obj.results  
          
        # まずクエリコンボボックスを更新  
        self.populate_query_combo()  
          
        # 最初のクエリを自動選択（もし存在すれば）  
        if self._query_combo_widget and self._query_combo_widget.count() > 0:  
            # 重要：setCurrentIndexを呼ぶ前にcurrent_query_resultsを設定  
            first_result = self.inference_results[0]  
            self.current_query_results = first_result  
              
            self._query_combo_widget.setCurrentIndex(0)  
            
            # 結果リストを更新  
            self.update_results_display()  
              
            # シグナルを発行  
            self.querySelected.emit(first_result)  
          
        # 外部に結果更新を通知  
        self.resultsUpdated.emit(self.inference_results)  
        return self.inference_results
        
    def save_results(self, file_path: str):
        """結果を保存"""
        if not self.inference_results:
            raise ValueError("No results to save")
            
        # 閾値以下の結果を除外して保存
        filtered_results = self.filter_results_by_confidence()
        self.inference_saver.save_to_json(filtered_results, file_path)
        
    def populate_query_combo(self):  
        """クエリコンボボックスを更新"""  
        if self._query_combo_widget is None:  
            return  
              
        self._query_combo_widget.clear()  
        if self.inference_results:  
            for result in self.inference_results:  
                query_text = result.query_text if hasattr(result, 'query_text') else f"Query {getattr(result, 'query_id', 'Unknown')}"  
                self._query_combo_widget.addItem(query_text)  
                
    def on_query_selected(self, query_text: str):  
        """クエリが選択された時の処理"""  
        if not self.inference_results:  
            return  
              
        # 選択されたクエリの結果を取得  
        for result in self.inference_results:  
            if (hasattr(result, 'query_text') and result.query_text == query_text):  
                self.current_query_results = result  
                self.update_results_display()  
                self.querySelected.emit(result)  
                break  
                
    def update_results_display(self):  
        """結果リストを更新"""  
        # より厳密なチェック：Noneチェックと有効性チェック  
        if self._results_list_widget is None:  
            return  
              
        # PyQt6ウィジェットの有効性をチェック  
        try:  
            # ウィジェットが有効かどうかをテスト  
            self._results_list_widget.count()  
        except RuntimeError:  
            print(f"ERROR: _results_list_widget is invalid: {e}") 
            return  
              
        if self.current_query_results is None:  
            return  
              
        self._results_list_widget.clear()  
          
        # QueryResultsオブジェクトのrelevant_windowsを使用  
        for i, interval in enumerate(self.current_query_results.relevant_windows):  
            start, end, confidence = interval.start_time, interval.end_time, interval.confidence_score  
            item_text = f"{i+1}: {start:.2f}s - {end:.2f}s (conf: {confidence:.4f})"  
            self._results_list_widget.addItem(item_text)  
            
    def on_result_selected(self, item: QListWidgetItem):
        """結果リストのアイテムが選択された時の処理"""
        if not self.current_query_results or not self._results_list_widget:
            return
            
        # 選択されたアイテムのインデックスを取得
        row = self._results_list_widget.row(item)
        relevant_windows = self.current_query_results.relevant_windows
        
        if 0 <= row < len(relevant_windows):
            interval = relevant_windows[row]
            
            # 信頼度ラベルを更新
            if self._confidence_label_widget:
                self._confidence_label_widget.setText(f"{interval.confidence_score:.4f}")
                
            # 外部に選択通知
            self.intervalSelected.emit(interval, row)
            
    def set_confidence_threshold(self, threshold: float):
        """信頼度閾値を設定"""
        self.confidence_threshold = threshold
        
    def set_saliency_threshold(self, threshold: float):
        """顕著性閾値を設定"""
        self.saliency_threshold = threshold
        
    def get_filtered_results(self):
        """フィルタが適用された結果を取得"""
        if not self.inference_results:
            return []
            
        filtered_results = []
        
        for result in self.inference_results:
            if hasattr(result, 'relevant_windows'):
                # 信頼度フィルタリング
                filtered_intervals = [
                    interval for interval in result.relevant_windows 
                    if interval.confidence_score >= self.confidence_threshold
                ]
                
                # 顕著性スコアフィルタリング
                filtered_saliency = [
                    score if score >= self.saliency_threshold else -1.0 
                    for score in result.saliency_scores
                ]
                
                # フィルタされた結果を作成
                from Results import QueryResults
                filtered_result = QueryResults(
                    query_text=result.query_text,
                    video_id=result.video_id,
                    relevant_windows=filtered_intervals,
                    saliency_scores=filtered_saliency,
                    query_id=result.query_id
                )
                filtered_results.append(filtered_result)
            else:
                # 辞書形式の場合（後方互換性）
                pred_windows = result.get('pred_relevant_windows', [])
                filtered_windows = [
                    window for window in pred_windows 
                    if len(window) >= 3 and window[2] >= self.confidence_threshold
                ]
                
                saliency_scores = result.get('pred_saliency_scores', [])
                filtered_saliency = [
                    score if score >= self.saliency_threshold else -1.0 
                    for score in saliency_scores
                ]
                
                filtered_result = result.copy()
                filtered_result['pred_relevant_windows'] = filtered_windows
                filtered_result['pred_saliency_scores'] = filtered_saliency
                filtered_results.append(filtered_result)
                
        return filtered_results
        
    def filter_results_by_confidence(self):
        """閾値以下の結果を除外"""
        if not self.inference_results:
            from Results import InferenceResults
            return InferenceResults(results=[], timestamp=datetime.now(), model_info={})
            
        filtered_results = []
        for result in self.inference_results:
            if hasattr(result, 'relevant_windows'):
                # 信頼度閾値でフィルタリング
                filtered_intervals = [
                    interval for interval in result.relevant_windows 
                    if interval.confidence_score >= self.confidence_threshold
                ]
                
                # フィルタされた結果を作成
                from Results import QueryResults
                filtered_result = QueryResults(
                    query_text=result.query_text,
                    video_id=result.video_id,
                    relevant_windows=filtered_intervals,
                    saliency_scores=result.saliency_scores,
                    query_id=result.query_id
                )
                filtered_results.append(filtered_result)
            else:
                # 辞書形式の場合（後方互換性）
                pred_windows = result.get('pred_relevant_windows', [])
                filtered_windows = [
                    window for window in pred_windows 
                    if len(window) >= 3 and window[2] >= self.confidence_threshold
                ]
                
                filtered_result = result.copy()
                filtered_result['pred_relevant_windows'] = filtered_windows
                filtered_results.append(filtered_result)
        
        # InferenceResultsオブジェクトを作成して返す
        from Results import InferenceResults
        return InferenceResults(
            results=filtered_results,
            timestamp=datetime.now(),
            model_info={"filtered": True},
            video_path=None,
            total_queries=len(filtered_results)
        )
        
    def select_interval_in_list(self, clicked_interval, query_result):
        """結果リストで指定された区間を選択"""
        if not self._results_list_widget:
            return
            
        # query_resultもQueryResultsオブジェクトの場合
        if hasattr(query_result, 'relevant_windows'):
            relevant_windows = query_result.relevant_windows
        else:
            # 辞書形式の場合（後方互換性）
            relevant_windows = []
            pred_windows = query_result.get('pred_relevant_windows', [])
            for window in pred_windows:
                if len(window) >= 3:
                    relevant_windows.append(DetectionInterval(window[0], window[1], window[2]))
        
        for i, interval in enumerate(relevant_windows):
            # クリックされた区間と一致するかチェック
            if (abs(interval.start_time - clicked_interval.start_time) < 0.1 and 
                abs(interval.end_time - clicked_interval.end_time) < 0.1):
                # リストアイテムを選択
                self._results_list_widget.setCurrentRow(i)
                # 詳細情報を更新
                self.on_result_selected(self._results_list_widget.item(i))
                break
                
    def get_current_query_results(self):
        """現在のクエリ結果を取得"""
        return self.current_query_results
        
    def get_all_results(self):
        """全ての推論結果を取得"""
        return self.inference_results
