"""Type definitions."""
from dataclasses import dataclass, fields
from enum import Enum, auto
from typing import Any, Type, Iterable
from types import MethodType
import re
import global_state


PROCEDURE_PREFIX = 'procedure_'


class Operator(Enum):
    """
    Every operator Pyre knows.

    Order matters because LexemeMatches uses the definition order that
    appears here.
    """

    # Arithmetic operations
    ADD                   = '+'                     # noqa e241
    SUB                   = '-'                     # noqa e241
    MUL                   = '*'                     # noqa e241
    DIV                   = '/'                     # noqa e241
    MOD                   = '%'                     # noqa e241

    # Logical operations
    EQUAL                 = '='                     # noqa e241
    NOT_EQUAL             = '!='                    # noqa e241
    LESS_THAN             = '<'                     # noqa e241
    GREATER_THAN          = '>'                     # noqa e241
    LESS_OR_EQUAL_THAN    = '<='                    # noqa e241
    GREATER_OR_EQUAL_THAN = '>='                    # noqa e241
    AND                   = 'and'                   # noqa e241
    OR                    = 'or'                    # noqa e241
    NOT                   = 'not'                   # noqa e241
    BOOL                  = 'bool'                  # noqa e241

    # Stack operations
    DROP                  = 'drop'                  # noqa e241
    ROT2                  = 'rot2'                  # noqa e241
    SWAP                  = 'swap'                  # noqa e241 same as ROT2
    DROT2                 = 'drot2'                 # noqa e241
    ROT3                  = 'rot3'                  # noqa e241
    DUP                   = 'dup'                   # noqa e241
    DUP2                  = '2dup'                  # noqa e241
    DUP3                  = '3dup'                  # noqa e241
    STACK_REFERENCE       = '@'                     # noqa e241

    # Memory operations
    # FIXME: These operations work with bytes
    #        We want to have similar operations that work with words
    LOAD1                 = 'load1'                 # noqa e241
    STORE1                = 'store1'                # noqa e241
    LOAD                  = 'load'                  # noqa e241
    STORE                 = 'store'                 # noqa e241
    MEMORY                = 'memory'                # noqa e241

    # Control flow
    IF                    = 'if'                    # noqa e241
    ELSE                  = 'else'                  # noqa e241
    ELIF                  = 'elif'                  # noqa e241
    END                   = 'end'                   # noqa e241
    WHILE                 = 'while'                 # noqa e241
    DO                    = 'do'                    # noqa e241
    WHERE                 = 'where'                 # noqa e241
    IN                    = 'in'                    # noqa e241

    # Other directives
    PROCEDURE             = 'procedure'             # noqa e241
    IMPORT                = 'import'                # noqa e241
    SYSCALL               = re.compile('syscall.')  # noqa e241
    DEFINE                = 'define'                # noqa e241
    MACRO                 = 'macro'                 # noqa e241

    # Directives for debugging purposes
    HARDPEEK              = 'hardpeek'              # noqa e241

    PROCEDURE_CALL        = global_state.procedures # noqa e241
    MACRO_EXPANSION       = global_state.macros     # noqa e241

    # We only type annotate addresses
    WRITE_TO              = re.compile('!([^:]+):?(.+)?\[(.*)?\]') # noqa e241
    DEREFERENCE           = re.compile('([^:]+):?(.+)?\[(.*)?\]')  # noqa e241
    MUTATE                = re.compile('!([^:]+)')                 # noqa e241

    AUTOINCREMENT         = re.compile('.+\+\+')    # noqa e241
    AUTODECREMENT         = re.compile('.+\-\-')    # noqa e241

    PUSH_UINT             = re.compile('[0-9]+')    # noqa e241
    PUSH_CHAR             = re.compile("'.?.'")     # noqa e241
    PUSH_STRING           = re.compile('".+"')      # noqa e241

    # Didn't match anything, so it's probably a variable
    # FIXME: We should keep track of variables while we tokenize the program
    #        Our problem right now is we don't have a mechanism for removing
    #        them of the symbols table during tokenization.
    RETRIEVE              = re.compile('.+')        # noqa e241

    def __repr__(self):
        return f'{self.__class__.__name__}.{self.name}'


def get_type_size(type_annotation):
    value_type_to_bytes = {
        'uint8' :    1,                 # noqa e241
        'uint16':    2,                 # noqa e241
        'uint32':    4,                 # noqa e241
        'uint64':    8,                 # noqa e241
        'char'  :    1                  # noqa e241
    }
    if type_annotation.isnumeric():
        return int(type_annotation)
    return value_type_to_bytes[type_annotation]


