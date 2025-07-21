# AppleScabFDs Dataset

A dataset of apple images showing healthy fruits and fruits infected by scab, collected from different locations in Latvia.

## Dataset Description

The AppleScabFDs dataset is designed for apple scab detection tasks. It contains images grouped into two categories: "Healthy" and "Scab". This dataset is suitable for image classification, transfer learning, and developing mobile applications for plant disease detection.

- **Categories**: Healthy and Scab
- **Image sources**: Smartphone cameras (12 MP, 13 MP, 48 MP) and a digital compact camera (10 MP)
- **Collection conditions**: Field conditions in orchards

## Data Collection

- **Location**: Various locations in Latvia
- **Collection time**: Images were taken at three different stages of the day:
  - Morning (9:00-10:00)
  - Around noon (12:00-14:00)
  - Evening (16:00-17:00)
- **Lighting conditions**: Both sunny days and overcast days to provide different types of light (soft light and hard light)
- **Composition**: Leaves were framed to occupy the image area as much as possible and centered in the image
- **Multiple perspectives**: The same object was photographed from multiple viewpoints

## Dataset Structure

The dataset is organized as follows:

```
AppleScabFDs/
├── Healthy/
│   ├── IMG_0001.JPG
│   ├── IMG_0001.json
│   ├── IMG_0002.JPG
│   ├── IMG_0002.json
│   └── ...
├── Scab/
│   ├── IMG_1001.JPG
│   ├── IMG_1001.json
│   ├── IMG_1002.JPG
│   ├── IMG_1002.json
│   └── ...
└── generate_annotations.py
```

- `Healthy/` and `Scab/` folders contain images of healthy apples and apples infected by scab, respectively.
- Each image has a corresponding JSON annotation file with the same name (only the extension differs).
- The annotation files are generated in COCO-style format.

## Annotation File Explanation

Each image has a corresponding annotation file (e.g., `IMG_0001.json`) with the following structure:

```
{
  "info": { ... },
  "images": [
    {
      "id": <10-digit unique id>,
      "width": <image width>,
      "height": <image height>,
      "file_name": "IMG_0001.JPG",
      "size": <file size in bytes>,
      "format": "JPG",
      "url": "",
      "hash": "",
      "status": "success"
    }
  ],
  "annotations": [],
  "categories": [
    {
      "id": 1000000000, // for healthy
      "name": "healthy",
      "supercategory": "applescabfds"
    }
  ]
}
```

- **info**: Dataset meta information (description, version, license, etc.).
- **images**: List containing metadata for the image (id, width, height, file name, size, format, etc.).
- **annotations**: Annotation list (empty if no object-level annotation is provided).
- **categories**: Only contains the category for the current image (either healthy or scab). The `id` is 1000000000 for healthy, 1000000001 for scab. The `supercategory` is always `applescabfds`.

## Applications

This dataset can be used for:
- Apple scab detection
- Plant disease classification
- Transfer learning
- Computer vision research
- Deep learning model training
- Agricultural AI applications

## Categories

- Computer Science
- Artificial Intelligence
- Computer Vision
- Image Classification
- Transfer Learning
- Plant Pathology
- Agriculture
- Deep Learning

## Citation

```
Kodors, S., Lacis, G., Sokolova, O., Zhukovs, V., Apeinans, I., & Bartulsons, T. (2021). Apple Scab Detection using CNN and Transfer Learning. Agronomy Research, 19(2), 507–519. doi: 10.15159/AR.21.045
```

## License

This dataset is licensed under the Creative Commons Attribution 4.0 International License (CC BY 4.0).

## Source

The dataset is available at:
- [Kaggle Dataset](https://www.kaggle.com/datasets/projectlzp201910094/applescabfds)
- [Papers with Code](https://paperswithcode.com/dataset/applescabfds) 