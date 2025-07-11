from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,   
                            QComboBox, QPushButton, QGroupBox, QFormLayout)  
from PyQt6.QtCore import Qt  
  
class STTExportDialog(QDialog):  
    def __init__(self, video_names, parent=None):  
        super().__init__(parent)  
        self.video_names = video_names  
        self.subset_settings = {}  
        self.setup_ui()  
          
    def setup_ui(self):  
        self.setWindowTitle("STT Dataset Export Settings")  
        self.setModal(True)  
        self.resize(400, 300)  
          
        layout = QVBoxLayout()  
          
        # 説明ラベル  
        info_label = QLabel("動画のデータセット分類を設定してください：")  
        layout.addWidget(info_label)  
          
        # 動画毎の設定グループ  
        settings_group = QGroupBox("Dataset Subset Settings")  
        settings_layout = QFormLayout()  
          
        self.subset_combos = {}  
        for video_name in self.video_names:  
            combo = QComboBox()  
            combo.addItems(["train", "validation", "test"])  
            combo.setCurrentText("train")  # デフォルト値  
            self.subset_combos[video_name] = combo  
            settings_layout.addRow(f"{video_name}:", combo)  
          
        settings_group.setLayout(settings_layout)  
        layout.addWidget(settings_group)  
          
        # ボタン  
        button_layout = QHBoxLayout()  
        self.ok_button = QPushButton("Export")  
        self.cancel_button = QPushButton("Cancel")  
          
        self.ok_button.clicked.connect(self.accept)  
        self.cancel_button.clicked.connect(self.reject)  
          
        button_layout.addWidget(self.cancel_button)  
        button_layout.addWidget(self.ok_button)  
        layout.addLayout(button_layout)  
          
        self.setLayout(layout)  
      
    def get_subset_settings(self):  
        """各動画のsubset設定を取得"""  
        settings = {}  
        for video_name, combo in self.subset_combos.items():  
            settings[video_name] = combo.currentText()  
        return settings