"""Some utils to make parsing easier."""


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
    return ','.join(vals_quoted) + ', 0', length + 1


def read_until_sentinel(iterator, sentinel: str) -> str:
    acc = ''
    for item in iterator:
        acc += item
        if item == sentinel:
            break
    return acc


def remove_comments(stream: str) -> str:
    """
    Remove comments from a stream of code.

    Not the prettiest of solutions but it'll do
    """

    def remove_comment_from_line(line):
        return line.split('#', maxsplit=1)[0]

    uncommented_lines = map(remove_comment_from_line, stream.split('\n'))
    uncommented_code = '\n'.join(uncommented_lines)
    return uncommented_code


def pyre_split(stream: str) -> list:
    """Get a list of lexemes from a stream of code."""
    # We add a space at the end to force the last item to be added
    # Modern problems require modern solutions
    stream = stream.strip() + ' '

    items = []
    acc = ''
    stream_iterator = iter(stream)
    for c in stream_iterator:
        if c == '"' or c == "'":
            assert acc == ''
            acc = c + read_until_sentinel(stream_iterator, sentinel=c)
        elif c == '[':
            acc += c + read_until_sentinel(stream_iterator, sentinel=']')
        elif c.isspace():
            if acc != '':
                items.append(acc)
                acc = ''
            continue
        else:
            acc += c
    return items
