.global _start
.text
_start:
    mov   $1, %al     # RAX holds syscall 1 (write), I chose to use
                      # %al, which is the lower 8 bits of the %rax 
                      # register. From a binary standpoint, there
                      # is less space used to represent this than
                      # mov $1, %rax
    mov   %rax, %rdi  # RDI holds File Handle 1, STDOUT. This means 
                      # that we are writing to the screen. Again, 
                      # moving RAX to RDI is shorter than 
                      # using mov $1, %rdi
    mov   $msg, %rsi  # RSI holds the address of our string buffer. 
    mov   $11, %dl    # RDX holds the size our of string buffer. 
                      # Moving into %dl to save space.
    syscall           # Invoke a syscall with these arguments.
    mov   $60, %al    # Now we are invoking syscall 60. 
    xor   %rdi, %rdi  # Zero out RDI, which holds the return value.
    syscall           # Call the system again to exit.
msg:
    .ascii "[^0^] u!!\n"
