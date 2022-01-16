# Building instance segementation and Building type detection



## Content

`code`: all the code used in this project

`dataset`: introduction of dataset 

`experiments`: .yaml files with all configurations needed to run the code

`files`: presentation and reports

`output`: output directory for any outputs from the code

`Laxiang_old`: code from previous project


**Note**: please download the zip files in the release section, unzip `data.zip` and put this folder in `code/data`; unzip `annotated_data.zip` and put this folder in `dataset/annotated_data`;  


## Introduction

This project use deep learning model mask rcnn to detect the builidng instance, openings and building type.

This project is mainly divided into **six tasks**:

- Segments transfer
- Training
- Validation
- Inferences
- Active Learning
- Floor Detection





#################################

## The core of the project is a custom yet functional approach to detectron2.

Aims at making detecton2 application more handy and clear.

It comprises of experiment description (.yaml dictionary files), starting point file (`main.py`) and the `deep_vitabuild` directory. The latter includes:

- `model1`: All functions needed for Floor Detections
- `procedures`: All functions needed for Training, Validation, Inference, Active Learning
- `utils`: Additional utilities, e.g. visualization, detectron to via conversions etc..



