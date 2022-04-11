import networkx as nx  # type: ignore
from program_graphs.cfg.cfg import CFG
from program_graphs.ddg.parser.java.utils import get_data_dependencies, read_write_variables
from program_graphs.cfg.fcfg import mk_fcfg_from_cfg


class DDG(nx.DiGraph):
    pass


def mk_ddg(cfg: CFG, source_code: str) -> DDG:
    ddg = DDG()
    full_cfg = mk_fcfg_from_cfg(cfg)
    dds = get_data_dependencies(full_cfg, source_code.encode())

    for node, stmt in full_cfg.nodes(data='statement'):
        read_vars, write_vars = read_write_variables(stmt, source_code.encode())
        if len(read_vars) + len(write_vars) > 0:
            ddg.add_node(node, statement=stmt)

    for (write_node, read_node, vars) in dds:
        ddg.add_edge(write_node, read_node, dependency='data', vars=vars)

    return ddg
