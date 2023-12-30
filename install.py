# installer for cwxn
# Copyright 2014-2020 Matthew Wall
# Distributed under the terms of the GNU Public License (GPLv3)

from weecfg.extension import ExtensionInstaller

def loader():
    return weewxaprxInstaller()

class weewxaprxInstaller(ExtensionInstaller):
    def __init__(self):
        super(weewxaprxInstaller, self).__init__(
            version="0.5",
            name='weewx-aprx',
            description='Emit a aprs wxnow.txt for LOOP data.',
            author="Mohd Misnan",
            author_email="9m2tpt@gmail.com",
            process_services='user.weewx-aprx',
            config={
                'CumulusWXNow' : {
                    'filename': '/var/tmp/wxnow.txt'}},
            files=[('bin/user', ['bin/user/aprx.py'])]
            )
