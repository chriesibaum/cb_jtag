import threading
import time

import logging
log = logging.getLogger(__name__)

class CBBsrPin():
    # def __init__(self):
        # self.cb = None
        # self.cb_parent = None
    def __init__(self):
        self.last_val = None

    def __str__(self):
        return self.__class__.__name__

    def config(self, bsr, verbose = False):
        return bsr

    def deconfig(self, bsr, verbose = False):
        # Deconfigure pin
        if self.verbose or verbose:
            log.info(f'  Pin {self.pin} deconfigured')
        self.last_val = None
        return bsr

    def run_input(self, bsr):
        pass

    def run_output(self, bsr):
        return bsr

    def set_cb(self, cb=None, cb_parent=None):
        self.cb = cb
        self.cb_parent = cb_parent

    def call_cb(self):
        if self.cb is not None:
            if self.cb_parent is None:
                self.cb(self.pin, self.val)
            else:
                self.cb(self.cb_parent, self.pin, self.val)

    def set_verbose(self, verbose):
        self.verbose = verbose


class CBBsrPinNotifier(CBBsrPin):
    def __init__(self, bsdl, pin,
                 cb=None, cb_parent=None,
                 verbose=False):

        self.bsdl = bsdl
        self.pin = pin
        self.cb = cb
        self.cb_parent = cb_parent
        self.verbose = verbose

        self.cell_num = self.bsdl.get_bsr_cell_num(self.pin +'_in')

        self.val = 0
        self.last_val = None

    def get_val(self):
        return self.val

    def run_input(self, bsr):
        self.val = bsr.get_bit(self.cell_num)

        if self.val != self.last_val:
            if self.verbose:
                log.info(f'Pin {self.pin} changed to {self.val}')

            self.call_cb()

            self.last_val = self.val

        return bsr


class CBRsrOutput(CBBsrPin):
    def __init__(self, bsdl, pin,
                 val=0,
                 cb=None, cb_parent=None,
                 verbose=False):

        self.bsdl = bsdl
        self.pin = pin
        self.val = val
        self.val_last = None
        self.cb = cb
        self.cb_parent = cb_parent
        self.verbose = verbose

        self.cell_num = self.bsdl.get_bsr_cell_num(self.pin +'_out')
        self.cell_ccell = self.bsdl.get_bsr_cell_ccell(self.pin +'_out')
        self.cell_disval = self.bsdl.get_bsr_cell_disval(self.pin +'_out')

        self.last_toggle_time = time.time()


    def config(self, bsr, ctrl_cell=True, verbose = False):
        # Configure the BSR for the output pin and its value
        if self.verbose or verbose:
            log.info(f'  Pin {self.pin} as output, data cell {self.cell_num:4d}, ctrl cell {self.cell_ccell:4d}')

        if ctrl_cell:
            bsr = bsr.set_bit(self.cell_ccell, 1 ^ self.cell_disval)

        bsr = bsr.set_bit(self.cell_num, self.val)

        self.val_last = None

        return bsr

    def deconfig(self, bsr, verbose = False):
        # Deconfigure the BSR for the output pin (set to input)
        if self.verbose or verbose:
            log.info(f'  Pin {self.pin} as input, data cell {self.cell_num:4d}, ctrl cell {self.cell_ccell:4d}')

        bsr = bsr.set_bit(self.cell_ccell, self.cell_disval)
        return bsr


    def set_val(self, val = 1):
        self.val = val


    def clear_val(self):
        self.val = 0


    def run_output(self, bsr):
        if self.val != self.val_last:
            if self.verbose:
                log.info(f'Output Pin {self.pin:<5s} set to {self.val}')

            self.call_cb()

        self.val_last = self.val

        bsr = bsr.set_bit(self.cell_num, self.val)

        return bsr



