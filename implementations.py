# noqa e302
"""Module with the assembly implementation for each operator."""
import sys
import global_state
from definitions import Token, Operator
from parsing_utils import string_to_db


def _ADD(self):
    return [
        '    pop     rax',
        '    pop     rbx',
        '    add     rax, rbx',
        '    push    rax'
    ]
def _SUB(self):
    return [
        '    pop     rax',
        '    pop     rbx',
        '    sub     rbx, rax',
        '    push    rbx'
    ]
def _MUL(self):
    return [
        '    pop     rax',
        '    pop     rbx',
        '    imul     rax, rbx',
        '    push    rax'
    ]
def _PEEK(self):
    return [
        '    ;; PEEK',
        '    mov     rdi, [rsp]',
        '    call    peek',
    ]
def _DROP(self):
    return [
        '    pop     rdi'
    ]
def _ROT2(self):
    return [
        '    pop     rax',
        '    pop     rbx',
        '    push    rax',
        '    push    rbx',
    ]
_SWAP = _ROT2
def _DROT2(self):
    return [
        # a b c d
        # c d a b
        '    pop     rdx',
        '    pop     rcx',
        '    pop     rbx',
        '    pop     rax',
        '    push    rcx',
        '    push    rdx',
        '    push    rax',
        '    push    rbx',
    ]
def _ROT3(self):
    return [
        '    pop     rax',
        '    pop     rbx',
        '    pop     rcx',
        '    push    rbx',
        '    push    rax',
        '    push    rcx',
    ]
def _DUP(self):
    return [
        '    pop     rax',
        '    push    rax',
        '    push    rax'
    ]
def _DUP2(self):
    return [
        '    pop     rbx',
        '    pop     rax',
        '    push    rax',
        '    push    rbx',
        '    push    rax',
        '    push    rbx'
    ]
def _DUP3(self):
    return [
        '    pop     rcx',
        '    pop     rbx',
        '    pop     rax',
        '    push    rax',
        '    push    rbx',
        '    push    rcx',
        '    push    rax',
        '    push    rbx',
        '    push    rcx',
    ]
def _LOAD(self):
    return [
        '    pop    rax',
        '    mov    rbx, 0',  # Clear rbx
        '    mov    bl, [rax]',  # Read one byte into rbx
        '    push   rbx',
    ]
def _STORE(self):
    return [
        '    pop    rbx',
        '    pop    rax',
        '    mov    [rax], bl',  # Write one byte from rbx
    ]
def _MEMORY(self):
    return [
        '    push    memory',
    ]
def _EQUAL(self):
    return [
        '    mov     rcx, FALSE',
        '    mov     rdx, TRUE',
        '    pop     rax',
        '    pop     rbx',
        '    cmp     rax, rbx',
        '    cmove   rcx, rdx',
        '    push    rcx'
    ]
def _NOT_EQUAL(self):
    return [
        '    mov     rcx, FALSE',
        '    mov     rdx, TRUE',
        '    pop     rax',
        '    pop     rbx',
        '    cmp     rax, rbx',
        '    cmovne  rcx, rdx',
        '    push    rcx'
    ]
def _LESS_THAN(self):
    return [
        '    mov     rcx, FALSE',
        '    mov     rdx, TRUE',
        '    pop     rax',
        '    pop     rbx',
        '    cmp     rbx, rax',
        '    cmovl   rcx, rdx',
        '    push    rcx'
    ]
def _GREATER_THAN(self):
    return [
        '    mov     rcx, FALSE',
        '    mov     rdx, TRUE',
        '    pop     rax',
        '    pop     rbx',
        '    cmp     rbx, rax',
        '    cmovg   rcx, rdx',
        '    push    rcx'
    ]
def _LESS_OR_EQUAL_THAN(self):
    return [
        '    mov     rcx, FALSE',
        '    mov     rdx, TRUE',
        '    pop     rax',
        '    pop     rbx',
        '    cmp     rbx, rax',
        '    cmovle   rcx, rdx',
        '    push    rcx'
    ]
def _GREATER_OR_EQUAL_THAN(self):
    return [
        '    mov     rcx, FALSE',
        '    mov     rdx, TRUE',
        '    pop     rax',
        '    pop     rbx',
        '    cmp     rbx, rax',
        '    cmovge   rcx, rdx',
        '    push    rcx'
    ]
def _IF(self):
    return [
        '    ;; IF',
        '    pop     rax',
        '    cmp     rax, TRUE',
        f'    jne      {self.end_token.label}'
    ]
def _ELSE(self):
    return [
        f'    jmp    {self.end_token.label}'
        '    ;; ELSE',
        f'{self.label}:'
    ]
