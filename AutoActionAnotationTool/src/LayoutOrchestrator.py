# LayoutOrchestrator.py  
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PyQt6.QtCore import Qt, QObject  
from typing import Dict, Any, Optional  
  
from ControlPanelBuilder import ControlPanelBuilder  
from TimelineDisplayManager import TimelineDisplayManager  
from EditWidgetManager import EditWidgetManager
  
class LayoutOrchestrator(QObject):  
    """メインレイアウトの構築を担当するクラス"""  
      
    def __init__(self, main_window=None):  
        super().__init__()  
        self.main_window = main_window  
        self.control_panel_builder = ControlPanelBuilder()  
          
        # レイアウト要素の参照  
        self.main_splitter: Optional[QSplitter] = None  
        self.left_panel: Optional[QWidget] = None  
        self.right_panel: Optional[QWidget] = None  
        self.video_container: Optional[QWidget] = None  
        self.timeline_container: Optional[QWidget] = None  
          
        # UI要素の辞書  
        self.ui_components: Dict[str, Any] = {}  

        # ControlPanelBuilderのシグナル接続  
        self.setup_control_panel_connections()  

    def setup_control_panel_connections(self):  
        """ControlPanelBuilderのシグナル接続"""  
        self.control_panel_builder.confidenceChanged.connect(  
            self.main_window.update_confidence_filter  
        )  
        self.control_panel_builder.handTypeFilterChanged.connect(  
            self.main_window.update_hand_type_filter  
        )  
        self.control_panel_builder.resultItemClicked.connect(  
            self.main_window.on_interval_selected  
        ) 

    def create_main_layout(self, video_widget, controls_layout,   
                        timeline_display_manager: TimelineDisplayManager,  
                        edit_widget_manager: EditWidgetManager) -> QSplitter:  
        """メインレイアウトを構築"""  
        # 左パネルを作成  
        self.left_panel = self.organize_left_panel(  
            video_widget, controls_layout, timeline_display_manager  
        )  
        
        # 右パネルを作成（EditWidgetManagerを含む）  
        self.right_panel, ui_components = self.organize_right_panel(edit_widget_manager)  
        self.ui_components.update(ui_components)  
        
        # メインスプリッターを作成  
        self.main_splitter = self.manage_main_splitter(self.left_panel, self.right_panel)  
        
        return self.main_splitter  
      
    def organize_left_panel(self, video_widget, controls_layout,   
                           timeline_display_manager: TimelineDisplayManager) -> QWidget:  
        """左パネルの構成を管理"""  
        # 垂直スプリッターを使用して動画とタイムラインを分離  
        vertical_splitter = QSplitter(Qt.Orientation.Vertical)  
          
        # 動画コンテナを作成  
        self.video_container = self._create_video_container(video_widget, controls_layout)  
          
        # タイムラインコンテナを作成  
        self.timeline_container = self._create_timeline_container(timeline_display_manager)  
          
        # スプリッターに追加  
        vertical_splitter.addWidget(self.video_container)  
        vertical_splitter.addWidget(self.timeline_container)  
          
        # 初期サイズ比率を設定  
        vertical_splitter.setSizes([300, 200])  
          
        # 最小サイズ制約  
        self.video_container.setMinimumHeight(200)  
        self.timeline_container.setMinimumHeight(100)  
          
        # 折りたたみ無効化  
        vertical_splitter.setChildrenCollapsible(False)  
          
        return vertical_splitter  
      
    def create_control_panel(self) -> tuple[QWidget, Dict[str, Any]]:  
        """コントロールパネルを作成"""  
        # ControlPanelBuilderからUI要素を取得  
        ui_components = self.control_panel_builder.get_ui_components()  
          
        # UI要素辞書を更新  
        self.ui_components.update(ui_components)  
          
        return self.control_panel_builder, ui_components  
      
    def organize_right_panel(self, edit_widget_manager) -> tuple[QWidget, Dict[str, Any]]:  
        """右パネルの構成を管理（修正版）"""  
        right_panel = QWidget()  
        layout = QVBoxLayout()  
          
        # コントロールパネルを作成  
        control_panel, ui_components = self.create_control_panel()  
        layout.addWidget(control_panel)  
          
        # EditWidgetManagerを追加  
        layout.addWidget(edit_widget_manager)  
          
        right_panel.setLayout(layout)  
        return right_panel, ui_components
      
    def manage_main_splitter(self, left_panel: QWidget, right_panel: QWidget) -> QSplitter:  
        """メインスプリッターの管理"""  
        splitter = QSplitter(Qt.Orientation.Horizontal)  
        splitter.addWidget(left_panel)  
        splitter.addWidget(right_panel)  
          
        # 初期サイズ比率を設定  
        splitter.setSizes([800, 600])  
          
        # 最小幅制約  
        left_panel.setMinimumWidth(400)  
        right_panel.setMinimumWidth(350)  
          
        # 折りたたみ無効化  
        splitter.setChildrenCollapsible(False)  
          
        return splitter  
      
    def _create_video_container(self, video_widget, controls_layout) -> QWidget:  
        """動画コンテナを作成"""  
        container = QWidget()  
        layout = QVBoxLayout()  
          
        # 動画ウィジェットを追加  
        layout.addWidget(video_widget)  
          
        # コントロールレイアウトをウィジェットに包んで高さ制御  
        controls_widget = QWidget()  
        controls_widget.setLayout(controls_layout)  
        controls_widget.setMaximumHeight(60)  
          
        layout.addWidget(controls_widget)  
        container.setLayout(layout)  
          
        return container  
      
    def _create_timeline_container(self, timeline_display_manager: TimelineDisplayManager) -> QWidget:  
        """タイムラインコンテナを作成"""  
        container = QWidget()  
        layout = QVBoxLayout()  
          
        # タイムライン表示マネージャーを追加  
        layout.addWidget(timeline_display_manager)  
        container.setLayout(layout)  
          
        return container  
      
    def get_ui_components(self) -> Dict[str, Any]:  
        """UI要素の辞書を取得"""  
        return self.ui_components  
      
    def get_main_splitter(self) -> Optional[QSplitter]:  
        """メインスプリッターを取得"""  
        return self.main_splitter  
      
    def get_left_panel(self) -> Optional[QWidget]:  
        """左パネルを取得"""  
        return self.left_panel  
      
    def get_right_panel(self) -> Optional[QWidget]:  
        """右パネルを取得"""  
        return self.right_panel  
      
    def get_video_container(self) -> Optional[QWidget]:  
        """動画コンテナを取得"""  
        return self.video_container  
      
    def get_timeline_container(self) -> Optional[QWidget]:  
        """タイムラインコンテナを取得"""  
        return self.timeline_container  
      
    def update_layout_constraints(self, **kwargs):  
        """レイアウト制約を動的に更新"""  
        if 'left_min_width' in kwargs and self.left_panel:  
            self.left_panel.setMinimumWidth(kwargs['left_min_width'])  
          
        if 'right_min_width' in kwargs and self.right_panel:  
            self.right_panel.setMinimumWidth(kwargs['right_min_width'])  
          
        if 'video_min_height' in kwargs and self.video_container:  
            self.video_container.setMinimumHeight(kwargs['video_min_height'])  
          
        if 'timeline_min_height' in kwargs and self.timeline_container:  
            self.timeline_container.setMinimumHeight(kwargs['timeline_min_height'])  
      
    def set_splitter_sizes(self, horizontal_sizes: list = None, vertical_sizes: list = None):  
        """スプリッターサイズを設定"""  
        if horizontal_sizes and self.main_splitter:  
            self.main_splitter.setSizes(horizontal_sizes)  
          
        if vertical_sizes and self.left_panel and isinstance(self.left_panel, QSplitter):  
            self.left_panel.setSizes(vertical_sizes)  
      
    def get_layout_state(self) -> Dict[str, Any]:  
        """現在のレイアウト状態を取得"""  
        state = {  
            'has_main_splitter': self.main_splitter is not None,  
            'has_left_panel': self.left_panel is not None,  
            'has_right_panel': self.right_panel is not None,  
            'ui_components_count': len(self.ui_components)  
        }  
          
        if self.main_splitter:  
            state['main_splitter_sizes'] = self.main_splitter.sizes()  
          
        if self.left_panel and isinstance(self.left_panel, QSplitter):  
            state['left_splitter_sizes'] = self.left_panel.sizes()  
          
        return state  
      
    def restore_layout_state(self, state: Dict[str, Any]):  
        """レイアウト状態を復元"""  
        if 'main_splitter_sizes' in state and self.main_splitter:  
            self.main_splitter.setSizes(state['main_splitter_sizes'])  
          
        if 'left_splitter_sizes' in state and self.left_panel and isinstance(self.left_panel, QSplitter):  
            self.left_panel.setSizes(state['left_splitter_sizes'])