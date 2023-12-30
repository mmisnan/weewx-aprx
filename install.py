# installer for weewx-aprx
# Distributed under the terms of the GNU Public License (GPLv3)

from weecfg.extension import ExtensionInstaller

def loader():
    return weewxAprxInstaller()

class weewxAprxInstaller(ExtensionInstaller):
    def __init__(self):
        super(weewxAprxInstaller, self).__init__(
            version="0.5",
            name='aprx',
            description='Emit an aprx ready file aprx_wx.txt.',
            author="Mohd Misnan",
            author_email="9m2tpt@gmail.com",
            process_services='user.aprx.weewxAprx',
            config={
                'weewxAprx' : {
                    'filename': '/var/tmp/aprx_wx.txt',
                    'binding': 'loop',
                    'symbol': '/_',
                    'note': '',
                    'position': 'true'},},
            files=[('bin/user', ['bin/user/aprx.py'])]
            )
