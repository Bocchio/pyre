# PyRe

A stack based programming language

**Important:** This language is a work in progress.

# Basic example

There's an example emulating rule110
```shell
./pyre.py rule110.pyre && ./rule110
```

# Control flow

## else-less if

### Definition
```
[boolean] if  # Pops boolean. If false jumps to end. 

end
```

### Examples

```
3 5 + 8 = if
    "8 is equal to (3 + 5)\n" print 
end
```

## If else



### Definition

```
[boolean] if  # Pops boolean. If false jumps to else.

# Implicitly jumps to end
else

end
```

### Examples

```
5 5 = if
    "The numbers are equal.\n" print
else
    "The numbers are different.\n" print 
end
```

## While loops

### Definition
```
while [boolean] do  # Pops boolean. If False, jumps to end

end  # Jumps back to while
```

### Examples

```
1 while dup 5 < do    # Counter starts at 1. While copy(counter) < 5, do
    dup 48 + putchar  # Print counter
    1 +               # Increment counter
end drop              # Drop the counter
'\n' putchar
# output
# 1234
```

Same thing keeping the 5 outside the loop.
```
1 5 while 2dup < do
    swap dup 48 + putchar  # Print counter
    1 +                    # Increment counter
    swap                   # Back to counter 5
end drop drop              # Drop the counter
'\n' putchar
# output
# 1234
```

# Running tests

```shell
python tests/tests.py
```
