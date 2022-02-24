from typing import Optional, Tuple, List
import os
from program_graphs.adg.adg import ADG, mk_empty_adg
from program_graphs.adg.parser.java.data_dependency import add_data_dependency_layer
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.utils import get_project_root
from program_graphs.types import NodeID, ASTNode
from functools import reduce
from program_graphs.adg.parser.java.switch_stmt import get_switch_block_label, get_switch_label, get_nodes_after_colon


def parse(source_code: str) -> ADG:
    Language.build_library(
        # Store the library in the `build` directory
        'build/my-languages.so',

        # Include one or more languages
        [
            os.path.join(get_project_root(), "tree-sitter-java")
        ]
    )
    JAVA_LANGUAGE = Language('build/my-languages.so', 'java')
    parser = Parser()
    parser.set_language(JAVA_LANGUAGE)
    source_code_bytes = bytes(source_code, 'utf-8')
    ast = parser.parse(source_code_bytes)
    return parse_from_ast(ast.root_node, source_code_bytes)


def parse_from_ast(ast: ASTNode, source_code_bytes: bytes) -> ADG:
    adg = mk_empty_adg()
    mk_adg(ast, adg, parent_adg_node=None, source=source_code_bytes)
    adg.wire_return_nodes()
    add_data_dependency_layer(adg, source_code_bytes)
    return adg


EntryNode = NodeID
ExitNode = NodeID

# flake8: noqa: C901
def mk_adg(
    node: ASTNode,
    adg: ADG,
    parent_adg_node: Optional[NodeID] = None,
    source: bytes = None
) -> Tuple[EntryNode, ExitNode]:
    # print(node.type)
    if node.type == 'program':
        return mk_adg_block(node, adg, parent_adg_node)

    if node.type == 'block':
        return mk_adg_block(node, adg, parent_adg_node)

    if node.type == 'enhanced_for_statement':
        return mk_adg_enhanced_for(node, adg, parent_adg_node)

    if node.type == 'for_statement':
        return mk_adg_for(node, adg, parent_adg_node)

    if node.type == 'while_statement':
        return mk_adg_while(node, adg, parent_adg_node)

    if node.type == 'do_statement':
        return mk_adg_do_while(node, adg, parent_adg_node)

    if node.type == 'if_statement':
        return mk_adg_if(node, adg, parent_adg_node)

    if node.type == 'switch_expression':
        return mk_adg_switch(node, adg, parent_adg_node)

    if node.type == 'continue_statement':
        return mk_adg_continue(node, adg, parent_adg_node)

    if node.type == 'break_statement':
        return mk_adg_break(node, adg, parent_adg_node)

    if node.type == 'return_statement':
        return mk_adg_return(node, adg, parent_adg_node)

    if node.type == 'local_variable_declaration':
        return mk_variable_declaration(node, adg, parent_adg_node)

    return mk_default(node, adg, parent_adg_node)


def mk_adg_enhanced_for(node: ASTNode, adg: ADG, parent_adg_node: Optional[NodeID] = None) -> Tuple[EntryNode, ExitNode]:
    ast_node_body = node.child_by_field_name('body')
    if ast_node_body.type == ';':
        return mk_default(node, adg, parent_adg_node)

    node_for_entry = adg.add_ast_node(ast_node=node)
    node_for_exit = adg.add_node(name='for_exit')
    node_body_entry, node_body_exit = mk_adg(ast_node_body, adg)
    if parent_adg_node is not None:
        adg.add_edge(parent_adg_node, node_for_entry, syntax=True)

    adg.add_edge(node_for_entry, node_body_entry, syntax=True, cdep=True, cflow=True)
    adg.add_edge(node_for_entry, node_for_exit, syntax=True, cdep=True, cflow=True, exit=True)
    adg.add_edge(node_body_exit, node_for_entry, cflow=True)

    return node_for_entry, node_for_exit


