# data_io_manager.py
"""
データインポート/エクスポート管理クラス
アノテーションデータのインポート/エクスポート処理
"""

from PyQt6.QtCore import QObject, pyqtSignal
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from annotation_data_manager import AnnotationDataManager, AnnotationItem, VideoInfo


class DataIOManager(QObject):
    """データインポート/エクスポート管理クラス"""
    
    data_imported = pyqtSignal(list)  # List[AnnotationItem]
    data_exported = pyqtSignal(str)   # file_path
    
    def __init__(self, data_manager: AnnotationDataManager):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.data_manager = data_manager
        
        self.logger.info("DataIOManager initialized")
    
    def import_inference_results(self, file_path: str) -> bool:
        """推論結果をインポート（moment-detr形式）"""
        self.logger.info(f"Importing inference results from: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 推論結果を内部形式に変換
            annotations = self._convert_inference_to_annotations(data)
            
            # データマネージャーに追加
            for annotation in annotations:
                self.data_manager.annotations.append(annotation)
            
            self.data_manager.data_changed.emit()
            self.data_imported.emit(annotations)
            self.logger.info(f"Successfully imported {len(annotations)} annotations")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import inference results: {e}")
            return False
    
    def export_to_stt_format(self, file_path: str, confidence_threshold: float = 0.0) -> bool:
        """STT形式でエクスポート"""
        self.logger.info(f"Exporting to STT format: {file_path} (threshold: {confidence_threshold})")
        try:
            # 内部形式からSTT形式に変換
            stt_data = self._convert_annotations_to_stt(confidence_threshold)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(stt_data, f, ensure_ascii=False, indent=2)
            
            self.data_exported.emit(file_path)
            self.logger.info(f"Successfully exported to STT format")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export to STT format: {e}")
            return False
    
    def export_inference_results(self, file_path: str) -> bool:
        """推論結果形式でエクスポート（moment-detr形式）"""
        self.logger.info(f"Exporting inference results: {file_path}")
        try:
            # 内部形式から推論結果形式に変換
            inference_data = self._convert_annotations_to_inference()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(inference_data, f, ensure_ascii=False, indent=2)
            
            self.data_exported.emit(file_path)
            self.logger.info(f"Successfully exported inference results")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export inference results: {e}")
            return False
    
    def _convert_inference_to_annotations(self, data: Dict[str, Any]) -> List[AnnotationItem]:
        """推論結果を内部アノテーション形式に変換"""
        annotations = []
        
        if 'data' not in data:
            self.logger.warning("No 'data' field found in inference results")
            return annotations
        
        for result in data['data']:
            query_text = result.get('query', '')
            video_id = result.get('vid', '')
            
            # Step/Actionの判定
            if query_text.startswith('Step:'):
                annotation_type = 'step'
                category = query_text.replace('Step: ', '').strip()
            else:
                annotation_type = 'action'
                # クエリテキストからカテゴリを抽出
                parts = query_text.split('_')
                category = parts[0] if parts else query_text
            
            # 関連する区間を処理
            for idx, window in enumerate(result.get('relevant_windows', [])):
                start_time = window[0]
                end_time = window[1]
                confidence = result.get('saliency_scores', [1.0])[idx] if idx < len(result.get('saliency_scores', [])) else 1.0
                
                # AnnotationItemを作成
                annotation = AnnotationItem(
                    id=f"{annotation_type}_{len(annotations)+1:04d}",
                    start_time=start_time,
                    end_time=end_time,
                    confidence_score=confidence,
                    annotation_type=annotation_type,
                    category=category,
                    video_id=video_id
                )
                
                # アクションの場合は追加情報を抽出
                if annotation_type == 'action' and len(parts) >= 4:
                    annotation.hand_type = parts[1] if parts[1] != 'None' else None
                    annotation.object_name = parts[2] if parts[2] != 'None' else None  
                    annotation.verb = parts[3] if parts[3] != 'None' else None
                
                annotations.append(annotation)
        
        self.logger.info(f"Converted {len(annotations)} annotations from inference results")
        return annotations
    
    def _convert_annotations_to_stt(self, confidence_threshold: float) -> Dict[str, Any]:
        """内部アノテーション形式をSTT形式に変換"""
        video_info = self.data_manager.get_video_info()
        if not video_info:
            raise ValueError("No video loaded")
        
        # 閾値でフィルタリング
        filtered_annotations = [
            ann for ann in self.data_manager.annotations 
            if ann.confidence_score >= confidence_threshold
        ]
        
        # STT形式のデータベース構築
        database = {}
        
        video_data = {
            "duration": video_info.duration,
            "subset": "train",  # デフォルト値
            "recipe_type": "unknown",  # デフォルト値
            "annotation": []
        }
        
        # アクションアノテーションを処理
        action_annotations = [ann for ann in filtered_annotations if ann.annotation_type == 'action']
        for annotation in action_annotations:
            action_data = {
                "segment": [annotation.start_time, annotation.end_time],
                "id": int(annotation.id.split('_')[1]),
                "label": annotation.category
            }
            video_data["annotation"].append(action_data)
        
        # ステップアノテーションを処理
        step_annotations = [ann for ann in filtered_annotations if ann.annotation_type == 'step']
        steps = []
        for annotation in step_annotations:
            step_data = {
                "segment": [annotation.start_time, annotation.end_time],
                "id": int(annotation.id.split('_')[1]),
                "step": annotation.category
            }
            steps.append(step_data)
        
        if steps:
            video_data["steps"] = steps
        
        database[video_info.video_id] = video_data
        
        stt_data = {
            "database": database,
            "version": "1.0",
            "split": {
                "train": [video_info.video_id],
                "test": [],
                "validation": []
            }
        }
        
        return stt_data
    
    def _convert_annotations_to_inference(self) -> Dict[str, Any]:
        """内部アノテーション形式を推論結果形式に変換"""
        video_info = self.data_manager.get_video_info()
        if not video_info:
            raise ValueError("No video loaded")
        
        # アノテーションをクエリ別にグループ化
        query_groups = {}
        
        for annotation in self.data_manager.annotations:
            if annotation.annotation_type == 'step':
                query_text = f"Step: {annotation.category}"
            else:
                # アクションクエリテキストを構築
                hand = annotation.hand_type or 'None'
                obj = annotation.object_name or 'None'
                verb = annotation.verb or 'None'
                query_text = f"{annotation.category}_{hand}_{obj}_{verb}"
            
            if query_text not in query_groups:
                query_groups[query_text] = []
            
            query_groups[query_text].append(annotation)
        
        # 推論結果形式に変換
        data = []
        for query_id, (query_text, annotations) in enumerate(query_groups.items()):
            windows = []
            scores = []
            
            for annotation in annotations:
                windows.append([annotation.start_time, annotation.end_time])
                scores.append(annotation.confidence_score)
            
            result = {
                "query": query_text,
                "vid": video_info.video_id,
                "relevant_windows": windows,
                "saliency_scores": scores,
                "qid": query_id
            }
            data.append(result)
        
        inference_data = {
            "data": data,
            "video_path": video_info.video_path,
            "video_duration": video_info.duration
        }
        
        return inference_data
    
    def load_video_metadata(self, video_path: str) -> Optional[VideoInfo]:
        """動画メタデータを読み込み"""
        self.logger.info(f"Loading video metadata: {video_path}")
        try:
            import cv2
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Cannot open video file: {video_path}")
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            
            cap.release()
            
            video_id = Path(video_path).stem
            video_info = VideoInfo(video_id, video_path, duration, fps, width, height)
            
            self.logger.info(f"Video metadata loaded: {video_id}, {duration:.2f}s")
            return video_info
            
        except Exception as e:
            self.logger.error(f"Failed to load video metadata: {e}")
            return None
