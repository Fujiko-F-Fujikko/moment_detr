import sys  
import json  
import os  
from pathlib import Path  
import torch

# moment_detrのパスを追加  
sys.path.append('.')  
  
from run_on_video.run import MomentDETRPredictor  
  
def main():  
    if len(sys.argv) != 3:  
        print("Usage: python inference_script.py <video_path> <query_text>")  
        sys.exit(1)  
      
    video_path = sys.argv[1]  
    query_text = sys.argv[2]  
      
    # ビデオファイルの存在確認  
    if not os.path.exists(video_path):  
        print(f"Error: Video file '{video_path}' not found.")  
        sys.exit(1)  
      
    # モデルチェックポイントのパス  
    ckpt_path = "run_on_video/moment_detr_ckpt/model_best.ckpt"  
      
    if not os.path.exists(ckpt_path):  
        print(f"Error: Model checkpoint '{ckpt_path}' not found.")  
        print("Please download the pre-trained model checkpoint.")  
        sys.exit(1)  
      
    try:  
        # MomentDETRPredictorの初期化  
        print("Loading Moment-DETR model...")  
        moment_detr_predictor = MomentDETRPredictor(  
            ckpt_path=ckpt_path,  
            clip_model_name_or_path="ViT-B/32",  
            device='cuda' if torch.cuda.is_available() else 'cpu'
        )  
        print("Using device:", moment_detr_predictor.device)
          
        # 推論実行  
        print("Running inference...")  
        query_list = [query_text]  
        predictions = moment_detr_predictor.localize_moment(  
            video_path=video_path,   
            query_list=query_list  
        )  
          
        # 結果を整形  
        result = {  
            "video_path": video_path,  
            "query": query_text,  
            "predictions": predictions[0] if predictions else {}  
        }  
          
        # JSON形式で出力  
        print("\n" + "="*50)  
        print("INFERENCE RESULT (JSON):")  
        print("="*50)  
        print(json.dumps(result, indent=2, ensure_ascii=False))  
          
        # 結果をファイルにも保存  
        output_file = f"result_{Path(video_path).stem}.json"  
        with open(output_file, 'w', encoding='utf-8') as f:  
            json.dump(result, f, indent=2, ensure_ascii=False)  
        print(f"\nResult saved to: {output_file}")  
          
    except Exception as e:  
        print(f"Error during inference: {str(e)}")  
        sys.exit(1)  
  
if __name__ == "__main__":  
    main()