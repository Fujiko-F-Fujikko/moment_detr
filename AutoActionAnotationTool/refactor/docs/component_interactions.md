# component_interactions.md

# Component Interactions - Detailed Documentation

## 主要な相互作用パターン

### 1. 初期化シーケンス

```
Application Startup:
┌─ main() 
├─ MainApplicationWindow.__init__()
│  ├─ _setup_logging()
│  ├─ AnnotationDataManager()
│  ├─ AnnotationCommandManager(data_manager)
│  ├─ DataIOManager(data_manager)
│  ├─ VideoController()
│  ├─ TimelineController(data_manager)
│  ├─ AnnotationListController(data_manager)
│  ├─ AnnotationEditorController(data_manager, command_manager)
│  ├─ _setup_ui()
│  ├─ _setup_connections()  ← シグナル/スロット接続
│  ├─ _setup_menus()
│  └─ _setup_shortcuts()
└─ show()
```

### 2. 動画読み込みシーケンス

```
動画ファイル選択:
┌─ MainApplicationWindow.open_video()
├─ QFileDialog.getOpenFileName()
└─ load_video(video_path)

動画読み込み処理:
┌─ MainApplicationWindow.load_video(video_path)
├─ DataIOManager.load_video_metadata(video_path)
│  └─ OpenCVによるメタデータ読み込み
├─ VideoController.load_video(video_path, video_info)
│  ├─ QMediaPlayer.setSource()
│  └─ Signal: video_loaded
├─ AnnotationDataManager.load_video(video_path, video_info)
│  └─ Signal: video_loaded
└─ 各コントローラーがシグナルを受信して初期化
```

### 3. アノテーション作成シーケンス

```
新規アノテーション作成:
┌─ User: Timeline上でドラッグ
├─ TimelineTrack.mouseMoveEvent()
├─ TimelineTrack.mouseReleaseEvent()
├─ Signal: new_interval_created(start, end, annotation_type)
├─ MainApplicationWindow.create_new_annotation()
├─ AnnotationCommandManager.execute_add_annotation()
├─ AddAnnotationCommand.redo()
├─ AnnotationDataManager.add_annotation()
├─ Signal: annotation_added
├─ Signal: data_changed
└─ 各コントローラーのUI更新
   ├─ TimelineController.update_timeline()
   ├─ AnnotationListController.update_list()
   └─ (AnnotationEditorController: 必要に応じて)
```

### 4. アノテーション編集シーケンス

```
アノテーション選択:
┌─ User: TimelineまたはListでクリック
├─ Signal: annotation_selected(annotation)
├─ AnnotationListController.select_annotation()
├─ TimelineController.set_highlighted_annotation()
├─ AnnotationEditorController.set_current_annotation()
└─ エディターフォームの更新

アノテーション修正:
┌─ User: エディターで値変更
├─ ActionEditor/StepEditor.apply_changes()
├─ AnnotationEditorController.apply_annotation_changes()
├─ AnnotationCommandManager.execute_modify_annotation()
├─ ModifyAnnotationCommand.redo()
├─ AnnotationDataManager.modify_annotation()
├─ Signal: annotation_modified
├─ Signal: data_changed
└─ 各コントローラーのUI更新
```

### 5. Undo/Redoシーケンス

```
Undo操作:
┌─ User: Ctrl+Z または Menu
├─ MainApplicationWindow: アクションハンドラー
├─ AnnotationCommandManager.undo()
├─ QUndoStack.undo()
├─ XXXCommand.undo()
├─ AnnotationDataManager: 状態復元
├─ Signal: data_changed
└─ 各コントローラーのUI更新

Redo操作:
┌─ User: Ctrl+Y または Menu
├─ MainApplicationWindow: アクションハンドラー
├─ AnnotationCommandManager.redo()
├─ QUndoStack.redo()
├─ XXXCommand.redo()
├─ AnnotationDataManager: 状態復元
├─ Signal: data_changed
└─ 各コントローラーのUI更新
```

### 6. データインポートシーケンス

