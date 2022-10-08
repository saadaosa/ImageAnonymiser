### Preparing data
* Download the LaPa dataset from https://github.com/JDAI-CV/lapa-dataset 
* Update `config.py` to use valid paths to the dataset
* Run the `lapa_data_prep.py` script; `python lapa_data_prep.py --split all --save`

### Training
* First run the script `train_setup.sh`; `source train_setup.sh`
* Update the config in `deeplab_config.yaml` if desired; possible parameters to adjust are `MAX_ITER` and `IMS_PER_BATCH`
* Run the script `train_face_seg.py` to train; `python train_face_seg.py --config-file deeplab_config.yaml --num-gpus 2`
* trained model is uploaded to weights and biases
