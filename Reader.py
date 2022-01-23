from __future__ import annotations
from typing import Generic, TypeVar

T = TypeVar("T")  # Declare type variable


class Reader(Generic[T]):
    def __init__(self, stream: list[T]) -> None:
        self.stream = stream
        self.index = 0

    def Next(self, amount: int = 1) -> T:
        if self.index > len(self.stream):
            return None
        self.index += amount
        return self.stream[self.index - 1]

    def Skip(self, amount: int = 1) -> Reader[T]:
        self.index += amount
        return self

    def Peek(self, amount: int = 1) -> T:
        peek_index = amount + self.index
        if peek_index > len(self.stream):
            return None
        return self.stream[peek_index - 1]
