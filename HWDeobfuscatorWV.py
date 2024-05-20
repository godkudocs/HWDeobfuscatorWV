import sys
import Helper
import Scanner
import GraphHelper
import Cleaner
import Rebuilder
import Injector
import xboxpy  # Import the xboxpy library

graph_name = "graph.txt"
image_name = "graph.png"
graph_name_cleaned = "graph_clean.txt"
image_name_cleaned = "graph_clean.png"
result_binary_name = "result.bin"

Helper.init_helper()
Helper.file_delete(graph_name)
Helper.file_delete(image_name)
Helper.file_delete(graph_name_cleaned)
Helper.file_delete(image_name_cleaned)
Helper.file_delete(result_binary_name)
config = Helper.load_config()

# Connect to Xbox One
console_ip = config["console_ip"]
xbox = xboxpy.XboxOne(console_ip)
Helper.assert_true(xbox is not None, "Could not connect to Xbox One", "Connected to Xbox One at " + console_ip)

# Retrieve the process ID for Happy Wars
pid = xbox.get_process_id("Happy Wars")
Helper.assert_true(pid is not None, "Happy Wars process not found on Xbox One", "Found Happy Wars process id = " + str(pid))

# Retrieve the process handle
handle = xbox.open_process(pid)
Helper.assert_true(handle is not None, "Could not get a process handle on Xbox One", "Got handle to process")

# Retrieve the base address of the process
base_addr = xbox.get_base_address(handle)
Helper.assert_true(base_addr is not None, "Could not get a base address on Xbox One", "Got base address = " + hex(base_addr))
Helper.assert_true(base_addr == 0x3F0000, "Base address should be 0x3F0000, remove ASLR first on Xbox One!", "Base address correct")

# Read memory to verify the EXE header
test = xbox.read_memory(handle, base_addr, 4)
test_value = int.from_bytes(test, byteorder='little')
Helper.assert_true(test_value == 0x905A4D, "EXE header not found on Xbox One!", "EXE header found")

start_addr = int(config["startaddress"], 16)
Helper.assert_true(start_addr > base_addr, "Start address is lower than base address on Xbox One", "Start address OK")

seen_addr = []
blist = []
used_hint = []
block = Scanner.get_asm_block(handle, start_addr, seen_addr, blist, used_hint, config["hints"])
Helper.assert_true(True, "", "Scanning done on Xbox One")
seen_addr = []
Helper.print_block(block, 0, blist, seen_addr)
Helper.assert_true(True, "", "Tree printing done on Xbox One")
GraphHelper.make_graph(blist, graph_name)
Helper.assert_true(Helper.file_exists(graph_name), "Graph file was not created on Xbox One", "Graph file was created")
GraphHelper.make_image(graph_name, image_name)
Helper.assert_true(Helper.file_exists(image_name), "Image file was not created on Xbox One", "Image file was created")
Cleaner.clean_graph(blist)
GraphHelper.make_graph(blist, graph_name_cleaned)
Helper.assert_true(Helper.file_exists(graph_name_cleaned), "Graph file was not created on Xbox One", "Graph file was created")
GraphHelper.make_image(graph_name_cleaned, image_name_cleaned)
Helper.assert_true(Helper.file_exists(image_name_cleaned), "Image file was not created on Xbox One", "Image file was created")

if config["rebuild"] == 1 and len(used_hint) == 0:
    byte_code = Rebuilder.rebuild(blist, start_addr)
    print("New binary size =", hex(len(byte_code)))
    rebuild_addr = xbox.alloc_memory(handle, len(byte_code))
    print("Allocated new memory at", hex(rebuild_addr))
    byte_code = Rebuilder.rebuild(blist, rebuild_addr)
    Helper.save_binary(byte_code, result_binary_name)
    if config["inject"] == 1:
        Helper.assert_true(Helper.file_exists(result_binary_name), "Result binary was not created on Xbox One", "Result binary was created")
        xbox.inject_code(handle, start_addr, rebuild_addr, byte_code)
Helper.assert_true(True, "", "Done on Xbox One!")
