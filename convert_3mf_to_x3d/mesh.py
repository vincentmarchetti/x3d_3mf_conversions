

def get_3MF_mesh( meshNode, ns):
    """
    Extracts the vertex-triangle properties of an 3MF mesh element
    meshNode an ElementTree.Element instance
    
    ns is a string->string callable object that converts a local-tag
    name to a namespace-qualified QName
    
    returns a dictionay with entries:
    points : (N,3) array of point coordinates
    triangles: (K,3) array of indices, each index  in range(N)
    """
    from numpy import array, float_, int_
    assert( meshNode.tag == ns('mesh') )
    
    retVal = dict()
    coordinates = list()
    vs = meshNode.find( ns('vertices'))
    if vs is None:
        raise ValueError("No vertices element found for mesh")
    for pnode in vs.findall( ns('vertex')):
        p = tuple([float( pnode.get(cn)) for cn in ('x','y','z')])
        coordinates.append(p)
    retVal['points'] = array( coordinates )
    
    indices = list()
    ts = meshNode.find( ns('triangles'))
    if ts is None:
        raise ValueError("Mesh triangles not found")
        
    for tnode in ts.findall( ns('triangle')):
        t = tuple([int( tnode.get(jn)) for jn in ('v1','v2','v3')])
        indices.append(t)
    retVal['triangles'] = array(indices)
    
    return retVal

    
