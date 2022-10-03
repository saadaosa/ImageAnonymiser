## Adding new detector models:

- Any new model should implement the `detect` method and return a `dict` that contains all the information required as described in `detectors.DetectionModel` 

<br>

- To be used in the app, a model config should be included in the `detectors` section of [config.yml](../backend/config.yml):
  ```yaml
    - class: Name of the python class in `models.detectors`
      name: Name of the model in the app
      description: Description of the model; will be included in the help tab of the app (model cards)
      url: Endpoint url (if null, local backend is used)
      params: Parameters used to create the model object (passed to init)
  ```

<br>

- There is no update required to the front-end. The backend will instanciate the detector and add it to the models available in the app

<br>

- For Detectron2-based models, a `weights_file_name` parameter can be set to the name of the file containing the weights (use case: models that are finetuned). The file should be placed in a folder called `artifacts` in `models`