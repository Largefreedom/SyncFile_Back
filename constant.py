from enum import Enum

# store const variable for this app

# unit byte
FILE_BYTE_COVERT_MB_NUM = 1
# unit byte
CHUNK_SIZE = 1024 * 1024 * 20

WEB_MAX_UPLOAD_SIZE = 5 * (1024 ** 4) * 1024 * 1024

# execute thread num
PROCESS_THREAD_NUM = 1

# temp const dir path
TMP_DIR_PATH = "D:/Coding/Practice/Pychon_Pra/temp"


# log path for save
LOG_SAVE_PATH = "../log/app.log"

# single log size
LOG_MAX_SIZE = 20_000_000

# backup file num for log
LOG_BACK_COUNT = 10

class UPLOAD_STATUS(Enum):
    success = "success"
    progress = "progress"
    error = "error",
    todo = "todo"