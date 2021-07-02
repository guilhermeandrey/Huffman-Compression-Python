from Huffman import HuffmanCode

# Example of implementarion of Huffman Compression

# path to file to compress
file = f'./Example Files/example1.txt'
# path to store compressed file
compression_output_path = './Compressed'
# path to store decompressed file
decompression_output_path = './Decompressed'

# Create instance
huff = HuffmanCode()
# Compress file
compressed_file = huff.Compress(file = file, output_path = compression_output_path, evaluate_time = True)
# Decompress file
decompressed_file = huff.Decompress(compressed_file = compressed_file, output_path = decompression_output_path, 
                                    extension = '.txt', evaluate_time = True)



