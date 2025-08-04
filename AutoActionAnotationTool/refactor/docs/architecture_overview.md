# architecture_overview.md

# Refactored Video Annotation Tool - Architecture Overview

## システム全体構成

### レイヤー構造

```
┌─────────────────────────────────────────────────────┐
│                 Presentation Layer                  │
│                                                     │
│  ┌─────────────────────────────────────────────────┐ │
│  │         MainApplicationWindow                   │ │
│  │           (Entry Point)                         │ │
│  └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│                  Controller Layer                   │
│                                                     │
│  ┌───────────────┐ ┌───────────────┐ ┌──────────────┐ │
│  │VideoController│ │TimelineController│ │ListController│ │
│  └───────────────┘ └───────────────┘ └──────────────┘ │
│                                                     │
│  ┌─────────────────────────────────────────────────┐ │
│  │         AnnotationEditorController              │ │
│  └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│                  Business Layer                     │
│                                                     │
│  ┌───────────────┐ ┌───────────────┐ ┌──────────────┐ │
│  │DataIOManager  │ │CommandManager │ │DataManager   │ │
│  │               │ │               │ │              │ │
│  │- Import/Export│ │- Undo/Redo    │ │- Data Store  │ │
│  └───────────────┘ └───────────────┘ └──────────────┘ │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│                    Data Layer                       │
│                                                     │
│  ┌─────────────────────────────────────────────────┐ │
│  │              Data Classes                       │ │
│  │                                                 │ │
│  │  • AnnotationItem (Unified Step/Action)        │ │
│  │  • VideoInfo                                    │ │
│  │  • Command Objects                              │ │
│  └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

## コンポーネント間通信

### シグナル/スロット通信マップ

```
AnnotationDataManager (データソース)
├── data_changed ──┬── TimelineController.update_timeline()
│                  ├── AnnotationListController.update_list()
│                  └── AnnotationEditorController.refresh_current()
│
├── annotation_added ──── ログ記録
├── annotation_modified ── ログ記録
├── annotation_deleted ─── ログ記録
└── video_loaded ─────┬── TimelineController.set_video_duration()
                      └── VideoController.load_video()

TimelineController (タイムライン操作)
├── interval_clicked ─────── AnnotationListController.select_annotation()
├── interval_drag_finished ── AnnotationCommandManager.execute_modify()
├── new_interval_created ─── AnnotationCommandManager.execute_add()
└── position_clicked ─────── VideoController.seek_to_time()

AnnotationListController (リスト操作)
├── annotation_selected ─┬── TimelineController.set_highlighted()
│                        └── AnnotationEditorController.set_current()
└── filter_changed ────── AnnotationDataManager.set_confidence_threshold()

AnnotationEditorController (編集操作)
├── annotation_modified ── AnnotationCommandManager.execute_modify()
└── annotation_deleted ─── AnnotationCommandManager.execute_delete()

VideoController (ビデオ操作)
├── position_changed ──── TimelineController.set_current_position()
└── video_loaded ────── MainApplicationWindow.on_video_loaded()

AnnotationCommandManager (コマンド実行)
├── command_executed ──── ログ記録
├── undo_available ───── MainApplicationWindow.update_menu_state()
└── redo_available ───── MainApplicationWindow.update_menu_state()

DataIOManager (データIO)
├── data_imported ────── ログ記録・通知表示
└── data_exported ────── ログ記録・通知表示
```

## データフロー

### 1. 動画読み込みフロー

```
User Input (Open Video)
       ↓
MainApplicationWindow.open_video()
       ↓
VideoController.load_video()
       ↓
DataIOManager.load_video_metadata()
       ↓
AnnotationDataManager.load_video()
       ↓
Signal: video_loaded
       ↓
┌─────────────────┬─────────────────┐
│                 │                 │
TimelineController   (Other Controllers)
.set_video_duration()   .refresh_for_new_video()
```

### 2. アノテーション編集フロー

```
User Input (Edit Annotation)
       ↓
AnnotationEditorController
.apply_annotation_changes()
       ↓
AnnotationCommandManager
.execute_modify_annotation()
       ↓
