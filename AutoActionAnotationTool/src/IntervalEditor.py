from PyQt6.QtWidgets import QWidget, QFormLayout, QDoubleSpinBox, QLineEdit, QHBoxLayout, QVBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal
from DetectionInterval import DetectionInterval


class IntervalEditor(QWidget):  
    intervalModified = pyqtSignal(DetectionInterval, DetectionInterval)  # old, new  
    intervalDeleted = pyqtSignal(DetectionInterval)  
    intervalAdded = pyqtSignal(DetectionInterval)  
      
    def __init__(self):  
        super().__init__()  
        self.current_interval = None  
        self.setup_ui()  
      
    def setup_ui(self):  
        layout = QFormLayout()  
          
        self.start_spinbox = QDoubleSpinBox()  
        self.start_spinbox.setRange(0, 99999)  
        self.start_spinbox.setDecimals(2)  
        self.start_spinbox.setSuffix(" s")  
          
        self.end_spinbox = QDoubleSpinBox()  
        self.end_spinbox.setRange(0, 99999)  
        self.end_spinbox.setDecimals(2)  
        self.end_spinbox.setSuffix(" s")  
          
        self.confidence_spinbox = QDoubleSpinBox()  
        self.confidence_spinbox.setRange(0, 1)  
        self.confidence_spinbox.setDecimals(4)  
        self.confidence_spinbox.setReadOnly(True)  
          
        self.label_edit = QLineEdit()  
          
        layout.addRow("Start Time:", self.start_spinbox)  
        layout.addRow("End Time:", self.end_spinbox)  
        layout.addRow("Confidence:", self.confidence_spinbox)  
        layout.addRow("Label:", self.label_edit)  
          
        # Buttons  
        button_layout = QHBoxLayout()  
        self.apply_button = QPushButton("Apply Changes")  
        self.delete_button = QPushButton("Delete Interval")  
        self.add_button = QPushButton("Add New Interval")  
          
        button_layout.addWidget(self.apply_button)  
        button_layout.addWidget(self.delete_button)  
        button_layout.addWidget(self.add_button)  
          
        main_layout = QVBoxLayout()  
        main_layout.addLayout(layout)  
        main_layout.addLayout(button_layout)  
          
        self.setLayout(main_layout)  
          
        # Connect signals  
        self.apply_button.clicked.connect(self.apply_changes)  
        self.delete_button.clicked.connect(self.delete_interval)  
        self.add_button.clicked.connect(self.add_new_interval)  
      
    def set_interval(self, interval: DetectionInterval):  
        self.current_interval = interval  
        self.start_spinbox.setValue(interval.start_time)  
        self.end_spinbox.setValue(interval.end_time)  
        self.confidence_spinbox.setValue(interval.confidence_score)  
        self.label_edit.setText(interval.label or "")  
          
        self.apply_button.setEnabled(True)  
        self.delete_button.setEnabled(True)