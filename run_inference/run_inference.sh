#!/bin/bash  
  
# 引数チェック  
if [ $# -lt 2 ]; then  
    echo "Usage: ./run_inference.sh [video_file_path] [query1] [query2] ..."  
    echo "Example: ./run_inference.sh \"video.mp4\" \"person walking\" \"car driving\" \"dog running\""  
    exit 1  
fi  
  
VIDEO_PATH="$1"  
shift  # 最初の引数（ビデオパス）を削除  
QUERIES=("$@")  # 残りの引数をクエリ配列として取得  
  
# ビデオファイルの存在確認  
if [ ! -f "$VIDEO_PATH" ]; then  
    echo "Error: Video file '$VIDEO_PATH' not found."  
    exit 1  
fi  
  
echo "Running Moment-DETR inference..."  
echo "Video: $VIDEO_PATH"  
echo "Queries: ${QUERIES[@]}"  
echo  
  
# Pythonスクリプトを実行（クエリを引数として渡す）  
python inference_script.py "$VIDEO_PATH" "${QUERIES[@]}"  
  
if [ $? -ne 0 ]; then  
    echo "Error: Inference failed."  
    exit 1  
fi  
  
echo "Inference completed successfully."