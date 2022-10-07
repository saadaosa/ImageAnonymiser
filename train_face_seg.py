import wandb
from image_anonymiser.utils import register_lapa_dataset
from detectron.projects.DeepLab.train_net import default_argument_parser, launch, main

LAPA_DATA_FILE_NAME_FORMAT =  "/home/team_003/Data/LaPa/json/{}.json"


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
    launch(
        main,
        args.num_gpus,
        num_machines=args.num_machines,
        machine_rank=args.machine_rank,
        dist_url=args.dist_url,
        args=(args,),
    )
    wandb.finish()


