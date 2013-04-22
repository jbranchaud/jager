# jager - symbolic specification-based program repair

a class project for CSE990 at [UNL](http://unl.edu) in
[the Department of Computer Science and Engineering](http://cse.unl.edu)

## Specification File Format

the specification files are [YAML](http://www.yaml.org/) files with the
following format:

    pre:
    - "precondition1"
    - "precondition2"
    - "precondition3"
    post:
    - "postcondition1"
    - "postcondition2"

## Requirements

Python Libraries:
- [PyYaml](http://pyyaml.org/)
