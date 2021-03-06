version = "0.1"

import logging

logger = logging.getLogger('X3D_3MF')
logger.setLevel(logging.WARN)
logger.addHandler( logging.NullHandler() )

# test non-standard library dependencies
try:
    try:
        import genshi
    except ImportError:
        raise Exception("'genshi' python package required and not found in import path")
        
    try:
        import numpy
    except ImportError:
        raise Exception("'NumPy' python package required and not found in import path")
    
    try:
        import opc
    except ImportError:
        raise Exception("'opc' python package required and not found in import path")
except Exception, exc:
    import sys
    sys.stderr.write("%s\n" % str(exc))
    sys.exit(1)
    
