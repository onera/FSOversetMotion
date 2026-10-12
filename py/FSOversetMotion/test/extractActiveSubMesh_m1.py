# Usage: kpython -n2 -t4 extractActiveSubMesh_m1.py
from FSDataManager import FSError, FSDataManager
from FSCGNSConverter.FSCGNSConverter import buildMeshOps
from FSOversetMotion.FSOversetMotion import FSOversetMotion, extractActiveSubMesh, getClacInfo, getMeshKeys
from FSPlugins.test import testH5
import Generator.PyTree as G
import Post.PyTree as P
import KCore.test as Ktest

localDirIn = './INPUT/'

meshDict = {
    'background': {'meshFilename': localDirIn+'background.h5', 'meshProcessorWeight': 1.},
    'naca': {'meshFilename': localDirIn+'naca.h5', 'meshProcessorWeight': 1.}
}
blankingMaskDict = {
    'naca': P.exteriorFaces(G.cart((-0.3,0,-0.2), (2.92,0.02,0.4), (2,2,2)))
}
blankingDict = {
    'background': ['naca']
}

# Get clacs
meshKey, meshColor, clac, globalClac, masterClac = getClacInfo(meshDict)
meshFilename = meshDict[meshKey]['meshFilename']
meshKeyActive, meshKeyOrig = getMeshKeys(meshKey, blankingDict)

# Get orig mesh
dm = FSDataManager(globalClac)
fsmeshOrig = dm.GetMesh(meshKeyOrig, clac, True)
meshOps = buildMeshOps(meshFilename, verbose=False)
fsmeshOrig.DoOps(meshOps) or FSError.PrintAndExit()

# Get active mesh
fsmeshActive = dm.GetMesh(meshKeyActive, clac, True)

# Initialize FSOversetMotion class for every meshKey
blankedObj = FSOversetMotion(clac=clac, fsmesh=fsmeshOrig, meshKey=meshKey, blankingDict=blankingDict)

# Update cell nature field with 0 (blanked) and 1 (active)
blankedObj.computeBlanking(blankingMaskDict)

# Remove blanked cells from active mesh
extractActiveSubMesh(dm, meshKeyOrig, meshKeyActive)

# test
testDir = Ktest.getDataFolderName()
testFile = testDir+'/extractActiveSubMesh_m1_%d.h5'%globalClac.GetProcID()
testH5(clac, blankedObj.fsmesh,
       coordsName='Coordinates',
       rtol=0., atol=1.e-10,
       reference=testFile)