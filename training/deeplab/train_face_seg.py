import wandb
import pickle
from utils import register_lapa_dataset
from detectron2.data import DatasetCatalog
from detectron.projects.DeepLab.train_net import default_argument_parser, launch, main, setup
from config import LAPA_DATA_FILE_NAME_FORMAT


if __name__ == "__main__":
    register_lapa_dataset(LAPA_DATA_FILE_NAME_FORMAT)
    args = default_argument_parser().parse_args()
    wandb.init(
        entity="fsdl_2022",
        project="face-seg",
        config=args,
        sync_tensorboard=True,
    )
    print("Command Line Args:", args)
    assert len(DatasetCatalog.get("lapa_train")) == 18168
    cfg = setup(args)
    launch(
        main,
        args.num_gpus,
        num_machines=args.num_machines,
        machine_rank=args.machine_rank,
        dist_url=args.dist_url,
        args=(args,),
    )
    # log model to wandb
    pickle.dump(cfg, open(cfg.OUTPUT_DIR+"/model_final_cfg.pkl","wb"))
    artifact_model = wandb.Artifact("model_final.pth", "model")
    artifact_cfg = wandb.Artifact("model_final_cfg.pkl", "model-config")
    artifact_cfg.add_file(cfg.OUTPUT_DIR+"/model_final_cfg.pkl")
    artifact_model.add_file(cfg.OUTPUT_DIR+"/model_final.pth")
    artifact_cfg.save()
    artifact_model.save()
    wandb.finish()


