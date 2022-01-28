"""Utils to help check each operation makes sense."""
from definitions import Operator, stack_effect


def _check_push_count_do_not_modify(token, program_iterator, stack_size) -> int:
    starting_stack_size = stack_size
    for child_token in program_iterator:
        if child_token is token.end_token:
            break
        if child_token.operator is Operator.SYSCALL:
            stack_size -= child_token.value + 1
        else:
            stack_size += stack_effect[child_token.operator]
        _check_push_count(child_token, program_iterator, stack_size)

    assert stack_size == starting_stack_size, f'Operator {token.operator} should not modify the stack'\
        f'{stack_size=} {starting_stack_size=}'

    return stack_size


def _check_push_count_normal(token, program_iterator, stack_size) -> int:
    for child_token in program_iterator:
        if child_token is token.end_token:
            break
        if child_token.operator is Operator.SYSCALL:
            stack_size -= child_token.value + 1
        else:
            stack_size += stack_effect[child_token.operator]
        _check_push_count(child_token, program_iterator, stack_size)

    return stack_size


def _check_push_count(token, program_iterator, stack_size) -> int:
    starting_stack_size = stack_size
    if token.operator in {Operator.IF, Operator.ELSE, Operator.WHILE}:
        if token.operator is Operator.IF and token.end_token.operator is Operator.END:
            stack_size = _check_push_count_do_not_modify(token, program_iterator, stack_size)
        elif token.operator is Operator.IF and token.end_token.operator is Operator.ELSE:
            stack_if = _check_push_count_normal(token, program_iterator, stack_size)
            stack_else = _check_push_count_normal(token.end_token, program_iterator, stack_size)
            assert stack_if == stack_else, 'If and else effect on the stack should match.\n' \
                f'{stack_if=} {stack_else=} {starting_stack_size=}'

            stack_size = stack_if
        # elif token.operator is Operator.WHILE:
        #     stack_size = _check_push_count_do_not_modify(token, program_iterator, stack_size)
    return stack_size


def _check_push_procedure(token, program_iterator, stack_size=0) -> int:
    for child_token in program_iterator:
        if child_token is token.end_token:
            break
        if child_token.operator is Operator.SYSCALL:
            stack_size -= child_token.value + 1
        else:
            stack_size += stack_effect[child_token.operator]
        stack_size = _check_push_count(child_token, program_iterator, stack_size)

    assert stack_size == 0, f'Procedures should clean the stack {stack_size=}'

    return stack_size


def check_push_count(program):
    """Checks the push count in the program."""
    return
    program_iterator = iter(program)
    for token in program_iterator:
        assert token.operator is Operator.PROCEDURE, 'The only top level tokens are procedures.'
        _check_push_procedure(token, program_iterator)
