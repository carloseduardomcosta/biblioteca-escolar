# protheus/Dockerfile

# 1. Base Linux com JRE (se o Protheus rodar em Java) ou Debian puro
FROM debian:bullseye-slim

# 2. Metadados
LABEL maintainer="seu@email"

# 3. Diretório de trabalho dentro do container
WORKDIR /opt/protheus

# 4. Copia todo o seu pacote Protheus (binaries, config, scripts)
#    supondo que você tenha colocado dentro de protheus/ tudo que
#    precisa: servidor, arquivos .ini, libs, etc.
COPY . .

# 5. Instala runtimes e dependências (ajuste conforme sua stack)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      default-jre-headless \
      unzip \
      libaio1 \
 && rm -rf /var/lib/apt/lists/*

# 6. Exponha a porta onde o Protheus escuta (ex: 9000 ou conforme seu appserver.ini)
EXPOSE 9000

# 7. Comando de inicialização (ajuste para o script real de start do Protheus)
#    Pode ser um shell script que chama o servidor, carrega configs, etc.
CMD ["./start-protheus.sh"]
