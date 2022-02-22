import sys
from program_graphs.adg.parser.java.parser import parse

if __name__ == '__main__':
    input = sys.stdin.read()
    adg = parse(input)
    print(adg)
