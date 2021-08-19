#!/bin/bash
# Finalize setup of Stenogotchi. Only needs to be run once.
# Use the below steps if you prefer not executing the automated script or run into issues.
# ------------------------------------------------------------------------------------------
#  1) Add configuration file for D-Bus service used by Stenogotchi and the Plover plugin to communicate  
#cp ./stenogotchi/plover_plugin/stenogotchi_link/com.github.stenogotchi.conf /etc/dbus-1/system.d/
#  2) Modify service file to remove input bluetooth plugin so it does not grab the sockets Stenogotchi requires access to. 
#    Append '-P input' to existing line in '/lib/systemd/system/bluetooth.service' file to end up with:
#ExecStart=/usr/libexec/bluetooth/bluetoothd -P input
#  3) Ensure 'root' user autologin to local terminal is enabled using dietpi-autostart
#  4) Create file '~/.bash_profile' with the below content (excluding #-characters)
#if [[ -z $DISPLAY ]] && [[ $(tty) = /dev/tty1 ]]; then
#  screen -S stenogotchi -dm python3 /root/stenogotchi/stenogotchi.py --debug
#  xinit
#fi
#  5) Create file '~/.xinitrc' with the below content
#screen -S plover plover -g none -l debug
#  6) Launch Stenogotchi manually once which will complete setup and reboot device. 
#     Configure settings per preference in '/etc/stenogotchi/config.toml' after reboot.
#  7) Optional but highly recommended. Reduce boot time by disabling Dietpi and APT update check and setting initial turbo boost to 60s.
#     In /boot/dietpi.txt set below values:
#CONFIG_CHECK_DIETPI_UPDATES=0
#CONFIG_CHECK_APT_UPDATES=0
#     In /boot/config.txt set:
#initial_turbo=60
#  8) Optional but recommended. Reduce boot time further by disabling waiting for network and NTP time sync.
#     Doing this you should be aware that the RPI0w does not have a hardware clock. It will lose track of real world time as soon it is powered off, making log timestamps or any time based action you may set up unreliable. None of this is important for the core functionality of the Stenogotchi and disabling time-sync at boot can shave up to a minute off the boot process. By adding a cheap I2C hardware clock you can completely remove the need for network sync.
#     In /boot/dietpi.txt set below values:
#CONFIG_BOOT_WAIT_FOR_NETWORK=0
#CONFIG_NTP_MODE=0
#  9) Launch stenogotchi manually and configure using /etc/stenogotchi/config.toml after reboot has completed
#python3 ./stenogotchi/stenogotchi.py

FLAG="/var/log/_stenogotchi_setup_completed.log"
BASEDIR=$(cd `dirname $0` && pwd)

# Check and run script only if it hasn't been done already
if [ ! -f $FLAG ]; then
    # Set flag indicating script has been run
    touch $FLAG

    # Configure bluetooth service
    printf "Adding configuration file for D-Bus service used by Stenogotchi and the Plover plugin to communicate.\n"
    sleep 1
    cp $BASEDIR/plover_plugin/stenogotchi_link/com.github.stenogotchi.conf /etc/dbus-1/system.d/ && printf "Success!\n" || printf "Failed! \nPlease manually copy 'com.github.stenogotchi.conf' from stenogotchi_link folder to '/etc/dbus-1/system.d/'"

    printf "\nModifying service file to remove input bluetooth plugin so it does not grab the sockets Stenogotchi requires access to.\n"
    sleep 1
    # Only add in case not appended yet
    if ! grep -q "\-P input" /lib/systemd/system/bluetooth.service; then
        sed '/^ExecStart=/s/$/ -P input/' /lib/systemd/system/bluetooth.service -i.bkp && printf "Success!\n" || printf "Failed! \nPlease manually modify existing line in '/lib/systemd/system/bluetooth.service' to 'ExecStart=/usr/lib/bluetooth/bluetoothd -P input' "
    else
        printf "Skipped! Bluetooth input plugin already disabled\n"
    fi

   # Configure autostart of plover
    printf "\nConfigure Stenogotchi to auto-start at boot. Will run under screen session named 'stenogotchi'\n"
    sleep 1
    echo "screen -S plover plover -g none -l debug" > ~/.xinitrc && printf "Success!\n" || printf "Failed! \nPlease manually create file '~/.xinitrc' with contents 'screen -S plover plover -g none -l debug'"

    # Configure autostart of stenogotchi
    read -r -d '' AUTOSTART << "EOM"
