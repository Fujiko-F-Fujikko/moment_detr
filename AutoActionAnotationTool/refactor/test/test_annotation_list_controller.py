# test_annotation_list_controller.py

import sys
import os
import logging
import unittest
from unittest.mock import MagicMock, patch

# テスト対象モジュールのインポートのためのパス設定
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from PyQt6.QtWidgets import QApplication, QWidget, QListWidget, QComboBox, QSlider, QListWidgetItem
from PyQt6.QtCore import Qt
from annotation_data_manager import AnnotationDataManager, AnnotationItem, VideoInfo
from annotation_list_controller import AnnotationListController, AnnotationListItem


class TestAnnotationListItem(unittest.TestCase):
    """AnnotationListItemクラスのテスト"""
    
    def setUp(self):
        """各テストメソッドの前に実行される設定"""
        if not QApplication.instance():
            self.app = QApplication([])
        
        self.annotation = AnnotationItem(
            id="test_001",
            start_time=10.0,
            end_time=20.0,
            confidence_score=0.9,
            annotation_type="Action",
            category="manipulation",
            hand_type="right",
            object_name="cup",
            verb="grab"
        )
        
        self.list_item = AnnotationListItem(self.annotation)
    
    def test_initial_state(self):
        """初期状態のテスト"""
        assert self.list_item.annotation == self.annotation
        assert isinstance(self.list_item, QListWidgetItem)
    
    def test_update_display(self):
        """表示更新テスト"""
        self.list_item.update_display()
        
        # テキストが適切に設定されることを確認
        text = self.list_item.text()
        assert "Action" in text
        assert "10.0s" in text
        assert "20.0s" in text
        assert "manipulation" in text
        assert "0.90" in text  # 信頼度が表示される
    
    def test_update_display_after_modification(self):
        """アノテーション修正後の表示更新テスト"""
        # アノテーションを修正
        self.annotation.start_time = 15.0
        self.annotation.end_time = 25.0
        self.annotation.category = "navigation"
        self.annotation.confidence_score = 0.85
        
        # 表示を更新
        self.list_item.update_display()
        
        # 修正された内容が反映されることを確認
        text = self.list_item.text()
        assert "15.0s" in text
        assert "25.0s" in text
        assert "navigation" in text
        assert "0.85" in text