ModifyAnnotationCommand.redo()
       ↓
AnnotationDataManager.modify_annotation()
       ↓
Signal: data_changed
       ↓
┌─────────────────┬─────────────────┬─────────────────┐
│                 │                 │                 │
TimelineController  ListController   EditorController
.update_timeline()  .update_list()   .refresh_current()
```

### 3. データインポートフロー

```
User Input (Load Inference)
       ↓
MainApplicationWindow.load_inference_results()
       ↓
DataIOManager.import_inference_results()
       ↓
DataIOManager._convert_inference_to_annotations()
       ↓
AnnotationDataManager.add_annotation() (複数回)
       ↓
Signal: data_changed (最終的に1回)
       ↓
全コントローラーのUI更新
```

## 責任分担

### MainApplicationWindow
- **役割**: アプリケーションのエントリポイント・UI統合
- **責任**:
  - 全コントローラーの生成と初期化
  - メニュー・ショートカットの管理
  - ウィンドウレイアウトの構築
  - 高レベル操作の調整

### AnnotationDataManager
- **役割**: データの一元管理・状態管理
- **責任**:
  - StepとActionの統一データ管理
  - 動画メタデータの管理
  - フィルタリング・検索機能
  - データ変更通知

### AnnotationCommandManager
- **役割**: 操作履歴管理・Undo/Redo
- **責任**:
  - コマンドパターンの実装
  - 操作の実行と取り消し
  - 操作履歴の管理

### DataIOManager
- **役割**: データの入出力・変換
- **責任**:
  - 推論結果のインポート
  - STT形式でのエクスポート
  - 動画メタデータの読み込み
  - 形式変換処理

### VideoController
- **役割**: 動画再生制御
- **責任**:
  - 動画ファイルの読み込み
  - 再生・停止・シーク制御
  - 動画UIウィジェットの管理

### TimelineController
- **役割**: タイムライン表示・操作
- **責任**:
  - アノテーションのビジュアル表示
  - ドラッグ操作の処理
  - 新規区間作成
  - トラック管理

### AnnotationListController
- **役割**: アノテーションリスト表示・フィルタ
- **責任**:
  - アノテーション一覧表示
  - タイプ別フィルタリング
  - 信頼度フィルタリング
  - 選択状態管理

### AnnotationEditorController
- **役割**: アノテーション詳細編集
- **責任**:
  - ActionとStepの編集フォーム
  - タブ切り替え管理
  - 入力値検証
  - 編集操作の実行

## エラーハンドリング戦略

### 1. デバッグ重視のエラー設計
- 例外は意図的に発生させてスタックトレースを確認
- 詳細なログ出力で操作の追跡が可能
- 段階的なデバッグができる構造

### 2. ログレベル戦略
```
DEBUG: 詳細な内部状態・処理フロー
INFO:  重要な操作・状態変更
WARNING: 回復可能な問題・非推奨使用
ERROR: 処理失敗・例外発生
```

### 3. 例外伝播ルール
- UIレイヤーでキャッチして適切なダイアログ表示
- ビジネスロジックでは例外を適切に伝播
- データレイヤーでは詳細なエラー情報を含める

## 拡張性設計

### 1. 新しいアノテーションタイプの追加
- `AnnotationItem`にフィールド追加
- 新しいエディターウィジェットの作成
- `TimelineTrack`での描画追加

### 2. 新しいエクスポート形式の追加
- `DataIOManager`にメソッド追加
- メニューへの項目追加
- 対応する変換ロジックの実装

### 3. プラグインシステムの準備
- インターフェースベースの設計
- シグナル/スロットによる疎結合
- コマンドパターンによる操作の標準化

## パフォーマンス考慮事項

### 1. 大量データ対応
- 遅延読み込み（Lazy Loading）
- ページネーション対応準備
- インデックス作成の準備

### 2. UI応答性
- 重い処理のワーカースレッド化準備
- プログレスバー表示の準備
- 非同期処理パターンの採用

### 3. メモリ管理
- 大きな動画ファイル対応
- 不要なデータの適切な解放
- キャッシュ戦略の準備
