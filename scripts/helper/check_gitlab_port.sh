# Lauscht wirklich jemand auf 5050?
sudo ss -ltnp | grep :5050    # oder: sudo lsof -i :5050

# GitLab Omnibus Komponenten:
sudo gitlab-ctl status | grep -i registry    # sollte "run: registry: (pid ...)" anzeigen
sudo gitlab-ctl tail registry                 # Registry-Logs live
sudo gitlab-ctl tail nginx | grep -i 5050     # NGINX-Proxy für Registry
