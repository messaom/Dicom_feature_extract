# Dicom_feature_extract
First attempt at creating a tool for automatic extraction of features from RT-plan dicom files and statistical features from RT-images 

## Basic usage: 
- Run `Initial_file_processing.py`
- Run `Reading_data.py`
- Run `feats_extract_RP.py`

The directory where the initial data are stored is located in `../2024/` ( to be changed in the future) 

### First run : 
The script `Initial_file_processing.py` iterates over the extracted folders and files and serves as a preprocessing script. 
- It matches the analysis files with the verification RI dicoms
- Copies the analysis files into new files with a new naming convention 'RA.HM#####.tag.dat'
- Checks for files ending with a single digit .dat (ex. "_9.dat") and replaces the file name with the inclusion of a leading 0 (ex."_09.dat")
- Does the same thing for the RI dcm files presenting the same pattern, ie. '_d.dcm'

The script `Reading_data.py` 
- Sets up destination directories for the RP and RI plan files.
- Extract the gamma pass rate along with the distance to agreement and dose to agreement parameters (used later to filter the data)
- Corresponds the gamma values with their RI measurement files.
- Copies the RP files to their destination folder.
- Copies the RI plan files to their destination folder. 
- Extracts the pixel_array data from the RI files. 
- Makes the correspondence between the RI plan and RI measurement files.
- Makes the correspondence between the Gamma extracted data and their corresponding plan files. 
- Saves the Gamma rates into and HDF file for later use.

to implement: 
    - Extraction and export of images.
    - Tests over the correspondence of the RI files. 


The script `feats_extract_RP.py`:
- Extracts features from RT plan along with Younge complexity score
- Calculates some statistical features over the images  
- Matches the RI plan files with their corresponding beam number in the RP file
- Creates a DataFrame with the features and saves it in an HDF file for later use