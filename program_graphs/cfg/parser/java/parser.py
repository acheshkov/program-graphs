import os
from typing import Any, List, Optional
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.cfg import CFG
from program_graphs.cfg.operators import mk_empty_cfg, combine
from program_graphs.cfg.operators import manage_jumps, eliminate_redundant_nodes
from program_graphs.cfg.parser.java.utils import get_identifier, get_nodes_after_colon
from program_graphs.cfg.parser.java.switch_stmt import get_switch_block_label, get_switch_label
from program_graphs.cfg.types import Node, JumpKind, Label
from program_graphs.cfg.parser.java.break_stmt import mk_cfg_break
from program_graphs.cfg.parser.java.continue_stmt import mk_cfg_continue
from program_graphs.cfg.parser.java.return_stmt import mk_cfg_return
from program_graphs.utils import get_project_root


def parse(source_code: str) -> CFG:
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
    return mk_cfg(ast.root_node, source=source_code_bytes)


# flake8: noqa: C901
def mk_cfg(node: Optional[Node], **kwargs: Any) -> CFG:
    if node is None:
        return mk_empty_cfg()

    if node.type == 'for_statement':
        return mk_cfg_for(node, **kwargs)

    if node.type == 'while_statement':
        return mk_cfg_while(node, **kwargs)

    if node.type == 'do_statement':
        return mk_cfg_do_while(node, **kwargs)

    if node.type == 'block':
        return mk_cfg_block(node, **kwargs)

    if node.type == 'program':
        return mk_cfg_block(node, **kwargs)

    if node.type == 'if_statement':
        return mk_cfg_if(node, **kwargs)

    if node.type == 'continue_statement':
        return mk_cfg_continue(node, **kwargs)

    if node.type == 'break_statement':
        return mk_cfg_break(node, **kwargs)

    if node.type == 'return_statement':
        return mk_cfg_return(node)

    if node.type == 'switch_expression':
        return mk_cfg_switch(node, **kwargs)

    if node.type == 'labeled_statement':
        return mk_cfg_labeled_statement(node, **kwargs)

    if node.type == 'method_declaration':
        return mk_cfg_method_declaration(node, **kwargs)

    if node.type == 'try_statement':
        return mk_cfg_try_catch(node, **kwargs)

    if node.type == 'synchronized_statement':
        return mk_cfg_synchronized(node, **kwargs)

    cfg = CFG()
    cfg.add_node([node], 'statement')
    return cfg


def mk_cfg_of_list_of_nodes(nodes: List[Node], **kwargs: Any) -> CFG:
    return combine_list([
        mk_cfg(n, **kwargs) for n in nodes if n.is_named
    ])


def combine_list(cfgs: List[CFG]) -> CFG:
    cfg = mk_empty_cfg()
    for _cfg in cfgs:
        cfg = combine(cfg, _cfg)
    return cfg


def mk_cfg_block(node: Node, **kwargs: Any) -> CFG:
    cfg = mk_cfg_of_list_of_nodes(node.children, **kwargs)
    manage_jumps(cfg)
    return eliminate_redundant_nodes(cfg)


def mk_cfg_for(node: Node, label: Label = None, source: bytes = None) -> CFG:
    init = mk_cfg(node.child_by_field_name('init'))
    condition = mk_cfg(node.child_by_field_name('condition'))
    body = mk_cfg(node.child_by_field_name('body'), source=source)
    update = mk_cfg(node.child_by_field_name('update'))
    exit = mk_empty_cfg()

    condition_id = condition.assign_id(condition.entry_node())
    update_id = update.assign_id(update.exit_node())
    exit_id = exit.assign_id(exit.entry_node())
    cfg = combine(init, condition)
    cfg = combine(cfg, body)
    cfg = combine(cfg, update)
    cfg = combine(cfg, exit, cfg.find_node_by_id(condition_id))
    cfg.add_edge(cfg.find_node_by_id(update_id), cfg.find_node_by_id(condition_id))

    cfg.add_possible_jump(cfg.find_node_by_id(update_id), None, JumpKind.CONTINUE)
    cfg.add_possible_jump(cfg.find_node_by_id(exit_id), None, JumpKind.BREAK)
    if label is not None:
        cfg.add_possible_jump(cfg.find_node_by_id(update_id), label, JumpKind.CONTINUE)

    cfg.set_node_name(cfg.find_node_by_id(update_id), 'for-update')
    cfg.set_node_name(cfg.find_node_by_id(condition_id), 'for-condition')
    cfg.set_node_name(cfg.entry_node(), 'for-init')
    cfg.set_node_name(cfg.find_node_by_id(exit_id), 'exit')

    manage_jumps(cfg)
    cfg = eliminate_redundant_nodes(cfg)
    return cfg


