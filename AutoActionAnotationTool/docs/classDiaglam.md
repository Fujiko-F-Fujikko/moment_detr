# class diaglam

## abstract

moment_detrの推論結果JSONファイルを読み込んで動画の検出区間を確認できるViewerアプリケーションのクラス図です。実装に基づいて設計されています。

## クラス図

```mermaid
classDiagram
    class DetectionInterval {
        +float start_time
        +float end_time
        +float confidence_score
        +Optional~int~ query_id
        +Optional~string~ label
        +property duration() float
        +overlaps_with(other) bool
    }

    class QueryResults {
        +string query_text
        +string video_id
        +List~DetectionInterval~ relevant_windows
        +List~float~ saliency_scores
        +Optional~int~ query_id
        +from_moment_detr_json(json_data, index) QueryResults
    }

    class InferenceResults {
        +List~QueryResults~ results
        +datetime timestamp
        +dict model_info
        +Optional~string~ video_path
        +Optional~int~ total_queries
        +get_results_for_video(video_id) List~QueryResults~
    }

    class VideoInfo {
        +string video_id
        +string file_path
        +float duration
        +float fps
        +int width
        +int height
    }

    class InferenceResultsLoader {
        +load_from_json(file_path) InferenceResults
        +load_from_jsonl(file_path) InferenceResults
    }

    class InferenceResultsSaver {
        +save_to_json(results, file_path)
        +save_to_jsonl(results, file_path)
    }

    class SaliencyFilter {
        +float threshold
        +filter_by_saliency(query_results) List~Tuple~
        +get_salient_intervals(query_results, clip_duration) List~DetectionInterval~
        +apply_temporal_smoothing(saliency_scores, window_size) List~float~
    }

    class VideoPlayerController {
        +QMediaPlayer video_player
        +QVideoWidget video_widget
        +QPushButton play_button
        +QSlider position_slider
        +QLabel time_label
        +get_video_widget() QVideoWidget
        +get_controls_layout() QHBoxLayout
        +load_video(video_path)
        +toggle_playback()
        +seek_to_time(time_seconds)
        ~positionChanged pyqtSignal
        ~durationChanged pyqtSignal
    }

    class TimelineViewer {
        +float video_duration
        +List~DetectionInterval~ intervals
        +float playhead_position
        +create_timeline_widget() QWidget
        +set_intervals(intervals)
        +update_playhead_position(position)
        +draw_timeline()
        +on_click(event)
        ~intervalClicked pyqtSignal
    }

    class MultiTimelineViewer {
        +List~TimelineViewer~ timeline_widgets
        +QScrollArea scroll_area
        +set_query_results(query_results_list)
        +create_query_timeline(query_result) QWidget
        +set_video_duration(duration)
        +update_playhead_position(position)
        ~intervalClicked pyqtSignal
    }

    class ResultsManager {
        +InferenceResults inference_results
        +QueryResults current_query_results
        +float confidence_threshold
        +float saliency_threshold
        +InferenceResultsLoader inference_loader
        +InferenceResultsSaver inference_saver
        +load_inference_results(json_path)
        +save_inference_results(file_path)
        +set_ui_components(query_combo, results_list, confidence_label)
        +get_all_results() List~QueryResults~
        ~querySelected pyqtSignal
        ~intervalSelected pyqtSignal
        ~resultsUpdated pyqtSignal
    }

    class IntervalEditController {
        +int selected_interval_index
        +QueryResults current_query_results
        +QDoubleSpinBox start_spinbox
        +QDoubleSpinBox end_spinbox
        +QLabel confidence_label
        +QPushButton apply_button
        +QPushButton delete_button
        +QPushButton add_button
        +set_ui_components(...)
        +set_current_query_results(query_results)
        +set_selected_interval(interval, index)
        +apply_interval_changes()
        +delete_interval()
        +add_new_interval()
        ~intervalUpdated pyqtSignal
        ~intervalDeleted pyqtSignal
        ~intervalAdded pyqtSignal
    }

    class FileManager {
        +open_video_dialog(parent) string
        +load_inference_results_dialog(parent) string
        +save_results_dialog(parent) string
        +validate_video_file(file_path) bool
        +show_save_success_message(file_path, parent)
        +show_no_results_warning(parent)
        ~videoLoaded pyqtSignal
        ~resultsLoaded pyqtSignal
        ~resultsSaved pyqtSignal
    }

    class UILayoutManager {
        +dict ui_components
        +create_main_layout(left_panel, right_panel) QHBoxLayout
        +create_left_panel(video_widget, controls_layout, multi_timeline_viewer) QWidget
        +create_right_panel() tuple~QWidget, dict~
        +create_query_selection_group() tuple~QGroupBox, dict~
        +create_filter_controls_group() tuple~QGroupBox, dict~
        +create_interval_edit_group() tuple~QGroupBox, dict~
    }

    class ApplicationController {
        +VideoInfo video_info
        +InferenceResults inference_results
        +QueryResults current_query_results
        +InferenceResultsLoader loader
        +InferenceResultsSaver saver
        +SaliencyFilter saliency_filter
        +load_video(video_path) VideoInfo
        +load_inference_results(results_path)
        +get_results_for_current_video() List~QueryResults~
        +save_inference_results(file_path)
        +filter_intervals_by_confidence(intervals, threshold) List~DetectionInterval~
        ~intervalChanged pyqtSignal
    }

    class FilterController {
        +ApplicationController app_controller
        +float confidence_threshold
        +float saliency_threshold
        +set_confidence_threshold(threshold)
        +set_saliency_threshold(threshold)
        ~filtersChanged pyqtSignal
    }

    class MainApplicationWindow {
        +VideoPlayerController video_controller
        +ResultsManager results_manager
        +IntervalEditController interval_edit_controller
        +FileManager file_manager
        +UILayoutManager ui_layout_manager
        +ApplicationController app_controller
        +FilterController filter_controller
        +MultiTimelineViewer multi_timeline_viewer
        +setup_ui()
        +setup_connections()
        +setup_menus()
        +create_left_panel() QWidget
        +create_right_panel() tuple~QWidget, dict~
        +setup_controller_ui_components(ui_components)
    }

    %% 関係性
    InferenceResults --> QueryResults : 含有
    QueryResults --> DetectionInterval : 含有
    ApplicationController --> VideoInfo : 参照
    
    InferenceResultsLoader --> InferenceResults : 作成
    InferenceResultsLoader --> QueryResults : 作成
    InferenceResultsLoader --> DetectionInterval : 作成
    
    InferenceResultsSaver --> InferenceResults : 使用
    
    SaliencyFilter --> DetectionInterval : フィルタ
    SaliencyFilter --> QueryResults : フィルタ
    
    VideoPlayerController --> VideoInfo : 使用
    
    TimelineViewer --> DetectionInterval : 表示
    MultiTimelineViewer --> TimelineViewer : 含有
    MultiTimelineViewer --> QueryResults : 表示
    
    ResultsManager --> InferenceResults : 管理
    ResultsManager --> InferenceResultsLoader : 使用
    ResultsManager --> InferenceResultsSaver : 使用
    
    IntervalEditController --> DetectionInterval : 編集
    
    ApplicationController --> InferenceResults : 管理
    ApplicationController --> VideoInfo : 参照
    ApplicationController --> SaliencyFilter : 使用
    ApplicationController --> InferenceResultsLoader : 使用
    ApplicationController --> InferenceResultsSaver : 使用
    
    FilterController --> ApplicationController : 参照
    FilterController --> SaliencyFilter : 制御
    
    FileManager --> QFileDialog : 使用
    
    UILayoutManager --> QWidget : 作成
    
    MainApplicationWindow --> VideoPlayerController : 統制
    MainApplicationWindow --> ResultsManager : 統制
    MainApplicationWindow --> IntervalEditController : 統制
    MainApplicationWindow --> FileManager : 統制
    MainApplicationWindow --> UILayoutManager : 統制
    MainApplicationWindow --> ApplicationController : 統制
    MainApplicationWindow --> FilterController : 統制
    MainApplicationWindow --> MultiTimelineViewer : 表示
```

