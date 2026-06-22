def print_title(name: str, version: str, path: str = None):
    """
    Prints the title and version of the application.

    Args:
        name (str): Name of the application.
        version (str): Version of the application.
        path (str, optional): Path to a text file containing a banner,
        or ASCII art of the application name. Defaults to None.
    """
    if path:
        with open(path, "r") as f:
            print(f.read())
    print(name)
    print("v%s" % version)


def print_kwargs(**kwargs):
    for key, value in kwargs.items():
        print(f" - {key}: {value}")


def print_tasks(tasks: dict):
    for task, args in tasks.items():
        print(f" - {task.__name__}:")
        for arg in args:
            print(f"   - {arg}")


def print_spacer(length: int = 40):
    print("-" * length)
