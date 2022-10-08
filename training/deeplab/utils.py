import json
from detectron2.data import DatasetCatalog, MetadataCatalog


def get_lapa_data_dicts(json_file):
    with open(json_file, "r") as f:
        _obj = json.load(f)
    return _obj

def get_lapa_file_name(split, file_name_format):
    return file_name_format.format(split)

def register_lapa_dataset(file_name_format=""):
    for split in ["train", "val", "test"]:
        if "lapa_"+split in DatasetCatalog.list():
            continue
        DatasetCatalog.register("lapa_" + split, lambda split=split, file_name_format=file_name_format: get_lapa_data_dicts(get_lapa_file_name(split, file_name_format)))
        MetadataCatalog.get("lapa_" + split).set(stuff_classes=["background","skin","hair"], 
                                                 stuff_colors=[(0,0,0),(0,153,255),(255, 0, 102)],
                                                 evaluator_type="sem_seg",
                                                 ignore_label=11,)
