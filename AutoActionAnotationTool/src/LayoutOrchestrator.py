# LayoutOrchestrator.py (リファクタリング版)  
import logging  
from typing import Dict, Any, Optional  
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter,   
                            QGroupBox, QSlider, QLabel, QComboBox, QListWidget,  
                            QScrollArea, QFrame)  
from PyQt6.QtCore import Qt, pyqtSignal  
from PyQt6.QtGui import QFont  
  
from UnifiedIntervalEditor import UnifiedIntervalEditor  
from TimelineDisplayManager import TimelineDisplayManager  
  
logger = logging.getLogger(__name__)  
  
class LayoutOrchestrator(QWidget):  
    """UIレイアウト管理クラス（リファクタリング版）"""  
      
    # シグナル定義  
    layoutCreated = pyqtSignal()  
    componentResized = pyqtSignal(str, int, int)  # component_name, width, height  
      
    def __init__(self, main_window):  
        super().__init__()  
        self.main_window = main_window  
          
        # レイアウト状態  
        self.main_splitter: Optional[QSplitter] = None  
        self.left_panel: Optional[QWidget] = None  
        self.right_panel: Optional[QWidget] = None  
        self.timeline_container: Optional[QWidget] = None  
          
        # UI要素の参照  
        self.ui_components: Dict[str, Any] = {}  
          
        # レイアウト設定  
        self.default_splitter_sizes = [800, 400, 400]  # 左パネル, タイムライン, 右パネル  
        self.minimum_panel_width = 200  
          
        logger.info("LayoutOrchestrator initialized (refactored)")  
      
    def create_main_layout(self, video_widget: QWidget, controls_layout: QHBoxLayout,  
                          timeline_manager: TimelineDisplayManager,   
                          unified_editor: UnifiedIntervalEditor) -> QSplitter:  
        """メインレイアウトを作成"""  
        logger.info("Creating main layout with unified components")  
          
        # メインスプリッターを作成  
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)  
          
        # 左パネル（動画とコントロール）を作成  
        self.left_panel = self._create_left_panel(video_widget, controls_layout)  
          
        # 中央パネル（タイムライン）を作成  
        self.timeline_container = self._create_timeline_panel(timeline_manager)  
          
        # 右パネル（統一エディターとフィルタ）を作成  
        self.right_panel = self._create_right_panel(unified_editor)  
          
        # スプリッターに追加  
        self.main_splitter.addWidget(self.left_panel)  
        self.main_splitter.addWidget(self.timeline_container)  
        self.main_splitter.addWidget(self.right_panel)  
          
        # スプリッターの設定  
        self._configure_splitter()  
          
        self.layoutCreated.emit()  
        logger.info("Main layout created successfully")  
          
        return self.main_splitter  
      
    def _create_left_panel(self, video_widget: QWidget, controls_layout: QHBoxLayout) -> QWidget:  
        """左パネル（動画プレイヤー）を作成"""  
        panel = QWidget()  
        layout = QVBoxLayout(panel)  
          
        # 動画ウィジェット  
        if video_widget:  
            layout.addWidget(video_widget)  
          
        # コントロールレイアウト  
        if controls_layout:  
            controls_widget = QWidget()  
            controls_widget.setLayout(controls_layout)  
            layout.addWidget(controls_widget)  
          
        # パネルの設定  
        panel.setMinimumWidth(self.minimum_panel_width)  
          
        logger.info("Left panel (video player) created")  
        return panel  
      
    def _create_timeline_panel(self, timeline_manager: TimelineDisplayManager) -> QWidget:  
        """中央パネル（タイムライン）を作成"""  
        panel = QWidget()  
        layout = QVBoxLayout(panel)  
          
        # タイムラインタイトル  
        title_label = QLabel("Timeline")  
        title_font = QFont()  
        title_font.setBold(True)  
        title_font.setPointSize(12)  
        title_label.setFont(title_font)  
        layout.addWidget(title_label)  
          
        # タイムラインウィジェットを作成  
        if timeline_manager:  
            timeline_widget = timeline_manager.create_timeline_widgets(panel)  
            layout.addWidget(timeline_widget)  
          
        # パネルの設定  
        panel.setMinimumWidth(self.minimum_panel_width)  
          
        logger.info("Timeline panel created")  
        return panel  
      
    def _create_right_panel(self, unified_editor: UnifiedIntervalEditor) -> QWidget:  
        """右パネル（統一エディターとフィルタ）を作成"""  
        panel = QWidget()  
        layout = QVBoxLayout(panel)  
          
        # フィルタコントロールセクション  
        filter_group = self._create_filter_controls()  
        layout.addWidget(filter_group)  
          
        # 統一エディターセクション  
        if unified_editor:  
            editor_group = QGroupBox("Interval Editor")  
            editor_layout = QVBoxLayout(editor_group)  
            editor_layout.addWidget(unified_editor)  
            layout.addWidget(editor_group)  
          
        # パネルの設定  
        panel.setMinimumWidth(self.minimum_panel_width)  
          
        logger.info("Right panel (unified editor) created")  
        return panel  
      
    def _create_filter_controls(self) -> QGroupBox:  
        """フィルタコントロールを作成"""  
        group = QGroupBox("Filters")  
        layout = QVBoxLayout(group)  
          
        # 信頼度フィルタ  
        confidence_layout = QHBoxLayout()  
        confidence_layout.addWidget(QLabel("Confidence:"))  
          
        confidence_slider = QSlider(Qt.Orientation.Horizontal)  
        confidence_slider.setRange(0, 100)  
        confidence_slider.setValue(0)  
        confidence_slider.setTickPosition(QSlider.TickPosition.TicksBelow)  
        confidence_slider.setTickInterval(10)  
          
        confidence_value_label = QLabel("0%")  
        confidence_value_label.setMinimumWidth(40)  
          
        # スライダー値変更時のラベル更新  
        confidence_slider.valueChanged.connect(  
            lambda value: confidence_value_label.setText(f"{value}%")  
        )  
          
        confidence_layout.addWidget(confidence_slider)  
        confidence_layout.addWidget(confidence_value_label)  
        layout.addLayout(confidence_layout)  
          
        # 手タイプフィルタ  
        hand_type_layout = QHBoxLayout()  
        hand_type_layout.addWidget(QLabel("Hand Type:"))  
          
        hand_type_combo = QComboBox()  
        hand_type_combo.addItems(["All", "Left", "Right", "Other"])  
        hand_type_layout.addWidget(hand_type_combo)  
        layout.addLayout(hand_type_layout)  
          
        # 区間タイプフィルタ  
        interval_type_layout = QHBoxLayout()  
        interval_type_layout.addWidget(QLabel("Type:"))  
          
        interval_type_combo = QComboBox()  
        interval_type_combo.addItems(["All", "action", "step"])  
        interval_type_layout.addWidget(interval_type_combo)  
        layout.addLayout(interval_type_layout)  
          
        # UI要素を保存  
        self.ui_components.update({  
            'confidence_slider': confidence_slider,  
            'confidence_value_label': confidence_value_label,  
            'hand_type_combo': hand_type_combo,  
            'interval_type_combo': interval_type_combo  
        })  
          
        logger.info("Filter controls created")  
        return group  
      
    def _configure_splitter(self):  
        """スプリッターの設定"""  
        if not self.main_splitter:  
            return  
          
        # 初期サイズを設定  
        self.main_splitter.setSizes(self.default_splitter_sizes)  
          
        # 各パネルの最小サイズを設定  
        for i in range(self.main_splitter.count()):  
            self.main_splitter.widget(i).setMinimumWidth(self.minimum_panel_width)  
          
        # スプリッターハンドルの設定  
        self.main_splitter.setHandleWidth(5)  
        self.main_splitter.setChildrenCollapsible(False)  
          
        # サイズ変更イベントを接続  
        self.main_splitter.splitterMoved.connect(self._on_splitter_moved)  
          
        logger.info("Splitter configured")  
      
    def _on_splitter_moved(self, pos: int, index: int):  
        """スプリッター移動時の処理"""  
        sizes = self.main_splitter.sizes()  
        logger.info(f"Splitter moved - sizes: {sizes}")  
          
        # 各パネルのサイズ変更を通知  
        panel_names = ["left_panel", "timeline_panel", "right_panel"]  
        if index < len(panel_names):  
            self.componentResized.emit(panel_names[index], sizes[index], 0)  
      
    def get_ui_components(self) -> Dict[str, Any]:  
        """UI要素の参照を取得"""  
        return self.ui_components.copy()  
      
    def update_layout_for_video_loaded(self, video_path: str):  
        """動画読み込み時のレイアウト更新"""  
        logger.info(f"Updating layout for video: {video_path}")  
          
        # 必要に応じてレイアウトを調整  
        if self.main_splitter:  
            # 動画が読み込まれた時の特別な処理があれば実装  
            pass  
      
    def update_layout_for_results_loaded(self):  
        """結果読み込み時のレイアウト更新"""  
        logger.info("Updating layout for results loaded")  
          
        # 結果が読み込まれた時の特別な処理があれば実装  
        if self.main_splitter:  
            pass  
      
    def set_panel_visibility(self, panel_name: str, visible: bool):  
        """パネルの表示/非表示を設定"""  
        panel_map = {  
            'left': self.left_panel,  
            'timeline': self.timeline_container,  
            'right': self.right_panel  
        }  
          
        if panel_name in panel_map and panel_map[panel_name]:  
            panel_map[panel_name].setVisible(visible)  
            logger.info(f"Panel '{panel_name}' visibility set to: {visible}")  
      
    def get_panel_sizes(self) -> Dict[str, int]:  
        """各パネルのサイズを取得"""  
        if not self.main_splitter:  
            return {}  
          
        sizes = self.main_splitter.sizes()  
        return {  
            'left_panel': sizes[0] if len(sizes) > 0 else 0,  
            'timeline_panel': sizes[1] if len(sizes) > 1 else 0,  
            'right_panel': sizes[2] if len(sizes) > 2 else 0  
        }  
      
    def set_panel_sizes(self, sizes: Dict[str, int]):  
        """各パネルのサイズを設定"""  
        if not self.main_splitter:  
            return  
          
        size_list = [  
            sizes.get('left_panel', self.default_splitter_sizes[0]),  
            sizes.get('timeline_panel', self.default_splitter_sizes[1]),  
            sizes.get('right_panel', self.default_splitter_sizes[2])  
        ]  
          
        self.main_splitter.setSizes(size_list)  
        logger.info(f"Panel sizes set to: {size_list}")  
      
    def get_layout_state(self) -> Dict[str, Any]:  
        """レイアウト状態を取得（デバッグ用）"""  
        return {  
            'has_main_splitter': self.main_splitter is not None,  
            'panel_sizes': self.get_panel_sizes(),  
            'ui_components_count': len(self.ui_components),  
            'minimum_panel_width': self.minimum_panel_width,  
            'default_splitter_sizes': self.default_splitter_sizes  
        }  
      
    def restore_default_layout(self):  
        """デフォルトレイアウトに復元"""  
        if self.main_splitter:  
            self.main_splitter.setSizes(self.default_splitter_sizes)  
            logger.info("Layout restored to default")  
      
    def save_layout_settings(self) -> Dict[str, Any]:  
        """レイアウト設定を保存用に取得"""  
        return {  
            'panel_sizes': self.get_panel_sizes(),  
            'splitter_state': self.main_splitter.saveState().data().hex() if self.main_splitter else None  
        }  
      
    def load_layout_settings(self, settings: Dict[str, Any]):  
        """保存されたレイアウト設定を読み込み"""  
        if 'panel_sizes' in settings:  
            self.set_panel_sizes(settings['panel_sizes'])  
          
        if 'splitter_state' in settings and settings['splitter_state'] and self.main_splitter:  
            try:  
                state_bytes = bytes.fromhex(settings['splitter_state'])  
                self.main_splitter.restoreState(state_bytes)  
                logger.info("Layout settings loaded successfully")  
            except Exception as e:  
                logger.error(f"Failed to load layout settings: {e}")