```
推論結果インポート:
┌─ User: Menu > Load Inference Results
├─ MainApplicationWindow.load_inference_results()
├─ QFileDialog.getOpenFileName()
├─ DataIOManager.import_inference_results(file_path)
│  ├─ JSONファイル読み込み
│  ├─ _convert_inference_to_annotations()
│  │  └─ Moment-DETR形式 → AnnotationItem変換
│  └─ 複数回のdata_manager.add_annotation()
├─ Signal: data_imported
├─ Signal: data_changed (最終的に1回)
└─ 各コントローラーのUI更新
```

### 7. データエクスポートシーケンス

```
STTエクスポート:
┌─ User: Menu > Export STT Dataset
├─ MainApplicationWindow.export_stt_dataset()
├─ QFileDialog.getSaveFileName()
├─ DataIOManager.export_to_stt_format(file_path, threshold)
│  ├─ _convert_annotations_to_stt(threshold)
│  │  ├─ 信頼度フィルタリング
│  │  └─ STT形式変換
│  └─ JSONファイル書き込み
├─ Signal: data_exported
└─ 成功メッセージ表示

推論結果エクスポート:
┌─ User: Menu > Export Inference Results
├─ MainApplicationWindow.export_inference_results()
├─ QFileDialog.getSaveFileName()
├─ DataIOManager.export_inference_results(file_path)
│  ├─ _convert_annotations_to_inference()
│  │  └─ Moment-DETR形式変換
│  └─ JSONファイル書き込み
├─ Signal: data_exported
└─ 成功メッセージ表示
```

## シグナル/スロット詳細マッピング

### AnnotationDataManager シグナル

```python
# データ変更通知
data_changed = pyqtSignal()
接続先:
├─ TimelineController.update_timeline()
├─ AnnotationListController.update_list()
└─ AnnotationEditorController._on_data_changed()

# 個別操作通知
annotation_added = pyqtSignal(object)
annotation_modified = pyqtSignal(object) 
annotation_deleted = pyqtSignal(str)  # annotation_id
接続先: ログ記録用

# 動画読み込み通知
video_loaded = pyqtSignal(object)  # VideoInfo
接続先:
├─ TimelineController.set_video_duration()
├─ VideoController._on_video_loaded()
└─ MainApplicationWindow._on_video_loaded()
```

### VideoController シグナル

```python
# 動画読み込み完了
video_loaded = pyqtSignal(str)  # video_path
接続先:
└─ MainApplicationWindow._on_video_controller_loaded()

# 再生位置変更
position_changed = pyqtSignal(float)  # seconds
接続先:
├─ TimelineController.set_current_position()
└─ MainApplicationWindow._update_position_display()

# 再生時間変更
duration_changed = pyqtSignal(float)  # seconds
接続先:
└─ TimelineController.set_video_duration()

# 再生状態変更
playback_state_changed = pyqtSignal(object)  # QMediaPlayer.PlaybackState
接続先:
└─ MainApplicationWindow._update_play_button()
```

### TimelineController シグナル

```python
# アノテーション区間クリック
interval_clicked = pyqtSignal(object)  # AnnotationItem
接続先:
├─ AnnotationListController.select_annotation()
└─ AnnotationEditorController.set_current_annotation()

# ドラッグ操作
interval_drag_started = pyqtSignal(object)  # AnnotationItem
interval_drag_moved = pyqtSignal(object, float, float)  # item, start, end
interval_drag_finished = pyqtSignal(object, float, float)  # item, start, end
接続先:
└─ MainApplicationWindow._on_interval_drag_finished()
   └─ AnnotationCommandManager.execute_modify_annotation()

# 新規区間作成
new_interval_created = pyqtSignal(float, float, str)  # start, end, type
接続先:
└─ MainApplicationWindow.create_new_annotation()

# 位置クリック
position_clicked = pyqtSignal(float)  # seconds
接続先:
└─ VideoController.seek_to_time()
```

### AnnotationListController シグナル

```python
# アノテーション選択
annotation_selected = pyqtSignal(object)  # AnnotationItem
接続先:
├─ TimelineController.set_highlighted_annotation()
├─ AnnotationEditorController.set_current_annotation()
└─ VideoController.seek_to_time() (annotation.start_time)

# フィルタ変更
filter_changed = pyqtSignal(str, float)  # type_filter, confidence_threshold
接続先:
└─ AnnotationDataManager.set_confidence_threshold()
```

### AnnotationEditorController シグナル

