"""
Manage the connections between the metadata elements
as defined in 3MF (Core Specification 1.1; section 3.4.1)
"""

"""
metadata_mapping is a dictionary
keys are the names of 3MF Core 1.1 metatadata values
as listed in Table 8-1 of the spec document.

corresponding values are the value of meta/@name attribute for
X3D XML encoding as recommended in X3D Authoring Hints
http://www.web3d.org/x3d/content/examples/X3dSceneAuthoringHints.html
and sample document http://www.web3d.org/x3d/content/examples/newScene.html
"""
metadata_mapping = {
    'Title' : 'title',
    'Designer' : 'creator',
    'Description' : 'description',
    'Copyright'   : 'rights',
    'LicenseTerms' : 'license',
    'Rating'       : 'warning',
    'CreationDate' : 'created',
    'ModificationDate' : 'modified'
}
