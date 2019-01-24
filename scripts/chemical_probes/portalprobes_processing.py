# exec(open('portalprobes_processing.py').read())

import numpy as np

# The three input files
filename_sgc = "ChemicalProbes/ChemicalProbes_Final_Data1_SGC.tsv"
filename_cpp = "ChemicalProbes/ChemicalProbes_Final_Data2_CPP_3_4stars.tsv"
filename_osp = "ChemicalProbes/ChemicalProbes_Final_Data3_OSP.tsv"
filename_sgc = "Chemical Probes - Curated - Chemical Probes Portal - Curated Data.tsv"
filename_cpp = "Chemical Probes - Curated - SGC - Curated Chemical Probes Data.tsv"
filename_osp = "Chemical Probes - Curated - Open Science Probes.tsv"

# The output file
oFile = open('chemicalprobes_alldata2.tsv', 'w')

# Store data for all probes and targets
Probes = []
Targets = []
SGClinks = []
SGCinfo = []
SGCnotes = []
CPPlinks = []
CPPscores = []
CPPnotes = []
OSPlinks = []
OSPnotes = []

myCounter = 0 # keep track of how many entries there are
n = 0
# **************************
#  *** Process SGC file *** 
# **************************
with open(filename_sgc, 'r') as input:
    # Read in SGC data row by row
    next(input) # skip header row
    for  row in input:
        (ProbeName, ProteinFamily, TargetNames, ControlCompound, InVivoActivity, DateAdded, SGCLink, TargetNote) = tuple(row.rstrip().split('\t'))
        ProbeName = ProbeName.strip()
        singleTargets = TargetNames.split(",")
        for singleTarget in singleTargets:
            singleTarget = singleTarget.strip()
            n += 1
            Probes.append(ProbeName)
            Targets.append(singleTarget)
            SGClinks.append(SGCLink)
            SGCinfo.append(InVivoActivity)
            SGCnotes.append(TargetNote)

# Initialise CPPlinks & CPPinfo to the same length as n
CPPlinks = ['']*n
CPPscores = ['']*n
CPPnotes = ['']*n

# **************************
#  *** Process CPP file *** 
# **************************
with open(filename_cpp, 'r') as input:
    # Read in CPP data row by row
    next(input) # skip header row
    for row in input:
        (ProbeName, TargetNames, ProteinFamily, ProteinSubclass, NumberOfReviewers, CPPscore, CPPLink, CPPnote) = tuple(row.rstrip().split('\t'))
        ProbeName = ProbeName.strip()
        singleTargets = TargetNames.split(",")
        for singleTarget in singleTargets:
            singleTarget = singleTarget.strip()
            # If target - probe combination is already in Probes & Targets, then add CPP score into CPPscore
            if singleTarget in Targets:
                # Get all positions of singleTarget in Targets
                targetPositions = [index for index, value in enumerate(Targets) if value == singleTarget]
                dataAdded=False
                for targetPosition in targetPositions:
                    if Probes[targetPosition] == ProbeName:
                        CPPlinks[targetPosition] = CPPLink
                        CPPscores[targetPosition] = CPPscore
                        CPPnotes[targetPosition] = CPPnote
                        dataAdded=True
                if not dataAdded:
                    n += 1
                    Probes.append(ProbeName)
                    Targets.append(singleTarget)
                    CPPlinks.append(CPPLink)
                    CPPscores.append(CPPscore)
                    CPPnotes.append(CPPnote)
            else:
                n += 1
                Probes.append(ProbeName)
                Targets.append(singleTarget)
                CPPlinks.append(CPPLink)
                CPPscores.append(CPPscore)
                CPPnotes.append(CPPnote)


# Initialise OSPlinks & OSPnotes to the same length as n
OSPlinks = ['']*n
OSPnotes = ['']*n

# **************************
#  *** Process OSP file *** 
# **************************
with open(filename_osp, 'r') as input:
    # Read in OSP data row by row
    next(input) # skip header row
    for row in input:
        (OSPTargets, OTtargets, ProbeName, ProteinFamily, MoA, UseInAnimalModel, DonatedBy, OSPLink, OSPNote) = tuple(row.rstrip().split('\t'))
        ProbeName = ProbeName.strip()
        singleTargets = OTtargets.split(",")
        for singleTarget in singleTargets:
            singleTarget = singleTarget.strip()
            # If target - probe combination is already in Probes & Targets, then add CPP score into CPPscore
            if singleTarget in Targets:
                # Get all positions of singleTarget in Targets
                targetPositions = [index for index, value in enumerate(Targets) if value == singleTarget]
                dataAdded=False
                for targetPosition in targetPositions:
                    if Probes[targetPosition] == ProbeName:
                        OSPlinks[targetPosition] = OSPLink
                        OSPnotes[targetPosition] = OSPNote
                        dataAdded=True
                if not dataAdded:
                    n += 1
                    Probes.append(ProbeName)
                    Targets.append(singleTarget)
                    OSPlinks.append(OSPLink)
                    OSPnotes.append(OSPNote)
            else:
                n += 1
                Probes.append(ProbeName)
                Targets.append(singleTarget)
                OSPlinks.append(OSPLink)
                OSPnotes.append(OSPNote)

# *****************************
#  *** Write data to oFile *** 
# *****************************
# Extend SGC/CPP links, SGC/CPP info and SGC/CPP notes to same length as len(Probes)
SGClinks = SGClinks + ['']*(n-len(SGClinks))
SGCinfo = SGCinfo + ['']*(n-len(SGCinfo))
SGCnotes = SGCnotes + ['']*(n-len(SGCnotes))

CPPlinks = CPPlinks + ['']*(n-len(CPPlinks))
CPPnotes = CPPnotes + ['']*(n-len(CPPnotes))
CPPscores = CPPscores + ['']*(n-len(CPPscores))

for i in range(0, len(Probes)):
    # Get note if there is one
    if SGCnotes[i] != "":
        iNote = SGCnotes[i]
    elif CPPnotes[i] != "":
        iNote = CPPnotes[i]
    else:
        iNote = OSPnotes[i]
    oFile.write(Probes[i] + '\t' + Targets[i] + '\t' + SGClinks[i] + '\t' + CPPlinks[i] + '\t'
                + OSPlinks[i] + '\t' + iNote + '\n')
oFile.close()