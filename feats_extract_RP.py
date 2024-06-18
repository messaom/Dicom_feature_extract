import os
import glob
import h5py
import ast
from scipy import stats
import pydicom
import re
import pandas as pd 
from tqdm import tqdm
import numpy as np

# Set the path variables
root_dir_rp = './RP_files/'
root_dir_ri = './RI_files/'


# More complicated function for Younge's complexity calculation
def calculate_younge_complexity(beam_energy, gantry_angle, collimator_angle, dose_rate, avg_movement):
    # Example of a more complicated calculation (replace with the actual formula if you have it)
    complexity = (beam_energy ** 2 + gantry_angle * collimator_angle) / (dose_rate + 1)
    complexity += avg_movement * (gantry_angle ** 2 + collimator_angle ** 2)
    return complexity

def read_feats(rt_plan):
    beams_data = {}
    
    for beamseq in rt_plan.BeamSequence:
        beam_number = beamseq.BeamNumber
        
        if(len(rt_plan.FractionGroupSequence)>1): # Juste au cas où y a un fraction
            print(rt_plan.PatientID)
        
        # Some RT plan files might not have all the attributes, handle missing attributes
        #beam_dose = getattr(beamseq, 'BeamDose', 0)
        if len(rt_plan.FractionGroupSequence[0].ReferencedBeamSequence)>=beam_number:
            beam_dose=getattr(rt_plan.FractionGroupSequence[0].ReferencedBeamSequence[beam_number-1],'BeamDose',0)
            beam_meter_set=getattr(rt_plan.FractionGroupSequence[0].ReferencedBeamSequence[beam_number-1],'BeamMeterset',0)
        #beam_meter_set = getattr(beamseq, 'FinalCumulativeMetersetWeight', 0)
        beam_energy = getattr(beamseq.ControlPointSequence[0], 'NominalBeamEnergy', 0)
        gantry_angle = getattr(beamseq.ControlPointSequence[0], 'GantryAngle', 0)
        collimator_angle = getattr(beamseq.ControlPointSequence[0], 'BeamLimitingDeviceAngle', 0)
        couch_angle = getattr(beamseq.ControlPointSequence[0], 'PatientSupportAngle', 0) 
        number_of_control_points=len(beamseq.ControlPointSequence)
        beam_type = beamseq.TreatmentDeliveryType if hasattr(beamseq, 'TreatmentDeliveryType') else ''
        dose_rate = getattr(beamseq.ControlPointSequence[0], 'DoseRateSet', 0)

        # Calculate average movement of the leaf jaws
        leaf_jaw_positions = []
        for cps in beamseq.ControlPointSequence:
            for device_position in cps.BeamLimitingDevicePositionSequence:
                if device_position.RTBeamLimitingDeviceType == "MLCX":
                    leaf_jaw_positions.append(device_position.LeafJawPositions)

        if leaf_jaw_positions:
            leaf_jaw_positions = np.array(leaf_jaw_positions)
            avg_movement = np.mean(np.diff(leaf_jaw_positions, axis=0), axis=0).mean()
        else:
            avg_movement = 0

        # Calculate Younge's complexity with a more complicated formula
        younge_complexity = calculate_younge_complexity(beam_energy, gantry_angle, collimator_angle, dose_rate, avg_movement)

        beam_data = [
            number_of_control_points,
            beam_dose,
            beam_meter_set,
            beam_energy,
            gantry_angle,
            collimator_angle,
            couch_angle,
            avg_movement,
            dose_rate,
            younge_complexity
        ]
        
        beams_data[beam_number] = beam_data

    return beams_data

root_dir = root_dir_rp
rplan_keys = {}
i=0

print("------------Reading plan files-----------------")
for root, dirs, files in os.walk(root_dir):
    folder_path = root
    for file_path in tqdm(glob.glob(os.path.join(folder_path, '*.dcm'))):
        rt_plan = pydicom.dcmread(file_path)
        patient_id = rt_plan.PatientID
        rplan_keys[file_path.split("/")[-1]]= read_feats(rt_plan)

