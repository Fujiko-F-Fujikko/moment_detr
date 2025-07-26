import json  
from pathlib import Path  
from typing import Dict, List, Optional  
from datetime import datetime  
from dataclasses import asdict
from STTDataStructures import *  
from Results import QueryResults, InferenceResults  
from VideoInfo import VideoInfo  
  
class STTDataManager:  
    def __init__(self):  
        self.stt_dataset = STTDataset()  
        self.action_id_counter = 1  
        self.step_id_counter = 1  
          
    def add_video_data(self, video_info: VideoInfo, subset: str = "train"):  
        """動画データを追加"""  
        video_name = Path(video_info.file_path).stem  
        self.stt_dataset.database[video_name] = VideoData(  
            subset=subset,  
            duration=video_info.duration,  
            fps=video_info.fps  
        )  
          
    def add_inference_results(self, video_name: str, inference_results: List[QueryResults]):  
        """推論結果からアクションデータを生成（クエリ形式検証付き）"""  
        if video_name not in self.stt_dataset.database:  
            return  
            
        video_data = self.stt_dataset.database[video_name]  
        fps = video_data.fps  
        invalid_queries = []  
        
        for query_result in inference_results:  
            # ステップクエリの場合は検証をスキップ  
            if query_result.query_text.startswith("Step:"):  
                continue  

            try:  
                # 新しい検証付きパーサーを使用  
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
      
        # 不正なクエリがあった場合は警告を表示  
        if invalid_queries:  
            error_msg = "以下のクエリが不正な形式です:\n"  
            for query, error in invalid_queries:  
                error_msg += f"- '{query}': {error}\n"  
            raise ValueError(error_msg)
      
    def add_step(self, video_name: str, step_text: str, segment: List[float]):  
        """ステップを追加"""  
        if video_name not in self.stt_dataset.database:  
            return  
              
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
      
    def update_video_subset(self, video_name: str, subset: str):  
        """動画のサブセットを更新"""  
        if video_name in self.stt_dataset.database:  
            self.stt_dataset.database[video_name].subset = subset  
      
    def export_to_json(self, file_path: str):  
        """STT Dataset形式でJSONエクスポート"""  
        # データ作成日時を更新  
        self.stt_dataset.info["data_created"] = datetime.now().strftime("%Y/%m/%d")  
          
        # データクラスを辞書に変換            
        data_dict = asdict(self.stt_dataset)
          
        with open(file_path, 'w', encoding='utf-8') as f:  
            json.dump(data_dict, f, indent=2, ensure_ascii=False)