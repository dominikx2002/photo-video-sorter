import re

PHOTO_EXT = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.tif', '.tiff',
             '.webp', '.bmp', '.gif', '.dng', '.raw', '.cr2', '.nef', '.arw', '.orf', '.rw2'}
VIDEO_EXT = {'.mp4', '.mov', '.m4v', '.avi', '.mkv', '.3gp', '.mts', '.m2ts', '.wmv', '.flv'}
MEDIA_EXT = PHOTO_EXT | VIDEO_EXT

THEME_COLOR = '#D97757'

FOLDER_DATE_RE = re.compile(r'(20\d{2})[-_]?(0[1-9]|1[0-2])')