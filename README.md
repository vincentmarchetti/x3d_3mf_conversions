convert_3mf_to_x3d
==================

Script to convert the geometric model in a 3MF format package to X3D file.

Sample 3MF files are available for testing at <https://github.com/3MFConsortium/3mf-samples>

Dependencies
------------
The following Python software must be installed for this conversion software to execute:

* [NumPy](http://www.numpy.org) Python package for multidimensional numeric arrays.
* [genshi](https://genshi.edgewall.org/) An XML templating engine.
* [python-opc](https://github.com/python-openxml/python-opc) Python package for opening and querying zip files conforming
to [Open Packaging Convention](https://msdn.microsoft.com/en-us/library/windows/desktop/dd742818(v=vs.85).aspx)

Format translation approach
---------------------------
This code will convert each of the build items in a 3MF file into a Shape node in the X3D scene graph. Each Shape
will be positioned through a Transform node into the final position and orientation as specified in the
3MF build/item element. The geometry of each build item will be taken from the resources section of the 3MF
model file.

The point coordinates defining the geometry of each shape are copied unchanged from the resources/object/mesh element
in the original 3MF file into the corresponding X3D field values in the X3D IndexedTriangleSet node. No scaling
or transformation is performed by the translation software.

The UNIT tag in the X3D header is taken from the model/@unit attribute in the 3MF file.


The Viewpoint defined in the X3D scene-graph will be directed downward along the Z-axis. 

The  metadata elements in the 3MF header section will be written to the corresponding meta elements in the 
X3D header. These supply document information such as author, creation date, title, and licensing and copyright
information.

The 3MF attributes defined for each build item will be copied into X3D MetadataObject nodes of the corresponding
X3D Transform node.

The 3MF attributes defined for each resource/object element will be copied into X3D MetadataObject nodes of the corresponding
X3D Shape node.

Translation limitations
-----------------------
In this initial implementation all color and material specifications in the 3MF file are ignored. The appearance
of Shapes in the X3D scene are defined by default coloring and lighting.

Special characters <>'"& are not allowed in the 3MF attribute values that are translated as X3D MetadataString nodes.
This will be corrected in later versions.

Commandline operation
---------------------

3MF files are converted to X3D files from the command line using the -m option. The Python 'convert_3mf_to_x3d' package
must be installed in the current working directory or in the Python module import searching path.

python -m convert_3mf_to_x3d [--verbose] INPUT_3MF_FILE > OUTPUT_X3D_FILE

XML output will be written to stdout and ordinarily should be redirected to a file, or piped to 
further XML processing code (e.g. XSLT engine).

The --verbose option will cause debugging and information level logging messages to be written to stderr.

Note
----
A 3MF file is a Zip archive; and can be readily expanded into a folder tree with ZIP software. However, this conversion
script is intended to be used on the .3mf archive file itelf and not on any of the expanded component files.
