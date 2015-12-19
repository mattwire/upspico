# upspico
Scripts for the UPS PIco from http://www.pimodules.com/

These are tested and working on a Debian 8 (Stretch) system with systemd.

## Scripts - Descriptions
* pico_register_readout.py: Read all registers and output
* pico_status.py: Output status (voltage, onbattery etc. in the same format as apcaccess so you can use the same scripts to parse the output).
* picofssd_mail.py: UPS monitoring script.  Requires something like nullmailer to allow the system to actually send emails.  Monitors the UPS, checks for charging and sends emails on status change.
* picofu2.py: Firmware updater.

## Setup
```
mkdir /opt/upspicp
cd /opt/upspico
git clone https://github.com/mattwire/upspico.git
```
### To upload firmware:
/opt/upspico/picofu2.py -v -f /opt/upspico/firmware/UPS_PIco_V1.0_10_11_2015_code_0x53.hex

### Edit /etc/rc.local and add the following line before exit 0:
`/opt/upspico/picofssd_mail.py &`

### Enable serial port for upspico
Comment out in /etc/inittab:
`#T0:23:respawn:/sbin/getty -L ttyAMA0 115200 vt100`

Edit /boot/cmdline.txt from:
`dwc_otg.lpm_enable=0 console=ttyAMA0,115200 kgdboc=ttyAMA0,115200 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline rootwait`

To:
`dwc_otg.lpm_enable=0 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline rootwait`

### Setup hwclock with systemd
Note that this requires a recent kernel with rtc-ds1307 module

```
cp /opt/upspico/systemd/*.service /lib/systemd/system
systemctl enable hwclock-start hwclock-stop
```

Edit /etc/modules and add:
```
i2c-bcm2708
i2c-dev
rtc-ds1307
```

Add to /boot/config.txt:
```
dtparam=i2c_arm=on
dtoverlay=ds1307-rtc
dtparam=spi=on
```

## Useful Commands
### Set on battery runtime to maximum
`i2cset -y 1 0x6b 0x09 0xff`
