import datetime
from aiohttp import web, ClientSession
from aiohttp.web import json_response, HTTPBadRequest, HTTPServerError, Request
from controller import Controller
from models import InstructRequest


class Server:
    def __init__(
        self, controller: Controller, host: str = "localhost", port: int = 5000
    ):
        self._controller: Controller = controller
        self._host: str = host
        self._port: int = port
        self._app: web.Application = web.Application(
            middlewares=[self._json_error_middleware, self._log_middleware]
        )
        self.routes: list[tuple[str, str, callable]] = [
            ("POST", "/cancel", self._cancel),
            ("POST", "/enqueue", self._enqueue),
            ("POST", "/exit", self._exit),
            ("POST", "/instruct", self._instruct),
            ("GET", "/status", self._get_status),
            ("GET", "/queue", self._get_queue),
            ("GET", "/devices", self._get_device),
            ("GET", "/devices/{port}", self._get_device),
            ("GET", "/distance", self._get_distance),
            ("GET", "/distance/{port}", self._get_distance),
            ("GET", "/color", self._get_color),
            ("GET", "/color/{port}", self._get_color),
            ("POST", "/debug/ping", self._ping),
        ]
        self._add_routes()

    # Public
    def add_route(self, method: str, path: str, handler: callable):
        self._app.router.add_route(method, path, handler)

    # Private
    def _add_routes(self):
        route_count = 0
        print("Adding routes...")
        for route in self.routes:
            print(f"- Adding {route[0]} route '{route[1]}'...")
            self.add_route(*route)
            route_count += 1
        print(f"{route_count} routes added.")

    @staticmethod
    async def _json_error_middleware(app, handler):
        async def middleware_handler(request):
            try:
                response = await handler(request)
                if response.content_type == "text/html":
                    response.content_type = "application/json"
                return response
            except web.HTTPException as ex:
                return web.json_response({"error": str(ex)}, status=ex.status)
            except Exception as ex:
                return web.json_response({"error": str(ex)}, status=500)

        return middleware_handler

    @staticmethod
    @web.middleware
    async def _log_middleware(request, handler):
        print(f"Request: {request.method} {request.path}")
        return await handler(request)

    # Route handlers
    async def _cancel(self, *args, **kwargs):
        success, state, message = await self._controller.cancel()
        print(message)
        if success:
            return json_response({"state": state})
        else:
            raise HTTPServerError(text=message, content_type="application/json")

    async def _enqueue(self, request: Request):
        """
        Enqueues an instruct with the given instruct id.

        Returns:
            A JSON response containing the updated queue size.
        """
        data = await request.json()
        instruct = InstructRequest(**data)

        if instruct.instructId is None:
            raise HTTPBadRequest(
                text="No instruct id given.", content_type="application/json"
            )

        qsize, message = self._controller.enqueue(instruct.instructId)
        print(message)
        return json_response({"queueSize": qsize})
        # TODO: Add whitelist & blacklist for instruct ids.

    async def _exit(self, *args, **kwargs):
        qsize, message = self._controller.exit()
        print(message)
        return json_response({"queueSize": qsize})

    async def _instruct(self, request: Request):
        data = await request.json()
        instruct = InstructRequest(**data)

        # TODO: Add feature flag to allow/prevent running hub commands directly.

        if instruct.instructId is None:
            raise HTTPBadRequest(
                text="No instruct id given.", content_type="application/json"
            )

        success, state, message = await self._controller.run_instruct(
            instruct.instructId
        )
        print(message)
        if success:
            return json_response({"result": state})
        else:
            raise HTTPServerError(text=message, content_type="application/json")

    async def _get_status(self, *args, **kwargs):
        return json_response(
            {
                "hubName": self._controller.get_hub_name(),
                "state": self._controller.get_state().name,
                "currentInstruct": self._controller.get_current_instruct(),
                "queueSize": self._controller.get_queue_size(),
            }
        )

    async def _get_queue(self, *args, **kwargs):
        return json_response({"queueInstructs": self._controller.get_queue()})

    async def _get_device(self, request: Request):
        port = request.match_info.get("port", None)
        type = request.query.get("type", None)
        device = self._controller.get_device(port, type)
        print(device)
        return json_response(device)

    async def _get_distance(self, request: Request):
        port = request.match_info.get("port", None)
        print(f"Getting distance for port {port}...")
        distance = self._controller.get_distance(port)
        print(distance)
        return json_response(distance)

    async def _get_color(self, request: Request):
        port = request.match_info.get("port", None)
        print(f"Getting color for port {port}...")
        color = self._controller.get_color(port)
        print(color)
        return json_response(color)

    async def _ping(self, request: Request):
        with open("output.temp.txt", "a") as file:
            file.write(f"{datetime.datetime.now()}: {request.remote}\r\n")
        return json_response({"timestamp": datetime.datetime.now().isoformat()})


async def server_runner(server: Server):
    print("Starting server...")

    app_runner = web.AppRunner(server._app)
    await app_runner.setup()

    site = web.TCPSite(app_runner, host=server._host, port=server._port)
    await site.start()

    print(f"Server started on {site._host}:{site._port}.")


# Test functions
if __name__ == "__main__":
    _TEST_REQUEST_PAYLOADS = {
        "/enqueue": {"instructId": "TEST"},
        "/instruct": {"instructId": "TEST"},
        "/distance": {},
        "/color": {"port": 1},
    }

    async def _request_runner(server: Server, method: str, path: str, data: dict):
        await asyncio.sleep(1)
        async with ClientSession() as session:
            async with session.request(
                method, f"http://localhost:{server._port}{path}", json=data
            ) as response:
                print(f"\nResponse from {method} request to {path}: {response.status}")
                print(f"Response type: {response.content_type}")
                print(await response.text())

    def get_requests(_server: Server):
        # TODO: Fix "/command/{argument}" type of routes to work with the test runner.
        requests: list[tuple[callable, str, str, dict]] = []
        for route in _server.routes:
            payload = _TEST_REQUEST_PAYLOADS.get(route[1], {})
            if not payload:
                payload = {}
            requests.append((_request_runner, route[0], route[1], payload))
        return requests

    async def gather_tasks(
        server: Server, requests: list[tuple[callable, str, str, dict]]
    ):
        tasks = [server_runner(server)]
        for request_runner, method, path, data in requests:
            print(f"Adding task for {method} request to {path}...")
            tasks.append(request_runner(server, method, path, data))
        await asyncio.gather(*tasks)

    import asyncio
    from pathlib import Path

    _instructs_config = (
        Path(__file__).resolve().parent.parent / "server_data" / "instructs.yml"
    )
    controller = Controller(instructs_config_path=str(_instructs_config))
    server = Server(controller, host="localhost", port=5000)
    test_requests: list[tuple[callable, str, str, dict]] = get_requests(server)

    asyncio.run(gather_tasks(server, test_requests))
    print("Goodbye.")
