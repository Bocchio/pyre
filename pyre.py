#!/usr/bin/env python
"""Pyre compiler."""
import argparse
from enum import Enum, auto
from pathlib import Path
import subprocess
from dataclasses import dataclass
from typing import Any
from copy import copy


MEM_CAPACITY = 1024 * 1024  # 1 MiB I hope that's enough
PROCEDURE_PREFIX = 'procedure_'
procedures = set()
macros = {}
add_symbols = []


class Operator(Enum):
    """Every operator Pyre knows."""

    ADD = auto()
    SUB = auto()
    MUL = auto()
    PEEK = auto()
    DROP = auto()
    ROT2 = auto()
    DROT2 = auto()
    ROT3 = auto()
    DUP = auto()
    DUP2 = auto()
    DUP3 = auto()
    LOAD = auto()
    STORE = auto()
    MEMORY = auto()
    PRINT = auto()
    EQUAL = auto()
    NOT_EQUAL = auto()
    LESS_THAN = auto()
    GREATER_THAN = auto()
    LESS_OR_EQUAL_THAN = auto()
    GREATER_OR_EQUAL_THAN = auto()
    IF = auto()
    ELSE = auto()
    END = auto()
    WHILE = auto()
    DO = auto()
    PUTCHAR = auto()
    PROCEDURE = auto()
    PROCEDURE_CALL = auto()

    # Yeah... not exactly pretty
    PUSH_UINT = auto()
    PUSH_CHAR = auto()
    PUSH_STRING = auto()

    MACRO = auto()
    MACRO_EXPANSION = auto()

    def __repr__(self):
        return f'{self.__class__.__name__}.{self.name}'


# Guess it's unused now
class Literal(Enum):
    """Literal types."""

    STRING = auto()
    CHAR = auto()
    UINT = auto()


@dataclass
class Token:
    """A token in the program."""
    operator: Operator
    value: Any = None

    # Useful when dealing with strings
    length: int = None

    # Useful when dealing with block operations
    block: bool = None
    address: int = None
    label: str = None

    start_token = None
    end_token = None


def tokenize(program: str) -> list:
    """Convert the program into a stream of tokens."""
    tokens = []
    for line in program.split('\n'):
        tokens.extend(tokenize_line(line))

    # Inject the address in each token
    for i, token in enumerate(tokens):
        token.addr = i

    return tokens


def read_until_sentinel(iterator, sentinel: str) -> str:
    acc = ''
    for item in iterator:
        acc += item
        if item == sentinel:
            break
    return acc


def pyre_split(stream: str) -> list:
    # We add a space at the end to force the last item to be added
    stream = stream.strip() + ' '

    items = []
    acc = ''
    stream_iterator = iter(stream)
    for c in stream_iterator:
        if c == '#':
            break
        if c == '"' or c == "'":
            assert acc == ''
            acc = c + read_until_sentinel(stream_iterator, sentinel=c)
        elif c.isspace():
            if acc != '':
                items.append(acc)
                acc = ''
            continue
        else:
            acc += c
    return items


def _string_to_db(stream: str) -> list:
    db_values = []
    if stream == '':
        return db_values

    escaped_actual = (
        (r'\n', ord('\n')),
        (r'\t', ord('\t'))
    )
    for c, val in escaped_actual:
        if c in stream:
            a, b = stream.split(c, maxsplit=1)
            a = _string_to_db(a)
            b = _string_to_db(b)
            db_values.extend([*a, val, *b])
            return db_values

    return [stream]


def string_to_db(stream: str) -> str:
    vals = _string_to_db(stream)
    vals_quoted = []
    length = 0
    for val in vals:
        if isinstance(val, str):
            length += len(val)
            vals_quoted.append(f'"{val}"')
        else:
            length += 1
            vals_quoted.append(str(val))
    return ','.join(vals_quoted), length


