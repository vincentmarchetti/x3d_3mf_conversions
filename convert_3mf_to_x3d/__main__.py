#! /Users/vmarchetti/bin/python
import sys
import logging
import numpy



logger = logging.getLogger()
logger.setLevel(logging.WARN)
logger.addHandler( logging.StreamHandler(sys.stderr))

import re


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
    
    
qname_pattern=re.compile(r"\{(\S+)\}(\S+)")
def split_tag(tag):
    res = qname_pattern.match(tag)
    if res:
        ns = res.group(1)
        local_name = res.group(2)
    else:
        ns = None
        local_name = tag
    return ns, local_name
    
def ns_generator( namespace ):
    def f(tag):
        if namespace is not None:
            return "{%s}%s" %  (namespace, tag)
        else:
            return tag
    return f
    
    
import opc



logger.info( "opening 3mf file %s" % input_path )
pkg = opc.OpcPackage.open(input_path)
logger.debug( "opened 3mf file to %s" % repr(pkg))

try:
    logger.info( "main document: %s" % pkg.main_document )
except KeyError:
    logger.warn( "No main document found" )


for part in pkg.parts:
    logger.debug( "part %s : %s : %s" % (part.partname, part.content_type, len(part.blob)))
 

from io import BytesIO
model_as_file = BytesIO(pkg.parts[0].blob)

# alternative: import xml.etree.ElementTree as ET
import lxml.etree as  ET

try:
    doc = ET.parse(  model_as_file )
except Exception, exc:
    logger.exception( str(exc) )
    sys.exit(1)


namespace, root_local_name =  split_tag( doc.getroot().tag )

ns_3mf = ns_generator(namespace)

def coordinates(mesh):
    coordinates = list()
    vs = mesh.find( ns_3mf('vertices'))
    if vs is None:
        raise Exception("Mesh vertice not found")
        
    for pnode in vs.findall( ns_3mf('vertex')):
        p = tuple([float( pnode.get(cn)) for cn in ('x','y','z')])
        coordinates.append(p)
        
    return numpy.array( coordinates )

def indices(mesh):
    indices = list()
    ts = mesh.find( ns_3mf('triangles'))
    if ts is None:
        raise Exception("Mesh triangles not found")
        
    for pnode in ts.findall( ns_3mf('triangle')):
        p = tuple([int( pnode.get(jn)) for jn in ('v1','v2','v3')])
        indices.append(p)
        
    return numpy.array( indices )

scaling = 1.0
root = ET.Element("Transform")
root.set('scale', " ".join( 3*[str(scaling)]))

for kmesh, mesh in enumerate( list( doc.iter( ns_3mf('mesh'))) ):
    ps = coordinates(mesh)
    ix = indices(mesh)
    shape = ET.SubElement(root,"Shape")
    geometry = ET.SubElement( shape, "IndexedTriangleSet")
    geometry.set('ccw','TRUE')
    geometry.set('solid','TRUE')    
    geometry.set('index', " ".join([str(k) for k in ix.reshape((-1,))]))
    
    coordinate = ET.SubElement(geometry, "Coordinate")
    coordinate.set('point', " ".join([str(v) for v in ps.reshape( (-1,))]))
    
    APPEARANCE_ID='mesh-appearance'
    appearance = ET.SubElement(shape, "Appearance")
    if kmesh == 0:
        appearance.set('DEF', APPEARANCE_ID)
        material = ET.SubElement(appearance, 'material')
        material.set('diffuseColor', '0.6 0.6 0.9')
    else:
        appearance.set('USE', APPEARANCE_ID)

viewpoints = [
    ET.Element('Viewpoint')
]

meta_tags = {
'author' : 'Vince Marchetti'
}


import genshi.input

from os.path import dirname
from genshi.template import TemplateLoader
template_loader= TemplateLoader(dirname(__file__), variable_lookup='lenient')
template = template_loader.load('x3d_template.xml')

args = {
    "unit"  : {'name':'inch', 'conversionFactor':0.0254},
    "model" :genshi.input.ET(root)
}


stream = template.generate(  **args)

sys.stdout.write( stream.render('xml') )