class CBRsrOutputToggler(CBRsrOutput):
    def __init__(self, bsdl, pin, toggle_time=1, cb=None, cb_parent=None, verbose=False):
        super().__init__(bsdl, pin, val=0, cb=cb, cb_parent=cb_parent, verbose=verbose)

        self.toggle_time = toggle_time

        self.cell_num = self.bsdl.get_bsr_cell_num(self.pin +'_out')
        self.cell_ccell = self.bsdl.get_bsr_cell_ccell(self.pin +'_out')
        self.cell_disval = self.bsdl.get_bsr_cell_disval(self.pin +'_out')

        self.last_toggle_time = time.time()

    def run_output(self, bsr):
        if time.time() - self.last_toggle_time >= self.toggle_time:
            self.val ^= 1
            self.last_toggle_time = time.time()

        bsr = super().run_output(bsr)

        return bsr



class CBBsr(threading.Thread):
    def __init__(self, jtag, inst_extest = 0b00000, inst_scan = 0b00010, verbose = False):
        super(CBBsr, self).__init__()
        self.jtag = jtag
        self.inst_extest = inst_extest
        self.inst_scan = inst_scan
        self.verbose = verbose

        self.enable_flag = False
        self.run_flag = True

        # read the initial boundaray scan register
        self.bsr_out = self.jtag.read_bsr(self.inst_scan)
        if self.verbose:
            log.info('Initial boundary scan register (BSR):')
            log.info(f'  0x{self.bsr_out:076x}')


            # print the value in binary, with leading zeros, grouped in 16-bit blocks
            bsr_len = self.jtag.get_bsr_len_target_tap()
            bsr_bin = f'{self.bsr_out:0{bsr_len}b}'
            print('BSR default value (binary):')
            pad = (16 - bsr_len % 16) % 16
            padded = ' ' * pad + bsr_bin
            for i in range(0, len(padded), 16):
                block = padded[i:i+16]
                bit_num = bsr_len - 1 - max(i - pad, 0)
                grouped = ' '.join(block[j:j+4] for j in range(0, 16, 4))
                actual_bits = block.replace(' ', '')
                hex_width = (len(actual_bits) + 3) // 4
                hex_str = f'{int(actual_bits, 2):0{hex_width}x}' if actual_bits else ''
                print(f'  [{bit_num:>4}]: {grouped}  0x{hex_str}')

        self.pins = []

    def set_verbose(self, verbose):
        self.verbose = verbose

    def add_pin(self, pin: CBBsrPin):
        self.pins.append(pin)


    def config_pins(self):
        if self.verbose:
            log.info('Configuring BSR pins:')

        for pin in self.pins:
            self.bsr_out = pin.config(self.bsr_out, verbose=self.verbose)

        self.bsr_in = self.jtag.write_bsr(self.inst_extest, self.bsr_out)

    def deconfig_pins(self):
        if self.verbose:
            log.info('Deconfiguring BSR pins:')

        for pin in self.pins:
            self.bsr_out = pin.deconfig(self.bsr_out, verbose=self.verbose)

        self.bsr_in = self.jtag.write_bsr(self.inst_extest, self.bsr_out)

    def enable(self):
        self.enable_flag = True

    def disable(self):
        self.enable_flag = False

    def stop(self):
        self.run_flag = False
        time.sleep(0.1)  # give the thread some time to finish

    def get_running(self):
        return self.run_flag and self.enable_flag


    def run(self):
        write_intr = True
        while self.run_flag:
            while not self.enable_flag:
                if self.run_flag == False:
                    return
                time.sleep(0.1)
                # make sure to write the instruction again when re-enabling
                # the BSR thread after a disabled state
                write_intr = True

            for pin in self.pins:
                self.bsr_out = pin.run_output(self.bsr_out)

            if self.verbose > 1:
                log.info(f'bs_write:       0x{self.bsr_out:076x}')

            self.bsr_in = self.jtag.write_bsr(self.inst_extest, self.bsr_out, write_intr)
            # only write the instruction in the first iteration,
            # then keep it for subsequent iterations
            write_intr = False

            if self.verbose > 2:
                log.info(f'bs_read:        0x{self.bsr_in:076x}')


            for pin in self.pins:
                pin.run_input(self.bsr_in)

            # adjust this sleep time as needed to balance CPU usage and responsiveness
            time.sleep(0.0001)




