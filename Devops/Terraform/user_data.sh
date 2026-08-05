#!/bin/bash
exec > >(tee /var/log/user-data.log | logger -t user-data ) 2>&1
set -xe

dnf update -y
dnf install -y git docker

systemctl enable docker
systemctl start docker

sleep 10

mkdir -p /usr/local/lib/docker/cli-plugins

curl -SL https://github.com/docker/compose/releases/download/v2.39.4/docker-compose-linux-x86_64 \
-o /usr/local/lib/docker/cli-plugins/docker-compose

chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

usermod -aG docker ec2-user

cd /home/ec2-user

git clone https://github.com/Prajwal7214/Document_Summarizer.git

cd Document_Summarizer/backend

cat > .env <<EOF
# API Keys
GROQ_API_KEY=
GEMINI_API_KEY=

# Redis
REDIS_URL=redis://redis:6379/0

# Qdrant
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=

# CORS
CORS_ORIGINS=http://localhost,http://localhost:5173,http://127.0.0.1:5173,http://15.206.153.66
EOF

cd ..

docker compose up -d --build