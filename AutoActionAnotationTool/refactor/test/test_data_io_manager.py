# test_data_io_manager.py

import sys
import os
import json
import tempfile
import logging
import unittest
from unittest.mock import MagicMock, patch, mock_open

# テスト対象モジュールのインポートのためのパス設定
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject
from annotation_data_manager import AnnotationDataManager, AnnotationItem, VideoInfo
from data_io_manager import DataIOManager


class TestDataIOManager(unittest.TestCase):
    """DataIOManagerクラスのテスト"""
    
    def setUp(self):
        """各テストメソッドの前に実行される設定"""
        if not QApplication.instance():
            self.app = QApplication([])
        
        self.data_manager = AnnotationDataManager()
        self.io_manager = DataIOManager(self.data_manager)
        
        # テスト用のVideoInfo
        self.video_info = VideoInfo(
            video_id="test_video",
            video_path="/test/video.mp4",
            duration=60.0,
            fps=25.0,
            width=1280,
            height=720
        )
        
        # 動画を読み込み
        self.data_manager.load_video("/test/video.mp4", self.video_info)
    
    def test_initial_state(self):
        """初期状態のテスト"""
        assert self.io_manager.data_manager == self.data_manager
    
    @patch('data_io_manager.cv2.VideoCapture')
    def test_load_video_metadata(self, mock_cv2_capture):
        """動画メタデータ読み込みテスト"""
        # OpenCVのモック設定
        mock_cap = MagicMock()
        mock_cv2_capture.return_value = mock_cap
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            7: 1500,    # フレーム数
            5: 30.0,    # FPS
            3: 1920,    # 幅
            4: 1080     # 高さ
        }.get(prop, 0)
        
        video_info = self.io_manager.load_video_metadata("/test/video.mp4")
        
        assert video_info is not None
        assert video_info.video_path == "/test/video.mp4"
        assert video_info.duration == 50.0  # 1500 / 30.0
        assert video_info.fps == 30.0
        assert video_info.width == 1920
        assert video_info.height == 1080
    
    @patch('data_io_manager.cv2.VideoCapture')
    def test_load_video_metadata_failure(self, mock_cv2_capture):
        """動画メタデータ読み込み失敗テスト"""
        # OpenCVが失敗する場合
        mock_cap = MagicMock()
        mock_cv2_capture.return_value = mock_cap
        mock_cap.isOpened.return_value = False
        
        video_info = self.io_manager.load_video_metadata("/invalid/video.mp4")
        assert video_info is None
    
    def test_import_inference_results_success(self):
        """推論結果インポート成功テスト"""
        # テスト用の推論結果データ
        inference_data = {
            "video_id": "test_video",
            "pred_relevant_windows": [
                [10.0, 20.0, 0.9],
                [25.0, 35.0, 0.8],
                [40.0, 50.0, 0.7]
            ],
            "pred_saliency_scores": [0.9, 0.8, 0.7],
            "query": "manipulation action",
            "qid": 1
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(inference_data))):
            with patch.object(self.io_manager, 'data_imported') as mock_signal:
                success = self.io_manager.import_inference_results("/test/inference.json")
                
                assert success is True
                
                # アノテーションが追加されたことを確認
                assert len(self.data_manager.annotations) == 3
                
                # 最初のアノテーションの確認
                first_annotation = self.data_manager.annotations[0]
                assert first_annotation.start_time == 10.0
                assert first_annotation.end_time == 20.0
                assert first_annotation.confidence_score == 0.9
                assert first_annotation.annotation_type == "Action"
                assert first_annotation.category == "manipulation action"
                
                # シグナルが発信されたことを確認
                mock_signal.emit.assert_called_once_with("/test/inference.json", 3)
    
    def test_import_inference_results_file_not_found(self):
        """推論結果インポート - ファイル未存在テスト"""
        with patch("builtins.open", side_effect=FileNotFoundError):
            try:
                self.io_manager.import_inference_results("/nonexistent/file.json")
                assert False, "Should have raised FileNotFoundError"
            except FileNotFoundError:
                pass  # 期待される例外
    
    def test_import_inference_results_invalid_json(self):
        """推論結果インポート - 無効なJSONテスト"""
        with patch("builtins.open", mock_open(read_data="invalid json")):
            try:
                self.io_manager.import_inference_results("/test/invalid.json")
                assert False, "Should have raised JSON decode error"
            except json.JSONDecodeError:
                pass  # 期待される例外
    
    def test_convert_inference_to_annotations(self):
        """推論結果からアノテーションへの変換テスト"""
        inference_data = {
            "video_id": "test_video",
            "pred_relevant_windows": [
                [5.0, 15.0, 0.95],
                [20.0, 30.0, 0.85]
            ],
            "pred_saliency_scores": [0.95, 0.85],
            "query": "cooking step",
            "qid": 2
        }
        
        annotations = self.io_manager._convert_inference_to_annotations(inference_data)
        
        assert len(annotations) == 2
        
        # 最初のアノテーション
        first = annotations[0]
        assert first.start_time == 5.0
        assert first.end_time == 15.0
        assert first.confidence_score == 0.95
        assert first.annotation_type == "Action"
        assert first.category == "cooking step"
        assert first.video_id == "test_video"
        
        # 2番目のアノテーション
        second = annotations[1]
        assert second.start_time == 20.0
        assert second.end_time == 30.0
        assert second.confidence_score == 0.85
    
    def test_export_to_stt_format(self):
        """STT形式エクスポートテスト"""
        # テスト用のアノテーションを追加
        self.data_manager.add_annotation(
            start_time=10.0,
            end_time=20.0,
            annotation_type="Action",
            category="manipulation",
            confidence_score=0.9,
            hand_type="right",
            object_name="cup",
            verb="grab"
        )
        
        self.data_manager.add_annotation(
            start_time=25.0,
            end_time=35.0,
            annotation_type="Step",
            category="cooking step",
            confidence_score=0.8
        )
        
        # 信頼度の低いアノテーション（フィルタリングされる）
        self.data_manager.add_annotation(
            start_time=40.0,
            end_time=50.0,
            annotation_type="Action",
            category="navigation",
            confidence_score=0.6
        )
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            with patch.object(self.io_manager, 'data_exported') as mock_signal:
                success = self.io_manager.export_to_stt_format(tmp_path, confidence_threshold=0.7)
                
                assert success is True
                
                # ファイルが作成されたことを確認
                with open(tmp_path, 'r', encoding='utf-8') as f:
                    exported_data = json.load(f)
                
                # STT形式の構造確認
                assert "database" in exported_data
                assert "version" in exported_data
                
                # 動画データの確認
                videos = exported_data["database"]["test_video"]
                assert videos["subset"] == "test"
                assert videos["duration"] == 60.0
                
                # アノテーションの確認（信頼度 >= 0.7のみ）
                annotations = videos["annotations"]
                assert len(annotations) == 2  # 信頼度0.6のものは除外される
                
                # シグナルが発信されたことを確認
                mock_signal.emit.assert_called_once_with(tmp_path, "STT")
                
        finally:
            # テンポラリファイルを削除
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_export_inference_results(self):
        """推論結果形式エクスポートテスト"""
        # テスト用のアノテーションを追加
        self.data_manager.add_annotation(
            start_time=10.0,
            end_time=20.0,
            annotation_type="Action",
            category="manipulation",
            confidence_score=0.9
        )
        
        self.data_manager.add_annotation(
            start_time=25.0,
            end_time=35.0,
            annotation_type="Action",
            category="navigation",
            confidence_score=0.8
        )
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            with patch.object(self.io_manager, 'data_exported') as mock_signal:
                success = self.io_manager.export_inference_results(tmp_path)
                
                assert success is True
                
                # ファイルが作成されたことを確認
                with open(tmp_path, 'r', encoding='utf-8') as f:
                    exported_data = json.load(f)
                
                # 推論結果形式の構造確認
                assert "video_id" in exported_data
                assert "pred_relevant_windows" in exported_data
                assert "pred_saliency_scores" in exported_data
                
                assert exported_data["video_id"] == "test_video"
                
                # ウィンドウとスコアの確認
                windows = exported_data["pred_relevant_windows"]
                scores = exported_data["pred_saliency_scores"]
                
                assert len(windows) == 2
                assert len(scores) == 2
                
                assert windows[0] == [10.0, 20.0, 0.9]
                assert windows[1] == [25.0, 35.0, 0.8]
                assert scores[0] == 0.9
                assert scores[1] == 0.8
                
                # シグナルが発信されたことを確認
                mock_signal.emit.assert_called_once_with(tmp_path, "Inference")
                
        finally:
            # テンポラリファイルを削除
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_convert_annotations_to_stt(self):
        """アノテーションからSTT形式への変換テスト"""
        # テスト用のアノテーションを追加
        action = self.data_manager.add_annotation(
            start_time=10.0,
            end_time=20.0,
            annotation_type="Action",
            category="manipulation",
            confidence_score=0.9,
            hand_type="right",
            object_name="cup",
            verb="grab"
        )
        
        step = self.data_manager.add_annotation(
            start_time=25.0,
            end_time=35.0,
            annotation_type="Step",
            category="cooking step",
            confidence_score=0.8
        )
        
        stt_data = self.io_manager._convert_annotations_to_stt(confidence_threshold=0.7)
        
        # 基本構造の確認
        assert "database" in stt_data
        assert "version" in stt_data
        assert stt_data["version"] == "1.0"
        
        # 動画データの確認
        video_data = stt_data["database"]["test_video"]
        assert video_data["subset"] == "test"
        assert video_data["duration"] == 60.0
        
        # アノテーションデータの確認
        annotations = video_data["annotations"]
        assert len(annotations) == 2
        
        # Actionアノテーションの確認
        action_anno = next(a for a in annotations if a["segment"] == [10.0, 20.0])
        assert action_anno["label"] == "manipulation"
        assert action_anno["hand_type"] == "right"
        assert action_anno["object"] == "cup"
        assert action_anno["verb"] == "grab"
        
        # Stepアノテーションの確認
        step_anno = next(a for a in annotations if a["segment"] == [25.0, 35.0])
        assert step_anno["label"] == "cooking step"
        assert "hand_type" not in step_anno
        assert "object" not in step_anno
        assert "verb" not in step_anno
    
    def test_convert_annotations_to_inference(self):
        """アノテーションから推論結果形式への変換テスト"""
        # テスト用のアノテーションを追加
        self.data_manager.add_annotation(
            start_time=5.0,
            end_time=15.0,
            annotation_type="Action",
            category="test_category",
            confidence_score=0.95
        )
        
        self.data_manager.add_annotation(
            start_time=20.0,
            end_time=30.0,
            annotation_type="Action",
            category="test_category",
            confidence_score=0.85
        )
        
        inference_data = self.io_manager._convert_annotations_to_inference()
        
        # 基本構造の確認
        assert "video_id" in inference_data
        assert "pred_relevant_windows" in inference_data
        assert "pred_saliency_scores" in inference_data
        assert "query" in inference_data
        assert "qid" in inference_data
        
        assert inference_data["video_id"] == "test_video"
        assert inference_data["query"] == "Generated from annotations"
        assert inference_data["qid"] == 0
        
        # ウィンドウとスコアの確認
        windows = inference_data["pred_relevant_windows"]
        scores = inference_data["pred_saliency_scores"]
        
        assert len(windows) == 2
        assert len(scores) == 2
        
        assert windows[0] == [5.0, 15.0, 0.95]
        assert windows[1] == [20.0, 30.0, 0.85]
        assert scores[0] == 0.95
        assert scores[1] == 0.85


if __name__ == "__main__":
    import unittest
    
    # ログ設定
    logging.basicConfig(level=logging.DEBUG)
    
    # unittestの実行
    unittest.main()
