from enum import Enum
from typing import List, Tuple
from tree_sitter import Node  # type: ignore


class JumpKind(Enum):
    CONTINUE = 1
    BREAK = 2


NodeID = int
Edge = Tuple[NodeID, NodeID]
BasicBlock = List[Node]
ForNode = Node
IfElseNode = Node
BlockNode = Node
SwitchNode = Node
Label = str
