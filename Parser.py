from __future__ import annotations
from ast import Expression
from pyclbr import Function
from typing import Union, Any, Iterable
from cprint import *
from Reader import Reader
from Lexer import Lexer, TokenType, Token

from prompt_toolkit.shortcuts import prompt
from pygments.lexers.lisp import CommonLispLexer
from pygments.styles import get_style_by_name
from prompt_toolkit.styles import style_from_pygments_cls, merge_styles, Style
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.completion import WordCompleter


OUTPUT = ""


class Atom:
    def __init__(self, value: Any, type: TokenType = None) -> None:
        self.value = value
        self.type = type

    def __call__(
        self,
        ctx: Context,
    ) -> Atom:
        if self.type == TokenType.SYMBOL:
            return ctx.Get(self.value)

        return self

    def __eq__(self, other: Atom) -> bool:
        if not isinstance(other, Atom):
            return False
        return self.value == other.value and self.type == other.type

    # def __transpile__(self) -> str:
    #     return str(self.value)

    def print1(self, prefix="└───", depth=-1, child=False):
        d = ".\n" if depth == -1 else ""

        if child:
            t = ("    " * depth) + "│" + "   "
        else:
            t = "    " * (depth + 1)

        print(f"{d}{t}{prefix}" + repr(self))
        if isinstance(self.value, list):
            is_child = (
                not any([isinstance(j.value, list) for j in self.value])
                and prefix == "├───"
            )

            for i, v in enumerate(self.value):
                if i != len(self.value) - 1:
                    v.print("├───", depth + 1, is_child)
                else:
                    v.print("└───", depth + 1, is_child)

    def print(self, depth=-1):
        t = "    " * (depth + 1)

        print(f"{t}{repr(self)}")
        if isinstance(self.value, list):

            for i, v in enumerate(self.value):
                v.print(depth + 1)

    def __repr__(self) -> str:
        value = (
            ""
            if isinstance(self.value, list)
            else f'{c(" value=", FAIL)}[{c(self.value, OKGREEN)}]'
        )

        t = (
            ""
            if self.type is None
            else f"{c(' type=', WARNING)}[{c(str(self.type).replace('TokenType.', ''), OKGREEN)}]"
        )

        color = OKBLUE if not isinstance(self, Expression) else WARNING
        return (
            f"{c('<', FAIL)}{c(self.__class__.__name__, color)}{value}{t}{c('>', FAIL)}"
        )

    def traverse(self):
        if isinstance(self.value, list):
            for child in self.value:
                print(child)
                child.traverse()
        else:
            self.value.traverse()
            print(self)


class Context:
    def __init__(
        self,
        scope: dict[str, Atom] = None,
        parent: Context = None,
        builtin: bool = False,
    ) -> None:
        self.scope = scope or dict()
        self.parent = parent
        self.builtin = builtin

    def Get(self, key: str) -> Atom:
        if atom := self.scope.get(key):
            return atom

        if self.parent is not None:
            return self.parent.Get(key)

        raise Exception(f"The variable {key.upper()} is unbound")

    def Set(self, key: str, value: Atom):
        if self.parent.builtin and key in self.parent.scope:
            raise Exception("Cannot override builtins")
        self.scope[key] = value

    def FindAndSet(self, key: str, value: Atom) -> Atom:
        if key in self.scope:
            self.scope[key] = value
            return

        if self.parent is not None:
            return self.parent.FindAndSet(key, value)

        raise Exception(f"The variable {key.upper()} is unbound")

    def set_on_parent(self, key: str, value: Atom):
        if self.parent is not None and not self.parent.builtin:
            self.parent.set_on_parent(key, value)
        else:
            self.Set(key, value)

    def func(self, func):
        self.scope[func.__name__] = Context.wrap(func)
        return func

    @staticmethod
    def wrap(func):
        def function(ctx, *args):
            args = [
                arg(ctx).value if not isinstance(arg, Function) else arg for arg in args
            ]

            return Atom(func(*args))

        return Function(value=function)

    @staticmethod
    def Build(functions: dict) -> dict:
        ctx = {}
        for k, v in functions.items():
            ctx[k] = Context.wrap(v)

        return ctx


class Function(Atom):
    def __call__(self, ctx: Context, *args) -> Atom:
        return self.value(ctx, *args)


