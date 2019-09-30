#!/usr/bin/python3

from Lepton import *
from struct import unpack
from sys import argv

def main():
    if len(argv) != 2:
        print("usage: print_program_load_table.py <FILE NAME>")
        exit()

    with open(argv[1], 'rb') as f:
        e = ELFFile(f)

    # get arch
    if unpack('<H', e.ELF_header.fields["e_machine"])[0] == 0x3:
        format = '<I'
    elif unpack('<H', e.ELF_header.fields["e_machine"])[0] == 0x3e:
        format = '<Q'

    if format == '<I': # all fields are 4 bytes
        for header in e.program_header_table.entries:
            for field_name, value in header.items():
                print(field_name + ":  \t" + hex(unpack(format, value)[0]))
            print("==============================")
    elif format == '<Q':
        for header in e.program_header_table.entries:
            for field_name, value in header.items():
                if field_name == 'p_type' or field_name == 'p_flags': # 4 bytes
                    print(field_name + ":  \t" + hex(unpack('<I', value)[0]))
                else:
                    print(field_name + ":  \t" + hex(unpack(format, value)[0])) # 8 bytes
            print("==============================")

if __name__=='__main__':
    main()
