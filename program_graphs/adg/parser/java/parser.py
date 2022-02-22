from typing import Optional, Tuple, List
import os
from program_graphs.adg.adg import ADG, mk_empty_adg
from program_graphs.adg.parser.java.data_dependency import add_data_dependency_layer
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.utils import get_project_root
from program_graphs.types import NodeID, ASTNode


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

    if node.type == 'if_statement':
        return mk_adg_if(node, adg, parent_adg_node)

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

    # print(node.child_by_field_name('dimensions'))
    # print(node.child_by_field_name('type'))
    # print(node.child_by_field_name('value'))
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
    # TODO: add comment nodes with only syntax dependency
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

    first_note_entry = adgs[0][0]
    adg.add_edge(node_entry, first_note_entry, cflow=True)

    for i in range(0, len(adgs)):
        if i < len(adgs) - 1:
            exit = adgs[i][-1]
            next_entry = adgs[i + 1][0]
            adg.add_edge(exit, next_entry, cflow=True)

        entry = adgs[i][0]
        adg.add_edge(node_entry, entry, syntax=True, cdep=True)

    if parent_adg_node is not None:
        adg.add_edge(parent_adg_node, node_entry, syntax=True)

    # last_node_entry = adgs[-1][0]
    last_node_exit = adgs[-1][-1]
    node_exit = adg.add_node(name='block-exit')
    adg.add_edge(node_entry, node_exit, syntax=True, cdep=True)
    adg.add_edge(last_node_exit, node_exit, cflow=True)

    # adg.add_edge(node_entry, last_node_entry, syntax=True)
    return node_entry, node_exit


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
