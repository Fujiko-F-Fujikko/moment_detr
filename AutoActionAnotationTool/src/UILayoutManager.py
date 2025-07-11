# UILayoutManager.py (修正版)  
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,   
                            QComboBox, QListWidget, QSlider, QLabel,   
                            QDoubleSpinBox, QPushButton, QSplitter)  
from PyQt6.QtCore import Qt  
from HandTypeFilterManager import HandTypeFilterManager  
from IntegratedEditWidget import IntegratedEditWidget  
  
class UILayoutManager:  
    def __init__(self, main_window=None):    
        self.ui_components = {}    
        self.main_window = main_window
        self.hand_type_filter_manager = HandTypeFilterManager()    
        print("UILayoutManager initialized. main_window:", main_window)
        self.integrated_edit_widget = IntegratedEditWidget(main_window)

    def create_main_layout(self, left_panel, right_panel):  
        """メインレイアウトを作成（スプリッター使用）"""  
        splitter = QSplitter(Qt.Orientation.Horizontal)  
        splitter.addWidget(left_panel)  
        splitter.addWidget(right_panel)  
          
        # 初期サイズ比率を設定  
        splitter.setSizes([800, 600])  
          
        # 最小幅を設定  
        left_panel.setMinimumWidth(400)  
        right_panel.setMinimumWidth(350)  
          
        splitter.setChildrenCollapsible(False)  
        return splitter  
      
    def create_left_panel(self, video_widget, controls_layout, multi_timeline_viewer):  
        """左パネルを作成（垂直スプリッター使用）"""  
        vertical_splitter = QSplitter(Qt.Orientation.Vertical)  
          
        # 上部：動画プレイヤーとコントロール  
        video_container = QWidget()  
        video_layout = QVBoxLayout()  
        video_layout.addWidget(video_widget)  
          
        # コントロールレイアウトをウィジェットに包んで高さ制御  
        controls_widget = QWidget()  
        controls_widget.setLayout(controls_layout)  
        controls_widget.setMaximumHeight(60)  
          
        video_layout.addWidget(controls_widget)  
        video_container.setLayout(video_layout)  
          
        # スプリッターに追加  
        vertical_splitter.addWidget(video_container)  
        vertical_splitter.addWidget(multi_timeline_viewer)  
          
        # 初期サイズ比率を設定  
        vertical_splitter.setSizes([300, 200])  
          
        # 最小サイズを設定  
        video_container.setMinimumHeight(200)  
        multi_timeline_viewer.setMinimumHeight(100)  
          
        vertical_splitter.setChildrenCollapsible(False)  
          
        return vertical_splitter  
      
    def create_right_panel(self):  
        """右パネルを作成（新しい構造）"""  
        right_widget = QWidget()  
        layout = QVBoxLayout()  
          
        # Hand Type フィルタグループ  
        filter_group, filter_components = self.create_hand_type_filter_group()  
        layout.addWidget(filter_group)  
          
        # Detection Results グループ  
        results_group, results_components = self.create_detection_results_group()  
        layout.addWidget(results_group)  
          
        # Confidence Filter グループ（Saliency Threshold削除）  
        confidence_group, confidence_components = self.create_confidence_filter_group()  
        layout.addWidget(confidence_group)  
          
        # Edit Selected グループ（統合編集ウィジェット）  
        layout.addWidget(self.integrated_edit_widget)  
          
        right_widget.setLayout(layout)  
          
        # UI要素を統合  
        ui_components = {}  
        ui_components.update(filter_components)  
        ui_components.update(results_components)  
        ui_components.update(confidence_components)  
          
        return right_widget, ui_components  
      
    def create_hand_type_filter_group(self):  
        """Hand Type フィルタグループを作成"""  
        group = QGroupBox("Filter by Hand Type")  
        layout = QVBoxLayout()  
          
        # Hand Type フィルタコンボボックス  
        hand_type_combo = QComboBox()  
        hand_type_combo.addItems(["All", "LeftHand", "RightHand", "BothHands", "Other"])  
        hand_type_combo.currentTextChanged.connect(self.hand_type_filter_manager.set_filter)  
          
        layout.addWidget(QLabel("Hand Type:"))  
        layout.addWidget(hand_type_combo)  
          
        group.setLayout(layout)  
          
        components = {  
            'hand_type_combo': hand_type_combo  
        }  
          
        return group, components  
      
    def create_detection_results_group(self):  
        """Detection Results グループを作成"""  
        group = QGroupBox("Detection Results")  
        layout = QVBoxLayout()  
          
        # 結果リスト  
        results_list = QListWidget()  
        results_list.setMinimumHeight(200)  
          
        layout.addWidget(results_list)  
        group.setLayout(layout)  
          
        components = {  
            'results_list': results_list  
        }  
          
        return group, components  
      
    def create_confidence_filter_group(self):  
        """Confidence Filter グループを作成（Saliency Threshold削除）"""  
        group = QGroupBox("Filters")  
        layout = QVBoxLayout()  
          
        # Confidence Threshold のみ  
        confidence_layout = QHBoxLayout()  
        confidence_slider = QSlider(Qt.Orientation.Horizontal)  
        confidence_slider.setRange(0, 100)  
        confidence_slider.setValue(0)  
        confidence_value_label = QLabel("0.00")  
          
        confidence_layout.addWidget(QLabel("Confidence:"))  
        confidence_layout.addWidget(confidence_slider)  
        confidence_layout.addWidget(confidence_value_label)  
          
        layout.addLayout(confidence_layout)  
        group.setLayout(layout)  
          
        components = {  
            'confidence_slider': confidence_slider,  
            'confidence_value_label': confidence_value_label  
        }  
          
        return group, components

    def setup_tab_order(self):  
        """タブオーダーを設定"""  
        # Hand Type Filter  
        self.hand_type_combo.setTabOrder(self.hand_type_combo, self.results_list)  
        
        # Results List  
        self.results_list.setTabOrder(self.results_list, self.confidence_slider)  
        
        # Confidence Filter  
        self.confidence_slider.setTabOrder(self.confidence_slider, self.integrated_edit_widget)