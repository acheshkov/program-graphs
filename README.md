# program-graphs

A Multi-language python library to build Control Flow Graphs (`CFG`) from source-code.


# Simple Example

```python

from program_graphs.cfg import CFG, parse_java

java_code = '''
    if (x  > 0) {
        y = 0;
    }
'''

cfg = parse_java(java_code)
print(cfg)

('if-condition'        -> 'statement')
('statement'           -> 'exit')
('condition-body'      -> 'exit')
```


# Limitation

 - For now, only a Java language is supported
 - It's not possible to build `CFG` for a project or class. Only method level is supported
