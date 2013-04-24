# jager - symbolic specification-based program adjustment

a class project for CSE990 at [UNL](http://unl.edu) in
[the Department of Computer Science and Engineering](http://cse.unl.edu)

This is an approach similar to some program repair techniques that seeks to
localize a fault and automatically fix that fault. However, we frame our
approach such that we seek to localize an inconsistency and adjust it such
that the program behaves in a desired way. The desired program behavior that
we are interested in is based on specifications for the program in the form
of pre and post conditions. Given a program that doesn't meet our
specifications, we adjust the program in such a way that it then satisifies
the specifications.

## Fault Localization

The FaultLocalization.py script is a module that can imported and used to
compute a ranked list of suspicious statements for a method based on a the
good and bad traces specified in a `Traces` YAML file (see below for
format).

The script utilizes the concept of *Statistical Fault Localization* to build
a ranked list of statements based on their suspiciousness as computed by:

    susp(s) = (failed(s)/totalFailed) / ((passed(s)/totalPassed) + (failed(s)/totalFailed))

This comes from the Tarantula paper (see References). This formula is based
on passing and failing test cases and the traces through the program
exercised by those test cases. For our approach, we generate symbolic traces
through a program using symbolic execution, so we have adapted the formula
to be the following:

    susp(s) = (bad(s)/totalBad) / ((good(s)/totalGood) + (bad(s)/totalBad))

This is the same formula, but based on good/bad traces rather than
passing/failing test cases.

Additionally, there are two corner cases that need to be dealt with when
computing the above suspiciousness score. The first corner case is when all
the traces for the program are *good* traces. The second corner case is when
all the traces for the program are *bad* traces.

For all *good* traces, we simply exit the fault localization procedure
because there is no reason to do program repair when the program meets the
given specification.

For all *bad* traces, we use a simplified version of the above formula that
looks like the following:

    susp(s) = bad(s) / totalBad

The ranked list returned by this script is a python list of lists where the
sublists are of length two with the first item being an integer representing
the particular line number and the second item being a string representing a
decimal value that is the ranking (between 1.0 and 0.0).

## Limitations

Jager has a number of limitations when it comes to adjusting programs. Some
of them are tied to limitations of symbolic execution and others are
limitations in our own implementation.

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

Copyright &copy; 2013 [Josh Branchaud](http://joshbranchaud.com) and Eric
Rizzi

... not sure yet
