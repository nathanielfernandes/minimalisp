from os import access
from typing import Union
import math
from Lexer import TokenType, Token
from Parser import Context, Atom, Expression, Function
import operator as op
from functools import reduce


NIL = Atom(value="NIL", type=TokenType.SYMBOL)
T = Atom(value="T", type=TokenType.SYMBOL)


def defun(ctx: Context, name: Atom, args: Expression, *body: list[Expression]) -> Atom:
    def func(_, *params) -> Atom:
        scope = Context(parent=ctx)

        for key, value in zip(args.value, params):
            scope.Set(key.value, value)

        for b in body:
            result = b(scope)
        return result

    f = Function(func)
    ctx.Set(name.value, f)
    return f


def _lambda(ctx: Context, args: Expression, *body: list[Expression]) -> Atom:
    def func(_, *params) -> Atom:
        scope = Context(parent=ctx)

        for key, value in zip(args.value, params):
            scope.Set(key.value, value)

        for b in body:
            result = b(scope)

        return result

    return Function(func)


def progn(ctx: Context, *body: list[Expression]) -> Atom:
    for b in body:
        result = b(ctx)

    return result


def loop(ctx: Context, func: Atom, n: Atom) -> Atom:
    for _ in range(n.value):
        result = func(ctx)

    return result


def dotimes(ctx: Context, args: Expression, body: Expression) -> Atom:
    scope = Context(parent=ctx)
    for i in range(args.value[1](ctx).value):
        scope.Set(args.value[0].value, Atom(type=TokenType.INTEGER, value=i))
        result = body(scope)

    if len(args.value) > 2:
        result = args.value[2](ctx).value

    return result


def let(ctx: Context, args: Expression, *body: list[Expression]) -> Atom:
    scope = Context(parent=ctx)

    for arg in args.value:
        scope.Set(arg.value[0].value, arg.value[1])

    for b in body:
        result = b(scope)

    return result


def do(
    ctx: Context, args: Expression, end: Expression, *body: list[Expression]
) -> Atom:
    scope = Context(parent=ctx)

    incs = []
    for arg in args.value:
        scope.Set(arg.value[0].value, arg.value[1])
        incs.append(
            (arg.value[0].value, arg.value[2] if len(arg.value) > 2 else arg.value[1])
        )

    incs.reverse()
    while end.value[0](scope) == NIL:
        for b in body:
            b(scope)

        for variable, func in incs:
            scope.Set(variable, func(scope))

    return end.value[1](scope) if len(end.value) > 1 else NIL


def iterate_over_atom(ctx: Context, iterable: Atom) -> Atom:
    if iterable.type == TokenType.ARRAY or iterable.type == TokenType.STRING:
        for atom in iterable.value:
            yield atom
    else:
        n = iterable
        yield car(ctx, n)
        while (n := cdr(ctx, n)) != NIL:
            yield car(ctx, n)


def dolist(ctx: Context, args: Expression, *body: list[Expression]) -> Atom:
    scope = Context(parent=ctx)

    for atom in iterate_over_atom(ctx, args.value[1](ctx)):
        scope.Set(args.value[0].value, atom)

        for b in body:
            result = b(scope)

    if len(args.value) == 3:
        result = args.value[2](scope)

    return result


def aref(ctx: Context, iterable: Atom, index: Atom) -> Atom:
    return iterable.value[index.value]


def _if(
    ctx: Context, condition: Expression, then: Expression, _else: Expression = None
) -> Atom:

    if condition(ctx) != NIL:
        return then(ctx)
    elif _else:
        return _else(ctx)
    else:
        return NIL


def _when(ctx: Context, condition: Expression, *then: list[Expression]) -> Atom:
    if condition(ctx) != NIL:
        for t in then:
            result = t(ctx)
        return result

    return NIL


def cond(ctx: Context, *conditions: list[Expression]) -> Atom:
    for pair in conditions:
        c = pair.value[0]
        body = pair.value[1:]

        if c(ctx) != NIL:
            result = NIL
            for b in body:
                result = b(ctx)
            return result

    return NIL


def _repr(_ctx: Context, atom: Atom) -> Atom:
    atom.print()
    return atom


def defvar(ctx: Context, name: Atom, value: Atom = None) -> Atom:
    if name.type != TokenType.SYMBOL:
        raise Exception("Variable not a symbol")

    ctx.set_on_parent(name.value, value(ctx) if value else NIL)
    return value


def setf(ctx: Context, atom: Atom, value: Atom) -> Atom:
    # if atom.value not in ctx.scope:
    #     raise Exception(f"The VARIABLE {atom.value} is UNBOUND")
    ctx.FindAndSet(atom.value, value(ctx))

    return value


def STD_MATH() -> dict:
    return {k: v for k, v in vars(math).items() if callable(v)}


def build_list(l: list[Union[Atom, Token]], end: Atom = None):
    if len(l) == 1:
        return Atom(
            [
                Atom(value=l[0].value, type=l[0].type)
                if isinstance(l[0], Token)
                else l[0],
                end or NIL,
            ],
            TokenType.LIST,
        )

    return Atom(
        [
            Atom(value=l[0].value, type=l[0].type) if isinstance(l[0], Token) else l[0],
            build_list(l[1:]),
        ],
        TokenType.LIST,
    )


def _list(ctx: Context, *items: list[Atom]) -> Atom:
    return build_list(items)


