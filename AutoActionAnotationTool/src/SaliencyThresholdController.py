from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSlider
from PyQt6.QtCore import Qt, pyqtSignal

class SaliencyThresholdController(QWidget):  
    thresholdChanged = pyqtSignal(float)  
      
    def __init__(self):  
        super().__init__()  
        layout = QHBoxLayout()  
          
        layout.addWidget(QLabel("Saliency Threshold:"))  
          
        self.slider = QSlider(Qt.Horizontal)  
        self.slider.setRange(-100, 100)  # -1.0 to 1.0 scaled  
        self.slider.setValue(0)  
          
        self.value_label = QLabel("0.00")  
          
        layout.addWidget(self.slider)  
        layout.addWidget(self.value_label)  
          
        self.setLayout(layout)  
          
        self.slider.valueChanged.connect(self.on_slider_changed)  
      
    def on_slider_changed(self, value):  
        threshold = value / 100.0  # Convert back to -1.0 to 1.0  
        self.value_label.setText(f"{threshold:.2f}")  
        self.thresholdChanged.emit(threshold)  