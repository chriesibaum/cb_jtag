import pytest
import time

from .test_base import CBJtagBase
from cb_jtag.cb_bsr import CBBsrPinNotifier, CBRsrOutput, CBRsrOutputToggler


class Test_Nucleo_U575(CBJtagBase):
    bsdl_file = './bsdl_files/STM32U575_U585_LQFP144.bsd'
    exp_num_taps = 2
    exp_idcodes = [0x2BA01477, 0x20000913]


