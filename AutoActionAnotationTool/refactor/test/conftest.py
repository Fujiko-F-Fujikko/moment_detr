# conftest.py

import sys
import os
import pytest
import logging
from unittest.mock import MagicMock

# テスト対象モジュールのインポートのためのパス設定
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# ログ設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@pytest.fixture(scope="session")
def qapp():
    """QApplicationのセッションスコープフィクスチャ"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture(scope="function")
def qtbot(qapp):
    """pytestQtのqtbotフィクスチャの代替"""
    # 簡易版のqtbot（実際のpytest-qtがない場合）
    class SimpleQtBot:
        def addWidget(self, widget):
            pass
        
        def waitForWindowShown(self, widget):
            pass
        
        def keyClick(self, widget, key):
            pass
        
        def mouseClick(self, widget, button):
            pass
    
    return SimpleQtBot()


@pytest.fixture
def mock_video_info():
    """テスト用VideoInfoのフィクスチャ"""
    from annotation_data_manager import VideoInfo
    return VideoInfo(
        video_id="test_video",
        video_path="/test/video.mp4",
        duration=60.0,
        fps=25.0,
        width=1280,
        height=720
    )


@pytest.fixture
def mock_annotation_action():
    """テスト用Actionアノテーションのフィクスチャ"""
    from annotation_data_manager import AnnotationItem
    return AnnotationItem(
        id="test_action_001",
        start_time=10.0,
        end_time=20.0,
        confidence_score=0.9,
        annotation_type="Action",
        category="manipulation",
        hand_type="right",
        object_name="cup",
        verb="grab"
    )


@pytest.fixture
def mock_annotation_step():
    """テスト用Stepアノテーションのフィクスチャ"""
    from annotation_data_manager import AnnotationItem
    return AnnotationItem(
        id="test_step_001",
        start_time=30.0,
        end_time=45.0,
        confidence_score=0.8,
        annotation_type="Step",
        category="cooking step: chop vegetables"
    )


@pytest.fixture
def data_manager_with_video(mock_video_info):
    """動画が読み込まれたAnnotationDataManagerのフィクスチャ"""
    from annotation_data_manager import AnnotationDataManager
    
    manager = AnnotationDataManager()
    manager.load_video("/test/video.mp4", mock_video_info)
    return manager


@pytest.fixture
def data_manager_with_annotations(data_manager_with_video, mock_annotation_action, mock_annotation_step):
    """アノテーション付きのAnnotationDataManagerのフィクスチャ"""
    manager = data_manager_with_video
    
    # アノテーションを追加
    manager.add_annotation(
        start_time=mock_annotation_action.start_time,
        end_time=mock_annotation_action.end_time,
        annotation_type=mock_annotation_action.annotation_type,
        category=mock_annotation_action.category,
        confidence_score=mock_annotation_action.confidence_score,
        hand_type=mock_annotation_action.hand_type,
        object_name=mock_annotation_action.object_name,
        verb=mock_annotation_action.verb
    )
    
    manager.add_annotation(
        start_time=mock_annotation_step.start_time,
        end_time=mock_annotation_step.end_time,
        annotation_type=mock_annotation_step.annotation_type,
        category=mock_annotation_step.category,
        confidence_score=mock_annotation_step.confidence_score
    )
    
    return manager


@pytest.fixture
def command_manager(data_manager_with_video):
    """AnnotationCommandManagerのフィクスチャ"""
    from annotation_command_manager import AnnotationCommandManager
    return AnnotationCommandManager(data_manager_with_video)


@pytest.fixture
def io_manager(data_manager_with_video):
    """DataIOManagerのフィクスチャ"""
    from data_io_manager import DataIOManager
    return DataIOManager(data_manager_with_video)


@pytest.fixture
def video_controller():
    """VideoControllerのフィクスチャ"""
    from video_controller import VideoController
    return VideoController()


@pytest.fixture
def timeline_controller(data_manager_with_video):
    """TimelineControllerのフィクスチャ"""
    from timeline_controller import TimelineController
    return TimelineController(data_manager_with_video)


@pytest.fixture
def list_controller(data_manager_with_video):
    """AnnotationListControllerのフィクスチャ"""
    from annotation_list_controller import AnnotationListController
    return AnnotationListController(data_manager_with_video)


@pytest.fixture
def editor_controller(data_manager_with_video, command_manager):
    """AnnotationEditorControllerのフィクスチャ"""
    from annotation_editor_controller import AnnotationEditorController
    return AnnotationEditorController(data_manager_with_video, command_manager)


@pytest.fixture
def main_window():
    """MainApplicationWindowのフィクスチャ"""
    from main_application_window import MainApplicationWindow
    window = MainApplicationWindow()
    yield window
    # クリーンアップ
    window.close()


# テスト用のダミーデータ
@pytest.fixture
def sample_inference_data():
    """テスト用推論結果データ"""
    return {
        "video_id": "test_video",
        "pred_relevant_windows": [
            [10.0, 20.0, 0.9],
            [25.0, 35.0, 0.8],
            [40.0, 50.0, 0.7]
        ],
        "pred_saliency_scores": [0.9, 0.8, 0.7],
        "query": "test query",
        "qid": 1
    }


@pytest.fixture
def sample_stt_data():
    """テスト用STTデータ"""
    return {
        "version": "1.0",
        "database": {
            "test_video": {
                "subset": "test",
                "duration": 60.0,
                "annotations": [
                    {
                        "segment": [10.0, 20.0],
                        "label": "manipulation",
                        "hand_type": "right",
                        "object": "cup",
                        "verb": "grab"
                    },
                    {
                        "segment": [30.0, 45.0],
                        "label": "cooking step"
                    }
                ]
            }
        }
    }


# OpenCVのモック（テスト環境にOpenCVがない場合）
@pytest.fixture(autouse=True)
def mock_opencv():
    """OpenCVのモック（自動適用）"""
    import sys
    from unittest.mock import MagicMock
    
    # cv2がインポートできない場合のモック
    if 'cv2' not in sys.modules:
        sys.modules['cv2'] = MagicMock()
        
        # VideoCapture の基本的な動作をモック
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            7: 1500,    # フレーム数
            5: 30.0,    # FPS
            3: 1920,    # 幅
            4: 1080     # 高さ
        }.get(prop, 0)
        
        sys.modules['cv2'].VideoCapture.return_value = mock_cap


# テスト実行時の設定
def pytest_configure(config):
    """pytest設定"""
    # テスト実行時の追加設定があればここに記述
    pass


def pytest_unconfigure(config):
    """pytest終了時の処理"""
    # QApplicationの終了処理
    app = QApplication.instance()
    if app:
        app.quit()


# カスタムマーカーの定義
pytest_plugins = []
