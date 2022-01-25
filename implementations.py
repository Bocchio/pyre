"""Module with the assembly implementation for each operator."""
import sys
from definitions import Token, Operator

def _ADD(self):
    pass
def _SUB(self):
    pass
def _MUL(self):
    pass
def _PEEK(self):
    pass
def _DROP(self):
    pass
def _ROT2(self):
    pass
def _DROT2(self):
    pass
def _ROT3(self):
    pass
def _DUP(self):
    pass
def _DUP2(self):
    pass
def _DUP3(self):
    pass
def _LOAD(self):
    pass
def _STORE(self):
    pass
def _MEMORY(self):
    pass
def _PRINT(self):
    pass
def _EQUAL(self):
    pass
def _NOT_EQUAL(self):
    pass
def _LESS_THAN(self):
    pass
def _GREATER_THAN(self):
    pass
def _LESS_OR_EQUAL_THAN(self):
    pass
def _GREATER_OR_EQUAL_THAN(self):
    pass
def _IF(self):
    pass
def _ELSE(self):
    pass
def _END(self):
    pass
def _WHILE(self):
    pass
def _DO(self):
    pass
def _PUTCHAR(self):
    pass
def _PROCEDURE(self):
    pass
def _PROCEDURE_CALL(self):
    pass
def _PUSH_UINT(self):
    pass
def _PUSH_CHAR(self):
    pass
def _PUSH_STRING(self):
    pass


def operator_to_implementation(operator):
    this_module = sys.modules[__name__]
    return getattr(this_module, '_' + operator.name)
