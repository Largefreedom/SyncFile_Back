
# server end
from aiohttp import web
import aiohttp
import logg
from main import MainClass
import asyncio
import tools
import  constant
import time
import os
import json
import logg
import uuid

logger = logg.Logger()
@web.middleware
async def cache_control(request: web.Request, handler):
    response: web.Response = await handler(request)
    if request.path.endswith('.js') or request.path.endswith('.css'):
        response.headers.setdefault('Cache-Control', 'no-cache')
    return response

def create_cors_middleware(allowed_origin: str):
    @web.middleware
    async def cors_middleware(request: web.Request, handler):
        logger.info("time:[%s] method:[%s] URL:[%s] params:[%s] "%
              (time.asctime(),request.method,request.path,request.scheme))
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
            # Wait for a response from the server
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    logger.info(f"Received from server: {json.loads(msg.data)}")
                    if msg.data == "close":
                        await ws.close()
                        break
                    if (len(self.socket) == 0):
                        self.socket.append(ws)
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    logger.info("WebSocket connection closed")
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.info(f"WebSocket error: {ws.exception()}")
                    break
            # if sid:
            #     # Reusing existing session, remove old
            #     self.sockets.pop(sid, None)
            # else:
            #     sid = uuid.uuid4().hex
            #
            # self.sockets[sid] = ws
            #
            # try:
            #     # Send initial state to the new client
            #     await self.send("status", { "status": self.get_queue_info(), 'sid': sid }, sid)
            #     # On reconnect if we are the currently executing client send the current node
            #     if self.client_id == sid and self.last_node_id is not None:
            #         await self.send("executing", { "node": self.last_node_id }, sid)
            #
            #     async for msg in ws:
            #         if msg.type == aiohttp.WSMsgType.ERROR:
            #             logging.warning('ws connection closed with exception %s' % ws.exception())
            # finally:
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

            filter_file = list(filter(lambda x: x["id"] == submit_id, self.operate_path_list))
            if len(filter_file) == 0:
                raise Exception("源数据有误")
            result_file = filter_file[0]
            await self.send_data_obj_programe(result_file)
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
            self.program.send_sync("query", {
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

    async  def send_data_obj_programe(self,pass_obj):
        self.program.init_file_version2(pass_obj)
    async def setup(self):
        # 设置 http basic setup
        timeout = aiohttp.ClientTimeout(total=None) # no timeout
        self.client_session = aiohttp.ClientSession(timeout=timeout)

    async def publish_loop(self):
        while True:
            msg = await self.program.state_msg.get()
            if len(self.socket)!=0 and msg:
                # logger.info(msg[1])
                await self.socket[0].send_str(json.dumps(
                    msg[1]
                ))

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
        # https  scheme
        # if args.tls_keyfile and args.tls_certfile:
        #     ssl_ctx = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_SERVER, verify_mode=ssl.CERT_NONE)
        #     ssl_ctx.load_cert_chain(certfile=args.tls_certfile,
        #                             keyfile=args.tls_keyfile)
        #     scheme = "https"

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
    await asyncio.gather(server.start(address, port, verbose, call_on_start),server.publish_loop())


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
