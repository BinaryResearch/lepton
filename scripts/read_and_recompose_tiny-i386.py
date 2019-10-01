#!/usr/bin/python3

from lepton import *

def main():
    # raw headers
    with open("tiny-i386", "rb") as f:
        elf_file = ELFFile(f)

    print("\n\tRaw header field values:\n")
    elf_file.ELF_header.print_fields()

    # create new headers
    with open("tiny-i386", "rb") as f:
        elf_file = ELFFile(f, new_header=True)

    # recompose binary
    with open("repaired_tiny-i386", "wb") as f:
        f.write(elf_file.recompose_binary())    # this moves the program header out of the file
                                                # header and recalculates the entry point
    print("\n\tRepaired header field values:\n")
    elf_file.ELF_header.print_fields()          # call once entry point has been recalculated


if __name__=="__main__":
    main()
