import sys  
import json  
import os  
from pathlib import Path  
import torch
  
# moment_detrのパスを追加  
sys.path.append('../')  
  
from run_on_video.run import MomentDETRPredictor  
  
def main():  
    if len(sys.argv) < 3:  
        print("Usage: python inference_script.py <video_path> <query1> [query2] [query3] ...")  
        sys.exit(1)  
      
    video_path = sys.argv[1]  
    query_list = sys.argv[2:]  # 2番目以降の引数をクエリリストとして取得  
      
    # ビデオファイルの存在確認  
    if not os.path.exists(video_path):  
        print(f"Error: Video file '{video_path}' not found.")  
        sys.exit(1)  
      
    # モデルチェックポイントのパス  
    ckpt_path = "../run_on_video/moment_detr_ckpt/model_best.ckpt"  
      
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
            device="cuda" if torch.cuda.is_available() else "cpu"
        )
        print("Using device:", moment_detr_predictor.device)
          
        # 推論実行（複数クエリを一度に処理）  
        print(f"Running inference for {len(query_list)} queries...")  
        predictions = moment_detr_predictor.localize_moment(  
            video_path=video_path,   
            query_list=query_list  
        )  
          
        # 結果を整形  
        result = {  
            "video_path": video_path,  
            "total_queries": len(query_list),  
            "results": predictions  
        }  
          
        # JSON形式で出力  
        print("\n" + "="*50)  
        print("INFERENCE RESULTS (JSON):")  
        print("="*50)  
        print(json.dumps(result, indent=2, ensure_ascii=False))  
          
        # 結果をファイルにも保存  
        output_dir = "inference_results"
        if( not os.path.exists(output_dir)):
            os.makedirs(output_dir)
        output_file = os.path.join(output_dir, f"result_{Path(video_path).stem}_multi_query.json")
        with open(output_file, 'w', encoding='utf-8') as f:  
            json.dump(result, f, indent=2, ensure_ascii=False)  
        print(f"\nResult saved to: {output_file}")  
          
        # 各クエリの結果を個別に表示  
        print("\n" + "="*50)  
        print("INDIVIDUAL QUERY RESULTS:")  
        print("="*50)  
        for i, pred in enumerate(predictions):  
            print(f"\nQuery {i+1}: {pred['query']}")  
            print(f"Top prediction: {pred['pred_relevant_windows'][0] if pred['pred_relevant_windows'] else 'No predictions'}")  
          
    except Exception as e:  
        print(f"Error during inference: {str(e)}")  
        sys.exit(1)  
  
if __name__ == "__main__":  
    main()