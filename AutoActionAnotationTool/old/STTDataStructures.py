from dataclasses import dataclass, field  
from typing import List, Optional, Dict, Any, Tuple  
from datetime import datetime  
  
@dataclass  
class ActionData:  
    action_verb: str  
    manipulated_object: Optional[str] = None  
    target_object: Optional[str] = None  
    tool: Optional[str] = None  
  
@dataclass  
class ActionEntry:  
    action: ActionData  
    ids: List[int] = field(default_factory=list)  
    id: int = 0  
    segment: List[float] = field(default_factory=list)  
    segment_frames: List[int] = field(default_factory=list)  
  
@dataclass  
class StepEntry:  
    step: str  
    id: int  
    segment: List[float] = field(default_factory=list)  
    segment_frames: List[int] = field(default_factory=list)  
  
@dataclass  
class VideoData:  
    subset: str = "train"  # "train", "validation", "test"  
    duration: float = 0.0  
    fps: float = 0.0  
    actions: Dict[str, List[ActionEntry]] = field(default_factory=lambda: {  
        "left_hand": [],   
        "right_hand": [],   
        "both_hands": [],  # 新しく追加  
        "unspecified": []  # 新しく追加  
    })  
    steps: List[StepEntry] = field(default_factory=list)  

@dataclass  
class ActionCategory:  
    id: int  
    interaction: str  
  
@dataclass  
class StepCategory:  
    id: int  
    step: str  
  
@dataclass  
class STTDataset:  
    info: Dict[str, Any] = field(default_factory=lambda: {  
        "description": "STT Dataset 2025",  
        "version": 1.0,  
        "data_created": datetime.now().strftime("%Y/%m/%d")  
    })  
    database: Dict[str, VideoData] = field(default_factory=dict)  
    action_categories: List[ActionCategory] = field(default_factory=list)  
    step_categories: List[StepCategory] = field(default_factory=list)  
    
class QueryValidationError(Exception):  
    """クエリ形式が不正な場合の例外"""  
    pass  
  
class QueryParser:  
    # 許可される手の種類  
    VALID_HAND_TYPES = {'LeftHand', 'RightHand', 'BothHands', 'None'}  
      
    @staticmethod  
    def validate_and_parse_query(query_text: str) -> Tuple[str, ActionData]:  
        """クエリテキストを検証し、アクション要素を抽出"""  
        #print(f"DEBUG: Parsing query: '{query_text}'")  
        parts = query_text.split('_')  
        #print(f"DEBUG: Query parts: {parts} (count: {len(parts)})")  
        
        if len(parts) != 5:  
            error_msg = f"クエリ形式が不正です。5つの要素が必要ですが、{len(parts)}個の要素が見つかりました: '{query_text}'"  
            print(f"DEBUG: {error_msg}")  
            raise QueryValidationError(error_msg)  
        
        hand_type, action_verb, manipulated_object, target_object, tool = parts  
        #print(f"DEBUG: Parsed - hand_type: {hand_type}, action_verb: {action_verb}")

        # 手の種類の検証  
        if hand_type not in QueryParser.VALID_HAND_TYPES:  
            raise QueryValidationError(  
                f"不正な手の種類です: '{hand_type}'. 許可される値: {QueryParser.VALID_HAND_TYPES}"  
            )  
          
        # 動作の検証（空文字列は許可しない）  
        if action_verb == "":  
            raise QueryValidationError(  
                f"動作が空文字列です: '{query_text}'"  
            )  
          
        # 物体名とツール名の検証（空文字列は許可しない）  
        for i, (name, part) in enumerate([  
            ("manipulated_object", manipulated_object),  
            ("target_object", target_object),   
            ("tool", tool)  
        ], 2):  # 2番目の要素から開始  
            if part == "":  
                raise QueryValidationError(  
                    f"要素{i+1}({name})が空文字列です。'None'を使用してください: '{query_text}'"  
                )  
          
        # ActionDataを作成  
        action_data = ActionData(  
            action_verb=action_verb,  
            manipulated_object=manipulated_object if manipulated_object != 'None' else None,  
            target_object=target_object if target_object != 'None' else None,  
            tool=tool if tool != 'None' else None  
        )  
          
        return hand_type, action_data

    @staticmethod  
    def detect_hand_type(query_text: str) -> str:  
        """クエリから手の種類を推定（新形式対応）"""  
        # Stepクエリの場合は検証をスキップ  
        if query_text.startswith("Step:"):  
            return 'unspecified'
        try:  
            hand_type, _ = QueryParser.validate_and_parse_query(query_text)  
            if hand_type == 'LeftHand':  
                return 'left_hand'  
            elif hand_type == 'RightHand':  
                return 'right_hand'  
            elif hand_type == 'BothHands':  
                return 'both_hands'  
            else:  # None  
                return 'unspecified'  
        except QueryValidationError:  
            # 旧形式のフォールバック  
            query_lower = query_text.lower()  
            if 'left' in query_lower or '左' in query_lower:  
                return 'left_hand'  
            elif 'right' in query_lower or '右' in query_lower:  
                return 'right_hand'  
            return 'right_hand'  # デフォルト