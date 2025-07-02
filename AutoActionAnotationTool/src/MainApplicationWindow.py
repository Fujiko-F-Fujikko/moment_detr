import sys  
import os
import json  
from typing import List, Dict
import argparse

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSlider, QComboBox, QGroupBox, QSplitter, QFileDialog,
    QPushButton, QDoubleSpinBox, QFormLayout, QListWidget, 
    QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QAction
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget

from MultiTimelineViewer import MultiTimelineViewer
from DetectionInterval import DetectionInterval



class MainApplicationWindow(QMainWindow):  
    def __init__(self):  
        super().__init__()  
        self.setWindowTitle("Moment-DETR Video Annotation Viewer")  
        self.setGeometry(100, 100, 1400, 900)  
          
        # データ管理  
        self.inference_results = None  
        self.current_video_path = None  
        self.current_query_results = []  
        self.saliency_threshold = 0.0  
          
        # UIコンポーネント  
        self.setup_ui()  
        self.setup_connections()  
        self.setup_menus()  
          
    def setup_ui(self):  
        """UIレイアウトの初期化"""  
        central_widget = QWidget()  
        self.setCentralWidget(central_widget)  
          
        # メインレイアウト（水平分割）  
        main_layout = QHBoxLayout()  
          
        # 左パネル（動画プレイヤーとタイムライン）  
        left_panel = self.create_left_panel()  
          
        # 右パネル（コントロールと編集）  
        right_panel = self.create_right_panel()  
          
        # スプリッター  
        splitter = QSplitter(Qt.Orientation.Horizontal)  
        splitter.addWidget(left_panel)  
        splitter.addWidget(right_panel)  
        splitter.setStretchFactor(0, 3)  
        splitter.setStretchFactor(1, 1)  
          
        main_layout.addWidget(splitter)  
        central_widget.setLayout(main_layout)  
          
    def create_left_panel(self) -> QWidget:  
        """左パネル（動画プレイヤーとタイムライン）の作成"""  
        left_widget = QWidget()  
        layout = QVBoxLayout()  
          
        # 動画プレイヤー  
        self.video_player = QMediaPlayer()  
        self.video_widget = QVideoWidget()  
        self.video_player.setVideoOutput(self.video_widget)  
        layout.addWidget(self.video_widget, stretch=2)  
          
        # 動画コントロール  
        controls_layout = QHBoxLayout()  
        self.play_button = QPushButton("▶")  
        self.play_button.setMaximumWidth(50)  
        self.position_slider = QSlider(Qt.Orientation.Horizontal)  
        self.time_label = QLabel("00:00 / 00:00")  
          
        controls_layout.addWidget(self.play_button)  
        controls_layout.addWidget(self.position_slider)  
        controls_layout.addWidget(self.time_label)  
        layout.addLayout(controls_layout)  
          
        # 複数タイムラインビューア（単一のTimelineViewerを置き換え）  
        self.multi_timeline_viewer = MultiTimelineViewer()  
        layout.addWidget(self.multi_timeline_viewer, stretch=2)  
          
        # 顕著性閾値コントロール  
        threshold_layout = QHBoxLayout()  
        threshold_layout.addWidget(QLabel("Saliency Threshold:"))  
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)  
        self.threshold_slider.setRange(-100, 100)  
        self.threshold_slider.setValue(0)  
        self.threshold_value_label = QLabel("0.00")  
        threshold_layout.addWidget(self.threshold_slider)  
        threshold_layout.addWidget(self.threshold_value_label)  
        layout.addLayout(threshold_layout)  
          
        left_widget.setLayout(layout)  
        return left_widget 
          
    def create_right_panel(self) -> QWidget:  
        """右パネル（コントロールと編集）の作成"""  
        right_widget = QWidget()  
        right_widget.setMaximumWidth(350)  
        layout = QVBoxLayout()  
          
          
        # フィルタ設定  
        filter_group = QGroupBox("Filters")  
        filter_layout = QVBoxLayout()  
          
        filter_layout.addWidget(QLabel("Confidence Threshold:"))  
        self.confidence_slider = QSlider(Qt.Orientation.Horizontal)  
        self.confidence_slider.setRange(0, 100)  
        self.confidence_slider.setValue(10)  
        filter_layout.addWidget(self.confidence_slider)  
          
        filter_group.setLayout(filter_layout)  
        layout.addWidget(filter_group)  
          
        # Detection Results表示（メインコンテンツ）  
        results_group = QGroupBox("Detection Results")  
        results_layout = QVBoxLayout()  
          
        # クエリ選択（Detection Results内で使用）  
        query_layout = QHBoxLayout()  
        query_layout.addWidget(QLabel("Query:"))  
        self.query_combo = QComboBox()  
        query_layout.addWidget(self.query_combo)  
        results_layout.addLayout(query_layout)  
          
        # 結果リスト  
        self.results_list = QListWidget()  
        results_layout.addWidget(self.results_list)  
          
        results_group.setLayout(results_layout)  
        layout.addWidget(results_group, stretch=2)  # より多くのスペースを割り当て  
          
        # 区間編集（コンパクト化）  
        edit_group = QGroupBox("Edit Selected")  
        edit_layout = QFormLayout()  
          
        self.start_spinbox = QDoubleSpinBox()  
        self.start_spinbox.setRange(0, 99999)  
        self.start_spinbox.setDecimals(2)  
        self.start_spinbox.setSuffix(" s")  
          
        self.end_spinbox = QDoubleSpinBox()  
        self.end_spinbox.setRange(0, 99999)  
        self.end_spinbox.setDecimals(2)  
        self.end_spinbox.setSuffix(" s")  
          
        edit_layout.addRow("Start:", self.start_spinbox)  
        edit_layout.addRow("End:", self.end_spinbox)  

        # 信頼度表示ラベル
        self.confidence_label = QLabel("0.0000")  
        edit_layout.addRow("Confidence:", self.confidence_label)  
          
        # 編集ボタン（水平レイアウト）  
        button_layout = QHBoxLayout()  
        self.apply_button = QPushButton("Apply")  
        self.delete_button = QPushButton("Delete")  
        self.add_button = QPushButton("Add")  
          
        # ボタンサイズを小さく  
        for btn in [self.apply_button, self.delete_button, self.add_button]:  
            btn.setMaximumHeight(30)  
          
        button_layout.addWidget(self.apply_button)  
        button_layout.addWidget(self.delete_button)  
        button_layout.addWidget(self.add_button)  
          
        edit_layout.addRow(button_layout)  
        edit_group.setLayout(edit_layout)  
        layout.addWidget(edit_group)  
          
        right_widget.setLayout(layout)  
        return right_widget
          
    def setup_connections(self):  
        """シグナル・スロット接続の設定"""  
        # 動画プレイヤー  
        self.play_button.clicked.connect(self.toggle_playback)  
        self.video_player.positionChanged.connect(self.update_position)  
        self.video_player.durationChanged.connect(self.update_duration)  
        self.position_slider.sliderMoved.connect(self.set_position)  
          
        # 閾値スライダー  
        self.threshold_slider.valueChanged.connect(self.update_saliency_threshold)  
        self.confidence_slider.valueChanged.connect(self.update_confidence_filter)  
          
        # クエリ選択  
        self.query_combo.currentTextChanged.connect(self.on_query_selected)  
          
        # 編集ボタン  
        self.apply_button.clicked.connect(self.apply_interval_changes)  
        self.delete_button.clicked.connect(self.delete_interval)  
        self.add_button.clicked.connect(self.add_new_interval)  
          
        # 結果リスト  
        self.results_list.itemClicked.connect(self.on_result_selected)  
          
        # クエリ選択（Detection Results内）  
        self.query_combo.currentTextChanged.connect(self.on_query_selected) 
          
    def setup_menus(self):  
        """メニューバーの設定"""  
        menubar = self.menuBar()  
          
        # ファイルメニュー  
        file_menu = menubar.addMenu('File')  
          
        open_video_action = QAction('Open Video', self)  
        open_video_action.triggered.connect(self.open_video)  
        file_menu.addAction(open_video_action)  
          
        load_results_action = QAction('Load Inference Results', self)  
        load_results_action.triggered.connect(self.load_inference_results)  
        file_menu.addAction(load_results_action)  
          
        file_menu.addSeparator()  
          
        save_results_action = QAction('Save Results', self)  
        save_results_action.triggered.connect(self.save_results)  
        file_menu.addAction(save_results_action)  
          
    def open_video(self):  
        """動画ファイルを開く"""  
        file_path, _ = QFileDialog.getOpenFileName(  
            self, "Open Video", "", "Video Files (*.mp4 *.avi *.mov *.mkv)"  
        )  
        if file_path:  
            self.current_video_path = file_path  
            self.video_player.setSource(QUrl.fromLocalFile(file_path))
              
    def load_inference_results(self):  
        """推論結果JSONファイルを読み込む"""  
        file_path, _ = QFileDialog.getOpenFileName(  
            self, "Load Inference Results", "", "JSON Files (*.json *.jsonl)"  
        )  
        if file_path:  
            try:  
                self.inference_results = self.load_json_results(file_path)  
                self.populate_query_combo()  
                self.update_display()  
                QMessageBox.information(self, "Success", "Results loaded successfully!")  
            except Exception as e:  
                QMessageBox.critical(self, "Error", f"Failed to load results: {str(e)}")  
                  
    def load_json_results(self, file_path: str) -> List[Dict]:  
        """JSONファイルから推論結果を読み込む"""  
        results = []  
        with open(file_path, 'r', encoding='utf-8') as f:  
            if file_path.endswith('.jsonl'):  
                for line in f:  
                    if line.strip():  
                        results.append(json.loads(line))  
            else:  
                data = json.load(f)  
                if isinstance(data, dict) and 'results' in data:  
                    results = data['results']  
                elif isinstance(data, list):  
                    results = data  
                else:  
                    results = [data]  
        return results  
          
    def populate_query_combo(self):  
        """クエリコンボボックスを更新"""  
        self.query_combo.clear()  
        if self.inference_results:  
            for result in self.inference_results:  
                query_text = result.get('query', f"Query {result.get('qid', 'Unknown')}")  
                self.query_combo.addItem(query_text)  
                  
    def on_query_selected(self, query_text: str):  
        """クエリが選択された時の処理"""  
        if not self.inference_results:  
            return  
              
        # 選択されたクエリの結果を取得  
        for result in self.inference_results:  
            if result.get('query') == query_text:  
                self.current_query_results = result  
                self.update_results_display()  
                break
                  
    def parse_intervals(self, pred_windows: List) -> List[DetectionInterval]:  
        """pred_relevant_windowsをDetectionIntervalオブジェクトに変換"""  
        intervals = []  
        for window in pred_windows:  
            if len(window) >= 3:  
                start_time, end_time, confidence = window[:3]  
                intervals.append(DetectionInterval(start_time, end_time, confidence))  
        return intervals  
          
    def update_results_display(self):  
        """結果リストを更新"""  
        self.results_list.clear()  
        if not self.current_query_results:  
            return  
              
        pred_windows = self.current_query_results.get('pred_relevant_windows', [])  
        for i, window in enumerate(pred_windows):  
            if len(window) >= 3:  
                start, end, confidence = window[:3]  
                item_text = f"{i+1}: {start:.2f}s - {end:.2f}s (conf: {confidence:.4f})"  
                self.results_list.addItem(item_text)  
                  
    def update_saliency_threshold(self, value: int):  
        """顕著性閾値を更新"""  
        threshold = value / 100.0  
        self.saliency_threshold = threshold  
        self.threshold_value_label.setText(f"{threshold:.2f}")  
        self.apply_filters()  
          
    def update_confidence_filter(self, value: int):  
        """信頼度フィルタを更新"""  
        threshold = value / 100.0  
        self.apply_filters()  
          
    def apply_filters(self):  
        """フィルタを適用して表示を更新"""  
        # フィルタリングロジックを実装  
        self.update_display()  
          
    def save_results(self):  
        """編集された結果を保存"""  
        if not self.inference_results:  
            QMessageBox.warning(self, "Warning", "No results to save!")  
            return  
              
        file_path, _ = QFileDialog.getSaveFileName(  
            self, "Save Results", "", "JSON Files (*.json *.jsonl)"  
        )  
        if file_path:  
            try:  
                # 閾値以下の結果を除外して保存  
                filtered_results = self.filter_results_by_threshold()  
                  
                if file_path.endswith('.jsonl'):  
                    with open(file_path, 'w', encoding='utf-8') as f:  
                        for result in filtered_results:  
                            f.write(json.dumps(result, ensure_ascii=False) + '\n')  
                else:  
                    with open(file_path, 'w', encoding='utf-8') as f:  
                        json.dump(filtered_results, f, indent=2, ensure_ascii=False)  
                          
                QMessageBox.information(self, "Success", f"Results saved to {file_path}")  
                  
            except Exception as e:  
                QMessageBox.critical(self, "Error", f"Failed to save results: {str(e)}")  
      
    def filter_results_by_threshold(self) -> List[Dict]:  
        """閾値以下の結果を除外"""  
        if not self.inference_results:  
            return []  
              
        filtered_results = []  
        for result in self.inference_results:  
            # 信頼度閾値でフィルタリング  
            pred_windows = result.get('pred_relevant_windows', [])  
            filtered_windows = [  
                window for window in pred_windows   
                if len(window) >= 3 and window[2] >= self.saliency_threshold  
            ]  
              
            # フィルタされた結果を作成  
            filtered_result = result.copy()  
            filtered_result['pred_relevant_windows'] = filtered_windows  
            filtered_results.append(filtered_result)  
              
        return filtered_results  
      
    def toggle_playback(self):  
        """再生/一時停止の切り替え"""  
        if self.video_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.video_player.pause()  
            self.play_button.setText("▶")  
        else:  
            self.video_player.play()  
            self.play_button.setText("⏸")  
      
    def update_position(self, position: int):  
        """再生位置の更新"""  
        self.position_slider.setValue(position)  
        self.update_time_label(position, self.video_player.duration())  
          
        # 複数タイムラインビューアの位置も更新  
        if hasattr(self, 'multi_timeline_viewer'):  
            current_time = position / 1000.0  # ミリ秒から秒に変換  
            self.multi_timeline_viewer.update_playhead_position(current_time)
      
    def update_duration(self, duration: int):  
        """動画の長さが取得された時の処理"""  
        self.position_slider.setRange(0, duration)  
        self.update_time_label(self.video_player.position(), duration)  
          
        # 複数タイムラインビューアーに動画の長さを設定  
        if hasattr(self, 'multi_timeline_viewer') and duration > 0:  
            duration_seconds = duration / 1000.0  
            self.multi_timeline_viewer.set_video_duration(duration_seconds)  
            print(f"Set video duration to timelines: {duration_seconds}")  
              
            # 既に推論結果が読み込まれている場合は、タイムラインを更新  
            if hasattr(self, 'inference_results') and self.inference_results:  
                self.multi_timeline_viewer.set_query_results(self.inference_results)

      
    def set_position(self, position: int):  
        """スライダーから再生位置を設定"""  
        self.video_player.setPosition(position)  
      
    def update_time_label(self, position: int, duration: int):  
        """時間表示ラベルの更新"""  
        def format_time(ms):  
            seconds = ms // 1000  
            minutes = seconds // 60  
            seconds = seconds % 60  
            return f"{minutes:02d}:{seconds:02d}"  
          
        current_time = format_time(position)  
        total_time = format_time(duration)  
        self.time_label.setText(f"{current_time} / {total_time}")  
      
    def apply_interval_changes(self):  
        """区間の変更を適用"""  
        if not hasattr(self, 'selected_interval'):  
            return  
              
        # 新しい値を取得  
        new_start = self.start_spinbox.value()  
        new_end = self.end_spinbox.value()  
          
        # バリデーション  
        if new_start >= new_end:  
            QMessageBox.warning(self, "Warning", "Start time must be less than end time!")  
            return  
              
        # 結果を更新  
        self.update_interval_in_results(self.selected_interval, new_start, new_end)  
        self.update_results_display()  
        self.update_display()  
          
    def delete_interval(self):  
        """選択された区間を削除"""  
        if not hasattr(self, 'selected_interval'):  
            return  
              
        reply = QMessageBox.question(  
            self, "Confirm Delete",   
            "Are you sure you want to delete this interval?",  
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No  
        )  
          
        if reply == QMessageBox.StandardButton.Yes:  
            self.remove_interval_from_results(self.selected_interval)  
            self.update_results_display()  
            self.update_display()  
      
    def add_new_interval(self):  
        """新しい区間を追加"""  
        start_time = self.start_spinbox.value()  
        end_time = self.end_spinbox.value()  
          
        if start_time >= end_time:  
            QMessageBox.warning(self, "Warning", "Start time must be less than end time!")  
            return  
              
        # 新しい区間を追加  
        new_interval = [start_time, end_time, 1.0]  # デフォルト信頼度  
        self.add_interval_to_results(new_interval)  
        self.update_results_display()  
        self.update_display()  
      
    def on_result_selected(self, item):  
        """結果リストのアイテムが選択された時の処理"""  
        if not self.current_query_results:  
            return  
              
        # 選択されたアイテムのインデックスを取得  
        row = self.results_list.row(item)  
        pred_windows = self.current_query_results.get('pred_relevant_windows', [])  
          
        if 0 <= row < len(pred_windows):  
            window = pred_windows[row]  
            if len(window) >= 3:  
                start, end, confidence = window[:3]  
                  
                # エディタに値を設定  
                self.start_spinbox.setValue(start)  
                self.end_spinbox.setValue(end)  
                  
                # 信頼度ラベルを更新  
                self.confidence_label.setText(f"{confidence:.4f}")  
                  
                # 選択された区間を記録  
                self.selected_interval = row  
                  
                # 動画をその位置にシーク  
                self.video_player.setPosition(int(start * 1000))
      
    def update_interval_in_results(self, interval_index: int, new_start: float, new_end: float):  
        """結果内の区間を更新"""  
        if not self.current_query_results:  
            return  
              
        pred_windows = self.current_query_results.get('pred_relevant_windows', [])  
        if 0 <= interval_index < len(pred_windows):  
            window = pred_windows[interval_index]  
            if len(window) >= 3:  
                # 新しい値で更新（信頼度は保持）  
                pred_windows[interval_index] = [new_start, new_end, window[2]]  
      
    def remove_interval_from_results(self, interval_index: int):  
        """結果から区間を削除"""  
        if not self.current_query_results:  
            return  
              
        pred_windows = self.current_query_results.get('pred_relevant_windows', [])  
        if 0 <= interval_index < len(pred_windows):  
            del pred_windows[interval_index]  
      
    def add_interval_to_results(self, new_interval: List[float]):  
        """結果に新しい区間を追加"""  
        if not self.current_query_results:  
            return  
              
        pred_windows = self.current_query_results.get('pred_relevant_windows', [])  
        pred_windows.append(new_interval)  
          
        # 信頼度でソート  
        pred_windows.sort(key=lambda x: x[2] if len(x) >= 3 else 0, reverse=True)  
      
    def update_display(self):  
        """表示を更新"""  
        # タイムラインビューアを更新  
        if hasattr(self, 'multi_timeline_viewer') and self.inference_results:  
            # 全ての推論結果を再設定してタイムラインを更新  
            self.multi_timeline_viewer.set_query_results(self.inference_results)  
              
            # 動画の長さも再設定  
            if hasattr(self, 'video_player') and self.video_player.duration() > 0:  
                duration_seconds = self.video_player.duration() / 1000.0  
                self.multi_timeline_viewer.set_video_duration(duration_seconds)

    def load_video_from_path(self, video_path: str):  
        """指定されたパスから動画を読み込む"""  
        if not os.path.exists(video_path):  
            QMessageBox.critical(self, "Error", f"Video file not found: {video_path}")  
            return  
              
        try:  
            self.current_video_path = video_path  
            self.video_player.setSource(QUrl.fromLocalFile(video_path))  
            print(f"Loaded video: {video_path}")  
        except Exception as e:  
            QMessageBox.critical(self, "Error", f"Failed to load video: {str(e)}")  
      
    def load_inference_results_from_path(self, json_path: str):  
        """指定されたパスから推論結果を読み込む"""  
        if not os.path.exists(json_path):  
            QMessageBox.critical(self, "Error", f"JSON file not found: {json_path}")  
            return  
              
        try:  
            self.inference_results = self.load_json_results(json_path)  
            self.populate_query_combo()  
              
            # 全てのクエリ結果を複数タイムラインビューアに設定  
            self.multi_timeline_viewer.set_query_results(self.inference_results)  
              
            # 動画の長さが既に取得されている場合のみ設定  
            if hasattr(self, 'video_player') and self.video_player.duration() > 0:  
                duration_seconds = self.video_player.duration() / 1000.0  
                self.multi_timeline_viewer.set_video_duration(duration_seconds)  
                print(f"Applied video duration to timelines: {duration_seconds}")  
            else:  
                print("Video duration not available yet, will be set when duration is loaded")  
              
            print(f"Loaded inference results: {json_path}")  
        except Exception as e:  
            QMessageBox.critical(self, "Error", f"Failed to load JSON: {str(e)}")


def parse_arguments():  
    """コマンドライン引数を解析"""  
    parser = argparse.ArgumentParser(description='Moment-DETR Video Annotation Viewer')  
    parser.add_argument('--video', type=str, help='Path to video file')  
    parser.add_argument('--json', type=str, help='Path to inference results JSON file')  
    return parser.parse_args()  
  
if __name__ == '__main__':  
    app = QApplication(sys.argv)  
      
    # コマンドライン引数を解析  
    args = parse_arguments()  
      
    window = MainApplicationWindow()  
      
    # 引数が指定されている場合は自動的に読み込み  
    if args.video:  
        window.load_video_from_path(args.video)  
      
    if args.json:  
        window.load_inference_results_from_path(args.json)  
      
    window.show()  
    sys.exit(app.exec())