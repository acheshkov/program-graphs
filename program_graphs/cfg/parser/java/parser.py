from typing import Any, List
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.cfg import CFG
from program_graphs.cfg.operators import mk_empty_cfg, combine, merge_cfgs, reduce_redundant_exit_nodes
from program_graphs.cfg.types import Node
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


def mk_cfg_for(node: Node, **kwargs: Any) -> CFG:
    pass


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


def mk_cfg_switch(node: Node, **kwargs: Any) -> CFG:
    pass


def mk_cfg_labeled_statement(node: Node, **kwargs: Any) -> CFG:
    pass
