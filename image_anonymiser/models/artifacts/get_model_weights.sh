#!/bin/sh

path="$0"
DIR_PATH=$(dirname "$path")

DETECTRON_URL=https://dl.fbaipublicfiles.com/detectron2/COCO-PanopticSegmentation/panoptic_fpn_R_50_3x/139514569/model_final_c10459.pkl
OCR_DETECTOR_URL=https://github.com/JaidedAI/EasyOCR/releases/download/pre-v1.1.6/craft_mlt_25k.zip
OCR_RECOGNISER_URL=https://github.com/JaidedAI/EasyOCR/releases/download/v1.3/english_g2.zip
TMPFILE=tmp

wget -q -O "$DIR_PATH"/model_final_c10459.pkl "$DETECTRON_URL"
wget -q -O "$DIR_PATH"/"$TMPFILE" "$OCR_DETECTOR_URL"
unzip -d "$DIR_PATH"/. "$DIR_PATH"/"$TMPFILE"
wget -q -O "$DIR_PATH"/"$TMPFILE" "$OCR_RECOGNISER_URL"
unzip -d "$DIR_PATH"/. "$DIR_PATH"/"$TMPFILE"
rm "$DIR_PATH"/"$TMPFILE"