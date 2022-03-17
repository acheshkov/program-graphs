from typing import Optional, Tuple, List
import os
from program_graphs.adg.adg import ADG, mk_empty_adg
from program_graphs.adg.parser.java.data_dependency import add_data_dependency_layer
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.utils import get_project_root
from program_graphs.types import NodeID, ASTNode
from functools import reduce
from program_graphs.utils.graph import filter_nodes
from program_graphs.adg.parser.java.utils import get_switch_block_label, get_switch_label, get_nodes_after_colon, get_identifier


def parse_ast_tree_sitter(source_code: str) -> ASTNode:
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
    return ast.root_node

def parse(source_code: str) -> ADG:
    ast = parse_ast_tree_sitter(source_code)
    source_code_bytes = bytes(source_code, 'utf-8')
    return parse_from_ast(ast, source_code_bytes)


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
        return mk_adg_block(node, adg, parent_adg_node, source)

    if node.type == 'class_declaration':
        methods = filter_nodes(node, ['method_declaration'])
        return mk_adg(methods[0], adg, parent_adg_node, source)

    if node.type == 'method_declaration':
        return mk_adg_method_declaration(node, adg, parent_adg_node, source)

    if node.type == 'block':
        return mk_adg_block(node, adg, parent_adg_node, source)

    if node.type == 'enhanced_for_statement':
        return mk_adg_enhanced_for(node, adg, parent_adg_node, source)

    if node.type == 'for_statement':
        return mk_adg_for(node, adg, parent_adg_node, source)

    if node.type == 'while_statement':
        return mk_adg_while(node, adg, parent_adg_node, source)

    if node.type == 'do_statement':
        return mk_adg_do_while(node, adg, parent_adg_node, source)

    if node.type == 'if_statement':
        return mk_adg_if(node, adg, parent_adg_node, source)

    if node.type == 'switch_expression':
        return mk_adg_switch(node, adg, parent_adg_node, source)

    if node.type == 'continue_statement':
        return mk_adg_continue(node, adg, parent_adg_node, source)

    if node.type == 'break_statement':
        return mk_adg_break(node, adg, parent_adg_node, source)

    if node.type == 'return_statement':
        return mk_adg_return(node, adg, parent_adg_node)
    
    if node.type in ['try_statement', 'try_with_resources_statement']:
        return mk_adg_try_catch(node, adg, parent_adg_node, source)

    if node.type == 'local_variable_declaration':
        return mk_variable_declaration(node, adg, parent_adg_node)

    if node.type == 'labeled_statement':
        return mk_adg_labeled_statement(node, adg, parent_adg_node, source)

    return mk_default(node, adg, parent_adg_node)


def mk_adg_method_declaration(node: ASTNode, adg: ADG, parent_adg_node: Optional[NodeID] = None, source: bytes = None) -> Tuple[EntryNode, ExitNode]:
    node_method_entry = adg.add_ast_node(ast_node=node)
    node_method_exit = adg.add_node(name='method_exit')
    formal_parameters = [n for n in node.child_by_field_name('parameters').children if n.type == 'formal_parameter']
    params_and_body= [mk_adg(n, adg) for n in formal_parameters] + [mk_adg(node.child_by_field_name('body'), adg, source=source)]
    entry, exit = combine_cf_linear(params_and_body, adg, node_method_entry)
    adg.add_edge(node_method_entry, entry, cflow=True)
    adg.add_edge(exit, node_method_exit, cflow=True)
    adg.add_edge(node_method_entry, node_method_exit, syntax=True, exit=True)
    if parent_adg_node is not None:
        adg.add_edge(parent_adg_node, node_method_entry, syntax=True)
    return node_method_entry, node_method_exit


