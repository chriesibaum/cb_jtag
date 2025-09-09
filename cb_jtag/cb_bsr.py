import threading
import time


class CBBsrPin():

    def config(self, bsr, verbose = False):
        return bsr

    def deconfig(self, bsr, verbose = False):
        return bsr

    def run_input(self, bsr):
        pass

    def run_output(self, bsr):
        return bsr


class CBBsrPinNotifier(CBBsrPin):
    def __init__(self, bsdl, pin, cb=None, verbose=False):
        self.bsdl = bsdl
        self.pin = pin
        self.cb = cb
        self.verbose = verbose

        self.data_cell = self.bsdl.get_bsr_data_cell(self.pin +'_in')

        self.val = 0
        self.last_val = 0


    def run_input(self, bsr):
        self.val = bsr.get_bit(self.data_cell)

        if self.val != self.last_val:
            if self.verbose:
                print(f'Pin {self.pin} changed to {self.val}')

            if self.cb is not None:
                self.cb(self.pin, self.val)

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


    def config(self, bsr, verbose = False):
        # Configure the BSR for the output pin and its value
        if self.verbose or verbose:
            print(f'  Pin {self.pin} as output, data cell {self.data_cell:4d}, ctrl cell {self.ctrl_cell:4d}')

        bsr = bsr.set_bit(self.ctrl_cell, 1 ^ self.disval)
        bsr = bsr.set_bit(self.data_cell, self.val)

        return bsr

    def deconfig(self, bsr, verbose = False):
        # Deconfigure the BSR for the output pin (set to input)
        if self.verbose or verbose:
            print(f'  Pin {self.pin} as input, data cell {self.data_cell:4d}, ctrl cell {self.ctrl_cell:4d}')

        bsr = bsr.set_bit(self.ctrl_cell, self.disval)
        return bsr


    def set_bit(self, val = True):
        self.val = val


    def clear_bit(self):
        self.val = 0


    def run_output(self, bsr):
        if self.val != self.val_last:
            if self.verbose:
                print(f'Pin {self.pin:<5s} set to {self.val}')

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
                print(f'Pin {self.pin:<5s} set to {self.val}')

        bsr = bsr.set_bit(self.data_cell, self.val)
        return bsr



class CBBsr(threading.Thread):
    def __init__(self, jtag, verbose = False):
        super(CBBsr, self).__init__()
        self.jtag = jtag
        self.verbose = verbose

        self.run_flag = True

        # read the initial boundaray scan register
        self.bsr_out = self.jtag.read_bsr(0, 0b00000)
        if self.verbose:
            print('\nInitial boundary scan register (BSR):')
            print(f'  0x{self.bsr_out:076x}')

        self.pins = []

    def add_pin(self, pin: CBBsrPin):
        self.pins.append(pin)


    def config_pins(self):
        if self.verbose:
            print('\nConfiguring BSR pins:')

        for pin in self.pins:
            self.bsr_out = pin.config(self.bsr_out, verbose=self.verbose)

        self.bsr_in = self.jtag.write_bsr(0, 0b00000, self.bsr_out)

    def deconfig_pins(self):
        if self.verbose:
            print('\nDeconfiguring BSR pins:')

        for pin in self.pins:
            self.bsr_out = pin.deconfig(self.bsr_out, verbose=self.verbose)

        self.bsr_in = self.jtag.write_bsr(0, 0b00000, self.bsr_out)



    def stop(self):
        self.run_flag = False


    def run(self):
        while self.run_flag:

            for pin in self.pins:
                self.bsr_out = pin.run_output(self.bsr_out)

            if self.verbose > 1:
                print(f'bs_write:       0x{self.bsr_out:076x}')

            self.bsr_in = self.jtag.write_bsr(0, 0b00000, self.bsr_out)

            if self.verbose > 2:
                print(f'bs_read:        0x{self.bsr_in:076x}')


            for pin in self.pins:
                pin.run_input(self.bsr_in)

            time.sleep(0.001)




