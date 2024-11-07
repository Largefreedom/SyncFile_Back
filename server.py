
# server end
from aiohttp import web
import aiohttp
from file_transfer import MainClass
import asyncio
import tools
import  constant
import time
import os
import json
from  logg import logger as logger

async def time_delay(num):
    logger.info("start count")
    time.sleep(num)
    logger.info("end count")


@web.middleware
async def cache_control(request: web.Request, handler):
    response: web.Response = await handler(request)
    if request.path.endswith('.js') or request.path.endswith('.css'):
        response.headers.setdefault('Cache-Control', 'no-cache')
    return response

def create_cors_middleware(allowed_origin: str):
    @web.middleware
    async def cors_middleware(request: web.Request, handler):
        if request.method == "OPTIONS":
            # Pre-flight request. Reply successfully:
            response = web.Response()
        else:
            response = await handler(request)
        if request.path.startswith("/api/ws"):

            return response
        response.headers['Access-Control-Allow-Origin'] = "*"
        response.headers['Access-Control-Allow-Methods'] = 'POST, GET, DELETE, PUT'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response
    return cors_middleware


class MainServer:
    def __init__(self,loop,main_program:MainClass):
        self.loop = loop
        self.program = main_program
        # 初始文件夹根目录
        middlewares = [cache_control]
        middlewares.append(create_cors_middleware("*"))
        max_upload_size = constant.WEB_MAX_UPLOAD_SIZE
        self.app = web.Application(client_max_size=max_upload_size, middlewares=middlewares)
        logger.info("Backend server start")
        routes = web.RouteTableDef()
        self.num_workers = 3
        self.routes = routes
        self.operate_path_list = []
        self.socket = []


        @routes.get('/ws')
        async def websocket_handler(request):
            ws = web.WebSocketResponse()
            await ws.prepare(request)
            sid = request.rel_url.query.get('clientId', '')
            logger.info("WebSocket connection established")
            # Send a message to the server
            await ws.send_str("Hello, Server!")
            # self.socket = []
            self.program.socket = []
            # Wait for a response from the server
            async for msg in ws:
                logger.info(f"input type {msg.type}  {aiohttp.WSMsgType.CLOSED}")
                if msg.type == aiohttp.WSMsgType.TEXT:
                    logger.info(f"Received from server: {json.loads(msg.data)}")
                    if msg.data == "close":
                        await ws.close()
                        break
                    if (len(self.program.socket) == 0):
                        # self.socket.append(ws)
                        self.program.socket.append(ws)
                    else:
                        logger.info("remove already socket")
                        # socket is not empty, remove already exits, add new
                        self.program.socket = []
                        # self.socket.append(ws)
                        self.program.socket.append(ws)
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    logger.info("WebSocket connection closed")
                    self.program.socket = []
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.info(f"WebSocket error: {ws.exception()}")
                    self.program.socket = []
                    break
            return ws

        @routes.get("/test")
        async def post_interrupt(request):
            return web.Response(status=200)

        @routes.get("/query-data")
        async def post_interrupt(request):
            data = self.program.rec_sync()
            logger.info("获取到数据为",data)
            return web.json_response(data)

        # process data in real time
        @routes.post("/start/process")
        async def post_interrupt(request):
            # data = self.program.rec_sync()
            data = await request.json()
            # logger.info("获取到数据为", data)
            submit_id = data.get("id")
            self.loop.call_soon_threadsafe(
                self.program.task_queue_file.put_nowait, (submit_id)
            )
            return web.json_response(data)

        @routes.get("/send-data")
        async def post_interrupt(request):
            self.program.send_sync("test",{
                "data": "data"
            })
            logger.info("获取到数据为", )
            return web.json_response({
                "data": "success"
            })

        # submit the dir info to server
        @routes.post("/submit-dir")
        async def post_interrupt(request):
            await self.program.send_sync("query", {
                "data": "data"
            })
            return self.obtain_all_file_size(constant.TMP_DIR_PATH)


    def obtain_all_file_size(self,file_path):
        file_all_list = []
        file_path_list = [os.path.join(file_path, item) for item in os.listdir(file_path)]
        for index, file_item in enumerate(file_path_list):
            file_size = os.path.getsize(file_item)
            # transfer speed and status
            file_item_dict = {
                "id": ("%s_%s" % (str(index), os.path.basename(file_item))).split(".")[0],
                "file_path": file_item.replace('\\', "/"),
                "file_size": file_size,
                "status": constant.UPLOAD_STATUS.todo.value,
                "process": 0
            }
            file_all_list.append(file_item_dict)
        self.operate_path_list = file_all_list
        return tools.warp_response_json({
            "file_info": file_all_list
        })

    async def send_data_obj_programe(self,pass_obj):
        await self.program.init_file_version2(pass_obj)

    async def setup(self):
        # 设置 http basic setup
        timeout = aiohttp.ClientTimeout(total=None) # no timeout
        self.client_session = aiohttp.ClientSession(timeout=timeout)

    async def task_execute_loop(self):
        while True:
            file_id = await self.program.task_queue_file.get()
            logger.info(f"query task_id {file_id}, start execute task")
            filter_file = list(filter(lambda x: x["id"] == file_id, self.operate_path_list))
            if len(filter_file) == 0:
                logger.error(f"error not query file_item for {file_id}")
            result_file = filter_file[0]
            await self.send_data_obj_programe(result_file)

    async def publish_loop(self):
        while True:
            msg = await self.program.state_msg.get()
            if len(self.program.socket) >0 :
                await self.program.socket[0].send_str(json.dumps(msg[1]))



    async def customor_run(self):
        # Start multiple consumer tasks for parallel processing
        consumers = [asyncio.create_task(self.task_execute_loop()) for _ in range(self.num_workers)]
        # # This runs indefinitely, as there’s no defined stopping point
        # await self.program.state_msg.join()  # Optionally wait for all items to be processed
        # # Cancel all consumers on shutdown
        # for consumer in consumers:
        #     consumer.cancel()
        await asyncio.gather(*consumers, return_exceptions=True)


    # async def allCustorStart(self):
    #
    #     consumer_task = asyncio.create_task(self.customor_run())
    #     await asyncio.gather(consumer_task)


    def add_routes(self):
        api_routes = web.RouteTableDef()
        for route in self.routes:
            # Custom nodes might add extra static routes. Only process non-static
            # routes to add /api prefix.
            if isinstance(route, web.RouteDef):
                api_routes.route(route.method, "/api" + route.path)(route.handler, **route.kwargs)
        self.app.add_routes(api_routes)
        self.app.add_routes(self.routes)

    async def start(self, address, port, verbose=True, call_on_start=None):
        runner = web.AppRunner(self.app, access_log=None)
        await runner.setup()
        ssl_ctx = None
        scheme = "http"
        site = web.TCPSite(runner, address, port, ssl_context=ssl_ctx)
        await site.start()
        self.address = address
        self.port = port
        if verbose:
            logger.info("Starting server")
            logger.info("Api endpoint is: {}://{}:{}".format(scheme, address, port))
        if call_on_start is not None:
            call_on_start(scheme, address, port)

async def run(server, address='', port=8188, verbose=True, call_on_start=None):
    await asyncio.gather(server.start(address, port, verbose, call_on_start),
                         server.publish_loop(),
                         server.customor_run())


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    main_program = MainClass(loop)
    file_path ="D:/BrowerDownload/A Conversation with the Founder of ChatGPT.mp4"
    main_server = MainServer(main_program=main_program,loop = loop)
    main_server.add_routes()
    try:
        loop.run_until_complete(main_server.setup())
        loop.run_until_complete(run(main_server, address="localhost", port=8001, verbose=True))
    except KeyboardInterrupt:
        logger.info("\nStopped server")
