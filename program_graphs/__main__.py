import sys
from program_graphs.cfg.parser.java import parse

if __name__ == '__main__':
    input = sys.stdin.read()
    cfg = parse(input)
    print(cfg)
    print("nodes count", len(cfg.nodes()))
