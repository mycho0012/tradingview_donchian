# 🚀 Kelly Trading Bot AWS 배포 가이드

## 📋 사전 준비사항

### 1. AWS EC2 인스턴스 설정
- **인스턴스 타입**: t3.micro (프리티어) 또는 t3.small
- **OS**: Ubuntu 22.04 LTS
- **보안 그룹**: 포트 8000, 22 (SSH) 오픈
- **키페어**: SSH 접속용 .pem 파일

### 2. 로컬에서 GitHub 업로드

```bash
# 1. GitHub 저장소 생성 (웹에서)
# 2. 로컬에서 업로드
git init
git add .
git commit -m "Initial Kelly Trading Bot"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/kelly-trading-bot.git
git push -u origin main
```

## 🛠️ AWS Ubuntu 설정

### Step 1: EC2 접속 및 기본 설정

```bash
# SSH 접속
ssh -i your-key.pem ubuntu@your-ec2-ip

# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 필수 패키지 설치
sudo apt install -y git curl wget htop
```

### Step 2: Docker 설치

```bash
# Docker 설치
sudo apt install -y docker.io docker-compose

# Docker 서비스 시작
sudo systemctl start docker
sudo systemctl enable docker

# 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER

# 새 세션 시작 (또는 로그아웃 후 재로그인)
newgrp docker

# Docker 설치 확인
docker --version
docker-compose --version
```

### Step 3: 코드 다운로드

```bash
# GitHub에서 코드 클론
git clone https://github.com/YOUR_USERNAME/kelly-trading-bot.git
cd kelly-trading-bot

# 실행 권한 부여
chmod +x deploy.sh
```

### Step 4: 환경 설정

```bash
# .env 파일 생성
nano .env
```

다음 내용 입력:
```
UPBIT_ACCESS_KEY=your_actual_access_key
UPBIT_SECRET_KEY=your_actual_secret_key
PASSPHRASE=MyTradingBot2024
```

### Step 5: 배포 실행

```bash
# 한 번에 배포
./deploy.sh
```

## 🌐 웹훅 URL 설정

### 옵션 1: AWS 고정 IP 사용 (추천)

```
http://YOUR_EC2_PUBLIC_IP:8000/webhook
```

**장점**: 
- URL 변경 없음
- ngrok 불필요
- 완전 무료

**보안 그룹 설정**:
- 포트 8000: 0.0.0.0/0 (또는 TradingView IP만)

### 옵션 2: ngrok 사용 (선택사항)

```bash
# ngrok 설치
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin

# ngrok 인증 (웹에서 토큰 복사)
ngrok config add-authtoken YOUR_AUTH_TOKEN

# 터널 시작
ngrok http 8000
```

## 📊 모니터링 및 관리

### 상태 확인

```bash
# 컨테이너 상태
docker-compose ps

# 실시간 로그
docker-compose logs -f kelly-trading

# 시스템 리소스
htop
```

### 일반적인 명령어

```bash
# 재시작
docker-compose restart

# 중지
docker-compose down

# 업데이트 배포
git pull
docker-compose up -d --build

# 로그 확인
docker-compose logs --tail=100 kelly-trading
```

## 🔧 트러블슈팅

### 1. 포트 8000 접속 안됨
```bash
# 방화벽 확인
sudo ufw status
sudo ufw allow 8000

# 컨테이너 상태 확인
docker-compose ps
```

### 2. 메모리 부족
```bash
# 메모리 사용량 확인
free -h

# 불필요한 Docker 이미지 정리
docker system prune -a
```

### 3. 자동 재시작 안됨
```bash
# Docker 서비스 재시작
sudo systemctl restart docker

# 컨테이너 재시작 정책 확인
docker inspect kelly-trading-bot | grep -i restart
```

## 🚨 보안 권장사항

### 1. 보안 그룹 설정
- SSH (22): 본인 IP만
- HTTP (8000): 필요한 IP만 (TradingView 또는 전체)

### 2. 환경 변수 보안
```bash
# .env 파일 권한 설정
chmod 600 .env

# 소유자만 읽기 가능하도록
ls -la .env
```

### 3. 정기 업데이트
```bash
# 시스템 업데이트 자동화
sudo apt install unattended-upgrades
```

## 📈 성능 최적화

### 1. 로그 로테이션
```bash
# logrotate 설정
sudo nano /etc/logrotate.d/docker-kelly
```

### 2. 모니터링 설정
```bash
# 시스템 모니터링
sudo apt install prometheus-node-exporter
```

## 🎊 완료!

✅ Kelly Trading Bot이 AWS에서 24시간 실행됩니다!
✅ 자동 재시작, 로그 관리, 헬스체크 모두 설정 완료
✅ 웹훅 URL: `http://YOUR_EC2_IP:8000/webhook`

**TradingView에서 이 URL로 알림을 설정하세요!**