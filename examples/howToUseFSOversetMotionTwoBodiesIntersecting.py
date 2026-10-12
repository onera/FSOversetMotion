# Usage: kpython -n3 -t4 howToUseFSOversetMotionTwoBodiesIntersecting.py
from FSDataManager import FSError, FSDataManager

from FSCGNSConverter.FSCGNSConverter import buildMeshOps
from FSOversetMotion.FSOversetMotion import FSOversetMotion, generateBlankingMask, extractActiveSubMesh, getClacInfo, getMeshKeys

localDirIn = './INPUT/'
localDirOut = './OUTPUT/TEST3/'

meshDict = {
    'background': {'meshFilename': localDirIn+'background.h5', 'meshProcessorWeight': 1.},
    'naca': {'meshFilename': localDirIn+'naca.h5', 'meshProcessorWeight': 1.},
    'cyl': {'meshFilename': localDirIn+'cylinder_large.h5', 'meshProcessorWeight': 1.}
}
offsetDict = {
    'naca': 0.3,
    'cyl': 0.3
}
blankingDict = {
    'background': ['naca','cyl'],
    'cyl': ['naca']
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

# FSOversetMotion
blankingMaskDict = generateBlankingMask(
    clac=clac, fsmesh=fsmeshOrig,
    offsetDict=offsetDict,
    meshKey=meshKey,
    localDir=localDirOut,
    offsetFromBC='BCWall',  
    check=False)

blankingObj = FSOversetMotion(clac=clac, fsmesh=fsmeshOrig, meshKey=meshKey, blankingDict=blankingDict)

# 1-update cell nature field with 0 (blanked) and 1 (active)
blankingObj.computeBlanking(blankingMaskDict=blankingMaskDict)

# 2-remove blanked cells
extractActiveSubMesh(dm, meshKeyOrig, meshKeyActive) 

# 3-save active mesh
fsmeshActive.ExportMeshHDF5(Filename=localDirOut+'%s_active.h5'%meshKey) or FSError.PrintAndExit()