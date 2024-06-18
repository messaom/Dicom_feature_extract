import os
import glob
import shutil
import re
import pydicom as dcm
import matplotlib.pyplot as plt
import numpy as np
import h5py

pass_rate={}
dest_dir_rp= './RP_files/' # Change accordingly
dest_dir_ri= './RI_files/'
root_dir = '../2024/'
associated_file=[]

# Create folder
def create_directory(directory_path):
    try:
        os.mkdir(directory_path)
        print(f"Directory '{directory_path}' created successfully.")
    except FileExistsError:
        print(f"Directory '{directory_path}' already exists.")
    except Exception as e:
        print(f"Error creating directory '{directory_path}': {e}")


create_directory(dest_dir_rp)

# Extract gamma passrate and dist/dose tolerence
# Copies the RP files into a new folder
for root, dirs, files in os.walk(root_dir):
    for dir_name in dirs:
        folder_path = os.path.join(root, dir_name)
        print(f"Processing folder: {folder_path}")
        
        for file_path in glob.glob(os.path.join(folder_path, '*.dat')):
            
            with open(file_path) as f: 
                lines = f.readlines()
            for line in lines:
                if "Gamma DTA:" in line:
                    toler=line.replace(',','.').split(':')
                    tol_dist=toler[1][:4]
                    tol_dose=toler[2][:4]
                if "ID dose portale" in line:
                    name=file_path.split('/')[-1]
                    associated_file.append([name, 'RI.'+str(name.split('.')[-3])+'.'+str(line.strip().split('\t')[-1])+".dcm"])
                
                if "Gamma de Surface" in line:
                    if len(line) > 40:
                        gamma_value = float(line.strip().split()[6].replace(',', '.'))
                        pass_rate[file_path.split('/')[-1]] = [1,gamma_value,tol_dist,tol_dose] if gamma_value > 95.0 else [0,gamma_value,tol_dist,tol_dose]

        for file_path in glob.glob(os.path.join(folder_path,'RP.*')):
            shutil.copy(file_path, dest_dir_rp)
            


img_dict={}
verif_images={}
meta_data={}
create_directory(dest_dir_ri)

# Iterate over folders in the root dir

for root, dirs, files in os.walk(root_dir):
    for dir_name in dirs:
        folder_path = os.path.join(root, dir_name)
        #print(f"Processing folder: {folder_path}")
        std_info={}
        # Iterate over files in the folder
        count_verif=0
        count_calcimg=0
        print(folder_path)
        
        for file_path in glob.glob(os.path.join(folder_path, 'RI.*')):
            f=dcm.dcmread(file_path) # Read the file 
            if file_path.split("/")[-1][3:-3] in list(i[3:-3] for i in pass_rate.keys()) :
                verif_images[file_path.split("/")[-1]]=f.pixel_array
                std_info["Study Description"] = f.StudyDescription
                count_verif+=1
            else:
                img_dict[file_path.split("/")[-1]]=f.pixel_array
                pid=f.PatientID
                #for file_path in glob.glob(os.path.join(folder_path,'RP.*')):
                shutil.copy(file_path, dest_dir_ri)
                std_info["Patient ID"]=f.PatientID    
                std_info["Patient Birth Date"]=f.PatientBirthDate
                std_info["Patient Sex"]=f.PatientSex
                
                meta_data[pid]=std_info        
                count_calcimg+=1
                
print(f" # Images Plan {len(img_dict)}")
print(f" # Images verif {len(verif_images)}")
print(f" # Analysis files {len(pass_rate)}")

img_files=list(img_dict.keys())
verif_files=list(verif_images.keys())
img_files.sort()
verif_files.sort()
clean_data_image=[]
for im1, im2 in zip(img_files,verif_files):
    print(im1,im2)
    clean_data_image.append([img_dict[im1],verif_images[im2]])
    
    
stack_data=[]
image_gamma={}
gamma_val=[]
gam=list(pass_rate.keys())
for im1, im2 in zip(img_files,verif_files):
    pass_key='RA.'+im2[3:-4]+'.dat'
    if pass_key in gam:
        input_image=img_dict[im1].flatten()
        verif_image=verif_images[im2].flatten()
        input_image=(input_image-np.min(input_image))/(np.max(input_image)-np.min(input_image))
        verif_image=(verif_image-np.min(verif_image))/(np.max(verif_image)-np.min(verif_image))
        gamma = pass_rate[pass_key][0] # Or 1 for regression values
        image_gamma[im1]=pass_rate[pass_key]    
        gamma_val.append(gamma)
        #columns=np.hstack((input_image,verif_image))
        stack_data.append(input_image)

with h5py.File('image_gamma_value.h5', 'w') as hf:
    hf.create_dataset('im_gamma', data=str(image_gamma)) # Write dictionary the hdf5 format
