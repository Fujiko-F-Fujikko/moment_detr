# STTDataController.py  
import json  
from pathlib import Path  
from typing import Dict, List, Optional  
from datetime import datetime  
from dataclasses import asdict  
from PyQt6.QtCore import QObject, pyqtSignal  
  
from STTDataStructures import *  
from Results import QueryResults, InferenceResults  
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
              
            del video_data.steps[step_index]  
              
            # シグナル発信  
            self.stepDeleted.emit(video_name, step_index)  
            self.datasetUpdated.emit()  
              
            return True  
              
        except Exception as e:  
            raise Exception(f"Failed to delete step: {str(e)}")  
      
    def get_video_steps(self, video_name: str) -> List[StepEntry]:  
        """指定動画のステップ一覧を取得"""  
        if video_name in self.stt_dataset.database:  
            return self.stt_dataset.database[video_name].steps  
        return []  
      
    def get_video_actions(self, video_name: str) -> Dict[str, List[ActionEntry]]:  
        """指定動画のアクション一覧を取得"""  
        if video_name in self.stt_dataset.database:  
            return self.stt_dataset.database[video_name].actions  
        return {}  
      
    def update_video_subset(self, video_name: str, subset: str) -> bool:  
        """動画のサブセットを更新"""  
        if video_name in self.stt_dataset.database:  
            self.stt_dataset.database[video_name].subset = subset  
            self.datasetUpdated.emit()  
            return True  
        return False  
      
    def export_to_json(self, file_path: str) -> bool:  
        """STT Dataset形式でJSONエクスポート"""  
        try:  
            # データ作成日時を更新  
            self.stt_dataset.info["data_created"] = datetime.now().strftime("%Y/%m/%d")  
              
            # データクラスを辞書に変換  
            data_dict = asdict(self.stt_dataset)  
              
            with open(file_path, 'w', encoding='utf-8') as f:  
                json.dump(data_dict, f, indent=2, ensure_ascii=False)  
              
            # シグナル発信  
            self.exportCompleted.emit(file_path)  
              
            return True  
              
        except Exception as e:  
            raise Exception(f"Failed to export dataset: {str(e)}")  
      
    def _get_or_create_action_category(self, interaction: str) -> int:  
        """アクションカテゴリを取得または作成"""  
        for category in self.stt_dataset.action_categories:  
            if category.interaction == interaction:  
                return category.id  
          
        new_id = self.action_id_counter  
        self.action_id_counter += 1  
          
        self.stt_dataset.action_categories.append(  
            ActionCategory(id=new_id, interaction=interaction)  
        )  
        return new_id  
      
    def _get_or_create_step_category(self, step: str) -> int:  
        """ステップカテゴリを取得または作成"""  
        for category in self.stt_dataset.step_categories:  
            if category.step == step:  
                return category.id  
          
        new_id = self.step_id_counter  
        self.step_id_counter += 1  
          
        self.stt_dataset.step_categories.append(  
            StepCategory(id=new_id, step=step)  
        )  
        return new_id  
      
    def get_dataset_info(self) -> Dict:  
        """データセット情報を取得"""  
        return {  
            'total_videos': len(self.stt_dataset.database),  
            'total_action_categories': len(self.stt_dataset.action_categories),  
            'total_step_categories': len(self.stt_dataset.step_categories),  
            'videos': list(self.stt_dataset.database.keys())  
        }  
      
    def clear_dataset(self):  
        """データセットをクリア"""  
        self.stt_dataset = STTDataset()  
        self.action_id_counter = 1  
        self.step_id_counter = 1  
        self.datasetUpdated.emit()  
      
    def is_video_loaded(self, video_name: str) -> bool:  
        """指定動画がデータセットに存在するかチェック"""  
        return video_name in self.stt_dataset.database