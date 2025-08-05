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
        
        # 新しい形式の場合 - results と steps フィールドを確認
        if 'results' in data or 'steps' in data:
            self.logger.info("Processing new inference result format")
            
            # Action アノテーションを処理 (results配列)
            for result in data.get('results', []):
                query_text = result.get('query', '')
                video_id = result.get('vid', '')
                
                # クエリテキストからカテゴリと詳細情報を抽出
                parts = query_text.split('_')
                raw_hand_type = parts[0] if len(parts) > 0 and parts[0] != 'None' else None
                verb = parts[1] if len(parts) > 1 and parts[1] != 'None' else None
                object_name = parts[2] if len(parts) > 2 and parts[2] != 'None' else None
                
                # Hand typeを正規化
                hand_type = None
                if raw_hand_type:
                    if raw_hand_type.lower() == 'lefthand':
                        hand_type = 'left'
                    elif raw_hand_type.lower() == 'righthand':
                        hand_type = 'right'
                    elif raw_hand_type.lower() == 'bothhands':
                        hand_type = 'both'
                    else:
                        hand_type = raw_hand_type.lower()  # その他の場合はそのまま小文字化
                
                category = f"{hand_type}_{verb}_{object_name}" if all([hand_type, verb, object_name]) else query_text
                
                # 関連する区間を処理
                for idx, window in enumerate(result.get('pred_relevant_windows', [])):
                    start_time = window[0]
                    end_time = window[1]
                    confidence = window[2] if len(window) > 2 else 1.0
                    
                    # AnnotationItemを作成
                    annotation = AnnotationItem(
                        id=f"Action_{len(annotations)+1:04d}",
                        start_time=start_time,
                        end_time=end_time,
                        confidence_score=confidence,
                        annotation_type='Action',
                        category=category,
                        video_id=video_id,
                        hand_type=hand_type,
                        verb=verb,
                        object_name=object_name
                    )
                    
                    annotations.append(annotation)
            
            # Step アノテーションを処理 (steps配列)
            for step in data.get('steps', []):
                query_text = step.get('query', '')
                video_id = step.get('vid', '')
                
                # Stepの場合はクエリテキストから "Step: " を除去
                category = query_text.replace('Step: ', '').strip() if query_text.startswith('Step:') else query_text
                
                # 関連する区間を処理
                for idx, window in enumerate(step.get('pred_relevant_windows', [])):
                    start_time = window[0]
                    end_time = window[1]
                    confidence = window[2] if len(window) > 2 else 1.0
                    
                    # AnnotationItemを作成
                    annotation = AnnotationItem(
                        id=f"Step_{len(annotations)+1:04d}",
                        start_time=start_time,
                        end_time=end_time,
                        confidence_score=confidence,
                        annotation_type='Step',
                        category=category,
                        video_id=video_id
                    )
                    
                    annotations.append(annotation)
        else:
            self.logger.warning("No recognized data format found in inference results")
            return annotations
        
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
        action_annotations = [ann for ann in filtered_annotations if ann.annotation_type.lower() == 'action']
        for annotation in action_annotations:
            action_data = {
                "segment": [annotation.start_time, annotation.end_time],
                "id": int(annotation.id.split('_')[1]),
                "label": annotation.category
            }
            video_data["annotation"].append(action_data)
        
        # ステップアノテーションを処理
        step_annotations = [ann for ann in filtered_annotations if ann.annotation_type.lower() == 'step']
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
            if annotation.annotation_type.lower() == 'step':
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
