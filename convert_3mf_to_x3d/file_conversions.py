import sys

import re
qname_pattern=re.compile(r"\{(\S+)\}(\S+)")
def split_tag(tag):
    """
    given tag as returned from Element instance,
    split into a namespace, local-name tuple
    (or None,local-name if no namespace)
    """
    res = qname_pattern.match(tag)
    if res:
        ns = res.group(1)
        local_name = res.group(2)
    else:
        ns = None
        local_name = tag
    return ns, local_name

    
def ns_generator( namespace ):
    """
    returns string->string callable object that converts
    local-name to QName
    """
    def f(tag):
        if namespace is not None:
            return "{%s}%s" %  (namespace, tag)
        else:
            return tag
    return f


def MFVec(point, format = "%f"):
    """
    point an (N,3) array
    returns string suitable for X3D attribute value
    for type MFVec3f
    """
    return " ".join([ " ".join([format % x for x in p]) for p in point])

    
def SFVec(point, format="%f"):
    """
    points a (3,) object
    """
    return " ".join([format % x for x in point])

def SFColor(color):
    return SFVec(color, format="%.3f")
    
def MFInt(indices): 
    """
    indices a (N,) array of integers
    """
    return " ".join([('%i' % i) for i in indices])




X3D_UNITS = {
    'millimeter' : ('millimeter', 0.001),
    'meter'      : ('meter',      1.000)
}

def get_unit( modelNode ):
    """
    queries the model/@units attribute of the 3MF model element
    and returns a dictionary with keys name, conversionFactor appropriate
    for X3D interpretation
    """
    units_3mf_name = modelNode.get('unit', None)
    if units_3mf_name is None:
        raise ValueError("No units attribute found in model node")
    try:
        name, conversionFactor = X3D_UNITS[units_3mf_name]
    except KeyError:
        raise ValueError("unknown units %s in 3MF model" % (repr(units_3mf_name),))
    return {
        'name': name,
        'conversionFactor': conversionFactor
    }
    

convert_to_X3D_default = {
    'color' : (0.7,0.7,0.7)
}

