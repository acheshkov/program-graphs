# program-graphs

An experimental python library to build graphs for programs written in different programming languages. The library is based on a great [Tree-sitter](https://tree-sitter.github.io/tree-sitter/) library and able to catch the following relations in a program:

 - Control Flow
 - Control Dependency
 - Data Dependency 
 - Syntax Dependency


# Simple Example

From console:

```bash 
$ echo "if (x > 0) { y = 0; }" |  python3 -m program_graphs
```

From python:

```python

from program_graphs.adg import parse_java

java_code = '''
    if (x  > 0) {
        y = 0;
    }
'''

adg = parse_java(java_code)
print(adg)
```
Expected output are nodes and relations between them:
```
From                        To                      Dependencies
----------------------  --  ----------------------  -------------------------------
program:1               ->  if:2                    syntax,control-flow,control-dep
program:1               ->  block-exit:10           syntax,control-dep
if:2                    ->  if_condition:3          syntax,control-flow,control-dep
if:2                    ->  block:4                 syntax
if:2                    ->  if_exit:9               syntax,control-dep
if_condition:3          ->  block:4                 control-flow,control-dep
if_condition:3          ->  if_exit:9               control-flow
block:4                 ->  {:5                     syntax
block:4                 ->  }:7                     syntax
block:4                 ->  expression_statement:6  syntax,control-flow,control-dep
block:4                 ->  block-exit:8            syntax,control-dep
expression_statement:6  ->  block-exit:8            control-flow
block-exit:8            ->  if_exit:9               control-flow
if_exit:9               ->  block-exit:10           control-flow

```

# How to install


```bash
$ git clone --recurse-submodules git@github.com:acheshkov/program-graphs.git
$ pip install -r requirements/default.txt
```


# Limitations

 - For now, only a Java language is supported;
 - For now, `CFG`, `CDG`, `DDG`, and `AST` relations are accounted;
 - It's not possible to build graphs for a project or class. Only method level is supported