## 主要な設計決定

このクラス図は、実際に実装されたコードに基づいて作成されています。moment_detrの推論結果構造に対応し、PyQt6を使用したGUIアプリケーションとして設計されています。

### コアデータモデル

**DetectionInterval**は、`@dataclass`として実装され、開始/終了時刻、信頼度スコア、クエリIDを持つ個別の検出区間を表現します。実際のmoment_detr出力の`pred_relevant_windows`フォーマット`[開始時刻（秒）, 終了時刻（秒）, 信頼度スコア]`に対応しています。

**QueryResults**は単一クエリの結果をカプセル化し、複数の検出区間と関連する`pred_saliency_scores`配列を含みます。`from_moment_detr_json`クラスメソッドでJSONからの変換を行います。

**InferenceResults**は複数のクエリ結果を管理し、動画パス、タイムスタンプ、モデル情報なども保持します。

### UI制御レイヤー

**VideoPlayerController**はQMediaPlayerとQVideoWidgetを使用した動画再生制御を担当し、PyQt6のシグナル・スロット機構でイベント通知を行います。

**MultiTimelineViewer**は複数のクエリ結果を同時に表示するタイムライン表示を提供し、個々の**TimelineViewer**を組み合わせて実装されています。

**ResultsManager**は推論結果の読み込み、表示、管理を統合的に行い、UIコンポーネントとの連携を担当します。

