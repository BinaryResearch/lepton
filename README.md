# Overview
Lepton is a Lightweight ELF Parsing Tool that can robustly read corrupted or damaged ELF headers. 
It was designed in order to analyze extremely minimalist ELF files, crackmes or malware with deliberately mangled ELF headers.
Development was prompted by the failure of other tools to accurately parse some of the minimalist ELF binaries in
Muppetlabs' "tiny" ELF file series. Since the design goal was specifically to be able to successfully and accurately parse the
ELF header of *any* ELF binary that can be loaded and executed by the Linux kernel, it is not a fully-featured parser like `readelf` or
`pyelftools`; there is no support for section or symbol information.

When using Lepton to parse ELF binaries, one has access to every field in the ELF header as well as every field in every entry of the
program load table. Individual fields can be straightforwardly modified. Example scripts and test
binaries are included in the repository.

# Usage

Example use cases:

### Editing Corrupted ELF Header Fields

One anti-analysis trick involving corrupting the ELF header is writing incorrect values to fields having to do with section information.
Some tools will subsequently fail to parse or load the binary. A concrete example of this is a "keygenme" crackme from 
[crackmes.one](https://crackmes.one/crackme/5d7c66d833c5d46f00e2c45b) that Ghidra (9.1-BETA_DEV_20190923) fails to load.

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

These values can be overwritten such that Ghidra successfully loads the binary.

```python
#!/usr/bin/python3

from Lepton import *
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

![Ghidra loads the binary after the ELF header is repaired](https://imgur.com/hKFWf96.png)


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
