## 👻 Guide: Configuration 

This guide will help you in understanding the configuration file and changing/adding functionalities in the application

### The configuration file

The configuration file currently has 5 main sections:

- **predictor**: This is where you specify the predictor `type` i.e. **inapp** inference or **api** (using a FastAPI endpoint)
<br>

- **anonymiser**: Used to specify the minimum and maximum kernel values for the blur (`min_blur_intensity` and `max_blur_intensity`) 
<br>

- **detectors**: Contains the list of detectors (based on the classes in `image_anonymiser/models/detectors.py`). Each detector should have the following elements:
  ```yaml
    - class: [required] Name of the python class in image_anonymiser/models/detectors.py
      name: [required] Name of the model as displayed in the frontend
      description: [required] Description of the model
      params: [optional] Parameters used to instantiate the model object (passed to the init function of the model class)
  ```

- **file_io**: Used to specify the names of the folders used to store app data
<br>

- **visualizer**: This is where you specify the name of the visualisation `class` in `image_anonymiser/backend/visualizer.py`

### Adding new functionalities

Here is a list of possible additions to the code base that require minimal and sometimes no adjustments to the other modules:

- Implementing a new visualisation class in `image_anonymiser/backend/visualizer.py`; the new class can then be activated in the config file
<br>

- Adding/removing models from the web app:
  - To be available in the web app, a model needs to have a config as specified above. If the config is removed, the model won't be available
  - You can add several `flavors` of the same model e.g. different initialisation parameters (which can be for instance useful in testing mode)
  - To add a new model class: 
    - The implementation should be added to `image_anonymiser/models/detectors.py`. The model should have a `detect` method and return a prediction `dict` that contains all the information required as described in the abstract class `detectors.DetectionModel`
    - The model configuration needs to be added to the config file. There is no update required to the front-end. The backend will instantiate the detector and add it to the models available in the app 
<br>

- Implement a new `file_io` backend (e.g. to store the data in the cloud)

You can even implement a new anonymisation feature since the detection and anonymisation are two different steps, but this will probably require also some changes in the frontend (to add the input parameters required for the new feature)