def _END(self):
    start_token = self.start_token
    assert start_token is not None

    if start_token.operator is Operator.IF or start_token.operator is Operator.ELSE:
        return [
            f'{self.label}:'
        ]
    elif start_token.operator is Operator.DO:
        while_token = start_token.start_token
        assert while_token is not None
        return [
            f'    jmp    {while_token.label}',
            f'{self.label}:'
        ]
    elif start_token.operator is Operator.PROCEDURE:
        if start_token.value == 'main':
            return [
                '    ;; EXIT',
                '    mov     rdi, 0',  # Set exit code to 0
                '    mov     rax, SYS_EXIT',
                '    syscall',
            ]
        else:
            return [
                '    ret',
            ]
def _WHILE(self):
    return [
        f'{self.label}:'
    ]
def _DO(self):
    return [
        '    ;; DO',
        '    mov    rcx, TRUE',
        '    pop    rax',
        '    cmp    rax, TRUE',
        f'    jne    {self.end_token.label}'
    ]
def _PUTCHAR(self):
    return [
        '    ;; PUTCHAR',
        '    lea     rsi, [rsp]',
        '    mov     rdi, STD_OUT',
        '    mov     rdx, 1',
        '    mov     rax, SYS_WRITE',
        '    syscall',
        '    pop     rbx',  # Get rid of the character
    ]
def _PROCEDURE(self):
    return [
        f'{self.label}:',
        '    push    rdi'
    ]
def _PROCEDURE_CALL(self):
    return [
        f'   ;; CALL {self.value}',
        f'   call    {self.value}'
    ]
def _SYSCALL(self):
    assert 0 <= self.value <= 5
    syscall_args = ['rdi', 'rsi', 'rdx', 'r10', 'r8', 'r9']
    arguments = syscall_args[:self.value]
    start = [
        '    ;; SYSCALL',
        '    pop rax',
    ]
    middle = [f'    pop {arg}' for arg in arguments]
    end = [
        '    syscall'
    ]
    return start + middle + end
def _PUSH_UINT(self):
    return [
        f'    push    {self.value}'
    ]
def _PUSH_CHAR(self):
    return [
        f'    push    {self.value}'
    ]
def _PUSH_STRING(self):
    if self not in global_state.add_symbols:
        global_state.add_symbols.append(self)
    return [
        f'    push    {self.label}',
        f'    push    {self.length}'
    ]


# TODO make this a bit more automatic
def _MACRO(self):
    raise RuntimeError('Macro operator reached assembly code')
def _MACRO_EXPANSION(self):
    raise RuntimeError('Macro expansion operator reached assembly code')
def _IMPORT(self):
    raise RuntimeError('Import operator reached assembly code')
def _DEFINE(self):
    raise RuntimeError('Define operator reached assembly code')


def operator_to_implementation(operator):
    this_module = sys.modules[__name__]
    return getattr(this_module, '_' + operator.name)


def get_implementation(operator):
    this_module = sys.modules[__name__]
    return getattr(this_module, '_' + operator.name)


def lexeme_to_operator(lexeme):
    lexeme_to_operator_dict = {item.value: item for item in Operator}
    return lexeme_to_operator_dict[lexeme]


def create_token_basic(operator, value, code_iterator, implementation):
    token = Token(operator, value=value, implementation=implementation)
    return token


def create_token_SWAP(operator, value, code_iterator, implementation):
    return operator_to_token(Operator.ROT2, value, code_iterator, implementation)


def create_token_PUSH_STRING(operator, value, code_iterator, implementation):
    value, length = string_to_db(value)
    token = Token(Operator.PUSH_STRING,
                  value=value,
                  length=length,
                  label=f'string_literal{global_state.string_literals}',
                  implementation=implementation)
    global_state.string_literals += 1
    return token


def create_token_MACRO(operator, value, code_iterator, implementation):
    name = next(code_iterator)
    global_state.macros[name] = []
    token = Token(Operator.MACRO, value=name)
    return token


def create_token_IMPORT(operator, value, code_iterator, implementation):
    filename = next(code_iterator)
    global_state.imports[filename] = []
    token = Token(Operator.MACRO, value=filename)
    return token


def create_token_MACRO_EXPANSION(operator, value, code_iterator, implementation):
    assert value in global_state.macros, f'Unrecognized macro {value}'
    token = Token(Operator.MACRO_EXPANSION, value=value)
    return token


def create_token_PROCEDURE(operator, value, code_iterator, implementation):
    name = next(code_iterator)
    global_state.procedures |= {name}
    token = Token(Operator.PROCEDURE, value=name, implementation=implementation)
    return token


def operator_to_token(operator, value, code_iterator, implementation):
    this_module = sys.modules[__name__]
    create_token = getattr(this_module, 'create_token_' + operator.name, create_token_basic)
    return create_token(operator, value, code_iterator, implementation)
