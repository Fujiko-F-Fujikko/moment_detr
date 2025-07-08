# HandTypeFilterManager.py  
from PyQt6.QtCore import QObject, pyqtSignal  
from typing import List, Dict  
from STTDataStructures import QueryParser, QueryValidationError  
from Results import QueryResults  
  
class HandTypeFilterManager(QObject):  
    filterChanged = pyqtSignal()  
      
    def __init__(self):  
        super().__init__()  
        self.current_filter = "All"  # "All", "LeftHand", "RightHand", "BothHands", "Steps"  
        self.all_results = []  
          
    def set_results(self, results: List[QueryResults]):  
        """全ての結果を設定"""  
        self.all_results = results  
        self.filterChanged.emit()  
      
    def set_filter(self, filter_type: str):  
        """フィルタタイプを設定"""  
        self.current_filter = filter_type  
        self.filterChanged.emit()  
      
    def get_filtered_results(self) -> List[QueryResults]:  
        """現在のフィルタに基づいて結果を返す"""  
        print(f"DEBUG: Current filter: {self.current_filter}")  
        print(f"DEBUG: Total results: {len(self.all_results)}")  
        
        if self.current_filter == "All":  
            print(f"DEBUG: Returning all {len(self.all_results)} results")  
            return self.all_results  
        
        filtered_results = []  
        for result in self.all_results:  
            try:  
                hand_type, _ = QueryParser.validate_and_parse_query(result.query_text)  
                print(f"DEBUG: Query '{result.query_text}' -> hand_type: {hand_type}")  
                # フィルタリングロジック...  
            except QueryValidationError as e:  
                print(f"DEBUG: Query validation error for '{result.query_text}': {e}")  
        
        print(f"DEBUG: Filtered results count: {len(filtered_results)}")  
        return filtered_results
      
    def get_grouped_results(self) -> Dict[str, List[QueryResults]]:  
        """hand type毎にグループ化された結果を返す"""  
        groups = {  
            "LeftHand": [],  
            "RightHand": [],  
            "BothHands": [],  
            "Steps": []  
        }  
          
        for result in self.all_results:  
            try:  
                hand_type, _ = QueryParser.validate_and_parse_query(result.query_text)  
                if hand_type == "LeftHand":  
                    groups["LeftHand"].append(result)  
                elif hand_type == "RightHand":  
                    groups["RightHand"].append(result)  
                elif hand_type == "BothHands":  
                    groups["BothHands"].append(result)  
                else:  # None  
                    groups["Steps"].append(result)  
            except QueryValidationError:  
                groups["Steps"].append(result)  
          
        return groups