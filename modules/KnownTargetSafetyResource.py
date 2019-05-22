import datetime
import logging
from modules.GoogleSpreadSheet import GoogleSpreadSheet
import json

from definitions import PIS_OUTPUT_KNOWN_TARGET_SAFETY, PIS_OUTPUT_ANNOTATIONS

logger = logging.getLogger(__name__)


class KnownTargetSafetyResource(object):

    def __init__(self, output_dir=PIS_OUTPUT_ANNOTATIONS, input_dir=PIS_OUTPUT_KNOWN_TARGET_SAFETY):
        self.filename_adr = input_dir + "/adverse_effects.tsv"
        self.filename_sri = input_dir + "/safety_risk_information.tsv"
        self.filename_ubr = input_dir + "/UBERON_mapping.tsv"
        self.filename_efo = input_dir + "/EFO_mapping.tsv"
        self.filename_ref = input_dir + "/references.tsv"
        self.output_dir = output_dir
        self.input_dir = input_dir
        self.suffix = datetime.datetime.today().strftime('%Y-%m-%d')

    def set_filename_type(self, spreadsheet_info):
        nome = 'filename_' + spreadsheet_info.s_type
        if hasattr(self, nome):
            new_filename = self.input_dir + '/' + spreadsheet_info.output_filename
            setattr(self, nome, new_filename)

    def download_spreadsheet(self, yaml_dict, safety_output_dir):
        for spreadsheet_info in yaml_dict.spreadsheets:
            google_spreadsheet = GoogleSpreadSheet(safety_output_dir)
            google_spreadsheet.download_as_csv(spreadsheet_info)
            self.set_filename_type(spreadsheet_info)

    def generate_known_safety_json(self, yaml_dict):

        output_filename = self.output_dir + '/' + yaml_dict.output_filename.replace('{suffix}', self.suffix)
        # Reference info
        ref_links = {}
        with open(self.filename_ref) as ref:
            # assert next(ref).strip() == "Reference\tPMID\tOther link\tShort description"
            next(ref)

            for line in ref:
                line = line.split("\t")
                ref_links[line[0].upper().strip()] = {"pmid": line[1].strip(), "link": line[2].strip()}

        # UBERON organ/system mapping
        uberon_map = {}
        with open(self.filename_ubr) as uberon:
            # assert next(uberon).strip() == "Publication term\tUBERON term\tUBERON code\tUBERON url"
            next(uberon)

            for line in uberon:
                line = line.split("\t")
                uberon_map[line[0].upper().strip()] = {"term": line[1].strip(), "code": line[2].strip()}

        # EFO adverse effect mapping
        efo_map = {}
        with open(self.filename_efo) as efo:
            # assert next(efo).strip() == "Source term\tOntology term\tCode\tUrl"
            next(efo)

            for line in efo:
                line = line.split("\t")
                efo_map[line[0].upper().strip()] = {"term": line[1].strip(), "code": line[2].strip()}


        # Function for filling in terms and their mapping in the required format
        def make_term_list(terms, mapping):
            term_list = []
            for term in terms:
                term = term.strip()
                mapped_term = ""
                code = ""
                if term.upper() in mapping:
                    mapped_term = mapping[term.upper().strip()]["term"]
                    code = mapping[term.upper()]["code"]
                term_list.append({
                    "term_in_paper": term,
                    "mapped_term": mapped_term,
                    "code": code})
            return (term_list)


        targets = {}

        # Fill in Adverse Effect information
        with open(self.filename_adr, "r") as adrs:
            # assert next(adrs).strip() == "Ref\tTarget\tMain organ/system affected\tUnspecified mechanism effects_General\tAgonism/Activation effects_Acute dosing\tAgonism/Activation effects_Chronic dosing\tAgonism/Activation effects_Developmental toxicity\tAgonism/Activation effects_General\tAntagonism/Inhibition effects_Acute dosing\tAntagonism/Inhibition effects_Chronic dosing\tAntagonism/Inhibition effects_Developmental toxicity\tAntagonism/Inhibition effects_General"
            next(adrs)

            for line in adrs:
                line = line.split("\t")
                target = line[1].strip()

                if target not in targets:
                    targets[target] = {}

                if "adverse_effects" not in targets[target]:
                    targets[target]["adverse_effects"] = []

                inner = {}
                #ref = line[0].strip()
                ref = [x.strip() for x in line[0].split(";") if x]
                organs = [x.strip() for x in line[2].split(";") if x]
                unspec_effects = [x.strip() for x in line[3].split(";") if x]
                act_acute = [x.strip() for x in line[4].split(";") if x]
                act_chr = [x.strip() for x in line[5].split(";") if x]
                act_dev = [x.strip() for x in line[6].split(";") if x]
                act_gen = [x.strip() for x in line[7].split(";") if x]
                inh_acute = [x.strip() for x in line[8].split(";") if x]
                inh_chr = [x.strip() for x in line[9].split(";") if x]
                inh_dev = [x.strip() for x in line[10].split(";") if x]
                inh_gen = [x.strip() for x in line[11].split(";") if x]
                if inh_gen == [""]: inh_gen = []

                inner["reference"] = ref
                inner["pmid"] = [ref_links[x.upper()]["pmid"] for x in ref]
                inner["ref_link"] = [ref_links[x.upper()]["link"] for x in ref]

                inner["organs_systems_affected"] = make_term_list(organs, uberon_map)

                inner["unspecified_interaction_effects"] = make_term_list(unspec_effects, efo_map)

                inner["activation_effects"] = {}
                if act_acute:
                    inner["activation_effects"]["acute_dosing"] = make_term_list(act_acute, efo_map)
                if act_chr:
                    inner["activation_effects"]["chronic_dosing"] = make_term_list(act_chr, efo_map)
                if act_dev:
                    inner["activation_effects"]["developmental"] = make_term_list(act_dev, efo_map)
                if act_gen:
                    inner["activation_effects"]["general"] = make_term_list(act_gen, efo_map)

                inner["inhibition_effects"] = {}
                if inh_acute:
                    inner["inhibition_effects"]["acute_dosing"] = make_term_list(inh_acute, efo_map)
                if inh_chr:
                    inner["inhibition_effects"]["chronic_dosing"] = make_term_list(inh_chr, efo_map)
                if inh_dev:
                    inner["inhibition_effects"]["developmental"] = make_term_list(inh_dev, efo_map)
                if inh_gen:
                    inner["inhibition_effects"]["general"] = make_term_list(inh_gen, efo_map)

                targets[target]["adverse_effects"].append(inner)

        # Fill in Safety risk information
        with open(self.filename_sri, "r") as riskinfo:
            # assert next(riskinfo).strip() == "Reference\tTarget\tMain organ/system affected\tSafety liability"
            next(riskinfo)

            for line in riskinfo:
                line = line.split("\t")
                target = line[1].strip()

                if target not in targets:
                    targets[target] = {}

                if "safety_risk_info" not in targets[target]:
                    targets[target]["safety_risk_info"] = []

                inner = {}
                # ref = line[0].strip()
                ref = [x.strip() for x in line[0].split(";") if x]
                inner["reference"] = ref
                inner["pmid"] = [ref_links[x.upper()]["pmid"] for x in ref]
                inner["ref_link"] = [ref_links[x.upper()]["link"] for x in ref]

                organs = [x.strip() for x in line[2].split(";")]
                inner["organs_systems_affected"] = make_term_list(organs, uberon_map)
                inner["safety_liability"] = line[3].strip()

                targets[target]["safety_risk_info"].append(inner)

        # Dump everything into a json file
        with open(output_filename, "w") as outjson:
            json.dump(targets, outjson)

        logger.info("Known target safety output filename : %s", output_filename)
        return output_filename