def mk_adg_enhanced_for(node: ASTNode, adg: ADG, parent_adg_node: Optional[NodeID] = None, source: bytes = None) -> Tuple[EntryNode, ExitNode]:
    ast_node_body = node.child_by_field_name('body')
    if ast_node_body.type == ';':
        return mk_default(node, adg, parent_adg_node, name='for_enhanced')

    node_for_entry = adg.add_ast_node(ast_node=node, name='for_enhanced')
    node_for_exit = adg.add_node(name='for_exit')
    node_body_entry, node_body_exit = mk_adg(ast_node_body, adg, source=source)
    if parent_adg_node is not None:
        adg.add_edge(parent_adg_node, node_for_entry, syntax=True)

    adg.add_edge(node_for_entry, node_body_entry, syntax=True, cdep=True, cflow=True)
    adg.add_edge(node_for_entry, node_for_exit, syntax=True, cdep=True, cflow=True, exit=True)
    adg.add_edge(node_body_exit, node_for_entry, cflow=True)

    adg.rewire_continue_nodes(node_for_entry)
    adg.rewire_break_nodes(node_for_exit)

    return node_for_entry, node_for_exit


def mk_adg_for(node: ASTNode, adg: ADG, parent_adg_node: Optional[NodeID] = None, source: bytes = None) -> Tuple[EntryNode, ExitNode]:
    node_for_entry = adg.add_ast_node(ast_node=node, name='for')
    node_init = adg.add_ast_node(ast_node=node.child_by_field_name('init'), name='for_init')
    node_condition = adg.add_ast_node(ast_node=node.child_by_field_name('condition'), name='for_condition')
    node_body_entry, node_body_exit = mk_adg(node.child_by_field_name('body'), adg, source=source)
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
    # adg.add_edge(node_condition, node_update, cdep=True)

    adg.rewire_continue_nodes(node_update)
    adg.rewire_break_nodes(node_for_exit)


    return node_for_entry, node_for_exit


def mk_adg_while(
    node: ASTNode, adg: ADG,
    parent_adg_node: Optional[NodeID] = None,
    source: bytes=None
) -> Tuple[EntryNode, ExitNode]:
    node_while_entry = adg.add_ast_node(ast_node=node, name='while')
    node_condition = adg.add_ast_node(ast_node=node.child_by_field_name('condition'), name='while_condition')
    node_body_entry, node_body_exit = mk_adg(node.child_by_field_name('body'), adg, source=source)
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


    adg.rewire_continue_nodes(node_condition)
    adg.rewire_break_nodes(node_while_exit)
    # while continue_node := adg.pop_continue_node():
    #     adg.remove_edges_from([e for e in adg.out_edges(continue_node)])
    #     adg.add_edge(continue_node, node_condition, cflow=True)

    # while break_node := adg.pop_break_node():
    #     adg.remove_edges_from([e for e in adg.out_edges(break_node)])
    #     adg.add_edge(break_node, node_while_exit, cflow=True)

    # break_nodes = list(adg._break_nodes.keys())
    # for node in break_nodes:
    #     if adg._break_nodes[node] is not None:
    #         continue
    #     adg.remove_edges_from([e for e in adg.out_edges(node)])
    #     adg.add_edge(node, node_while_exit, cflow=True)
    #     del adg._break_nodes[node]

    return node_while_entry, node_while_exit


def mk_adg_do_while(
    node: ASTNode, adg: ADG,
    parent_adg_node: Optional[NodeID] = None,
    source: bytes = None
) -> Tuple[EntryNode, ExitNode]:
    node_while_entry = adg.add_ast_node(ast_node=node, name='do_while')
    node_condition = adg.add_ast_node(ast_node=node.child_by_field_name('condition'), name='do_condition')
    node_body_entry, node_body_exit = mk_adg(node.child_by_field_name('body'), adg, source=source)
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


    adg.rewire_continue_nodes(node_condition)
    adg.rewire_break_nodes(node_while_exit)
    return node_while_entry, node_while_exit


