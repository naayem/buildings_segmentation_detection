# import some common libraries
import os, cv2
import json

# import some common detectron2 utilities
from detectron2.engine import DefaultPredictor
from detectron2.utils.visualizer import Visualizer
from detectron2.utils.visualizer import ColorMode

from deep_vitabuild.utils.detectron2via import wrap_jsonVia, convert_annot_detectron2via_RDP, convert_bbox_detectron2lightly

def inference_detectron_full(detec_cfg, gen_cfg, building_metadata):
    DATASET_DIR = gen_cfg.INFERENCE.DATASET_PATH
    TARGET_PATH = gen_cfg.INFERENCE.TARGET_PATH

    # Inference should use the config with parameters that are used in training
    # detec_cfg now already contains everything we've set previously. We changed it a little bit for inference:
    detec_cfg.MODEL.WEIGHTS = gen_cfg.INFERENCE.WEIGHTS  # path to the model we just trained
    detec_cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = gen_cfg.INFERENCE.SCORE_THRESH_TEST   # set a custom testing threshold
    predictor = DefaultPredictor(detec_cfg)

    os.makedirs(TARGET_PATH, exist_ok=True)
    
    print(next(os.walk(DATASET_DIR))[1])

    for folder in next(os.walk(DATASET_DIR))[1]:
        folder_path = DATASET_DIR+'/'+folder
        for filename in os.listdir(folder_path):
            if filename.endswith(".jpg"):
                im = cv2.imread(folder_path+'/'+filename)
                outputs = predictor(im)  # format is documented at https://detectron2.readthedocs.io/tutorials/models.html#model-output-format
                v = Visualizer(im[:, :, ::-1],
                            metadata=building_metadata, 
                            scale=0.5, 
                            instance_mode=ColorMode.IMAGE_BW   # remove the colors of unsegmented pixels. This option is only available for segmentation models
                )
                out = v.draw_instance_predictions(outputs["instances"].to("cpu"))

                img_name = 'inference_on_'+filename
                savepath = TARGET_PATH + img_name
                cv2.imwrite(savepath, out.get_image()[:, :, ::-1])
    
    return detec_cfg

def inference_detectron_folder(detec_cfg, gen_cfg, building_metadata):
    DATASET_DIR = gen_cfg.INFERENCE.DATASET_PATH
    TARGET_PATH = gen_cfg.INFERENCE.TARGET_PATH

    # Inference should use the config with parameters that are used in training
    # detec_cfg now already contains everything we've set previously. We changed it a little bit for inference:
    detec_cfg.MODEL.WEIGHTS = gen_cfg.INFERENCE.WEIGHTS  # path to the model we just trained
    detec_cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = gen_cfg.INFERENCE.SCORE_THRESH_TEST   # set a custom testing threshold
    predictor = DefaultPredictor(detec_cfg)
    
    os.makedirs(TARGET_PATH, exist_ok=True)
    
    via_dict = {}
    for filename in os.listdir(DATASET_DIR):
        if filename.endswith(".jpg"):
            size = os.path.getsize(DATASET_DIR+'/'+filename)
            im = cv2.imread(DATASET_DIR+'/'+filename)

            outputs = predictor(im)  # format is documented at https://detectron2.readthedocs.io/tutorials/models.html#model-output-format
            v = Visualizer(im[:, :, ::-1],
                        metadata=building_metadata, 
                        scale=0.5, 
                        instance_mode=ColorMode.IMAGE_BW   # remove the colors of unsegmented pixels. This option is only available for segmentation models
            )
            out = v.draw_instance_predictions(outputs["instances"].to("cpu"))
            
            output_via = convert_annot_detectron2via_RDP(filename, outputs, size)
            via_dict.update(output_via)

            img_name = 'inference_on_'+filename
            savepath = TARGET_PATH + img_name

            cv2.imwrite(savepath, out.get_image()[:, :, ::-1])

    jsonpath = TARGET_PATH + 'data.json'
    wrapped = wrap_jsonVia(via_dict)
    with open(jsonpath, 'w') as fp:
        json.dump(wrapped, fp,  indent=4)

    return detec_cfg