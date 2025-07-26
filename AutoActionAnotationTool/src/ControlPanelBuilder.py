# ControlPanelBuilder.py (新規実装)  
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,   
                            QSlider, QComboBox, QListWidget, QGroupBox,   
                            QListWidgetItem)  
from PyQt6.QtCore import Qt, pyqtSignal  
from typing import Dict, Any, List  
  
class ControlPanelBuilder(QWidget):  
    """右パネルのコントロール要素構築を担当するクラス"""  
      
    # シグナル定義  
    confidenceChanged = pyqtSignal(float)  
    handTypeFilterChanged = pyqtSignal(str)  
    resultItemClicked = pyqtSignal(object)  
      
    def __init__(self, parent=None):  
        super().__init__(parent)  
        self.ui_components: Dict[str, Any] = {}  
        self.setup_ui()  
      
    def setup_ui(self):  
        """UIレイアウトの設定"""  
        layout = QVBoxLayout()  
          
        # フィルタコントロールグループ  
        filter_group = self.create_filter_controls()  
        layout.addWidget(filter_group)  
          
        # 結果表示グループ  
        results_group = self.create_results_display()  
        layout.addWidget(results_group)  
          
        # 信頼度コントロールグループ  
        confidence_group = self.create_confidence_controls()  
        layout.addWidget(confidence_group)  
          
        self.setLayout(layout)  
      
    def create_filter_controls(self) -> QGroupBox:  
        """フィルタコントロールを作成"""  
        group = QGroupBox("Filters")  
        layout = QVBoxLayout()  
          
        # Hand Typeフィルタ  
        hand_type_layout = QHBoxLayout()  
        hand_type_label = QLabel("Hand Type:")  
        hand_type_combo = QComboBox()  
        hand_type_combo.addItems(["All", "LeftHand", "RightHand", "BothHands", "Other"])  
        hand_type_combo.setCurrentText("All")  
        hand_type_combo.currentTextChanged.connect(self.handTypeFilterChanged.emit)  
          
        hand_type_layout.addWidget(hand_type_label)  
        hand_type_layout.addWidget(hand_type_combo)  
        layout.addLayout(hand_type_layout)  
          
        # UI要素を保存  
        self.ui_components['hand_type_combo'] = hand_type_combo  
          
        group.setLayout(layout)  
        return group  
      
    def create_results_display(self) -> QGroupBox:  
        """結果表示を作成"""  
        group = QGroupBox("Detection Results")  
        layout = QVBoxLayout()  
        
        # 結果リスト  
        results_list = QListWidget()  
        results_list.itemClicked.connect(self._on_result_item_clicked)  
        
        # デバッグ用の初期アイテムを追加  
        debug_item = QListWidgetItem("No results loaded yet...")  
        debug_item.setFlags(debug_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)  
        results_list.addItem(debug_item)  
        
        layout.addWidget(results_list)  
        
        # UI要素を保存  
        self.ui_components['results_list'] = results_list  
        print("DEBUG: ControlPanelBuilder created results_list")  
        
        group.setLayout(layout)  
        return group 
      
    def create_confidence_controls(self) -> QGroupBox:  
        """信頼度コントロールを作成"""  
        group = QGroupBox("Confidence Threshold")  
        layout = QVBoxLayout()  
          
        # 信頼度スライダー  
        slider_layout = QHBoxLayout()  
        confidence_slider = QSlider(Qt.Orientation.Horizontal)  
        confidence_slider.setMinimum(0)  
        confidence_slider.setMaximum(100)  
        confidence_slider.setValue(0)  
        confidence_slider.valueChanged.connect(self._on_confidence_changed)  
          
        confidence_value_label = QLabel("0.00")  
        confidence_value_label.setMinimumWidth(40)  
          
        slider_layout.addWidget(QLabel("Confidence:"))  
        slider_layout.addWidget(confidence_slider)  
        slider_layout.addWidget(confidence_value_label)  
        layout.addLayout(slider_layout)  
          
        # UI要素を保存  
        self.ui_components['confidence_slider'] = confidence_slider  
        self.ui_components['confidence_value_label'] = confidence_value_label  
          
        group.setLayout(layout)  
        return group  
      
    def _on_confidence_changed(self, value: int):  
        """信頼度スライダー変更時の処理"""  
        confidence = value / 100.0  
        self.ui_components['confidence_value_label'].setText(f"{confidence:.2f}")  
        self.confidenceChanged.emit(confidence)  
      
    def _on_result_item_clicked(self, item):  
        """結果アイテムクリック時の処理"""  
        if hasattr(item, 'data') and item.data(Qt.ItemDataRole.UserRole):  
            query_result = item.data(Qt.ItemDataRole.UserRole)  
            self.resultItemClicked.emit(query_result)  
      
    def get_ui_components(self) -> Dict[str, Any]:  
        """UI要素を取得"""  
        return self.ui_components  
      
    def update_results_display(self, query_results: List):  
        """結果表示を更新"""  
        results_list = self.ui_components.get('results_list')  
        if results_list:  
            results_list.clear()  
            for result in query_results:  
                item_text = f"{result.query_text} ({len(result.relevant_windows)} intervals)"  
                item = results_list.addItem(item_text)  
                if hasattr(results_list, 'item'):  
                    list_item = results_list.item(results_list.count() - 1)  
                    list_item.setData(Qt.ItemDataRole.UserRole, result)