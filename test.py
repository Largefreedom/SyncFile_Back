#  a test scripts to validate whether func's logic is correct.
import os
import constant
from main import MainClass
import asyncio

def obtain_all_file_size( file_path):
    file_all_list = []
    file_path_list = [os.path.join(file_path, item) for item in os.listdir(file_path)]
    for index, file_item in enumerate(file_path_list):
        file_size = os.path.getsize(file_item)
        # transfer speed and status
        file_item_dict = {
            "id":  ("%s_%s" % (str(index),os.path.basename(file_item))).split(".")[0],
            "file_path": file_item.replace('\\', "/"),
            "file_size": file_size,
            "status": constant.UPLOAD_STATUS.todo.value,
            "process": 0
        }
        file_all_list.append(file_item_dict)
    return file_all_list





operate_path_list = obtain_all_file_size(constant.TMP_DIR_PATH)
submit_id = "1_epoch=1-step=8687"
filter_file = list(filter(lambda x: x["id"] == submit_id, operate_path_list))
if len(filter_file) ==0:
    raise Exception("源数据有误")
result_file =  filter_file[0]

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
main_process = MainClass(loop)
main_process.init_file_version2(result_file)


