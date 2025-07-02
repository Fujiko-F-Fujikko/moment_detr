#!/bin/bash

# 引数チェック
if [ $# -ne 2 ]; then
    echo "Usage: ./run_inference.sh [video_file_path] [query_text]"
    echo "Example: ./run_inference.sh \"video.mp4\" \"person walking in the park\""
    exit 1
fi

VIDEO_PATH="$1"
QUERY_TEXT="$2"

# ビデオファイルの存在確認
if [ ! -f "$VIDEO_PATH" ]; then
    echo "Error: Video file '$VIDEO_PATH' not found."
exit 1
fi

echo "Running Moment-DETR inference..."
echo "Video: $VIDEO_PATH"
echo "Query: $QUERY_TEXT"
echo

# Pythonスクリプトを実行
python inference_script.py "$VIDEO_PATH" "$QUERY_TEXT"

if [ $? -ne 0 ]; then
    echo "Error: Inference failed."
exit 1
fi

echo "Inference completed successfully."
