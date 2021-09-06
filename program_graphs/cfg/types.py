from enum import Enum
from typing import List
from tree_sitter import Node  # type: ignore


class JumpKind(Enum):
    CONTINUE = 1
    BREAK = 2


BasicBlock = List[Node]
ForNode = Node
IfElseNode = Node
BlockNode = Node
SwitchNode = Node
Label = str