# FIXME: Implement types properly
def get_load_instruction(type_annotation):
    type_to_load_instruction = {
        'uint8' :    'load1',      # noqa e241
        'uint64':    'load',       # noqa e241
        'char'  :    'load1',      # noqa e241
        '1'     :    'load1',      # noqa e241
        '8'     :    'load'        # noqa e241
    }
    return type_to_load_instruction[type_annotation]

# FIXME: Implement types properly
def get_store_instruction(type_annotation):
    type_to_store_instruction = {
        'uint8' :    'store1',      # noqa e241
        'uint64':    'store',       # noqa e241
        'char'  :    'store1',      # noqa e241
        '1'     :    'store1',      # noqa e241
        '8'     :    'store'        # noqa e241
    }
    return type_to_store_instruction[type_annotation]


def lexeme_matches(item) -> Operator:
    def filter_operators(operators: Iterable, value_types: Iterable[Type]) -> Iterable:
        """Filter out all the operators whose value isn't of type value_type."""
        def does_value_match(operator):
            return any(isinstance(operator.value, value_type) for value_type in value_types)
        return filter(does_value_match, operators)

    # If the item is equal to the value of one operator
    # That's because it's a keyword and we are done
    for operator in filter_operators(Operator, [str]):
        if item == operator.value:
            return operator

    # If the item is exactly equal to one of the items in the value of one operator
    # That's because it's a label and we are done
    for operator in filter_operators(Operator, [list, dict]):
        if item in operator.value:
            return operator

    # No luck, we'll check with regular expressions
    for operator in filter_operators(Operator, [re.Pattern]):
        if operator.value.fullmatch(item) is not None:
            return operator

    raise ValueError(f'Lexeme {item} does not match any known operator')


stack_effect = {
    Operator.ADD                        : -1,     # noqae 241
    Operator.SUB                        : -1,     # noqae 241
    Operator.MUL                        : -1,     # noqae 241
    Operator.DIV                        : -1,     # noqae 241
    Operator.MOD                        : -1,     # noqae 241

    Operator.HARDPEEK                   :  0,     # noqae 241

    Operator.DROP                       : -1,     # noqae 241
    Operator.ROT2                       :  0,     # noqae 241
    Operator.SWAP                       :  0,     # noqae 241
    Operator.DROT2                      :  0,     # noqae 241
    Operator.ROT3                       :  0,     # noqae 241
    Operator.DUP                        :  1,     # noqae 241
    Operator.DUP2                       :  2,     # noqae 241
    Operator.DUP3                       :  3,     # noqae 241

    Operator.LOAD1                      :  0,     # noqae 241
    Operator.STORE1                     : -2,     # noqae 241
    Operator.LOAD                       :  0,     # noqae 241
    Operator.STORE                      : -2,     # noqae 241
    Operator.MEMORY                     :  1,     # noqae 241

    Operator.EQUAL                      : -1,     # noqae 241
    Operator.NOT_EQUAL                  : -1,     # noqae 241
    Operator.LESS_THAN                  : -1,     # noqae 241
    Operator.GREATER_THAN               : -1,     # noqae 241
    Operator.LESS_OR_EQUAL_THAN         : -1,     # noqae 241
    Operator.GREATER_OR_EQUAL_THAN      : -1,     # noqae 241

    Operator.IF                         :  0,     # noqae 241
    Operator.ELIF                       :  0,     # noqae 241
    Operator.ELSE                       :  0,     # noqae 241
    Operator.END                        :  0,     # noqae 241

    Operator.WHILE                      :  0,     # noqae 241
    Operator.DO                         : -1,     # noqae 241

    Operator.PROCEDURE                  :  0,     # noqae 241
    Operator.PROCEDURE_CALL             :  0,     # noqae 241

    Operator.WHERE                      :  0,     # noqae 241
    Operator.IN                         :  0,     # noqae 241

    Operator.RETRIEVE                   :  1,     # noqae 241
    Operator.MUTATE                     : -1,     # noqae 241

    Operator.STACK_REFERENCE            :  1,     # noqae 241
    Operator.DEREFERENCE                :  0,     # noqae 241

    Operator.IMPORT                     :  0,     # noqae 241

    Operator.SYSCALL                    :  1,     # noqae 241
    Operator.PUSH_UINT                  :  1,     # noqae 241
    Operator.PUSH_CHAR                  :  1,     # noqae 241
    Operator.PUSH_STRING                :  2,     # noqae 241

    Operator.MACRO                      : None,   # noqae 241
    Operator.MACRO_EXPANSION            : None,   # noqae 241
    Operator.DEFINE                     : None,   # noqae 241
}


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
