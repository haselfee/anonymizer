# CA auf Docker-Host vertrauen
sudo mkdir -p /etc/docker/certs.d/vmgitlab:5050/
sudo cp ca.crt /etc/docker/certs.d/vmgitlab:5050/ca.crt
sudo systemctl restart docker
# (curl/openssl nutzen systemweite CAs; optional in /usr/local/share/ca-certificates/ ablegen und update-ca-certificates)