def mk_adg_for(node: ASTNode, adg: ADG, parent_adg_node: Optional[NodeID] = None) -> Tuple[EntryNode, ExitNode]:
    node_for_entry = adg.add_ast_node(ast_node=node)
    node_init = adg.add_ast_node(ast_node=node.child_by_field_name('init'), name='for_init')
    node_condition = adg.add_ast_node(ast_node=node.child_by_field_name('condition'), name='for_condition')
    node_body_entry, node_body_exit = mk_adg(node.child_by_field_name('body'), adg)
    node_update = adg.add_ast_node(ast_node=node.child_by_field_name('update'), name='for_update')
    node_for_exit = adg.add_node(name='for_exit')

    if parent_adg_node is not None:
        adg.add_edge(parent_adg_node, node_for_entry, syntax=True)
    adg.add_edge(node_for_entry, node_init, syntax=True, cflow=True, cdep=True)
    adg.add_edge(node_for_entry, node_condition, syntax=True, cdep=True)
    adg.add_edge(node_for_entry, node_body_entry, syntax=True)
    adg.add_edge(node_for_entry, node_update, syntax=True)
    adg.add_edge(node_for_entry, node_for_exit, syntax=True, cdep=True, exit=True)
    adg.add_edge(node_init, node_condition, cflow=True)
    adg.add_edge(node_condition, node_body_entry, cflow=True, cdep=True)
    adg.add_edge(node_body_exit, node_update, cflow=True)
    adg.add_edge(node_update, node_condition, cflow=True, back=True)
    adg.add_edge(node_condition, node_for_exit, cflow=True)
    adg.add_edge(node_condition, node_update, cdep=True)

    while continue_node := adg.pop_continue_node():
        adg.remove_edges_from([e for e in adg.out_edges(continue_node)])
        adg.add_edge(continue_node, node_update, cflow=True)

    while break_node := adg.pop_break_node():
        adg.remove_edges_from([e for e in adg.out_edges(break_node)])
        adg.add_edge(break_node, node_for_exit, cflow=True)

    return node_for_entry, node_for_exit


def mk_adg_while(node: ASTNode, adg: ADG, parent_adg_node: Optional[NodeID] = None) -> Tuple[EntryNode, ExitNode]:
    node_while_entry = adg.add_ast_node(ast_node=node)
    node_condition = adg.add_ast_node(ast_node=node.child_by_field_name('condition'), name='while_condition')
    node_body_entry, node_body_exit = mk_adg(node.child_by_field_name('body'), adg)
    node_while_exit = adg.add_node(name='while_exit')

    if parent_adg_node is not None:
        adg.add_edge(parent_adg_node, node_while_entry, syntax=True)

    adg.add_edge(node_while_entry, node_condition, syntax=True, cdep=True, cflow=True)
    adg.add_edge(node_while_entry, node_body_entry, syntax=True)
    adg.add_edge(node_while_entry, node_while_exit, syntax=True, cdep=True, exit=True)
    adg.add_edge(node_condition, node_body_entry, cflow=True, cdep=True)
    adg.add_edge(node_condition, node_while_exit, cflow=True)
    adg.add_edge(node_condition, node_condition, cdep=True)
    adg.add_edge(node_body_exit, node_condition, cflow=True)

    while continue_node := adg.pop_continue_node():
        adg.remove_edges_from([e for e in adg.out_edges(continue_node)])
        adg.add_edge(continue_node, node_condition, cflow=True)

    while break_node := adg.pop_break_node():
        adg.remove_edges_from([e for e in adg.out_edges(break_node)])
        adg.add_edge(break_node, node_while_exit, cflow=True)

    return node_while_entry, node_while_exit


def mk_adg_do_while(node: ASTNode, adg: ADG, parent_adg_node: Optional[NodeID] = None) -> Tuple[EntryNode, ExitNode]:
    node_while_entry = adg.add_ast_node(ast_node=node)
    node_condition = adg.add_ast_node(ast_node=node.child_by_field_name('condition'), name='do_condition')
    node_body_entry, node_body_exit = mk_adg(node.child_by_field_name('body'), adg)
    node_while_exit = adg.add_node(name='do_while_exit')

    if parent_adg_node is not None:
        adg.add_edge(parent_adg_node, node_while_entry, syntax=True)

    adg.add_edge(node_while_entry, node_condition, syntax=True, cdep=True)
    adg.add_edge(node_while_entry, node_body_entry, syntax=True, cflow=True, cdep=True)
    adg.add_edge(node_while_entry, node_while_exit, syntax=True, cdep=True, exit=True)
    adg.add_edge(node_condition, node_body_entry, cflow=True, cdep=True)
    adg.add_edge(node_condition, node_while_exit, cflow=True)
    adg.add_edge(node_condition, node_condition, cdep=True)
    adg.add_edge(node_body_exit, node_condition, cflow=True)

    while continue_node := adg.pop_continue_node():
        adg.remove_edges_from([e for e in adg.out_edges(continue_node)])
        adg.add_edge(continue_node, node_condition, cflow=True)

    while break_node := adg.pop_break_node():
        adg.remove_edges_from([e for e in adg.out_edges(break_node)])
        adg.add_edge(break_node, node_while_exit, cflow=True)

    return node_while_entry, node_while_exit


