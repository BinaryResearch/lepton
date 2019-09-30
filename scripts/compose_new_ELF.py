#!/usr/bin/python3

from Lepton import *
from struct import unpack
from sys import argv

def main():
    if len(argv) != 2:
        print("usage: print_program_load_table.py <FILE NAME>")
        exit()

    with open(argv[1], 'rb') as f:
        e = ELFFile(f, new_header=True)

    print("\nwrite the following to a new file:\n")
    print(e.recompose_binary())

    with open(argv[1], 'rb') as f:
        e = ELFFile(f)

    print()
    print(e.recompose_binary())


if __name__=='__main__':
    main()