def mk_adg_if(
    node: ASTNode, adg: ADG, parent_adg_node: Optional[NodeID] = None,
    source: bytes=None
) -> Tuple[EntryNode, ExitNode]:
    node_if_entry = adg.add_ast_node(ast_node=node, name='if')
    node_condition = adg.add_ast_node(ast_node=node.child_by_field_name('condition'), name='if_condition')
    node_body_entry, node_body_exit = mk_adg(node.child_by_field_name('consequence'), adg, source=source)
    node_if_exit = adg.add_node(name='if_exit')

    if parent_adg_node is not None:
        adg.add_edge(parent_adg_node, node_if_entry, syntax=True)

    adg.add_edge(node_if_entry, node_condition, syntax=True, cflow=True, cdep=True)
    adg.add_edge(node_if_entry, node_body_entry, syntax=True)
    adg.add_edge(node_condition, node_body_entry, cflow=True, cdep=True)
    adg.add_edge(node_if_entry, node_if_exit, syntax=True, cdep=True, exit=True)

    adg.add_edge(node_body_exit, node_if_exit, cflow=True)

    if node.child_by_field_name('alternative') is not None:
        node_else_entry, node_else_exit = mk_adg(node.child_by_field_name('alternative'), adg, source=source)
        adg.add_edge(node_if_entry, node_else_entry, syntax=True)
        adg.add_edge(node_condition, node_else_entry, cflow=True, cdep=True)
        adg.add_edge(node_else_exit, node_if_exit, cflow=True)
    else:
        adg.add_edge(node_condition, node_if_exit, cflow=True)

    return node_if_entry, node_if_exit


def mk_adg_switch(node: ASTNode, adg: ADG, parent_adg_node: Optional[NodeID] = None, source: bytes=None) -> Tuple[EntryNode, ExitNode]:
    node_switch_entry = adg.add_ast_node(ast_node=node, name='switch')
    node_switch_exit = adg.add_node(name='switch_exit')
    node_condition = adg.add_ast_node(ast_node=node.child_by_field_name('condition'), name='switch_condition')
    # TODO: add not named syntax nodes { }

    for _node in node.child_by_field_name('body').children:
        if not _node.is_named or _node.type in ['line_comment', 'block_comment']:
            syntax_node = adg.add_ast_node(_node)
            adg.add_edge(node_switch_entry, syntax_node, syntax=True)

    groups: List[ASTNode] = [n for n in node.child_by_field_name('body').children if n.type == 'switch_block_statement_group']
    case_groups = [mk_adg_switch_case_group(g, adg) for g in groups if get_switch_block_label(g) == 'case']
    default_groups = [mk_adg_switch_default_group(g, adg) for g in groups if get_switch_block_label(g) == 'default']
    block_entry, block_exit = combine_cf_linear(case_groups + default_groups, adg, node_switch_entry)
    adg.add_edge(node_switch_entry, node_condition, cflow=True, syntax=True)
    adg.add_edge(node_condition, block_entry, cflow=True)
    adg.add_edge(block_exit, node_switch_exit, cflow=True)
    # adg.add_edge(node_condition, node_switch_exit, cflow=True)
    adg.add_edge(node_switch_entry, node_switch_exit, syntax=True, exit=True)
    if parent_adg_node is not None:
        adg.add_edge(parent_adg_node, node_switch_entry, syntax=True)
    return node_switch_entry, node_switch_exit

def mk_adg_switch_block_group_body(node: ASTNode, adg: ADG, syntax_parent: ASTNode, source: bytes = None) -> Tuple[EntryNode, ExitNode]:
    nodes_after_colon = [mk_adg(node, adg, source=source) for node in get_nodes_after_colon(node)]
    if len(nodes_after_colon) == 0:
        node = adg.add_node(name='empty-case')
        return node, node
    return combine_cf_linear(nodes_after_colon, adg, syntax_parent)