string_literals = 0
def tokenize_line(line_of_code: str) -> list:
    """Convert a line of code into a stream of tokens."""
    global string_literals, procedures, macros
    tokens = []
    code_iterator = iter(pyre_split(line_of_code))
    for item in code_iterator:
        # TODO add support for floats
        if item.isnumeric():
            value = int(item)
            item = Operator.PUSH_UINT
        elif item.startswith("'") and item.endswith("'"):
            item = bytes(item, 'ascii').decode('unicode_escape')
            assert len(item) == 3, 'Expected item enclosed by single quotes to be a single character.'
            value = ord(item[1])
            item = Operator.PUSH_CHAR
        elif item.startswith('"') and item.endswith('"'):
            value = item[1:-1]
            item = Operator.PUSH_STRING
        elif item in procedures:
            value = f'{PROCEDURE_PREFIX}{item}'
            item = Operator.PROCEDURE_CALL
        elif item in macros:
            value = item
            item = Operator.MACRO_EXPANSION

        if item == '+':
            token = Token(Operator.ADD)
        elif item == '-':
            token = Token(Operator.SUB)
        elif item == '*':
            token = Token(Operator.MUL)
        elif item == 'peek':
            token = Token(Operator.PEEK)
        elif item == 'drop':
            token = Token(Operator.DROP)
        elif item == 'rot2' or item == 'swap':
            token = Token(Operator.ROT2)
        elif item == 'drot2':
            token = Token(Operator.DROT2)
        elif item == 'rot3':
            token = Token(Operator.ROT3)
        elif item == 'print':
            token = Token(Operator.PRINT)
        elif item == 'putchar':
            token = Token(Operator.PUTCHAR)
        elif item == '=':
            token = Token(Operator.EQUAL)
        elif item == '!=':
            token = Token(Operator.NOT_EQUAL)
        elif item == '<':
            token = Token(Operator.LESS_THAN)
        elif item == '>':
            token = Token(Operator.GREATER_THAN)
        elif item == '<=':
            token = Token(Operator.LESS_OR_EQUAL_THAN)
        elif item == '>=':
            token = Token(Operator.GREATER_OR_EQUAL_THAN)
        elif item == 'dup':
            token = Token(Operator.DUP)
        elif item == '2dup':
            token = Token(Operator.DUP2)
        elif item == '3dup':
            token = Token(Operator.DUP3)
        elif item == 'load':
            token = Token(Operator.LOAD)
        elif item == 'store':
            token = Token(Operator.STORE)
        elif item == 'memory':
            token = Token(Operator.MEMORY)
        elif item == 'if':
            token = Token(Operator.IF)
        elif item == 'else':
            token = Token(Operator.ELSE)
        elif item == 'while':
            token = Token(Operator.WHILE)
        elif item == 'do':
            token = Token(Operator.DO)
        elif item == 'procedure':
            name = next(code_iterator)
            procedures |= {name}
            token = Token(Operator.PROCEDURE, value=name)
        elif item == 'end':
            token = Token(Operator.END)
        elif item == Operator.PUSH_UINT:
            token = Token(Operator.PUSH_UINT, value=value)
        elif item == Operator.PUSH_CHAR:
            token = Token(Operator.PUSH_CHAR, value=value)
        elif item == Operator.PUSH_STRING:
            value, length = string_to_db(value)
            token = Token(Operator.PUSH_STRING,
                          value=value,
                          length=length,
                          label=f'string_literal{string_literals}')
            string_literals += 1
        elif item == Operator.PROCEDURE_CALL:
            token = Token(Operator.PROCEDURE_CALL, value=value)
        elif item == 'macro':
            name = next(code_iterator)
            macros[name] = []
            token = Token(Operator.MACRO, value=name)
        elif item == Operator.MACRO_EXPANSION:
            assert value in macros, f'Unrecognized macro {value}'
            token = Token(Operator.MACRO_EXPANSION, value=value)
        else:
            raise RuntimeError(f'Unrecognized token {item}')
        tokens.append(token)
    return tokens


def load_macros(program: list) -> list:
    """Load the macros in the program."""
    global macros
    resulting_program = []
    stack = []

    current_macro = None
    in_macro = False
    in_macro_end = False
    token_iterator = iter(program)  # Welp, sometimes you gotta do what you gotta do
    for token in token_iterator:
        if token.operator is Operator.PROCEDURE:
            stack.append(token)  # Needs an end
        elif token.operator is Operator.IF:
            stack.append(token)  # Needs an else or an end
        elif token.operator is Operator.ELSE:
            stack.pop()
            stack.append(token)  # Needs an end
        elif token.operator is Operator.DO:
            stack.append(token)  # Needs an end
        elif token.operator is Operator.END:
            start_token = stack.pop()
            assert start_token.operator in {Operator.IF,
                                            Operator.ELSE,
                                            Operator.DO,
                                            Operator.PROCEDURE,
                                            Operator.MACRO}
            if start_token.operator is Operator.MACRO:
                in_macro_end = True
        elif token.operator is Operator.MACRO:
            assert not in_macro, f'Cannot nest macros: {token.value} inside {current_macro}'
            current_macro = token.value
            in_macro = True

            stack.append(token)  # Needs an end

        if not in_macro:
            resulting_program.append(token)
        elif in_macro_end:
            current_macro = None
            in_macro = False
            in_macro_end = False
        elif token.operator is not Operator.MACRO:
            assert current_macro is not None
            macros[current_macro].append(token)

    return resulting_program


