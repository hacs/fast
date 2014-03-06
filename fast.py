#!/usr/bin/env python
import os
import reticular

message = '''________             _____
___  __/_____ _________  /_
__  /_ _  __ `/_  ___/  __/
_  __/ / /_/ /_(__  )/ /_
/_/    \__,_/ /____/ \__/

Welcome! Use -h or --help to see command help.'''

reticular.CLI(message=message, directory=os.path.normpath(os.path.dirname(__file__))).run()
