"""Type definitions."""
from dataclasses import dataclass, fields
from enum import Enum, auto
from typing import Any
from types import MethodType


class Literal(Enum):
    """Literal types."""

    STRING = auto()
    CHAR = auto()
    UINT = auto()


class Lexeme(Enum):
    """
    I don't know how to call this.

    Names maybe?
    """

    MACRO_EXPANSION = auto()
    PROCEDURE_CALL = auto()


class Operator(Enum):
    """Every operator Pyre knows."""

    ADD                   = '+'                     # noqa e241
    SUB                   = '-'                     # noqa e241
    MUL                   = '*'                     # noqa e241
    PEEK                  = 'peek'                  # noqa e241
    DROP                  = 'drop'                  # noqa e241
    ROT2                  = 'rot2'                  # noqa e241
    SWAP                  = 'swap'                  # noqa e241 same as ROT2
    DROT2                 = 'drot2'                 # noqa e241
    ROT3                  = 'rot3'                  # noqa e241
    DUP                   = 'dup'                   # noqa e241
    DUP2                  = '2dup'                  # noqa e241
    DUP3                  = '3dup'                  # noqa e241
    LOAD                  = 'load'                  # noqa e241
    STORE                 = 'store'                 # noqa e241
    MEMORY                = 'memory'                # noqa e241
    EQUAL                 = '='                     # noqa e241
    NOT_EQUAL             = '!='                    # noqa e241
    LESS_THAN             = '<'                     # noqa e241
    GREATER_THAN          = '>'                     # noqa e241
    LESS_OR_EQUAL_THAN    = '<='                    # noqa e241
    GREATER_OR_EQUAL_THAN = '>='                    # noqa e241
    IF                    = 'if'                    # noqa e241
    ELSE                  = 'else'                  # noqa e241
    END                   = 'end'                   # noqa e241
    WHILE                 = 'while'                 # noqa e241
    DO                    = 'do'                    # noqa e241
    PUTCHAR               = 'putchar'               # noqa e241
    PROCEDURE             = 'procedure'             # noqa e241
    PROCEDURE_CALL        = Lexeme.PROCEDURE_CALL   # noqa e241

    IMPORT                = 'import'                # noqa e241

    SYSCALL               = 'syscall'               # noqa e241

    PUSH_UINT             = Literal.UINT            # noqa e241
    PUSH_CHAR             = Literal.CHAR            # noqa e241
    PUSH_STRING           = Literal.STRING          # noqa e241

    MACRO                 = 'macro'                 # noqa e241
    MACRO_EXPANSION       = Lexeme.MACRO_EXPANSION  # noqa e241

    DEFINE                = 'define'                # noqa e241

    def __repr__(self):
        return f'{self.__class__.__name__}.{self.name}'


@dataclass
class Token:
    """A token in the program."""

    operator: Operator
    # This ends up being a method, but you need to pass in a regular callable
    implementation: MethodType = None
    value: Any = None

    # Useful when dealing with strings
    length: int = None

    # Useful when dealing with block operations
    block: bool = None
    address: int = None
    label: str = None

    start_token = None
    end_token = None

    def __new__(cls, *_, **__):
        obj = super().__new__(cls)
        obj.__init = cls.__init__

        def __init__(self, *args, **kwargs):
            obj.__init(self, *args, **kwargs)
            self.bind_methods()

        cls.__init__ = __init__

        return obj

    def bind_methods(self):
        """
        Bind fields that should be methods but aren't methods yet to this instance.

        This method is called right after creating the object.
        If that wasn't the case then we could accomplish the same doing:
            token = Token(...)._bind_methods()
        But luckily it is the case.
        There's no need to call this method more than once.

        I know, this is just evil.
        """

        for item in fields(self):
            member = getattr(self, item.name)
            if member is None:
                continue
            if item.type is MethodType:
                if not isinstance(member, MethodType):
                    setattr(self, item.name, MethodType(member, self))
                elif member.__self__ is not self:
                    setattr(self, item.name, MethodType(member.__func__, self))
        return self
