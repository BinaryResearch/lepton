# Lepton
Lepton is a Lightweight ELF Parsing Tool that can robustly read corrupted or damaged ELF headers. 
This is useful for analyzing extremely minimalist ELF files, crackmes or malware with deliberately mangled ELF headers.
Through this tool, one has access to every field in the ELF header as well as every field in every entry of the
program load table. Individual fields can be straightforwardly accessed and modified. Example scripts and test
binaries are included in the repository. 

# Usage

```python3

from Lepton import *

with open([ an ELF binary ], 'rb') as f:
    elf_file = ELFFile(f)

elf_file.ELF_header.print_fields()

for header in elf_file.program_header_table.entries:
    for field, value in header.items():
        print(field + ":  \t" + str(value))
```

More complete examples can be found in the programs in the `scripts` folder.

# Test Binaries

The test binaries included in this repo are from Muppetlabs' "tiny" series, as well as netspooky's "golfclub" programs:

 - https://www.muppetlabs.com/~breadbox/software/tiny/return42.html
 - https://www.muppetlabs.com/~breadbox/software/tiny/useless.html
 - https://www.muppetlabs.com/~breadbox/software/tiny/useful.html

 - https://github.com/netspooky/golfclub



### TODO
 - The binary recomposition feature is experimental. It appears to work for the very simple, very small binaries,
but modifies the behavior or corrupts the logic of larger or more complex programs. Further investigation is
required.

 - The ELFExceptions module needs work as it is very basic.

 - The Lepton classes and functions need to be documented
