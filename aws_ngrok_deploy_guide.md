# 🚀 AWS + ngrok + Docker Kelly Trading Bot 완전 배포 가이드

## 🎯 왜 이 방법인가?

**TradingView 웹훅 URL 제한:**
- ❌ `http://IP:8000/webhook` (포트 번호 불가)
- ✅ `https://abc123.ngrok.io/webhook` (ngrok URL 가능)

**AWS + ngrok의 장점:**
- ✅ TradingView 100% 호환
- ✅ 24시간 안정적 운영
- ✅ 자동 재시작 지원
- ✅ SSL 자동 제공

## 📋 Step-by-Step 배포 가이드

### 1단계: AWS EC2 설정

```bash
# EC2 인스턴스 생성
- 타입: t3.micro (프리티어)
- OS: Ubuntu 22.04 LTS
- 보안 그룹: SSH (22) 포트만 열기
- 키페어: SSH 접속용
```

### 2단계: SSH 접속 및 초기 설정

```bash
# SSH 접속
ssh -i your-key.pem ubuntu@your-ec2-ip

# 설정 스크립트 다운로드
wget https://raw.githubusercontent.com/your-repo/aws_ngrok_setup.sh
chmod +x aws_ngrok_setup.sh
./aws_ngrok_setup.sh
```

### 3단계: Kelly Trading Bot 코드 배포

```bash
# GitHub에서 코드 클론
git clone https://github.com/your-username/kelly-trading-bot.git
cd kelly-trading-bot

# .env 파일 생성
nano .env
```

`.env` 내용:
```
UPBIT_ACCESS_KEY=your_access_key
UPBIT_SECRET_KEY=your_secret_key
PASSPHRASE=MyTradingBot2024
```

### 4단계: Kelly Trading Bot 시작

```bash
# 봇 시작 (Docker + ngrok)
./start_kelly_bot.sh
```

**출력 예시:**
```
🚀 Kelly Trading Bot 시작...
✅ Kelly Trading Bot 시작 완료!
🌐 웹훅 URL: https://abc123.ngrok.io/webhook
```

### 5단계: TradingView 알림 업데이트

**새로운 웹훅 URL 사용:**
```
https://abc123.ngrok.io/webhook
```

**알림 메시지 (동일):**
```json
{
  "alert_name": "donchian_buy",
  "symbol": "KRW-BTC",
  "passphrase": "MyTradingBot2024"
}
```

## 🔧 관리 명령어

### 일상 관리
```bash
# 상태 확인
docker-compose ps
curl http://localhost:4040/api/tunnels

# 로그 확인  
docker-compose logs -f kelly-trading
tail -f ngrok.log

# 재시작
./restart_kelly_bot.sh

# 중지
./stop_kelly_bot.sh
```

### URL 확인
```bash
# 현재 웹훅 URL 확인
cat current_webhook_url.txt

# ngrok 웹 인터페이스
curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('🌐 웹훅 URL:', data['tunnels'][0]['public_url'] + '/webhook')
"
```

## 🚨 중요한 차이점

### 로컬 vs AWS
| 항목 | 로컬 PC | AWS |
|------|---------|-----|
| **가동시간** | PC 켜져있을 때만 | 24시간 무중단 |
| **안정성** | PC 재부팅 시 중단 | 자동 재시작 |
| **전력비용** | 24시간 PC 전력 | AWS 프리티어 |
| **URL 변경** | ngrok 재시작 시 | 시스템 재시작 시 |

### ngrok URL 관리
```bash
# URL 변경 시 자동 알림 (선택사항)
echo "새 웹훅 URL: $(cat current_webhook_url.txt)" | \
  curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Kelly Bot URL 변경됨"}' \
  YOUR_SLACK_WEBHOOK_URL
```

## 🎯 Pro Tips

### 1. ngrok Pro 계정 (권장)
- 고정 도메인: `https://yourname.ngrok.io`
- URL 변경 없음
- 더 많은 연결 허용

### 2. 자동 재시작 설정
```bash
# 시스템 부팅 시 자동 시작
sudo systemctl enable kelly-trading-bot
sudo systemctl start kelly-trading-bot
```

### 3. 모니터링 스크립트
```bash
# URL 변경 감지 스크립트
cat > monitor_url.sh << 'EOF'
#!/bin/bash
OLD_URL=$(cat current_webhook_url.txt 2>/dev/null)
NEW_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['tunnels'][0]['public_url'] + '/webhook')
except:
    pass
")

if [ "$OLD_URL" != "$NEW_URL" ] && [ ! -z "$NEW_URL" ]; then
    echo $NEW_URL > current_webhook_url.txt
    echo "🚨 웹훅 URL 변경됨: $NEW_URL"
    # 여기에 알림 로직 추가 가능
fi
EOF

# 5분마다 실행 (crontab)
*/5 * * * * /home/ubuntu/kelly-trading-bot/monitor_url.sh
```

## 🎊 결론

**AWS + ngrok 방식의 장점:**
1. ✅ **TradingView 완벽 호환** (포트 제한 해결)
2. ✅ **24시간 무중단 운영** (로컬 PC 불필요)
3. ✅ **자동 재시작** (시스템 장애 시 복구)
4. ✅ **프로페셔널** (기업급 안정성)

**이제 진정한 24시간 자동 Kelly Trading 시스템이 완성됩니다!** 🚀