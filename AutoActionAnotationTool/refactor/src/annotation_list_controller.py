# annotation_list_controller.py
"""
アノテーションリストコントロールクラス
アノテーション一覧の表示と選択管理
"""

from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                           QListWidgetItem, QLabel, QComboBox, QSlider, 
                           QPushButton, QSplitter)
from PyQt6.QtGui import QFont
import logging
from typing import List, Optional

from annotation_data_manager import AnnotationDataManager, AnnotationItem


class AnnotationListItem(QListWidgetItem):
    """アノテーションリストアイテム"""
    
    def __init__(self, annotation: AnnotationItem):
        super().__init__()
        self.annotation = annotation
        self.update_display()
    
    def update_display(self):
        """表示更新"""
        start_time = self.annotation.start_time
        end_time = self.annotation.end_time
        category = self.annotation.category
        confidence = self.annotation.confidence_score
        
        # 時間フォーマット
        start_str = f"{int(start_time//60):02d}:{int(start_time%60):02d}"
        end_str = f"{int(end_time//60):02d}:{int(end_time%60):02d}"
        
        # 表示テキスト
        text = f"[{start_str}-{end_str}] {category} ({confidence:.2f})"
        
        # タイプ別の表示調整
        if self.annotation.annotation_type == 'step':
            text = f"📝 {text}"
        else:
            text = f"🎬 {text}"
        
        self.setText(text)
        
        # ツールチップ
        tooltip_parts = [
            f"Type: {self.annotation.annotation_type}",
            f"Category: {category}",
            f"Time: {start_time:.2f}s - {end_time:.2f}s",
            f"Duration: {end_time - start_time:.2f}s",
            f"Confidence: {confidence:.3f}"
        ]
        
        if self.annotation.hand_type:
            tooltip_parts.append(f"Hand: {self.annotation.hand_type}")
        if self.annotation.object_name:
            tooltip_parts.append(f"Object: {self.annotation.object_name}")
        if self.annotation.verb:
            tooltip_parts.append(f"Verb: {self.annotation.verb}")
        
        self.setToolTip("\n".join(tooltip_parts))


