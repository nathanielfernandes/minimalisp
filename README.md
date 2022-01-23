# Minimalisp

## Imagine a toy Lisp... but without a real use case

This was just a fun project made with the help of [my friend](https://github.com/fabyanMikhael).

## Implemented Features

- Running from a file or string
- Working Repl
- A simple debugging mode
- A wrapper for passing in regular python functions to lisp

```py
ctx = STD_LIB() # or Context()

@ctx.func
def fibb(n: int) -> int:
    if n == 0: return 0
    if n == 1: return 1

    return fibb(n - 1) + fibb(n - 2)

parser = Parser()
parser.Read("(print (fibb 9))")

parser.Run(ctx)
```

```
output: 34
```

## Types

- `Integer` `Float` `String` `Symbol` `List` `Array`

### Builtins

- `defun` `lambda`
- `if` `cond` `when`
- `do` `dotimes` `dolist`
- `let` `progn`
- `defvar`
- `setf`
- `print` `format`
- `list` `cons` `aref` `elt` `append` `length`
- `>` `<` `>=` `<=` `=`
- `and` `or`
- `atom`
- `car` `cdr` `caar` `cadr` `cdar` `cddr` `caaar` `caadr` `cadar` `caddr` `cdaar` `cdadr` `cddar` `cdddr`
- `+` `-` `*` `/` `//` `%` `rem`

## Example use

running lisp from file or string

```py
from Parser import Parser
from std import STD_LIB

parser = Parser()
with open("main.lisp", "r") as f:
    parser.Read(f.read())

ctx = STD_LIB()
parser.Run(ctx)
```

running the repl

```py
from Parser import Parser
from std import STD_LIB

ctx = STD_LIB()
Parser.Repl(ctx)
```

#### using `Parser.Print` or `(repr <atom>)` prints out how your lisp code is represented within the interpreter.

```lisp
(defun fizz-buzz (n)
    (dotimes (num n)
        (cond
            ((and (= (rem num 3) 0) (= (rem num 5) 0))
                (print "FizzBuzz"))
            ((= (rem num 3) 0)
                (print "Fizz"))
            ((= (rem num 5) 0)
                (print "Buzz"))
            (T (print num)))))


(fizz-buzz 20)
```

is represented as

```xml
<Expression>
    <Atom value=[defun] type=[SYMBOL]>
    <Atom value=[fizz-buzz] type=[SYMBOL]>
    <Expression>
        <Atom value=[n] type=[SYMBOL]>
    <Expression>
        <Atom value=[dotimes] type=[SYMBOL]>
        <Expression>
            <Atom value=[num] type=[SYMBOL]>
            <Atom value=[n] type=[SYMBOL]>
        <Expression>
            <Atom value=[cond] type=[SYMBOL]>
            <Expression>
                <Expression>
                    <Atom value=[and] type=[SYMBOL]>
                    <Expression>
                        <Atom value=[=] type=[SYMBOL]>
                        <Expression>
                            <Atom value=[rem] type=[SYMBOL]>
                            <Atom value=[num] type=[SYMBOL]>
                            <Atom value=[3] type=[INTEGER]>
                        <Atom value=[0] type=[INTEGER]>
                    <Expression>
                        <Atom value=[=] type=[SYMBOL]>
                        <Expression>
                            <Atom value=[rem] type=[SYMBOL]>
                            <Atom value=[num] type=[SYMBOL]>
                            <Atom value=[5] type=[INTEGER]>
                        <Atom value=[0] type=[INTEGER]>
                <Expression>
                    <Atom value=[print] type=[SYMBOL]>
                    <Atom value=[FizzBuzz] type=[STRING]>
            <Expression>
                <Expression>
                    <Atom value=[=] type=[SYMBOL]>
                    <Expression>
                        <Atom value=[rem] type=[SYMBOL]>
                        <Atom value=[num] type=[SYMBOL]>
                        <Atom value=[3] type=[INTEGER]>
                    <Atom value=[0] type=[INTEGER]>
                <Expression>
                    <Atom value=[print] type=[SYMBOL]>
                    <Atom value=[Fizz] type=[STRING]>
            <Expression>
                <Expression>
                    <Atom value=[=] type=[SYMBOL]>
                    <Expression>
                        <Atom value=[rem] type=[SYMBOL]>
                        <Atom value=[num] type=[SYMBOL]>
                        <Atom value=[5] type=[INTEGER]>
                    <Atom value=[0] type=[INTEGER]>
                <Expression>
                    <Atom value=[print] type=[SYMBOL]>
                    <Atom value=[Buzz] type=[STRING]>
            <Expression>
                <Atom value=[T] type=[SYMBOL]>
                <Expression>
                    <Atom value=[print] type=[SYMBOL]>
                    <Atom value=[num] type=[SYMBOL]>


<Expression>
    <Atom value=[fizz-buzz] type=[SYMBOL]>
    <Atom value=[20] type=[INTEGER]>
```

## Pros

- Some basic lisp functions have operations have been changed to be more pythonic.
- ie. lambdas, string operations, array operations

## Drawbacks

- The maximum recursion depth is easily hit when recursing inside lisp.
- There is no real use for this.
- Not every operation is vanilla lisp.