### データ管理レイヤー

**InferenceResultsLoader**と**InferenceResultsSaver**は、JSONおよびJSONL形式でのファイル入出力を処理します。moment_detrの出力形式とアプリケーション内部形式の変換を担当します。

### フィルタリングシステム

**SaliencyFilter**は`pred_saliency_scores`を使用した閾値ベースのフィルタリングを実装し、時間的平滑化機能も提供します。

**FilterController**は信頼度とSaliency閾値の制御を統合し、**ApplicationController**と連携してフィルタリング処理を管理します。

### アーキテクチャパターン

この設計はMVC（Model-View-Controller）パターンとPyQt6のシグナル・スロット機構を組み合わせ、以下の特徴を持ちます：

- **MainApplicationWindow**がメインコントローラーとして各種サブコントローラーを統制
- **UILayoutManager**によるレイアウト管理の分離
- **FileManager**による一元的なファイル操作管理
- シグナル・スロットによる疎結合な部品間通信

この設計により、動画アノテーションワークフローのための保守可能で拡張可能なアプリケーションを実現しています。

## 実装状況

### 実装済みクラス
- DetectionInterval（データクラス）
- QueryResults、InferenceResults（データクラス）
- VideoInfo（データクラス）
- InferenceResultsLoader、InferenceResultsSaver（データ処理）
- SaliencyFilter（フィルタリング）
- VideoPlayerController（動画制御）
- TimelineViewer、MultiTimelineViewer（タイムライン表示）
- ResultsManager（結果管理）
- IntervalEditController（区間編集）
- FileManager（ファイル操作）
- UILayoutManager（レイアウト管理）
- ApplicationController（アプリケーション制御）
- FilterController（フィルタ制御）
- MainApplicationWindow（メインウィンドウ）

### 廃止されたクラス（設計から削除）
- VideoPlayer（VideoPlayerControllerに統合）
- IntervalEditor（IntervalEditControllerに統合）
- SaliencyThresholdController（MainApplicationWindowに統合）
- IntervalModificationController（実装不要と判断）

## Notes

この実装は、実際のコードベースに基づいて設計されており、PyQt6のGUIフレームワークを活用しています。moment_detrのJSON出力形式（`pred_relevant_windows`と`pred_saliency_scores`）に対応し、動画ファイルごとの複数クエリ結果をサポートします。

シグナル・スロット機構により、各コンポーネント間の疎結合を実現し、区間編集、フィルタリング、動画再生の連携を効率的に行います。データの整合性を保ちながら、ユーザーが動的に閾値を調整できる仕組みを提供しています。