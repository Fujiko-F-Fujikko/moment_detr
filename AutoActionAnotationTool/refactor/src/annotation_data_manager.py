# annotation_data_manager.py
"""
アノテーションデータの一元管理クラス
StepとActionのアノテーションデータを統一して管理
"""

from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, List, Optional, Any, Union
import logging
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AnnotationItem:
    """統一アノテーションアイテム"""
    id: str
    start_time: float
    end_time: float
    confidence_score: float
    annotation_type: str  # 'action' or 'step'
    category: str  # アクションカテゴリまたはステップテキスト
    hand_type: Optional[str] = None  # アクション用
    object_name: Optional[str] = None  # アクション用
    verb: Optional[str] = None  # アクション用
    video_id: Optional[str] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        self.modified_at = datetime.now()


@dataclass
class VideoInfo:
    """動画情報"""
    video_id: str
    video_path: str
    duration: float
    fps: float
    width: int
    height: int


class AnnotationDataManager(QObject):
    """アノテーションデータの一元管理クラス"""
    
    # シグナル定義
    data_changed = pyqtSignal()
    annotation_added = pyqtSignal(object)  # AnnotationItem
    annotation_modified = pyqtSignal(object, object)  # old_item, new_item
    annotation_deleted = pyqtSignal(object)  # AnnotationItem
    video_loaded = pyqtSignal(object)  # VideoInfo
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 内部データ構造
        self.video_info: Optional[VideoInfo] = None
        self.annotations: List[AnnotationItem] = []  # StepとActionの統一リスト
        self.confidence_threshold = 0.0
        self._next_id = 1
        
        self.logger.info("AnnotationDataManager initialized")
    
    def load_video(self, video_path: str, video_info: VideoInfo):
        """動画を読み込み"""
        self.logger.info(f"Loading video: {video_path}")
        self.video_info = video_info
        self.annotations.clear()
        self.video_loaded.emit(video_info)
        self.data_changed.emit()
    
    def add_annotation(self, annotation_type: str, start_time: float, end_time: float, 
                      category: str, confidence_score: float = 1.0, **kwargs) -> AnnotationItem:
        """アノテーション追加"""
        annotation_id = f"{annotation_type}_{self._next_id:04d}"
        self._next_id += 1
        
        annotation = AnnotationItem(
            id=annotation_id,
            start_time=start_time,
            end_time=end_time,
            confidence_score=confidence_score,
            annotation_type=annotation_type,
            category=category,
            video_id=self.video_info.video_id if self.video_info else None,
            **kwargs
        )
        
        self.logger.info(f"Adding annotation: {annotation}")
        self.annotations.append(annotation)
        self.annotation_added.emit(annotation)
        self.data_changed.emit()
        return annotation
    
    def modify_annotation(self, index: int, **updates) -> bool:
        """アノテーション修正"""
        self.logger.info(f"Modifying annotation at index {index}")
        if 0 <= index < len(self.annotations):
            old_annotation = self.annotations[index]
            
            # 新しいアノテーションアイテムを作成
            annotation_data = {
                'id': old_annotation.id,
                'start_time': updates.get('start_time', old_annotation.start_time),
                'end_time': updates.get('end_time', old_annotation.end_time),
                'confidence_score': updates.get('confidence_score', old_annotation.confidence_score),
                'annotation_type': old_annotation.annotation_type,
                'category': updates.get('category', old_annotation.category),
                'hand_type': updates.get('hand_type', old_annotation.hand_type),
                'object_name': updates.get('object_name', old_annotation.object_name),
                'verb': updates.get('verb', old_annotation.verb),
                'video_id': old_annotation.video_id,
                'created_at': old_annotation.created_at,
                'modified_at': datetime.now()
            }
            
            new_annotation = AnnotationItem(**annotation_data)
            self.annotations[index] = new_annotation
            
            self.annotation_modified.emit(old_annotation, new_annotation)
            self.data_changed.emit()
            return True
        return False
    
    def delete_annotation(self, index: int) -> bool:
        """アノテーション削除"""
        self.logger.info(f"Deleting annotation at index {index}")
        if 0 <= index < len(self.annotations):
            deleted_annotation = self.annotations.pop(index)
            self.annotation_deleted.emit(deleted_annotation)
            self.data_changed.emit()
            return True
        return False
    
    def get_annotation_by_id(self, annotation_id: str) -> Optional[AnnotationItem]:
        """IDでアノテーション取得"""
        for annotation in self.annotations:
            if annotation.id == annotation_id:
                return annotation
        return None
    
    def get_annotations_by_type(self, annotation_type: str) -> List[AnnotationItem]:
        """タイプ別アノテーション取得"""
        return [ann for ann in self.annotations if ann.annotation_type == annotation_type]
    
    def get_filtered_annotations(self) -> List[AnnotationItem]:
        """フィルタリング済みアノテーション取得"""
        filtered = [ann for ann in self.annotations 
                   if ann.confidence_score >= self.confidence_threshold]
        self.logger.debug(f"Filtered {len(filtered)} annotations from {len(self.annotations)}")
        return filtered
    
    def get_annotations_in_time_range(self, start_time: float, end_time: float) -> List[AnnotationItem]:
        """時間範囲内のアノテーション取得"""
        return [ann for ann in self.annotations 
                if not (ann.end_time <= start_time or ann.start_time >= end_time)]
    
    def set_confidence_threshold(self, threshold: float):
        """信頼度閾値設定"""
        self.logger.info(f"Setting confidence threshold: {threshold}")
        self.confidence_threshold = threshold
        self.data_changed.emit()
    
    def get_video_info(self) -> Optional[VideoInfo]:
        """動画情報取得"""
        return self.video_info
    
    def get_all_annotations(self) -> List[AnnotationItem]:
        """全アノテーション取得"""
        return self.annotations.copy()
    
    def clear_annotations(self):
        """全アノテーションクリア"""
        self.logger.info("Clearing all annotations")
        self.annotations.clear()
        self.data_changed.emit()
    
    def get_statistics(self) -> Dict[str, Any]:
        """統計情報取得"""
        total_count = len(self.annotations)
        
        # タイプ別統計
        by_type = {}
        for annotation in self.annotations:
            ann_type = annotation.annotation_type
            by_type[ann_type] = by_type.get(ann_type, 0) + 1
        
        # カテゴリ別統計
        by_category = {}
        for annotation in self.annotations:
            category = annotation.category
            by_category[category] = by_category.get(category, 0) + 1
        
        # 平均信頼度
        if total_count > 0:
            average_confidence = sum(ann.confidence_score for ann in self.annotations) / total_count
        else:
            average_confidence = 0.0
        
        # 総時間
        total_duration = sum(ann.end_time - ann.start_time for ann in self.annotations)
        
        return {
            'total_annotations': total_count,
            'by_type': by_type,
            'by_category': by_category,
            'average_confidence': average_confidence,
            'total_duration': total_duration,
            'confidence_threshold': self.confidence_threshold,
            'video_loaded': self.video_info is not None
        }
