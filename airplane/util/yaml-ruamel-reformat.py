#!/usr/bin/env python3

"""Converts regular YAML to Ruamel formatted YAML"""

import getopt
import sys

from ruamel.yaml import YAML

input_file = ''
output_file = ''
try:
    opts, args = getopt.getopt(sys.argv[1:], "hi:o:", ["input=", "output="])
except getopt.GetoptError:
    print(f'{sys.argv[0]} -i <inputfile> -o <outputfile>')
    sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        print(f'{sys.argv[0]} -i <inputfile> -o <outputfile>')
        sys.exit()
    elif opt in ("-i", "--input"):
        input_file = arg
    elif opt in ("-o", "--output"):
        output_file = arg

yaml = YAML(pure=True)
yaml.indent(mapping=2, sequence=4, offset=2)

with open(input_file, 'r') as file:
    data = yaml.load(file)

with open(output_file, 'w') as file:
    yaml.dump(data, file)
