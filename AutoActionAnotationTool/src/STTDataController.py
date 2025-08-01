# STTDataController.py (完全版)  
import json  
from pathlib import Path  
from typing import Dict, List
from dataclasses import asdict  
from PyQt6.QtCore import QObject, pyqtSignal  
  
from DetectionInterval import DetectionInterval
from STTDataStructures import *  
from Results import QueryResults  
from VideoInfo import VideoInfo  
from Utilities import show_call_stack
  
class STTDataController(QObject):  
    """STTデータセットの管理を担当するクラス"""  
      
    # シグナル定義  
    datasetUpdated = pyqtSignal()  
    stepAdded = pyqtSignal(str, str)  # video_name, step_text  
    stepModified = pyqtSignal(str, int, str, float, float)  # video_name, step_index, new_text, new_segment_start, new_segment_end  
    stepDeleted = pyqtSignal(str, int)  # video_name, step_index  
    actionAdded = pyqtSignal(str, str)  # video_name, action_text  
    exportCompleted = pyqtSignal(str)  # file_path  
      
    def __init__(self, application_coordinator=None):  
        super().__init__()  
        self.stt_dataset = STTDataset()  
        self.action_id_counter = 1  
        self.step_id_counter = 1  
        self.application_coordinator = application_coordinator
        self.confidence_threshold = 0.0  # デフォルトの信頼度閾値
      
    def add_video_data(self, video_info: VideoInfo, subset: str = "train") -> bool:  
        """動画データを追加"""  
        try:  
            video_name = Path(video_info.file_path).stem  
            self.stt_dataset.database[video_name] = VideoData(  
                subset=subset,  
                duration=video_info.duration,  
                fps=video_info.fps  
            )  
            self.datasetUpdated.emit()  
            return True  
        except Exception as e:  
            raise Exception(f"Failed to add video data: {str(e)}")  
      
    def add_inference_results(self, video_name: str, inference_results: List[QueryResults]) -> List[str]:  
        """推論結果からアクションデータを生成"""  
        if video_name not in self.stt_dataset.database:  
            raise ValueError(f"Video {video_name} not found in dataset")  
          
        video_data = self.stt_dataset.database[video_name]  
        fps = video_data.fps  
        invalid_queries = []  
          
        for query_result in inference_results:  
            # ステップクエリの場合は検証をスキップ  
            if query_result.query_text.startswith("Step:"):  
                continue  
              
            try:  
                # クエリ検証とパース  
                hand_type_raw, action_data = QueryParser.validate_and_parse_query(query_result.query_text)  
                hand_type = QueryParser.detect_hand_type(query_result.query_text)  
                  
                # アクションカテゴリを追加/取得  
                action_id = self._get_or_create_action_category(query_result.query_text)  
                  
                # 各区間をアクションエントリとして追加  
                for interval in query_result.relevant_windows:  
                    segment = [interval.start_time, interval.end_time]  
                    segment_frames = [int(interval.start_time * fps), int(interval.end_time * fps)]  
                      
                    action_entry = ActionEntry(  
                        action=action_data,  
                        id=action_id,  
                        segment=segment,  
                        segment_frames=segment_frames  
                    )  
                      
                    # 手の種類に応じて適切なリストに追加  
                    if hand_type not in video_data.actions:  
                        video_data.actions[hand_type] = []  
                    video_data.actions[hand_type].append(action_entry)  
                      
            except QueryValidationError as e:  
                invalid_queries.append((query_result.query_text, str(e)))  
          
        if invalid_queries:  
            self.datasetUpdated.emit()  
          
        return invalid_queries  
      
    def add_step(self, video_name: str, step_text: str, segment: List[float]) -> bool:  
        """ステップを追加"""  
        if video_name not in self.stt_dataset.database:  
            return False  
          
        try:  
            video_data = self.stt_dataset.database[video_name]  
            fps = video_data.fps  
              
            step_id = self._get_or_create_step_category(step_text)  
            segment_frames = [int(segment[0] * fps), int(segment[1] * fps)]  
              
            step_entry = StepEntry(  
                step=step_text,  
                id=step_id,  
                segment=segment,  
                segment_frames=segment_frames  
            )  
              
            video_data.steps.append(step_entry)  
              
            # シグナル発信  
            self.stepAdded.emit(video_name, step_text)  
            self.datasetUpdated.emit()  
              
            return True  
              
        except Exception as e:  
            raise Exception(f"Failed to add step: {str(e)}")  
      
    def modify_step(self, video_name: str, step_index: int, new_text: str = None, new_segment: List[float] = None) -> bool:  
        """ステップを修正"""  
        print(f"Modifying step for video '{video_name}' at index {step_index} with new_text='{new_text}' and new_segment={new_segment}")
        if video_name not in self.stt_dataset.database:  
            print(f"Video '{video_name}' not found in dataset")
            return False  
            
        try:  
            video_data = self.stt_dataset.database[video_name]  
            if step_index >= len(video_data.steps):  
                return False  
                
            step = video_data.steps[step_index]  
            old_step_text = step.step  # 古いテキストを保存  
                
            # テキスト変更  
            if new_text is not None:  
                old_step_text = step.step  
                step.step = new_text  
                  
                # 新しいカテゴリIDを取得（既存があれば再利用）  
                new_category_id = self._get_or_create_step_category(new_text)  
                step.id = new_category_id  
                  
                # 古いカテゴリの処理（削除または保持）  
                self._update_step_category(old_step_text, new_text)
                
            # セグメント変更  
            if new_segment is not None:  
                step.segment = new_segment  
                fps = video_data.fps  
                step.segment_frames = [int(new_segment[0] * fps), int(new_segment[1] * fps)]  
                
            # シグナル発信    
            if new_text is not None:    
                # テキスト変更の場合は現在のセグメント情報を使用  
                current_segment = step.segment  
                self.stepModified.emit(video_name, step_index, new_text, current_segment[0], current_segment[1])  
            elif new_segment is not None:  
                # セグメント変更の場合  
                self.stepModified.emit(video_name, step_index, step.step, new_segment[0], new_segment[1])

            self.datasetUpdated.emit()  
                
            return True  
                
        except Exception as e:  
            raise Exception(f"Failed to modify step: {str(e)}")  
      
    def _update_step_category(self, old_text: str, new_text: str):  
        """ステップカテゴリを更新または削除する"""  
        print(f"Updating step category from '{old_text}' to '{new_text}'")  
          
        # 古いテキストに対応するカテゴリを検索  
        old_category = None  
        for category in self.stt_dataset.step_categories:  
            if category.step == old_text:  
                old_category = category  
                break  
          
        if old_category:  
            # 他のステップエントリで同じ古いテキストが使用されているかチェック  
            is_still_used = False  
            for video_data in self.stt_dataset.database.values():  
                for step_entry in video_data.steps:  
                    if step_entry.step == old_text and step_entry.id == old_category.id:  
                        is_still_used = True  
                        break  
                if is_still_used:  
                    break  
              
            # 他で使用されていない場合は、古いカテゴリを削除  
            if not is_still_used:  
                print(f"Removing unused category ID {old_category.id} with text '{old_text}'")  
                self.stt_dataset.step_categories.remove(old_category)  
            else:  
                print(f"Category '{old_text}' is still in use, not removing")
      
    def delete_step(self, video_name: str, step_index: int) -> bool:  
        """ステップを削除"""  
        if video_name not in self.stt_dataset.database:  
            return False  
          
        try:  
            video_data = self.stt_dataset.database[video_name]  
            if step_index >= len(video_data.steps):  
                return False  
              
            video_data.steps.pop(step_index)  
              
            # シグナル発信  
            self.stepDeleted.emit(video_name, step_index)  
            self.datasetUpdated.emit()  
              
            return True  
              
        except Exception as e:  
            raise Exception(f"Failed to delete step: {str(e)}")  
      
    def _get_or_create_action_category(self, query_text: str) -> int:  
        """アクションカテゴリを取得または作成"""  
        # 既存のカテゴリを検索  
        for category in self.stt_dataset.action_categories:  
            if category.interaction == query_text:  
                return category.id  
          
        # 新しいカテゴリを作成  
        new_category = ActionCategory(  
            id=self.action_id_counter,  
            interaction=query_text  
        )  
        self.stt_dataset.action_categories.append(new_category)  
        self.action_id_counter += 1  
          
        return new_category.id  
      
    def _get_or_create_step_category(self, step_text: str) -> int:  
        """ステップカテゴリを取得または作成"""  
        # 既存のカテゴリを検索  
        for category in self.stt_dataset.step_categories:  
            if category.step == step_text:  
                return category.id  
          
        # 新しいカテゴリを作成  
        new_category = StepCategory(  
            id=self.step_id_counter,  
            step=step_text  
        )  
        self.stt_dataset.step_categories.append(new_category)  
        self.step_id_counter += 1  
          
        return new_category.id  
      
    def update_video_subset(self, video_name: str, subset: str) -> bool:  
        """動画のサブセット設定を更新"""  
        if video_name not in self.stt_dataset.database:  
            return False  
          
        self.stt_dataset.database[video_name].subset = subset  
        self.datasetUpdated.emit()  
        return True  
      
    def export_to_json(self, file_path: str, confidence_threshold: float = 0.0):  
        """STTデータセットをJSONファイルにエクスポート"""  
        self.confidence_threshold = confidence_threshold  # 閾値を保存
        print(f"Exporting STT dataset to {file_path} with confidence threshold {confidence_threshold}")
        try:  
            # データセットを辞書に変換  
            dataset_dict = asdict(self.stt_dataset)  
              
            # JSONファイルに保存  
            with open(file_path, 'w', encoding='utf-8') as f:  
                json.dump(dataset_dict, f, ensure_ascii=False, indent=2)  
              
            self.exportCompleted.emit(file_path)  
            return True  
              
        except Exception as e:  
            raise Exception(f"Failed to export STT dataset: {str(e)}")  
      
    def get_dataset_info(self) -> Dict:  
        """データセット情報を取得"""  
        videos = list(self.stt_dataset.database.keys())  
        return {  
            'total_videos': len(videos),  
            'videos': videos,  
            'action_categories': len(self.stt_dataset.action_categories),  
            'step_categories': len(self.stt_dataset.step_categories)  
        }  
      
    def is_dataset_loaded(self) -> bool:  
        """データセットが読み込まれているかチェック"""  
        return len(self.stt_dataset.database) > 0

    def get_steps(self, video_name: str) -> List[StepEntry]:  
        """指定された動画のステップリストを取得"""  
        if video_name not in self.stt_dataset.database:  
            return []  
        return self.stt_dataset.database[video_name].steps

    def sync_from_results_data(self):  
        """ResultsDataControllerから最新の編集内容を同期"""  
        # ApplicationCoordinatorを通じてResultsDataControllerを取得  
        if not hasattr(self, 'application_coordinator'):  
            return  
          
        results_controller = self.application_coordinator.get_results_data_controller()  
        if not results_controller or not results_controller.is_results_loaded():  
            return  
          
        # 現在のフィルタリング済み結果を取得  
        current_results = results_controller.get_filtered_results()  
        if not current_results:  
            return  
          
        # 動画名を取得  
        video_name = self.application_coordinator.video_data_controller.get_video_name()  
        if not video_name:  
            return  
          
        # STTデータセットの該当VideoDataを更新  
        self._update_video_data_from_results(video_name, current_results)

    def _update_video_data_from_results(self, video_name: str, results: List[QueryResults]):  
        """QueryResultsからVideoDataを更新"""  
        # VideoDataが存在しない場合は作成  
        if video_name not in self.stt_dataset.database:  
            self.stt_dataset.database[video_name] = VideoData()  
          
        video_data = self.stt_dataset.database[video_name]  
          
        # 既存のアクションエントリをクリア（完全同期）  
        video_data.actions = {  
            "LeftHand": [],  
            "RightHand": [],  
            "BothHands": [],  
            "None": []  
        }  
          
        # 各QueryResultsを処理  
        for query_result in results:  
            self._process_query_result(video_data, query_result)

    def _process_query_result(self, video_data: VideoData, query_result: QueryResults):  
        """個別のQueryResultsを処理してActionEntryを作成（confidence閾値対応）"""  
        if query_result.query_text.startswith("Step:"):  
            return  
          
        try:  
            hand_type, action_data = QueryParser.validate_and_parse_query(query_result.query_text)  
            hand_category = QueryParser.detect_hand_type(query_result.query_text)  

            # アクションカテゴリを確実に作成  
            action_id = self._get_or_create_action_category(query_result.query_text)  
              
            # confidence閾値以上のintervalのみを処理  
            for interval in query_result.relevant_windows:  
                if interval.confidence_score >= self.confidence_threshold:  
                    action_entry = self._create_action_entry(action_data, interval)  
                    action_entry.id = action_id  # アクションIDを設定
                    video_data.actions[hand_category].append(action_entry)  
                      
        except QueryValidationError:  
            print(f"Failed to parse query: {query_result.query_text}")  
            # "_"で区切られていない場合、文章全体をaction_verbに設定  
            action_data = ActionData(  
                action_verb=query_result.query_text,  
                manipulated_object=None,  
                target_object=None,  
                tool=None  
            )  
              
            # デフォルトの手の種類を設定  
            hand_category = "unspecified"  
              
            # アクションカテゴリを作成  
            action_id = self._get_or_create_action_category(query_result.query_text)  
              
            # confidence閾値以上のintervalのみを処理  
            for interval in query_result.relevant_windows:  
                if interval.confidence_score >= self.confidence_threshold:  
                    action_entry = self._create_action_entry(action_data, interval)  
                    action_entry.id = action_id  
                    video_data.actions[hand_category].append(action_entry)

    def _create_action_entry(self, action_data: ActionData, interval: DetectionInterval) -> ActionEntry:  
        """DetectionIntervalからActionEntryを作成"""  
        # フレーム数の計算（FPSが設定されている場合）  
        fps = getattr(self.application_coordinator.video_data_controller, 'fps', 30.0)  
        start_frame = int(interval.start_time * fps)  
        end_frame = int(interval.end_time * fps)  
          
        return ActionEntry(  
            action=action_data,  
            ids=[],  # 必要に応じて設定  
            id=hash(f"{interval.start_time}_{interval.end_time}_{action_data.action_verb}"),  
            segment=[interval.start_time, interval.end_time],  
            segment_frames=[start_frame, end_frame]  
        )
