# STTExportDialog.py  
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,   
                            QComboBox, QPushButton, QScrollArea, QWidget)  
from typing import List, Dict  
  
class STTExportDialog(QDialog):  
    """STTデータセットエクスポート用ダイアログ"""  
      
    def __init__(self, video_names: List[str], parent=None):  
        super().__init__(parent)  
        self.video_names = video_names  
        self.subset_settings: Dict[str, str] = {}  
        self.subset_combos: Dict[str, QComboBox] = {}  
          
        self.setup_ui()  
          
    def setup_ui(self):  
        """UIセットアップ"""  
        self.setWindowTitle("Export STT Dataset")  
        self.setModal(True)  
        self.resize(400, 300)  
          
        layout = QVBoxLayout()  
          
        # 説明ラベル  
        info_label = QLabel("各動画のサブセット設定を選択してください:")  
        layout.addWidget(info_label)  
          
        # スクロールエリア  
        scroll_area = QScrollArea()  
        scroll_widget = QWidget()  
        scroll_layout = QVBoxLayout()  
          
        # 各動画のサブセット選択  
        for video_name in self.video_names:  
            video_layout = QHBoxLayout()  
              
            # 動画名ラベル  
            name_label = QLabel(video_name)  
            name_label.setMinimumWidth(200)  
            video_layout.addWidget(name_label)  
              
            # サブセット選択コンボボックス  
            subset_combo = QComboBox()  
            subset_combo.addItems(["train", "test", "validation"])  
            subset_combo.setCurrentText("train")  # デフォルト  
            self.subset_combos[video_name] = subset_combo  
            video_layout.addWidget(subset_combo)  
              
            scroll_layout.addLayout(video_layout)  
          
        scroll_widget.setLayout(scroll_layout)  
        scroll_area.setWidget(scroll_widget)  
        scroll_area.setWidgetResizable(True)  
        layout.addWidget(scroll_area)  
          
        # ボタン  
        button_layout = QHBoxLayout()  
          
        self.ok_button = QPushButton("OK")  
        self.ok_button.clicked.connect(self.accept)  
        button_layout.addWidget(self.ok_button)  
          
        self.cancel_button = QPushButton("Cancel")  
        self.cancel_button.clicked.connect(self.reject)  
        button_layout.addWidget(self.cancel_button)  
          
        layout.addLayout(button_layout)  
        self.setLayout(layout)  
      
    def get_subset_settings(self) -> Dict[str, str]:  
        """サブセット設定を取得"""  
        settings = {}  
        for video_name, combo in self.subset_combos.items():  
            settings[video_name] = combo.currentText()  
        return settings