def expand_macros(program: list) -> list:
    """Expand the macros in the program."""
    global macros
    expanded_program = []

    for token in program:
        value = token.value

        if token.operator is Operator.MACRO_EXPANSION:
            expanded_macro = expand_macros(macros[value])
            expanded_program.extend([copy(token) for token in expanded_macro])
        elif token.operator is Operator.MACRO:
            raise RuntimeError('The program should not have any remaining macro definitions.')
        else:
            expanded_program.append(token)

    return expanded_program


def create_references(program: list) -> list:
    """Append information about sibling tokens in block tokens."""
    referenced_program = []
    stack = []
    block = 1

    for token in program:
        value = token.value

        if token.operator is Operator.PROCEDURE:
            # TODO make sure the main procedure appears only once
            if value == 'main':  # Main is a special procedure
                token.label = '_start'
            else:
                token.label = f'{PROCEDURE_PREFIX}{value}'
            token.block = block
            block += 1

            stack.append(token)  # Needs an end
        elif token.operator is Operator.IF:
            stack.append(token)  # Needs an else or an end
        elif token.operator is Operator.WHILE:
            token.label = f'while{block}'
            block += 1

            stack.append(token)  # Needs a do
        elif token.operator is Operator.ELSE:
            token.label = f'else{block}'
            block += 1

            start_token = stack.pop()
            assert start_token.operator is Operator.IF

            token.start_token = start_token
            start_token.end_token = token

            stack.append(token)  # Needs an end
        elif token.operator is Operator.DO:
            start_token = stack.pop()
            assert start_token.operator is Operator.WHILE

            # We'll propagate this to the end
            token.start_token = start_token

            stack.append(token)  # Needs an end
        elif token.operator is Operator.END:
            token.label = f'end{block}'
            block += 1

            start_token = stack.pop()
            assert start_token.operator in {Operator.IF,
                                            Operator.ELSE,
                                            Operator.DO,
                                            Operator.PROCEDURE}

            token.start_token = start_token
            start_token.end_token = token

        referenced_program.append(token)

    return referenced_program


