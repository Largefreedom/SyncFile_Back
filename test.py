# #  a test scripts to validate whether func's logic is correct.
#
# import os
# import time
# import constant
# from file_transfer import MainClass
# import asyncio
# from logg import logger
#
# # def obtain_all_file_size( file_path):
# #     file_all_list = []
# #     file_path_list = [os.path.join(file_path, item) for item in os.listdir(file_path)]
# #     for index, file_item in enumerate(file_path_list):
# #         file_size = os.path.getsize(file_item)
# #         # transfer speed and status
# #         file_item_dict = {
# #             "id":  ("%s_%s" % (str(index),os.path.basename(file_item))).split(".")[0],
# #             "file_path": file_item.replace('\\', "/"),
# #             "file_size": file_size,
# #             "status": constant.UPLOAD_STATUS.todo.value,
# #             "process": 0
# #         }
# #         file_all_list.append(file_item_dict)
# #     return file_all_list
# #
# # operate_path_list = obtain_all_file_size(constant.TMP_DIR_PATH)
# # # print("all path list is",operate_path_list)
# # submit_id = "0_A Conversation with the Founder of ChatGPT_360332649_17081293538886294"
# # filter_file = list(filter(lambda x: x["id"] == submit_id, operate_path_list))
# # if len(filter_file) ==0:
# #     raise Exception("源数据有误")
# # result_file =  filter_file[0]
# #
# # loop = asyncio.new_event_loop()
# # asyncio.set_event_loop(loop)
# # main_process = MainClass(loop)
# # main_process.init_file_version2(result_file)
#
#
# async def read_data(tempdata):
#     with open(
#             "D:/Coding/Practice/Pychon_Pra/temp/A Conversation with the Founder of ChatGPT_360332649_17081293538886294.mp4",
#             "rb") as file:
#         temp = file.read()
#     logger.info(f"temp is {tempdata}")
# class A:
#     def __init__(self):
#         self.queue_state = asyncio.Queue()
#
#     async def start(self):
#         while True:
#
#             data = await self.queue_state.get()
#             logger.info(f"data is {data}")
#
#
#     async def start_one(self):
#         # for i in range(20):
#         #     # self.queue_state.put_nowait("1111")
#         #     logger.info(f"input msg-- {1111}")
#         logger.info(f"input msg-- {1111}")
#         await read_data("start_one")
#         await asyncio.sleep(5)
#         logger.info(f"input msg-- {1122211}")
#         await read_data("start_two")
#
#     async def start_loop(self):
#         while True:
#             await asyncio.sleep(0.2)
#             self.queue_state.put_nowait("111111111111")
#             logger.info("--------------------------")
#
#             await read_data("start_loop")
#
#
#     async def num_a(self):
#         return "1"
#
#     async def num_b(self):
#         return "2"
#
#     async def num_c(self):
#         return "3"
#
#
# async def run(a):
#     await asyncio.gather(a.start(),a.start_one(),a.start_loop())
#
#
# async def run_abc(a):
#     result = await asyncio.gather(a.num_a(),a.num_b(),a.num_c())
#     print(result)
#
# if __name__ =="__main__":
#     a = A()
#     asyncio.run( run(a))
#     # asyncio.run(run_abc(a))
#     # loop = asyncio.new_event_loop()
#     # asyncio.set_event_loop(loop)
#     # a = A()
#     # try:
#     #     loop.run_until_complete(run(a))
#     # except KeyboardInterrupt:
#     #     logger.info("\nStopped server")

import asyncio


class YourClass:
    def __init__(self, num_workers=3):
        self.queue = asyncio.Queue()
        self.num_workers = num_workers

    async def process(self, msg):
        # Simulate a long processing time
        print(f"Processing {msg}")
        await asyncio.sleep(2)  # Simulate processing time
        print(f"Finished processing {msg}")

    async def add_to_queue(self, msg):
        """Method to be called externally to add messages to the queue."""
        await self.queue.put(msg)
        print(f"Added {msg} to the queue")

    async def consumer(self):
        while True:
            msg = await self.queue.get()  # Wait for a message from the queue
            await self.process(msg)  # Process the message
            self.queue.task_done()  # Mark the task as done

    async def run(self):
        # Start multiple consumer tasks for parallel processing
        consumers = [asyncio.create_task(self.consumer()) for _ in range(self.num_workers)]

        # # This runs indefinitely, as there’s no defined stopping point
        # await self.queue.join()  # Optionally wait for all items to be processed
        #
        # # Cancel all consumers on shutdown
        # for consumer in consumers:
        #     consumer.cancel()
        await asyncio.gather(*consumers, return_exceptions=True)


# Simulate client events adding messages to the queue
async def simulate_client_events(your_class_instance):
    i = 0
    while True:
        await asyncio.sleep(1)  # Simulate delay between client events
        await your_class_instance.add_to_queue(f"message {i}")
        i += 1


# Run the system with continuous event generation
async def main():
    your_class = YourClass(num_workers=3)

    # Start the consumer loop
    consumer_task = asyncio.create_task(your_class.run())

    # Simulate client events adding to the queue
    client_simulation_task = asyncio.create_task(simulate_client_events(your_class))

    # Await both tasks indefinitely
    await asyncio.gather(consumer_task, client_simulation_task)


# Start the asyncio event loop
asyncio.run(main())
