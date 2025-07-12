# ControlPanelBuilder.py  
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,  
                            QComboBox, QListWidget, QSlider, QLabel)  
from PyQt6.QtCore import Qt  
from typing import Dict, Any, Tuple  
  
class ControlPanelBuilder:  
    """右パネルのコントロール要素構築を担当するクラス"""  
      
    def __init__(self):  
        self.ui_components: Dict[str, Any] = {}  
      
    def create_control_panel(self) -> Tuple[QWidget, Dict[str, Any]]:  
        """右パネル全体を構築"""  
        right_widget = QWidget()  
        layout = QVBoxLayout()  
          
        # Hand Type フィルタグループ  
        filter_group, filter_components = self.create_filter_controls()  
        layout.addWidget(filter_group)  
        self.ui_components.update(filter_components)  
          
        # Detection Results グループ  
        results_group, results_components = self.create_results_display()  
        layout.addWidget(results_group)  
        self.ui_components.update(results_components)  
          
        # Confidence Filter グループ  
        confidence_group, confidence_components = self.create_confidence_controls()  
        layout.addWidget(confidence_group)  
        self.ui_components.update(confidence_components)  
          
        right_widget.setLayout(layout)  
        return right_widget, self.ui_components.copy()  
      
    def create_filter_controls(self) -> Tuple[QGroupBox, Dict[str, Any]]:  
        """Hand Type フィルタコントロールを作成"""  
        group = QGroupBox("Filter by Hand Type")  
        layout = QVBoxLayout()  
          
        # Hand Type フィルタコンボボックス  
        hand_type_combo = QComboBox()  
        hand_type_combo.addItems(["All", "LeftHand", "RightHand", "BothHands", "Other"])  
          
        layout.addWidget(QLabel("Hand Type:"))  
        layout.addWidget(hand_type_combo)  
          
        group.setLayout(layout)  
          
        components = {  
            'hand_type_combo': hand_type_combo  
        }  
          
        return group, components  
      
    def create_results_display(self) -> Tuple[QGroupBox, Dict[str, Any]]:  
        """Detection Results 表示を作成"""  
        group = QGroupBox("Detection Results")  
        layout = QVBoxLayout()  
          
        # 結果リスト  
        results_list = QListWidget()  
        results_list.setMinimumHeight(200)  
          
        # スタイルシートを適用  
        results_list.setStyleSheet("""  
            QListWidget::item:selected {  
                background-color: #3daee9;  
                color: white;  
                border: 2px solid #2980b9;  
            }  
            QListWidget::item:hover {  
                background-color: #e3f2fd;  
            }  
        """)  
          
        layout.addWidget(results_list)  
        group.setLayout(layout)  
          
        components = {  
            'results_list': results_list  
        }  
          
        return group, components  
      
    def create_confidence_controls(self) -> Tuple[QGroupBox, Dict[str, Any]]:  
        """Confidence フィルタコントロールを作成"""  
        group = QGroupBox("Filters")  
        layout = QVBoxLayout()  
          
        # Confidence Threshold  
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
      
    def get_ui_components(self) -> Dict[str, Any]:  
        """作成されたUI要素の辞書を取得"""  
        return self.ui_components.copy()  
      
    def create_custom_filter_group(self, title: str, controls: Dict[str, Any]) -> Tuple[QGroupBox, Dict[str, Any]]:  
        """カスタムフィルタグループを作成（拡張用）"""  
        group = QGroupBox(title)  
        layout = QVBoxLayout()  
          
        components = {}  
          
        for control_name, control_config in controls.items():  
            if control_config['type'] == 'combo':  
                combo = QComboBox()  
                combo.addItems(control_config.get('items', []))  
                layout.addWidget(QLabel(control_config.get('label', control_name)))  
                layout.addWidget(combo)  
                components[control_name] = combo  
                  
            elif control_config['type'] == 'slider':  
                slider_layout = QHBoxLayout()  
                slider = QSlider(Qt.Orientation.Horizontal)  
                slider.setRange(control_config.get('min', 0), control_config.get('max', 100))  
                slider.setValue(control_config.get('default', 0))  
                  
                value_label = QLabel(str(control_config.get('default', 0)))  
                  
                slider_layout.addWidget(QLabel(control_config.get('label', control_name)))  
                slider_layout.addWidget(slider)  
                slider_layout.addWidget(value_label)  
                  
                layout.addLayout(slider_layout)  
                components[control_name] = slider  
                components[f"{control_name}_label"] = value_label  
          
        group.setLayout(layout)  
        return group, components  
      
    def apply_theme(self, theme_name: str):  
        """テーマを適用（将来の拡張用）"""  
        if theme_name == "dark":  
            # ダークテーマの設定  
            pass  
        elif theme_name == "light":  
            # ライトテーマの設定  
            pass