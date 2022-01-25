"""Type definitions."""
import sys
from dataclasses import dataclass, fields
from enum import Enum, auto
from typing import Any
from types import MethodType
from parsing_utils import string_to_db
import global_state


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
    PRINT                 = 'print'                 # noqa e241
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

    PUSH_UINT             = Literal.UINT            # noqa e241
    PUSH_CHAR             = Literal.CHAR            # noqa e241
    PUSH_STRING           = Literal.STRING          # noqa e241

    MACRO                 = 'macro'                 # noqa e241
    MACRO_EXPANSION       = Lexeme.MACRO_EXPANSION  # noqa e241

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

    # def __new__(cls, *_args, **__kwargs):
    #     cls.__init = cls.__init__

    #     def __init__(self, *args, **kwargs):
    #         self.__init(*args, **kwargs)
    #         self._bind_methods()

    #     cls.__init__ = __init__

    #     obj = super().__new__(cls)
    #     return obj

    # def _bind_methods(self):
    #     """
    #     Bind fields that should be methods but aren't methods yet to this instance.

    #     This method is called right after creating the object.
    #     If that wasn't the case then we could accomplish the same doing:
    #         token = Token(...)._bind_methods()
    #     But luckily it is the case.
    #     There's no need to call this method more than once.

    #     I know, this is just evil.
    #     """
    #     for item in fields(self):
    #         member = getattr(self, item.name)
    #         if member is None:
    #             continue
    #         if item.type is MethodType and not isinstance(member, MethodType):
    #             setattr(self, item.name, MethodType(member, self))
    #     return self


def lexeme_to_operator(lexeme):
    lexeme_to_operator_dict = {item.value: item for item in Operator}
    return lexeme_to_operator_dict[lexeme]


def create_token_basic(operator, value, code_iterator):
    return Token(operator, value=value)

def create_token_SWAP(operator, value, code_iterator):
    return operator_to_token(Operator.ROT2, value, code_iterator)


def create_token_PUSH_STRING(operator, value, code_iterator):
    value, length = string_to_db(value)
    token = Token(Operator.PUSH_STRING,
                  value=value,
                  length=length,
                  label=f'string_literal{global_state.string_literals}')
    global_state.string_literals += 1
    return token

def create_token_MACRO(operator, value, code_iterator):
    name = next(code_iterator)
    global_state.macros[name] = []
    token = Token(Operator.MACRO, value=name)
    return token

def create_token_MACRO_EXPANSION(operator, value, code_iterator):
    assert value in global_state.macros, f'Unrecognized macro {value}'
    token = Token(Operator.MACRO_EXPANSION, value=value)
    return token

def create_token_PROCEDURE(operator, value, code_iterator):
    name = next(code_iterator)
    global_state.procedures |= {name}
    token = Token(Operator.PROCEDURE, value=name)
    return token


def operator_to_token(operator, value, code_iterator):
    this_module = sys.modules[__name__]
    create_token = getattr(this_module, 'create_token_' + operator.name, create_token_basic)
    return create_token(operator, value, code_iterator)