class AnnotationListController(QObject):
    """アノテーションリストコントロールクラス"""
    
    annotation_selected = pyqtSignal(object, int)  # AnnotationItem, index
    filter_changed = pyqtSignal()
    
    def __init__(self, data_manager: AnnotationDataManager):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.data_manager = data_manager
        
        # UIコンポーネント
        self.list_widget = None
        self.main_widget = None
        self.type_filter = None
        self.confidence_slider = None
        self.confidence_label = None
        self.count_label = None
        
        # フィルタ状態
        self.current_type_filter = "all"  # "all", "action", "step"
        self.current_confidence_threshold = 0.0
        
        self._setup_ui()
        self._connect_data_manager()
        
        self.logger.info("AnnotationListController initialized")
    
    def _setup_ui(self):
        """UI設定"""
        self.main_widget = QWidget()
        layout = QVBoxLayout(self.main_widget)
        
        # フィルタコントロール
        filter_widget = self._create_filter_controls()
        layout.addWidget(filter_widget)
        
        # アノテーションリスト
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.list_widget)
        
        # ステータス表示
        self.count_label = QLabel("0 annotations")
        self.count_label.setStyleSheet("color: gray; font-size: 12px;")
        layout.addWidget(self.count_label)
    
    def _create_filter_controls(self) -> QWidget:
        """フィルタコントロール作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # タイトル
        title_label = QLabel("Annotations")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # タイプフィルタ
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All", "Actions", "Steps"])
        self.type_filter.currentTextChanged.connect(self._on_type_filter_changed)
        type_layout.addWidget(self.type_filter)
        
        layout.addLayout(type_layout)
        
        # 信頼度フィルタ
        confidence_layout = QVBoxLayout()
        
        confidence_header_layout = QHBoxLayout()
        confidence_header_layout.addWidget(QLabel("Confidence:"))
        
        self.confidence_label = QLabel("0.00")
        self.confidence_label.setMinimumWidth(40)
        confidence_header_layout.addWidget(self.confidence_label)
        confidence_header_layout.addStretch()
        
        confidence_layout.addLayout(confidence_header_layout)
        
        self.confidence_slider = QSlider(Qt.Orientation.Horizontal)
        self.confidence_slider.setMinimum(0)
        self.confidence_slider.setMaximum(100)
        self.confidence_slider.setValue(0)
        self.confidence_slider.valueChanged.connect(self._on_confidence_changed)
        confidence_layout.addWidget(self.confidence_slider)
        
        layout.addLayout(confidence_layout)
        
        # 操作ボタン
        button_layout = QHBoxLayout()
        
        clear_button = QPushButton("Clear Selection")
        clear_button.clicked.connect(self._clear_selection)
        button_layout.addWidget(clear_button)
        
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.update_list)
        button_layout.addWidget(refresh_button)
        
        layout.addLayout(button_layout)
        
        return widget
    
    def _connect_data_manager(self):
        """データマネージャーとの接続"""
        self.data_manager.data_changed.connect(self.update_list)
        self.data_manager.annotation_added.connect(self.update_list)
        self.data_manager.annotation_modified.connect(self.update_list)
        self.data_manager.annotation_deleted.connect(self.update_list)
    
    def update_list(self):
        """リスト更新"""
        self.logger.debug("Updating annotation list")
        
        # フィルタリング
        annotations = self._get_filtered_annotations()
        
        # リストクリア
        self.list_widget.clear()
        
        # アイテム追加
        for annotation in annotations:
            item = AnnotationListItem(annotation)
            self.list_widget.addItem(item)
        
        # カウント更新
        total_count = len(self.data_manager.annotations)
        filtered_count = len(annotations)
        self.count_label.setText(f"{filtered_count} / {total_count} annotations")
        
        self.logger.debug(f"List updated: {filtered_count} items displayed")
    
    def _get_filtered_annotations(self) -> List[AnnotationItem]:
        """フィルタリング済みアノテーション取得"""
        annotations = self.data_manager.annotations.copy()
        
        # タイプフィルタ
        if self.current_type_filter == "action":
            annotations = [ann for ann in annotations if ann.annotation_type == 'action']
        elif self.current_type_filter == "step":
            annotations = [ann for ann in annotations if ann.annotation_type == 'step']
        
        # 信頼度フィルタ
        annotations = [ann for ann in annotations 
                      if ann.confidence_score >= self.current_confidence_threshold]
        
        # 時間順でソート
        annotations.sort(key=lambda x: x.start_time)
        
        return annotations
    
    def get_list_widget(self) -> QWidget:
        """メインウィジェット取得"""
        return self.main_widget
    
    def select_annotation(self, annotation: AnnotationItem):
        """アノテーション選択"""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if isinstance(item, AnnotationListItem) and item.annotation == annotation:
                self.list_widget.setCurrentItem(item)
                self.list_widget.scrollToItem(item)
                break
    
    def get_selected_annotation(self) -> Optional[AnnotationItem]:
        """選択中のアノテーション取得"""
        current_item = self.list_widget.currentItem()
        if isinstance(current_item, AnnotationListItem):
            return current_item.annotation
        return None
    
    def _on_item_clicked(self, item: QListWidgetItem):
        """アイテムクリック処理"""
        if isinstance(item, AnnotationListItem):
            # インデックス取得
            index = -1
            all_annotations = self.data_manager.annotations
            for i, annotation in enumerate(all_annotations):
                if annotation == item.annotation:
                    index = i
                    break
            
            self.logger.info(f"Annotation selected: {item.annotation.id}")
            self.annotation_selected.emit(item.annotation, index)
    
    def _on_item_double_clicked(self, item: QListWidgetItem):
        """アイテムダブルクリック処理"""
        if isinstance(item, AnnotationListItem):
            self.logger.info(f"Annotation double-clicked: {item.annotation.id}")
            # ダブルクリック時はタイムラインにフォーカス（シグナル発信のみ）
            self._on_item_clicked(item)
    
    def _on_type_filter_changed(self, text: str):
        """タイプフィルタ変更処理"""
        filter_map = {
            "All": "all",
            "Actions": "action", 
            "Steps": "step"
        }
        
        self.current_type_filter = filter_map.get(text, "all")
        self.logger.debug(f"Type filter changed to: {self.current_type_filter}")
        self.update_list()
        self.filter_changed.emit()
    
    def _on_confidence_changed(self, value: int):
        """信頼度フィルタ変更処理"""
        threshold = value / 100.0
        self.current_confidence_threshold = threshold
        self.confidence_label.setText(f"{threshold:.2f}")
        
        self.logger.debug(f"Confidence threshold changed to: {threshold}")
        self.update_list()
        self.filter_changed.emit()
        
        # データマネージャーの閾値も更新
        self.data_manager.set_confidence_threshold(threshold)
    
    def _clear_selection(self):
        """選択クリア"""
        self.list_widget.clearSelection()
        self.list_widget.setCurrentItem(None)
        self.logger.debug("Selection cleared")
    
    def set_confidence_threshold(self, threshold: float):
        """信頼度閾値設定（外部から）"""
        self.current_confidence_threshold = threshold
        self.confidence_slider.setValue(int(threshold * 100))
        self.confidence_label.setText(f"{threshold:.2f}")
        self.update_list()
    
    def get_current_filters(self) -> dict:
        """現在のフィルタ設定取得"""
        return {
            'type_filter': self.current_type_filter,
            'confidence_threshold': self.current_confidence_threshold
        }
