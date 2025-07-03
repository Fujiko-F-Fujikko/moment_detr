from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSlider, QComboBox, QGroupBox, QSplitter, 
    QPushButton, QDoubleSpinBox, QFormLayout, QListWidget
)
from PyQt6.QtCore import Qt


class UILayoutManager:
    """UIレイアウトの作成と管理を担当するクラス"""
    
    def __init__(self):
        self.ui_components = {}
        
    def create_main_layout(self, left_panel: QWidget, right_panel: QWidget) -> QHBoxLayout:
        """メインレイアウトを作成"""
        main_layout = QHBoxLayout()
        
        # スプリッター
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
        return main_layout
        
    def create_left_panel(self, video_widget, controls_layout, multi_timeline_viewer) -> QWidget:
        """左パネル（動画プレイヤーとタイムライン）を作成"""
        left_widget = QWidget()
        layout = QVBoxLayout()
        
        # 動画プレイヤー
        layout.addWidget(video_widget, stretch=2)
        
        # 動画コントロール
        layout.addLayout(controls_layout)
        
        # 複数タイムラインビューア
        layout.addWidget(multi_timeline_viewer, stretch=2)
        
        left_widget.setLayout(layout)
        return left_widget
        
    def create_right_panel(self) -> tuple[QWidget, dict]:
        """右パネル（コントロールと編集）を作成"""
        right_widget = QWidget()
        right_widget.setMaximumWidth(350)
        layout = QVBoxLayout()
        
        # UIコンポーネントを格納する辞書
        components = {}
        
        # フィルタ設定
        filter_group, filter_components = self.create_filter_group()
        components.update(filter_components)
        layout.addWidget(filter_group)
        
        # 区間編集
        edit_group, edit_components = self.create_edit_group()
        components.update(edit_components)
        layout.addWidget(edit_group)
        
        # Detection Results表示
        results_group, results_components = self.create_results_group()
        components.update(results_components)
        layout.addWidget(results_group, stretch=2)
        
        right_widget.setLayout(layout)
        return right_widget, components
        
    def create_filter_group(self) -> tuple[QGroupBox, dict]:
        """フィルタ設定グループを作成"""
        filter_group = QGroupBox("Filters")
        filter_layout = QVBoxLayout()
        
        components = {}
        
        # 信頼度閾値のレイアウト
        confidence_layout = QHBoxLayout()
        confidence_layout.addWidget(QLabel("Confidence Threshold:"))
        confidence_slider = QSlider(Qt.Orientation.Horizontal)
        confidence_slider.setRange(0, 100)
        confidence_slider.setValue(10)
        confidence_value_label = QLabel("0.10")
        confidence_layout.addWidget(confidence_slider)
        confidence_layout.addWidget(confidence_value_label)
        
        # 顕著性閾値のレイアウト
        saliency_layout = QHBoxLayout()
        saliency_layout.addWidget(QLabel("Saliency Threshold:"))
        threshold_slider = QSlider(Qt.Orientation.Horizontal)
        threshold_slider.setRange(-100, 100)
        threshold_slider.setValue(0)
        threshold_value_label = QLabel("0.00")
        saliency_layout.addWidget(threshold_slider)
        saliency_layout.addWidget(threshold_value_label)
        
        filter_layout.addLayout(saliency_layout)
        filter_layout.addLayout(confidence_layout)
        filter_group.setLayout(filter_layout)
        
        # コンポーネントを辞書に格納
        components['confidence_slider'] = confidence_slider
        components['confidence_value_label'] = confidence_value_label
        components['threshold_slider'] = threshold_slider
        components['threshold_value_label'] = threshold_value_label
        
        return filter_group, components
        
    def create_edit_group(self) -> tuple[QGroupBox, dict]:
        """区間編集グループを作成"""
        edit_group = QGroupBox("Edit Selected")
        edit_layout = QFormLayout()
        
        components = {}
        
        # スピンボックス
        start_spinbox = QDoubleSpinBox()
        start_spinbox.setRange(0, 99999)
        start_spinbox.setDecimals(2)
        start_spinbox.setSuffix(" s")
        
        end_spinbox = QDoubleSpinBox()
        end_spinbox.setRange(0, 99999)
        end_spinbox.setDecimals(2)
        end_spinbox.setSuffix(" s")
        
        edit_layout.addRow("Start:", start_spinbox)
        edit_layout.addRow("End:", end_spinbox)
        
        # 信頼度表示ラベル
        confidence_label = QLabel("0.0000")
        edit_layout.addRow("Confidence:", confidence_label)
        
        # 編集ボタン（水平レイアウト）
        button_layout = QHBoxLayout()
        apply_button = QPushButton("Apply")
        delete_button = QPushButton("Delete")
        add_button = QPushButton("Add")
        
        # ボタンサイズを小さく
        for btn in [apply_button, delete_button, add_button]:
            btn.setMaximumHeight(30)
            
        button_layout.addWidget(apply_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(add_button)
        
        edit_layout.addRow(button_layout)
        edit_group.setLayout(edit_layout)
        
        # コンポーネントを辞書に格納
        components['start_spinbox'] = start_spinbox
        components['end_spinbox'] = end_spinbox
        components['confidence_label'] = confidence_label
        components['apply_button'] = apply_button
        components['delete_button'] = delete_button
        components['add_button'] = add_button
        
        return edit_group, components
        
    def create_results_group(self) -> tuple[QGroupBox, dict]:
        """結果表示グループを作成"""
        results_group = QGroupBox("Detection Results")
        results_layout = QVBoxLayout()
        
        components = {}
        
        # クエリ選択
        query_layout = QHBoxLayout()
        query_layout.addWidget(QLabel("Query:"))
        query_combo = QComboBox()
        query_layout.addWidget(query_combo)
        results_layout.addLayout(query_layout)
        
        # 結果リスト
        results_list = QListWidget()
        results_layout.addWidget(results_list)
        
        results_group.setLayout(results_layout)
        
        # コンポーネントを辞書に格納
        components['query_combo'] = query_combo
        components['results_list'] = results_list
        
        print(f"UILayoutManager: Created query_combo: {query_combo} (type: {type(query_combo)})")
        print(f"UILayoutManager: Created results_list: {results_list} (type: {type(results_list)})")
        
        return results_group, components
