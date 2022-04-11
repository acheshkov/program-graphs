from typing import Tuple
from tree_sitter import Node  # type: ignore

ASTNode = Node
NodeID = int
Edge = Tuple[NodeID, NodeID]
