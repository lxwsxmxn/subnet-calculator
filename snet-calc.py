"""Script for calculationg subnets""" 
import re

nosferatu_chart = (128, 64, 32, 16, 8, 4, 2, 1) # Used for binary to decimal conversions 
nosferat2_chart = (2, 4, 8, 16, 32, 64, 128, 256) # Used for calculating the number of bit required for a specified number of subnets or host addresses  

smask_len_error = "Invalid Value: Subnet mask must be less than or equal to 32"

def splitcidr(cidr_address):
    """Devides the the address from the prefix"""
    return cidr_address.split("/")

def cidr2binsmask(cidr_prefix): # net_addr example: 192.168.0.0/16 
    """Converts a CIDR notation subnet mask to binary""" 
    smask_bin_array = [] 
    if cidr_prefix > 32: 
        return smask_len_error 
    else:
        for onbit in range(cidr_prefix): smask_bin_array.append(1)
        for offbit in range(32-cidr_prefix): smask_bin_array.append(0)
    return smask_bin_array

def binsmaskarray2matrix(binsmask):
    """Turns the binsmask array the cidr2binmask function returns into a nested array"""
    if binsmask == smask_len_error:
        return smask_len_error
    else:
        smask_bin_matrix = []
        count = 1
        temp_array = []
        for bit in binsmask:
            if count > 8:
                smask_bin_matrix.append(temp_array)
                temp_array = []
                count = 1
            temp_array.append(bit) 
            count += 1
            if len(smask_bin_matrix) == 3: smask_bin_matrix.append(temp_array)
        return smask_bin_matrix

def numberofbits(sub_net_mod):
    """Returns the number of bits required for a specified number of hosts or subnets"""
    bit_count = 1
    for num in nosferat2_chart:
        if num >= sub_net_mod:
            break
        bit_count += 1
    return bit_count

def findincrement(smask_matrix):
    """Finds the increment of a subnet mask"""
    increment = None
    increment_index = None
    matrix_index = 0
    for array_index in range(len(smask_matrix)):
        array = smask_matrix[array_index]
        for bit in range(len(array)):
            if bit == 7 and array[bit] == 1 and smask_matrix[array_index+1][0] == 0:
                increment_index = 7
            if array[bit] == 0:
                increment_index = bit-1 
                break
        if increment_index != None:
            increment = nosferatu_chart[increment_index]
            break
        if matrix_index > 3:
            matrix_index = None
            break
        matrix_index += 1
    if matrix_index == None:
        return "No results"
    else:
        return {"increment": increment, "increment_octet_location": matrix_index+1,"increment_index": increment_index}

def snetaddressrangegen(address_space):
    """Generates address ranges for specified subnet mask and address space"""
    address_space_array = [int(octet) for octet in address_space[:len(address_space)-3].split(".")]
    split_addr_space = splitcidr(address_space)
    increment_dict = findincrement(binsmaskarray2matrix(cidr2binsmask(int(split_addr_space[1]))))
    if type(increment_dict) != type(dict()):
        return "Invalid Address Space!"
    octet_index = increment_dict["increment_octet_location"]-1
    address_space_range_array = []

    for increment in range(0, 255, increment_dict["increment"]):
        start_range = f"{".".join([str(octet) for octet in address_space_array])}"
        if octet_index < 3:
            for subseq_octet in range(octet_index+1, len(address_space_array)):
                address_space_array[subseq_octet] = 255
        address_space_array[octet_index] = address_space_array[octet_index] + increment_dict["increment"]  
        temp_address_space_array = [octet for octet in address_space_array]
        temp_address_space_array[octet_index] = temp_address_space_array[octet_index]-1
        end_range = f"{".".join([str(octet) for octet in temp_address_space_array])}"
        address_space_range_array.append(f"{start_range}-{end_range}")
        if octet_index < 3:
            for subseq_octet in range(octet_index+1, len(address_space_array)):
                address_space_array[subseq_octet] = 0
    for snet_range in address_space_range_array:
        yield snet_range

def normalizenetaddress(net_addr, increment_dict):
    """Turn the octet where the increment and susequent octets to zero"""
    increment_octet = increment_dict["increment_octet_location"]
    net_addr_array = [int(octet) for octet in net_addr.split(".")]
    for octet_index in range(increment_octet, 4):
        net_addr_array[octet_index] = 0
    return ".".join([str(octet) for octet in net_addr_array])

def subnetcalc(net_addr, snet_size=None, num_of_snets=None): 
    """Calculates the number of bits required for a specified number of hosts or subnets"""
    cidr_address_array = splitcidr(net_addr)
    original_smask_bin_array = cidr2binsmask(int(cidr_address_array[1]))
    original_smask_bin_matrix = binsmaskarray2matrix(original_smask_bin_array)
    normalized_net_addr = normalizenetaddress(cidr_address_array[0], findincrement(original_smask_bin_matrix))
    if original_smask_bin_array == smask_len_error:
        return f"Cannot subnet: [{smask_len_error}]"
    else:
        if snet_size != None and snet_size >= 2:
            host_bits = numberofbits(snet_size)
            new_smask_cidr = 32 - host_bits
            if new_smask_cidr < int(cidr_address_array[1]):
                return "Cannot subnet!"
            else:
                return normalized_net_addr + f"/{new_smask_cidr}"
        elif num_of_snets != None and num_of_snets >= 2:
            net_bits = numberofbits(num_of_snets)
            new_smask_cidr = int(net_addr.split("/")[1]) + net_bits
            if new_smask_cidr < int(cidr_address_array[1]):
                return "Cannot subnet!"
            else:
                return normalized_net_addr + f"/{new_smask_cidr}"
        else:
            return "You don't need to this script for that."

program_help = "SYNTAX:\n<A.A.A.A>/<prefix> host=N\n<A.A.A.A>/<prefix> subnet=N\nq or quit - to quit program\nh or help - for for program syntax\ndispensesnet - print an address space\n\nEXAMPLE:\n192.168.1.0/24 hosts=13\n172.16.0.0/16 subnets=N\n"
subnet_range = "No subnet range!"
token_regex = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,3}|hosts=\d+|subnets=\d+")
print(program_help)
while True:
    try:
        net_addr_input = str(input(">"))
        if net_addr_input == "dispensesnet":
            if type(subnet_range) == type(str()):
                print(subnet_range)
            else:
                print(next(subnet_range))
        if net_addr_input == "h" or net_addr_input == "help":
            print(program_help)
        if net_addr_input == "q" or net_addr_input == "quit":
            break
        input_tokens = token_regex.findall(net_addr_input)
        if "host" in input_tokens[1]:
            host_based_subnets = subnetcalc(input_tokens[0], snet_size=int(input_tokens[1].split("=")[1]))
            print(host_based_subnets)
            subnet_range = snetaddressrangegen(host_based_subnets)
        if "subnet" in input_tokens[1]:
            net_based_subnets = subnetcalc(input_tokens[0], num_of_snets=int(input_tokens[1].split("=")[1]))
            print(net_based_subnets)
            subnet_range = snetaddressrangegen(net_based_subnets)
    except:
        continue
