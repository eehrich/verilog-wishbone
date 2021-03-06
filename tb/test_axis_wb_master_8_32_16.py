#!/usr/bin/env python
"""

Copyright (c) 2016 Alex Forencich

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""

from myhdl import *
import os
import struct

try:
    from queue import Queue
except ImportError:
    from Queue import Queue

import axis_ep
import wb

module = 'axis_wb_master'

srcs = []

srcs.append("../rtl/%s.v" % module)
srcs.append("test_%s_8_32_16.v" % module)

src = ' '.join(srcs)

build_cmd = "iverilog -o test_%s_8_32_16.vvp %s" % (module, src)

def dut_axis_wb_master(clk,
                       rst,
                       current_test,

                       input_axis_tdata,
                       input_axis_tkeep,
                       input_axis_tvalid,
                       input_axis_tready,
                       input_axis_tlast,
                       input_axis_tuser,

                       output_axis_tdata,
                       output_axis_tkeep,
                       output_axis_tvalid,
                       output_axis_tready,
                       output_axis_tlast,
                       output_axis_tuser,

                       wb_adr_o,
                       wb_dat_i,
                       wb_dat_o,
                       wb_we_o,
                       wb_sel_o,
                       wb_stb_o,
                       wb_ack_i,
                       wb_err_i,
                       wb_cyc_o,

                       busy):

    if os.system(build_cmd):
        raise Exception("Error running build command")
    return Cosimulation("vvp -m myhdl test_%s_8_32_16.vvp -lxt2" % module,
                clk=clk,
                rst=rst,
                current_test=current_test,

                input_axis_tdata=input_axis_tdata,
                input_axis_tkeep=input_axis_tkeep,
                input_axis_tvalid=input_axis_tvalid,
                input_axis_tready=input_axis_tready,
                input_axis_tlast=input_axis_tlast,
                input_axis_tuser=input_axis_tuser,

                output_axis_tdata=output_axis_tdata,
                output_axis_tkeep=output_axis_tkeep,
                output_axis_tvalid=output_axis_tvalid,
                output_axis_tready=output_axis_tready,
                output_axis_tlast=output_axis_tlast,
                output_axis_tuser=output_axis_tuser,

                wb_adr_o=wb_adr_o,
                wb_dat_i=wb_dat_i,
                wb_dat_o=wb_dat_o,
                wb_we_o=wb_we_o,
                wb_sel_o=wb_sel_o,
                wb_stb_o=wb_stb_o,
                wb_ack_i=wb_ack_i,
                wb_err_i=wb_err_i,
                wb_cyc_o=wb_cyc_o,

                busy=busy)

def bench():

    # Parameters
    IMPLICIT_FRAMING = 0
    COUNT_SIZE = 16
    AXIS_DATA_WIDTH = 8
    AXIS_KEEP_WIDTH = (AXIS_DATA_WIDTH/8)
    WB_DATA_WIDTH = 32
    WB_ADDR_WIDTH = 31
    WB_SELECT_WIDTH = 2
    READ_REQ = 0xA1
    WRITE_REQ = 0xA2
    READ_RESP = 0xA3
    WRITE_RESP = 0xA4

    # Inputs
    clk = Signal(bool(0))
    rst = Signal(bool(0))
    current_test = Signal(intbv(0)[8:])

    input_axis_tdata = Signal(intbv(0)[AXIS_DATA_WIDTH:])
    input_axis_tkeep = Signal(intbv(1)[AXIS_KEEP_WIDTH:])
    input_axis_tvalid = Signal(bool(0))
    input_axis_tlast = Signal(bool(0))
    input_axis_tuser = Signal(bool(0))
    output_axis_tready = Signal(bool(0))
    wb_dat_i = Signal(intbv(0)[WB_DATA_WIDTH:])
    wb_ack_i = Signal(bool(0))
    wb_err_i = Signal(bool(0))

    # Outputs
    input_axis_tready = Signal(bool(0))
    output_axis_tdata = Signal(intbv(0)[AXIS_DATA_WIDTH:])
    output_axis_tkeep = Signal(intbv(1)[AXIS_KEEP_WIDTH:])
    output_axis_tvalid = Signal(bool(0))
    output_axis_tlast = Signal(bool(0))
    output_axis_tuser = Signal(bool(0))
    wb_adr_o = Signal(intbv(0)[WB_ADDR_WIDTH:])
    wb_dat_o = Signal(intbv(0)[WB_DATA_WIDTH:])
    wb_we_o = Signal(bool(0))
    wb_sel_o = Signal(intbv(0)[WB_SELECT_WIDTH:])
    wb_stb_o = Signal(bool(0))
    wb_cyc_o = Signal(bool(0))
    busy = Signal(bool(0))

    # sources and sinks
    source_queue = Queue()
    source_pause = Signal(bool(0))
    sink_queue = Queue()
    sink_pause = Signal(bool(0))

    source = axis_ep.AXIStreamSource(clk,
                                     rst,
                                     tdata=input_axis_tdata,
                                     tkeep=input_axis_tkeep,
                                     tvalid=input_axis_tvalid,
                                     tready=input_axis_tready,
                                     tlast=input_axis_tlast,
                                     tuser=input_axis_tuser,
                                     fifo=source_queue,
                                     pause=source_pause,
                                     name='source')

    sink = axis_ep.AXIStreamSink(clk,
                                 rst,
                                 tdata=output_axis_tdata,
                                 tkeep=output_axis_tkeep,
                                 tvalid=output_axis_tvalid,
                                 tready=output_axis_tready,
                                 tlast=output_axis_tlast,
                                 tuser=output_axis_tuser,
                                 fifo=sink_queue,
                                 pause=sink_pause,
                                 name='sink')

    # WB RAM model
    wb_ram_inst = wb.WBRam(2**16)

    wb_ram_port0 = wb_ram_inst.create_port(clk,
                                           adr_i=wb_adr_o,
                                           dat_i=wb_dat_o,
                                           dat_o=wb_dat_i,
                                           we_i=wb_we_o,
                                           sel_i=wb_sel_o,
                                           stb_i=wb_stb_o,
                                           ack_o=wb_ack_i,
                                           cyc_i=wb_cyc_o,
                                           latency=1,
                                           async=False,
                                           name='port0')

    # DUT
    dut = dut_axis_wb_master(clk,
                             rst,
                             current_test,
                             input_axis_tdata,
                             input_axis_tkeep,
                             input_axis_tvalid,
                             input_axis_tready,
                             input_axis_tlast,
                             input_axis_tuser,
                             output_axis_tdata,
                             output_axis_tkeep,
                             output_axis_tvalid,
                             output_axis_tready,
                             output_axis_tlast,
                             output_axis_tuser,
                             wb_adr_o,
                             wb_dat_i,
                             wb_dat_o,
                             wb_we_o,
                             wb_sel_o,
                             wb_stb_o,
                             wb_ack_i,
                             wb_err_i,
                             wb_cyc_o,
                             busy)

    @always(delay(4))
    def clkgen():
        clk.next = not clk

    @instance
    def check():
        yield delay(100)
        yield clk.posedge
        rst.next = 1
        yield clk.posedge
        rst.next = 0
        yield clk.posedge
        yield delay(100)
        yield clk.posedge

        # testbench stimulus

        yield clk.posedge
        print("test 1: test write")
        current_test.next = 1

        source_queue.put(bytearray(b'\xA2'+struct.pack('>IH', 0, 4)+b'\x11\x22\x33\x44'))
        yield clk.posedge

        yield input_axis_tvalid.negedge

        yield delay(100)

        yield clk.posedge

        data = wb_ram_inst.read_mem(0, 32)
        for i in range(0, len(data), 16):
            print(" ".join(("{:02x}".format(c) for c in bytearray(data[i:i+16]))))

        assert wb_ram_inst.read_mem(0, 4) == b'\x11\x22\x33\x44'

        rx_data = b''
        while not sink_queue.empty():
            rx_data += bytearray(sink_queue.get())
        print(repr(rx_data))
        assert rx_data == b'\xA4'+struct.pack('>IH', 0, 4)

        yield delay(100)

        yield clk.posedge
        print("test 2: test read")
        current_test.next = 2

        source_queue.put(bytearray(b'\xA1'+struct.pack('>IH', 0, 4)))
        yield clk.posedge

        yield input_axis_tvalid.negedge

        yield delay(100)

        yield clk.posedge

        rx_data = b''
        while not sink_queue.empty():
            rx_data += bytearray(sink_queue.get())
        print(repr(rx_data))
        assert rx_data == b'\xA3'+struct.pack('>IH', 0, 4)+b'\x11\x22\x33\x44'

        yield delay(100)

        yield clk.posedge
        print("test 3: various writes")
        current_test.next = 3

        for length in range(1,8):
            for offset in range(4):
                source_queue.put(bytearray(b'\xA2'+struct.pack('>IH', 256*(16*offset+length)+offset, length)+b'\x11\x22\x33\x44\x55\x66\x77\x88'[0:length]))
                yield clk.posedge

                yield input_axis_tvalid.negedge

                yield delay(200)

                yield clk.posedge

                data = wb_ram_inst.read_mem(256*(16*offset+length), 32)
                for i in range(0, len(data), 16):
                    print(" ".join(("{:02x}".format(c) for c in bytearray(data[i:i+16]))))

                assert wb_ram_inst.read_mem(256*(16*offset+length)+offset,length) == b'\x11\x22\x33\x44\x55\x66\x77\x88'[0:length]

                rx_data = b''
                while not sink_queue.empty():
                    rx_data += bytearray(sink_queue.get())
                print(repr(rx_data))
                assert rx_data == b'\xA4'+struct.pack('>IH', 256*(16*offset+length)+offset, length)

        yield delay(100)

        yield clk.posedge
        print("test 4: various reads")
        current_test.next = 4

        for length in range(1,8):
            for offset in range(4):
                source_queue.put(bytearray(b'\xA1'+struct.pack('>IH', 256*(16*offset+length)+offset, length)))
                yield clk.posedge

                yield input_axis_tvalid.negedge

                yield delay(200)

                yield clk.posedge

                rx_data = b''
                while not sink_queue.empty():
                    rx_data += bytearray(sink_queue.get())
                print(repr(rx_data))
                assert rx_data == b'\xA3'+struct.pack('>IH', 256*(16*offset+length)+offset, length)+b'\x11\x22\x33\x44\x55\x66\x77\x88'[0:length]

        yield delay(100)

        yield clk.posedge
        print("test 5: test leading padding")
        current_test.next = 5

        source_queue.put(bytearray(b'\xA2'+struct.pack('>IH', 4, 2)+b'\xAA\xBB'))
        source_queue.put(bytearray(b'\x00'*8+b'\xA2'+struct.pack('>IH', 6, 2)+b'\xCC\xDD'))
        source_queue.put(bytearray(b'\x00'*8+b'\xA1'+struct.pack('>IH', 4, 2)))
        source_queue.put(bytearray(b'\xA2'+struct.pack('>IH', 8, 2)+b'\xEE\xFF'))
        yield clk.posedge

        yield input_axis_tvalid.negedge

        yield delay(100)

        yield clk.posedge

        data = wb_ram_inst.read_mem(0, 32)
        for i in range(0, len(data), 16):
            print(" ".join(("{:02x}".format(c) for c in bytearray(data[i:i+16]))))

        assert wb_ram_inst.read_mem(4, 6) == b'\xAA\xBB\x00\x00\xEE\xFF'

        rx_data = b''
        while not sink_queue.empty():
            rx_data += bytearray(sink_queue.get())
        print(repr(rx_data))
        assert rx_data == b'\xA4'+struct.pack('>IH', 4, 2)+b'\xA4'+struct.pack('>IH', 8, 2)

        yield delay(100)

        yield clk.posedge
        print("test 6: test trailing padding")
        current_test.next = 6

        source_queue.put(bytearray(b'\xA2'+struct.pack('>IH', 10, 2)+b'\xAA\xBB'))
        source_queue.put(bytearray(b'\xA2'+struct.pack('>IH', 12, 2)+b'\xCC\xDD'+b'\x00'*8))
        source_queue.put(bytearray(b'\xA1'+struct.pack('>IH', 10, 2)+b'\x00'*8))
        source_queue.put(bytearray(b'\xA1'+struct.pack('>IH', 10, 2)+b'\x00'*1))
        source_queue.put(bytearray(b'\xA2'+struct.pack('>IH', 14, 2)+b'\xEE\xFF'))
        yield clk.posedge

        yield input_axis_tvalid.negedge

        yield delay(100)

        yield clk.posedge

        data = wb_ram_inst.read_mem(0, 32)
        for i in range(0, len(data), 16):
            print(" ".join(("{:02x}".format(c) for c in bytearray(data[i:i+16]))))

        assert wb_ram_inst.read_mem(10, 6) == b'\xAA\xBB\xCC\xDD\xEE\xFF'

        rx_data = b''
        while not sink_queue.empty():
            rx_data += bytearray(sink_queue.get())
        print(repr(rx_data))
        assert rx_data == b'\xA4'+struct.pack('>IH', 10, 2)+\
                            b'\xA4'+struct.pack('>IH', 12, 2)+\
                            b'\xA3'+struct.pack('>IH', 10, 2)+b'\xAA\xBB'+\
                            b'\xA3'+struct.pack('>IH', 10, 2)+b'\xAA\xBB'+\
                            b'\xA4'+struct.pack('>IH', 14, 2)

        yield delay(100)

        raise StopSimulation

    return dut, clkgen, source, sink, wb_ram_port0, check

def test_bench():
    sim = Simulation(bench())
    sim.run()

if __name__ == '__main__':
    print("Running test...")
    test_bench()
