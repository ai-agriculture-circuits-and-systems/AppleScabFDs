#!/usr/bin/env python3
"""
标准化 AppleScabFDs 数据集结构
这是一个分类数据集（healthy/scab），按照标准化规范重组
在apples目录下创建healthy和scab子目录以体现分类结果
"""

import json
import csv
import shutil
import random
from pathlib import Path
from PIL import Image

def create_labelmap(output_path: Path):
    """创建包含两个类别的labelmap.json"""
    labelmap = [
        {
            "object_id": 0,
            "label_id": 0,
            "keyboard_shortcut": "0",
            "object_name": "background"
        },
        {
            "object_id": 1,
            "label_id": 1,
            "keyboard_shortcut": "1",
            "object_name": "healthy"
        },
        {
            "object_id": 2,
            "label_id": 2,
            "keyboard_shortcut": "2",
            "object_name": "scab"
        }
    ]
    output_path.write_text(json.dumps(labelmap, indent=2), encoding='utf-8')
    print(f"创建 labelmap.json: {output_path}")

def json_to_csv(json_path: Path, csv_path: Path, img_width: int, img_height: int, category_id: int):
    """从JSON标注转换为CSV格式（分类任务，使用全图边界框）"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        annotations = data.get('annotations', [])
        rows = []
        
        # 如果是分类任务，创建一个覆盖全图的边界框
        if not annotations:
            # 创建全图边界框用于分类标注
            rows.append({
                'item': 0,
                'x': 0,
                'y': 0,
                'width': img_width,
                'height': img_height,
                'label': category_id
            })
        else:
            # 如果有标注，使用第一个标注
            for idx, ann in enumerate(annotations):
                bbox = ann.get('bbox', [])
                if len(bbox) == 4:
                    rows.append({
                        'item': idx,
                        'x': bbox[0],
                        'y': bbox[1],
                        'width': bbox[2],
                        'height': bbox[3],
                        'label': category_id
                    })
                elif not bbox:
                    # 如果没有边界框，创建全图边界框
                    rows.append({
                        'item': idx,
                        'x': 0,
                        'y': 0,
                        'width': img_width,
                        'height': img_height,
                        'label': category_id
                    })
        
        if rows:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['item', 'x', 'y', 'width', 'height', 'label'])
                writer.writeheader()
                writer.writerows(rows)
        else:
            # 默认全图边界框
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['item', 'x', 'y', 'width', 'height', 'label'])
                writer.writeheader()
                writer.writerow({
                    'item': 0,
                    'x': 0,
                    'y': 0,
                    'width': img_width,
                    'height': img_height,
                    'label': category_id
                })
    except Exception as e:
        print(f"转换 {json_path} 时出错: {e}")
        csv_path.write_text('#item,x,y,width,height,label\n', encoding='utf-8')

def create_splits(healthy_dir: Path, scab_dir: Path, sets_dir: Path, train_ratio=0.7, val_ratio=0.15, seed=42):
    """创建数据集划分文件，分别处理healthy和scab类别"""
    sets_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取healthy图像
    healthy_images = []
    for img_file in healthy_dir.glob('*.jpg'):
        healthy_images.append(img_file.stem)
    for img_file in healthy_dir.glob('*.JPG'):
        healthy_images.append(img_file.stem)
    for img_file in healthy_dir.glob('*.png'):
        healthy_images.append(img_file.stem)
    
    # 获取scab图像
    scab_images = []
    for img_file in scab_dir.glob('*.jpg'):
        scab_images.append(img_file.stem)
    for img_file in scab_dir.glob('*.JPG'):
        scab_images.append(img_file.stem)
    for img_file in scab_dir.glob('*.png'):
        scab_images.append(img_file.stem)
    
    random.seed(seed)
    
    # 分别划分healthy和scab
    def split_images(images):
        random.shuffle(images)
        total = len(images)
        train_end = int(total * train_ratio)
        val_end = train_end + int(total * val_ratio)
        return images[:train_end], images[train_end:val_end], images[val_end:]
    
    healthy_train, healthy_val, healthy_test = split_images(healthy_images)
    scab_train, scab_val, scab_test = split_images(scab_images)
    
    # 合并所有类别
    train_files = healthy_train + scab_train
    val_files = healthy_val + scab_val
    test_files = healthy_test + scab_test
    all_files = healthy_images + scab_images
    
    # 打乱合并后的列表
    random.shuffle(train_files)
    random.shuffle(val_files)
    random.shuffle(test_files)
    
    (sets_dir / 'train.txt').write_text('\n'.join(train_files) + '\n', encoding='utf-8')
    (sets_dir / 'val.txt').write_text('\n'.join(val_files) + '\n', encoding='utf-8')
    (sets_dir / 'test.txt').write_text('\n'.join(test_files) + '\n', encoding='utf-8')
    (sets_dir / 'all.txt').write_text('\n'.join(all_files) + '\n', encoding='utf-8')
    (sets_dir / 'train_val.txt').write_text('\n'.join(train_files + val_files) + '\n', encoding='utf-8')
    
    print(f"数据集划分: 训练={len(train_files)} (healthy={len(healthy_train)}, scab={len(scab_train)}), "
          f"验证={len(val_files)} (healthy={len(healthy_val)}, scab={len(scab_val)}), "
          f"测试={len(test_files)} (healthy={len(healthy_test)}, scab={len(scab_test)}), "
          f"总计={len(all_files)} (healthy={len(healthy_images)}, scab={len(scab_images)})")

def main():
    root = Path(__file__).parent.parent
    healthy_dir = root / 'Healthy'
    scab_dir = root / 'Scab'
    apples_dir = root / 'apples'
    
    # 创建标准目录结构 - 在apples下创建healthy和scab子目录
    healthy_subdir = apples_dir / 'healthy'
    scab_subdir = apples_dir / 'scab'
    
    for subdir in ['csv', 'json', 'images', 'segmentations']:
        (healthy_subdir / subdir).mkdir(parents=True, exist_ok=True)
        (scab_subdir / subdir).mkdir(parents=True, exist_ok=True)
    
    # 创建sets目录在apples根目录下
    sets_dir = apples_dir / 'sets'
    sets_dir.mkdir(parents=True, exist_ok=True)
    
    create_labelmap(apples_dir / 'labelmap.json')
    
    # 处理Healthy类别的图像
    print("处理Healthy类别...")
    healthy_count = 0
    for img_file in (healthy_dir / 'images').glob('*.jpg'):
        shutil.copy2(img_file, healthy_subdir / 'images' / img_file.name)
        healthy_count += 1
    for img_file in (healthy_dir / 'images').glob('*.JPG'):
        shutil.copy2(img_file, healthy_subdir / 'images' / img_file.name)
        healthy_count += 1
    for img_file in (healthy_dir / 'images').glob('*.png'):
        shutil.copy2(img_file, healthy_subdir / 'images' / img_file.name)
        healthy_count += 1
    
    # 处理Scab类别的图像
    print("处理Scab类别...")
    scab_count = 0
    for img_file in (scab_dir / 'images').glob('*.jpg'):
        shutil.copy2(img_file, scab_subdir / 'images' / img_file.name)
        scab_count += 1
    for img_file in (scab_dir / 'images').glob('*.JPG'):
        shutil.copy2(img_file, scab_subdir / 'images' / img_file.name)
        scab_count += 1
    for img_file in (scab_dir / 'images').glob('*.png'):
        shutil.copy2(img_file, scab_subdir / 'images' / img_file.name)
        scab_count += 1
    
    print(f"复制了 {healthy_count} 个Healthy图像和 {scab_count} 个Scab图像，总计 {healthy_count + scab_count} 个图像")
    
    # 处理JSON文件并生成CSV
    json_count = 0
    csv_count = 0
    
    # 处理Healthy的JSON文件
    for json_file in (healthy_dir / 'json').glob('*.json'):
        stem = json_file.stem
        # 查找对应的图像文件
        img_path = None
        for ext in ['.jpg', '.JPG', '.png', '.PNG']:
            test_path = healthy_subdir / 'images' / f"{stem}{ext}"
            if test_path.exists():
                img_path = test_path
                break
        
        if img_path and img_path.exists():
            with Image.open(img_path) as img:
                img_width, img_height = img.size
        else:
            # 从JSON读取尺寸
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    img_info = data.get('images', [{}])[0]
                    img_width = img_info.get('width', 1000)
                    img_height = img_info.get('height', 750)
            except:
                img_width, img_height = 1000, 750
        
        # 复制JSON
        shutil.copy2(json_file, healthy_subdir / 'json' / json_file.name)
        json_count += 1
        
        # 生成CSV（类别ID=1表示healthy）
        csv_path = healthy_subdir / 'csv' / f"{stem}.csv"
        json_to_csv(json_file, csv_path, img_width, img_height, category_id=1)
        csv_count += 1
    
    # 处理Scab的JSON文件
    for json_file in (scab_dir / 'json').glob('*.json'):
        stem = json_file.stem
        # 查找对应的图像文件
        img_path = None
        for ext in ['.jpg', '.JPG', '.png', '.PNG']:
            test_path = scab_subdir / 'images' / f"{stem}{ext}"
            if test_path.exists():
                img_path = test_path
                break
        
        if img_path and img_path.exists():
            with Image.open(img_path) as img:
                img_width, img_height = img.size
        else:
            # 从JSON读取尺寸
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    img_info = data.get('images', [{}])[0]
                    img_width = img_info.get('width', 1000)
                    img_height = img_info.get('height', 750)
            except:
                img_width, img_height = 1000, 750
        
        # 复制JSON
        shutil.copy2(json_file, scab_subdir / 'json' / json_file.name)
        json_count += 1
        
        # 生成CSV（类别ID=2表示scab）
        csv_path = scab_subdir / 'csv' / f"{stem}.csv"
        json_to_csv(json_file, csv_path, img_width, img_height, category_id=2)
        csv_count += 1
    
    print(f"处理了 {json_count} 个JSON文件，生成了 {csv_count} 个CSV文件")
    
    # 创建数据集划分
    print("\n创建数据集划分...")
    create_splits(healthy_subdir / 'images', scab_subdir / 'images', sets_dir)
    
    print("\n标准化完成！")
    print(f"数据集位置: {apples_dir}")
    print(f"结构: apples/healthy/ 和 apples/scab/")

if __name__ == '__main__':
    main()
