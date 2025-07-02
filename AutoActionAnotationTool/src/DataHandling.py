import json  
from pathlib import Path  
from typing import List, Union
from datetime import datetime

from Results import QueryResults, InferenceResults

  
class InferenceResultsLoader:  
    def load_from_jsonl(self, file_path: Union[str, Path]) -> InferenceResults:  
        """Load results from moment_detr JSONL format"""  
        results = []  
        with open(file_path, 'r') as f:  
            for line in f:  
                if line.strip():  
                    data = json.loads(line)  
                    results.append(QueryResults.from_moment_detr_json(data))  
          
        return InferenceResults(  
            results=results,  
            timestamp=datetime.now(),  
            model_info={"source": str(file_path)}  
        )  
      
    def load_from_json(self, file_path: Union[str, Path]) -> InferenceResults:  
        """Load results from single JSON file"""  
        with open(file_path, 'r') as f:  
            data = json.load(f)  
          
        if isinstance(data, list):  
            results = [QueryResults.from_moment_detr_json(item) for item in data]  
        else:  
            results = [QueryResults.from_moment_detr_json(data)]  
          
        return InferenceResults(  
            results=results,  
            timestamp=datetime.now(),  
            model_info={"source": str(file_path)}  
        )  
  
class InferenceResultsSaver:  
    def save_to_jsonl(self, results: InferenceResults, file_path: Union[str, Path]):  
        """Save in moment_detr JSONL format"""  
        with open(file_path, 'w') as f:  
            for result in results.results:  
                json_data = {  
                    'qid': result.query_id,  
                    'query': result.query_text,  
                    'vid': result.video_id,  
                    'pred_relevant_windows': [  
                        [interval.start_time, interval.end_time, interval.confidence_score]  
                        for interval in result.relevant_windows  
                    ],  
                    'pred_saliency_scores': result.saliency_scores  
                }  
                f.write(json.dumps(json_data) + '\n')