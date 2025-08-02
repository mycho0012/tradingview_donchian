#!/bin/bash

# AWS Ubuntu에서 ngrok + Docker Kelly Trading Bot 설정
echo "🚀 AWS ngrok + Docker Kelly Trading Bot 설정"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}📋 Step 1: 시스템 업데이트${NC}"
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget unzip

echo -e "${YELLOW}📋 Step 2: Docker 설치${NC}"
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

echo -e "${YELLOW}📋 Step 3: ngrok 설치${NC}"
# ngrok 최신 버전 다운로드
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin
rm ngrok-v3-stable-linux-amd64.tgz

echo -e "${YELLOW}📋 Step 4: ngrok 인증${NC}"
echo "ngrok authtoken을 입력하세요 (https://dashboard.ngrok.com/get-started/your-authtoken):"
read -p "authtoken: " NGROK_TOKEN
ngrok config add-authtoken $NGROK_TOKEN

echo -e "${YELLOW}📋 Step 5: 자동 시작 스크립트 생성${NC}"

# Kelly Trading Bot 시작 스크립트
cat > start_kelly_bot.sh << 'EOF'
#!/bin/bash

# Kelly Trading Bot + ngrok 자동 시작 스크립트
echo "🚀 Kelly Trading Bot 시작..."

# Docker 컨테이너 시작
cd ~/kelly-trading-bot
docker-compose up -d

# 3초 대기
sleep 3

# ngrok 터널 시작 (백그라운드)
echo "🌐 ngrok 터널 시작..."
nohup ngrok http 8000 > ngrok.log 2>&1 &

# 5초 대기 후 URL 확인
sleep 5

# ngrok URL 획득
WEBHOOK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['tunnels'][0]['public_url'] + '/webhook')
except:
    print('URL 획득 실패')
")

echo "✅ Kelly Trading Bot 시작 완료!"
echo "🌐 웹훅 URL: $WEBHOOK_URL"
echo ""
echo "📋 유용한 명령어:"
echo "• 컨테이너 로그: docker-compose logs -f kelly-trading"
echo "• ngrok 상태: curl http://localhost:4040/api/tunnels"
echo "• 시스템 중지: ./stop_kelly_bot.sh"

# URL을 파일에 저장
echo $WEBHOOK_URL > current_webhook_url.txt
EOF

# 중지 스크립트
cat > stop_kelly_bot.sh << 'EOF'
#!/bin/bash

echo "🛑 Kelly Trading Bot 중지..."

# ngrok 프로세스 종료
pkill -f ngrok

# Docker 컨테이너 중지
cd ~/kelly-trading-bot
docker-compose down

echo "✅ 중지 완료"
EOF

# 재시작 스크립트
cat > restart_kelly_bot.sh << 'EOF'
#!/bin/bash

echo "🔄 Kelly Trading Bot 재시작..."

# 중지
./stop_kelly_bot.sh

# 3초 대기
sleep 3

# 시작
./start_kelly_bot.sh
EOF

# 실행 권한 부여
chmod +x start_kelly_bot.sh
chmod +x stop_kelly_bot.sh  
chmod +x restart_kelly_bot.sh

echo -e "${YELLOW}📋 Step 6: 시스템 서비스 등록 (선택사항)${NC}"

# systemd 서비스 파일 생성
sudo tee /etc/systemd/system/kelly-trading-bot.service > /dev/null << EOF
[Unit]
Description=Kelly Trading Bot with ngrok
After=network.target docker.service

[Service]
Type=forking
User=ubuntu
WorkingDirectory=/home/ubuntu/kelly-trading-bot
ExecStart=/home/ubuntu/kelly-trading-bot/start_kelly_bot.sh
ExecStop=/home/ubuntu/kelly-trading-bot/stop_kelly_bot.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 서비스 활성화
sudo systemctl daemon-reload
sudo systemctl enable kelly-trading-bot

echo -e "${GREEN}🎉 AWS ngrok + Docker 설정 완료!${NC}"
echo ""
echo -e "${BLUE}📋 다음 단계:${NC}"
echo "1. Kelly Trading Bot 코드 업로드"
echo "2. .env 파일 설정"
echo "3. ./start_kelly_bot.sh 실행"
echo "4. TradingView에서 새 웹훅 URL 설정"
echo ""
echo -e "${YELLOW}🔧 관리 명령어:${NC}"
echo "• 시작: ./start_kelly_bot.sh"
echo "• 중지: ./stop_kelly_bot.sh"
echo "• 재시작: ./restart_kelly_bot.sh"
echo "• 상태 확인: sudo systemctl status kelly-trading-bot"