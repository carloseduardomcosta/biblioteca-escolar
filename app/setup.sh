#!/usr/bin/env bash

# Script de preparação de ambiente para Biblioteca Escolar POC - Ubuntu 20.04
# Autor: ChatGPT TI
# Uso: Salve como setup.sh, dê permissão (chmod +x setup.sh) e execute: ./setup.sh

set -euo pipefail

# 1. Atualiza repositórios e realiza upgrade
sudo apt-get update \
    && sudo apt-get upgrade -y

# 2. Instala pacotes básicos
sudo apt-get install -y \
    git \
    curl \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    lsb-release \
    unzip \
    zip \
    tree \
    htop \
    ufw \
    fail2ban \
    imagemagick \
    zbar-tools

# 3. Instala Python 3.11 via Deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev python3.11-distutils

# 4. Atualiza 'python3' para apontar para a versão 3.11
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# 5. Instala pip para Python 3.11
curl -sS https://bootstrap.pypa.io/get-pip.py | sudo python3.11

# 6. Instala MySQL Server e cliente
sudo apt-get install -y mysql-server mysql-client libmysqlclient-dev
# Ajusta segurança inicial do MySQL (opcional)
sudo mysql_secure_installation <<< "y
password
password
y
y
y
y"

# 7. Instala conector Python para MySQL
python3 -m pip install --upgrade mysql-connector-python

# 8. Instala Docker Engine e Compose Plugin
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
# Adiciona usuário atual ao grupo 'docker'
sudo usermod -aG docker $USER

# 9. Habilita e inicia serviços
sudo systemctl enable mysql
sudo systemctl enable docker
sudo systemctl start mysql
sudo systemctl start docker

# 10. Configura firewall básico
sudo ufw allow OpenSSH
sudo ufw allow 5000/tcp    # Porta padrão Flask
sudo ufw --force enable

echo "\nInstalação concluída com sucesso!"
echo "Reinicie sua sessão ou faça logout/login para aplicar o grupo 'docker'."
