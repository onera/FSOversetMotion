import Converter.PyTree as C
import Converter.Internal as Internal
import Transform.PyTree as T
import Generator.PyTree as G
import Geom.PyTree as D
from FSCGNSConverter.FSCGNSConverter import FSCGNSConverter

import math
import sys

if len(sys.argv) < 2:
    LARGE = input('Create large cylinder? Y/n: ')
else:
    LARGE = sys.argv[1]

LARGE = LARGE.upper() in ['Y', 'YES', 'TRUE', 'T']

# Input parameters
localDir = './INPUT/'
fname = 'cylinder_large' if LARGE else 'cylinder_small'
snearWall = 0.005
snearFF = 0.02
dfar = 1.0 if LARGE else 0.7
Center = (1.8, 0., 0.)
RWall = 0.1
dz = 0.02

# Create external boundaries
Nff = int(dfar*360*math.pi/(180*snearFF))
ff = D.circle(Center=Center, R=dfar, N=Nff)
ff = C.convertArray2Tetra(ff)

# Create wall boundaries (cylinder)
NWall = int(RWall*360*math.pi/(180*snearWall))
wall = D.circle(Center=Center, R=RWall, N=NWall)
wall = C.convertArray2Tetra(wall)
T._reorder(wall, (-1,)) # normals have to point outwards

# Create tri mesh
borders = T.join(wall, ff)
z = G.T3mesher2D(borders, triangulateOnly=0, grading=1.05, metricInterpType=0)

# Get BCs
bc1 = C.convertArray2Tetra(ff); bc1[0] = 'bc1'
bc2 = C.convertArray2Tetra(wall); bc2[0] = 'bc2'
bc3 = Internal.copyTree(z); bc3[0] = 'bc3'
bc4 = T.translate(bc3, (0,0,dz)); bc4[0] = 'bc4'

# Extrude mesh and BCs
for zloc in [z, bc1, bc2]:
    T._addkplane(zloc)
    T._contract(zloc, (0,0,0), (1,0,0), (0,1,0), dz)

# Add BCs to zone
C._addBC2Zone(z, 'BCOverset0', 'BCOverset', subzone=bc1)
C._addBC2Zone(z, 'BCWallInviscid0', 'BCWallInviscid', subzone=bc2)
C._addBC2Zone(z, 'BCSymmetryPlane0', 'BCSymmetryPlane', subzone=bc3)
C._addBC2Zone(z, 'BCSymmetryPlane1', 'BCSymmetryPlane', subzone=bc4)

# Create final pyTree
t = C.newPyTree(['Base', z])

# Convert CGNS to H5
convObj = FSCGNSConverter(pyTree=t, flipYZAxes=True)
convObj.convert2FSDM()
convObj.export(filename=localDir+'%s.h5'%fname)