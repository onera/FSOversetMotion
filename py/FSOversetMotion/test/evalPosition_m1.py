# Usage: kpython -n2 -t4 evalPosition_m1.py
from FSDataManager import FSError, FSDataManager
from FSCGNSConverter.FSCGNSConverter import buildMeshOps
from FSOversetMotion.FSOversetMotion import generateBlankingMask, copyGrid2GridInit, evalPosition, getClacInfo, getMeshKeys
from FSPlugins.test import testH5
import KCore.test as Ktest

localDirIn = './INPUT/'

meshDict = {
    'background': {'meshFilename': localDirIn+'background.h5', 'meshProcessorWeight': 1.},
    'naca': {'meshFilename': localDirIn+'naca.h5', 'meshProcessorWeight': 1.}
}
blankingDict = {
    'background': ['naca']
}
offsetDict = {
    'naca': 0.2,
}
motionDict = {
    'naca': {
        'transl_speed': [0.,0.,0.],
        'axis_pnt': [0.25,0.,0.],
        'axis_vct': [0.,1.,0.],
        'angular_frq': 0.038
    }
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

# Automatically generate blankingMaskDict from offsetDict
blankingMaskDict = generateBlankingMask(
    clac=clac, globalClac=globalClac, fsmesh=fsmeshOrig,
    offsetDict=offsetDict,
    meshKey=meshKey,
    offsetFromBC='BCWall', 
    check=False)

# Init undeformed coordinates
copyGrid2GridInit(fsmeshOrig, meshKey, motionDict, blankingMaskDict)

# Eval grid position at time = 0.25
evalPosition(fsmeshOrig, meshKey, 0.25, motionDict, blankingMaskDict)

# test
testDir = Ktest.getDataFolderName()
testFile = testDir+'/evalPosition_m1_%d.h5'%globalClac.GetProcID()
testH5(clac, fsmeshOrig,
       coordsName='Coordinates',
       rtol=0., atol=1.e-10,
       reference=testFile)

if globalClac.GetProcID() == 0:
    for pos, meshKeyLocal in enumerate(blankingMaskDict): Ktest.testT(blankingMaskDict[meshKeyLocal],pos+1)