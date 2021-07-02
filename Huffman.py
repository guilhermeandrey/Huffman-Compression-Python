# -*- coding: utf-8 -*-
import os
import re
from bitstring import BitArray
import operator
from time import time


class HuffmanCode:
  # Huffman Code implementation for 256-symbols file
  def __init__(self):
    # Initialization
    self.pat = '(alpha\d+__)'   # Regex pattern for the special codes used during compression
    self.codesnames = [f'alpha{i}__' for i in range(256)]   # Codes names used during compression, from alpha0 to alpha255 

  @staticmethod
  def read_bytes(file):
    # Inputs:
    # file: file from which bytes are read

    # Outputs:
    # bitlist: list with every byte from the file in its binary form

    with open(file, 'rb') as f:
        bitlist = []
        while True:
          byte = f.read(1)
          if byte:
            bitlist.append(BitArray(byte).bin)
          else:
            break
        return bitlist

  @staticmethod
  def make_frequency_tuples(binary_list):
    # Inputs:
    # binary_list: list of bytes in its binary forms

    # Outputs:
    # freqs: list of tuples with the frequency count of every distinct byte

    counts = {}
    for x in binary_list:
      counts[x] = counts.get(x,0) + 1  # Count every symbol in the file
    freqs = [(v, k) for k,v in counts.items()]    # Create list of tuples of the form (count, symbol)
    total_elements = sum([i[0] for i in freqs])
    freqs = [(i[0]/total_elements, i[1]) for i in freqs]    # Normalize frequencies in percentage
    freqs.sort(key = operator.itemgetter(0), reverse = True)    # Sort the list from most common to least common symbol
    return freqs
  
  def update_dictionary(self, cd):
    # Inputs:
    # cd: current encoding dictionary

    # Outputs:
    # cd: the input dictionary with the codes already defined substituted by its values

    for i in cd:
      match = re.match(self.pat, cd[i])   # Check if current symbol possesses an 
                                            # special symbol in its code (eg 'alpha1': 'alpha2' + '0')
      if match:   # If so, check if the special symbol is already defined in the dictionary and make the substitution
        if match.group(1) in cd.keys():
          cd[i] = re.sub(self.pat, cd[match.group(1)], cd[i])
    return cd

  def create_encoder_dictionary(self, freqs):
    # Inputs:
    # freqs: frequency tuples of the form (count, symbol)

    # Outputs:
    # final_codes: encoding dictionary

    ptr = 0   # Pointe to run through the codesnames list
    codes = {}    # Dictionary to store the codes generated
    final_codes = {}    # Dictionary to store the final codes
    while len(freqs) > 2:   # While there are more than 3 symbols being encoded
      last = freqs[-2:]   # Take least common symbols to group together
      top = freqs[:-2]    # The remaining of the symbols to be kept on the table
      new_freq = last[0][0] + last[1][0]    # Group the frequencies of the least 2 common symbols into one
      codes[last[0][1]] = self.codesnames[ptr] + '0'  # Create special code and assign 
      codes[last[1][1]] = self.codesnames[ptr] + '1'  # code+0 and code+1 for the symbols
      freqs = top + [(new_freq, self.codesnames[ptr])]    # Substitute least common symbols with new symbol
      freqs.sort(key = operator.itemgetter(0), reverse = True)    # Sort frequencies from highest to lowest
      codes = self.update_dictionary(codes)   # Update codes dictionary with previously created symbols
      ptr += 1
    codes[freqs[0][1]] = '0'    # Assign values 0 and 1 to last 2 symbols
    codes[freqs[1][1]] = '1'
    codes = self.update_dictionary(codes)   # Last update to dictionary
    for i in codes:
        if not re.match(self.pat, i):
            final_codes[i] = codes[i]   # Form final encoder without the special codes used for the table
    return final_codes

 
  @staticmethod
  def make_header(bin_string, encoder_dict):
    # Make header of compressed file such that:
    # - The first byte indicates the amount of padding
    # - The second byte is the number n of symbols in the source subtracted by 1 to account for range [1,256]
    # - The next 3n bytes are three bytes for each symbol containing [symbol, number of bits of codeword, codeword]

    # Inputs:
    # bin_string: encoded binary string
    # encoder_dict: encoding dictionary

    # Outputs:
    # header: header of the compressed file

    header = ''
    n_symbols = len(encoder_dict) - 1
    header += BitArray(uint = n_symbols, length = 8).bin    # Add n_symbols to header
    for i in encoder_dict:    # For each symbol in the encoder
      n_bits = len(encoder_dict[i])   # Number of bits of the code
      header += f'{i}{BitArray(uint = n_bits, length = 8).bin}{encoder_dict[i]}'  # Add [symbol, number of bits of codeword, codeword]
    return header  

  def Encode(self, file):
    # Inputs:
    # file: file to be encoded

    # Outputs:
    # encoded_string: string of bits with the Huffman compressed representation of the file

    bitlist = self.read_bytes(file)    # Get list of bits
    freqs = self.make_frequency_tuples(bitlist)   # Make frequency table
    encoder_dict = self.create_encoder_dictionary(freqs)    # Create encoding dictionary
    orig_encoded_string = ''
    for i in bitlist:   # Encode each symbol on the list
      orig_encoded_string += encoder_dict[i]
    header = self.make_header(orig_encoded_string, encoder_dict) # Create and add header for encoded string
    encoded_string = header + orig_encoded_string
    n_pad = 8 - len(encoded_string)%8
    encoded_string = f'{BitArray(uint = n_pad, length = 8).bin}{encoded_string}{"0"*n_pad}'
    assert len(encoded_string)%8 == 0
    # Store variables as instance variables
    self.orig_encoded_string = orig_encoded_string
    self.freqs = freqs    
    self.encoder_dict = encoder_dict
    self.bitlist = bitlist
    self.encoded_string = encoded_string
    return encoded_string

  @staticmethod
  def Decode(encoded_bin_string):
    # Inputs:
    # encoded_bin_string: encoded representation of a file

    # Outputs:
    # decoded_string: binary string with the decoded binary form of the encoded file

    n_pad = BitArray(bin=encoded_bin_string[:8]).uint   # Check padding
    n_symb = BitArray(bin=encoded_bin_string[8:16]).uint + 1    # Check number of symbols
    head = encoded_bin_string[:16]    # Obtain first 2 bytes of header (n_pad, n_symb)
    code2symb = {}
    # Progressively remove header and its informations from the string
    bin_to_decompress = encoded_bin_string[16:]   
    for _ in range(n_symb):   # Loop to get informations from header symbol by symbol and remove it from string to be decompressed
      symb = bin_to_decompress[:8]    # Get the current symbol
      n_bits = BitArray(bin=bin_to_decompress[8:16]).uint   # Get the codewords number of bits
      code = bin_to_decompress[16:16+n_bits]    # Get codeword
      code2symb[code] = symb    # Add pair {codeword:symbol} to decompression dictionary
      # Add elements already processed to header and remove them from main string
      head += bin_to_decompress[:16+n_bits]   
      bin_to_decompress = bin_to_decompress[16+n_bits:]
    if n_pad>0:   # Remove padding from encoded string
      bin_to_decompress = bin_to_decompress[:-n_pad]
    symb_being_decoded = ''   # Variable to keep track of the current code being decoded
    decoded_string = ''   # Final decoded string
    for i in bin_to_decompress:   # Iterate over every bit on string without the header
      symb_being_decoded += i   # Add current symbol to variable
      # Check if code is in the decoding dictionary, if so, add its symbol to decoded string
      # and reinitialize tracking variable, but if not, keep adding bits until it is found in the dictionary
      if symb_being_decoded in code2symb:   
        decoded_string += code2symb[symb_being_decoded]
        symb_being_decoded = ''
    return decoded_string

  def Compress(self, file, output_path, evaluate_time = True):
    # Inputs:
    # file: full path to file to be compressed
    # output_path: path to save compressed file
    # evaluate_time: if True, prints time elapsed for compression, default = True   

    # Outputs:
    # compressed_file: Huffman-compressed file

    s = time() # Evaluate time
    if not os.path.isdir(output_path):  # Create Compressed directory if it does'nt already exist
      os.mkdir(output_path)
    filename = os.path.splitext(os.path.basename(file))[0]   # Create compressed file name
    compressed_file = os.path.join(output_path, f'{filename}_compressed.bin')
    encoded_string = self.Encode(file)    # Encode file
    with open(compressed_file, 'wb') as out:    # Use encoded string to create compressed file
    # Importante to note that the method .tofile() of class bitstring.BitArray automatically pads the input binary data
      BitArray(bin = encoded_string).tofile(out)
    e = time()
    if evaluate_time:
      print(f'{filename} compressed in {int(e-s)}s')
    return compressed_file

  def Decompress(self, compressed_file, output_path, extension = '.txt', evaluate_time = True):
    # Inputs:
    # compressed_file: full path to compressed file
    # output_path: path to save decompressed file
    # extension: desired extension of the decompressed file, defaults = '.txt'
    # evaluate_time: if True, prints time elapsed for compression, default = True  

    # Outputs:
    # decompressed_file: original file decompressed

    s = time()    # Evaluate time
    if not os.path.isdir(output_path):    # Create Decompressed directory if it does'nt already exist
      os.mkdir(output_path)
    match = re.match(r"(.*)_compressed", os.path.splitext(os.path.basename(compressed_file))[0])
    filename = match.group(1)
    decompressed_file = os.path.join(output_path, f'{filename}_decompressed{extension}')
    with open(compressed_file, 'rb') as f:    # Obtain string of bits from the compressed file
      encoded_bin_string = ''
      while True:
        byte = f.read(1)
        if byte:
          encoded_bin_string += BitArray(byte).bin
        else:
          break
    decoded_string = self.Decode(encoded_bin_string)    # Decode the string
    with open(decompressed_file, 'wb') as out:    # Decode file
      BitArray(bin = decoded_string).tofile(out)
    e = time()
    if evaluate_time:
      print(f'{filename} decompressed in {int(e-s)}s')
    return decompressed_file