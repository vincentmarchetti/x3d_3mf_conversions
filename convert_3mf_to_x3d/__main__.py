import logging, sys
from . import logger
logging.getLogger().addHandler( logging.StreamHandler( sys.stderr))
logger.setLevel(logging.WARN)


import argparse
parser = argparse.ArgumentParser("3MF to X3D conversion")
parser.add_argument('inpath', metavar="INPUT FILE", help="input 3MF file")
parser.add_argument('--verbose', dest='verbose', action="store_true", help="print info messages to stderr")

args = parser.parse_args()

if args.verbose:
    logger.setLevel(logging.DEBUG)

from os.path import exists
if not exists( args.inpath):
    raise Exception("File %s not found" % args.inpath)
input_path = args.inpath
    
    
from file_conversions import convert_to_X3D
convert_to_X3D(input_path, sys.stdout)