def mk_adg_if(node: ASTNode, adg: ADG, parent_adg_node: Optional[NodeID] = None) -> Tuple[EntryNode, ExitNode]:
    node_if_entry = adg.add_ast_node(ast_node=node, name='if')
    node_condition = adg.add_ast_node(ast_node=node.child_by_field_name('condition'), name='if_condition')
    node_body_entry, node_body_exit = mk_adg(node.child_by_field_name('consequence'), adg)
    node_if_exit = adg.add_node(name='if_exit')

    if parent_adg_node is not None:
        adg.add_edge(parent_adg_node, node_if_entry, syntax=True)

    adg.add_edge(node_if_entry, node_condition, syntax=True, cflow=True, cdep=True)
    adg.add_edge(node_if_entry, node_body_entry, syntax=True)
    adg.add_edge(node_condition, node_body_entry, cflow=True, cdep=True)
    adg.add_edge(node_if_entry, node_if_exit, syntax=True, cdep=True, exit=True)

    adg.add_edge(node_body_exit, node_if_exit, cflow=True)

    if node.child_by_field_name('alternative') is not None:
        node_else_entry, node_else_exit = mk_adg(node.child_by_field_name('alternative'), adg)
        adg.add_edge(node_if_entry, node_else_entry, syntax=True)
        adg.add_edge(node_condition, node_else_entry, cflow=True, cdep=True)
        adg.add_edge(node_else_exit, node_if_exit, cflow=True)
    else:
        adg.add_edge(node_condition, node_if_exit, cflow=True)

    return node_if_entry, node_if_exit


def mk_adg_switch(node: ASTNode, adg: ADG, parent_adg_node: Optional[NodeID] = None) -> Tuple[EntryNode, ExitNode]:
    node_switch_entry = adg.add_ast_node(ast_node=node, name='switch')
    node_switch_exit = adg.add_node(name='switch_exit')
    groups: List[ASTNode] = [n for n in node.child_by_field_name('body').children if n.type == 'switch_block_statement_group']
    case_groups = [mk_adg_switch_case_group(g, adg) for g in groups if get_switch_block_label(g) == 'case']
    default_groups = [mk_adg_switch_default_group(g, adg) for g in groups if get_switch_block_label(g) == 'default']
    combine(case_groups + default_groups , adg, node_switch_entry, node_switch_exit)
    # default_group_adg = combine([mk_adg_switch_default_group(g, adg) for g in default_groups], adg, node_switch_entry, node_switch_exit)
    return node_switch_entry, node_switch_exit

def mk_adg_switch_block_group_body(node: ASTNode, adg: ADG, entry: ASTNode, exit: ASTNode) -> None:
    nodes_after_colon = [ mk_adg(node, adg) for node in get_nodes_after_colon(node)]
    combine(nodes_after_colon, adg, entry, exit)

def mk_adg_switch_case_group(node: ASTNode, adg: ADG, parent_adg_node: Optional[NodeID] = None) -> Tuple[EntryNode, ExitNode]:
    assert node.type == 'switch_block_statement_group'
    node_entry = adg.add_ast_node(ast_node=node, name='switch_case')
    node_exit = adg.add_node(name='switch_case_exit')
    
    condition = adg.add_ast_node(ast_node=get_switch_label(node), name='case_condition')
    mk_adg_switch_block_group_body(node, adg, condition, node_exit)
    adg.add_edge(condition, node_exit, syntax=True, cdep=True)
    if parent_adg_node is not None:
        adg.add_edge(parent_adg_node, node_entry, syntax=True)
    adg.add_edge(node_entry, condition, cflow=True, cdep=True)
    adg.add_edge(condition, node_exit, cflow=True)

    return node_entry, node_exit

def mk_adg_switch_default_group(node: ASTNode, adg: ADG, parent_adg_node: Optional[NodeID] = None) -> Tuple[EntryNode, ExitNode]:
    assert node.type == 'switch_block_statement_group'
    node_entry = adg.add_ast_node(ast_node=node, name='switch_default')
    node_exit = adg.add_node(name='switch_default_exit')
    if parent_adg_node is not None:
        adg.add_edge(parent_adg_node, node_entry, syntax=True)
    adg.add_edge(node_entry, node_exit, syntax=True, cdep=True)
    mk_adg_switch_block_group_body(node, adg, node_entry, node_exit)
    return node_entry, node_exit