def mk_cfg_if(node: Node, **kwargs: Any) -> CFG:
    if node.child_by_field_name('alternative') is not None:
        return mk_cfg_if_else(node, **kwargs)

    condition = mk_cfg(node.child_by_field_name('condition'))
    consequence = mk_cfg(node.child_by_field_name('consequence'), **kwargs)
    exit = mk_empty_cfg()
    assert len(consequence.entry_nodes()) == 1

    condition_id = condition.assign_id(condition.exit_node())
    exit_id = exit.assign_id(exit.entry_node())
    cfg = combine(condition, consequence)
    cfg = combine(cfg, exit)
    cfg.add_edge(cfg.find_node_by_id(condition_id), cfg.find_node_by_id(exit_id))
    cfg.set_node_name(cfg.entry_node(), 'if-condition')
    cfg.set_node_name(cfg.find_node_by_id(exit_id), 'exit')
    cfg = eliminate_redundant_nodes(cfg)
    return cfg


def mk_cfg_if_else(node: Node, **kwargs: Any) -> CFG:
    condition = mk_cfg(node.child_by_field_name('condition'))
    consequence = mk_cfg(node.child_by_field_name('consequence'), **kwargs)
    alternative = mk_cfg(node.child_by_field_name('alternative'), **kwargs)
    exit = mk_empty_cfg()
    assert len(consequence.entry_nodes()) == 1

    condition_id = condition.assign_id(condition.exit_node())
    alternative_id = alternative.assign_id(alternative.exit_node())
    exit_id = exit.assign_id(exit.entry_node())
    cfg = combine(condition, consequence)
    cfg = combine(cfg, exit)
    cfg = combine(cfg, alternative, cfg.find_node_by_id(condition_id))
    cfg.add_edge(cfg.find_node_by_id(alternative_id), cfg.find_node_by_id(exit_id))

    cfg.set_node_name(cfg.entry_node(), 'if-condition')
    cfg.set_node_name(cfg.find_node_by_id(exit_id), 'exit')
    cfg = eliminate_redundant_nodes(cfg)
    return cfg


def get_cfg_switch_block_group_body(node: Node, **kwargs: Any) -> CFG:
    nodes_after_colon = get_nodes_after_colon(node)
    return mk_cfg_of_list_of_nodes(nodes_after_colon, **kwargs)


def mk_cfg_switch_case_group(node: Node, **kwargs: Any) -> CFG:
    assert node.type == 'switch_block_statement_group'
    condition = CFG([get_switch_label(node)])
    body = get_cfg_switch_block_group_body(node, **kwargs)
    exit = mk_empty_cfg()

    condition_id = condition.assign_id(condition.exit_node())
    exit_id = exit.assign_id(exit.entry_node())
    cfg = combine(condition, body)
    cfg = combine(cfg, exit)
    cfg.add_edge(cfg.find_node_by_id(condition_id), cfg.find_node_by_id(exit_id))
    cfg.set_node_name(cfg.entry_node(), 'case')
    cfg.set_node_name(cfg.exit_node(), 'exit')
    cfg = eliminate_redundant_nodes(cfg)
    return cfg


def mk_cfg_switch_default_group(node: Node, **kwargs: Any) -> CFG:
    assert node.type == 'switch_block_statement_group'
    body = get_cfg_switch_block_group_body(node, **kwargs)
    exit = mk_empty_cfg()
    cfg = combine(body, exit)
    cfg.set_node_name(cfg.entry_node(), 'default')
    cfg.set_node_name(cfg.exit_node(), 'exit')
    cfg = eliminate_redundant_nodes(cfg)
    return cfg


def mk_cfg_switch(node: Node, **kwargs: Any) -> CFG:
    groups = [n for n in node.child_by_field_name('body').children if n.type == 'switch_block_statement_group']
    default_groups = [g for g in groups if get_switch_block_label(g) == 'default']
    case_groups = [g for g in groups if get_switch_block_label(g) == 'case']
    case_groups_cfg = combine_list([mk_cfg_switch_case_group(g, **kwargs) for g in case_groups])
    default_group_cfg = combine_list([mk_cfg_switch_default_group(g, **kwargs) for g in default_groups])

    cfg = combine(case_groups_cfg, default_group_cfg)
    cfg = combine(cfg, mk_empty_cfg())
    cfg.add_possible_jump(cfg.exit_node(), None, JumpKind.BREAK)
    manage_jumps(cfg)
    cfg = eliminate_redundant_nodes(cfg)
    return cfg


def mk_cfg_labeled_statement(node: Node, **kwargs: Any) -> CFG:
    assert node.type == 'labeled_statement'
    assert kwargs['source'] is not None
    cfg = CFG()

    identifier = get_identifier(node, **kwargs)
    nodes_after_colon = get_nodes_after_colon(node)
    cfg = mk_cfg(nodes_after_colon[0], label=identifier, **kwargs)
    cfg.add_possible_jump(cfg.exit_node(), identifier, JumpKind.BREAK)
    manage_jumps(cfg)
    cfg = eliminate_redundant_nodes(cfg)
    return cfg


