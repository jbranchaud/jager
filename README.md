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

## References

- James A. Jones, Mary Jean Harrold, and John Stasko. 2002. **Visualization of
  test information to assist fault localization**. In Proceedings of the 24th
  International Conference on Software Engineering (ICSE '02). ACM, New
  York, NY, USA, 467-477.

- Hoang D. T. Nguyen, Dawei Qi, Abhik Roychoudhury, and Satish Chandra.
  \2013. **SemFix: Program Repair via Semantic Analysis**. In Proceedings of the
  35th International Conference on Software Engineering (ICSE '13).
  ACM, San Francisco, CA, USA.
