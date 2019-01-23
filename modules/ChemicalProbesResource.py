import numpy as np
import logging
from modules.GoogleSpreadSheet import GoogleSpreadSheet

from definitions import PIS_OUTPUT_CHEMICAL_PROBES,PIS_OUTPUT_ANNOTATIONS

logger = logging.getLogger(__name__)

class ChemicalProbesResource(object):

    def __init__(self, output_dir=PIS_OUTPUT_ANNOTATIONS, input_dir=PIS_OUTPUT_CHEMICAL_PROBES):
        self.filename_cpp = input_dir+"/chemical_probes_portal.tsv"
        self.filename_sgc = input_dir+"/chemical_probes_SGC.tsv"
        self.filename_osp = input_dir+"/open_science_probes.tsv"
        self.output_dir = output_dir
        self.input_dir = input_dir

    def set_filename_type(self,spreadsheet_info):
        nome = 'filename_'+spreadsheet_info.cp_type
        if hasattr(self,nome):
            new_filename = self.input_dir+'/'+ spreadsheet_info.output_filename
            setattr(self, nome, new_filename)

    def download_spreadsheet(self, yaml_dict, chemical_output_dir):
        for spreadsheet_info in yaml_dict.chemical_probes_input:
            google_spreadsheet = GoogleSpreadSheet(chemical_output_dir)
            google_spreadsheet.download_as_csv(spreadsheet_info)
            self.set_filename_type(spreadsheet_info)

    def generate_probes(self, yaml_dict):
        # The output file
        output_filename = self.output_dir + '/'+ yaml_dict.chemical_probes_output_filename
        oFile = open(output_filename, 'w')

        # Store data for all probes and targets
        Probes = []
        Targets = []
        SGClinks = []
        SGCinfo = []
        SGCnotes = []


        myCounter = 0  # keep track of how many entries there are
        n = 0
        # **************************
        #  *** Process SGC file ***
        # **************************
        with open(self.filename_sgc, 'r') as input:
            # Read in SGC data row by row
            next(input)  # skip header row
            for row in input:
                (ProbeName, ProteinFamily, TargetNames, ControlCompound, InVivoActivity, DateAdded, SGCLink,
                 TargetNote) = tuple(row.rstrip().split('\t'))
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
        CPPlinks = [''] * n
        CPPscores = [''] * n
        CPPnotes = [''] * n

        # **************************
        #  *** Process CPP file ***
        # **************************
        with open(self.filename_cpp, 'r') as input:
            # Read in CPP data row by row
            next(input)  # skip header row
            for row in input:
                (ProbeName, TargetNames, ProteinFamily, ProteinSubclass, NumberOfReviewers, CPPscore, CPPLink,
                 CPPnote) = tuple(row.rstrip().split('\t'))
                ProbeName = ProbeName.strip()
                singleTargets = TargetNames.split(",")
                for singleTarget in singleTargets:
                    singleTarget = singleTarget.strip()
                    # If target - probe combination is already in Probes & Targets, then add CPP score into CPPscore
                    if singleTarget in Targets:
                        # Get all positions of singleTarget in Targets
                        targetPositions = [index for index, value in enumerate(Targets) if value == singleTarget]
                        dataAdded = False
                        for targetPosition in targetPositions:
                            if Probes[targetPosition] == ProbeName:
                                CPPlinks[targetPosition] = CPPLink
                                CPPscores[targetPosition] = CPPscore
                                CPPnotes[targetPosition] = CPPnote
                                dataAdded = True
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
        OSPlinks = [''] * n
        OSPnotes = [''] * n

        # **************************
        #  *** Process OSP file ***
        # **************************
        with open(self.filename_osp, 'r') as input:
            # Read in OSP data row by row
            next(input)  # skip header row
            for row in input:
                (OSPTargets, OTtargets, ProbeName, ProteinFamily, MoA, UseInAnimalModel, DonatedBy, OSPLink,
                 OSPNote) = tuple(row.rstrip().split('\t'))
                ProbeName = ProbeName.strip()
                singleTargets = OTtargets.split(",")
                for singleTarget in singleTargets:
                    singleTarget = singleTarget.strip()
                    # If target - probe combination is already in Probes & Targets, then add CPP score into CPPscore
                    if singleTarget in Targets:
                        # Get all positions of singleTarget in Targets
                        targetPositions = [index for index, value in enumerate(Targets) if value == singleTarget]
                        dataAdded = False
                        for targetPosition in targetPositions:
                            if Probes[targetPosition] == ProbeName:
                                OSPlinks[targetPosition] = OSPLink
                                OSPnotes[targetPosition] = OSPNote
                                dataAdded = True
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
        SGClinks = SGClinks + [''] * (n - len(SGClinks))
        SGCinfo = SGCinfo + [''] * (n - len(SGCinfo))
        SGCnotes = SGCnotes + [''] * (n - len(SGCnotes))

        CPPlinks = CPPlinks + [''] * (n - len(CPPlinks))
        CPPnotes = CPPnotes + [''] * (n - len(CPPnotes))
        CPPscores = CPPscores + [''] * (n - len(CPPscores))

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

        return output_filename