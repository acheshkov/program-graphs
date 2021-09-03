import networkx as nx
from program_graphs import CFG
from program_graphs.ddg.parser.java.utils import get_data_dependencies
from program_graphs.cfg.fcfg import mk_fcfg


class DDG(nx.DiGraph):
    pass


def mk_ddg(cfg: CFG) -> DDG:
    ddg = DDG()
    full_cfg = mk_fcfg(cfg)
    dds = get_data_dependencies(full_cfg)
    ddg.add_nodes_from(full_cfg.nodes())
    ddg.add_edges_from(dds, dependency='data')
    return ddg
