MainApplicationWindowアプリ次のJsonデータを作れるようにするために、まずはそれぞれのデータを取得する機能を追加したいです。

```json
{
    "info": {"description": "STT Dataset 2025", "version": 1.0, "data_created": "2025/05/09"},
    "database": {
        "<Video name 1>": {
            "subset": "train", // "train" or "validation" or "test",
            "duration": 81.5, 
            "fps": 15,
            "actions": {
                "left_hand": [{
                    "action": {
                        "action_verb": "Grasp", "manipulated_object": "Cotton swab", 
                        "target_object": null, "tool": null
                    },
                    "ids": [1, 4, 8, 0],
                    "id": 10
                    "segment": [1.0, 2.5],
                    "segment(frames)": [15, 23],
                }],
                    "right_hand": [{...}, ...]
            },
            "steps": [{
                "step": "Apply Hanarl A to Rear cabinet",
                "id": 2,
                "segment": [1.0, 10.5],
                "segment(frames)": [15, 168],
            }]
        },
        …
    },
    "action_categories": [{"id": 10, "interaction": "Grasp_Cotton swab_None_None"}, ...],
    "step_categories": [{"id": 2, "Apply Hanarl A to Rear cabinet"}, ...]
}
```

以下、各要素に対する要件です。

* info::description: 固定値でOK
* info::version: 固定値でOK
* info::data created: エクスポートしたときの日時（自動取得）
* database::<video name 1,2,...>: 読み込んだ動画のファイル名（自動取得）
* database::<video name 1,2,...>::subset: "train" / "validation" / "test" のいずれか（GUIから設定）
* database::<video name 1,2,...>::duration: 動画の長さ（自動取得）
* database::<video name 1,2,...>::fps: 動画のフレームレート（自動取得）
* database::<video name 1,2,...>::actions::left hand or right hand: そのアノテーションが右手のものか左手のものか（アノテーションされているクエリから自動推定して分類・指定するが、GUIから修正できるようにする）
* database::<video name 1,2,...>::actions::action verb: アクションの名前（アノテーションされているクエリから自動推定（クエリの構造としてはaction_verb, manipulated_object, target_object, tool がこの順番で_で連結された文字列になっているはずなので、抜き出す）して初期値を埋めるが、GUIから修正できるようにする）
* database::<video name 1,2,...>::actions::manipulated object: 操作対象のオブジェクト名（アノテーションされているクエリから自動推定して初期値を埋めるが、GUIから修正できるようにする）この順番でこの順番でこの順番でこの順この順番で番でこのこの順番で
* database::<video name 1,2,...>::actions::target object: ターゲットオブジェクト名（アノテーションされているクエリから自動推定して初期値を埋めるが、GUIから修正できるようにする）
* database::<video name 1,2,...>::actions::tool: ツール名（アノテーションされているクエリから自動推定して初期値を埋めるが、GUIから修正できるようにする）
* database::<video name 1,2,...>::actions::ids: 一旦空でOK
* database::<video name 1,2,...>::actions::id: 後述のaction_categoriesのidと紐づく（自動）
* database::<video name 1,2,...>::actions::segment: アクションの開始と終了時間（アノテーション結果で初期値を埋めるが、既存のTimeline GUIから修正できるようにする）
* database::<video name 1,2,...>::actions::segment(frames): アクションの開始と終了フレーム（segmentの値と動画のfpsを使って計算して自動で埋める）
* database::<video name 1,2,...>::steps::step ステップ（作業工程）のクエリ（GUIから入力）
* database::<video name 1,2,...>::steps::id: 後述のstep_categoriesのidと紐づく（自動）
* database::<video name 1,2,...>::steps::segment: ステップの開始と終了時間（既存のTimeline GUIから入力）
* database::<video name 1,2,...>::steps::segment(frames): ステップの開始と終了フレーム（segmentの値と動画のfpsを使って計算して自動で埋める）
* action_categories::id: アクションのID（自動で割り振る）
* action_categories::interaction: アクションの名前（アノテーションのクエリ情報から自動生成する。クエリの構造としてはaction_verb, manipulated_object, target_object, tool が_で連結された文字列になっているはずなので、その文字列をそのまま使用する）
* step_categories::id: ステップのID（自動で割り振る）
* step_categories::step: ステップの名前（stepの文字列）

アノテーションのクエリの形式は [Left | Right | Both | None]_[<何らかの動作を表す文言>]_[<何らかの物体の名前> | None]_[<何らかの物体の名前> | None]_[<何らかのツールの名前> | None] とします。これに当てはまらない場合はエラーを出してください。


修正後のAutoActionAnotationToolのソースコードを全て出力してください。出力が長くなる場合は回答が途中で切れてしまう前に区切って出力してください。

