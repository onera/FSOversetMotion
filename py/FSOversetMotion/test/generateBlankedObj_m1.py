# Usage: kpython -n2 -t4 generateBlankedObj_m1.py
from FSDataManager import FSError, FSDataManager
from FSCGNSConverter.FSCGNSConverter import buildMeshOps
from FSOversetMotion.FSOversetMotion import FSOversetMotion, getClacInfo, getMeshKeys
import Converter.PyTree as C
import KCore.test as Ktest

localDirIn = './INPUT/'

meshDict = {
    'background': {'meshFilename': localDirIn+'background.h5', 'meshProcessorWeight': 1.},
    'naca': {'meshFilename': localDirIn+'naca.h5', 'meshProcessorWeight': 1.}
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

# Initialize FSOversetMotion class for every meshKey
blankedObj = FSOversetMotion(clac=clac, fsmesh=fsmeshOrig, meshKey=meshKey, blankingDict=blankingDict)

# test
t = blankedObj.pyTree
if t is None: t = C.newPyTree(['DUMMY_%d'%meshColor])
Ktest.testT(t,globalClac.GetProcID())