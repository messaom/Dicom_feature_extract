import os
import glob
import shutil
import re


directory = '../2024/' 


def replace_last_digit(file_path):
    """The replace_last_digit function is designed to rename a file by modifying the last digit in its name
    (specifically for files ending with _X.dcm, where X is a single digit). 
    The function appends a leading zero to this digit to form a two-digit sequence and then renames the file accordingly.
    
    The second part looks for the ".dat" RA analysis files and makes the same replacement as for the RI files
    """
    
    # Regular expression pattern to match the last part
    pattern = r'_(\d)\.dcm$'
    pattern2 = r'_(\d)\.dat$'
    
    # Match the pattern with the file name
    match    = re.search(pattern, file_path)
    match_dat= re.search(pattern2, file_path)
    if match:
        # Extract the last digit
        last_digit = match.group(1)
        
        # Replace the last digit with a zero-padded version if it's a single digit
        if len(last_digit) == 1:
            new_last_part = f"0{last_digit}.dcm"
            
            # Construct the new file path
            new_file_path = file_path[:-len(last_digit + ".dcm")] + new_last_part
            
            # Rename the file
            os.rename(file_path, new_file_path)
            print(f"Renamed {file_path} to {new_file_path}")
        else:
            print(f"File path does not end with a single digit before .dcm: {file_path}")
        
    if match_dat:
        # Extract the last digit
        last_digit = match_dat.group(1)
        
        # Replace the last digit with a zero-padded version if it's a single digit
        if len(last_digit) == 1:
            new_last_part = f"0{last_digit}.dat"
            
            # Construct the new file path
            new_file_path = file_path[:-len(last_digit + ".dat")] + new_last_part
            
            # Rename the file
            os.rename(file_path, new_file_path)
            print(f"Renamed {file_path} to {new_file_path}")


root_dir=directory

# Copy analysis files ---> RA.HM#####.tag.dat
for root, dirs, files in os.walk(root_dir):
    for dir_name in dirs:
        folder_path = os.path.join(root, dir_name)
        #print(f"folder: {folder_path}")
        
        # visite les fichiers 
        for filename in os.listdir(folder_path):
            if filename.startswith('analyse'):           
                filepath=os.path.join(folder_path,filename)
                with open(filepath) as f: 
                    lines = f.readlines()
                for line in lines:
                    if 'ID:' in line.strip().split():
                        p_id=line.strip().split(':')[-1].strip()
                    elif 'ID dose portale' in line.strip().split(":"):
                        tag=line.strip().split(':')[-1].strip()
                new_filename='RA.'+p_id+'.'+tag+'.dat'
                new_filepath = os.path.join(folder_path, new_filename)
                shutil.copy(filepath,new_filepath)
                print(f"Working Dir : {folder_path}")
                print(f"Copy {filepath} --> {new_filepath}")
# Walk through the directory and subdirectories and replace the last digit 
for root, dirs, files in os.walk(directory):
    for dir_name in dirs:
        folder_path = os.path.join(root, dir_name)
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            print(file_path)
            replace_last_digit(file_path)
            

