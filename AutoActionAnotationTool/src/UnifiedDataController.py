# UnifiedDataController.py  
import json  
import logging  
from typing import List, Dict
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal  
  
from VideoInfo import VideoInfo
from UnifiedInterval import UnifiedInterval  
from STTDataStructures import STTDataset  
  
logger = logging.getLogger(__name__)  
  
@dataclass  
class VideoMetadata:  
    """動画メタデータ"""  
    video_id: str  
    subset: str  
    duration: float  
    fps: float  
    file_path: str  
  
@dataclass   
class CategoryInfo:  
    """カテゴリ情報"""  
    id: int  
    content_text: str  
    category_type: str  # "action" or "step"  
  
class UnifiedDataController(QObject):  
    """統一されたデータ管理クラス"""  
      
    # シグナル定義  
    dataUpdated = pyqtSignal()  
    intervalAdded = pyqtSignal(str)  # interval_id  
    intervalModified = pyqtSignal(str)  # interval_id  
    intervalDeleted = pyqtSignal(str)  # interval_id  
      
    def __init__(self):  
        super().__init__()  
        self.all_intervals: List[UnifiedInterval] = []  
        self.video_metadata: Dict[str, VideoMetadata] = {}  
        self.action_categories: List[CategoryInfo] = []  
        self.step_categories: List[CategoryInfo] = []  
          
        # フィルタ設定  
        self.confidence_threshold: float = 0.0  
        self.hand_type_filter: str = "All"  
        self.interval_type_filter: str = "All"  # "All", "action", "step"  
          
        # カテゴリIDカウンター  
        self.action_id_counter = 1  
        self.step_id_counter = 1  
          
        logger.info("UnifiedDataController initialized")  
      
    def load_inference_results(self, json_path: str) -> bool:  
        """推論結果JSONファイルを読み込み"""  
        try:  
            logger.info(f"Loading inference results from: {json_path}")  
              
            with open(json_path, 'r', encoding='utf-8') as f:  
                data = json.load(f)  
              
            # 既存データをクリア  
            self.all_intervals.clear()  
              
            # QueryResultsからUnifiedIntervalに変換  
            for query_result in data:  
                query_text = query_result.get('query', '')  
                  
                # Step/Actionの判定（既存ロジックを維持）  
                if query_text.startswith("Step:"):  
                    interval_type = "step"  
                    content_text = query_text[5:].strip()  # "Step:"を除去  
                else:  
                    interval_type = "action"  
                    content_text = query_text  
                  
                # 各区間を変換  
                for window in query_result.get('relevant_windows', []):  
                    start_time = window.get('start_time', 0.0)  
                    end_time = window.get('end_time', 0.0)  
                    confidence = window.get('confidence_score', 0.0)  
                      
                    interval = UnifiedInterval(  
                        start_time=start_time,  
                        end_time=end_time,  
                        confidence_score=confidence,  
                        interval_type=interval_type,  
                        content_text=content_text,  
                        video_id=query_result.get('video_id', ''),  
                        category_id=self.get_or_create_category(content_text, interval_type)  
                    )  
                      
                    self.all_intervals.append(interval)  
              
            logger.info(f"Loaded {len(self.all_intervals)} intervals")  
            self.dataUpdated.emit()  
            return True  
              
        except Exception as e:  
            logger.error(f"Failed to load inference results: {e}")  
            return False  
      
    def add_video_metadata(self, video_info: VideoInfo, subset: str) -> bool:  
        """動画メタデータを追加"""  
        try:  
            metadata = VideoMetadata(  
                video_id=video_info.video_id,  
                subset=subset,  
                duration=video_info.duration,  
                fps=video_info.fps,  
                file_path=video_info.file_path  
            )  
              
            self.video_metadata[video_info.video_id] = metadata  
            logger.info(f"Added video metadata: {video_info.video_id}")  
            return True  
              
        except Exception as e:  
            logger.error(f"Failed to add video metadata: {e}")  
            return False  
      
    def add_interval(self, interval: UnifiedInterval) -> bool:  
        """区間を追加"""  
        try:  
            self.all_intervals.append(interval)  
            logger.info(f"Added interval: {interval.interval_id}")  
            self.intervalAdded.emit(interval.interval_id)  
            self.dataUpdated.emit()  
            return True  
              
        except Exception as e:  
            logger.error(f"Failed to add interval: {e}")  
            return False  
      
    def modify_interval(self, interval_id: str, new_data: dict) -> bool:  
        """区間を変更"""  
        try:  
            for interval in self.all_intervals:  
                if interval.interval_id == interval_id:  
                    # データを更新  
                    for key, value in new_data.items():  
                        if hasattr(interval, key):  
                            setattr(interval, key, value)  
                      
                    logger.info(f"Modified interval: {interval_id}")  
                    self.intervalModified.emit(interval_id)  
                    self.dataUpdated.emit()  
                    return True  
              
            logger.warning(f"Interval not found: {interval_id}")  
            return False  
              
        except Exception as e:  
            logger.error(f"Failed to modify interval: {e}")  
            return False  
      
    def delete_interval(self, interval_id: str) -> bool:  
        """区間を削除"""  
        try:  
            for i, interval in enumerate(self.all_intervals):  
                if interval.interval_id == interval_id:  
                    del self.all_intervals[i]  
                    logger.info(f"Deleted interval: {interval_id}")  
                    self.intervalDeleted.emit(interval_id)  
                    self.dataUpdated.emit()  
                    return True  
              
            logger.warning(f"Interval not found: {interval_id}")  
            return False  
              
        except Exception as e:  
            logger.error(f"Failed to delete interval: {e}")  
            return False  
      
    def get_intervals_for_video(self, video_id: str) -> List[UnifiedInterval]:  
        """指定動画の区間を取得"""  
        return [interval for interval in self.all_intervals   
                if interval.video_id == video_id]  
      
    def get_filtered_intervals(self) -> List[UnifiedInterval]:  
        """フィルタ適用済み区間を取得"""  
        filtered = []  
          
        for interval in self.all_intervals:  
            # 信頼度フィルタ  
            if interval.confidence_score < self.confidence_threshold:  
                continue  
              
            # 区間タイプフィルタ  
            if (self.interval_type_filter != "All" and   
                interval.interval_type != self.interval_type_filter):  
                continue  
              
            # 手タイプフィルタ（アクションのみ）  
            if (interval.is_action_type() and   
                self.hand_type_filter != "All"):  
                # 既存のhand_type判定ロジックを適用  
                if not self._matches_hand_type_filter(interval):  
                    continue  
              
            filtered.append(interval)  
          
        return filtered  
      
    def _matches_hand_type_filter(self, interval: UnifiedInterval) -> bool:  
        """手タイプフィルタにマッチするかチェック"""  
        # 既存のResultsDataControllerのロジックを移植  
        if self.hand_type_filter == "All":  
            return True  
          
        query_text = interval.content_text.lower()  
          
        if self.hand_type_filter == "Left":  
            return "left" in query_text  
        elif self.hand_type_filter == "Right":  
            return "right" in query_text  
        elif self.hand_type_filter == "Other":  
            return "left" not in query_text and "right" not in query_text  
          
        return True  
      
    def set_confidence_threshold(self, threshold: float):  
        """信頼度閾値を設定"""  
        self.confidence_threshold = threshold  
        logger.info(f"Confidence threshold set to: {threshold}")  
        self.dataUpdated.emit()  
      
    def set_hand_type_filter(self, hand_type: str):  
        """手タイプフィルタを設定"""  
        self.hand_type_filter = hand_type  
        logger.info(f"Hand type filter set to: {hand_type}")  
        self.dataUpdated.emit()  
      
    def set_interval_type_filter(self, type_filter: str):  
        """区間タイプフィルタを設定"""  
        self.interval_type_filter = type_filter  
        logger.info(f"Interval type filter set to: {type_filter}")  
        self.dataUpdated.emit()  
      
    def export_to_stt_format(self, file_path: str) -> bool:  
        """STT形式でエクスポート"""  
        try:  
            logger.info(f"Exporting to STT format: {file_path}")  
              
            # STTDatasetを構築  
            stt_dataset = STTDataset()  
              
            # 動画データを追加  
            for video_id, metadata in self.video_metadata.items():  
                video_info = VideoInfo(  
                    video_id=video_id,  
                    subset=metadata.subset,  
                    duration=metadata.duration,  
                    fps=metadata.fps,  
                    file_path=metadata.file_path  
                )  
                stt_dataset.add_video(video_info)  
              
            # 区間データを変換して追加  
            for interval in self.all_intervals:  
                if interval.video_id not in self.video_metadata:  
                    continue  
                  
                fps = self.video_metadata[interval.video_id].fps  
                  
                if interval.is_action_type():  
                    action_entry = interval.to_stt_action_entry(fps)  
                    stt_dataset.add_action_to_video(interval.video_id, action_entry)  
                else:  
                    step_entry = interval.to_stt_step_entry(fps)  
                    stt_dataset.add_step_to_video(interval.video_id, step_entry)  
              
            # JSONファイルに保存  
            with open(file_path, 'w', encoding='utf-8') as f:  
                json.dump(stt_dataset.to_dict(), f, ensure_ascii=False, indent=2)  
              
            logger.info(f"Successfully exported to: {file_path}")  
            return True  
              
        except Exception as e:  
            logger.error(f"Failed to export to STT format: {e}")  
            return False  
      
    def get_or_create_category(self, content_text: str, interval_type: str) -> int:  
        """カテゴリを取得または作成"""  
        if interval_type == "action":  
            for category in self.action_categories:  
                if category.content_text == content_text:  
                    return category.id  
              
            # 新しいアクションカテゴリを作成  
            new_category = CategoryInfo(  
                id=self.action_id_counter,  
                content_text=content_text,  
                category_type="action"  
            )  
            self.action_categories.append(new_category)  
            self.action_id_counter += 1  
            return new_category.id  
          
        else:  # step  
            for category in self.step_categories:  
                if category.content_text == content_text:  
                    return category.id  
              
            # 新しいステップカテゴリを作成  
            new_category = CategoryInfo(  
                id=self.step_id_counter,  
                content_text=content_text,  
                category_type="step"  
            )  
            self.step_categories.append(new_category)  
            self.step_id_counter += 1  
            return new_category.id  
      
    def group_intervals_by_type(self) -> Dict[str, List[UnifiedInterval]]:  
        """区間をタイプ別にグループ化"""  
        groups = {"action": [], "step": []}  
          
        for interval in self.all_intervals:  
            groups[interval.interval_type].append(interval)  
          
        return groups  
      
    def clear_all_data(self):  
        """全データをクリア"""  
        self.all_intervals.clear()  
        self.video_metadata.clear()  
        self.action_categories.clear()  
        self.step_categories.clear()  
        self.action_id_counter = 1  
        self.step_id_counter = 1  
          
        logger.info("All data cleared")  
        self.dataUpdated.emit()