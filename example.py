from Parser import Parser
from std import STD_LIB

parser = Parser()

# Parser.Repl(ctx)

with open("test.lisp", "r") as f:
    parser.Read(f.read())

ctx = STD_LIB()  # or Context()


@ctx.func
def fibb(n: int) -> int:
    if n == 0:
        return 0
    if n == 1:
        return 1

    return fibb(n - 1) + fibb(n - 2)


# parser.Print()
parser.Run(ctx)