def mk_adg_switch_case_group(node: ASTNode, adg: ADG, parent_adg_node: Optional[NodeID] = None, source: bytes = None) -> Tuple[EntryNode, ExitNode]:
    assert node.type == 'switch_block_statement_group'
    node_entry = adg.add_ast_node(ast_node=node, name='switch_case')
    node_exit = adg.add_node(name='switch_case_exit')
    
    condition = adg.add_ast_node(ast_node=get_switch_label(node), name='case_condition')
    case_entry, case_exit = mk_adg_switch_block_group_body(node, adg, node_entry)
    adg.add_edges_from([
        (node_entry, condition),
        (condition, case_entry),
        (case_exit, node_exit),
        (condition, node_exit)
    ], cflow=True)
    adg.add_edge(node_entry, condition, syntax=True)
    adg.add_edge(node_entry, node_exit, syntax=True, exit=True)
    adg.rewire_break_nodes(node_exit)
    if parent_adg_node is not None:
        adg.add_edge(parent_adg_node, node_entry, syntax=True)
    return node_entry, node_exit

def mk_adg_switch_default_group(node: ASTNode, adg: ADG, parent_adg_node: Optional[NodeID] = None, source: bytes = None) -> Tuple[EntryNode, ExitNode]:
    assert node.type == 'switch_block_statement_group'
    node_entry = adg.add_ast_node(ast_node=node, name='switch_default')
    node_exit = adg.add_node(name='switch_default_exit')
    
    case_entry, case_exit = mk_adg_switch_block_group_body(node, adg, node_entry)
    adg.add_edge(node_entry, node_exit, syntax=True, exit=True)
    adg.add_edge(node_entry, case_entry, cflow=True)
    adg.add_edge(case_exit, node_exit, cflow=True)
    adg.rewire_break_nodes(node_exit)
    if parent_adg_node is not None:
        adg.add_edge(parent_adg_node, node_entry, syntax=True)
    return node_entry, node_exit

def find_continue_target_node(adg: ADG, node: NodeID, ast_node_type: str) -> Optional[NodeID]:
    if ast_node_type == 'for_statement':
        return next((s for s in adg.successors(node) if adg.nodes[s].get('name') == 'for_update'), None)
    if ast_node_type == 'while_statement':
        return next((s for s in adg.successors(node) if adg.nodes[s].get('name') == 'while_condition'), None)
    if ast_node_type == 'do_statement':
        return next((s for s in adg.successors(node) if adg.nodes[s].get('name') == 'do_condition'), None)
    if ast_node_type == 'enhanced_for_statement':
        return node
    return None


def mk_adg_labeled_statement(node: ASTNode, adg: ADG, parent_adg_node: Optional[NodeID] = None, source: bytes = None) -> Tuple[EntryNode, ExitNode]:
    assert node.type == 'labeled_statement'
    assert source is not None

    label = get_identifier(node, source)
    labeled_statement: ASTNode = get_nodes_after_colon(node)[0]
    entry, exit = mk_adg(labeled_statement, adg, parent_adg_node, source)

    continue_target = find_continue_target_node(adg, entry, labeled_statement.type)
    if continue_target is not None:
        adg.rewire_continue_nodes(continue_target, label)
    adg.rewire_break_nodes(exit, label)
    return entry, exit

def mk_adg_continue(
    node: ASTNode,
    adg: ADG,
    parent_adg_node: Optional[NodeID] = None,
    source: bytes = None
) -> Tuple[EntryNode, ExitNode]:
    maybe_label = get_identifier(node, source)
    node_entry = adg.add_ast_node(ast_node=node)
    adg.push_continue_node(node_entry, maybe_label)
    if parent_adg_node is not None:
        adg.add_edge(parent_adg_node, node_entry, syntax=True)
    return node_entry, node_entry


def mk_adg_break(
    node: ASTNode,
    adg: ADG,
    parent_adg_node: Optional[NodeID] = None,
    source: bytes = None
) -> Tuple[EntryNode, ExitNode]:
    maybe_label = get_identifier(node, source)
    node_entry = adg.add_ast_node(ast_node=node)
    adg.push_break_node(node_entry, maybe_label)
    if parent_adg_node is not None:
        adg.add_edge(parent_adg_node, node_entry, syntax=True)
    return node_entry, node_entry


