# noqa e302
"""Module with the assembly implementation for each operator."""
import sys
import global_state
from definitions import Token, Operator, PROCEDURE_PREFIX
from parsing_utils import string_to_db
from definitions import PROCEDURE_PREFIX


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
def _MOD(self):
    return [
        '    xor     rdx, rdx',  # Clear rdx
        '    pop     rbx',
        '    pop     rax',
        '    idiv    rbx',
        '    push    rdx',
    ]
def _MUL(self):
    return [
        '    pop     rax',
        '    pop     rbx',
        '    imul     rax, rbx',
        '    push    rax'
    ]
def _DIV(self):
    return [
        '    xor     rdx, rdx',  # Clear rdx
        '    pop     rbx',
        '    pop     rax',
        '    idiv    rbx',
        '    push    rax'
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
def _LOAD1(self):
    return [
        '    pop     rax',
        '    mov     rbx, 0',  # Clear rbx
        '    mov     bl, [rax]',  # Read one byte into rbx
        '    push    rbx',
    ]
def _STORE1(self):
    return [
        '    pop     rax',
        '    pop     rbx',
        '    mov     [rax], bl',  # Write one byte from rbx
    ]
def _LOAD(self):
    return [
        '    pop     rax',
        '    mov     rbx, 0',  # Clear rbx
        '    mov     rbx, [rax]',  # Read into rbx
        '    push    rbx',
    ]
def _STORE(self):
    return [
        '    pop    rax',
        '    pop    rbx',
        '    mov    [rax], rbx',  # Write from rbx
    ]
def _WHERE(self):
    # TODO this can be way more efficient
    global_state.symbols.extend(self.value)
    inst = [f'    ;; {global_state.symbols}']
    variables = self.value
    for i, item in enumerate(variables):
        length = len(variables) - 1
        stack_location = (length - i) * 8
        inst.extend([
           f'    ;; Bind {item} {stack_location}',
            '    mov     rax, rsp',
           f'    add     rax, {stack_location}',  # rax has the address of the variable
            '    mov     rcx, [symbols]',         # rcx points to the last free slot
            '    mov     [rcx], rax',
            '    add rcx, 8',                     # update symbols so it points
            '    mov [symbols], rcx'              # to a free slot
        ])
    # print()
    return inst
def _RETRIEVE(self):
    i = global_state.symbols[::-1].index(self.value)
    location = i * 8 + 8
    return [
       f'    ;; {global_state.symbols}',
        '    mov     rcx, [symbols]',   # rcx points to the last free slot
       f'    sub     rcx, {location}',  # rcx points to the variable
        '    mov     rcx, [rcx]',
        '    mov     rax, [rcx]',
       f'    push    rax  ;; Push {self.value} onto the stack',
    ]
def _MUTATE(self):
    i = global_state.symbols[::-1].index(self.value)
    location = i * 8 + 8
    return [
         '    mov     rcx, [symbols]',
        f'    sub     rcx, {location}',
        f'    mov     rbx, [rcx]',
         '    pop     rax',
        f'    mov     [rbx], rax',
         '    xor     rax, rax',
    ]
def _HARDPEEK(self):
    return [
        '    mov     rdi, [rsp]',
        '    call    peek',
        '    mov     rdi, [rsp + 8]',
        '    call    peek',
        '    mov     rdi, [rsp + 16]',
        '    call    peek',
        '    mov     rdi, [rsp + 24]',
        '    call    peek',
    ]
def _DEREFERENCE(self):
    return [
        '   pop     rax',
        '   mov     rbx, [rax]',
        '   push    rbx',
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
        '    cmovle  rcx, rdx',
        '    push    rcx'
    ]
def _GREATER_OR_EQUAL_THAN(self):
    return [
        '    mov     rcx, FALSE',
        '    mov     rdx, TRUE',
        '    pop     rax',
        '    pop     rbx',
        '    cmp     rbx, rax',
        '    cmovge  rcx, rdx',
        '    push    rcx'
    ]
def _AND(self):
    return [
        '    pop     rax',
        '    pop     rbx',
        '    and     rax, rbx',
        '    push    rax'
    ]
def _OR(self):
    return [
        '    pop     rax',
        '    pop     rbx',
        '    or      rax, rbx',
        '    push    rax'
    ]
def _NOT(self):
    return [
        '    mov     rbx, TRUE',
        '    pop     rax',
        '    not     rax',
        '    and     rax, rbx',
        '    push    rax'
    ]
def _BOOL(self):
    return [
        '    mov     rbx, FALSE',
        '    mov     rcx, TRUE',
        '    pop     rax',
        '    cmp     rax, rbx',
        '    cmove   rcx, rbx',
        '    push    rcx'
    ]
def _IF(self):
    return [
        '',
        # '    pop     rax',
        # '    cmp     rax, TRUE',
        # f'    jne     {self.end_token.label}'
    ]
def _ELIF(self):
    return [
        f'    jmp     {self.end_token.label}',
        f'{self.label}:'
    ]
def _ELSE(self):
    return [
        f'    jmp     {self.end_token.label}',
        f'{self.label}:'
    ]
def _END(self):
    start_token = self.start_token
    assert start_token is not None

    if start_token.operator is Operator.IF or start_token.operator is Operator.ELSE:
        return [
            f'{self.label}:'
        ]
    elif start_token.operator is Operator.DO and start_token.start_token.operator is Operator.WHILE:
        while_token = start_token.start_token
        assert while_token.operator is Operator.WHILE
        return [
            f'    jmp     {while_token.label}',
            f'{self.label}:'
        ]
    elif start_token.operator is Operator.DO:
        return [
            f'{self.label}:'
        ]
    elif start_token.operator is Operator.WHERE:
        to_remove = len(start_token.value) * 8
        for variable in start_token.value:
            global_state.symbols.pop()
        return [
            '    ;; Remove variables from the symbols table',
            '    mov     rcx, [symbols]',
           f'    sub     rcx, {to_remove}',
            '    mov     [symbols], rcx'

        ]
    elif start_token.operator is Operator.PROCEDURE:
        if start_token.value == 'main':
            return [
                '    mov     rdi, 0   ;; EXIT',  # Set exit code to 0
                '    mov     rax, SYS_EXIT',
                '    syscall'
            ]
        else:
            input_variables, return_variables = global_state.procedure_to_variables[start_token.value]
            all_variables = return_variables + ['__return_address'] + input_variables
            to_remove = len(all_variables)
            for variable in all_variables:
                global_state.symbols.pop()
            return [
                '    ;; Remove variables from the symbols table',
                '    mov     rcx, [symbols]',
               f'    sub     rcx, {to_remove * 8}',
                '    mov     [symbols], rcx',
                '    ;; Remove variables from the stack',
               f'    add     rsp, {8 * len(input_variables)}',
                '    ret',
            ]
    else:
        raise RuntimeError('Could not process end token')
def _WHILE(self):
    return [
        f'{self.label}:'
    ]
def _DO(self):
    return [
        '    mov     rcx, TRUE',
        '    pop     rax',
        '    cmp     rax, TRUE',
       f'    jne     {self.end_token.label}'
    ]
def _STACK_REFERENCE(self):
    return [
        '    push    rsp',
    ]

#            [symbols]
# STACK [var1, var2, addr]
# STACK [ret1, ret2, ret3, addr, var1, var2]


[]
def _PROCEDURE(self):
    input_variables, return_variables = global_state.procedure_to_variables[self.value]
    original_variables = input_variables + ['__return_address']
    input_variables = ['__return_address'] + input_variables
    all_variables = return_variables + input_variables
    global_state.symbols.extend(all_variables)
    inst = [f'{self.label}:', f'    ;; {global_state.symbols}']
    if self.value == 'main':
        inst.extend([
            '    ;; Setup the symbols table',
            '    mov     rcx, symbols',
            '    add     rcx, 8',
            '    mov     [symbols], rcx'
        ])
    if self.value != 'main':
        inst.extend(['    ;; Shift everything to make space for the address and return variables'])
        inst.extend([
           f'    ;; {self.value}',
        ])
        shift_amount = (len(return_variables) + 1) * 8
        shift_back_amount = len(input_variables) * 8 - shift_amount
        if len(input_variables) > 1:
            for i, variable in enumerate(original_variables[::-1]):
                inst.extend([
                    f'    mov     rcx, [rsp {i * 8:+}]',
                    f'    mov     [rsp {i * 8 - shift_amount:+}], rcx  ;; Move {variable} ahead',
                ])
            inst.extend([
                   f'    mov     rcx, [rsp {-shift_amount:+}]',
                   f'    mov     [rsp {shift_back_amount:+}], rcx  ;; Move return address back'
            ])
        else:
            inst.extend([
                '    mov     rcx, [rsp]  ;; Take the return address',  # Take the return address
               f'    mov     [rsp {-len(return_variables) * 8:+}], rcx  ;; Move it forward making space for the return variables'
            ])
        inst.extend([
               f'    sub     rsp, {shift_amount - 8}  ;; Resize the stack accordingly',
        ])



        for i, item in enumerate(all_variables):
            length = len(all_variables) - 1
            stack_location = (length - i) * 8
            inst.extend([
               f'    ;; Bind {item} {stack_location}',
                '    mov     rax, rsp',
               f'    add     rax, {stack_location}',  # rax has the address of the variable
                '    mov     rcx, [symbols]',         # rcx points to the last free slot
                '    mov     [rcx], rax',
                # TODO Do this once after the whole for loop is finished
                '    add     rcx, 8',                 # update symbols so it points
                '    mov     [symbols], rcx'          # to a free slot
            ])
        inst.extend([
           f'    ;; {self.value}'
        ])
    return inst
def _PROCEDURE_CALL(self):
    return [
       f'    ;; {global_state.symbols}',
        '    xor     rax, rax',
       f'    call    {self.value}',
    ]
def _SYSCALL(self):
    assert 0 <= self.value <= 5
    syscall_args = ['rdi', 'rsi', 'rdx', 'r10', 'r8', 'r9']
    arguments = syscall_args[:self.value]
    start = [
        '',
        '    pop     rax',
    ]
    middle = [f'    pop     {arg}' for arg in arguments]
    end = [
        '    syscall',
        '    push    rax'
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
        f'    push    {self.length}',
        f'    push    {self.label}'
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
    value = value[1:-1]
    value, length = string_to_db(value)
    token = Token(Operator.PUSH_STRING,
                  value=value,
                  length=length,
                  label=f'string_literal{global_state.string_literals}',
                  implementation=implementation)
    global_state.string_literals += 1
    return token


def create_token_PUSH_CHAR(operator, value, code_iterator, implementation):
    value = bytes(value, 'ascii').decode('unicode_escape')
    assert len(value) == 3, 'Expected item enclosed by single quotes to be a single character.'
    value = ord(value[1])
    token = Token(operator, value=value, implementation=implementation)
    return token


def create_token_PUSH_UINT(operator, value, code_iterator, implementation):
    value = int(value)
    token = Token(operator, value=value, implementation=implementation)
    return token


def create_token_MUTATE(operator, value, code_iterator, implementation):
    value = value[1:]
    token = Token(operator, value=value, implementation=implementation)
    return token


def create_token_PROCEDURE(operator, value, code_iterator, implementation):
    name = next(code_iterator)
    if name in global_state.procedures:
        raise RuntimeError(f'The procedure {name} was previously defined')
    global_state.procedures.append(name)

    variables = []
    return_variables = []
    for variable in code_iterator:
        # TODO Check if we find a keyword and report an appropriate error.
        if variable == '--':
            break
        variables.append(variable)
    for variable in code_iterator:
        # TODO Check if we find a keyword and report an appropriate error.
        if variable == 'in':
            break
        return_variables.append(variable)

    global_state.procedure_to_variables[name] = variables, return_variables
    token = Token(Operator.PROCEDURE, value=name, implementation=implementation)

    return token


def create_token_PROCEDURE_CALL(operator, value, code_iterator, implementation):
    procedure_name = value
    value = f'{PROCEDURE_PREFIX}{value}'
    token = Token(operator, value=value, implementation=implementation)
    token.name = procedure_name
    return token


def create_token_IMPORT(operator, value, code_iterator, implementation):
    filename = next(code_iterator)
    global_state.imports[filename] = list()
    token = Token(Operator.MACRO, value=filename)
    return token


def create_token_MACRO(operator, value, code_iterator, implementation):
    value = next(code_iterator)
    global_state.macros[value] = list()
    token = Token(Operator.MACRO, value=value)
    return token


def create_token_MACRO_EXPANSION(operator, value, code_iterator, implementation):
    assert value in global_state.macros, f'Unrecognized macro {value}'
    token = Token(Operator.MACRO_EXPANSION, value=value)
    return token


def create_token_SYSCALL(operator, value, code_iterator, implementation):
    value = int(value[-1])
    token = Token(Operator.SYSCALL, value=value, implementation=implementation)
    return token


def create_token_WHERE(operator, value, code_iterator, implementation):
    variables = []
    for variable in code_iterator:
        if variable == 'in':
            break
        variables.append(variable)

    return Token(operator, value=variables, implementation=implementation)

def operator_to_token(operator, value, code_iterator, implementation):
    this_module = sys.modules[__name__]
    create_token = getattr(this_module, 'create_token_' + operator.name, create_token_basic)
    return create_token(operator, value, code_iterator, implementation)