def mk_cfg_while(node: Node, label: Label = None, source: bytes = None) -> CFG:
    start = mk_empty_cfg()
    condition = mk_cfg(node.child_by_field_name('condition'))
    body = mk_cfg(node.child_by_field_name('body'), source=source)
    exit = mk_empty_cfg()

    condition_id = condition.assign_id(condition.entry_node())
    body_id = body.assign_id(body.exit_node())
    exit_id = exit.assign_id(exit.entry_node())
    
    cfg = combine(start, condition)
    cfg = combine(cfg, body)
    cfg = combine(cfg, exit, cfg.find_node_by_id(condition_id))
    cfg.add_edge(cfg.find_node_by_id(body_id), cfg.find_node_by_id(condition_id))

    cfg.add_possible_jump(cfg.find_node_by_id(condition_id), None, JumpKind.CONTINUE)
    cfg.add_possible_jump(cfg.find_node_by_id(exit_id), None, JumpKind.BREAK)
    if label is not None:
        cfg.add_possible_jump(cfg.find_node_by_id(condition_id), label, JumpKind.CONTINUE)

    cfg.set_node_name(cfg.find_node_by_id(condition_id), 'while-condition')
    cfg.set_node_name(cfg.find_node_by_id(exit_id), 'exit')

    manage_jumps(cfg)
    cfg = eliminate_redundant_nodes(cfg)
    return cfg

def mk_cfg_do_while(node: Node, label: Label = None, source: bytes = None) -> CFG:
    start = mk_empty_cfg()
    condition = mk_cfg(node.child_by_field_name('condition'))
    body = mk_cfg(node.child_by_field_name('body'), source=source)
    exit = mk_empty_cfg()

    condition_id = condition.assign_id(condition.exit_node())
    body_id = body.assign_id(body.entry_node())
    exit_id = exit.assign_id(exit.entry_node())
    
    cfg = combine(start, body)
    cfg = combine(cfg, condition)
    cfg = combine(cfg, exit)
    cfg.add_edge(cfg.find_node_by_id(condition_id), cfg.find_node_by_id(body_id))
    cfg.add_possible_jump(cfg.find_node_by_id(condition_id), None, JumpKind.CONTINUE)
    cfg.add_possible_jump(cfg.find_node_by_id(exit_id), None, JumpKind.BREAK)
    if label is not None:
        cfg.add_possible_jump(cfg.find_node_by_id(condition_id), label, JumpKind.CONTINUE)

    cfg.set_node_name(cfg.find_node_by_id(condition_id), 'do-condition')
    cfg.set_node_name(cfg.find_node_by_id(exit_id), 'exit')

    manage_jumps(cfg)
    cfg = eliminate_redundant_nodes(cfg)
    return cfg

def mk_cfg_method_declaration(node: Node, label: Label = None, source: bytes = None) -> CFG:
    body = mk_cfg(node.child_by_field_name('body'), source=source)
    formal_params = mk_cfg_of_list_of_nodes(
        [n for n in node.child_by_field_name('parameters').children if n.type == 'formal_parameter'],
        source=source,
        bytes=bytes
    )
    cfg = combine(formal_params, body)
    cfg = eliminate_redundant_nodes(cfg)
    return cfg

def mk_cfg_try_catch(node: Node, **kwargs: Any) -> CFG:
    try_body = mk_cfg(node.child_by_field_name('body'), **kwargs)
    catch_node = [ch for ch in node.children if ch.type == 'catch_clause'][0]
    catch = mk_cfg(catch_node.child_by_field_name('body'), **kwargs)
    final_nodes = [ch for ch in node.children if ch.type == 'finally_clause']
    if len(final_nodes) > 0:
        final_body_node =  [ch for ch in final_nodes[0].children if ch.type == 'block'][0]
        final = mk_cfg(final_body_node, **kwargs)
    else:
        final = mk_empty_cfg()
    try_id = try_body.assign_id(try_body.exit_node())
    final_id = final.assign_id(final.entry_node())
    cfg = combine(try_body, catch)
    cfg = combine(cfg, final)
    cfg.add_edge(cfg.find_node_by_id(try_id), cfg.find_node_by_id(final_id))
    # cfg.set_node_name(cfg.entry_node(), 'if-condition')
    # cfg.set_node_name(cfg.find_node_by_id(exit_id), 'exit')
    cfg = eliminate_redundant_nodes(cfg)
    return cfg

def mk_cfg_synchronized(node: Node, **kwargs: Any) -> CFG:
    return mk_cfg(node.child_by_field_name('body'), **kwargs)
