sudo apt update && sudo apt upgrade && sudo apt autoremove #upgrade packages
sudo hostnamectl set-hostname exam_host #change hostname
ip a #check ip
sudo dhclient #connect to dhcp
sudo ping -c 4 8.8.8.8 #check connection
sudo apt install -y cups cups-pdf #install app adds printer 
sudo systemctl restart cups #if need to restart something
sudo systemctl enable --now cups #activate v printer
sudo lpstat -r #проверка, что служба работает
tar -czvf backup_home.tar.gz /home/ #create backup zip
sudo adduser testuser #add user
sudo groupadd developers #create group developers
sudo usermod -aG developers testuser #add testuser into devs group
sudo passwd testuser # change password for testuser
