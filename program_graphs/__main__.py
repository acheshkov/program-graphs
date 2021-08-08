from program_graphs import CFG

if __name__ == '__main__':
    cfg = CFG()
    node_1 = cfg.add_node([], 'if-condition')
    node_2 = cfg.add_node([], 'statement')
    node_3 = cfg.add_node([], 'exit')
    cfg.add_edges_from([(node_1, node_2), (node_1, node_3), (node_2, node_3)])
    print(cfg)