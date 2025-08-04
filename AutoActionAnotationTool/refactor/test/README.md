# README.md

# Test Suite for Refactored Video Annotation Tool

このディレクトリには、リファクタリングされた動画アノテーションツールの包括的なテストスイートが含まれています。

## テスト構成

### テストファイル

1. **test_annotation_data_manager.py** - AnnotationDataManagerクラスのテスト
   - データクラス（AnnotationItem, VideoInfo）のテスト
   - アノテーションの追加・修正・削除
   - フィルタリング機能
   - 統計情報取得

2. **test_annotation_command_manager.py** - AnnotationCommandManagerクラスのテスト
   - コマンドパターンの実装テスト
   - Undo/Redo機能
   - 各種コマンド（Add, Modify, Delete）

3. **test_data_io_manager.py** - DataIOManagerクラスのテスト
   - 推論結果のインポート
   - STT形式エクスポート
   - 推論結果形式エクスポート
   - 動画メタデータ読み込み

4. **test_video_controller.py** - VideoControllerクラスのテスト
   - 動画読み込み・再生制御
   - シーク機能
   - UIコントロール

5. **test_timeline_controller.py** - TimelineControllerクラスのテスト
   - タイムライン表示
   - ドラッグ操作
   - アノテーションの視覚化

6. **test_annotation_list_controller.py** - AnnotationListControllerクラスのテスト
   - アノテーション一覧表示
   - フィルタリング機能
   - 選択管理

7. **test_annotation_editor_controller.py** - AnnotationEditorControllerクラスのテスト
   - アノテーション編集フォーム
   - ActionEditor/StepEditor
   - タブ管理

8. **test_main_application_window.py** - MainApplicationWindowクラスのテスト
   - UI統合テスト
   - メニュー・ショートカット
   - 全体的なワークフロー

### サポートファイル

- **conftest.py** - pytest設定とフィクスチャ（pytest使用時）
- **run_tests.py** - テスト実行スクリプト（unittest使用）
- **test_requirements.txt** - テスト用依存関係

## テスト実行方法

### 方法1: 標準のunittestを使用（推奨）

```bash
# 全てのテストを実行
cd AutoActionAnotationTool/refactor/test
python run_tests.py

# 依存関係チェック
python run_tests.py --check-deps

# 特定のテストモジュールを実行
python run_tests.py --test test_annotation_data_manager

# 詳細出力
python run_tests.py --verbose
```

### 方法2: pytestを使用（オプション）

pytestがインストールされている場合：

```bash
# テスト用依存関係をインストール
pip install -r test_requirements.txt

# 全てのテストを実行
pytest test/

# カバレッジ付きで実行
pytest test/ --cov=../ --cov-report=html

# 特定のテストを実行
pytest test/test_annotation_data_manager.py

# 詳細出力
pytest test/ -v
```

### 方法3: 個別実行

各テストファイルを個別に実行：

```bash
python test_annotation_data_manager.py
python test_annotation_command_manager.py
# ... 他のテストファイル
```

## テストの特徴

### 包括的なカバレッジ

- **クラスの全メソッドをテスト**: 各クラスの公開メソッドを網羅
- **エラーケースもテスト**: 正常系だけでなく異常系もカバー
- **シグナル/スロット連携**: PyQt6のシグナル/スロット機能をテスト
- **モックとスタブ**: 外部依存関係を適切にモック化

### テストパターン

1. **初期状態テスト**: オブジェクトの初期化状態を確認
2. **正常動作テスト**: 期待される動作を確認
3. **異常系テスト**: エラー条件での動作を確認
4. **境界値テスト**: 境界条件での動作を確認
5. **統合テスト**: 複数コンポーネント間の連携を確認

### モック化対象

- **OpenCV**: 動画ファイル操作
- **QFileDialog**: ファイル選択ダイアログ
- **QMessageBox**: メッセージボックス
- **QMediaPlayer**: 動画再生機能
- **ファイルI/O**: JSON読み書き操作

## テスト環境要件

### 必須要件

- Python 3.8+
- PyQt6
- OpenCV（または適切なモック）

### オプション要件

- pytest（高度なテスト機能）
- pytest-qt（PyQt特化テスト）
- coverage（カバレッジ測定）

## テストデータ

### サンプルデータ

テストでは以下のサンプルデータを使用：

```python
# VideoInfo
video_info = VideoInfo(
    video_id="test_video",
    video_path="/test/video.mp4",
    duration=60.0,
    fps=25.0,
    width=1280,
    height=720
)

# AnnotationItem (Action)
action_annotation = AnnotationItem(
    id="test_action_001",
    start_time=10.0,
    end_time=20.0,
    confidence_score=0.9,
    annotation_type="Action",
    category="manipulation",
    hand_type="right",
    object_name="cup",
    verb="grab"
)

# AnnotationItem (Step)
step_annotation = AnnotationItem(
    id="test_step_001",
    start_time=30.0,
    end_time=45.0,
    confidence_score=0.8,
    annotation_type="Step",
    category="cooking step"
)
```

## 継続的インテグレーション

テストスイートはCI/CDパイプラインに組み込み可能：

```yaml
# GitHub Actions例
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r test/test_requirements.txt
    - name: Run tests
      run: cd refactor && python test/run_tests.py
```

## トラブルシューティング

### よくある問題

1. **PyQt6インポートエラー**
   ```bash
   pip install PyQt6
   ```

2. **OpenCVエラー**
   ```bash
   pip install opencv-python
   ```

3. **テスト実行時のパスエラー**
   - `run_tests.py`を使用するか、PYTHONPATHを適切に設定

4. **GUI関連エラー**
   - ヘッドレス環境では`QT_QPA_PLATFORM=offscreen`を設定

### デバッグ

```bash
# 詳細ログ付きで実行
python run_tests.py --verbose

# 特定のテストクラスのみ実行
python -m unittest test_annotation_data_manager.TestAnnotationDataManager

# 単一テストメソッドのみ実行
python -m unittest test_annotation_data_manager.TestAnnotationDataManager.test_add_annotation
```

## テスト拡張

新しい機能を追加する際のテスト作成ガイドライン：

1. **新しいクラス**: 対応するtest_*.pyファイルを作成
2. **新しいメソッド**: 既存テストクラスにテストメソッドを追加
3. **新しいシグナル**: シグナル発信のテストを追加
4. **エラーケース**: 例外処理のテストを追加

## パフォーマンステスト

大量データでのパフォーマンステストも可能：

```python
def test_large_dataset_performance(self):
    """大量アノテーションでのパフォーマンステスト"""
    # 1000個のアノテーションを追加
    start_time = time.time()
    for i in range(1000):
        self.data_manager.add_annotation(...)
    end_time = time.time()
    
    # 処理時間が許容範囲内であることを確認
    assert end_time - start_time < 5.0  # 5秒以内
```

これらのテストにより、リファクタリングされたアーキテクチャの品質と信頼性を保証できます。
