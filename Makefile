sync:
	uv sync

flash:
	uv run pybricksdev run ble ./hub/hub_controller.py

server:
	./start.sh

server-win:
	powershell -ExecutionPolicy Bypass ./start.ps1
