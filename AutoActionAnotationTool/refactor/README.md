# README.md

# Refactored Video Annotation Tool

## 概要

このディレクトリには、提案されたアーキテクチャに基づいてリファクタリングされた動画アノテーションツールが含まれています。

## アーキテクチャ

### 主要クラス構成（7クラス）

1. **AnnotationDataManager** - アノテーションデータの一元管理
2. **AnnotationCommandManager** - Undo/Redo管理
3. **DataIOManager** - データインポート/エクスポート管理
4. **VideoController** - ビデオコントロール
5. **TimelineController** - タイムラインコントロール
6. **AnnotationListController** - アノテーションリストコントロール
7. **AnnotationEditorController** - アノテーション編集タブコントロール

### エントリポイント

- **MainApplicationWindow** - メインアプリケーションウィンドウ

## 主要な改善点

### データ管理の一元化
- `AnnotationDataManager`でStepとActionを統一管理
- STT形式は`DataIOManager`でエクスポート時のみ生成
- 内部は統一した`AnnotationItem`データクラスで管理

### 責任の明確化
- 各コントローラーが特定の機能領域を担当
- シグナル/スロットで疎結合な連携
- コマンドパターンによるUndo/Redo機能

### デバッグ性の向上
- 各クラスに詳細なログ出力
- エラー時の例外は意図的に発生させる設計
- 段階的なデバッグが可能

### 現状機能の完全保持
- GUIレイアウトは現状維持
- 全ての既存機能を新アーキテクチャで実現
- デグレを防ぐための設計

## ファイル構成

```
refactor/
├── src/
│   ├── annotation_data_manager.py         # アノテーションデータ管理
│   ├── annotation_command_manager.py      # Undo/Redo管理
│   ├── data_io_manager.py                 # データIO管理
│   ├── video_controller.py                # ビデオ制御
│   ├── timeline_controller.py             # タイムライン制御
│   ├── annotation_list_controller.py      # アノテーションリスト制御
│   ├── annotation_editor_controller.py    # アノテーション編集制御
│   └── main_application_window.py         # メインウィンドウ（エントリポイント）
├── test/
│   ├── conftest.py                        # pytest設定
│   ├── run_tests.py                       # テスト実行スクリプト
│   ├── test_*.py                          # 各クラスのテストファイル
│   └── test_requirements.txt              # テスト用依存関係
├── docs/
│   ├── architecture_overview.md           # アーキテクチャ概要
│   ├── class_diagram.md                   # クラス図
│   └── component_interactions.md          # コンポーネント相互作用
├── requirements.txt                       # 必要ライブラリ
└── README.md                              # このファイル
```

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. アプリケーション実行

```bash
cd src
python main_application_window.py
```

## 主要機能

### 動画管理
- 動画ファイルの読み込み
- 再生・一時停止・シーク制御
- 動画メタデータの管理

### アノテーション管理
- ActionとStepアノテーションの統一管理
- 信頼度フィルタリング
- タイムライン上での直感的な編集

### データインポート/エクスポート
- Moment-DETR推論結果のインポート
- STT形式でのエクスポート
- 推論結果形式でのエクスポート

### 編集機能
- ドラッグによる区間調整
- 新規アノテーション作成
- 詳細情報の編集
- Undo/Redo機能

### フィルタリング
- アノテーションタイプ別フィルタ
- 信頼度による閾値フィルタ
- リアルタイムフィルタリング

## キーボードショートカット

- **Ctrl+O**: 動画を開く
- **Ctrl+L**: 推論結果を読み込み
- **Ctrl+E**: STTデータセットをエクスポート
- **Ctrl+Shift+E**: 推論結果をエクスポート
- **Ctrl+Z**: Undo
- **Ctrl+Y**: Redo
- **Space**: 再生/一時停止
- **Left/Right**: シーク（1秒）
- **Delete**: 選択中のアノテーション削除
- **Escape**: 選択クリア
- **Ctrl+Shift+A**: 新規アクションアノテーション
- **Ctrl+Shift+S**: 新規ステップアノテーション

## 技術的特徴

### コマンドパターン
- 全ての編集操作はコマンドとして実装
- 完全なUndo/Redo機能
- 操作履歴の管理

### シグナル/スロット
- PyQt6のシグナル/スロットによる疎結合設計
- リアルタイムなUI更新
- イベント駆動アーキテクチャ

### データクラス
- 型安全なデータ構造
- 自動的なシリアライゼーション
- 明確なデータ仕様

### ログ機能
- 詳細なログ出力
- デバッグ情報の追跡
- 操作履歴の記録

## 拡張性

この設計では以下の拡張が容易です：

1. **新しいアノテーションタイプの追加**
2. **追加のエクスポート形式**
3. **高度なフィルタリング機能**
4. **プラグインシステム**
5. **ネットワーク機能**

## 注意事項

- OpenCVが動画メタデータ読み込みに必要
- PyQt6の最新版を推奨
- 大きな動画ファイルではメモリ使用量に注意
