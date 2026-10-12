import Converter.PyTree as C
import Converter.Internal as Internal
import Post.PyTree as P
import Transform.PyTree as T
import Generator.PyTree as G
from FSCGNSConverter.FSCGNSConverter import FSCGNSConverter

# Input parameters
localDir = './INPUT/'
fname = 'background'
snearFF = 0.50
snearCore = 0.02
dfar = 15.0
dz = 0.02

# Create Cartesian mesh with double geometric steps
XF0, XF1 = [-dfar, -dfar, 0], [dfar, dfar, 0]
XC0, XC1 = [-1, -1, 0], [3, 1, 0]
HC = [snearCore, snearCore, 1]
R = [1.1, 1.1, 1]
z = G.cartRx3(XC0, XC1, HC, XF0, XF1, R, dim=2)
z = C.convertArray2Hexa(z)
z = T.join(z, tol=1e-6)

# Get BCs
bc1 = P.exteriorFaces(z); bc1[0] = 'bc1'
bc2 = Internal.copyTree(z); bc2[0] = 'bc2'
bc3 = T.translate(bc2, (0,0,dz)); bc3[0] = 'bc3'

# Extrude mesh and BCs
for zloc in [z, bc1]:
    T._addkplane(zloc)
    T._contract(zloc, (0,0,0), (1,0,0), (0,1,0), dz)

# Add BCs to zone
C._addBC2Zone(z, 'BCFarfield0', 'BCFarfield', subzone=bc1)
C._addBC2Zone(z, 'BCSymmetryPlane0', 'BCSymmetryPlane', subzone=bc2)
C._addBC2Zone(z, 'BCSymmetryPlane1', 'BCSymmetryPlane', subzone=bc3)

t = C.newPyTree(['Base', z])

convObj = FSCGNSConverter(pyTree=t, flipYZAxes=True)
convObj.convert2FSDM()
convObj.export(filename=localDir+'%s.h5'%fname)