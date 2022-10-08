
# check if detectron folder has been cloned
DIR="./detectron"
if [ ! -d "$DIR" ]; then
  git clone https://github.com/facebookresearch/detectron2.git
  mv detectron2 detectron
fi

export PYTHONPATH="./:./detectron/projects/DeepLab/"