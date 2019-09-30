#!/usr/bin/python3

from Lepton import *
from struct import unpack
from sys import argv

def main():
    if len(argv) != 2:
        print("usage: get_entry_point.py <FILE NAME>")
        exit()

    with open(argv[1], "rb") as f:
        e = ELFFile(f)

    # 32 bit or 64 bit?
    if e.ELF_header.fields["e_ident"][4] == 1:
        format = '<I'
    else:
        format = '<Q'

    raw_entry_point = e.ELF_header.fields["e_entry"]
    human_readable_entry_point = hex(unpack(format, e.ELF_header.fields["e_entry"])[0])

    print("Raw entry point: %s" % raw_entry_point)
    print("Human-readable entry point: %s" % human_readable_entry_point)


if __name__ == '__main__':
    main()
