# 🚀 Kelly Trading Bot

**TradingView Donchian 전략을 위한 동적 Kelly Fraction 기반 자동 거래봇**

## ✨ 핵심 기능

### 🧮 동적 Kelly Fraction 시스템
- **변동성 적응형**: BTC 30일 변동성에 따른 자동 포지션 사이징
- **구간별 Kelly**: 저변동성(40%) → 고변동성(15%) 자동 조정
- **리스크 관리**: 15%-100% 범위 내 안전한 거래

### 📊 TradingView 통합
- **Donchian Breakout**: 브레이크아웃 매수/매도 신호 처리
- **웹훅 지원**: 실시간 알림 → 자동 거래 실행
- **스마트 포지션**: 중복 매수 방지, 전량 매도 로직

### 💰 Upbit 연동
- **실시간 거래**: 시장가 매수/매도 자동 실행
- **잔고 관리**: 실시간 KRW/BTC 잔고 확인
- **거래 검증**: UUID 기반 거래 완료 확인

## 🏗️ 시스템 아키텍처

```
TradingView Alert → 웹훅 → Kelly Trading Bot → Upbit API
                                     ↓
            동적 Kelly 계산 ← BTC 변동성 분석
```

## 🐳 Docker 배포

### 로컬 테스트
```bash
# Docker 빌드 및 실행
docker-compose up -d

# 상태 확인
docker-compose ps
docker-compose logs -f kelly-trading
```

### AWS 배포 (추천)
```bash
# EC2 Ubuntu에서 실행
git clone https://github.com/your-username/kelly-trading-bot.git
cd kelly-trading-bot

# 환경 설정
nano .env

# 자동 배포 (Docker + ngrok)
chmod +x aws_ngrok_setup.sh
./aws_ngrok_setup.sh

# 봇 시작
./start_kelly_bot.sh
```

## ⚙️ 환경 설정

### .env 파일 생성
```env
UPBIT_ACCESS_KEY=your_upbit_access_key
UPBIT_SECRET_KEY=your_upbit_secret_key
PASSPHRASE=MyTradingBot2024
```

### TradingView 웹훅 설정
**웹훅 URL**: `https://your-ngrok-url.ngrok.io/webhook`

**매수 알림 메시지**:
```json
{
  "alert_name": "donchian_buy",
  "symbol": "KRW-BTC",
  "passphrase": "MyTradingBot2024"
}
```

**매도 알림 메시지**:
```json
{
  "alert_name": "donchian_exit",
  "symbol": "KRW-BTC",
  "passphrase": "MyTradingBot2024"
}
```

## 📈 Kelly Fraction 동작 원리

### 변동성 기반 구간 분류
| BTC 변동성 | Kelly 비율 | 투자 성향 |
|-----------|-----------|----------|
| ≤ 1% | 40% | 저변동성(공격적) |
| 1-2% | 30% | 보통변동성(균형) |
| 2-3% | 20% | 중변동성(보수적) |
| ≥ 3% | 15% | 고변동성(안전) |

### 실시간 계산 예시
```
📊 BTC 30일 변동성: 1.14%
🎯 변동성 구간: 보통변동성(균형)
✅ 최종 Kelly: 30.0%
💰 거래 금액: 17,063원 (잔고의 30%)
```

## 🛡️ 보안 및 안전장치

### API 보안
- **환경변수**: API 키는 .env 파일로 분리
- **패스프레이즈**: 웹훅 요청 검증
- **IP 화이트리스트**: Upbit IP 등록 필수

### 거래 안전장치
- **중복 매수 방지**: 기존 포지션 확인
- **최소 거래 금액**: 5,000원 이상
- **잔고 초과 방지**: 사용 가능 금액 내 거래
- **오류 처리**: 상세한 로깅 및 예외 처리

## 📊 모니터링

### 실시간 로그
```bash
# Docker 로그 확인
docker-compose logs -f kelly-trading

# 웹훅 URL 확인
cat current_webhook_url.txt

# 시스템 상태
curl http://localhost:8000/health
```

### 거래 내역
모든 거래는 UUID와 함께 로그에 기록됩니다:
```
INFO:__main__:Upbit 매수 주문 완료: KRW-BTC, 금액: 17063.089996296 KRW
UUID: c85fdda8-29a7-4029-a341-63e78e72ee54
```

## 🚨 주의사항

### Upbit 설정
1. **API 키 발급**: 거래 권한 포함
2. **IP 등록**: API 사용 전 필수
3. **2FA 설정**: 보안 강화

### TradingView 설정
1. **Donchian 전략**: 24주기, Long-Only
2. **알림 빈도**: Once Per Bar Close
3. **웹훅 URL**: ngrok 주소 사용

## 📚 추가 문서

- [AWS 배포 가이드](./README_AWS_DEPLOY.md)
- [ngrok 설정 가이드](./aws_ngrok_deploy_guide.md)
- [Docker 설정](./docker-compose.yml)

## 🤝 기여

이슈나 개선사항이 있으시면 GitHub Issues를 통해 알려주세요.

## 📄 라이선스

MIT License

---

**⚠️ 투자 위험 고지**: 이 봇은 교육 및 연구 목적으로 제작되었습니다. 실제 투자 시 발생하는 손실에 대한 책임은 사용자에게 있습니다.