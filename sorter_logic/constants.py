import re

# Comprehensive image formats: common raster, HEIF/AVIF/JXL, and camera RAW
# formats across every major manufacturer.
PHOTO_EXT = {
    # common raster
    '.jpg', '.jpeg', '.jpe', '.jfif', '.jif', '.png', '.apng', '.gif',
    '.bmp', '.dib', '.tif', '.tiff', '.webp', '.heic', '.heif', '.hif',
    '.avif', '.jxl', '.jp2', '.j2k', '.jpf', '.jpx', '.jpm',
    # editor / exchange / other
    '.psd', '.psb', '.tga', '.ico', '.cur', '.dds', '.exr', '.hdr',
    '.svg', '.svgz', '.pbm', '.pgm', '.ppm', '.pnm', '.xbm', '.xpm', '.ras',
    # camera RAW (Canon, Nikon, Sony, Fuji, Olympus, Panasonic, Pentax,
    # Samsung, Sigma, Leica, Hasselblad, Phase One, Kodak, Epson, Mamiya,
    # Minolta, GoPro, Adobe, generic)
    '.raw', '.dng', '.cr2', '.cr3', '.crw', '.nef', '.nrw', '.arw', '.srf',
    '.sr2', '.raf', '.orf', '.rw2', '.pef', '.ptx', '.srw', '.x3f', '.rwl',
    '.3fr', '.fff', '.iiq', '.dcr', '.dc2', '.kdc', '.erf', '.mef', '.mos',
    '.mrw', '.gpr', '.rwz', '.cap', '.eip', '.bay', '.dcs', '.drf', '.k25',
}

# Comprehensive video formats, including DVD (VOB/IFO/BUP), broadcast and
# camera container formats.
VIDEO_EXT = {
    '.mp4', '.m4v', '.m4p', '.mov', '.qt', '.avi', '.mkv', '.webm', '.wmv',
    '.asf', '.flv', '.f4v', '.f4p', '.mpg', '.mpeg', '.mpe', '.m1v', '.m2v',
    '.mp2', '.mpv', '.3gp', '.3g2', '.mts', '.m2ts', '.m2t', '.ts', '.tsv',
    '.vob', '.ifo', '.bup', '.ogv', '.ogm', '.rm', '.rmvb', '.divx', '.xvid',
    '.mxf', '.dv', '.dav', '.mod', '.tod', '.amv', '.drc', '.mng', '.yuv',
    '.h264', '.hevc', '.264', '.265', '.dvr-ms', '.wtv', '.vro', '.mqv',
    '.nsv', '.roq', '.svi', '.3gpp', '.mjpeg', '.mjpg', '.gifv',
}
MEDIA_EXT = PHOTO_EXT | VIDEO_EXT

THEME_COLOR = '#0A84FF'

FOLDER_DATE_RE = re.compile(r'(20\d{2})[-_]?(0[1-9]|1[0-2])')