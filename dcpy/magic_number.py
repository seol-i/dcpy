magic_numbers: dict[list[bytes], str] = {
    'mp4':  [[b'\x00\x00\x00\x18\x66\x74\x79\x70']],            # MPEG-4 Video File
    'jpg':  [[b'\xff\xd8\xff\xe0', b'\x4a\x46\x49\x46'],        # Graphics – JPEG/JFIF Format
            [b'\xff\xd8\xff\xe1', b'\x45\x78\x69\x66'],         # Graphics – JPEG/Exif Format – Digital Camera
            [b'\xff\xd8\xff\xe8', b'\x53\x50\x49\x46\x46\x00']],# Graphics – Still Picture Interchange File Format
    'gif':  [[b'\x47\x49\x46\x38\x37\x61'],                     # Graphics – Graphics Interchange Format
            [b'\x47\x49\x46\x38\x39\x61']],                     # Graphics – Graphics Interchange Format
    'png':  [[b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a']],            # Graphics – Portable Network Graphics File
    'webp': [[b'\x52\x49\x46\x46', b'\x57\x45\x42\x50']],       # Google WebP image file
    'mkv':  [[b'\x1a\x45\xdf\xa3']],                            # Matroska media container, including WebM
}


# magic = '52 49 46 46 ?? ?? ?? ?? 57 45 42 50'
# print(r'\x' + r'\x'.join(magic.split()).lower())