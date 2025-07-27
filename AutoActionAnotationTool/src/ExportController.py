# ExportController.py  
import json  
import logging  
from typing import List, Dict, Any  
from pathlib import Path  
  
from UnifiedDataController import UnifiedDataController  
  
logger = logging.getLogger(__name__)  
  
class ExportController:  
    """エクスポート管理クラス"""  
      
    def __init__(self, data_controller: UnifiedDataController):  
        self.data_controller = data_controller  
        logger.info("ExportController initialized")  
      
    def export_to_stt_json(self, file_path: str) -> bool:  
        """STT形式でJSONエクスポート"""  
        try:  
            logger.info(f"Exporting to STT JSON: {file_path}")  
              
            # データコントローラーのエクスポート機能を使用  
            success = self.data_controller.export_to_stt_format(file_path)  
              
            if success:  
                logger.info(f"Successfully exported STT JSON to: {file_path}")  
            else:  
                logger.error("Failed to export STT JSON")  
              
            return success  
              
        except Exception as e:  
            logger.error(f"Error exporting STT JSON: {e}")  
            return False  
      
    def export_filtered_intervals(self, file_path: str, filters: Dict[str, Any]) -> bool:  
        """フィルタ適用済み区間をエクスポート"""  
        try:  
            logger.info(f"Exporting filtered intervals: {file_path}")  
              
            # フィルタを一時的に適用  
            original_confidence = self.data_controller.confidence_threshold  
            original_hand_type = self.data_controller.hand_type_filter  
            original_interval_type = self.data_controller.interval_type_filter  
              
            # 新しいフィルタを適用  
            if 'confidence_threshold' in filters:  
                self.data_controller.set_confidence_threshold(filters['confidence_threshold'])  
            if 'hand_type_filter' in filters:  
                self.data_controller.set_hand_type_filter(filters['hand_type_filter'])  
            if 'interval_type_filter' in filters:  
                self.data_controller.set_interval_type_filter(filters['interval_type_filter'])  
              
            # フィルタ済みデータを取得  
            filtered_intervals = self.data_controller.get_filtered_intervals()  
              
            # JSON形式で出力  
            export_data = []  
            for interval in filtered_intervals:  
                interval_data = {  
                    'interval_id': interval.interval_id,  
                    'start_time': interval.start_time,  
                    'end_time': interval.end_time,  
                    'confidence_score': interval.confidence_score,  
                    'interval_type': interval.interval_type,  
                    'content_text': interval.content_text,  
                    'video_id': interval.video_id,  
                    'category_id': interval.category_id  
                }  
                export_data.append(interval_data)  
              
            with open(file_path, 'w', encoding='utf-8') as f:  
                json.dump(export_data, f, ensure_ascii=False, indent=2)  
              
            # 元のフィルタ設定を復元  
            self.data_controller.set_confidence_threshold(original_confidence)  
            self.data_controller.set_hand_type_filter(original_hand_type)  
            self.data_controller.set_interval_type_filter(original_interval_type)  
              
            logger.info(f"Successfully exported {len(filtered_intervals)} filtered intervals")  
            return True  
              
        except Exception as e:  
            logger.error(f"Error exporting filtered intervals: {e}")  
            return False  
      
    def validate_export_data(self) -> List[str]:  
        """エクスポートデータの検証"""  
        validation_errors = []  
          
        try:  
            # 基本的な検証  
            if not self.data_controller.all_intervals:  
                validation_errors.append("No intervals to export")  
              
            if not self.data_controller.video_metadata:  
                validation_errors.append("No video metadata available")  
              
            # 各区間の検証  
            for interval in self.data_controller.all_intervals:  
                if interval.start_time >= interval.end_time:  
                    validation_errors.append(f"Invalid time range for interval {interval.interval_id}")  
                  
                if not interval.content_text.strip():  
                    validation_errors.append(f"Empty content text for interval {interval.interval_id}")  
                  
                if interval.video_id not in self.data_controller.video_metadata:  
                    validation_errors.append(f"Missing video metadata for interval {interval.interval_id}")  
              
            logger.info(f"Validation completed with {len(validation_errors)} errors")  
              
        except Exception as e:  
            logger.error(f"Error during validation: {e}")  
            validation_errors.append(f"Validation error: {str(e)}")  
          
        return validation_errors