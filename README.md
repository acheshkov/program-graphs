# program-graphs

A python library to build graphs for programs written in different programming languages. 

 - Control Flow Graph
 - Control Dependency Graph
 - Data Dependency Graph
 - Program Dependency Graph


# Simple Example

From console:

```$ echo "if (x > 0) { y = 0; }" |  python3 -m program_graphs```

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


# Limitations

 - For now, only a Java language is supported
 - It's not possible to build `CFG` for a project or class. Only method level is supported
