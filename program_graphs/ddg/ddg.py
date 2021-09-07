import networkx as nx  # type: ignore
from program_graphs import CFG
from program_graphs.ddg.parser.java.utils import get_data_dependencies
from program_graphs.cfg.fcfg import mk_fcfg_from_cfg


class DDG(nx.DiGraph):
    pass


def mk_ddg(cfg: CFG, source_code: str) -> DDG:
    ddg = DDG()
    full_cfg = mk_fcfg_from_cfg(cfg)
    dds = get_data_dependencies(full_cfg, source_code.encode())
    for (write_node, read_node, var) in dds:
        ddg.add_edge(write_node, read_node, dependency='data', var=var)
    return ddg
