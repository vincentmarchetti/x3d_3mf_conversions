"""
Manages 3MF matrices as specified in Core spec 1.1 Section 3.3
and the representation of action of 3MF matrix as a 
X3D Transform node

A 3MF matrix will be represented by a numpy array of shape (4,3)

Note that numpy.dot function implements matrix multiplication for 1 and 2 rank arrays
"""

def _identity_matrix():
    from numpy import array, float_
    return array([(1,0,0),(0,1,0),(0,0,1),(0,0,0)], float_)
    
identity_matrix = _identity_matrix()

def matrix_from_string(a):
    """
    a is a string of 12 numerical values separated by
    white space. This is the form used when a 3MF matrix
    is specified as the value of an XML attribute
    """
    
    try:
        values = [float(v) for v in a.split()]
    except Exception, exc:
        message = "cannot interpret %s as string with floating point values" % (repr(a),)
        raise ValueError(message)
    
    if len(values) != 12:
        message = "matrix string must has 12 floating point values"
        raise ValueError(message)
        
    from numpy import array, float_
    return array( [values[k:k+3] for k in range(0,12,3)], float_)



def transform_points(M, points):
    """
    M a (4,3) array interpreted as a 3MF matrix
    points a (N,3) array, a list of N points with 3 coordinates
    
    returns (N,3) array of transformed coordinates
    """
    assert( M.shape == (4,3))
    assert( len(points.shape) == 2 and points.shape[1] == 3 )
    
    # implemented so as to demonstrate use of affine coordinates
    from numpy import array, ones, float_, dot, identity
    N = points.shape[0]
    affine_points = ones( (N,4), float_)
    affine_points[:,0:3] = points
    
    affine_M = identity( 4, float_)
    affine_M[:,0:3] = M
    transformed_affine_points = dot( affine_points, affine_M )
    
    return transformed_affine_points[:,0:3]
    
def transform_one_point(M, point):
    """
    convenience wrapper for point just (3,) coordinates
    """
    assert( point.shape == (3,) )
    from numpy import array
    points = array( (point,))
    return transform_points(M,points)[0]

def transform_attributes_from_matrix( M ):
    """
    input M a (4,3) array interpreted as 3MF matrix
    returns a dict object whose entries are 
    fields of the X3D Transform node
    """
    TOL = 1.0e-6
    assert( M.shape == (4,3))
    retVal = dict()
    
    translation = M[3]
    if (abs(translation) > 0.0).any():
        retVal['translation'] = translation
        
    R = M[:3,:3].transpose()
    from numpy.linalg import svd, det
    from numpy import identity, float_, dot
    from math import atan2
    U,S,Vh = svd( R )
    
    scale_spread = S.ptp()
    if scale_spread > TOL:
        raise ValueError("non-isotropic scaling not implemented")
    scale = S.mean()
    R = R/scale
    
    if abs(scale-1.0) > TOL:
        retVal['scale'] = array((scale,scale,scale), float_)
    
    U,S,Vh = svd(R-identity(3, float_))
    Vh = Vh * det(Vh)
    axis = Vh[2]
    
    K = dot(Vh, dot(R,Vh.transpose()))
    theta = atan2(-K[0,1],K[0,0])
    
    if theta < 0.0:
        theta = -theta
        axis = -axis
    
    if abs(theta) > TOL:
        retVal['rotation'] = array( list(axis) + [theta], float_)
        
    return retVal
    
    
if __name__ == '__main__':
    from numpy import array, float_
    
    # CYCLIC_ROTATE is the 3MF matrix that transform coordinates
    # (1,0,0) --> (0,1,0)  ; x line --> y-line
    # (0,1,0) --> (0,0,1)  ; y line --> z-line
    # (0,0,1) --> (1,0,0)  ; z line --> x-line
    
    # development note: following example should be documented or replaced
    # by a worked example from 3MF specifications
    CYCLIC_ROTATE = array( [(0,1,0),(0,0,1),(1,0,0),(0,0,0)], float_ )
    CYCLIC_ROTATE_STRING = "0 1 0 0 0 1 1 0 0 0 0 0"
    
    # a 3MF array that should translate by 2 units in y-axis
    TRANSLATE_Y = array( [(1,0,0),(0,1,0),(0,0,1),(0,2,0)], float_)
    
    import unittest
    
    class TestCase(unittest.TestCase):
        NEARLY_EQUAL_TOLERANCE = 1.0e-8
        
        def nearly_equal_arrays(self, a,b):
            return (a.shape == b.shape) and (abs(a-b) < self.NEARLY_EQUAL_TOLERANCE).all()
            
        def __str__(self):
            return self._testMethodDoc
    
        def test10(self):
            "Basic 3MF transformations"
            x = array( (1,0,0), float_)
            y = array( (0,1,0), float_)
            z = array( (0,0,1), float_)
            
            M = CYCLIC_ROTATE
            for orig, exact_conv in [(x,y),(y,z),(z,x)]:
                conv = transform_one_point(M, orig)
                self.assert_( self.nearly_equal_arrays(conv, exact_conv))
                
        def test20(self):
            "Read 3MF matrix from string"
            M = matrix_from_string( CYCLIC_ROTATE_STRING )
            self.assert_( self.nearly_equal_arrays( M, CYCLIC_ROTATE))
        
        def test30(self):
            "convert 3MF matrix to Transform attributes"
            rv = transform_attributes_from_matrix( CYCLIC_ROTATE )
            
            from math import pi, sqrt
            exact_polar = array([sqrt(1./3.)] * 3 + [2.*pi/3], float_)
            
            self.assert_( len(rv) == 1)
            polar = rv['rotation']
            self.assert_( self.nearly_equal_arrays( polar, exact_polar))
           
        def test40(self):
            "Translate with 3MF matrix"
            from numpy import array, cos, sin, linspace
            from math import pi
            # generate a bunch of points to translate
            Npoints = 20
            angles = linspace(0.0, 2.*pi, Npoints)
            points = array([sin(angles), cos(2.*angles), angles]).transpose()
            
            t = array([0.0,2.0,0.0])
            
            exact_transformed = points + t
            transformed = transform_points( TRANSLATE_Y, points)
            self.assert_(self.nearly_equal_arrays( transformed, exact_transformed))

        def test50(self):
            "3MF translation matrix converted to X3D Transform"
            from numpy import array, cos, sin, linspace
            from math import pi
            
            exact_t = array([0.0,2.0,0.0])
            
            rv = transform_attributes_from_matrix( TRANSLATE_Y )
            
            self.assert_( len(rv) == 1 )
            t = rv['translation']
            self.assert_(self.nearly_equal_arrays( t, exact_t ))
            
            
    suite = unittest.TestSuite()
    suite.addTest( unittest.defaultTestLoader.loadTestsFromTestCase(TestCase))
    unittest.TextTestRunner(descriptions=False, verbosity=2).run(suite)
        
        
