#!/usr/bin/python3

from Lepton import *
from struct import unpack
from sys import argv

def main():
    if len(argv) != 2:
        print("usage: build_new_binary.py <FILE NAME>")
        exit()

    print("raw header:")
    with open(argv[1], 'rb') as f:
        e1 = ELFFile(f)
    try:
        e1.ELF_header.print_fields()
    except:
        print("Error unpacking ELF header fields")
        pass
    print()


    print("new header:")
    with open(argv[1], 'rb') as f:
        e2 = ELFFile(f, new_header = True)  # Only fields required for loading will be read from the binary
                                            # The rest will be set to 0 or have standard values filled in
    e2.ELF_header.print_fields()


if __name__=='__main__':
    main()
