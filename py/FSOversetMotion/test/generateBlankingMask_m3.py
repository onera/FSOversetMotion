# Usage: kpython -n3 -t4 generateBlankingMask_m3.py
from FSDataManager import FSError, FSDataManager
from FSCGNSConverter.FSCGNSConverter import buildMeshOps
from FSOversetMotion.FSOversetMotion import generateBlankingMask, getClacInfo
import KCore.test as Ktest

localDirIn = './INPUT/'

meshDict = {
    'background': {'meshFilename': localDirIn+'background.h5', 'meshProcessorWeight': 1.},
    'naca': {'meshFilename': localDirIn+'naca.h5', 'meshProcessorWeight': 1.},
    'cyl': {'meshFilename': localDirIn+'cylinder_small.h5', 'meshProcessorWeight': 1.}
}
offsetDict = {
    'naca': 0.,
    'cyl': 0.
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
import Converter.Mpi as Cmpi
import Converter.Internal as Internal

if globalClac.GetProcID() == 0:
    for pos, meshKeyLocal in enumerate(blankingMaskDict):
        # The three lines below are meant to prevent regression
        Cmpi._setProc(blankingMaskDict[meshKeyLocal], pos+1)
        param = Internal.getNodeFromName1(blankingMaskDict[meshKeyLocal], '.Solver#Param')
        Internal.newDataArray('meshID', parent=param, value=pos+1)
        
        Ktest.testT(blankingMaskDict[meshKeyLocal],pos+1)