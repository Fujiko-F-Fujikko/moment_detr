# README

## プロジェクト構成

このプロジェクトには2つのバージョンが含まれています：

1. **従来版** (`src/`): オリジナルの動画アノテーションツール
2. **リファクタリング版** (`refactor/`): 新アーキテクチャによる改良版

## 環境構築

### python

3.11.2

### コマンド手順

```cmd
python -m venv venv
source venv/Scripts/activate

python -m pip install --upgrade pip
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
※numpyは2.3.2でも動きます
```

## 実行手順

1. スクリプトによるアクション検出実行
```cmd
cd run_inference
./run_inference.sh <video_path> <query1> [query2] [query3] ... 

./run_inference.sh ../stt/20250724_object-annotation/H1125062070282_2025-06-20_12-39-19_0.mp4 "LeftHand_Hold_Camera Rear Cabin_None_None" "RightHand_Pickup_Cotton Swab_None_None" "BothHands_Hold_Camera Rear Cabin_None_None" "RightHand_Putdown_Camera Rear Cabin_Clear Tray_None"

./run_inference.sh ../stt/20250724_object-annotation/H1125062070282_2025-06-20_12-39-19_0.mp4 "a woman is holding a camera in front of workbench." "a woman is picking up cotton swab on workbench." "a woman is put cotton swab in the bottle on workbench." "a woman is put cotton swab on a camera." "a woman is put down cotton swab in the bottole on workbench."
"a woman is holding a camera in front of workbench."
"a woman is picking up cotton swab on workbench."
"a woman is put cotton swab in the bottle on workbench."
"a woman is put cotton swab on a camera."
"a woman is put down cotton swab in the bottole on workbench."
""



```
* ※ queryは`<LeftHand | RightHand | BothHands | Other>_<Verb>_<Maniqulated Object Name>_<Target Object Name>_<Tool Name>`の形式を想定していますが、どんな形式・文でも指定できます。ただし英語のみ。
* 手順2のツールでアノテーション結果を編集したい場合は、この形式に従って指定してください。指定するものがない場合は`None`と指定してください。

2. GUIツールでアノテーション結果の確認&編集

```cmd
cd ../ # ルートディレクトリに戻る
python AutoActionAnotationTool/src/MainApplicationWindow.py --video <path_to_video> --results <path_to_json_generated_by_step_1> 

# 従来版（オリジナル）
python AutoActionAnotationTool/src/MainApplicationWindow.py --video stt/20250724_object-annotation/H1125062070282_2025-06-20_12-39-19_0.mp4 --results run_inference/inference_results/result_H1125062070282_2025-06-20_12-39-19_0_20250726_225936.json 

# リファクタリング版（新アーキテクチャ）
python AutoActionAnotationTool/refactor/src/main_application_window.py --video stt/20250724_object-annotation/H1125062070282_2025-06-20_12-39-19_0.mp4 --results run_inference/inference_results/result_H1125062070282_2025-06-20_12-39-19_0_20250731_155055.json 

```

## リファクタリング版について

`refactor/` フォルダには、新しいアーキテクチャで再設計されたバージョンが含まれています：

### 主な改善点
- モジュール化されたアーキテクチャ
- 包括的なテストスイート
- 改良されたエラーハンドリング
- 詳細なドキュメント

### リファクタリング版の実行
```cmd
cd AutoActionAnotationTool/refactor/src
python main_application_window.py
```

詳細は `refactor/README.md` を参照してください。