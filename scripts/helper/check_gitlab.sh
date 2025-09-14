# Hostname-Auflösung
getent hosts vmgitlab

# Port offen?
nc -vz vmgitlab 5050    # oder: timeout 3 bash -c '</dev/tcp/vmgitlab/5050' && echo "open"

# TLS-Handshake + Zert anzeigen (SAN=vmgitlab?)
openssl s_client -connect vmgitlab:5050 -servername vmgitlab -showcerts </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer -dates

# Registry-V2 Probe (sollte 200 OK oder 401 Unauthorized liefern)
curl -vkI https://vmgitlab:5050/v2/
# Erwartete Header u. a.:  HTTP/1.1 401 Unauthorized  +  Docker-Distribution-API-Version: registry/2.0
