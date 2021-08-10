from typing import Any, List
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.cfg import CFG
from program_graphs.cfg.operators import mk_empty_cfg, combine, merge_cfgs
from program_graphs.cfg.operators import reduce_redundant_exit_nodes, manage_jumps
from program_graphs.cfg.parser.java.utils import get_identifier, get_nodes_after_colon
from program_graphs.cfg.parser.java.switch_stmt import get_switch_block_label, get_switch_label
from program_graphs.cfg.types import Node, JumpKind, Label
from program_graphs.cfg.parser.java.break_stmt import mk_cfg_break
from program_graphs.cfg.parser.java.continue_stmt import mk_cfg_continue
from program_graphs.cfg.parser.java.return_stmt import mk_cfg_return


def parse(source_code: str) -> CFG:
    Language.build_library(
        # Store the library in the `build` directory
        'build/my-languages.so',

        # Include one or more languages
        [
            './tree-sitter-java'
        ]
    )
    JAVA_LANGUAGE = Language('build/my-languages.so', 'java')
    parser = Parser()
    parser.set_language(JAVA_LANGUAGE)
    ast = parser.parse(bytes(source_code, 'utf-8'))
    return mk_cfg(ast.root_node)


def mk_cfg(node: Node, **kwargs: Any) -> CFG:
    if node.type == 'for_statement':
        return mk_cfg_for(node, **kwargs)

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
    return mk_cfg_of_list_of_nodes(node.children, **kwargs)


def mk_cfg_for(node: Node, label: Label = None, source: bytes = None) -> CFG:
    init = mk_cfg(node.child_by_field_name('init'))
    condition = mk_cfg(node.child_by_field_name('condition'))
    body = mk_cfg(node.child_by_field_name('body'), source=source)
    update = mk_cfg(node.child_by_field_name('update'))
    exit = mk_empty_cfg()

    cfg, m1, m2, m3, m4, m5 = merge_cfgs(init, condition, body, update, exit)
    cfg.add_edges_from([
        (m1[init.exit_node()], m2[condition.entry_node()]),
        (m2[condition.exit_node()], m3[body.entry_node()]),
        (m3[body.exit_node()], m4[update.entry_node()]),
        (m4[update.exit_node()], m2[condition.entry_node()]),
        (m2[condition.exit_node()], m5[exit.entry_node()])
    ])

    cfg.add_possible_jump(m4[update.entry_node()], None, JumpKind.CONTINUE)
    cfg.add_possible_jump(m5[exit.entry_node()], None, JumpKind.BREAK)
    if label is not None:
        cfg.add_possible_jump(m4[update.entry_node()], label, JumpKind.CONTINUE)
    cfg.set_node_name(m4[update.entry_node()], 'for-update')
    cfg.set_node_name(m2[condition.entry_node()], 'for-condition')
    cfg.set_node_name(m1[init.exit_node()], 'for-init')
    cfg.set_node_name(m5[exit.entry_node()], 'exit')

    cfg = reduce_redundant_exit_nodes(cfg)
    cfg = manage_jumps(cfg)
    return cfg


def mk_cfg_if(node: Node, **kwargs: Any) -> CFG:
    if node.child_by_field_name('alternative') is not None:
        return mk_cfg_if_else(node, **kwargs)

    condition = mk_cfg(node.child_by_field_name('condition'))
    consequence = mk_cfg(node.child_by_field_name('consequence'), **kwargs)
    exit = mk_empty_cfg()
    assert len(consequence.entry_nodes()) == 1

    cfg, m1, m2, m3 = merge_cfgs(condition, consequence, exit)
    cfg.add_edges_from([
        (m1[condition.exit_node()], m2[consequence.entry_node()]),
        (m1[condition.exit_node()], m3[exit.entry_node()]),
        (m2[consequence.exit_node()], m3[exit.entry_node()]),
    ])

    cfg.set_node_name(m1[condition.entry_node()], 'if-condition')
    cfg.set_node_name(m3[exit.entry_node()], 'exit')
    cfg = reduce_redundant_exit_nodes(cfg)
    return cfg


def mk_cfg_if_else(node: Node, **kwargs: Any) -> CFG:
    condition = mk_cfg(node.child_by_field_name('condition'))
    consequence = mk_cfg(node.child_by_field_name('consequence'), **kwargs)
    alternative = mk_cfg(node.child_by_field_name('alternative'), **kwargs)
    exit = mk_empty_cfg()
    assert len(consequence.entry_nodes()) == 1

    cfg, m1, m2, m3, m4 = merge_cfgs(condition, consequence, alternative, exit)
    cfg.add_edges_from([
        (m1[condition.exit_node()], m2[consequence.entry_node()]),
        (m1[condition.exit_node()], m3[alternative.entry_node()]),
        (m2[consequence.exit_node()], m4[exit.entry_node()]),
        (m3[alternative.exit_node()], m4[exit.entry_node()])
    ])
    cfg.set_node_name(m1[condition.entry_node()], 'if-condition')
    cfg.set_node_name(m4[exit.entry_node()], 'exit')
    cfg = reduce_redundant_exit_nodes(cfg)
    return cfg


def get_cfg_switch_block_group_body(node: Node, **kwargs: Any) -> CFG:
    nodes_after_colon = get_nodes_after_colon(node)
    return mk_cfg_of_list_of_nodes(nodes_after_colon, **kwargs)


def mk_cfg_switch_case_group(node: Node, **kwargs: Any) -> CFG:
    assert node.type == 'switch_block_statement_group'
    condition = CFG([get_switch_label(node)])
    body = get_cfg_switch_block_group_body(node, **kwargs)
    exit = mk_empty_cfg()

    cfg, m1, m2, m3 = merge_cfgs(condition, body, exit)
    cfg.add_edges_from([
        (m1[condition.exit_node()], m2[body.entry_node()]),
        (m1[condition.exit_node()], m3[exit.entry_node()]),
        (m2[body.exit_node()], m3[exit.entry_node()]),
    ])
    cfg = reduce_redundant_exit_nodes(cfg)
    return cfg


def mk_cfg_switch_default_group(node: Node, **kwargs: Any) -> CFG:
    assert node.type == 'switch_block_statement_group'
    body = get_cfg_switch_block_group_body(node, **kwargs)
    exit = mk_empty_cfg()
    cfg, m1, m2 = merge_cfgs(body, exit)
    cfg.add_edges_from([
        (m1[body.exit_node()], m2[exit.entry_node()]),
    ])
    cfg = reduce_redundant_exit_nodes(cfg)
    return cfg


def mk_cfg_switch(node: Node, **kwargs: Any) -> CFG:
    groups = [n for n in node.child_by_field_name('body').children if n.type == 'switch_block_statement_group']
    default_groups = [g for g in groups if get_switch_block_label(g) == 'default']
    case_groups = [g for g in groups if get_switch_block_label(g) == 'case']
    case_groups_cfg = combine_list([mk_cfg_switch_case_group(g, **kwargs) for g in case_groups])
    default_group_cfg = combine_list([mk_cfg_switch_default_group(g, **kwargs) for g in default_groups])

    cfg = combine(case_groups_cfg, default_group_cfg)
    cfg.add_possible_jump(cfg.exit_node(), None, JumpKind.BREAK)
    manage_jumps(cfg)
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
    return cfg
