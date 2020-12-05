from aiohttp import web


mock_resp = {}
mock_req = {}

routes = web.RouteTableDef()


async def setup_web_server(app, host='localhost', port=8109):
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()


@routes.route("*", "/{endpoint:.*}")
async def handler(request):
    mock_req.clear()
    mock_req["endpoint"] = request.match_info['endpoint']
    mock_req["headers"] = dict(request.headers)
    mock_req["request"] = request
    return web.Response(**mock_resp)

app = web.Application()
app.add_routes(routes)
