#!/usr/bin/python
import os
import sys

sys.path.append(os.path.dirname(os.path.realpath(__file__)) +"/pypaswas")

from pacasus.pacasusall import Pacasus
import logging

if __name__ == '__main__':
    try:
        ppw = Pacasus()
        ppw.run()
    except Exception as exception:
        # Show complete exception when running in DEBUG
        if (hasattr(ppw.settings, 'loglevel') and
            getattr(logging, 'DEBUG') == ppw.logger.getEffectiveLevel()):
            ppw.logger.exception(str(exception))
        else:
            print('Program ended. The message was: {}'.format(exception))
                
            print("Please use the option --help for information on command line arguments.")
