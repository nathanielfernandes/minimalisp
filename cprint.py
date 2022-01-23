HEADER = "\033[95m"
OKBLUE = "\033[94m"
OKCYAN = "\033[96m"
OKGREEN = "\033[92m"
WARNING = "\033[93m"
FAIL = "\033[91m"
ENDC = "\033[0m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"


def c(text: str, color) -> str:
    return f"{color}{text}{ENDC}"


def cprint(text: str, color):
    print(c(text, color))


def header(text: str):
    cprint(text, HEADER)


def okblue(text: str):
    cprint(text, OKBLUE)


def okcyan(text: str):
    cprint(text, OKBLUE)


def okgreen(text: str):
    cprint(text, OKGREEN)


def warning(text: str):
    cprint(text, WARNING)


def fail(text: str):
    cprint(text, FAIL)
