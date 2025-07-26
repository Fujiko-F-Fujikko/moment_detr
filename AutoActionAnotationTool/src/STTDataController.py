# STTDataController.py (完全版)  
import json  
from pathlib import Path  
from typing import Dict, List
from dataclasses import asdict  
from PyQt6.QtCore import QObject, pyqtSignal  
  
from STTDataStructures import *  
from Results import QueryResults  
from VideoInfo import VideoInfo  
  
class STTDataController(QObject):  
    """STTデータセットの管理を担当するクラス"""  
      
    # シグナル定義  
    datasetUpdated = pyqtSignal()  
    stepAdded = pyqtSignal(str, str)  # video_name, step_text  
    stepModified = pyqtSignal(str, int, str)  # video_name, step_index, new_text  
    stepDeleted = pyqtSignal(str, int)  # video_name, step_index  
    actionAdded = pyqtSignal(str, str)  # video_name, action_text  
    exportCompleted = pyqtSignal(str)  # file_path  
      
    def __init__(self):  
        super().__init__()  
        self.stt_dataset = STTDataset()  
        self.action_id_counter = 1  
        self.step_id_counter = 1  
      
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
        if video_name not in self.stt_dataset.database:  
            return False  
          
        try:  
            video_data = self.stt_dataset.database[video_name]  
            if step_index >= len(video_data.steps):  
                return False  
              
            step = video_data.steps[step_index]  
              
            # テキスト変更  
            if new_text is not None:  
                step.step = new_text  
                step.id = self._get_or_create_step_category(new_text)  
              
            # セグメント変更  
            if new_segment is not None:  
                step.segment = new_segment  
                fps = video_data.fps  
                step.segment_frames = [int(new_segment[0] * fps), int(new_segment[1] * fps)]  
              
            # シグナル発信  
            if new_text is not None:  
                self.stepModified.emit(video_name, step_index, new_text)  
            self.datasetUpdated.emit()  
              
            return True  
              
        except Exception as e:  
            raise Exception(f"Failed to modify step: {str(e)}")  
      
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
      
    def export_to_json(self, file_path: str) -> bool:  
        """STTデータセットをJSONファイルにエクスポート"""  
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