from program_graphs.cfg.parser.java.utils import extract_code
from program_graphs import FCFG
from typing import Tuple, List, Mapping, Set
from program_graphs.types import NodeID
from tree_sitter import Node as Statement  # type: ignore


Variable = str
DataDependency = Tuple[NodeID, NodeID]


def get_variables_written(node: Statement, source_code: bytes) -> Set[Variable]:
    if node is None:
        return set()
    if node.type == 'lambda_expression':
        return set()
    if node.type == 'assignment_expression':
        return get_variables_written(node.child_by_field_name('left'), source_code)
    if node.type == 'resource':
        return get_variables_written(node.child_by_field_name('name'), source_code)
    if node.type == 'variable_declarator':
        return get_variables_written(node.child_by_field_name('name'), source_code)
    if node.type == 'identifier' and node.parent.type not in ['labeled_statement', 'break_statement', 'continue_statement']:
        return set([extract_code(node.start_byte, node.end_byte, source_code)])

    variables = set()
    for child in node.children:
        variables |= get_variables_written(child, source_code)

    return variables


def get_variables_read(node: Statement, source_code: bytes) -> Set[Variable]:
    if node is None:
        return set()
    if node.type in ['lambda_expression', 'catch_formal_parameter']:
        return set()
    if node.type == 'assignment_expression':
        return get_variables_read(node.child_by_field_name('right'), source_code)
    if node.type == 'class_body' and node.parent.type == 'object_creation_expression':
        return set()
    if node.type == 'resource':
        return get_variables_read(node.child_by_field_name('value'), source_code)
    if node.type == 'method_invocation':
        subject = get_variables_read(node.child_by_field_name('object'), source_code)
        args = get_variables_read(node.child_by_field_name('arguments'), source_code)
        return subject | args
    if node.type == 'variable_declarator':
        return get_variables_read(node.child_by_field_name('value'), source_code)
    if node.type == 'identifier' and node.parent.type not in ['labeled_statement', 'break_statement', 'continue_statement']:
        return set([extract_code(node.start_byte, node.end_byte, source_code)])

    variables = set()
    for child in node.children:
        variables |= get_variables_read(child, source_code)

    return variables


def get_all_variables(node: Statement, source_code: bytes) -> Set[Variable]:
    write_vars = get_variables_written(node, source_code)
    read_vars = get_variables_read(node, source_code)
    return write_vars | read_vars


def get_data_dependencies(fcgf: FCFG, variables: Mapping[NodeID, Set[Variable]]) -> List[DataDependency]:
    return []