def convert_to_X3D(input_path, output_stream, **keyw):
    """
    input_path a file system path
    output_stream a file-like object open for writing
    """
    from . import logger
    from numpy import array
    
    params = dict()
    params.update( convert_to_X3D_default )
    params.update( keyw )
    
    import opc
    logger.info( "opening 3mf file %s" % input_path )
    pkg = opc.OpcPackage.open(input_path)
    logger.debug( "opened 3mf file to %s" % repr(pkg))

    try:
        logger.info( "main document: %s" % pkg.main_document )
    except KeyError:
        logger.info( "No main document found" )

    for part in pkg.parts:
        logger.debug( "part %s : %s : %s" % (part.partname, part.content_type, len(part.blob)))
 

    from io import BytesIO
    model_as_file = BytesIO(pkg.parts[0].blob)

    # alternative: import xml.etree.ElementTree as ET
    try:
        import lxml.etree as  ET
        logger.info("Using lxml as ElementTree")
    except ImportError:
        import xml.etree.ElementTree as ET
        logger.info("Using xml.etree.ElementTree as ElementTree")

    try:
        doc = ET.parse(  model_as_file )
    except Exception, exc:
        logger.exception( str(exc) )
        sys.exit(1)

    namespace, root_local_name =  split_tag( doc.getroot().tag )
    logger.info("3MF model uses namespace %s" % namespace)
    ns_3mf = ns_generator(namespace)
    
    modelNode = doc.getroot()
    unit = get_unit( modelNode )
    logger.info("unit identified as %s" % unit['name'])
    
    # collect metadata
    from .metatags import metadata_mapping
    metaitems = list()
    for mNode in modelNode.findall( ns_3mf('metadata')):
        name = mNode.get('name')
        x3d_name = metadata_mapping.get(name, name)
        logger.debug("metadata %s -> %s" % (name, x3d_name))
        metaitems.append( (x3d_name, mNode.text))
    
    resourcesNode=modelNode.find(ns_3mf('resources'))
    if resourcesNode is None:
        raise ValueError("No resources node found")
        
    buildNode=modelNode.find(ns_3mf('build'))
    if buildNode is None:
        raise ValueError("No build node located")
    
    from mesh import get_3MF_mesh
    from .matrix import matrix_from_string, transform_points, identity_matrix,\
                        transform_attributes_from_matrix
    
    
    items = list( buildNode.findall(ns_3mf('item')))
    logger.debug("%i build/item elements in model" % len(items))
    
    globalPoints = list()   # will be a collection of points
                            # which define the extent of all built
                            # items in global space
                            
    group = ET.Element("Group")
    
    for itemNode in items:
        itemid = itemNode.get('objectid')
        if itemid is None:
            raise ValueError("no objectid located")
        logger.debug("build item id: %s" % (itemid,))
        for objectNode in resourcesNode.findall( ns_3mf('object')):
            if objectNode.get('id') == itemid:
                break
        else:
            raise ValueError("resource not found for id: %s" % itemid)
         
        transformString = itemNode.get('transform',None)
        if transformString is not None:
            buildMatrix = matrix_from_string( transformString )
        else:
            buildMatrix = identity_matrix
            
        meshNode = objectNode.find(ns_3mf('mesh'))
        if meshNode is None:
            raise ValueError("No mesh node for object id %s" % itemid)
        
        meshData = get_3MF_mesh( meshNode, ns_3mf)
        NPoints = len( meshData['points'] )
        NTriangles = len( meshData['triangles'] )
        logger.debug("object %s mesh: %i vertices, %i triangles" % \
                     (itemid, NPoints, NTriangles))
    
        buildPoints = transform_points(buildMatrix, meshData['points'])
        globalPoints.append(buildPoints.min(axis=0))
        globalPoints.append(buildPoints.max(axis=0))
        
        itemTransform = ET.SubElement(group, "Transform")
        transformData = transform_attributes_from_matrix( buildMatrix )
        if 'translation' in transformData:
            itemTransform.set('translation', SFVec( transformData['translation'] ))
        if 'rotation' in transformData:
            itemTransform.set('rotation', SFVec( transformData['rotation'] ))
        if 'scale' in transformData:
            itemTransform.set('scale', SFVec( transformData['scale'] ))
            
        shape = ET.SubElement(itemTransform,"Shape")
        geometry = ET.SubElement( shape, "IndexedTriangleSet")
        geometry.set('ccw','TRUE')
        geometry.set('solid','TRUE')    
        geometry.set('index', MFInt( meshData['triangles'].reshape((-1,))))
        
        coordinate = ET.SubElement(geometry, "Coordinate")
        coordinate.set('point', MFVec(meshData['points']))

        appearance = ET.SubElement(shape, "Appearance")
        material = ET.SubElement(appearance, 'Material')
        material.set('diffuseColor', SFColor( params['color'] ))

        
    # form the global bounds array of shape (2,3)
    globalPoints = array(globalPoints)
    global_bounds = array([globalPoints.min(axis=0), globalPoints.max(axis=0)])
    
    logger.info("global bounds: %s" % (repr(global_bounds),))

    centerOfRotation = 0.5*(global_bounds[0] + global_bounds[1])
    extent = max( (global_bounds[1] - global_bounds[0])[:2] )
    logger.debug("extent: %f" % (extent,))
    
    viewpointHeight = global_bounds[1,2] + 8.0 * extent
    position = array( list( centerOfRotation[:2]) + [viewpointHeight] )
    
    viewpoint = ET.Element('Viewpoint')
    viewpoint.set('centerOfRotation', SFVec( centerOfRotation))
    viewpoint.set('position', SFVec(position))
    viewpoint.set('description',"Printer Overhead")
    
    viewpoints = [viewpoint]

    import genshi.input
    
    from os.path import dirname
    from genshi.template import TemplateLoader
    template_loader= TemplateLoader(dirname(__file__), variable_lookup='lenient')
    template = template_loader.load('x3d_template.xml')
    
    args = {
        "unit"  : unit,
        "model" :genshi.input.ET(group),
        "metatags" : metaitems,
        "viewpoints" : [genshi.input.ET(vp) for vp in viewpoints]
    }
    
    
    stream = template.generate(  **args)
    
    output_stream.write( stream.render('xml') )
