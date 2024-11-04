from enum import Enum

# store const variable for this app

# unit byte
FILE_BYTE_COVERT_MB_NUM = 1
# unit byte
CHUNK_SIZE = 1024 * 1024 * 50

WEB_MAX_UPLOAD_SIZE = 5 * (1024 ** 4) * 1024 * 1024


# temp const dir path
TMP_DIR_PATH = "D:/Coding/Practice/Pychon_Pra/temp"


LOG_SAVE_PATH = "app.log"

class UPLOAD_STATUS(Enum):
    success = "success"
    progress = "progress"
    error = "error",
    todo = "todo"