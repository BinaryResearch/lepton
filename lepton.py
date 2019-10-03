from ELFExceptions import *
from ELFStructures import *
from struct import pack, unpack
from copy import deepcopy


# if new_header is == True, build a header with standard/appropriate values in the corresponding
# fields. If new_header == False, simply read the raw header values into the ELF header dictionary
# TODO: the recompose_binary function may need to be updated to reflect the introduction of this option
class ELFFile:
    def __init__(self, file_handle, new_header = False):
        self.new_header = new_header

        try:
            self.file_buffer = file_handle.read()
        except PermissionError as e:
            print("Permission error: {0}".format(e))
            exit()
        try:
            self.ELF_header = self.ELFHeader(self.file_buffer, new_header)
        except ELFHeaderError as e:
            print("ELF header error: {0}".format(e))
            exit()
        try:
            self.program_header_table = self.ProgramHeaderTable(self.file_buffer, self.ELF_header.fields)
        except ProgramHeaderTableError as e:
            print("Program header table error: {0}".format(e))
            exit()

    # EXPERIMENTAL
    #
    # Check if program header table overlaps ELF header
    # If so, copy bytes in range [OEP : EOF] in the original file into a buffer
    # This buffer will be appended to the end of the program header table
    # Then recalculate the entry point to be at the new file offest
    # (Entry point = LOAD vaddr + file offset of entry point instruction)
    #TODO: this often results in a binary that malfunctions - segfaults, incorrect output, etc. Investigate.
    def recompose_binary(self):
        if self.new_header == False:
            print("first set the 'new_header' argument to ELFFile equal to True. Exiting.")
            exit()
        #
        program_header_table_bytes = self.program_header_table.to_bytes()
        ELF_header_bytes = self.ELF_header.to_bytes()
        entry_point_file_offset = 0

        if len(self.ELF_header.fields["e_entry"]) == 8:
            format = '<Q'
            if unpack(format, self.file_buffer[32:40])[0] < 64: # e_phoff < e_ehsize
                entry_point_file_offset = unpack(format, self.file_buffer[24:32])[0] - unpack(format, self.program_header_table.entries[0]["p_vaddr"])[0]
            else:
                return self.ELF_header.to_bytes() + program_header_table_bytes + self.file_buffer[len(ELF_header_bytes) + len(program_header_table_bytes) : ]
        else:
            format = '<I'
            if unpack(format, self.file_buffer[28:32])[0] < 52: # e_phoff < e_ehsize
                entry_point_file_offset = unpack(format, self.file_buffer[24:28])[0] - unpack(format, self.program_header_table.entries[0]["p_vaddr"])[0]
            else:
                return ELF_header_bytes + program_header_table_bytes + self.file_buffer[len(ELF_header_bytes) + len(program_header_table_bytes) : ]

        # rebuild
        segment = self.file_buffer[entry_point_file_offset:]
        new_entry_point_offset = unpack('<H', self.ELF_header.fields["e_ehsize"])[0] + len(program_header_table_bytes)
        new_entry_point = new_entry_point_offset + unpack(format, self.program_header_table.entries[0]["p_vaddr"])[0]
        self.ELF_header.fields["e_entry"] = pack(format, new_entry_point)
        binary = self.ELF_header.to_bytes() + program_header_table_bytes + segment

        return binary



    class ELFHeader:
        def __init__(self, file_buffer, new_header):

            # check file format
            def check_magic(file_buffer):
                if file_buffer[0:4] != b'\x7fELF':
                    raise ELFMagicError("ELFMagicError: wrong magic values: ", hex(unpack('<I', file_buffer[0:4])[0]))

            # select appropriate ELF header structure based on
            # the CPU rather than the EI_CLASS byte
            def get_target_arch(file_buffer):
                try:
                    check_magic(file_buffer)
                except ELFMagicError as e:
                    print("{0}".format(e))
                    exit()
                try:
                    self.arch = architectures[file_buffer[18:20]] #
                except KeyError as e:
                    print("Unsupported architecture: " + hex(unpack('<H', file_buffer[18:20])[0]))
                    raise ELFHeaderError("Error in ELF header")

                return self.arch

            # read file buffer contents into appropriate fields
            def build_ELF32_hdr(file_buffer):
                hdr = deepcopy(ELF32_header)
                hdr["e_type"] = file_buffer[16:18]
                hdr["e_machine"] = file_buffer[18:20]
                hdr["e_entry"] = file_buffer[24:28]
                hdr["e_phnum"] = file_buffer[44].to_bytes(2, byteorder="little")
                return hdr

            def build_ELF64_hdr(file_buffer):
                hdr = deepcopy(ELF64_header)
                hdr["e_type"] = file_buffer[16:18]
                hdr["e_machine"] = file_buffer[18:20]
                hdr["e_entry"] = file_buffer[24:32]
                hdr["e_phnum"] = file_buffer[56].to_bytes(2, byteorder="little")
                return hdr

            # simply read bytes into dictionary
            def build_raw_header(file_buffer, arch):
                if arch[1] == 1:
                    header = build_ELF32_hdr(file_buffer)
                    header["e_ident"] = file_buffer[:16]
                    header["e_version"] = file_buffer[20:24]
                    header["e_phoff"] = file_buffer[28:32]
                    header["e_shoff"] = file_buffer[32:36]
                    header["e_flags"] = file_buffer[36:40]
                    header["e_ehsize"] = file_buffer[40:42]
                    header["e_phentsize"] = file_buffer[42:44]
                    header["e_shentsize"] = file_buffer[46:48]
                    header["e_shnum"] = file_buffer[48:50]
                    header["e_shstrndx"] = file_buffer[50:52]
                else:
                    header = build_ELF64_hdr(file_buffer)
                    header["e_ident"] = file_buffer[:16]
                    header["e_version"] = file_buffer[20:24]
                    header["e_phoff"] = file_buffer[32:40]
                    header["e_shoff"] = file_buffer[40:48]
                    header["e_flags"] = file_buffer[48:52]
                    header["e_ehsize"] = file_buffer[52:54]
                    header["e_phentsize"] = file_buffer[54:56]
                    header["e_shentsize"] = file_buffer[58:60]
                    header["e_shnum"] = file_buffer[60:62]
                    header["e_shstrndx"] = file_buffer[62:64]

                return header

            # read the bytes in the file buffer in order to
            # populate the empty ELF header dictionary with the
            # appropriate values
            def build_new_header(file_buffer, arch):
                padding = b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                if arch[2] == 1:
                    EI_DATA = b'\x01'
                else:
                    EI_DATA = b'\x02'

                # these values are being manually inserted into the following fields in order
                # to create a header that can be successfully parsed by readelf or other tools.
                #  As such, these values may not reflect the true values found in the original ELF header
                if arch[1] == 1: # 32 bit
                    header = build_ELF32_hdr(file_buffer)
                    header["e_ident"] = b'\x7fELF\x01' + EI_DATA + padding
                    header["e_phoff"] = pack('<I', 52)
                    header["e_ehsize"] = pack('<h', 52)
                    header["e_phentsize"] = pack('<h', 32)
                else:
                    header = build_ELF64_hdr(file_buffer)
                    header["e_ident"] = b'\x7fELF\x02' + EI_DATA + padding
                    header["e_phoff"] = pack('<Q', 64)
                    header["e_ehsize"] = pack('<h', 64)
                    header["e_phentsize"] = pack('<h', 56)

                header["e_version"] = pack('<I', 1)

                return header

            #arch = get_target_arch(file_buffer)
            if new_header == True:
                self.fields = build_new_header(file_buffer, get_target_arch(file_buffer))
            else:
                self.fields = build_raw_header(file_buffer, get_target_arch(file_buffer))


        # concatenate all fields
        def to_bytes(self):
            header_bytes = self.fields["e_ident"] + \
                           self.fields["e_type"] + \
                           self.fields["e_machine"] + \
                           self.fields["e_version"] + \
                           self.fields["e_entry"] + \
                           self.fields["e_phoff"] + \
                           self.fields["e_shoff"] + \
                           self.fields["e_flags"] + \
                           self.fields["e_ehsize"] + \
                           self.fields["e_phentsize"] + \
                           self.fields["e_phnum"] + \
                           self.fields["e_shentsize"] + \
                           self.fields["e_shnum"] + \
                           self.fields["e_shstrndx"]
            return header_bytes

        def print_fields(self):
            if len(self.fields["e_entry"]) == 8:
                try:
                    print("\tE_IDENT: " + str(unpack("<BBBBBBBBBBBBBBBB", self.fields["e_ident"])))
                    print("\tType: 0x%x" % unpack('<h', self.fields["e_type"])[0])
                    print("\tMachine: 0x%x" % unpack('<h', self.fields["e_machine"])[0])
                    print("\tVersion: 0x%x" % unpack('<I', self.fields["e_version"])[0])
                    print("\tEntry point: 0x%x" % unpack('<Q', self.fields["e_entry"])[0])
                    print("\tProgram header table offset (bytes into file): 0x%x" % unpack('<Q', self.fields["e_phoff"])[0])
                    print("\tSection header table offset (bytes into file): 0x%x" % unpack('<Q', self.fields["e_shoff"])[0])
                    print("\tFlags: 0x%x" % unpack('<I', self.fields["e_flags"])[0])
                    print("\tELF header size (bytes): %d" % unpack('<h', self.fields["e_ehsize"])[0])
                    print("\tProgram header table entry size: %d" % unpack('<h', self.fields["e_phentsize"])[0])
                    print("\tNumber of entries in the program header table: %d" % unpack('<h', self.fields["e_phnum"])[0])
                    print("\tSection header table entry size: %d" % unpack('<h', self.fields["e_shentsize"])[0])
                    print("\tNumber of entries in the section header table: %d" % unpack('<h', self.fields["e_shnum"])[0])
                    print("\tNumber of entries in the string header index table: %d" % unpack('<h', self.fields["e_shstrndx"])[0])
                except:
                    print("\t[+] Null field encountered. File is smaller than expected header size [+]")
                    pass
            else:
                try:
                    print("\tE_IDENT: " + str(unpack("<BBBBBBBBBBBBBBBB", self.fields["e_ident"])))
                    print("\tType: 0x%x" % unpack('<h', self.fields["e_type"])[0])
                    print("\tMachine: 0x%x" % unpack('<h', self.fields["e_machine"])[0])
                    print("\tVersion: 0x%x" % unpack('<I', self.fields["e_version"])[0])
                    print("\tEntry point: 0x%x" % unpack('<I', self.fields["e_entry"])[0])
                    print("\tProgram header table offset (bytes into file): 0x%x" % unpack('<I', self.fields["e_phoff"])[0])
                    print("\tSection header table offset (bytes into file): 0x%x" % unpack('<I', self.fields["e_shoff"])[0])
                    print("\tFlags: 0x%x" % unpack('<I', self.fields["e_flags"])[0])
                    print("\tELF header size (bytes): %d" % unpack('<h', self.fields["e_ehsize"])[0])
                    print("\tProgram header table entry size: %d" % unpack('<h', self.fields["e_phentsize"])[0])
                    print("\tNumber of entries in the program header table: %d" % unpack('<h', self.fields["e_phnum"])[0])
                    print("\tSection header table entry size: %d" % unpack('<h', self.fields["e_shentsize"])[0])
                    print("\tNumber of entries in the section header table: %d" % unpack('<h', self.fields["e_shnum"])[0])
                    print("\tNumber of entries in the string header index table: %d" % unpack('<h', self.fields["e_shstrndx"])[0])
                except:
                    print("\t[+] Null field encountered. File is smaller than expected header size [+]")
                    pass

    class ProgramHeaderTable:
        def __init__(self, file_buffer, ELF_header_fields):

            #
            def build_ELF32_phdr(file_buffer, ELF_header_fields, phdr_num):
                # calculate offset of p_hdr
                # offset is e_phoff + e_phentsize * program header number
                # first program header number is 0, then 1, then 2 ...
                table_offset = unpack('<I', file_buffer[28:32])[0]
                phdr_size = 32

                if phdr_num == 0:
                    phdr_offset = table_offset
                else:
                    phdr_offset = table_offset + phdr_size * phdr_num  #

                # read data in file buffer at this offset to create program header
                phdr = deepcopy(ELF32_program_header)  # 32-bit is easy, all fields are 4 bytes
                phdr["p_type"] = file_buffer[phdr_offset : phdr_offset + 4]
                phdr["p_offset"] = file_buffer[phdr_offset + 4 : phdr_offset + 8]
                phdr["p_vaddr"] = file_buffer[phdr_offset + 8 : phdr_offset + 12]
                phdr["p_paddr"] = file_buffer[phdr_offset + 12: phdr_offset + 16]
                phdr["p_filesz"] = file_buffer[phdr_offset + 16 : phdr_offset + 20]
                phdr["p_memsz"] = file_buffer[phdr_offset + 20 : phdr_offset + 24]
                phdr["p_flags"] = file_buffer[phdr_offset + 24 : phdr_offset + 28]
                phdr["p_align"] = file_buffer[phdr_offset + 28 : phdr_offset + 32]

                return phdr

            #
            def build_ELF64_phdr(file_buffer, ELF_header_fields, phdr_num):
                # calculate offset of p_hdr
                # offset is e_phoff + e_phentsize * program header number
                # first program header number is 0, then 1, then 2 ...
                table_offset = unpack('Q', file_buffer[32:40])[0]
                phdr_size = 56

                if phdr_num == 0:
                    phdr_offset = table_offset
                else:
                    phdr_offset = table_offset + phdr_size * phdr_num

                # read data in file buffer at this offset to create program header
                phdr = deepcopy(ELF64_program_header)
                phdr["p_type"] = file_buffer[phdr_offset : phdr_offset + 4]         # 4
                phdr["p_flags"] = file_buffer[phdr_offset + 4 : phdr_offset + 8]    # 4
                phdr["p_offset"] = file_buffer[phdr_offset + 8 : phdr_offset + 16]  # 8
                phdr["p_vaddr"] = file_buffer[phdr_offset + 16: phdr_offset + 24]   # 8
                phdr["p_paddr"] = file_buffer[phdr_offset + 24 : phdr_offset + 32]  # 8
                phdr["p_filesz"] = file_buffer[phdr_offset + 32 : phdr_offset + 40] # 8
                phdr["p_memsz"] = file_buffer[phdr_offset + 40 : phdr_offset + 48]  # 8
                phdr["p_align"] = file_buffer[phdr_offset + 48 : phdr_offset + 56]  # 8

                return phdr


            # read ELF header to construct program header table
            # loop over entries
            def build_program_header_table(file_buffer, ELF_header_fields):
                phdr_table = []
                phnum = unpack("<h", ELF_header_fields["e_phnum"])[0]
                arch = ELF_header_fields["e_ident"][4]

                for phdr_num in range(phnum):
                    if arch == 1:
                       program_header = build_ELF32_phdr(file_buffer, ELF_header_fields, phdr_num)
                    else:
                       program_header = build_ELF64_phdr(file_buffer, ELF_header_fields, phdr_num)

                    phdr_table.append(program_header)

                return phdr_table

            self.entries = build_program_header_table(file_buffer, ELF_header_fields)


        def to_bytes(self):
            phdr_table_bytes = bytes()
            if len(self.entries[0]["p_vaddr"]) == 8:
                for header in self.entries:
                    header_bytes = header["p_type"] + \
                                   header["p_flags"] + \
                                   header["p_offset"] + \
                                   header["p_vaddr"] + \
                                   header["p_paddr"] + \
                                   header["p_filesz"] + \
                                   header["p_memsz"] + \
                                   header["p_align"]
                    phdr_table_bytes += header_bytes
            else:
                for header in self.entries:
                    header_bytes = header["p_type"] + \
                                   header["p_offset"] + \
                                   header["p_vaddr"] + \
                                   header["p_paddr"] + \
                                   header["p_filesz"] + \
                                   header["p_memsz"] + \
                                   header["p_flags"] + \
                                   header["p_align"]
                    phdr_table_bytes += header_bytes
            return phdr_table_bytes
