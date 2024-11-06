#  a test scripts to validate whether func's logic is correct.

import os
import time
import constant
from file_transfer import MainClass
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


async def read_data(tempdata):
    with open(
            "D:/Coding/Practice/Pychon_Pra/temp/A Conversation with the Founder of ChatGPT_360332649_17081293538886294.mp4",
            "rb") as file:
        temp = file.read()
    logger.info(f"temp is {tempdata}")
class A:
    def __init__(self):
        self.queue_state = asyncio.Queue()

    async def start(self):
        while True:

            data = await self.queue_state.get()
            logger.info(f"data is {data}")


    async def start_one(self):
        # for i in range(20):
        #     # self.queue_state.put_nowait("1111")
        #     logger.info(f"input msg-- {1111}")
        logger.info(f"input msg-- {1111}")
        await read_data("start_one")
        await asyncio.sleep(5)
        logger.info(f"input msg-- {1122211}")
        await read_data("start_two")

    async def start_loop(self):
        while True:
            await asyncio.sleep(0.2)
            self.queue_state.put_nowait("111111111111")
            logger.info("--------------------------")

            await read_data("start_loop")


    async def num_a(self):
        return "1"

    async def num_b(self):
        return "2"

    async def num_c(self):
        return "3"


async def run(a):
    await asyncio.gather(a.start(),a.start_one(),a.start_loop())


async def run_abc(a):
    result = await asyncio.gather(a.num_a(),a.num_b(),a.num_c())
    print(result)

if __name__ =="__main__":
    a = A()
    asyncio.run( run(a))
    # asyncio.run(run_abc(a))
    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)
    # a = A()
    # try:
    #     loop.run_until_complete(run(a))
    # except KeyboardInterrupt:
    #     logger.info("\nStopped server")
