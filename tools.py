from aiohttp import web



# wrap response data into a json object
def warp_response_json(data):
    return web.json_response(data={
        "data": data
    })




