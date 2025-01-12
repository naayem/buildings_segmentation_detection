from detectron2.utils.logger import setup_logger

setup_logger()

# import some common libraries
import numpy as np
import os, json, cv2
from pathlib import Path

# import some common detectron2 utilities
from detectron2 import model_zoo
from detectron2.config import get_cfg
from detectron2.data import MetadataCatalog, DatasetCatalog
from detectron2.engine import DefaultTrainer
from detectron2.structures import BoxMode



def get_building_dicts(img_dir):
    '''
        Reads the "via_region_data.json" file. File must respect the format of json output from via 2.0 annotation tool
        Otherwise new function must be written for new formats
    '''
    # if your dataset is in COCO format, this cell can be replaced by the following three lines:
    # from detectron2.data.datasets import register_coco_instances
    # register_coco_instances("my_dataset_train", {}, "json_annotation_train.json", "path/to/image/dir")
    # register_coco_instances("my_dataset_val", {}, "json_annotation_val.json", "path/to/image/dir")

    json_file = os.path.join(img_dir, "via_region_data.json")
    with open(json_file) as f:
        imgs_anns = json.load(f)

    dataset_dicts = []

    # here we set 'masonry', 'm6', 'rcw' as a same class 'building'
    dict_category_id = {
      'opening':0,
      'masonry':1,
      'm6':1,
      'rcw':1
    }

    for idx, v in enumerate(imgs_anns.values()):
        record = {}
        
        filename = os.path.join(img_dir, v["filename"])
        height, width = cv2.imread(filename).shape[:2]
        
        record["file_name"] = filename
        record["image_id"] = idx
        record["height"] = height
        record["width"] = width
      
        annos = v["regions"]
        objs = []
        # since we use VIA 2.0 tool， annos is a list not a set
        for idx, anno in enumerate(annos):

            # assert not anno["region_attributes"]
            #  record category_id
            category_id = dict_category_id[anno["region_attributes"]['class_name']]
            anno = anno["shape_attributes"]
            print(anno)
            px = anno["all_points_x"]
            if len(px)<4:
                print(len(px))
                print(filename)
            py = anno["all_points_y"]
            poly = [(x + 0.5, y + 0.5) for x, y in zip(px, py)]
            poly = [p for x in poly for p in x]

            obj = {
                "bbox": [np.min(px), np.min(py), np.max(px), np.max(py)],
                "bbox_mode": BoxMode.XYXY_ABS,
                "segmentation": [poly],
                "category_id": category_id,
            }
            objs.append(obj)
        record["annotations"] = objs
        dataset_dicts.append(record)
    return dataset_dicts

def add_to_catalog(gen_cfg):
    '''
        Add the datasets to Detecron2 catalog.
        Outputs building_metadata for Visualizer
    '''
    print(gen_cfg.DETECTRON.CATALOG)

    # add the dict to Catalog
    DatasetCatalog.clear()
    for d in gen_cfg.DETECTRON.CATALOG:
        print(gen_cfg.TRAINING.DATASET_DIR+'/' + d)
        DatasetCatalog.register("building_" + d, lambda d=d: get_building_dicts(gen_cfg.TRAINING.DATASET_DIR+'/' + d))
        building_metadata = MetadataCatalog.get("building_" + d).set(thing_classes=["opening","building"])
    return building_metadata

def cfg_detectron(gen_cfg):
    '''
        Separate detectron2 configurations from general configurations
        Outputs detec_cfg for Detecton2 configurations 
    '''
    if gen_cfg.DETECTRON.STEPS == None : gen_cfg.DETECTRON.STEPS = []
    print(gen_cfg.DETECTRON.STEPS)

    detec_cfg = get_cfg()
    detec_cfg.merge_from_file(model_zoo.get_config_file(gen_cfg.DETECTRON.MODEL_ZOO))
    detec_cfg.MODEL.DEVICE = f"cuda:{gen_cfg.GPUS}"
    detec_cfg.DATASETS.TRAIN = tuple(gen_cfg.TRAINING.CATALOG)
    detec_cfg.DATASETS.TEST = ()
    detec_cfg.DATALOADER.NUM_WORKERS = gen_cfg.DETECTRON.NUM_WORKERS
    detec_cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url(gen_cfg.DETECTRON.WEIGHTS)  # Let training initialize from model zoo
    detec_cfg.SOLVER.IMS_PER_BATCH = gen_cfg.DETECTRON.IMS_PER_BATCH
    detec_cfg.SOLVER.BASE_LR = gen_cfg.DETECTRON.BASE_LR  # pick a good LR
    detec_cfg.SOLVER.MAX_ITER = int(gen_cfg.DETECTRON.EPOCH*gen_cfg.DETECTRON.TOTAL_NUM_IMAGES/detec_cfg.SOLVER.IMS_PER_BATCH-1)     # 300 iterations seems good enough for this toy dataset; you will need to train longer for a practical dataset
    detec_cfg.SOLVER.STEPS = list(gen_cfg.DETECTRON.STEPS)        # do not decay learning rate
    detec_cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = gen_cfg.DETECTRON.BATCH_SIZE_PER_IMAGE   # faster, and good enough for this toy dataset (default: 512)
    detec_cfg.MODEL.ROI_HEADS.NUM_CLASSES = gen_cfg.DETECTRON.NUM_CLASSES  # 2 class ("opening","masonry","m6","rcw"). (see https://detectron2.readthedocs.io/tutorials/datasets.html#update-the-config-for-new-datasets)
    # NOTE: this config means the number of classes, but a few popular unofficial tutorials incorrect uses num_classes+1 here.

    output_dir = gen_cfg.OUTPUT_DIR
    exp_foldername = gen_cfg.EXP_NAME
    final_output_dir = f'{output_dir}/{exp_foldername}'
    final_output_dir = gen_cfg.TRAINING.TARGET_PATH

    detec_cfg.OUTPUT_DIR = final_output_dir
    os.makedirs(detec_cfg.OUTPUT_DIR, exist_ok=True)
    return detec_cfg

def train_detectron(detec_cfg):
    '''
        Training function following detec_cfg configurations
    '''
    trainer = DefaultTrainer(detec_cfg) 
    trainer.resume_or_load(resume=False)
    trainer.train()
    return