class Expression(Atom):
    def __call__(self, ctx: Context) -> Atom:
        from std import reserved

        function = self.value[0](ctx)

        if isinstance(self.value[0], Expression):
            if isinstance(function, Atom):
                function = function.value(ctx, *[arg(ctx) for arg in self.value[1:]])
            else:
                function = function(ctx, *[arg(ctx) for arg in self.value[1:]])
        else:
            if self.value[0].value in reserved:
                args = [arg for arg in self.value[1:]]
            else:
                args = [arg(ctx) for arg in self.value[1:]]

            return function(ctx, *args)

    # def __transpile__(self) -> str:
    #     return (
    #         self.value[0].value
    #         + "("
    #         + ", ".join([arg.__transpile__() for arg in self.value[1:]])
    #         + ")"
    #     )


class Symbol(Atom):
    def __call__(self, _ctx: Context) -> Atom:
        return self


class Parser:
    def __init__(self) -> None:
        self.atoms = []

    def Print(self):
        for atom in self.atoms:
            atom.print()
            print("\n")

    def __parse__(self, reader: Reader[Token]) -> Atom:
        try:
            return (
                self.Symbol(reader)
                or self.Atom(reader)
                or self.Expression(reader)
                or self.Error(reader)
            )
        except:

            raise Exception(f"Syntax error at: {reader.stream}")

    def Parse(self, reader: Reader[Token]) -> Parser:
        while (read := reader.Peek()) is not None:
            self.atoms.append(self.__parse__(reader))

        return self

    def Read(self, code: str) -> Parser:
        lexer = Lexer()
        lexer.Read(code)
        return self.Parse(Reader(stream=lexer.tokens))

    def Repl(self, ctx: Context):
        print("Lisper Version 69.0\nGet Coding!\n")
        style = merge_styles(
            [
                style_from_pygments_cls(get_style_by_name("gruvbox-dark")),
                Style.from_dict({"repl": "#0cf54e"}),
            ]
        )

        lisp_completer = WordCompleter(list(ctx.scope.keys()))

        while True:
            code = prompt(
                message=[("class:repl", ">>> ")],
                lexer=PygmentsLexer(CommonLispLexer),
                style=style,
                include_default_pygments_style=False,
                completer=lisp_completer,
            )
            if code == "":
                continue

            if code == "quit":
                break

            lexer = Lexer()
            try:
                atom = self.__parse__(Reader(stream=lexer.Read(code).tokens))(ctx)
                if atom and atom.value:
                    print(atom.value)
            except Exception as e:
                cprint(e, FAIL)

    def Run(self, ctx: Context) -> Parser:
        for expression in self.atoms:
            expression(ctx)

        return self

    def Debug(self, ctx: Context, watch: list = []) -> Parser:
        for i, expression in enumerate(self.atoms):
            cprint(f"{i}: ", OKGREEN)
            print(expression.value)

            for w in watch:
                cprint(f"{w} = {ctx.scope.get(w)}", OKBLUE)

            input()
            expression(ctx)

        return self

    def Atom(self, reader: Reader[Token]) -> Union[Atom, None]:
        read = reader.Peek()
        if read.type.is_atom():
            n = reader.Next()

            if read.type == TokenType.LIST:
                from std import build_list

                return build_list(n.value)

            if read.type == TokenType.ARRAY:
                return Atom(
                    value=[Atom(value=a.value, type=a.type) for a in read.value],
                    type=TokenType.ARRAY,
                )

            return Atom(value=n.value, type=n.type)

    def Expression(self, reader: Reader[Token]) -> Union[Atom, None]:
        read = reader.Peek()
        if read.type == TokenType.OPEN_BRACKET:
            reader.Next()

            args = []
            while (read := reader.Peek()) and read.type != TokenType.CLOSING_BRACKET:
                args.append(self.__parse__(reader))

            reader.Next()
            return Expression(args)

    def Symbol(self, reader: Reader[Token]) -> Union[Atom, None]:
        read = reader.Peek()
        if read.type == TokenType.SPECIAL:
            n = reader.Next()
            return Symbol(value=n.value, type=n.type)

    def Error(self, reader):
        raise Exception("farter: ", reader.Peek())

    def get_out(self):
        return OUTPUT
