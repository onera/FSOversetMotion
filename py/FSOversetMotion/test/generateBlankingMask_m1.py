# Usage: kpython -n2 -t4 generateBlankingMask_m1.py
from FSDataManager import FSError, FSDataManager
from FSCGNSConverter.FSCGNSConverter import buildMeshOps
from FSOversetMotion.FSOversetMotion import generateBlankingMask, getClacInfo
import KCore.test as Ktest

localDirIn = './INPUT/'

meshDict = {
    'background': {'meshFilename': localDirIn+'background.h5', 'meshProcessorWeight': 1.},
    'naca': {'meshFilename': localDirIn+'naca.h5', 'meshProcessorWeight': 1.}
}
offsetDict = {
    'background': 0.01, # there is no BCWall in 'background' mesh so it will not be taken into account
    'naca': 0.3
}

# Get clacs
meshKey, meshColor, clac, globalClac, masterClac = getClacInfo(meshDict)
meshFilename = meshDict[meshKey]['meshFilename']

# Get orig mesh
dm = FSDataManager(globalClac)
fsmeshOrig = dm.GetMesh(meshKey, clac, True)
meshOps = buildMeshOps(meshFilename, verbose=False)
fsmeshOrig.DoOps(meshOps) or FSError.PrintAndExit()

# Automatically generate blankingMaskDict from offsetDict
blankingMaskDict = generateBlankingMask(
    clac=clac, fsmesh=fsmeshOrig,
    offsetDict=offsetDict,
    meshKey=meshKey,
    offsetFromBC='BCWall', 
    check=False)

# test
if globalClac.GetProcID() == 0:
    for pos, meshKeyLocal in enumerate(blankingMaskDict): Ktest.testT(blankingMaskDict[meshKeyLocal],pos+1)

