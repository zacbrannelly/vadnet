import logging
import argparse
import os
from surround import Surround, Config
from .stages import ValidateData, VadData

logging.basicConfig(level=logging.INFO)

def is_valid_dir(arg_parser, arg):
    if not os.path.isdir(arg):
        arg_parser.error("Invalid directory %s" % arg)
    else:
        return arg

def is_valid_file(arg_parser, arg):
    if not os.path.isfile(arg):
        arg_parser.error("Invalid file %s" % arg)
    else:
        return arg

parser = argparse.ArgumentParser(description="The Surround Command Line Interface")
parser.add_argument('-o', '--output-dir', required=True, help="Output directory",
                                     type=lambda x: is_valid_dir(parser, x))

parser.add_argument('-i', '--input-dir', required=True, help="Input directory",
                                     type=lambda x: is_valid_dir(parser, x))
parser.add_argument('-c', '--config-file', required=True, help="Path to config file",
                                     type=lambda x: is_valid_file(parser, x))

def transform(input_dir, output_dir, config_path):
    surround = Surround([ValidateData()])
    config = Config()
    config.read_config_files([config_path])
    surround.set_config(config)

    # TODO: Read data from input directory here

    data = VadData(None)
    surround.process(data)
    with open(os.path.abspath(os.path.join(output_dir, "output.txt")), 'w') as f:
        f.write(data.output_data)
    logging.info(data.output_data)

if __name__ == "__main__":
    args = parser.parse_args()
    transform(args.input_dir, args.output_dir, args.config_file)
