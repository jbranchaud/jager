"""
SpecParser.py

this module allows for easy parsing of specification files that contain pre
and post conditions.
"""

import os.path
import sys
import yaml

PRE_STRING = "pre"
POST_STRING = "post"

def parse_spec(filename):
    """
    parse_spec

    given a String that represents the filename of a YAML spec file, this
    function will grab the contents of the file, parse out the specification
    information (namely pre and post conditions) and return them in a
    dictionary to the caller.
    """

    # grab the file content
    content = get_yaml_content(filename)

    # grab the preconditions
    pre_list = content[PRE_STRING]

    # grab the postconditions
    post_list = content[POST_STRING]

    # transform the pre_list and its elements as needed

    # transform the post_list and its elements as needed

    return {PRE_STRING:pre_list, POST_STRING,post_list}

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
