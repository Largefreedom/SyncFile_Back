#  a test scripts to validate whether func's logic is correct.
import os
import time

import constant
from main import MainClass
import asyncio
from logg import logger

# def obtain_all_file_size( file_path):
#     file_all_list = []
#     file_path_list = [os.path.join(file_path, item) for item in os.listdir(file_path)]
#     for index, file_item in enumerate(file_path_list):
#         file_size = os.path.getsize(file_item)
#         # transfer speed and status
#         file_item_dict = {
#             "id":  ("%s_%s" % (str(index),os.path.basename(file_item))).split(".")[0],
#             "file_path": file_item.replace('\\', "/"),
#             "file_size": file_size,
#             "status": constant.UPLOAD_STATUS.todo.value,
#             "process": 0
#         }
#         file_all_list.append(file_item_dict)
#     return file_all_list
#
# operate_path_list = obtain_all_file_size(constant.TMP_DIR_PATH)
# # print("all path list is",operate_path_list)
# submit_id = "0_A Conversation with the Founder of ChatGPT_360332649_17081293538886294"
# filter_file = list(filter(lambda x: x["id"] == submit_id, operate_path_list))
# if len(filter_file) ==0:
#     raise Exception("源数据有误")
# result_file =  filter_file[0]
#
# loop = asyncio.new_event_loop()
# asyncio.set_event_loop(loop)
# main_process = MainClass(loop)
# main_process.init_file_version2(result_file)


class A:
    def __init__(self):
        self.queue_state = asyncio.Queue()



    async def start(self):
        while True:
            # logger.info(f"queue status is {self.queue_state.empty()}")
            data = await self.queue_state.empty()
            if not await self.queue_state.empty():
                logger.info(f"data is {await self.queue_state.put_nowait()}")


    async def start_one(self):
        while True:
            time.sleep(2)
            self.queue_state.put_nowait("1111")
            logger.info(f"input msg {1111}")

async def run(a):
    await asyncio.gather(a.start(),a.start_one())



if __name__ =="__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    a = A()

    try:
        loop.run_until_complete(run(a))
    except KeyboardInterrupt:
        logger.info("\nStopped server")