def mk_adg_return(
    node: ASTNode,
    adg: ADG,
    parent_adg_node: Optional[NodeID] = None
) -> Tuple[EntryNode, ExitNode]:
    node_entry = adg.add_ast_node(ast_node=node, name='return')
    adg.push_return_node(node_entry)
    if parent_adg_node is not None:
        adg.add_edge(parent_adg_node, node_entry, syntax=True)
    return node_entry, node_entry


def mk_adg_finally_block(node: ASTNode, adg: ADG, syntax_parent: NodeID, source: bytes = None) -> Tuple[Optional[EntryNode], Optional[ExitNode]]:
    final_node = next((ch for ch in node.children if ch.type == 'finally_clause'), None)
    if final_node is None:
        return None, None
    final_body_node = [ch for ch in final_node.children if ch.type == 'block'][0]
    return mk_adg(final_body_node, adg, syntax_parent, source)

def mk_adg_single_catch_block(node: ASTNode, adg: ADG, source: bytes = None) -> Tuple[EntryNode, ExitNode]:
    case_node_entry = adg.add_ast_node(node, name='catch-block')
    entry, exit = combine_cf_linear([
        mk_adg(filter_nodes(node, ['catch_formal_parameter'])[0], adg, source=source),
        mk_adg(node.child_by_field_name('body'), adg, source=source)
    ], adg, case_node_entry)
    adg.add_edge(case_node_entry, entry, cflow=True)
    adg.add_edge(entry, exit, cflow=True)
    return case_node_entry, exit

def mk_adg_many_catch_blocks(node: ASTNode, adg: ADG, syntax_parent: NodeID, source: bytes = None) -> Tuple[Optional[EntryNode], Optional[ExitNode]]:
    catch_nodes = [ch for ch in node.children if ch.type == 'catch_clause']
    catches = [mk_adg_single_catch_block(node, adg, source) for node in catch_nodes]
    if len(catches) == 0:
        return None, None
    return combine_cf_linear(catches, adg, syntax_parent)

def mk_adg_try_block(node: ASTNode, adg: ADG, syntax_parent: NodeID, source: bytes = None) -> Tuple[Optional[EntryNode], Optional[ExitNode]]:
    resources = filter_nodes(node.child_by_field_name('resources'), ['resource'])
    if len(resources) == 0:
        return mk_adg(node.child_by_field_name('body'), adg, syntax_parent, source=source)
    
    resources_entry, resources_exit = combine_cf_linear([mk_adg(r, adg, source=source) for r in resources], adg, syntax_parent)
    try_entry, try_exit = mk_adg(node.child_by_field_name('body'), adg, syntax_parent, source)
    adg.add_edge(resources_exit, try_entry, cflow=True)
    return resources_entry, try_exit
    
  

def mk_adg_try_catch(node: ASTNode, adg: ADG, parent_adg_node: Optional[NodeID] = None, source: bytes = None) -> Tuple[EntryNode, ExitNode]:
    try_catch_node = adg.add_ast_node(node, name='try_catch')
    try_entry, try_exit = mk_adg_try_block(node, adg, try_catch_node, source)
    mb_final_entry, mb_final_exit = mk_adg_finally_block(node, adg, try_catch_node, source)
    mb_catches_entry, mb_catches_exit = mk_adg_many_catch_blocks(node, adg, try_catch_node, source)

    adg.add_edge(try_catch_node, try_entry, cflow=True)
    if parent_adg_node is not None:
        adg.add_edge(parent_adg_node, try_catch_node, syntax=True)

    if mb_final_entry is None and mb_catches_exit is None:
        return try_catch_node, try_exit  # type: ignore

    if mb_catches_entry is not None and mb_final_entry is None:
        # adg.add_edge(parent_adg_node, mb_catches_entry, syntax=True)
        adg.add_edge(try_entry, mb_catches_entry, cflow=True)
        adg.add_edge(try_exit, mb_catches_entry, cflow=True)
        return try_catch_node, mb_catches_exit  # type: ignore

    if mb_catches_entry is None and mb_final_entry is not None:
        adg.add_edge(try_exit, mb_final_entry, cflow=True)
        return try_catch_node, mb_final_exit  # type: ignore

    adg.add_edges_from([
        (try_entry, mb_catches_entry),
        (try_exit, mb_catches_entry),
        (try_entry, mb_final_entry),
        (mb_catches_exit, mb_final_entry)
    ], cflow=True)

    return try_catch_node, mb_final_exit  # type: ignore


