from aiohttp import web
from tests.helpers import SimpleMock, SimpleMockRequest


routes = web.RouteTableDef()

mock_resp = SimpleMock()
mock_req = SimpleMockRequest()


@routes.route("*", "/{_:.*}")
async def handler(request):
    mock_req.update(request)
    return web.Response(**mock_resp)


async def setup_web_server(app, host='localhost', port=8109):
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()

app = web.Application()
app.add_routes(routes)