def car(_ctx: Context, l: Atom) -> Atom:
    if isinstance(l.value, Atom):
        return l.value.value[0]

    return l.value[0]


def cdr(_ctx: Context, l: Atom) -> Atom:
    if isinstance(l.value, Atom):
        return Atom(l.value[-1], TokenType.LIST)

    return l.value[-1]


def elt(ctx: Context, iterable: Atom, index: Atom) -> Atom:
    for i, atom in enumerate(iterate_over_atom(ctx, iterable)):
        if i == index.value:
            return atom

    raise Exception("Index Out of Bounds")


def cons(ctx: Context, a: Atom, b: Atom) -> Atom:
    return build_list([a], end=b)


def _str(ctx: Context, v: Atom) -> str:
    if isinstance(v, Atom):
        if v.type == TokenType.STRING:
            return f'"{v.value}"'
        elif v.type == TokenType.LIST:
            s = [str(atom.value) for atom in iterate_over_atom(ctx, v)]
            return "(" + " ".join(s) + ")"

        else:
            return str(v.value)
    else:
        return str(v)


def _format(ctx: Context, stdout: Atom, fstring: Atom, *args: list[Atom]) -> Atom:
    out = fstring.value.replace("~%", "\n").replace("~s", "{}").replace("~S", "{}")
    out = out.format(*[_str(ctx, a) for a in args])

    if stdout != NIL:
        print(out, end="")

    return Atom(value=out, type=TokenType.STRING)


def _print(ctx: Context, v: Atom) -> Atom:
    if isinstance(v, Atom):
        if v.type == TokenType.STRING:
            print(f'"{v.value}"')
        elif v.type == TokenType.LIST:
            s = [_str(ctx, atom) for atom in iterate_over_atom(ctx, v)]
            print("(" + " ".join(s) + ")")
        elif v.type == TokenType.ARRAY:
            print("#(" + " ".join([_str(ctx, e) for e in v.value]) + ")")
        else:
            print(v.value)
    else:
        print(v)

    return NIL


reserved = {
    "defun": defun,
    "if": _if,
    "when": _when,
    "repr": _repr,
    "loop": loop,
    "do": do,
    "dotimes": dotimes,
    "progn": progn,
    "let": let,
    "defvar": defvar,
    "setf": setf,
    "cond": cond,
    "lambda": _lambda,
    "dolist": dolist,
}


def STD_LIB() -> Context:
    builtins = dict(reserved)
    builtins.update(
        {
            "T": T,
            "NIL": NIL,
            "t": T,
            "nil": NIL,
            "print": _print,
            "aref": aref,
            "elt": elt,
            "format": _format,
            "list": _list,
            "car": car,
            "cdr": cdr,
            "cons": cons,
            ">": lambda ctx, a, b: T if a(ctx).value > b(ctx).value else NIL,
            "<": lambda ctx, a, b: T if a(ctx).value < b(ctx).value else NIL,
            ">=": lambda ctx, a, b: T if a(ctx).value >= b(ctx).value else NIL,
            "<=": lambda ctx, a, b: T if a(ctx).value <= b(ctx).value else NIL,
            "=": lambda ctx, a, b: T if a(ctx).value == b(ctx).value else NIL,
            "and": lambda _, a, b: T if (a != NIL and b != NIL) else NIL,
            "or": lambda _, a, b: T if (a != NIL or b != NIL) else NIL,
            "atom": lambda _, a: T if a.type != TokenType.LIST else NIL,
            "caar": lambda ctx, a: car(ctx, car(ctx, a), a),
            "cadr": lambda ctx, a: car(ctx, cdr(ctx, a), a),
            "cdar": lambda ctx, a: cdr(ctx, car(ctx, a), a),
            "cddr": lambda ctx, a: cdr(ctx, cdr(ctx, a), a),
            "caaar": lambda ctx, a: car(ctx, car(ctx, car(ctx, a), a)),
            "caadr": lambda ctx, a: car(ctx, car(ctx, cdr(ctx, a), a)),
            "cadar": lambda ctx, a: car(ctx, cdr(ctx, car(ctx, a), a)),
            "caddr": lambda ctx, a: car(ctx, cdr(ctx, cdr(ctx, a), a)),
            "cdaar": lambda ctx, a: cdr(ctx, car(ctx, car(ctx, a), a)),
            "cdadr": lambda ctx, a: cdr(ctx, car(ctx, cdr(ctx, a), a)),
            "cddar": lambda ctx, a: cdr(ctx, cdr(ctx, car(ctx, a), a)),
            "cdddr": lambda ctx, a: cdr(ctx, cdr(ctx, cdr(ctx, a), a)),
        }
    )
    builtins.update(
        Context.Build(
            {
                "+": lambda *x: reduce(op.add, x),
                "-": lambda *x: reduce(op.sub, x),
                "*": lambda *x: reduce(op.mul, x),
                "/": lambda *x: reduce(op.truediv, x),
                "//": lambda *x: reduce(op.floordiv, x),
                "%": lambda *x: reduce(lambda a, b: a % b, x),
                "rem": lambda *x: reduce(lambda a, b: a % b, x),
                "abs": abs,
                "append": lambda a, v: a.append(v),
                "length": lambda x: len(x),
            }
        )
    )
    builtins.update(Context.Build(STD_MATH()))
    builtins.update(Context.Build({"robert": lambda n: print("woof\n" * n)}))

    return Context(parent=Context(scope=builtins, builtin=True))