#--------------------------------------------------------------------------#
#                                                                          #
#           Match RI RP files                                              #
#--------------------------------------------------------------------------#

def match_ri_to_rp(ri_files, rp_dict):
    ri_rp_map = {}

    # Create regex patterns to match different RI and RP filename formats
    # ri_pattern_with_index = re.compile(r'RI\.(HM\d+)\.Champ \d+_(\d+)\.dcm')
    # ri_pattern_without_index = re.compile(r'RI\.(HM\d+)\.Champ \d+\.dcm')
    # rp_pattern_with_index = re.compile(r'RP\.(HM\d+)\.F(\d+)_(\d+)\.dcm')
    # rp_pattern_without_index = re.compile(r'RP\.(HM\d+)\.F\d+\.dcm')
    ri_pattern_with_index = re.compile(r'RI\.(HM\d+)\.(.+?) \d+_(\d+)\.dcm')
    ri_pattern_without_index = re.compile(r'RI\.(HM\d+)\.(.+?) \d+\.dcm')
    rp_pattern_with_index = re.compile(r'RP\.(HM\d+)\.F(\d+)_(\d+)\.dcm')
    rp_pattern_without_index = re.compile(r'RP\.(HM\d+)\.F\d+\.dcm')


    # Iterate over RI files to build the mapping
    for ri_file in ri_files:
        filename = os.path.basename(ri_file)
        match_with_index = ri_pattern_with_index.match(filename)
        match_without_index = ri_pattern_without_index.match(filename)
        
        if match_with_index:
            patient_id = match_with_index.group(1)
            plan_index = match_with_index.group(3)
        elif match_without_index:
            patient_id = match_without_index.group(1)
            plan_index = None
        else:
            continue

        # Find the corresponding RP key
        for rp_key in rp_dict:
            rp_match_with_index = rp_pattern_with_index.match(rp_key)
            rp_match_without_index = rp_pattern_without_index.match(rp_key)

            if rp_match_with_index:
                rp_patient_id = rp_match_with_index.group(1)
                rp_plan_index = rp_match_with_index.group(3)
                if patient_id == rp_patient_id and plan_index == rp_plan_index:
                    if rp_key not in ri_rp_map:
                        ri_rp_map[rp_key] = []
                    ri_rp_map[rp_key].append(ri_file.split('/')[-1])
                    break
            elif rp_match_without_index:
                rp_patient_id = rp_match_without_index.group(1)
                if patient_id == rp_patient_id and plan_index is None:
                    if rp_key not in ri_rp_map:
                        ri_rp_map[rp_key] = []
                    ri_rp_map[rp_key].append(ri_file.split('/')[-1])
                    break

    # Sort RI files for each RP key
    for rp_key in ri_rp_map:
        ri_rp_map[rp_key].sort()

    return rp_dict, ri_rp_map

# Example usage:
path_var=root_dir_ri+"*.dcm"
ri_files = glob.glob(path_var)
updated_rp_dict, rirp_map = match_ri_to_rp(ri_files, rplan_keys)


with h5py.File('image_gamma_value.h5', 'r') as hf:
    dataset = hf['im_gamma']
    loaded_data = dataset[()].decode('utf-8')
    im_gamma = ast.literal_eval(loaded_data)
    #im_gamma = ast.literal_eval(hf['im_gamma'][()])
