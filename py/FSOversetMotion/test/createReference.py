import Converter.PyTree as C
import Converter.Internal as Internal
import Post.PyTree as P
import Transform.PyTree as T
import Generator.PyTree as G
from FSCGNSConverter.FSCGNSConverter import FSCGNSConverter

# Input parameters
localDir = './INPUT/'
fname = 'reference'

t_back = C.convertFile2PyTree(localDir+'background.h5')
t_naca = C.convertFile2PyTree(localDir+'naca.h5')

zmin = C.getMinValue(t_naca, 'CoordinateZ')
zmax = C.getMaxValue(t_naca, 'CoordinateZ')
xmin = C.getMinValue(t_naca, 'CoordinateX')
xmax = C.getMaxValue(t_naca, 'CoordinateX')
eps = 1.e-12

def mask(x,z):
    if   x <= xmin-eps or x >= xmax+eps: return 1
    elif z <= zmin-eps or z >= zmax+eps: return 1
    else: return 0

# 1 - Recover BCs
BCInfo = []

bc1 = C.extractBCOfType(t_naca, 'FamilySpecified:BCWallInviscid0')[0]
bc1[0] = 'bc1'

bc2 = C.extractBCOfType(t_back, 'FamilySpecified:BCFarfield0')[0]
bc2[0] = 'bc2'

bc31 = C.extractBCOfType(t_naca, 'FamilySpecified:BCSymmetryPlane0')[0]
bc32 = C.extractBCOfType(t_back, 'FamilySpecified:BCSymmetryPlane0')[0]
C._initVars(bc32, 'cellN', mask, ['CoordinateX','CoordinateZ'])
bc32 = P.selectCells(bc32, '{cellN}', strict=0)
Internal._rmNodesByName(bc32, Internal.__FlowSolutionNodes__)
bc31[0] = 'bc31'; bc32[0] = 'bc32'

bc41 = C.extractBCOfType(t_naca, 'FamilySpecified:BCSymmetryPlane1')[0]
bc42 = C.extractBCOfType(t_back, 'FamilySpecified:BCSymmetryPlane1')[0]
C._initVars(bc42, 'cellN', mask, ['CoordinateX','CoordinateZ'])
bc42 = P.selectCells(bc42, '{cellN}', strict=0)
Internal._rmNodesByName(bc42, Internal.__FlowSolutionNodes__)
bc41[0] = 'bc41'; bc42[0] = 'bc42'

BCInfo.append([bc1, 'BCWallInviscid0', 'BCWallInviscid'])
BCInfo.append([bc2, 'BCFarfield0', 'BCFarfield'])
BCInfo.append([bc32, 'BCSymmetryPlane20', 'BCSymmetryPlane'])
BCInfo.append([bc42, 'BCSymmetryPlane10', 'BCSymmetryPlane'])
BCInfo.append([bc31, 'BCSymmetryPlane21', 'BCSymmetryPlane'])
BCInfo.append([bc41, 'BCSymmetryPlane11', 'BCSymmetryPlane'])

# 2 - Merge Background (HEXA) and Naca (PENTA)
C._initVars(t_back, 'cellN', mask, ['CoordinateX','CoordinateZ'])
C._initVars(t_naca, 'cellN', 1)

t_back = P.selectCells(t_back, '{cellN}', strict=0)
t_naca = P.selectCells(t_naca, '{cellN}', strict=0)

Internal._rmNodesByName(t_back, Internal.__FlowSolutionNodes__)
Internal._rmNodesByName(t_naca, Internal.__FlowSolutionNodes__)

Internal._rmNodesFromName(t_back, 'BC*')
Internal._rmNodesFromName(t_naca, 'BC*')

z1 = Internal.getZones(t_back)[0]; z1[0] = 'back'
z2 = Internal.getZones(t_naca)[0]; z2[0] = 'naca'

t = C.mergeConnectivity(z1, z2)

# 3 - add BC to zones
for (subzone, bcname, bctype) in BCInfo:
    C._addBC2Zone(t, bcname, bctype, subzone=subzone)

# Convert CGNS to H5
convObj = FSCGNSConverter(pyTree=t, flipYZAxes=False)
convObj.convert2FSDM()
convObj.export(filename=localDir+'%s.h5'%fname)