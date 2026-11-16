# Usage: kpython -n1 -t4 howToUseFSOversetMotionSteadSimReference.py
from FSDataManager import FSClac, FSError, FSDataLog, FSDataManager, FSMesh

from CODA import DiscretizationFactory, TimeIntegrationFactory
from CODA import StopNumIterations, StopRelativeReduction
from CODA import MonitorTabular, MonitorSelection
from CODA.CODAHelpers import BuildDiscretizationParameterTrees, BuildTimeIntegrationParameterTrees

from FSOversetMotion.FSOversetMotion import generateDiscParasFromMesh
from FSCGNSConverter.FSCGNSConverter import buildMeshOps

# mesh settings
localDirIn = 'INPUT/'
localDirOut = 'OUTPUT/STEADY_REF/'
meshFilename = localDirIn+'reference.h5'

# solver settings
targetResidualReduction = 1.0e-8
maximumNumberOfIterations = 200

discSelectionParaDict = {
    "PDE" : "Euler",
    "spatial scheme" : "FV",
    "convection scheme" : "Roe upwinding",
    "order" : 2,
}
discParaDict = {
    "testing": {
        "willfully ignore excessive load imbalance among domains w.r.t. the number of faces": True,
    },
    "reference state": {
        "flow speed specification": {
            "type": "Mach number based",
            "Mach": 0.755,
        },
        "flow direction specification": {
            "type": "aerodynamic flow angles",
            "angle of attack": 0.0,
        },
    },
    "preprocessing" : {
        "maximum relative surface integral" : 1e-13,
        "non-local boundary treatments" : {
            "epsilon for in-element check" : 1e-13,
        },
    },
    "reconstruction": {
        "type": "limited linear",
        "face gradient augmentation": {
            "type": "cell-to-face"
        },
        "face gradient augmentation for the Jacobian matrix": {
            "type": "cell-to-face"
        },
        "gradient limiter": {
            "type": "full limiting",
        },
    },
    "boundary integral quantities": {
        "Coef_Area": 1.0,
        "Moment_Center": [0.25, 0.0, 0.0],
        "Coef_Length": 1.0,
    },
}
timeIntegrationParaDict = {
    "time integration method": "linearized implicit Euler",
    "time step": {
        "type": "local",
        "CFL": {
            "type": "SER ramp max refmax",
            "initial CFL number": 1.0,
            "maximum CFL number": 1000,
            "SER exponent": 0.5,
        },
    }
}

## ====================================
## Create Data Manager & set Orig/Active
## ====================================    
clac = FSClac()
dm = FSDataManager(clac)
fsmeshActive = FSMesh(clac)

meshOps = buildMeshOps(meshFilename, preserveCellStacks=True, verbose=True)
fsmeshActive.DoOps(meshOps) or FSError.PrintAndExit()

## ====================================
## Set up CODA Dics & Settings
## ====================================
fsmeshActive.CreateLocalNumbering() # mandatory for Cmpi.size > 2

discParaDict = generateDiscParasFromMesh(fsmeshActive, discParaDict)

discSelectionParas, discParas = BuildDiscretizationParameterTrees(discSelectionParaDict, discParaDict)
disc = DiscretizationFactory.GetSingleton().Create(discSelectionParas, clac, fsmeshActive, discParas)

timeIntegrationParasAllLevels = BuildTimeIntegrationParameterTrees([timeIntegrationParaDict])
timeIntegrationParas = timeIntegrationParasAllLevels[0]
timeIntegration = TimeIntegrationFactory.GetSingleton().Create(disc, timeIntegrationParasAllLevels)

state = disc.CreateZeroFieldVector()
disc.InitializeFieldVector({'type': 'free stream'}, state)

residualNames = ['DensityResidual', 'MomentumResidual', 'EnergyStagnationDensityResidual']
monitorVariables = ['CFL'] + ['%sReduction'%res for res in residualNames]
reductionCallback = StopRelativeReduction(residualNames, targetResidualReduction)

iterationCallbacks = (reductionCallback | StopNumIterations(maximumNumberOfIterations)) + MonitorTabular(
    clac,
    disc.GetStateVariableNames(),
    timeIntegrationParas['state backup controller'],
    monitorVariables=monitorVariables,
    monitorSelection=MonitorSelection(monitorWallClockTime=False),
    monitorPeriod=1,
)

dataLog = FSDataLog(clac)

## ====================================
## Compute loop
## ====================================

# solution process
status = timeIntegration.Iterate([iterationCallbacks], state, dataLog)

# copy solution to active grids
state.ExportToFSMesh(disc.GetMeshInterface(), fsmeshActive, 'State') or FSError.PrintAndExit()

# export convergence history
dataLog.ExportDataTECPLOT(localDirOut+'monitor.dat', 'l2-norms') or FSError.PrintAndExit()

# export flow solution
fsmeshActive.ExportMeshHDF5(HDF5Filename=localDirOut+'solution_reference.h5', FilePerProcess=False) or FSError.PrintAndExit()