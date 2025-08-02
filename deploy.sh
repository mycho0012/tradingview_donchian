#!/bin/bash

# Kelly Trading Bot 배포 스크립트
echo "🚀 Kelly Trading Bot AWS 배포 시작..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 단계 1: 환경 체크
echo -e "${YELLOW}📋 Step 1: 환경 체크${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker가 설치되어 있지 않습니다.${NC}"
    echo "설치 명령어: sudo apt install docker.io docker-compose"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose가 설치되어 있지 않습니다.${NC}"
    echo "설치 명령어: sudo apt install docker-compose"
    exit 1
fi

echo -e "${GREEN}✅ Docker 환경 준비 완료${NC}"

# 단계 2: .env 파일 확인
echo -e "${YELLOW}📋 Step 2: .env 파일 확인${NC}"
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env 파일이 없습니다!${NC}"
    echo "다음 내용으로 .env 파일을 생성하세요:"
    echo ""
    echo "UPBIT_ACCESS_KEY=your_access_key"
    echo "UPBIT_SECRET_KEY=your_secret_key"
    echo "PASSPHRASE=MyTradingBot2024"
    echo ""
    read -p "Enter를 눌러 계속하거나 Ctrl+C로 종료하세요..."
    exit 1
fi

echo -e "${GREEN}✅ .env 파일 존재 확인${NC}"

# 단계 3: 로그 디렉토리 생성
echo -e "${YELLOW}📋 Step 3: 로그 디렉토리 생성${NC}"
mkdir -p logs
echo -e "${GREEN}✅ logs 디렉토리 생성 완료${NC}"

# 단계 4: 기존 컨테이너 정리
echo -e "${YELLOW}📋 Step 4: 기존 컨테이너 정리${NC}"
sudo docker-compose down 2>/dev/null || true
echo -e "${GREEN}✅ 기존 컨테이너 정리 완료${NC}"

# 단계 5: 이미지 빌드
echo -e "${YELLOW}📋 Step 5: Docker 이미지 빌드${NC}"
sudo docker-compose build
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker 이미지 빌드 실패${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker 이미지 빌드 완료${NC}"

# 단계 6: 컨테이너 시작
echo -e "${YELLOW}📋 Step 6: 컨테이너 시작${NC}"
sudo docker-compose up -d
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 컨테이너 시작 실패${NC}"
    exit 1
fi

sleep 5

# 단계 7: 헬스체크
echo -e "${YELLOW}📋 Step 7: 헬스체크${NC}"
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ || echo "000")
if [ "$response" = "200" ]; then
    echo -e "${GREEN}✅ Kelly Trading Bot 정상 작동 중!${NC}"
else
    echo -e "${RED}❌ 헬스체크 실패 (HTTP: $response)${NC}"
    echo "로그를 확인하세요: sudo docker-compose logs kelly-trading"
    exit 1
fi

# 단계 8: 상태 확인
echo -e "${YELLOW}📋 Step 8: 최종 상태 확인${NC}"
sudo docker-compose ps

echo ""
echo -e "${GREEN}🎉 Kelly Trading Bot 배포 성공!${NC}"
echo ""
echo -e "${YELLOW}📊 유용한 명령어:${NC}"
echo "• 로그 확인: sudo docker-compose logs -f kelly-trading"
echo "• 상태 확인: sudo docker-compose ps"
echo "• 재시작: sudo docker-compose restart"
echo "• 중지: sudo docker-compose down"
echo "• 업데이트: git pull && sudo docker-compose up -d --build"
echo ""
echo -e "${YELLOW}🌐 접속 정보:${NC}"
echo "• 로컬 서버: http://localhost:8000"
echo "• 서버 공개 주소 설정 후 ngrok 대신 직접 사용 가능"
echo ""
echo -e "${GREEN}🚀 24시간 자동 운영 시작!${NC}"