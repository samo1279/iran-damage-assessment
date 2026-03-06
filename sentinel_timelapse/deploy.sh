#!/bin/bash
# Auto-deploy to 85.215.243.95

SERVER="85.215.243.95"
USER="root"

echo "🚀 Deploying to $SERVER..."

ssh $USER@$SERVER << 'ENDSSH'
set -e

echo "📦 Installing dependencies..."
apt update -qq
apt install -y python3 python3-pip python3-venv nodejs npm git libgdal-dev > /dev/null 2>&1

echo "📥 Cloning repository..."
cd /opt
rm -rf iran-damage-assessment
git clone https://github.com/samo1279/iran-damage-assessment.git
cd iran-damage-assessment

echo "🐍 Setting up Python..."
python3 -m venv venv
source venv/bin/activate
pip install --quiet -r requirements.txt

echo "⚛️ Building React frontend..."
cd frontend
npm install --silent
npm run build
cd ..

echo "🔥 Opening firewall..."
ufw allow 9000 2>/dev/null || true

echo "🛑 Stopping old instance..."
pkill -f "gunicorn app:app" 2>/dev/null || true
sleep 2

echo "🚀 Starting app..."
cd /opt/iran-damage-assessment
source venv/bin/activate
nohup venv/bin/gunicorn app:app --bind 0.0.0.0:9000 --workers 2 > /var/log/damage-app.log 2>&1 &

sleep 3
echo ""
echo "✅ DONE! App running at: http://85.215.243.95:9000"
ENDSSH
