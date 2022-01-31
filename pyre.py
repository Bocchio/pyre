#!/usr/bin/env python
"""Pyre compiler."""
import argparse
from pathlib import Path
import subprocess
from copy import copy
from definitions import Token, Operator, lexeme_matches, get_type_size, PROCEDURE_PREFIX
from definitions import get_load_instruction, get_store_instruction
from implementations import operator_to_token, get_implementation
from parsing_utils import pyre_split, remove_comments
from grammar_checking import check_push_count
from pprint import pprint
import global_state


MEM_CAPACITY = 1024 * 1024  # 1 MiB I hope that's enough
SYMBOLS_TABLE_SIZE = 512  # 64 symbols of 8 bytes each

# TODO make sure I don't redefine constants

# TODO tag macro expansions so we know where they start and end


def tokenize(program: str) -> list:
    """Convert the program into a stream of tokens."""
    program = remove_comments(program)
    tokens = []

    code_iterator = iter(pyre_split(program))
    for item in code_iterator:
        # TODO add support for floats

        value = item
        operator = lexeme_matches(item)

        # Here we handle tokens that are instructions to the lexer and not the
        # program
        if operator is Operator.IMPORT:
            # This is special we don't want a lexeme
            # We want to execute something right away
            # Now this is the funny part
            # We can edit the iterator, getting the operators this function
            filename = next(code_iterator)
            assert filename.startswith('"')
            assert filename.endswith('"')
            filename = filename[1:-1] + '.pyre'
            if filename not in global_state.imports:  # Nothing should be imported more than once
                with open(filename, 'r') as imported_library:
                    imported_code = imported_library.read()
                tokens.extend(tokenize(imported_code))
                global_state.imports.append(filename)
            continue
        elif operator is Operator.DEFINE:
            name = next(code_iterator)
            value = next(code_iterator)
            macro_code = f'macro {name} {value} end'
            tokens.extend(tokenize(macro_code))
            continue
        elif operator is Operator.AUTOINCREMENT:
            value = item[:-2]
            tokens.extend(tokenize(f'{value} 1 + !{value}'))
            continue
        elif operator is Operator.AUTODECREMENT:
            value = item[:-2]
            tokens.extend(tokenize(f'{value} 1 - !{value}'))
            continue
        elif operator is Operator.WRITE_TO:
            match = operator.value.fullmatch(item)

            address, type_annotation, value = match.groups()

            type_annotation = type_annotation if type_annotation is not None else '1'
            value = value if value != '' else 0
            value *= get_type_size(type_annotation)

            store_instruction = get_store_instruction(type_annotation)

            tokens.extend(tokenize(f'{address} {value} + {store_instruction}'))
            continue
        elif operator is Operator.DEREFERENCE:
            match = operator.value.fullmatch(item)

            address, type_annotation, value = match.groups()

            type_annotation = type_annotation if type_annotation is not None else '1'
            value = value if value != '' else 0
            value *= get_type_size(type_annotation)
            load_instruction = get_load_instruction(type_annotation)

            tokens.extend(tokenize(f'{address} {value} + {load_instruction}'))

            continue

        implementation = get_implementation(operator)
        token = operator_to_token(operator, value, code_iterator, implementation)
        assert Token is not None

        tokens.append(token)

    # Inject the address in each token
    # Now this is not needed anymore
    for i, token in enumerate(tokens):
        token.address = i

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
            # print(f'start token {token.operator.name}')
            stack.append(token)  # Needs an end
        elif token.operator is Operator.IF:
            # print(f'start token {token.operator.name}')
            stack.append(token)  # Needs an else or an end
        elif token.operator is Operator.ELSE:
            start_token = stack.pop()
            # print(f'end   token {start_token.operator.name}')
            # print()
            # print(f'start token {token.operator.name}')
            stack.append(token)  # Needs an end
        elif token.operator is Operator.WHILE:
            # print(f'start token {token.operator.name}')
            stack.append(token)  # Needs a do
        elif token.operator is Operator.DO:
            start_token = stack.pop()
            # print(f'end   token {start_token.operator.name}')
            # print()
            # print(f'start token {token.operator.name}')
            stack.append(token)  # Needs an end
        elif token.operator is Operator.WHERE:
            # print(f'start token {token.operator.name}')
            stack.append(token)  # Needs an end
        elif token.operator is Operator.END:
            start_token = stack.pop()
            # print(f'end   token {start_token.operator.name}')
            # print()
            assert start_token.operator in {Operator.IF,
                                            Operator.ELIF,
                                            Operator.ELSE,
                                            Operator.DO,
                                            Operator.PROCEDURE,
                                            Operator.MACRO,
                                            Operator.WHERE}
            if start_token.operator is Operator.MACRO:
                in_macro_end = True
        elif token.operator is Operator.MACRO:
            assert not in_macro, f'Cannot nest macros: {token.value} inside {current_macro}'
            current_macro = token.value
            in_macro = True

            # print(f'start token {token.operator.name}')
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

    variables = []

    for token in program:
        value = token.value

        if token.operator is Operator.RETRIEVE:
            assert token.value in variables, f'Unexpeted variable {token.value}'

        assert token.operator not in {Operator.MACRO, Operator.MACRO_EXPANSION}

        if token.operator is Operator.PROCEDURE:
            # TODO make sure the main procedure appears only once
            if value == 'main':  # Main is a special procedure
                token.label = '_start'
            else:
                token.label = f'{PROCEDURE_PREFIX}{value}'
            token.block = block
            block += 1

            input_variables, return_variable = global_state.procedure_to_variables[token.value]
            all_variables = input_variables + return_variable
            variables.extend(all_variables)
            stack.append(token)  # Needs an end
        elif token.operator is Operator.IF:
            stack.append(token)  # Needs a do
        elif token.operator is Operator.WHILE:
            token.label = f'while{block}'
            block += 1

            stack.append(token)  # Needs a do
        elif token.operator is Operator.ELIF:
            token.label = f'elif{block}'
            block += 1

            start_token = stack.pop()
            assert start_token.operator is Operator.DO

            token.start_token = start_token
            start_token.end_token = token

            stack.append(token)  # Needs a do
        elif token.operator is Operator.ELSE:
            token.label = f'else{block}'
            block += 1

            start_token = stack.pop()
            assert start_token.operator is Operator.DO

            token.start_token = start_token
            start_token.end_token = token

            stack.append(token)  # Needs an end
        elif token.operator is Operator.DO:
            start_token = stack.pop()
            assert start_token.operator in {Operator.WHILE,
                                            Operator.IF,
                                            Operator.ELIF}

            start_token.end_token = token

            # We'll propagate this to the end
            token.start_token = start_token

            stack.append(token)  # Needs an end an elif or an else
        elif token.operator is Operator.WHERE:
            variables.extend(token.value)
            stack.append(token)  # Needs an end
        elif token.operator is Operator.END:
            # FIXME add the type of block it ends to the label
            token.label = f'end{block}'
            block += 1

            start_token = stack.pop()
            assert start_token.operator in {Operator.ELSE,
                                            Operator.DO,
                                            Operator.PROCEDURE,
                                            Operator.WHERE}

            # FIXME: This is really ugly.
            #        I think it's better to keep track of the block type inside
            #        the token itself
            if_block = start_token.operator is Operator.DO and start_token.start_token.operator in {Operator.IF, Operator.ELIF}
            if_block = if_block or start_token.operator is Operator.ELSE

            if start_token.operator is Operator.WHERE:
                for variable in start_token.value:
                    variables.pop()
            elif start_token.operator is Operator.PROCEDURE:
                input_variables, return_variable = global_state.procedure_to_variables[start_token.value]
                all_variables = input_variables + return_variable
                for variable in all_variables:
                    variables.pop()
            elif if_block:
                # TODO: Make this prettier
                st = start_token
                while True:
                    assert st.operator in {Operator.IF,
                                           Operator.ELIF,
                                           Operator.DO,
                                           Operator.ELSE}
                    if st.operator in {Operator.ELIF, Operator.ELSE}:
                        st.end_token = token
                    if st.operator is Operator.IF:
                        break
                    st = st.start_token

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
        f'symbols:   resb {SYMBOLS_TABLE_SIZE}',

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

    def tag_instructions(instructions, name):
        lines = instructions.split('\n')
        tag_position = 29
        padding = max(0, tag_position - len(lines[0])) * ' '
        lines[0] += f'{padding} ;; {name}'

        return '\n'.join(lines)

    global_state.add_symbols = []
    for token in program:
        instructions = generate_instruction(token)
        instructions = tag_instructions(instructions, token.operator.name)
        assembly.append(instructions)

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

    # pprint([token.operator for token in program])

    # check_push_count(program)

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
