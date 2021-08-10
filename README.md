# program-graphs

An experimental python library to build graphs for programs written in different programming languages. The library is based on a great [Tree-sitter](https://tree-sitter.github.io/tree-sitter/) library.

 - Control Flow Graph
 - Control Dependency Graph
 - Data Dependency Graph
 - Program Dependency Graph


# Simple Example

From console:

```bash 
$ echo "if (x > 0) { y = 0; }" |  python3 -m program_graphs
```

From python:

```python

from program_graphs.cfg import CFG, parse_java

java_code = '''
    if (x  > 0) {
        y = 0;
    }
'''

cfg = parse_java(java_code)
print(cfg)
```
Expected output:
```
From              To
------------  --  ---------
if-condition  ->  statement
statement     ->  exit
if-condition  ->  exit
```

# How to install


```bash
$ git clone --recurse-submodules git@github.com:acheshkov/program-graphs.git
$ pip install -r requirements/default.txt
```


# Limitations

 - For now, only a Java language is supported
 - It's not possible to build `CFG` for a project or class. Only method level is supported
