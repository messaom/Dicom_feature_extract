from img2vec_pytorch import Img2Vec
import torch
from torchvision import transforms
from PIL import Image
import pandas as pd
import pydicom
from tqdm import tqdm
import numpy as np
import h5py
import ast


def torch_feats(img):
    def grayscale_to_rgb(img):
        grayscale_tensor = torch.from_numpy(np.array(img)).unsqueeze(0)  # Convert to tensor with channel dimension
        return grayscale_tensor.repeat(3, 1, 1)  # Duplicate grayscale channel for RGB

    rgb_img = grayscale_to_rgb(img)  
    # Convert to PyTorch tensor
    tensor = torch.from_numpy(np.array(rgb_img))  

    pil_image = transforms.ToPILImage()(tensor)

    # Extract the feature vector
    image2vec = Img2Vec()
    feature_vector = image2vec.get_vec(pil_image)

    return(feature_vector)

def load_dicom_image(file_path):
    dicom_file = pydicom.dcmread(file_path)
    image = dicom_file.pixel_array
    max_value = np.iinfo(image.dtype).max  # max value uint16
    image_data = (image / max_value) * 255  # Normalize and convert to uint8
    return image_data

root_dir='./'
data_read=pd.read_hdf(root_dir+'Champ_dic.h5',key='data')

image_feats={}
for i in tqdm(list(data_read.iloc[:,0])):
    file_path = root_dir+'/RI_files/'+i
    dicom_image = load_dicom_image(file_path)
    pil_image = Image.fromarray(dicom_image, mode="L")
    feats=torch_feats(pil_image)
    image_feats[i]=feats
    
image_feats_df=pd.DataFrame.from_dict(image_feats, orient='index')
image_feats_df.to_hdf('torch_image_feats.h5', key='data', mode='w')