def mk_adg_continue(
    node: ASTNode,
    adg: ADG,
    parent_adg_node: Optional[NodeID] = None,
    source: bytes = None
) -> Tuple[EntryNode, ExitNode]:
    node_entry = adg.add_ast_node(ast_node=node)
    adg.push_continue_node(node_entry)
    if parent_adg_node is not None:
        adg.add_edge(parent_adg_node, node_entry, syntax=True)
    return node_entry, node_entry


def mk_adg_break(
    node: ASTNode,
    adg: ADG,
    parent_adg_node: Optional[NodeID] = None,
    source: bytes = None
) -> Tuple[EntryNode, ExitNode]:
    node_entry = adg.add_ast_node(ast_node=node)
    adg.push_break_node(node_entry)
    if parent_adg_node is not None:
        adg.add_edge(parent_adg_node, node_entry, syntax=True)
    return node_entry, node_entry


def mk_adg_return(
    node: ASTNode,
    adg: ADG,
    parent_adg_node: Optional[NodeID] = None,
    source: bytes = None
) -> Tuple[EntryNode, ExitNode]:
    node_entry = adg.add_ast_node(ast_node=node)
    adg.push_return_node(node_entry)
    if parent_adg_node is not None:
        adg.add_edge(parent_adg_node, node_entry, syntax=True)
    return node_entry, node_entry


def mk_adg_block(node: ASTNode, adg: ADG, parent_adg_node: Optional[NodeID] = None) -> Tuple[EntryNode, ExitNode]:
    node_entry = adg.add_ast_node(ast_node=node)
    node_exit = adg.add_node(name='block-exit')
    comment_node_types = ['line_comment', 'block_comment']

    adgs: List[Tuple[EntryNode, ExitNode]] = []
    for _node in node.children:
        if not _node.is_named or _node.type in comment_node_types:
            syntax_node = adg.add_ast_node(_node)
            adg.add_edge(node_entry, syntax_node, syntax=True)
        else:
            adgs.append(mk_adg(_node, adg))

    if len(adgs) == 0:
        return node_entry, node_entry

    adg.add_edge(node_entry, node_exit, syntax=True, cdep=True)
    if parent_adg_node is not None:
        adg.add_edge(parent_adg_node, node_entry, syntax=True)
    combine(adgs, adg, node_entry, node_exit)

    # first_note_entry = adgs[0][0]
    # adg.add_edge(node_entry, first_note_entry, cflow=True)

    # for i in range(0, len(adgs)):
    #     if i < len(adgs) - 1:
    #         exit = adgs[i][-1]
    #         next_entry = adgs[i + 1][0]
    #         adg.add_edge(exit, next_entry, cflow=True)

    #     entry = adgs[i][0]
    #     adg.add_edge(node_entry, entry, syntax=True, cdep=True)

    

    # last_node_entry = adgs[-1][0]
    # last_node_exit = adgs[-1][-1]
    
    
    # adg.add_edge(last_node_exit, node_exit, cflow=True)

    # adg.add_edge(node_entry, last_node_entry, syntax=True)
    return node_entry, node_exit

def combine(entry_exit_pairs: List[Tuple[EntryNode, ExitNode]], adg: ADG, entry: NodeID, exit: NodeID) -> None:
    if len(entry_exit_pairs) == 0:
        return
    State = Tuple[ADG, NodeID, Optional[ExitNode]]
    def reduce_step(state: State, point: Tuple[EntryNode, ExitNode]) -> State:
        adg, parent, mb_last_exit = state
        next_entry, next_exit = point
        adg.add_edge(parent, next_entry, cdep=True, syntax=True)
        if mb_last_exit is not None:
            adg.add_edge(mb_last_exit, next_entry, cflow=True)
        return adg, parent, next_exit
        
    state: State = (adg, entry, None)
    _, _, last_exit = reduce(reduce_step, entry_exit_pairs, state)
    adg.add_edge(entry, entry_exit_pairs[0][0], cflow=True)
    adg.add_edge(last_exit, exit, cflow=True)
    return 

def mk_variable_declaration(
    node: Optional[ASTNode],
    adg: ADG,
    parent_adg_node: Optional[NodeID] = None
) -> Tuple[EntryNode, ExitNode]:
    node_id = adg.add_ast_node(ast_node=node, var_decl=True)
    if parent_adg_node is not None:
        adg.add_edge(parent_adg_node, node_id, syntax=True)

    return node_id, node_id


def mk_default(node: Optional[ASTNode], adg: ADG, parent_adg_node: Optional[NodeID] = None) -> Tuple[EntryNode, ExitNode]:
    node_id = adg.add_ast_node(ast_node=node)
    if parent_adg_node is not None:
        adg.add_edge(parent_adg_node, node_id, syntax=True)
    return node_id, node_id
