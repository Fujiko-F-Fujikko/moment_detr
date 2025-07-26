# README

## 環境構築

### python

3.11.2

### コマンド手順

```cmd
python -m venv venv
source venv/Scripts/activate

python -m pip install --upgrade pip
pip install numpy==1.26.4
pip install torch==2.1.2+cu118 torchvision==0.16.2+cu118 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cu118
pip install -r requirements.txt
```

## 実行手順

```cmd
python AutoActionAnotationTool/src/MainApplicationWindow.py --video run_on_video/example/RoripwjYFp8_60.0_210.0.mp4 --results AutoActionAnotationTool/sample_data/dummy_stt_json.json 
```