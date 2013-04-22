"""
FaultLocalization.py

this script can be used to do Tarantula-style fault localization. Given
input that represents a set of good and bad traces through a software
system, this script will determine the statements that are most suspicious
-- likely to be culpable for a fault -- and return them as a ranked list.
"""

# imports
import sys
import os.path
import yaml
from decimal import Decimal
import decimal

def main(args):
    """
    main

    the main function for this script that will read in the given YAML file
    and compute the suspiciousness for it.
    """
    
    # set the decimal context
    decimal.getcontext().prec = 6

    # grab the yaml content
    document = get_yaml_content(args[0])

    # count the number of good and bad traces
    # the first will be good and the second will be bad
    good_bad_count = count_traces(document['traces'])
    good_count = good_bad_count[0]
    bad_count = good_bad_count[1]
    total_count = len(document['traces'])

    if bad_count == 0 and good_count == total_count:
        print("your program works, why are you here?!")
        sys.exit(0)

    # parse the traces
    stmt_list = parse_traces(document['traces'])

    #print stmt_list

    susp_dict = compute_all_susp(stmt_list, good_count, bad_count, total_count)

    ranked_list = rank_stmt_dict(susp_dict)

    print('susp dict: ' + str(susp_dict))

    print('ranked list: ' + str(ranked_list))

def rank_statements(filename):
    """
    rank_statement

    given the filename for a yaml file, this function will access the
    content of the yaml file and then compute the ranked list which will be
    returned by this function.
    """
    decimal.getcontext().prec = 6

    # grab the yaml content
    document = get_yaml_content(filename)

    # count the number of good and bad traces
    # the first will be good and the second will be bad
    good_bad_count = count_traces(document['traces'])
    good_count = good_bad_count[0]
    bad_count = good_bad_count[1]
    total_count = len(document['traces'])

    if bad_count == 0 and good_count == total_count:
        print("your program works, why are you here?!")
        sys.exit(0)

    # parse the traces
    stmt_list = parse_traces(document['traces'])

    susp_dict = compute_all_susp(stmt_list, good_count, bad_count, total_count)

    ranked_list = rank_stmt_dict(susp_dict)

    return ranked_list


def rank_stmt_dict(stmt_dict):
    """
    rank_stmt_dict

    this function will go through the stmt_dict and build a ranked list of
    the line with the highest suspiciousness score down to the line with
    the smallest suspiciousness score.
    """
    # create an empty ranked_list
    ranked_list = []

    for stmt in stmt_dict:
        ranked_list.append([stmt,stmt_dict[stmt]])

    # sort the list
    ranked_list = quicksort(ranked_list)

    # reverse the list to get it in order of most to least suspicious
    ranked_list.reverse()

    return ranked_list

def quicksort(stmt_list):
    """
    quicksort

    this function will perform a quick sort on the values of each item in
    the statement list. The resulting list ranked from the smallest value to
    the largest value.
    """
    if len(stmt_list) <= 1:
        return stmt_list

    pivot = stmt_list.pop()

    less = []
    more = []

    pivot_dec = Decimal(pivot[1])

    for stmt in stmt_list:
        if Decimal(stmt[1]) < pivot_dec:
            less.append(stmt)
        else:
            more.append(stmt)

    sorted_less = quicksort(less)
    sorted_more = quicksort(more)
    sorted_list = []
    sorted_list.extend(sorted_less)
    sorted_list.extend([pivot])
    sorted_list.extend(sorted_more)
    return sorted_list

def compute_all_susp(stmt_dict, good, bad, total):
    """
    compute_all_susp

    given a dictionary of lines and the number of good and bad traces
    associated with each as well as the count of the good, bad, and total
    traces for this program, this function will compute the same
    suspiciousness score for each statement that is computed by the
    Tarantula tool (Jones).
    """
    susp_dict = {}

    # go through all the statements
    for stmt in stmt_dict:
        goods = stmt_dict[stmt][0]
        bads = stmt_dict[stmt][1]
        susp = get_susp_score(goods, good, bads, bad, total)
        susp_dict[stmt] = str(susp)

    return susp_dict

def get_susp_score(goods, good, bads, bad, total):
    """
    get_susp_score

    this function will compute a specific suspiciousness score based on the
    formula used in the Tarantula paper.

    susp(s) = bads/bad / (bads/bad) + (goods/good)

    if all the traces are bad traces, then a simpler formula will be
    computed:

    susp(s) = bads/bad
    """
    # if there are no good traces, then compute simpler formula
    if good == 0:
        return Decimal(bads) / Decimal(bad)

    # compute a Decimal value and return that
    bad_div = Decimal(bads) / Decimal(bad)
    good_div = Decimal(goods) / Decimal(good)
    return (bad_div / (bad_div + good_div))

def parse_traces(traces):
    """
    parse_traces

    given a dictionary of traces, this function will go through trace by
    trace to build up a dictionary of good and bad line counts.
    """

    # a dictionary of statements to their good and bad count (list)
    stmt_dict = {}

    # go through all of the traces
    for trace in traces:
        # grab the info about this trace
        trace_id = trace['id']
        status = trace['status']

        # go through the statements in the trace
        for stmt in trace['statements']:
            line = stmt['line']
            statement = stmt['statement']

            # if it is good, then add one to the good count
            if status == 'good':
                if stmt_dict.has_key(line):
                    stmt_dict[line][0] += 1
                else:
                    stmt_dict[line] = [1,0]
            # if it is bad, then add one to the bad count
            elif status == 'bad':
                if stmt_dict.has_key(line):
                    stmt_dict[line][1] += 1
                else:
                    stmt_dict[line] = [0,1]

    return stmt_dict

def count_traces(traces):
    """
    count_traces

    given a dictionary of traces, this function will go through the
    dictionary to count the number of good and bad traces. A tuple of the
    form (goodcount,badcount) will be returned.
    """
    good = 0
    bad = 0
    for trace in traces:
        status = trace['status']
        if status == 'good':
            good += 1
        elif status == 'bad':
            bad += 1
    
    return (good,bad)

def get_yaml_content(filename):
    """
    get_yaml_content

    this function will attempt to access the content for the given filename
    and return that content. If there is an issue accessing the content then
    an error can be thrown.
    """

    # check that the given path even exists
    if not (os.path.exists(filename) and os.path.isfile(filename)):
        print('the given file does not exist - ' + filename)
        sys.exit(1)

    yamlStream = file(filename, 'r')
    document = yaml.load(yamlStream)
    yamlStream.close()

    return document

if __name__ == '__main__':
    main(sys.argv[1:])
