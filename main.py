'''
    实现续传
    implement resume breakpoint of a file
'''
import os
from pathlib import Path
import json
import hashlib
from enum import Enum
import asyncio
from concurrent.futures import  ThreadPoolExecutor,as_completed
import constant
import time
from  logg import logger as logger
import psutil

# task execute status
class UPLOAD_STATUS(Enum):
    success = "success"
    progress = "progress"
    error = "error"

class  MainClass:
    def __init__(self,
                loop = None,
                socket=[],
                chunk_size= constant.CHUNK_SIZE ,
                output_path="../tempOut",
                state_json_path = "file_progress.json"
                ):
        self.state_msg = asyncio.Queue()
        self.task_queue_file = asyncio.Queue()

        self.chunk_size = chunk_size
        self.loop = loop
        self.output_path = output_path
        self.state_json_path = state_json_path
        self.process_json_path = os.path.join(self.output_path, self.state_json_path)
        # progress_bar init value is 0
        self.process_bar = 0
        self.socket = socket

    async def init_file_version2(self, file_path_obj):
        # file_path is a json obj
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path, exist_ok=True)
        # acquire the byte size of a file
        file_size = file_path_obj["file_size"]
        file_path = file_path_obj["file_path"]
        file_path_suffix = Path(file_path)
        file_suffix = file_path_suffix.suffix
        file_id = file_path_obj["id"]
        file_json_data = self.load_progress(file_id)
        if not file_json_data:
            file_json_data["file_name"] = file_id
            file_json_data["suffix"] = file_suffix
            file_json_data["size"] = file_size
            file_json_data["chunk_size"] = self.chunk_size
            file_json_data["file_id"] = file_id
            file_json_data["file_path"] = file_path
            #   all restart upload
            logger.info("数据初始化 %s" % file_json_data["file_id"])
            self.process_bar = 0
            await self.all_ini_restart_upload(file_json_data)
        else:
            #   已上传一部分，
            if "status" in file_json_data and UPLOAD_STATUS.success.value == file_json_data["status"]:
                pass
            chunk_list = await self.divide_file_chunks(file_json_data)
            need_upload_list = await self.check_data_interity_and_correct(file_json_data, chunk_list)
            logger.info("部分文件缺失，需要补充 %s, %s" % (need_upload_list, file_json_data["file_id"]))
            if (len(need_upload_list) > 0):
                await self.fix_uncomplete_upload(file_json_data, need_upload_list)



    # send_msg
    async def send_sync(self, event, data, sid=None):
        # time.sleep(0.1)
        logger.info(f"invoke send_sync func, event is {event} data is {data} {len(self.socket)}")
        if len(self.socket) > 0:
            self.loop.call_soon_threadsafe(
                self.socket[0].send_str, json.dumps(data)
            )
            await self.socket[0].send_str(json.dumps(data))
            # self.loop.call_soon(
            #     self.state_msg.put_nowait, (event, data, sid)
            # )

    async def init_socket(self,ws_item):
        self.socket = []
        self.socket = self.socket.append(ws_item)
    async def clear_socket(self):
        self.socket = []

    async def send_process_bar_event(self,file_id,file_total_size,chunk_num):
        file_size = [os.path.getsize(os.path.join(self.output_path,item))
                     for item in os.listdir(self.output_path) if item.startswith(str(file_id))]
        await self.send_sync("progress",{
            "file_id": file_id,
            "chunk_num":chunk_num,
            "progress": ( round(sum(file_size) *100/file_total_size, ndigits=2))
        })


    async def rec_sync(self):
        return self.loop.call_soon_threadsafe(
            self.state_msg.get_nowait()).result()

    def load_progress(self,file_identifier):
        # load json from file
        if os.path.exists(self.process_json_path):
            with open(self.process_json_path, "r") as json_file:
                new_json = json.load(json_file)
                if file_identifier in new_json:
                    return new_json[file_identifier]
        return {}

    def save_progress(self,json_data):
        # save json to file
        new_json = dict()
        if os.path.exists(self.process_json_path):
            with open(self.process_json_path, "r") as json_file:
                if json_file:
                    new_json = json.load(json_file)
        new_json[json_data["file_id"]] = json_data
        with open(self.process_json_path, "w") as json_file:
            json.dump(new_json, json_file)



    async def receive_chunk_file(self,chunk, file_id, chunk_num):
        new_part_file = "%s_part%s" % (file_id, chunk_num)
        chunk_item_complete_path = os.path.join(self.output_path, new_part_file)
        with open(chunk_item_complete_path, "wb") as chunk_file:
            # 保存文件夹
            chunk_file.write(chunk)
        return new_part_file, chunk_item_complete_path


    async def divide_file_chunks(self,file_json_data):
        with open(file_json_data["file_path"], "rb") as f:
            chunk_num = 1
            chunk_dict_list = []
            while True:
                chunk_item_dict = dict()
                chunk_content = f.read(self.chunk_size)
                if not chunk_content:
                    break
                new_part_file = "%s_part%s" % (file_json_data["file_id"], chunk_num)
                chunk_item_complete_path = os.path.join(self.output_path, new_part_file)
                chunk_item_dict["file_name"] = new_part_file
                chunk_item_dict["chunk_num"] = chunk_num
                chunk_item_dict["file_path"] = chunk_item_complete_path
                chunk_num += 1
                chunk_dict_list.append(chunk_item_dict)
            chunk_dict_list = sorted(chunk_dict_list, key=lambda x: x["chunk_num"])
        return chunk_dict_list

    # start a multi thread to process single chunk  data
    async def multi_thread_single_chunk_data(self,
                                       file_path,
                                       chunk_num,
                                       need_list_data,
                                       file_id,
                                       total_size):
        chunk_item_dict = dict()
        combine_data_item = dict()
        if chunk_num in need_list_data:
            with open(file_path, "rb") as f:
                f.seek(chunk_num * self.chunk_size)
                data = f.read(self.chunk_size)
            new_part_file, chunk_item_complete_path = await self.receive_chunk_file(data,
                                                                              file_id,
                                                                              chunk_num)
            chunk_item_dict["file_name"] = new_part_file
            chunk_item_dict["chunk_num"] = chunk_num
            chunk_item_dict["file_path"] = chunk_item_complete_path
        await self.send_process_bar_event(file_id,total_size,chunk_num)
        return  chunk_item_dict,combine_data_item


    async def multi_thread_single_chunk_data_init(self,
                                            file_path,
                                            chunk_num,
                                            file_id,
                                            total_size):
        chunk_item_dict = dict()
        combine_data_item = dict()
        with open(file_path, "rb") as f:
            f.seek(chunk_num * self.chunk_size)
            data = f.read(self.chunk_size)
        new_part_file, chunk_item_complete_path = await self.receive_chunk_file(data,
                                                                          file_id,
                                                                          chunk_num)
        chunk_item_dict["file_name"] = new_part_file
        chunk_item_dict["chunk_num"] = chunk_num
        chunk_item_dict["file_path"] = chunk_item_complete_path
        chunk_item_dict["status"] = UPLOAD_STATUS.success.value
        # calculate hash for hex num
        # chunk_item_dict["hash"] = hashlib.sha256(data).hexdigest()
        await self.send_process_bar_event(file_id, total_size,chunk_num)
        return chunk_item_dict



    async def get_chunk_file(self,file_path,chunk_num):
        with open(file_path,"rb") as f:
            f.seek(chunk_num * self.chunk_size)
            data = f.read(self.chunk_size)
        return data,chunk_num


    async def fix_uncomplete_upload(self,file_json_data,need_list_data):
        chunk_num = 0
        ini_offset_size = chunk_num * self.chunk_size
        file_size = file_json_data["size"]
        chunk_dict_list = file_json_data["chunks"]
        with ThreadPoolExecutor(max_workers=constant.PROCESS_THREAD_NUM) as executor:
            thread_pool_param_list = []
            while (ini_offset_size<=file_size):
                param_list = []
                param_list.append(file_json_data["file_path"])
                param_list.append(chunk_num)
                param_list.append(need_list_data)
                param_list.append(file_json_data["file_id"])
                param_list.append(file_json_data["size"])
                thread_pool_param_list.append(param_list)
                chunk_num += 1
                ini_offset_size = chunk_num * self.chunk_size
            # every 3 item process parallel to threadPool
            # for i in range(0, len(thread_pool_param_list),constant.PROCESS_THREAD_NUM):
            #     item_list = thread_pool_param_list[i:i+constant.PROCESS_THREAD_NUM]
            #     futures = {executor.submit(self.multi_thread_single_chunk_data, *data): data for data in
            #                item_list}
            #     for future in as_completed(futures):
            #         result = future.result()  # Get the result from the Future
            #         if result[0]:
            #             chunk_dict_list.append(result[0])

            for i in thread_pool_param_list:
                result = await self.multi_thread_single_chunk_data(*i)
                # item_list = thread_pool_param_list[i:i + constant.PROCESS_THREAD_NUM]
                # futures = {executor.submit(self.multi_thread_single_chunk_data, *data): data for data in
                #            item_list}
                # for future in as_completed(futures):
                #     result = future.result()  # Get the result from the Future
                if result[0]:
                     chunk_dict_list.append(result[0])

        file_json_data["chunk_num"] = chunk_num - 1
        chunk_dict_list = sorted(chunk_dict_list, key=lambda x: x["chunk_num"])
        file_json_data["chunks"] = chunk_dict_list
        await self.save_all_file(file_json_data)


    async def all_ini_restart_upload(self,file_json_data):
        chunk_num = 0
        ini_offset_size = chunk_num * self.chunk_size
        file_size = file_json_data["size"]
        chunk_dict_list = []
        with ThreadPoolExecutor(max_workers=constant.PROCESS_THREAD_NUM) as executor:
            thread_pool_param_list = []
            while (ini_offset_size <= file_size):
                # thread pool
                param_list = []
                param_list.append(file_json_data["file_path"])
                param_list.append(chunk_num)
                param_list.append(file_json_data["file_id"])
                param_list.append(file_json_data["size"])
                thread_pool_param_list.append(param_list)
                chunk_num += 1
                ini_offset_size = chunk_num * self.chunk_size

            for param_item in thread_pool_param_list:
                result = await self.multi_thread_single_chunk_data_init(*param_item)
                if result:
                    chunk_dict_list.append(result)
            # for i in range(0, len(thread_pool_param_list), constant.PROCESS_THREAD_NUM):
            #     item_list = thread_pool_param_list[i:i + constant.PROCESS_THREAD_NUM]
            #     futures = {executor.submit(self.multi_thread_single_chunk_data_init, *data): data for data in
            #                item_list}
            #     for future in as_completed(futures):
            #         result = future.result()  # Get the result from the Future
            #         if result:
            #             chunk_dict_list.append(result)
        # 计算所有 hash 值
        file_json_data["chunk_num"] = chunk_num - 1
        chunk_dict_list = sorted(chunk_dict_list, key=lambda x: x["chunk_num"])
        file_json_data["chunks"] = chunk_dict_list
        await self.save_all_file(file_json_data)

    async def check_data_interity_and_correct(self,file_json_data, chunk_dict_list):
        # validate the data, need upload list, return all chunk_num
        need_upload_list = []
        if "chunk_num" not in file_json_data or "chunks" not in file_json_data:
            need_upload_list = [item["chunk_num"] for item in chunk_dict_list]
            return need_upload_list
        chunks = file_json_data["chunks"]
        for item in chunk_dict_list:
            result_chunk_list = [chunk_item for chunk_item in chunks if chunk_item["chunk_num"] == item["chunk_num"]]
            if len(result_chunk_list) == 0:
                need_upload_list.append(item["chunk_num"])
        return need_upload_list


    async def save_all_file(self,file_json_data):
        '''
            save the byte content of a file to local computer
        :param file_json_data:
        :param combined_data:
        :return:
        '''
        # 读取chunks
        chunk_path_list = file_json_data["chunks"]
        file_out_path = os.path.join(self.output_path, str(file_json_data["file_id"]) + file_json_data["suffix"])
        chunk_path_list = [item["file_path"] for item in chunk_path_list]

        with open(file_out_path,"wb") as final_file:
            for item in chunk_path_list:
                with open(item,"rb") as temp_file:
                    final_file.write(temp_file.read())
                #  remove this part file path
                os.remove(item)
        # self.send_sync(event="done",data={
        #     "file_id": file_json_data["file_id"],
        #     "chunk_num": "all",
        #     "progress": 100
        # })
        logger.info(f"all job done for file {file_json_data['file_id']}")
        # with open(os.path.join(self.output_path, str(file_json_data["file_id"]) + file_json_data["suffix"]), "wb") as f:
        #     file_content = b"".join(sorted_combined_data)
        #     # TODO write the content to file
        #     # f.write(file_content)
        #     file_json_data["status"] = UPLOAD_STATUS.success.value
        #     to_remove_file_list = [ i for i in os.listdir(self.output_path) if "%s_part"%file_json_data["file_name"] in i ]
        #     for item in to_remove_file_list:
        #         # 删除item
        #         os.remove(os.path.join(self.output_path,item))
        #     self.save_progress(file_json_data)