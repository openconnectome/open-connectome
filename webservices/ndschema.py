import json
from jsonspec.validators import load

CHANNEL_SCHEMA = load( {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "Schema for Channel JSON object for ingest",
    "type": "object",
    "properties": {
        "channel_name": {
            "description": "Channel name for the channel",
            "type": "string",
            "pattern": "^[^$&+,:;=?@#|'<>.^*()%!-]+$"
        },
        "datatype": {
            "description": "Datatype of the channel",
            "enum": ["uint8", "uint16", "uint32", "uint64", "float32"],
            "pattern": "^(uint8|uint16|uint32|uint64|float32)$"
        },
        "channel_type": {
            "description": "Type of Scaling - Isotropic(1) or Normal(0)",
            "enum": ["image", "annotation", "probmap", "timeseries"],
            "pattern": "^(image|annotation|probmap|timeseries)$"
        },
        "exceptions": {
            "description": "Enable exceptions - Yes(1) or No(0) (for annotation data)",
            "type": "integer"
        },
        "resolution": {
            "description": "Start Resolution (for annotation data)",
            "type": "integer"
        },
        "windowrange": {
            "description": "Window clamp function for 16-bit channels with low max value of pixels",
            "type": "array",
            "pattern": "^\\([0-9]+,[0-9]+\\)$"
        },
        "readonly": {
            "description": "Read-only Channel(1) or Not(0). You can remotely post to channel if it is not readonly and overwrite data",
            "type": "integer"
        },
        "data_url": {
            "description": "This url points to the root directory of the files. Dropbox is not an acceptable HTTP Server.",
            "type": "string",
            "pattern": "^http:\/\/.*\/"
        },
        "file_format": {
            "description": "This is the file format type. For now we support only Slice stacks and CATMAID tiles.",
            "enum": ["SLICE", "CATMAID"],
            "pattern": "^(SLICE|CATMAID)$"
        },
        "file_type": {
            "description": "This the file type the data is stored in",
            "enum": ["tif", "png", "tiff"],
            "pattern": "^(tif|png|tiff)$"
        },
    },
    "required": ["channel_name", "channel_type", "data_url", "datatype", "file_format", "file_type"]
} )

DATASET_SCHEMA = load( {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "Schema for Dataset JSON object for ingest",
    "type": "object",
    "properties": {
        "dataset_name": {
            "description": "The name of the dataset",
            "type": "string",
            "pattern": "^[^$&+,:;=?@#|'<>.^*()%!-]+$"
        },
        "imagesize": {
            "type": "array",
            "description": "The image dimensions of the dataset",
            "pattern": "^\\([0-9]+,[0-9]+,[0-9]+\\)$"
        },
        "voxelres": {
            "type": "array",
            "description": "The voxel resolutoin of the data",
            "pattern": "^\\([0-9]+\\.[0-9]+,[0-9]+\\.[0-9]+,[0-9]+\\.[0-9]+\\)$"
        },
        "offset": {
            "type": "array",
            "description": "The dimensions offset from origin",
            "pattern": "^\\([0-9]+,[0-9]+,[0-9]+\\)$"
        },
        "timerange": {
            "description": "The timerange of the data",
            "type": "array",
            "pattern": "^\\([0-9]+,[0-9]+\\)$"
        },
        "scalinglevels": {
            "description": "Required Scaling levels/ Zoom out levels",
            "type": "integer"
        },
        "scaling": {
            "description": "Type of Scaling - Isotropic(1) or Normal(0)",
            "type": "integer"
        },
    },
    "required": ["dataset_name", "imagesize", "voxelres"]
} )

PROJECT_SCHEMA = load( {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "Schema for Dataset JSON object for ingest",
    "type": "object",
    "properties": {
        "project_name": {
            "description": "The name of the project",
            "type": "string",
            "pattern": "^[^$&+,:;=?@#|'<>.^*()%!-]+$"
        },
        "public": {
            "description": "Whether or not the project is publicly viewable, by default not",
            "type": "integer"
        },
        "token_name":  {
            "description": "The token name for the project, by default same as project_name",
            "type": "string",
            "pattern": "^[^$&+,:;=?@#|'<>.^*()%!-]+$"
        },
    },
    "required": ["project_name"]
} )
