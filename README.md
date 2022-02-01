# PyRe

A stack based programming language

**Important:** This language is a work in progress

# TODO

- [ ] Check stack effects during compilation time.
- [ ] Implement a dependency chain between procedures.
- [ ] Do not include unused procedures in the generated code.
- [ ] Add an option to generate a graph showing the flow of the program.
- [ ] A way to handle dynamic memory.
- [ ] A proper type system.
- [ ] A way to bind variables inside a block and automatically removing them at the end of it.
- [ ] A proper way to interact with files.


# Basic example

There's an example emulating rule110
```shell
./pyre.py rule110.pyre && ./rule110
```

# Control flow

## if elif else

### Definition
```
if condition do

elif condition do

elif condition do

else

end
```

`if`, `elif` and `else` are similar to labels. The `do` operator is the most important here.
The `do` operator pops a value from the stack and either continues with the execution or jumps to an appropriate label.

Incidentally, that means the following code is equivalent to the one above:

```
condition if do

elif condition do

elif condition do

else

end
```

**Note:** Currently the do operator only acts on boolean values. The behaviour is undefined for any other type of value.


### Examples

```
if 3 5 + 8 = do
    "8 is equal to (3 + 5)\n" print
end
```

```
  if foo 1 = do
    "foo is equal to 1\n" print
elif foo 2 = do
    "foo is equal to 2\n" print
elif foo 3 = do
    "foo is equal to 3\n" print
end
```

```
  if foo 5 < do
    "foo is less than 5\n" print
elif foo 6 > do
    "foo is bigger than 6\n" print
elif foo 6 = do
    "foo is equal to 6\n" print
else
    "foo is 5\n" print
end
```


## While loops

### Definition
```
while condition do

end
```

### Examples

```
1 !foo                    # Assign 1 to foo
while foo 5 < do          # While foo is less than 5
    foo num2char putchar  # Convert foo to a character and print it
    foo++                 # Increment foo
end
'\n' putchar
```

A more involved example without any variable-binding:
```
1 5 while 2dup < do        #    a  b a  b <
    swap dup 48 + putchar  #    b  a a 48 + putchar
    1 +                    #    b  a 1  +
    swap                   # (a+1) b
end drop drop              # Drop <a> and <b> from the stack
'\n' putchar
```

## Procedures

```
procedure name [input variables] -- [output variables] in


end
```

The procedure can have as many input and output variables as possible.
The net effect on the stack of the procedure needs to be `output_variables - input_variables`

```
procedure next_fibonacci_pair a b -- c d in
    b     !c  # assign the value of b to c
    a b + !d  # assign the value of a + b to d
end
```

# Running tests

```shell
python tests/tests.py
```