if [[ -z $DISPLAY ]] && [[ $(tty) = /dev/tty1 ]]; then
  screen -S stenogotchi -dm python3 /root/stenogotchi/stenogotchi.py --debug
  xinit
fi 
EOM

    printf "\nConfigure Plover to auto-start at boot. Will run under screen session named 'plover'\n"
    sleep 1
    echo "$AUTOSTART" > ~/.bash_profile && printf "Success!\n" || printf "Failed! \nPlease manually create '~/.bash_profile' file with contents \n"$AUTOSTART" "

    # Optionally: Optimize boot time
    printf "\nReduce boot time by disabling automatic Dietpi and APT update checks. Set initial turbo boost to 60s."
    printf "\nSettings can be changed later in '/boot/dietpi.txt' and '/boot/config.txt'\n"
    while true; do
        read -p "Do you wish to enable these highly recommended optimizations? (y/n)" yn
        case $yn in
            [Yy]* )
                sed -i 's/CONFIG_CHECK_DIETPI_UPDATES=.*/CONFIG_CHECK_DIETPI_UPDATES=0/' /boot/dietpi.txt && printf "set CONFIG_CHECK_DIETPI_UPDATES=0 in /boot/dietpi.txt\n";
                sed -i 's/CONFIG_CHECK_APT_UPDATES=.*/CONFIG_CHECK_APT_UPDATES=0/' /boot/dietpi.txt && printf "set CONFIG_CHECK_APT_UPDATES=0 in /boot/dietpi.txt\n";
                sed -i 's/initial_turbo=.*/initial_turbo=60/' /boot/config.txt && printf "set initial_turbo=60 in /boot/config.txt\n";
                break;;
            [Nn]* ) 
                printf "Boot optimization skipped. Enable later by setting CONFIG_CHECK_DIETPI_UPDATES=0 and CONFIG_CHECK_APT_UPDATES=0 in /boot/dietpi.txt and initial_turbo=60 in /boot/config.txt\n";
                break;;
            * ) echo "Please answer yes or no.";;
        esac
    done

    # Optionally: Disable waiting for network and NTP-sync   
    printf "\nDisable waiting for network and NTP-sync at boot to significantly reduce boot time when networks are unavailable."
    printf "\nSettings can be changed later in '/boot/dietpi.txt'\n"
    while true; do
        read -p "Do you wish to enable these optimizations? (y/n)" yn
        case $yn in
            [Yy]* )
                sed -i 's/CONFIG_BOOT_WAIT_FOR_NETWORK=.*/CONFIG_BOOT_WAIT_FOR_NETWORK=0/' /boot/dietpi.txt && printf "set CONFIG_BOOT_WAIT_FOR_NETWORK=0 in /boot/dietpi.txt\n";
                sed -i 's/CONFIG_NTP_MODE=.*/CONFIG_NTP_MODE=0/' /boot/dietpi.txt && printf "set CONFIG_NTP_MODE=0 in /boot/dietpi.txt\n";
                break;;
            [Nn]* ) 
                printf "Boot optimization skipped. Enable later by setting CONFIG_BOOT_WAIT_FOR_NETWORK=0 and CONFIG_NTP_MODE=0 in /boot/dietpi.txt\n";
                break;;
            * ) echo "Please answer yes or no.";;
        esac
    done
    
    # Initial launch of Stenogotchi which triggers reboot
    printf "\nFirst time launch of Stenogotchi. Configure settings in /etc/stenogotchi/config.toml after reboot\n"
    sleep 5
    python3 $BASEDIR/stenogotchi.py
else
    printf "Setup script has already been executed and should not need to be run again. (Delete '/var/log/_stenogotchi_setup_completed.log' to bypass check)\n"
fi