def mk_adg_block(node: ASTNode, adg: ADG, parent_adg_node: Optional[NodeID] = None, source: bytes = None) -> Tuple[EntryNode, ExitNode]:
    node_entry = adg.add_ast_node(ast_node=node)
    node_exit = adg.add_node(name='block-exit')
    comment_node_types = ['line_comment', 'block_comment']

    adgs: List[Tuple[EntryNode, ExitNode]] = []
    for _node in node.children:
        if not _node.is_named or _node.type in comment_node_types:
            syntax_node = adg.add_ast_node(_node)
            adg.add_edge(node_entry, syntax_node, syntax=True)
        else:
            adgs.append(mk_adg(_node, adg, source=source))

    if len(adgs) == 0:
        return node_entry, node_entry

    adg.add_edge(node_entry, node_exit, syntax=True, cdep=True, exit=True)
    if parent_adg_node is not None:
        adg.add_edge(parent_adg_node, node_entry, syntax=True)
    entry, exit = combine_cf_linear(adgs, adg, node_entry)
    adg.add_edge(node_entry, entry, syntax=True, cflow=True)
    adg.add_edge(exit, node_exit, cflow=True)
    
    return node_entry, node_exit

def combine_cf_linear(entry_exit_pairs: List[Tuple[EntryNode, ExitNode]], adg: ADG, syntax_parent: Optional[NodeID]) -> Tuple[EntryNode, ExitNode]:
    if len(entry_exit_pairs) == 0:
        raise ValueError()
    State = Tuple[ADG, Optional[NodeID], Optional[EntryNode], Optional[ExitNode]]
    def reduce_step(state: State, point: Tuple[EntryNode, ExitNode]) -> State:
        adg, mb_parent_syntax_node, mb_first_exit, mb_last_exit = state
        next_entry, next_exit = point
        mb_first_exit = mb_first_exit or next_entry
        if mb_parent_syntax_node is not None:
            adg.add_edge(mb_parent_syntax_node, next_entry, syntax=True)
        if mb_last_exit is not None:
            adg.add_edge(mb_last_exit, next_entry, cflow=True)
        return adg, mb_parent_syntax_node, mb_first_exit, next_exit
        
    state: State = (adg, syntax_parent, None, None)
    _, _, first_entry, latest_exit = reduce(reduce_step, entry_exit_pairs, state)
    return first_entry, latest_exit  # type: ignore

def mk_variable_declaration(
    node: Optional[ASTNode],
    adg: ADG,
    parent_adg_node: Optional[NodeID] = None
) -> Tuple[EntryNode, ExitNode]:
    node_id = adg.add_ast_node(ast_node=node, var_decl=True)
    if parent_adg_node is not None:
        adg.add_edge(parent_adg_node, node_id, syntax=True)

    return node_id, node_id


def mk_default(
    node: Optional[ASTNode],
    adg: ADG,
    parent_adg_node: Optional[NodeID] = None,
    name: Optional[str] = None
) -> Tuple[EntryNode, ExitNode]:
    node_id = adg.add_ast_node(ast_node=node, name=name)
    if parent_adg_node is not None:
        adg.add_edge(parent_adg_node, node_id, syntax=True)
    return node_id, node_id
