"""Sample Python code used as test fixture for Python analyzer tests."""


def greet(name: str) -> str:
    return f"Hello, {name}"


def add(a: int, b: int) -> int:
    return a + b


class Calculator:
    def multiply(self, x: int, y: int) -> int:
        return x * y


# Insecure code examples for detection testing
def insecure_sql(user_id: str) -> None:
    query = "SELECT * FROM users WHERE id = " + user_id


def insecure_command(cmd: str) -> None:
    import subprocess
    subprocess.call(cmd, shell=True)


def insecure_eval(code: str) -> None:
    eval(code)
