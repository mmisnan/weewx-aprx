# installer for weewx-aprx
# Distributed under the terms of the GNU Public License (GPLv3)

from weecfg.extension import ExtensionInstaller

def loader():
    return weewxaprxInstaller()

class weewxaprxInstaller(ExtensionInstaller):
    def __init__(self):
        super(weewxaprxInstaller, self).__init__(
            version="0.1",
            name='weewx-aprx',
            description='Emit a aprs aprx_wx.txt for LOOP data.',
            author="Mohd Misnan",
            author_email="9m2tpt@gmail.com",
            process_services='user.weewx-aprx',
            config={
                'weewx-aprx' : {
                    'filename': '/var/tmp/aprx_wx.txt'}},
            files=[('bin/user', ['bin/user/aprx.py'])]
            )