```python
# アノテーション修正
annotation_modified = pyqtSignal(object, dict)  # AnnotationItem, changes
接続先:
└─ MainApplicationWindow._on_annotation_modified()
   └─ AnnotationCommandManager.execute_modify_annotation()

# アノテーション削除
annotation_deleted = pyqtSignal(str)  # annotation_id
接続先:
└─ MainApplicationWindow._on_annotation_deleted()
   └─ AnnotationCommandManager.execute_delete_annotation()
```

### AnnotationCommandManager シグナル

```python
# コマンド実行通知
command_executed = pyqtSignal(str)  # command_description
接続先:
└─ MainApplicationWindow._on_command_executed() (ログ記録)

# Undo/Redo可能状態変更
undo_available = pyqtSignal(bool)
redo_available = pyqtSignal(bool)
接続先:
├─ MainApplicationWindow._update_undo_action()
└─ MainApplicationWindow._update_redo_action()
```

### DataIOManager シグナル

```python
# データインポート完了
data_imported = pyqtSignal(str, int)  # file_path, count
接続先:
└─ MainApplicationWindow._on_data_imported() (メッセージ表示)

# データエクスポート完了
data_exported = pyqtSignal(str, str)  # file_path, format
接続先:
└─ MainApplicationWindow._on_data_exported() (メッセージ表示)
```

## イベント処理の流れ

### マウス操作

```
Timeline上でのマウス操作:
┌─ TimelineTrack.mousePressEvent()
│  ├─ 位置計算
│  ├─ アノテーション検出
│  └─ ドラッグ状態初期化
├─ TimelineTrack.mouseMoveEvent()
│  ├─ ドラッグ中の処理
│  ├─ 視覚的フィードバック
│  └─ リアルタイム更新
└─ TimelineTrack.mouseReleaseEvent()
   ├─ 最終位置計算
   ├─ 操作種別判定
   └─ 適切なシグナル発信
```

### キーボード操作

```
ショートカットキー:
┌─ QShortcut.activated
├─ MainApplicationWindow: ハンドラー関数
├─ 対応するアクション実行
└─ 必要に応じてUI更新

例: Ctrl+Z (Undo)
┌─ QShortcut("Ctrl+Z").activated
├─ MainApplicationWindow._undo_action()
├─ AnnotationCommandManager.undo()
└─ データ復元 + UI更新
```

## エラーハンドリングパターン

### 1. データ操作エラー

```python
# AnnotationDataManager
def modify_annotation(self, index: int, **updates) -> bool:
    try:
        # 更新処理
        self.logger.info(f"Modified annotation {annotation.id}")
        return True
    except Exception as e:
        self.logger.error(f"Failed to modify annotation: {e}")
        raise  # 意図的に上位に伝播
```

### 2. ファイルI/Oエラー

```python
# DataIOManager
def import_inference_results(self, file_path: str) -> bool:
    try:
        # インポート処理
        self.data_imported.emit(file_path, len(annotations))
        return True
    except Exception as e:
        self.logger.error(f"Import failed: {e}")
        raise  # UI層でダイアログ表示
```

### 3. UI操作エラー

```python
# MainApplicationWindow
def load_inference_results(self):
    try:
        # ファイル選択・読み込み
        pass
    except Exception as e:
        self.logger.error(f"Failed to load inference: {e}")
        QMessageBox.critical(self, "Error", f"Failed to load file:\n{str(e)}")
```

## デバッグ支援機能

### 1. ログ出力パターン

```python
# 操作開始
self.logger.debug(f"Starting operation: {operation_name}")

# 重要な状態変更
self.logger.info(f"State changed: {old_state} -> {new_state}")

# 警告レベル
self.logger.warning(f"Unexpected condition: {condition}")

# エラー詳細
self.logger.error(f"Operation failed: {error_details}", exc_info=True)
```

### 2. デバッグ用メソッド

```python
# AnnotationDataManager
def get_debug_info(self) -> dict:
    return {
        'annotation_count': len(self.annotations),
        'video_info': self.video_info,
        'confidence_threshold': self.confidence_threshold,
        'next_id': self._next_id
    }
```

この詳細なコンポーネント相互作用図により、システム全体の動作を理解し、デバッグや拡張を効率的に行うことができます。
