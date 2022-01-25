#!/usr/bin/env python
"""Pyre compiler."""
import argparse
from pathlib import Path
import subprocess
from copy import copy
from definitions import Token, Operator, Literal, Lexeme
from implementations import lexeme_to_operator, operator_to_token, get_implementation
from parsing_utils import pyre_split
import global_state


MEM_CAPACITY = 1024 * 1024  # 1 MiB I hope that's enough
PROCEDURE_PREFIX = 'procedure_'


def tokenize(program: str) -> list:
    """Convert the program into a stream of tokens."""
    tokens = []
    for line in program.split('\n'):
        tokens.extend(tokenize_line(line))

    # Inject the address in each token
    for i, token in enumerate(tokens):
        token.addr = i

    return tokens


def tokenize_line(line_of_code: str) -> list:
    """Convert a line of code into a stream of tokens."""
    tokens = []
    code_iterator = iter(pyre_split(line_of_code))
    for item in code_iterator:
        # TODO add support for floats

        value = None
        if item.isnumeric():
            value = int(item)
            lexeme = Literal.UINT
        elif item.startswith("'") and item.endswith("'"):
            item = bytes(item, 'ascii').decode('unicode_escape')
            assert len(item) == 3, 'Expected item enclosed by single quotes to be a single character.'
            value = ord(item[1])
            lexeme = Literal.CHAR
        elif item.startswith('"') and item.endswith('"'):
            value = item[1:-1]
            lexeme = Literal.STRING
        elif item in global_state.procedures:
            value = f'{PROCEDURE_PREFIX}{item}'
            lexeme = Lexeme.PROCEDURE_CALL
        elif item in global_state.macros:
            value = item
            lexeme = Lexeme.MACRO_EXPANSION
        else:
            lexeme = item

        try:
            operator = lexeme_to_operator(lexeme)
        except KeyError:
            raise RuntimeError(f'Unrecognized token {item}')

        implementation = get_implementation(operator)
        token = operator_to_token(operator, value, code_iterator, implementation)

        assert Token is not None

        tokens.append(token)
    return tokens


def load_macros(program: list) -> list:
    """Load the macros in the program."""
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
            global_state.macros[current_macro].append(token)

    return resulting_program


def expand_macros(program: list) -> list:
    """Expand the macros in the program."""
    expanded_program = []

    for token in program:
        value = token.value

        if token.operator is Operator.MACRO_EXPANSION:
            expanded_macro = expand_macros(global_state.macros[value])
            expanded_program.extend([copy(token).bind_methods() for token in expanded_macro])
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

        assert token.operator not in {Operator.MACRO, Operator.MACRO_EXPANSION}

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
    assembly = token.implementation()

    return '\n'.join(assembly)


def generate_assembly(program: list):
    """Generate assembly for a Pyre program."""
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
    global_state.add_symbols = []
    for token in program:
        assembly.append(generate_instruction(token))

    for token in global_state.add_symbols:
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
