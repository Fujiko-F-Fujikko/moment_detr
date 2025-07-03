import json  
from pathlib import Path  
from typing import List, Union
from datetime import datetime

from Results import QueryResults, InferenceResults

  
class InferenceResultsLoader:    
    def load_from_json(self, file_path: Union[str, Path]) -> InferenceResults:    
        """Load results from single JSON file"""    
        with open(file_path, 'r') as f:    
            data = json.load(f)    
            
        # 新しい形式の場合  
        if 'results' in data and 'video_path' in data:  
            results = []  
            for i, item in enumerate(data['results']):  
                query_result = QueryResults.from_moment_detr_json(item, i)  
                results.append(query_result)  
              
            return InferenceResults(    
                results=results,    
                timestamp=datetime.now(),    
                model_info={"source": str(file_path)},  
                video_path=data.get('video_path'),  
                total_queries=data.get('total_queries')  
            )  
          
        # 従来の形式の場合（後方互換性）  
        if isinstance(data, list):    
            results = [QueryResults.from_moment_detr_json(item, i) for i, item in enumerate(data)]    
        else:    
            results = [QueryResults.from_moment_detr_json(data, 0)]    
            
        return InferenceResults(    
            results=results,    
            timestamp=datetime.now(),    
            model_info={"source": str(file_path)}    
        )  

class InferenceResultsSaver:    
    def save_to_json(self, results: InferenceResults, file_path: Union[str, Path]):    
        """Save in new JSON format"""    
        with open(file_path, 'w') as f:    
            output_data = {  
                "video_path": results.video_path or "",  
                "total_queries": results.total_queries or len(results.results),  
                "results": []  
            }  
              
            for result in results.results:    
                json_data = {    
                    'query': result.query_text,    
                    'vid': result.video_id,    
                    'pred_relevant_windows': [    
                        [interval.start_time, interval.end_time, interval.confidence_score]    
                        for interval in result.relevant_windows    
                    ],    
                    'pred_saliency_scores': result.saliency_scores    
                }    
                output_data["results"].append(json_data)  
              
            json.dump(output_data, f, indent=2)