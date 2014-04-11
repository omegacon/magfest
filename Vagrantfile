# -*- mode: ruby -*-

VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
    config.vm.box = "UbuntuRaringRingtailServer"
    config.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/raring/current/raring-server-cloudimg-i386-vagrant-disk1.box"
    config.vm.network :forwarded_port, guest: 4321, host: 4321
    config.vm.synced_folder ".", "/home/vagrant/magfest"
    config.vm.provision :shell, :path => "vagrant/vagrant.sh"
end