def generate_instruction(token: Token):
    """Generate assembly for a single token"""
    global add_symbols
    value = token.value

    assembly = []

    # TODO: Convert to literal or something like that
    if token.operator is Operator.PUSH_UINT:
        assembly.append(
            f'    push    {value}'
        )
    elif token.operator is Operator.PUSH_CHAR:
        assembly.append(
            f'    push    {value}'
        )
    elif token.operator is Operator.PUSH_STRING:
        assembly.extend([
            f'    push    {token.label}',
            f'    push    {token.length}'
        ])
        if token not in add_symbols:
            add_symbols.append(token)
    elif token.operator is Operator.ADD:
        assembly.extend([
            '    pop     rax',
            '    pop     rbx',
            '    add     rax, rbx',
            '    push    rax'
        ])
    elif token.operator is Operator.SUB:
        assembly.extend([
            '    pop     rax',
            '    pop     rbx',
            '    sub     rbx, rax',
            '    push    rbx'
        ])
    elif token.operator is Operator.MUL:
        assembly.extend([
            '    pop     rax',
            '    pop     rbx',
            '    imul     rax, rbx',
            '    push    rax'
        ])
    elif token.operator is Operator.EQUAL:
        assembly.extend([
            '    mov     rcx, FALSE',
            '    mov     rdx, TRUE',
            '    pop     rax',
            '    pop     rbx',
            '    cmp     rax, rbx',
            '    cmove   rcx, rdx',
            '    push    rcx'
        ])
    elif token.operator is Operator.NOT_EQUAL:
        assembly.extend([
            '    mov     rcx, FALSE',
            '    mov     rdx, TRUE',
            '    pop     rax',
            '    pop     rbx',
            '    cmp     rax, rbx',
            '    cmovne  rcx, rdx',
            '    push    rcx'
        ])
    elif token.operator is Operator.LESS_THAN:
        assembly.extend([
            '    mov     rcx, FALSE',
            '    mov     rdx, TRUE',
            '    pop     rax',
            '    pop     rbx',
            '    cmp     rbx, rax',
            '    cmovl   rcx, rdx',
            '    push    rcx'
        ])
    elif token.operator is Operator.LESS_OR_EQUAL_THAN:
        assembly.extend([
            '    mov     rcx, FALSE',
            '    mov     rdx, TRUE',
            '    pop     rax',
            '    pop     rbx',
            '    cmp     rbx, rax',
            '    cmovle   rcx, rdx',
            '    push    rcx'
        ])
    elif token.operator is Operator.GREATER_THAN:
        assembly.extend([
            '    mov     rcx, FALSE',
            '    mov     rdx, TRUE',
            '    pop     rax',
            '    pop     rbx',
            '    cmp     rbx, rax',
            '    cmovg   rcx, rdx',
            '    push    rcx'
        ])
    elif token.operator is Operator.GREATER_OR_EQUAL_THAN:
        assembly.extend([
            '    mov     rcx, FALSE',
            '    mov     rdx, TRUE',
            '    pop     rax',
            '    pop     rbx',
            '    cmp     rbx, rax',
            '    cmovge   rcx, rdx',
            '    push    rcx'
        ])
    elif token.operator is Operator.PEEK:
        assembly.extend([
            '    ;; PEEK',
            '    mov     rdi, [rsp]',
            '    call    peek',
        ])
    elif token.operator is Operator.DROP:
        assembly.extend([
            '    pop     rdi'
        ])
    elif token.operator is Operator.ROT2:
        assembly.extend([
            '    pop     rax',
            '    pop     rbx',
            '    push    rax',
            '    push    rbx',
        ])
    elif token.operator is Operator.DROT2:
        assembly.extend([
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
        ])
    elif token.operator is Operator.ROT3:
        assembly.extend([
            '    pop     rax',
            '    pop     rbx',
            '    pop     rcx',
            '    push    rbx',
            '    push    rax',
            '    push    rcx',
        ])
    elif token.operator is Operator.PRINT:
        assembly.extend([
            '    ;; PRINT',
            '    pop     rdx',  # the length
            '    pop     rsi',  # the string
            '    mov     rdi, STD_OUT',
            '    mov     rax, SYS_WRITE',
            '    syscall',
        ])
    elif token.operator is Operator.PUTCHAR:
        assembly.extend([
            '    ;; PUTCHAR',
            '    lea     rsi, [rsp]',
            '    mov     rdi, STD_OUT',
            '    mov     rdx, 1',
            '    mov     rax, SYS_WRITE',
            '    syscall',
            '    pop     rbx',  # Get rid of the character
        ])
    elif token.operator is Operator.DUP:
        assembly.extend([
            '    pop     rax',
            '    push    rax',
            '    push    rax'
        ])
    elif token.operator is Operator.DUP2:
        assembly.extend([
            '    pop     rbx',
            '    pop     rax',
            '    push    rax',
            '    push    rbx',
            '    push    rax',
            '    push    rbx'
        ])
    elif token.operator is Operator.DUP3:
        assembly.extend([
            '    pop     rcx',
            '    pop     rbx',
            '    pop     rax',
            '    push    rax',
            '    push    rbx',
            '    push    rcx',
            '    push    rax',
            '    push    rbx',
            '    push    rcx',
        ])
    elif token.operator is Operator.MEMORY:
        assembly.extend([
            '    push    memory',
        ])
    elif token.operator is Operator.LOAD:
        assembly.extend([
            '    pop    rax',
            '    mov    rbx, 0',  # Clear rbx
            '    mov    bl, [rax]',  # Read one byte into rbx
            '    push   rbx',
        ])
    elif token.operator is Operator.STORE:
        assembly.extend([
            '    pop    rbx',
            '    pop    rax',
            '    mov    [rax], bl',  # Write one byte from rbx
        ])
    elif token.operator is Operator.IF:
        assembly.extend([
            '    ;; IF',
            '    pop     rax',
            '    cmp     rax, TRUE',
            f'    jne      {token.end_token.label}'
        ])
    elif token.operator is Operator.ELSE:
        assembly.extend([
            f'    jmp    {token.end_token.label}'
            '    ;; ELSE',
            f'{token.label}:'
        ])
    elif token.operator is Operator.WHILE:
        assembly.extend([
            f'{token.label}:'
        ])
    elif token.operator is Operator.DO:
        assembly.extend([
            '    ;; DO',
            '    mov    rcx, TRUE',
            '    pop    rax',
            '    cmp    rax, TRUE',
            f'    jne    {token.end_token.label}'
        ])
    elif token.operator is Operator.PROCEDURE_CALL:
        assembly.extend([
            f'   ;; CALL {token.value}',
            f'   call    {token.value}'
        ])
    elif token.operator is Operator.PROCEDURE:
        assembly.extend([
            f'{token.label}:',
            '    push    rdi'
        ])
    elif token.operator is Operator.END:
        start_token = token.start_token
        assert start_token is not None

        if start_token.operator is Operator.IF or start_token.operator is Operator.ELSE:
            assembly.extend([
                f'{token.label}:'
            ])
        elif start_token.operator is Operator.DO:
            while_token = start_token.start_token
            assert while_token is not None
            assembly.extend([
                f'    jmp    {while_token.label}',
                f'{token.label}:'
            ])
        elif start_token.operator is Operator.PROCEDURE:
            if start_token.value == 'main':
                assembly.extend([
                    '    ;; EXIT',
                    '    mov     rdi, 0',  # Set exit code to 0
                    '    mov     rax, SYS_EXIT',
                    '    syscall',
                ])
            else:
                assembly.extend([
                    '    ret',
                ])
        else:
            raise RuntimeError(f'Unrecognized start token {start_token}')
    else:
        raise RuntimeError(f'Unrecognized token {token}')
    return '\n'.join(assembly)