class TestAnnotationListController(unittest.TestCase):
    """AnnotationListControllerクラスのテスト"""
    
    def setUp(self):
        """各テストメソッドの前に実行される設定"""
        if not QApplication.instance():
            self.app = QApplication([])
        
        self.data_manager = AnnotationDataManager()
        self.list_controller = AnnotationListController(self.data_manager)
        
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
        
        # テスト用のアノテーションを追加
        self.action_annotation = self.data_manager.add_annotation(
            start_time=10.0,
            end_time=20.0,
            annotation_type="Action",
            category="manipulation",
            confidence_score=0.9,
            hand_type="right"
        )
        
        self.step_annotation = self.data_manager.add_annotation(
            start_time=30.0,
            end_time=40.0,
            annotation_type="Step",
            category="cooking",
            confidence_score=0.8
        )
        
        self.low_conf_annotation = self.data_manager.add_annotation(
            start_time=50.0,
            end_time=55.0,
            annotation_type="Action",
            category="navigation",
            confidence_score=0.5
        )
    
    def test_initial_state(self):
        """初期状態のテスト"""
        assert self.list_controller.data_manager == self.data_manager
        assert isinstance(self.list_controller.list_widget, QListWidget)
        assert isinstance(self.list_controller.main_widget, QWidget)
        assert isinstance(self.list_controller.type_filter, QComboBox)
        assert isinstance(self.list_controller.confidence_slider, QSlider)
        assert self.list_controller.current_type_filter == "All"
        assert self.list_controller.current_confidence_threshold == 0.0
    
    def test_update_list_all_types(self):
        """全タイプでのリスト更新テスト"""
        self.list_controller.update_list()
        
        # 全アノテーションが表示されることを確認
        assert self.list_controller.list_widget.count() == 3
        
        # 各アイテムが正しい型であることを確認
        for i in range(self.list_controller.list_widget.count()):
            item = self.list_controller.list_widget.item(i)
            assert isinstance(item, AnnotationListItem)
    
    def test_update_list_action_filter(self):
        """Actionタイプフィルターでのリスト更新テスト"""
        # フィルターをActionに設定
        self.list_controller.current_type_filter = "Action"
        self.list_controller.update_list()
        
        # Actionタイプのアノテーションのみ表示されることを確認
        assert self.list_controller.list_widget.count() == 2  # action_annotation と low_conf_annotation
        
        # 表示されたアイテムがActionタイプであることを確認
        for i in range(self.list_controller.list_widget.count()):
            item = self.list_controller.list_widget.item(i)
            assert item.annotation.annotation_type == "Action"
    
    def test_update_list_step_filter(self):
        """Stepタイプフィルターでのリスト更新テスト"""
        # フィルターをStepに設定
        self.list_controller.current_type_filter = "Step"
        self.list_controller.update_list()
        
        # Stepタイプのアノテーションのみ表示されることを確認
        assert self.list_controller.list_widget.count() == 1
        
        item = self.list_controller.list_widget.item(0)
        assert item.annotation.annotation_type == "Step"
        assert item.annotation == self.step_annotation
    
    def test_update_list_confidence_filter(self):
        """信頼度フィルターでのリスト更新テスト"""
        # 信頼度閾値を0.7に設定
        self.list_controller.current_confidence_threshold = 0.7
        self.list_controller.update_list()
        
        # 信頼度0.7以上のアノテーションのみ表示されることを確認
        assert self.list_controller.list_widget.count() == 2  # action_annotation(0.9) と step_annotation(0.8)
        
        # low_conf_annotation(0.5)は表示されないことを確認
        for i in range(self.list_controller.list_widget.count()):
            item = self.list_controller.list_widget.item(i)
            assert item.annotation.confidence_score >= 0.7
    
    def test_update_list_combined_filters(self):
        """複合フィルターでのリスト更新テスト"""
        # Actionタイプかつ信頼度0.7以上
        self.list_controller.current_type_filter = "Action"
        self.list_controller.current_confidence_threshold = 0.7
        self.list_controller.update_list()
        
        # action_annotation(Action, 0.9)のみ表示されることを確認
        assert self.list_controller.list_widget.count() == 1
        
        item = self.list_controller.list_widget.item(0)
        assert item.annotation == self.action_annotation
        assert item.annotation.annotation_type == "Action"
        assert item.annotation.confidence_score >= 0.7
    
    def test_select_annotation(self):
        """アノテーション選択テスト"""
        # まずリストを更新
        self.list_controller.update_list()
        
        # 特定のアノテーションを選択
        self.list_controller.select_annotation(self.action_annotation)
        
        # 選択されたアイテムが正しいことを確認
        current_item = self.list_controller.list_widget.currentItem()
        assert current_item is not None
        assert current_item.annotation == self.action_annotation
    
    def test_select_annotation_not_in_list(self):
        """リストにないアノテーションの選択テスト"""
        # フィルターでStepのみ表示
        self.list_controller.current_type_filter = "Step"
        self.list_controller.update_list()
        
        # Actionアノテーションを選択しようとする（リストにない）
        self.list_controller.select_annotation(self.action_annotation)
        
        # 何も選択されないことを確認
        current_item = self.list_controller.list_widget.currentItem()
        assert current_item is None or current_item.annotation != self.action_annotation
    
    def test_get_selected_annotation(self):
        """選択中アノテーション取得テスト"""
        # まずリストを更新
        self.list_controller.update_list()
        
        # アノテーションを選択
        self.list_controller.select_annotation(self.step_annotation)
        
        # 選択されたアノテーションを取得
        selected = self.list_controller.get_selected_annotation()
        assert selected == self.step_annotation
    
    def test_get_selected_annotation_none(self):
        """未選択時のアノテーション取得テスト"""
        # まずリストを更新
        self.list_controller.update_list()
        
        # 何も選択しない
        self.list_controller.list_widget.clearSelection()
        
        # Noneが返されることを確認
        selected = self.list_controller.get_selected_annotation()
        assert selected is None
    
    def test_set_confidence_threshold(self):
        """信頼度閾値設定テスト"""
        with patch.object(self.list_controller, 'filter_changed') as mock_signal:
            self.list_controller.set_confidence_threshold(0.8)
            
            assert self.list_controller.current_confidence_threshold == 0.8
            assert self.list_controller.confidence_slider.value() == 80  # 0.8 * 100
            
            # シグナルが発信されたことを確認
            mock_signal.emit.assert_called_once_with("All", 0.8)
    
    def test_get_current_filters(self):
        """現在のフィルター取得テスト"""
        self.list_controller.current_type_filter = "Action"
        self.list_controller.current_confidence_threshold = 0.7
        
        filters = self.list_controller.get_current_filters()
        
        assert filters['type_filter'] == "Action"
        assert filters['confidence_threshold'] == 0.7
    
    def test_get_list_widget(self):
        """リストウィジェット取得テスト"""
        widget = self.list_controller.get_list_widget()
        assert isinstance(widget, QWidget)
        assert widget == self.list_controller.main_widget
    
    def test_type_filter_change(self):
        """タイプフィルター変更テスト"""
        with patch.object(self.list_controller, 'filter_changed') as mock_signal, \
             patch.object(self.list_controller, 'update_list') as mock_update:
            
            # フィルター変更をシミュレート
            self.list_controller._on_type_filter_changed("Step")
            
            assert self.list_controller.current_type_filter == "Step"
            
            # シグナルとリスト更新が呼ばれることを確認
            mock_signal.emit.assert_called_once_with("Step", 0.0)
            mock_update.assert_called_once()
    
    def test_confidence_slider_change(self):
        """信頼度スライダー変更テスト"""
        with patch.object(self.list_controller, 'filter_changed') as mock_signal, \
             patch.object(self.list_controller, 'update_list') as mock_update:
            
            # スライダー変更をシミュレート（スライダー値は0-100）
            self.list_controller._on_confidence_changed(75)  # 0.75に相当
            
            assert self.list_controller.current_confidence_threshold == 0.75
            
            # シグナルとリスト更新が呼ばれることを確認
            mock_signal.emit.assert_called_once_with("All", 0.75)
            mock_update.assert_called_once()
    
    def test_item_selection_change(self):
        """アイテム選択変更テスト"""
        # まずリストを更新
        self.list_controller.update_list()
        
        with patch.object(self.list_controller, 'annotation_selected') as mock_signal:
            # アイテムを選択
            item = self.list_controller.list_widget.item(0)
            self.list_controller.list_widget.setCurrentItem(item)
            
            # 選択変更をシミュレート
            self.list_controller._on_item_selection_changed()
            
            # シグナルが発信されたことを確認
            mock_signal.emit.assert_called_once_with(item.annotation)
    
    def test_data_manager_signals(self):
        """データマネージャーシグナル連携テスト"""
        with patch.object(self.list_controller, 'update_list') as mock_update:
            # データ変更シグナルをシミュレート
            self.data_manager.data_changed.emit()
            
            # update_listが呼ばれることを確認
            mock_update.assert_called_once()


if __name__ == "__main__":
    import unittest
    
    # ログ設定
    logging.basicConfig(level=logging.DEBUG)
    
    # unittestの実行
    unittest.main()
