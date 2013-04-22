# jager - symbolic specification-based program repair

a class project for CSE990 at [UNL](http://unl.edu) in
[the Department of Computer Science and Engineering](http://cse.unl.edu)

## File Formats

### Specification File Format

the specification files are [YAML](http://www.yaml.org/) files with the
following format:

    ---
    pre:
    - "precondition1"
    - "precondition2"
    - "precondition3"
    post:
    - "postcondition1"
    - "postcondition2"
    ...

### Traces File Format

the traces files are [YAML](http://www.yaml.org/) files with the following
format:

    ---
    programid: program1
    preconditions:
      - "precondition1"
      - "precondition2"
    postconditions:
      - "postcondition1"
      - "postcondition2"
    traces:
      - id: trace1
        status: good
        statements:
          - statement: "x = x + 1"
            line: 1
          - statement: "(x > 0)"
            line: 2
          - statement: "x = x + 1"
            line: 3
          - statement: "return x"
            line: 6
      - id: trace2
        status: bad
        statements:
          - statement: "x = x + 1"
            line: 1
          - statement: "!(x > 0)"
            line: 2
          - statement: "x = x - 1"
            line: 5
          - statement: "return x"
            line: 6
    ...

## Requirements

Python Libraries:
- [PyYaml](http://pyyaml.org/)

## References

- James A. Jones, Mary Jean Harrold, and John Stasko. 2002. **Visualization of
  test information to assist fault localization**. In Proceedings of the 24th
  International Conference on Software Engineering (ICSE '02). ACM, New
  York, NY, USA, 467-477.

- Hoang D. T. Nguyen, Dawei Qi, Abhik Roychoudhury, and Satish Chandra.
  2013\. **SemFix: Program Repair via Semantic Analysis**. In Proceedings of the
  35th International Conference on Software Engineering (ICSE '13).
  ACM, San Francisco, CA, USA.

## License

... not sure yet