def generate_assembly(program: list):
    """Generate assembly for a Pyre program."""
    global add_symbols

    assembly = [
        r'%define SYS_EXIT 60',
        r'%define SYS_WRITE 1',
        r'%define STD_OUT 1',
        r'%define TRUE 1',
        r'%define FALSE 0',
        'global _start',

        'segment .bss',
        f'memory:   resb {MEM_CAPACITY}',

        'segment .text',

        # Print unsigned integer routine
        # It's not like I stole this piece of code from gcc -O3 or something like that
        '',
        'peek:',
        '    mov     r9, -3689348814741910323',
        '    sub     rsp, 40',
        '    mov     BYTE [rsp+31], 10',
        '    lea     rcx, [rsp+30]',
        '.L2:',
        '    mov     rax, rdi',
        '    lea     r8, [rsp+32]',
        '    mul     r9',
        '    mov     rax, rdi',
        '    sub     r8, rcx',
        '    shr     rdx, 3',
        '    lea     rsi, [rdx+rdx*4]',
        '    add     rsi, rsi',
        '    sub     rax, rsi',
        '    add     eax, 48',
        '    mov     BYTE [rcx], al',
        '    mov     rax, rdi',
        '    mov     rdi, rdx',
        '    mov     rdx, rcx',
        '    sub     rcx, 1',
        '    cmp     rax, 9',
        '    ja      .L2',
        '    lea     rax, [rsp+32]',
        '    mov     edi, 1',
        '    sub     rdx, rax',
        '    xor     eax, eax',
        '    lea     rsi, [rsp+32+rdx]',
        '    mov     rdx, r8',
        '    mov     rax, SYS_WRITE',
        '    syscall',
        '    add     rsp, 40',
        '    ret',
        '',
    ]
    add_symbols = []
    for token in program:
        assembly.append(generate_instruction(token))

    for token in add_symbols:
        assembly.extend([
            '',
            f'{token.label}:',
            f'    db    {token.value}',
        ])

    return "\n".join(assembly)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simple Pyre compiler.')
    parser.add_argument('source', nargs='+',
                        help='source files')
    # TODO make this mutually exclusive with sim
    parser.add_argument('-r',
                        '--run',
                        action='store_true',
                        dest='run',
                        default=False,
                        help='Run the program after compiling it.')

    args = parser.parse_args()

    main_file = args.source[0]
    with open(main_file, 'r') as f:
        program_text = f.read()
    tokens = tokenize(program_text)
    tokens = load_macros(tokens)
    tokens = expand_macros(tokens)
    program = create_references(tokens)

    # The real work
    assembly = generate_assembly(program)
    assembly_file = Path(main_file).with_suffix('.asm').as_posix()
    object_file = Path(main_file).with_suffix('.o').as_posix()
    executable = Path(main_file).with_suffix('').absolute().as_posix()

    with open(assembly_file, 'w') as f:
        f.write(assembly)

    res = subprocess.run(['nasm', '-felf64', assembly_file])
    if res.returncode:
        raise RuntimeError('Could not generate object file')

    res = subprocess.run(['ld', object_file, '-o', executable])
    if res.returncode:
        raise RuntimeError('Could not link the object file')

    if args.run:
        subprocess.run([executable])
