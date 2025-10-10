import threading
import time

import logging
log = logging.getLogger(__name__)

class CBBsrPin():
    def __str__(self):
        return self.__class__.__name__

    def config(self, bsr, verbose = False):
        return bsr

    def deconfig(self, bsr, verbose = False):
        return bsr

    def run_input(self, bsr):
        pass

    def run_output(self, bsr):
        return bsr

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

        self.data_cell = self.bsdl.get_bsr_data_cell(self.pin +'_in')

        self.val = 0
        self.last_val = 0

    def get_val(self):
        return self.val

    def set_cb(self, cb=None, cb_parent=None):
        self.cb = cb
        self.cb_parent = cb_parent

    def run_input(self, bsr):
        self.val = bsr.get_bit(self.data_cell)

        if self.val != self.last_val:
            if self.verbose:
                log.info(f'Pin {self.pin} changed to {self.val}')

            if self.cb is not None:
                if self.cb_parent is None:
                    self.cb(self.pin, self.val)
                else:
                    self.cb(self.cb_parent, self.pin, self.val)

            self.last_val = self.val

        return bsr



class CBRsrOutput(CBBsrPin):
    def __init__(self, bsdl, pin, val = 0, verbose = False):
        self.bsdl = bsdl
        self.pin = pin
        self.val = val
        self.val_last = val
        self.verbose = verbose

        self.data_cell = self.bsdl.get_bsr_data_cell(self.pin +'_out')
        self.ctrl_cell = self.bsdl.get_bsr_ctrl_cell(self.pin +'_out')
        self.disval = self.bsdl.get_bsr_disval(self.pin +'_out')

        self.last_toggle_time = time.time()


    def config(self, bsr, ctrl_cell=True, verbose = False):
        # Configure the BSR for the output pin and its value
        if self.verbose or verbose:
            log.info(f'  Pin {self.pin} as output, data cell {self.data_cell:4d}, ctrl cell {self.ctrl_cell:4d}')

        if ctrl_cell:
            bsr = bsr.set_bit(self.ctrl_cell, 1 ^ self.disval)
        bsr = bsr.set_bit(self.data_cell, self.val)

        return bsr

    def deconfig(self, bsr, verbose = False):
        # Deconfigure the BSR for the output pin (set to input)
        if self.verbose or verbose:
            log.info(f'  Pin {self.pin} as input, data cell {self.data_cell:4d}, ctrl cell {self.ctrl_cell:4d}')

        bsr = bsr.set_bit(self.ctrl_cell, self.disval)
        return bsr


    def set_val(self, val = True):
        self.val = val


    def clear_val(self):
        self.val = 0


    def run_output(self, bsr):
        if self.val != self.val_last:
            if self.verbose:
                log.info(f'Pin {self.pin:<5s} set to {self.val}')

        self.val_last = self.val
        bsr = bsr.set_bit(self.data_cell, self.val)
        return bsr



class CBRsrOutputToggler(CBRsrOutput):
    def __init__(self, bsdl, pin, toggle_time = 1, verbose = False):
        self.bsdl = bsdl
        self.pin = pin
        self.toggle_time = toggle_time
        self.verbose = verbose

        self.data_cell = self.bsdl.get_bsr_data_cell(self.pin +'_out')
        self.ctrl_cell = self.bsdl.get_bsr_ctrl_cell(self.pin +'_out')
        self.disval = self.bsdl.get_bsr_disval(self.pin +'_out')

        self.val = 0
        self.last_toggle_time = time.time()

    def run_output(self, bsr):
        if time.time() - self.last_toggle_time > self.toggle_time:
            self.val ^= 1
            self.last_toggle_time = time.time()

            if self.verbose:
                log.info(f'Pin {self.pin:<5s} set to {self.val}')

        bsr = bsr.set_bit(self.data_cell, self.val)
        return bsr



class CBBsr(threading.Thread):
    def __init__(self, jtag, verbose = False):
        super(CBBsr, self).__init__()
        self.jtag = jtag
        self.verbose = verbose

        self.enable_flag = False
        self.run_flag = True

        # read the initial boundaray scan register
        self.bsr_out = self.jtag.read_bsr(0, 0b00000)
        if self.verbose:
            log.info('Initial boundary scan register (BSR):')
            log.info(f'  0x{self.bsr_out:076x}')

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

        self.bsr_in = self.jtag.write_bsr(0, 0b00000, self.bsr_out)

    def deconfig_pins(self):
        if self.verbose:
            log.info('Deconfiguring BSR pins:')

        for pin in self.pins:
            self.bsr_out = pin.deconfig(self.bsr_out, verbose=self.verbose)

        self.bsr_in = self.jtag.write_bsr(0, 0b00000, self.bsr_out)

    def enable(self):
        self.enable_flag = True

    def disable(self):
        self.enable_flag = False

    def stop(self):
        self.run_flag = False

    def get_running(self):
        return self.run_flag and self.enable_flag


    def run(self):
        while self.run_flag:
            while not self.enable_flag:
                if self.run_flag == False:
                    return
                time.sleep(0.1)

            for pin in self.pins:
                self.bsr_out = pin.run_output(self.bsr_out)

            if self.verbose > 1:
                log.info(f'bs_write:       0x{self.bsr_out:076x}')

            self.bsr_in = self.jtag.write_bsr(0, 0b00000, self.bsr_out)

            if self.verbose > 2:
                log.info(f'bs_read:        0x{self.bsr_in:076x}')


            for pin in self.pins:
                pin.run_input(self.bsr_in)


            time.sleep(0.001)