# Ce bloc fait correspondre le beamnumber au fichier champ correspondant
feats={}
rp_pattern_with_index = re.compile(r'RP\.(HM\d+)\.F(\d+)_(\d+)\.dcm')
rp_pattern_without_index = re.compile(r'RP\.(HM\d+)\.F\d+\.dcm')
for plan in rirp_map:
    for ir_file in rirp_map[plan]:
        if rp_pattern_with_index.match(plan):
            feats[ir_file]=updated_rp_dict[plan][int(ir_file[-10])] # 1_0001.dcm
        if rp_pattern_without_index.match(plan):
            if int(ir_file[-5]) in updated_rp_dict[plan]:
                feats[ir_file]=updated_rp_dict[plan][int(ir_file[-5])] # 1.dcm
                
            ### J'ai eu un problème ou le champ 3.dcm n'était pas reconnu dans le fichier RP.HM###.F1.dcm
            ### La clé se trouve dans le prochain plan généré RP.HM###.F1_0001.dcm. Finalement le _0001 est ajouté si le fichié est généré une deuxième fois
            ### Donc la correspondance champ 3.dcm avec RP.HM###.F1.dcm n'est pas systématique! s'il est généré la première fois dans un RP.HM###.F1_0001.dcm
            ### Il s'appelera toujours RI.HM####.champ 3.dcm
            else:
            # Look for the corresponding key with "_0001" appended
                plan_with_index = f"{plan[:-4]}_0001.dcm"
                if plan_with_index in updated_rp_dict:
                    feats[ir_file] = updated_rp_dict[plan_with_index][int(ir_file[-5])]  # 1.dcm
                else:
                    print(f"Key not found: {plan}")
                    
                    
data = pd.DataFrame.from_dict(feats, orient='index', columns=['number_of_control_points','beam_dose', 'beam_meter_set', 'beam_energy','gantry_angle','collimator_angle','couch_angle',
        'avg_movement','dose_rate','younge_complexity'])
#-------------------------------------------------------------
# Read data processed previously for the gamma properties 
with h5py.File('image_gamma_value.h5', 'r') as hf:
    dataset = hf['im_gamma']
    loaded_data = dataset[()].decode('utf-8')
    im_gamma = ast.literal_eval(loaded_data)
    
data2=data.reset_index().rename(columns={'index':'id'})  # Colonne ID pour la comparaison 
#--------------------------------
# Read features from images
rootdir= root_dir_ri
im_properties={}

print("------------Collecting image features-----------------")
for i in tqdm(data2['id']):
    file=pydicom.dcmread(rootdir+i)
    img=file.pixel_array
    img_flat=img.flatten()
    imim=(img_flat-np.min(img_flat))/(np.max(img_flat)-np.min(img_flat))
    im_properties[i]={'mean':np.mean(imim),'median':np.median(imim),
                    'std_dev':np.std(imim),'skewness':stats.skew(imim),
                    'kurtosis':stats.kurtosis(imim),'entropy':stats.entropy(imim),'energy':np.sum(imim**2)}
new_df=pd.DataFrame.from_dict(im_properties, orient='index')
new_df=new_df.reset_index().rename(columns={'index':'id'})



gamma_data = pd.DataFrame.from_dict(im_gamma, orient='index', columns=['pass/fail', 'pass rate','distanceTA','doseTA'])

gamma_data=gamma_data.reset_index().rename(columns={'index':'id'}) # Enlève la column index et l'insère dans une nouvelle column appelée ID
gamma_data['distanceTA']=gamma_data['distanceTA'].astype(float)
gamma_data['doseTA']=gamma_data['doseTA'].astype(float)

new_df=pd.DataFrame.from_dict(im_properties, orient='index')
new_df=new_df.reset_index().rename(columns={'index':'id'})

result_df = data2.merge(new_df, on='id', how='left') # Add stats to DataFrame
Whole_data=result_df.merge(gamma_data, on='id', how='left') # Add gamma to DataFrame

Selected_data=Whole_data[(Whole_data['distanceTA'] == 3.0)&(Whole_data['doseTA']==3.0)]
#Selected_data= Selected_data.drop(['mode'], axis=1)  # Drop non interesting columns columns 
Selected_data.to_hdf('Champ_dic.h5', key='data', mode='w') # Save_file