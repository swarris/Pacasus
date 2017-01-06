#!/usr/bin/python
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) +"/pypaswas")

from pacagus.pacagusall import pacagus
import logging

if __name__ == '__main__':

    try:
        ppw = pacagus()
        ppw.run()
    except Exception as exception:
        # Show complete exception when running in DEBUG
        if (hasattr(ppw.settings, 'loglevel') and
            getattr(logging, 'DEBUG') == ppw.logger.getEffectiveLevel()):
            ppw.logger.exception(str(exception))
        else:
            print('Program ended. The message was: ', ','.join(exception.args))
            print("Please use the option --help for information on command line arguments.")
