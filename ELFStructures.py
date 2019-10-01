ELF64_header = {"e_ident":    bytearray(16),        	# EI_MAG0 - EI_MAG3
                "e_type":     bytearray(2),		# <---------
                "e_machine":  bytearray(2),		# architecture
                "e_version":  bytearray(4),
                "e_entry":    bytearray(8),		# <----------
                "e_phoff":    bytearray(8),		# <----------
                "e_shoff":    bytearray(8),
                "e_flags":    bytearray(4),
                "e_ehsize":   bytearray(2),
                "e_phentsize":bytearray(2),
                "e_phnum":    bytearray(2),		# <----------
                "e_shentsize":bytearray(2),
                "e_shnum":    bytearray(2),
                "e_shstrndx": bytearray(2)}


ELF64_program_header = {"p_type":   bytearray(4),
                        "p_offset": bytearray(4),
                        "p_vaddr":  bytearray(8),
                        "p_paddr":  bytearray(8),
                        "p_filesz": bytearray(8),
                        "p_memsz":  bytearray(8),
                        "p_flags":  bytearray(8),
                        "p_align":  bytearray(8)}


ELF32_header = {"e_ident":    bytearray(16),            # EI_MAG0 - EI_MAG3
                "e_type":     bytearray(2),             # <---------
                "e_machine":  bytearray(2),             # architecture
                "e_version":  bytearray(4),
                "e_entry":    bytearray(4),             # <----------
                "e_phoff":    bytearray(4),             # <----------
                "e_shoff":    bytearray(4),
                "e_flags":    bytearray(4),
                "e_ehsize":   bytearray(2),
                "e_phentsize":bytearray(2),
                "e_phnum":    bytearray(2),             # <----------
                "e_shentsize":bytearray(2),
                "e_shnum":    bytearray(2),
                "e_shstrndx": bytearray(2)}

ELF32_program_header = {"p_type":   bytearray(4),
                        "p_offset": bytearray(4),
                        "p_vaddr":  bytearray(4),
                        "p_paddr":  bytearray(4),
                        "p_filesz": bytearray(4),
                        "p_memsz":  bytearray(4),
                        "p_flags":  bytearray(4),
                        "p_align":  bytearray(4)}


# [ e_machine byte string, EI_CLASS, EI_DATA ]
# architecture-specific information is tied to the CPU
architectures = { b'\x03\x00':['i386', 1, 1],
                  b'>\x00':['AMD64', 2, 1] }

