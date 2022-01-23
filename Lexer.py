from __future__ import annotations
from multiprocessing.dummy import Array
from typing import Any
from enum import Enum
import string
from Reader import Reader
from cprint import *


class TokenType(Enum):
    INTEGER = 0
    FLOAT = 1
    STRING = 2
    OPEN_BRACKET = 3
    CLOSING_BRACKET = 4
    SYMBOL = 5
    SPECIAL = 6
    SEMICOLON = 7
    LIST = 8
    ARRAY = 9

    def is_atom(self):
        return self != self.CLOSING_BRACKET and self != self.OPEN_BRACKET
        # return (
        #     self == TokenType.STRING
        #     or self == TokenType.INTEGER
        #     or self == TokenType.FLOAT
        #     or self == TokenType.SYMBOL
        #     or self == TokenType.SPECIAL
        #     or self == TokenType.LIST
        #     or self == TokenType.ARRAY
        # )


class Token:
    def __init__(self, type: TokenType, value: Any = None) -> None:
        self.type = type
        self.value = value

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self) -> str:
        return f"{c('<', FAIL)}{c(self.type, OKBLUE)} {c('value=', FAIL)}[{c(self.value, OKGREEN)}]{c('>', FAIL)}"


class Lexer:
    def __init__(self) -> None:
        self.tokens = []

    def Read(self, code: str) -> Lexer:
        reader = Reader(code)
        while reader.Peek():
            while (read := reader.Peek()) and read in " \n":
                reader.Next()

            if reader.Peek() is not None:
                self.Bracket(reader) or self.Array(reader) or self.List(
                    reader
                ) or self.Special(reader) or self.Number(reader) or self.String(
                    reader
                ) or self.Symbol(
                    reader
                ) or self.Comment(
                    reader
                ) or self.Error(
                    reader
                )

        return self

    def Error(self, reader: Reader):
        raise Exception(f"READ error during LOAD: {reader.Peek()}")

    def Number(self, reader: Reader) -> bool:
        if not (reader.Peek() in "-0123456789."):
            return False

        if reader.Peek() == "-" and not reader.Peek(2).isdigit():
            return False

        number = reader.Next()
        while (read := reader.Peek()) and read in "0123456789.":
            number += reader.Next()

        if "." in number:
            self.tokens.append(Token(TokenType.FLOAT, value=float(number)))
        else:
            self.tokens.append(Token(TokenType.INTEGER, value=int(number)))

        return True

    def String(self, reader: Reader) -> bool:
        if reader.Peek() != '"':
            return False

        reader.Next()
        string = ""
        while reader.Peek() != '"':
            string += reader.Next()

        reader.Next()
        self.tokens.append(Token(TokenType.STRING, value=string))

        return True

    bracket_map = {"(": TokenType.OPEN_BRACKET, ")": TokenType.CLOSING_BRACKET}

    def Bracket(self, reader: Reader) -> bool:
        if not (reader.Peek() in self.bracket_map):
            return False

        self.tokens.append(Token(type=self.bracket_map[reader.Next()]))
        return True

    symbol_chars = string.ascii_letters + "+-=/><*0123456789%?"

    def Symbol(self, reader: Reader) -> bool:
        if not (reader.Peek() in self.symbol_chars):
            return False

        symbol = reader.Next()
        while (read := reader.Peek()) and read in self.symbol_chars:
            symbol += reader.Next()

        self.tokens.append(Token(TokenType.SYMBOL, value=symbol))
        return True

    def Array(self, reader: Reader) -> bool:
        if reader.Peek() != "#":
            return False

        if reader.Peek(2) != "(":
            return False

        lst = ""
        reader.Next(2)
        symbols = []
        i = 0
        while (read := reader.Peek()) and read != ")":
            if read == "(":
                depth = 0
                sym = ""
                while True:
                    n = reader.Next()
                    sym += n
                    if n == "(":
                        depth += 1
                    elif n == ")":
                        depth -= 1

                        if depth == 0:
                            break

                lst += f'"{sym}"'
                symbols.append(i)
                i += 1
            else:
                n = reader.Next()
                lst += n
                if n == " ":
                    i += 1

        l = Lexer()

        list_elements = [
            Token(type=TokenType.SPECIAL, value=v.value) if i in symbols else v
            for i, v in enumerate(l.Read(lst).tokens)
        ]

        reader.Next()
        self.tokens.append(Token(TokenType.ARRAY, list_elements))

        return True

    def List(self, reader: Reader) -> bool:
        if reader.Peek() != "'":
            return False

        if reader.Peek(2) != "(":
            return False

        lst = ""
        reader.Next(2)
        symbols = []
        i = 0
        while (read := reader.Peek()) and read != ")":
            if read == "(":
                depth = 0
                sym = ""
                while True:
                    n = reader.Next()
                    sym += n
                    if n == "(":
                        depth += 1
                    elif n == ")":
                        depth -= 1

                        if depth == 0:
                            break

                lst += f'"{sym}"'
                symbols.append(i)
                i += 1
            else:
                n = reader.Next()
                lst += n
                if n == " ":
                    i += 1

        l = Lexer()

        list_elements = [
            Token(type=TokenType.SPECIAL, value=v.value) if i in symbols else v
            for i, v in enumerate(l.Read(lst).tokens)
        ]

        reader.Next()
        self.tokens.append(Token(TokenType.LIST, list_elements))

        return True

    def Special(self, reader: Reader) -> bool:
        if reader.Peek() != "'":
            return False

        reader.Next()
        symbol = reader.Next()
        while (read := reader.Peek()) and read in self.symbol_chars:
            symbol += reader.Next()

        self.tokens.append(Token(TokenType.SPECIAL, value=symbol.upper()))
        return True

    def Comment(self, reader: Reader) -> bool:
        if reader.Peek() != ";":
            return False

        while (read := reader.Peek()) and read != "\n":
            reader.Next()

        return True
