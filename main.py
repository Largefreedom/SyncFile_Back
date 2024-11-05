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
from  logg import logger as logger


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
        self.chunk_size = chunk_size
        self.loop = loop
        self.output_path = output_path
        self.state_json_path = state_json_path
        self.process_json_path = os.path.join(self.output_path, self.state_json_path)
        # progress_bar init value is 0
        self.process_bar = 0
        self.socket = socket

    def init_file_version2(self, file_path_obj):
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
            self.all_ini_restart_upload(file_json_data)
        else:
            #   已上传一部分，
            if "status" in file_json_data and UPLOAD_STATUS.success.value == file_json_data["status"]:
                pass
            chunk_list = self.divide_file_chunks(file_json_data)
            need_upload_list = self.check_data_interity_and_correct(file_json_data, chunk_list)
            logger.info("部分文件缺失，需要补充 %s, %s" % (need_upload_list, file_json_data["file_id"]))
            if (len(need_upload_list) > 0):
                self.fix_uncomplete_upload(file_json_data, need_upload_list)

    def init_socket(self,socket):
        self.socket = socket

    # send_msg
    def send_sync(self, event, data, sid=None):

        self.loop.call_soon_threadsafe(
            self.state_msg.put_nowait, (event, data, sid)
        )



    def send_process_bar_event(self,file_id,file_total_size,chunk_num):
        file_size = [os.path.getsize(os.path.join(self.output_path,item))
                     for item in os.listdir(self.output_path) if item.startswith(str(file_id))]
        self.send_sync("progress",{
            "file_id": file_id,
            "chunk_num":chunk_num,
            "progress": ( round(sum(file_size) *100/file_total_size, ndigits=2))
        })


    def rec_sync(self):
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
        # with open(self.process_json_path, "w") as json_file:
        #     json.dump(new_json, json_file)

    def receive_chunk_file(self,chunk, file_id, chunk_num):
        new_part_file = "%s_part%s" % (file_id, chunk_num)
        chunk_item_complete_path = os.path.join(self.output_path, new_part_file)
        with open(chunk_item_complete_path, "wb") as chunk_file:
            # 保存文件夹
            chunk_file.write(chunk)
        return new_part_file, chunk_item_complete_path


    def divide_file_chunks(self,file_json_data):
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
    def multi_thread_single_chunk_data(self,
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

            new_part_file, chunk_item_complete_path = self.receive_chunk_file(data,
                                                                              file_id,
                                                                              chunk_num)
            chunk_item_dict["file_name"] = new_part_file
            chunk_item_dict["chunk_num"] = chunk_num
            chunk_item_dict["file_path"] = chunk_item_complete_path
            # chunk_dict_list.append(chunk_item_dict)
        else:
            new_part_file = "%s_part%s" % (file_id, chunk_num)
            chunk_item_complete_path = os.path.join(self.output_path, new_part_file)
            with open(chunk_item_complete_path, "rb") as f_chunk:
                combine_data_item["data"] = f_chunk.read()

        combine_data_item["chunk_num"] = chunk_num

        self.send_process_bar_event(file_id,total_size,chunk_num)
        return  chunk_item_dict,combine_data_item

    def multi_thread_single_chunk_data_init(self, chunk_num, chunk_content,
                                       file_id,total_size):

        chunk_item_dict = dict()
        combine_data_item = dict()

        new_part_file, chunk_item_complete_path = self.receive_chunk_file(chunk_content,
                                                                          file_id,
                                                                          chunk_num)
        chunk_item_dict["file_name"] = new_part_file
        chunk_item_dict["chunk_num"] = chunk_num
        chunk_item_dict["file_path"] = chunk_item_complete_path
        chunk_item_dict["status"] = UPLOAD_STATUS.success.value
        # 计算 hash 16进制
        chunk_item_dict["hash"] = hashlib.sha256(chunk_content).hexdigest()
        combine_data_item["data"] = chunk_content
        combine_data_item["chunk_num"] = chunk_num
        self.send_process_bar_event(file_id, total_size,chunk_num)
        return chunk_item_dict, combine_data_item



    def get_chunk_file(self,file_path,chunk_num):
        with open(file_path,"rb") as f:
            f.seek(chunk_num * self.chunk_size)
            data = f.read(self.chunk_size)
        return data,chunk_num


    def fix_uncomplete_upload(self,file_json_data,need_list_data):
        chunk_num = 0
        ini_offset_size = chunk_num * self.chunk_size
        file_size = file_json_data["size"]
        chunk_dict_list = file_json_data["chunks"]
        with ThreadPoolExecutor(max_workers=3) as executor:
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
            futures = {executor.submit(self.multi_thread_single_chunk_data, *data): data for data in
                       thread_pool_param_list}

            for future in as_completed(futures):
                result = future.result()  # Get the result from the Future
                if result[0]:
                    chunk_dict_list.append(result[0])

        file_json_data["chunk_num"] = chunk_num - 1
        chunk_dict_list = sorted(chunk_dict_list, key=lambda x: x["chunk_num"])
        file_json_data["chunks"] = chunk_dict_list
        self.save_all_file(file_json_data)




    def fix_uncomplete_upload(self,file_json_data, need_list_data):
        combined_data = []
        with open(file_json_data["file_path"], "rb") as f:
            chunk_num = 0
            chunk_dict_list = file_json_data["chunks"]
            with ThreadPoolExecutor(max_workers=3) as executor:
                thread_pool_param_list = []
                # 线程池
                while chunk_content := f.read(self.chunk_size):
                    param_list = []
                    param_list.append(chunk_num)
                    param_list.append(need_list_data)
                    param_list.append(chunk_content)
                    param_list.append( file_json_data["file_id"])
                    param_list.append(file_json_data["size"])
                    thread_pool_param_list.append(param_list)
                    chunk_num += 1
                futures = {executor.submit(self.multi_thread_single_chunk_data, *data): data for data in thread_pool_param_list}
                for future in as_completed(futures):
                    data = futures[future]
                    result = future.result()  # Get the result from the Future
                    if result[0]:
                        chunk_dict_list.append(result[0])
                    combined_data.append(result[1])

            file_json_data["all_hash"] = hashlib.sha256(f.read()).hexdigest()
            file_json_data["chunk_num"] = chunk_num - 1
            chunk_dict_list = sorted(chunk_dict_list, key=lambda x: x["chunk_num"])
            file_json_data["chunks"] = chunk_dict_list
            self.save_all_file(file_json_data, combined_data)

    def all_ini_restart_upload(self,file_json_data):
        combined_data = []
        with open(file_json_data["file_path"], "rb") as f:
            chunk_num = 1
            chunk_dict_list = []
            with ThreadPoolExecutor(max_workers=3) as executor:
                thread_pool_param_list = []
                # 线程池
                while chunk_content := f.read(self.chunk_size):
                    param_list = []
                    param_list.append(chunk_num)
                    param_list.append(chunk_content)
                    param_list.append(file_json_data["file_id"])
                    param_list.append(file_json_data["size"])
                    thread_pool_param_list.append(param_list)
                    chunk_num += 1
                futures = {executor.submit(self.multi_thread_single_chunk_data_init, *data): data for data in
                           thread_pool_param_list}
                for future in as_completed(futures):
                    data = futures[future]
                    result = future.result()  # Get the result from the Future

                    if result[0]:
                        chunk_dict_list.append(result[0])

                    combined_data.append(result[1])

            # 计算所有 hash 值
            file_json_data["all_hash"] = hashlib.sha256(f.read()).hexdigest()
            file_json_data["chunk_num"] = chunk_num - 1
            chunk_dict_list = sorted(chunk_dict_list, key=lambda x: x["chunk_num"])
            file_json_data["chunks"] = chunk_dict_list
            self.save_all_file(file_json_data, combined_data)



    def check_data_interity_and_correct(self,file_json_data, chunk_dict_list):
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

    def save_all_file(self,file_json_data, combined_data):
        '''
            save the byte content of a file to local computer
        :param file_json_data:
        :param combined_data:
        :return:
        '''
        sorted_combined_data = [item["data"] for item in sorted(combined_data,key=lambda item: item["chunk_num"])]
        with open(os.path.join(self.output_path, str(file_json_data["file_id"]) + file_json_data["suffix"]), "wb") as f:
            file_content = b"".join(sorted_combined_data)
            # TODO write the content to file
            # f.write(file_content)
            file_json_data["status"] = UPLOAD_STATUS.success.value
            to_remove_file_list = [ i for i in os.listdir(self.output_path) if "%s_part"%file_json_data["file_name"] in i ]
            for item in to_remove_file_list:
                # 删除item
                os.remove(os.path.join(self.output_path,item))
            self.save_progress(file_json_data)

