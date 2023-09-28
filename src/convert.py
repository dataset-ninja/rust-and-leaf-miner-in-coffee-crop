# https://www.kaggle.com/datasets/alvarole/coffee-leaves-disease

import os
import shutil
import xml.etree.ElementTree as ET
from urllib.parse import unquote, urlparse

import cv2
import numpy as np
import supervisely as sly
from dataset_tools.convert import unpack_if_archive
from dotenv import load_dotenv
from supervisely.io.fs import (
    dir_exists,
    file_exists,
    get_file_ext,
    get_file_name,
    get_file_name_with_ext,
    get_file_size,
    mkdir,
    remove_dir,
)
from tqdm import tqdm

import src.settings as s


def download_dataset(teamfiles_dir: str) -> str:
    """Use it for large datasets to convert them on the instance"""
    api = sly.Api.from_env()
    team_id = sly.env.team_id()
    storage_dir = sly.app.get_data_dir()

    if isinstance(s.DOWNLOAD_ORIGINAL_URL, str):
        parsed_url = urlparse(s.DOWNLOAD_ORIGINAL_URL)
        file_name_with_ext = os.path.basename(parsed_url.path)
        file_name_with_ext = unquote(file_name_with_ext)

        sly.logger.info(f"Start unpacking archive '{file_name_with_ext}'...")
        local_path = os.path.join(storage_dir, file_name_with_ext)
        teamfiles_path = os.path.join(teamfiles_dir, file_name_with_ext)

        fsize = api.file.get_directory_size(team_id, teamfiles_dir)
        with tqdm(
            desc=f"Downloading '{file_name_with_ext}' to buffer...",
            total=fsize,
            unit="B",
            unit_scale=True,
        ) as pbar:        
            api.file.download(team_id, teamfiles_path, local_path, progress_cb=pbar)
        dataset_path = unpack_if_archive(local_path)

    if isinstance(s.DOWNLOAD_ORIGINAL_URL, dict):
        for file_name_with_ext, url in s.DOWNLOAD_ORIGINAL_URL.items():
            local_path = os.path.join(storage_dir, file_name_with_ext)
            teamfiles_path = os.path.join(teamfiles_dir, file_name_with_ext)

            if not os.path.exists(get_file_name(local_path)):
                fsize = api.file.get_directory_size(team_id, teamfiles_dir)
                with tqdm(
                    desc=f"Downloading '{file_name_with_ext}' to buffer...",
                    total=fsize,
                    unit="B",
                    unit_scale=True,
                ) as pbar:
                    api.file.download(team_id, teamfiles_path, local_path, progress_cb=pbar)

                sly.logger.info(f"Start unpacking archive '{file_name_with_ext}'...")
                unpack_if_archive(local_path)
            else:
                sly.logger.info(
                    f"Archive '{file_name_with_ext}' was already unpacked to '{os.path.join(storage_dir, get_file_name(file_name_with_ext))}'. Skipping..."
                )

        dataset_path = storage_dir
    return dataset_path
    
def count_files(path, extension):
    count = 0
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(extension):
                count += 1
    return count
    
def convert_and_upload_supervisely_project(
    api: sly.Api, workspace_id: int, project_name: str
) -> sly.ProjectInfo:

    # project_name = "Disease and pest in coffee leaves"
    dataset_path = "/home/grokhi/rawdata/rust-and-leaf-miner-in-coffee-crop"

    images_ext = ".jpg"
    masks_ext = ".xml"
    batch_size = 30

    ds_name = "ds"


    def create_ann(image_path):
        labels = []

        image_np = sly.imaging.image.read(image_path)[:, :, 0]
        img_height = image_np.shape[0]
        img_width = image_np.shape[1]

        ann_path = os.path.join(curr_ds_path, get_file_name(image_path) + ".xml")

        tree = ET.parse(ann_path)
        root = tree.getroot()
        # img_height = int(root.find(".//height").text)
        # img_width = int(root.find(".//width").text)
        objects_content = root.findall(".//object")
        for obj_data in objects_content:
            name = obj_data.find(".//name").text
            if name == "ferrugemw":
                name = "ferrugem"
            bndbox = obj_data.find(".//bndbox")
            top = int(bndbox.find(".//ymin").text)
            left = int(bndbox.find(".//xmin").text)
            bottom = int(bndbox.find(".//ymax").text)
            right = int(bndbox.find(".//xmax").text)

            rectangle = sly.Rectangle(top=top, left=left, bottom=bottom, right=right)
            obj_class = name_to_class.get(name)
            label = sly.Label(rectangle, obj_class)
            labels.append(label)

        return sly.Annotation(img_size=(img_height, img_width), labels=labels)


    obj_class_bicho_mineiro = sly.ObjClass("leaf miner", sly.Rectangle)
    obj_class_ferrugem = sly.ObjClass("rust", sly.Rectangle)

    name_to_class = {"bicho_mineiro": obj_class_bicho_mineiro, "ferrugem": obj_class_ferrugem}

    project = api.project.create(workspace_id, project_name, change_name_if_conflict=True)
    meta = sly.ProjectMeta(obj_classes=[obj_class_bicho_mineiro, obj_class_ferrugem])
    api.project.update_meta(project.id, meta.to_json())

    dataset = api.dataset.create(project.id, ds_name, change_name_if_conflict=True)

    for folder_name in os.listdir(dataset_path):
        curr_ds_path = os.path.join(dataset_path, folder_name)

        if dir_exists(curr_ds_path):
            
            images_names = [
                im_name for im_name in os.listdir(curr_ds_path) if get_file_ext(im_name) == images_ext
            ]

            progress = sly.Progress("Create dataset {}".format(folder_name), len(images_names))

            for img_names_batch in sly.batched(images_names, batch_size=batch_size):
                img_pathes_batch = [os.path.join(curr_ds_path, im_name) for im_name in img_names_batch]

                # TODO =========================== must have, check EXIF Rotate 180 =========================
                temp_img_pathes_batch = []
                temp_folder = os.path.join(curr_ds_path, "temp")
                mkdir(temp_folder)
                for im_path in img_pathes_batch:
                    temp_img = cv2.imread(
                        im_path,
                        flags=cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH | cv2.IMREAD_IGNORE_ORIENTATION,
                    )
                    new_img_path = os.path.join(temp_folder, get_file_name_with_ext(im_path))
                    temp_img_pathes_batch.append(new_img_path)
                    cv2.imwrite(new_img_path, temp_img)

                # TODO =======================================================================================

                img_infos = api.image.upload_paths(dataset.id, img_names_batch, temp_img_pathes_batch)
                img_ids = [im_info.id for im_info in img_infos]

                anns = [create_ann(image_path) for image_path in temp_img_pathes_batch]
                api.annotation.upload_anns(img_ids, anns)

                remove_dir(temp_folder)

                progress.iters_done_report(len(img_names_batch))
    return project


