# Overview
Lepton is a Lightweight ELF Parsing Tool that was designed specifically for analyzing and editing binaries with damaged or corrupted
ELF headers, such as extremely minimalist ELF files in which the entry point and program header table lie within the ELF header,
or binaries that have had the ELF header deliberately mangled as an anti-analysis method, such as crackmes or malware.
Development was prompted by the failure of other tools to parse some of the ELF binaries in
[Muppetlabs' "tiny" ELF file series](http://www.muppetlabs.com/~breadbox/software/tiny/). 

When using Lepton to parse ELF binaries, one has access to every field in the ELF header as well as every field in every entry of the
program load table. Individual fields can be straightforwardly modified to repair corruption.

Lepton succeeds in cases where other parsers fail for two main reasons:

 1. When reading the ELF header and program header table, the fields are simply read without any assumptions about 
    their correctness and without additional analysis. The main exceptions are the magic bytes and the value of the `e_machine` field; if the file 
    being read is not an ELF file or the architecture is not supported, Lepton quits. The result is that that if the binary can be executed, it can also be
    parsed correctly by Lepton, regardless of the extent of the corruption in the ELF header.

 2. When reconstructing the ELF header, only the values in the fields read by the kernel when loading the binay into memory are considered correct;
    the values of the rest of the fields are derived from the fields required by the kernel or assigned standard values. For example, the endianness 
    and architecture of the data in the file is derived from the value in the `e_machine` field, which must be correct in order for the binary to be 
    loaded by the kernel.  

Example scripts and test binaries are included in the repository.

Currently, only x86 and x86-64 binaries are supported, but support for additional architectures can be added very easily by creating a new
entry in the `architectures` dictionary in ELFStructures.py.

# Usage

A detailed example can be found at [Analyzing ELF Binaries with Malformed Headers Part 3 - Automatically Solving a Corrupted Keygenme with angr](https://binaryresearch.github.io/2020/01/15/Analyzing-ELF-Binaries-with-Malformed-Headers-Part-3-Solving-A-Corrupted-Keygenme.html)

Example use cases:

### Editing Corrupted ELF Header Fields

One anti-analysis trick involving corrupting the ELF header is writing incorrect values to fields having to do with section information.
Some tools will subsequently fail to parse or load the binary. A concrete example of this is a ["keygenme" crackme from 
crackmes.one](https://crackmes.one/crackme/5d7c66d833c5d46f00e2c45b) that Ghidra (9.1-BETA_DEV_20190923) fails to load. The crackme file
is included with this repository, in the `test_binaries` folder.

![Ghidra fails to correctly parse ELF header](https://imgur.com/PLZkF2v.png)

Using `readelf` it can clearly be seen that the start of the section headers (`e_shoff`), size of the section headers (`e_shentsize`) 
and the section header string table index (`e_shstrndx`) all hold bogus values:

```shell
$ readelf -h keygenme_copy 
ELF Header:
  Magic:   7f 45 4c 46 02 01 01 00 00 00 00 00 00 00 00 00 
  Class:                             ELF64
  Data:                              2's complement, little endian
  Version:                           1 (current)
  OS/ABI:                            UNIX - System V
  ABI Version:                       0
  Type:                              DYN (Shared object file)
  Machine:                           Advanced Micro Devices X86-64
  Version:                           0x1
  Entry point address:               0x1320
  Start of program headers:          64 (bytes into file)
  Start of section headers:          65535 (bytes into file)              <--------------
  Flags:                             0x0
  Size of this header:               64 (bytes)
  Size of program headers:           56 (bytes)
  Number of program headers:         11
  Size of section headers:           64 (bytes)
  Number of section headers:         65535                                <--------------
  Section header string table index: 65535 <corrupt: out of range>        <--------------
readelf: Error: Reading 4194240 bytes extends past end of file for section headers
readelf: Error: Reading 14312 bytes extends past end of file for dynamic string table
```

These values can be overwritten such that Ghidra successfully imports the binary. In the script below,
all fields having to do with sections are zeroed out:

```python
#!/usr/bin/python3

from lepton import *
from struct import pack

def main():
    with open("keygenme", "rb") as f:
        elf_file = ELFFile(f)

    # overwrite fields values with 0x00 bytes
    elf_file.ELF_header.fields["e_shoff"] = pack("<Q", 0)
    elf_file.ELF_header.fields["e_shentsize"] = pack("<H", 0)
    elf_file.ELF_header.fields["e_shnum"] = pack("<H", 0)
    elf_file.ELF_header.fields["e_shstrndx"] = pack("<H", 0)

    # output to file
    binary = elf_file.ELF_header.to_bytes() + elf_file.file_buffer[64:]
    with open("fixed_crackme", "wb") as f:
        f.write(binary)


if __name__=="__main__":
    main()
```

Ghidra now successfully imports the binary and displays the new ELF header values as well:

![Ghidra loads the binary after the ELF header is repaired](https://imgur.com/hKFWf96.png)

<hr>

### Recomposing a Corrupted Binary 

Edit 5/6/2021: This fails in most cases because it breaks most, if not all, offsets and relocations in the code.

`readelf` completely fails to read `tiny-i386`, which is 45 bytes in size - smaller than the 52 bytes of a well-formed ELF32 header:

```shell
$ readelf -h tiny-i386 
readelf: Error: tiny-i386: Failed to read file header
```

Lepton can be used to read the ELF header, as well as create a new binary holding the same information as the original but that can be parsed by `readelf`:

```python3
#!/usr/bin/python3

#read_and_recompose_tiny-i386.py
from lepton import *

def main():
    # raw headers
    with open("tiny-i386", "rb") as f:
        elf_file = ELFFile(f)

    print("\n\tRaw header field values:\n")
    elf_file.ELF_header.print_fields()

    # create new headers
    with open("tiny-i386", "rb") as f:
        elf_file = ELFFile(f, new_header=True)  # create new, well-formed ELF header

    with open("repaired_tiny-i386", "wb") as f:
        f.write(elf_file.recompose_binary())    # moves the program header out of the file
                                                # header and recalculates the entry point
    print("\n\tRepaired header field values:\n")
    elf_file.ELF_header.print_fields()          # call once entry point has been recalculated


if __name__=="__main__":
    main()
```

When an `ELFFile` object is instantiated with the `new_header` argument set to `True`, a new ELF header and program header table are created
in which fields besides those having to do with sections are given standard values. Fields having to do with sections are filled in with `0x00` bytes.

The `recompose_binary()` function checks if the program header table and the ELF header table overlap. If so, the program header table is moved out of
the ELF header by copying all of the bytes between the original entry point and the end of the file into a buffer, appending this buffer to a correctly-formed
ELF header + program header table and then recalculating the entry point based on its new offset within the file.
(note that this function is exprerimental and as of right now often results in programs with corrupted logic that produce erroneous I/O or segfault, 
but in this case it works.)


```shell
$ python3 read_and_recompose_tiny-i386.py 

	Raw header field values:

	E_IDENT: (127, 69, 76, 70, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0)
	Type: 0x2
	Machine: 0x3
	Version: 0x10020
	Entry point: 0x10020
	Program header table offset (bytes into file): 0x4
	Section header table offset (bytes into file): 0xc0312ab3
	Flags: 0x80cd40
	ELF header size (bytes): 52
	Program header table entry size: 32
	Number of entries in the program header table: 1
	[+] Null field encountered. File is smaller than expected header size [+]

	Repaired header field values:

	E_IDENT: (127, 69, 76, 70, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0)
	Type: 0x2
	Machine: 0x3
	Version: 0x1
	Entry point: 0x10054
	Program header table offset (bytes into file): 0x34
	Section header table offset (bytes into file): 0x0
	Flags: 0x0
	ELF header size (bytes): 52
	Program header table entry size: 32
	Number of entries in the program header table: 1
	Section header table entry size: 0
	Number of entries in the section header table: 0
	Number of entries in the string header index table: 0
```

The newly created ELF file is called `repaired_tiny-i386`. `readelf` can now parse it without choking:

```shell
$ readelf -h repaired_tiny-i386 
ELF Header:
  Magic:   7f 45 4c 46 01 01 01 00 00 00 00 00 00 00 00 00 
  Class:                             ELF32
  Data:                              2's complement, little endian
  Version:                           1 (current)
  OS/ABI:                            UNIX - System V
  ABI Version:                       0
  Type:                              EXEC (Executable file)
  Machine:                           Intel 80386
  Version:                           0x1
  Entry point address:               0x10054
  Start of program headers:          52 (bytes into file)
  Start of section headers:          0 (bytes into file)
  Flags:                             0x0
  Size of this header:               52 (bytes)
  Size of program headers:           32 (bytes)
  Number of program headers:         1
  Size of section headers:           0 (bytes)
  Number of section headers:         0
  Section header string table index: 0

$ readelf -l repaired_tiny-i386 

Elf file type is EXEC (Executable file)
Entry point 0x10054
There is 1 program header, starting at offset 52

Program Headers:
  Type           Offset   VirtAddr   PhysAddr   FileSiz MemSiz  Flg Align
  LOAD           0x000000 0x00010000 0x00030002 0x10020 0x10020 R   0xc0312ab3
```

The runtime behavior of the new file is identical to the original:

```shell
$ strace ./repaired_tiny-i386 
execve("./repaired_tiny-i386", ["./repaired_tiny-i386"], 0x7ffd19a0f1b0 /* 52 vars */) = 0
strace: [ Process PID=5822 runs in 32 bit mode. ]
exit(42)                                = ?
+++ exited with 42 +++
```

More examples can be found in the programs in the `scripts` folder.


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
