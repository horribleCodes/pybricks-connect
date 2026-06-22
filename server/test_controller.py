import asyncio
from pathlib import Path

from controller import Controller, controller_runner, _UPDATE_KEY

_INSTRUCTS_CONFIG = (
    Path(__file__).resolve().parent.parent / "server_data" / "instructs.yml"
)


async def _enqueue_exit_when_running(controller: Controller):
    while not controller.is_running():
        await asyncio.sleep(1)
    qsize, message = controller.exit()
    print(f"Size: {qsize} - {message}")


async def _test_main(controller: Controller):
    await asyncio.gather(
        controller_runner(controller), _enqueue_exit_when_running(controller)
    )


def _enqueue_and_print(controller: Controller, instruct_id: str):
    qsize, message = controller.enqueue(instruct_id)
    print(f"Size: {qsize} - {message}")


def _test_connection(hub_name="Pybricks Hub"):
    controller = Controller(hub_name, instructs_config_path=str(_INSTRUCTS_CONFIG))
    _enqueue_and_print(controller, _UPDATE_KEY)
    _enqueue_and_print(controller, "UNKNOWN")  # Test missing instruct
    _enqueue_and_print(controller, _UPDATE_KEY)
    qsize, message = controller.exit()
    print(f"Size: {qsize} - {message}")

    asyncio.run(_test_main(controller))


if __name__ == "__main__":
    _test_connection()
