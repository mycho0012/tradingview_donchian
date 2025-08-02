from fastapi import FastAPI, Request, HTTPException
import pyupbit
import uvicorn
import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from pathlib import Path

# 로깅 설정 (먼저 설정)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# .env 파일 자동 로딩
def load_env_file(env_file: str = ".env"):
    """환경변수 파일을 로드"""
    env_path = Path(env_file)
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value
        logger.info(f"✅ {env_file} 파일 로딩 완료")
    else:
        logger.warning(f"⚠️  {env_file} 파일을 찾을 수 없습니다.")

# .env 파일 로딩 (main.py와 같은 디렉토리에서)
load_env_file(".env")

# --- 설정 (Configuration) ---
# Upbit 설정 (환경 변수에서 API 키 로드)
UPBIT_ACCESS_KEY = os.getenv('UPBIT_ACCESS_KEY')
UPBIT_SECRET_KEY = os.getenv('UPBIT_SECRET_KEY')

# 보안 설정
MY_SECRET_PASSPHRASE = os.getenv('PASSPHRASE', "YourSuperSecretPassword")

app = FastAPI(title="TradingView to Upbit Webhook", version="1.0.0")

# Upbit 클라이언트 초기화
upbit = None
if UPBIT_ACCESS_KEY and UPBIT_SECRET_KEY:
    upbit = pyupbit.Upbit(UPBIT_ACCESS_KEY, UPBIT_SECRET_KEY)
    logger.info("Upbit 클라이언트 초기화 완료")
else:
    logger.warning("Upbit API 키가 설정되지 않았습니다.")

# --- 포트폴리오 관리 함수 ---
def get_current_balance(currency: str = "KRW") -> float:
    """현재 잔고 조회"""
    if not upbit:
        return 0.0
    
    try:
        balances = upbit.get_balances()
        for balance in balances:
            if balance['currency'] == currency:
                return float(balance['balance'])
        return 0.0
    except Exception as e:
        logger.error(f"잔고 조회 오류: {e}")
        return 0.0

def get_current_position(symbol: str) -> float:
    """현재 포지션 수량 조회 (예: BTC 보유 수량)"""
    if not upbit:
        return 0.0
    
    # KRW-BTC에서 BTC 추출
    currency = symbol.split('-')[1]
    
    try:
        balances = upbit.get_balances()
        for balance in balances:
            if balance['currency'] == currency:
                return float(balance['balance'])
        return 0.0
    except Exception as e:
        logger.error(f"포지션 조회 오류: {e}")
        return 0.0

# --- Kelly Fraction 정교한 계산 시스템 ---
def get_historical_candles(symbol: str, interval: str = "day", count: int = 200) -> pd.DataFrame:
    """Upbit에서 과거 캔들 데이터 가져오기 (일봉)"""
    try:
        # 일봉 데이터 가져오기 (200개)
        df = pyupbit.get_ohlcv(symbol, interval=interval, count=count)
        if df is None or df.empty:
            logger.error(f"캔들 데이터 조회 실패: {symbol}")
            return pd.DataFrame()
        
        logger.info(f"📊 {symbol} 일봉 캔들 {len(df)}개 조회 완료")
        return df
    except Exception as e:
        logger.error(f"캔들 데이터 조회 오류: {e}")
        return pd.DataFrame()

def calculate_donchian_signals(df: pd.DataFrame, period: int = 24) -> pd.DataFrame:
    """Donchian Breakout 신호 계산"""
    if df.empty:
        return df
    
    # Donchian Channel 계산
    df['donchian_high'] = df['high'].rolling(window=period).max()
    df['donchian_low'] = df['low'].rolling(window=period).min()
    
    # 매수/매도 신호 생성
    df['buy_signal'] = (df['close'] > df['donchian_high'].shift(1))
    df['sell_signal'] = (df['close'] < df['donchian_low'].shift(1))
    
    # 디버깅: Donchian 채널 정보
    logger.info(f"🔍 Donchian 채널 ({period}일):")
    logger.info(f"   최고가 범위: {df['donchian_high'].min():,.0f} ~ {df['donchian_high'].max():,.0f}")
    logger.info(f"   최저가 범위: {df['donchian_low'].min():,.0f} ~ {df['donchian_low'].max():,.0f}")
    logger.info(f"   현재가 범위: {df['close'].min():,.0f} ~ {df['close'].max():,.0f}")
    
    return df

def simulate_donchian_strategy(df: pd.DataFrame) -> Tuple[List[float], float, float, float]:
    """Donchian 전략 백테스팅 및 성과 분석"""
    if df.empty:
        return [], 0.0, 0.0, 0.0
    
    trades = []
    position = 0.0  # 0: 노포지션, 1: 롱포지션
    entry_price = 0.0
    
    # 디버깅: 신호 개수 확인
    buy_signals = df['buy_signal'].sum()
    sell_signals = df['sell_signal'].sum()
    logger.info(f"🔍 디버깅: 매수 신호 {buy_signals}개, 매도 신호 {sell_signals}개")
    
    for i in range(1, len(df)):
        current_price = df.iloc[i]['close']
        
        # 매수 신호
        if df.iloc[i]['buy_signal'] and position == 0.0:
            position = 1.0
            entry_price = current_price
            logger.info(f"📈 매수 신호: {current_price:,.0f}원")
        
        # 매도 신호 (Long Only)
        elif df.iloc[i]['sell_signal'] and position == 1.0:
            exit_price = current_price
            return_pct = (exit_price - entry_price) / entry_price
            trades.append(return_pct)
            position = 0.0
            logger.info(f"📉 매도 신호: {exit_price:,.0f}원, 수익률: {return_pct:.2%}")
    
    logger.info(f"🎯 백테스팅 완료: {len(trades)}개 거래 감지")
    
    if not trades:
        return [], 0.0, 0.0, 0.0
    
    # 성과 분석
    win_trades = [t for t in trades if t > 0]
    lose_trades = [t for t in trades if t <= 0]
    
    win_rate = len(win_trades) / len(trades) if trades else 0.0
    avg_win = np.mean(win_trades) if win_trades else 0.0
    avg_loss = abs(np.mean(lose_trades)) if lose_trades else 0.0
    
    return trades, win_rate, avg_win, avg_loss

def calculate_dynamic_kelly_fraction(symbol: str, available_krw: float) -> Tuple[float, Dict[str, Any]]:
    """동적 Kelly Fraction 계산 (변동성 적응형)"""
    try:
        logger.info("🚀 동적 Kelly Fraction 계산 시작")
        
        # 1. BTC 변동성 계산 (30일)
        df = get_historical_candles(symbol, interval="day", count=30)
        
        if not df.empty:
            daily_returns = df['close'].pct_change().dropna()
            volatility = daily_returns.std()
            logger.info(f"📊 BTC 30일 변동성: {volatility:.2%}")
        else:
            volatility = 0.02  # 기본값 2%
            logger.warning("변동성 계산 실패, 기본값 2% 사용")
        
        # 2. 동적 Kelly 계산 방법들
        
        # 방법 1: 변동성 역비례 Kelly
        # 변동성이 낮으면 더 공격적, 높으면 더 보수적
        base_kelly = 0.25  # 기본 25%
        volatility_adjusted_kelly = base_kelly * (0.02 / max(volatility, 0.005))  # 2% 기준 정규화
        volatility_kelly = max(0.10, min(volatility_adjusted_kelly, 0.50))  # 10%-50% 제한
        
        # 방법 2: 고정 비율 (안전한 25%)
        fixed_kelly = 0.25
        
        # 방법 3: 공격적 Kelly (50% - 브레이크아웃 전용)
        aggressive_kelly = 0.50
        
        # 방법 4: 변동성 구간별 Kelly
        if volatility <= 0.01:    # 1% 이하: 저변동성
            tier_kelly = 0.40
            tier_name = "저변동성(공격적)"
        elif volatility <= 0.02:  # 1-2%: 보통변동성  
            tier_kelly = 0.30
            tier_name = "보통변동성(균형)"
        elif volatility <= 0.03:  # 2-3%: 중변동성
            tier_kelly = 0.20
            tier_name = "중변동성(보수적)"
        else:                     # 3% 이상: 고변동성
            tier_kelly = 0.15
            tier_name = "고변동성(안전)"
        
        # 5. 최종 Kelly 선택 (변동성 구간별 추천)
        kelly_fraction = tier_kelly
        method_name = f"구간별_Kelly_{tier_name}"
        
        logger.info(f"💡 동적 Kelly 분석:")
        logger.info(f"   🎯 변동성 구간: {tier_name}")
        logger.info(f"   ⚖️ 변동성 역비례: {volatility_kelly:.1%}")
        logger.info(f"   🛡️ 고정 안전: {fixed_kelly:.1%}")
        logger.info(f"   💪 공격적: {aggressive_kelly:.1%}")
        logger.info(f"   ✅ 최종 선택: {kelly_fraction:.1%}")
        
        # 6. 최종 범위 제한 (10%-50%)
        kelly_fraction = max(0.10, min(kelly_fraction, 0.50))
        
        # 7. 실제 거래 금액 계산
        kelly_amount = available_krw * kelly_fraction
        final_amount = max(kelly_amount, 5000)  # 최소 5천원
        final_amount = min(final_amount, available_krw)  # 잔고 초과 방지
        
        stats = {
            "method": method_name,
            "volatility": volatility,
            "volatility_kelly": volatility_kelly,
            "fixed_kelly": fixed_kelly,
            "aggressive_kelly": aggressive_kelly,
            "tier_kelly": tier_kelly,
            "tier_name": tier_name,
            "kelly_fraction": kelly_fraction,
            "kelly_amount": kelly_amount,
            "final_amount": final_amount,
            "available_krw": available_krw,
            "min_threshold": 0.10,
            "max_threshold": 0.50
        }
        
        logger.info(f"🚀 동적 Kelly 계산 완료:")
        logger.info(f"   📊 변동성: {volatility:.2%}")
        logger.info(f"   🎯 선택된 구간: {tier_name}")
        logger.info(f"   ✅ 최종 Kelly: {kelly_fraction:.1%}")
        logger.info(f"   💰 거래 금액: {final_amount:,.0f}원")
        
        return final_amount, stats
        
    except Exception as e:
        logger.error(f"동적 Kelly 계산 오류: {e}")
        # 오류 시 안전한 기본값 (25%)
        safe_amount = max(available_krw * 0.25, 5000)
        return safe_amount, {"method": "error", "kelly_fraction": 0.25}

def calculate_sell_quantity(symbol: str) -> float:
    """매도할 전체 수량 계산"""
    return get_current_position(symbol)

# --- Upbit 주문 처리 함수 ---
def place_upbit_order(symbol: str, side: str, quantity: float, order_type: str = "market") -> Dict[str, Any]:
    """
    Upbit 주문을 처리하는 함수
    
    Args:
        symbol: 마켓 심볼 (예: KRW-BTC)
        side: 매수/매도 ("buy" or "sell")
        quantity: 주문 수량/금액
        order_type: 주문 타입 (기본값: "market")
    
    Returns:
        주문 결과 딕셔너리
    """
    if not upbit:
        raise Exception("Upbit 클라이언트가 초기화되지 않았습니다.")
    
    try:
        if side.lower() == 'buy':
            # 시장가 매수: quantity는 주문 총액(KRW)
            result = upbit.buy_market_order(symbol, quantity)
            logger.info(f"Upbit 매수 주문 완료: {symbol}, 금액: {quantity} KRW")
        elif side.lower() == 'sell':
            # 시장가 매도: quantity는 코인 수량
            result = upbit.sell_market_order(symbol, quantity)
            logger.info(f"Upbit 매도 주문 완료: {symbol}, 수량: {quantity}")
        else:
            raise ValueError(f"지원하지 않는 주문 방향: {side}")
        
        return result
    except Exception as e:
        logger.error(f"Upbit 주문 오류: {e}")
        raise

def validate_upbit_symbol(symbol: str) -> bool:
    """
    Upbit 심볼 형식 검증
    """
    if not symbol or '-' not in symbol:
        return False
    
    parts = symbol.split('-')
    if len(parts) != 2:
        return False
    
    market, coin = parts
    return market in ['KRW', 'BTC', 'USDT'] and len(coin) > 0

# --- 헬스체크 엔드포인트 ---
@app.get("/")
async def root():
    return {
        "message": "TradingView to Upbit Webhook Server",
        "status": "running",
        "upbit_connected": upbit is not None
    }

@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    try:
        if upbit:
            # Upbit 연결 상태 확인
            balances = upbit.get_balances()
            return {
                "status": "healthy",
                "upbit_connected": True,
                "balance_count": len(balances) if balances else 0
            }
        else:
            return {
                "status": "warning",
                "upbit_connected": False,
                "message": "Upbit API 키가 설정되지 않았습니다."
            }
    except Exception as e:
        return {
            "status": "error",
            "upbit_connected": False,
            "error": str(e)
        }

# --- 웹훅 엔드포인트 ---
@app.post("/webhook")
async def tradingview_webhook(request: Request):
    """
    TradingView 웹훅을 받아 Upbit 주문을 처리하는 엔드포인트
    
    기본 형식:
    {
        "symbol": "KRW-BTC",
        "side": "buy",
        "quantity": "10000",
        "passphrase": "YOUR_SECRET_PASSPHRASE"
    }
    
    고급 알림 형식:
    {
        "alert_name": "donchian_buy" or "donchian_exit",
        "symbol": "KRW-BTC",
        "passphrase": "YOUR_SECRET_PASSPHRASE"
    }
    """
    try:
        data = await request.json()
        logger.info(f"웹훅 요청 수신: {data}")
        
        # 패스프레이즈 검증
        if data.get("passphrase") != MY_SECRET_PASSPHRASE:
            client_host = getattr(request.client, 'host', 'unknown') if request.client else 'unknown'
            logger.warning(f"잘못된 패스프레이즈 시도: {client_host}")
            raise HTTPException(status_code=401, detail="Invalid passphrase")
        
        # 알림 이름 기반 고급 거래 로직
        alert_name = data.get("alert_name", "").lower()
        symbol = data.get("symbol")
        
        # 심볼 검증
        if not symbol or not validate_upbit_symbol(symbol):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid symbol format: {symbol}. Expected format: KRW-BTC, BTC-ETH, etc."
            )
        
        if alert_name == "donchian_buy":
            # Donchian Breakout 매수 로직
            logger.info(f"🚀 Donchian Buy 신호 수신: {symbol}")
            
            # 현재 포지션 확인
            current_position = get_current_position(symbol)
            if current_position > 0:
                logger.info(f"⚠️ 기존 포지션 존재 ({current_position:.8f}), 매수 스킵")
                return {
                    "status": "skipped",
                    "reason": "existing_position",
                    "symbol": symbol,
                    "current_position": current_position
                }
            
            # Available KRW 조회
            available_krw = get_current_balance("KRW")
            if available_krw < 5000:  # 최소 거래 금액
                raise HTTPException(status_code=400, detail=f"Insufficient KRW balance: {available_krw}")
            
            # 동적 Kelly Fraction 계산
            logger.info(f"📊 Kelly Fraction 계산 시작 (잔고: {available_krw:,.0f}원)")
            kelly_amount, kelly_stats = calculate_dynamic_kelly_fraction(symbol, available_krw)
            
            logger.info(f"💰 최적 Kelly 매수: {kelly_amount:,.0f}원")
            
            # 매수 실행
            trade_details = place_upbit_order(symbol, "buy", kelly_amount, "market")
            
            return {
                "status": "success",
                "strategy": "donchian_buy",
                "symbol": symbol,
                "side": "buy",
                "quantity": kelly_amount,
                "kelly_stats": kelly_stats,
                "details": trade_details
            }
            
        elif alert_name == "donchian_exit":
            # Donchian Exit 매도 로직
            logger.info(f"📤 Donchian Exit 신호 수신: {symbol}")
            
            # 현재 포지션 확인
            current_position = get_current_position(symbol)
            if current_position <= 0:
                logger.info(f"⚠️ 매도할 포지션 없음")
                return {
                    "status": "skipped",
                    "reason": "no_position",
                    "symbol": symbol,
                    "current_position": current_position
                }
            
            logger.info(f"💸 전량 매도: {current_position:.8f} {symbol.split('-')[1]}")
            
            # 전량 매도 실행
            trade_details = place_upbit_order(symbol, "sell", current_position, "market")
            
            return {
                "status": "success",
                "strategy": "donchian_exit",
                "symbol": symbol,
                "side": "sell",
                "quantity": current_position,
                "details": trade_details
            }
            
        else:
            # 기존 수동 거래 로직 (호환성 유지)
            required_fields = ["symbol", "side", "quantity"]
            for field in required_fields:
                if field not in data:
                    raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
            
            side = data.get("side")
            quantity = float(data.get("quantity"))
            
            if quantity <= 0:
                raise HTTPException(status_code=400, detail="Quantity must be positive")
            
            # 기존 주문 처리
            trade_details = place_upbit_order(symbol, side, quantity, "market")
            
            return {
                "status": "success",
                "exchange": "upbit",
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "details": trade_details
            }
    
    except HTTPException:
        # HTTPException은 FastAPI에서 자동 처리되므로 그대로 다시 발생
        raise
    
    except ValueError as e:
        logger.error(f"데이터 형식 오류: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid data format: {str(e)}")
    
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# --- 잔고 조회 엔드포인트 (디버깅용) ---
@app.get("/balances")
async def get_balances():
    """현재 잔고 조회 (디버깅용)"""
    if not upbit:
        raise HTTPException(status_code=500, detail="Upbit 클라이언트가 초기화되지 않았습니다.")
    
    try:
        balances = upbit.get_balances()
        return {"balances": balances}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"잔고 조회 오류: {str(e)}")

# 서버 실행
if __name__ == "__main__":
    if not UPBIT_ACCESS_KEY or not UPBIT_SECRET_KEY:
        logger.warning("경고: Upbit API 키가 설정되지 않았습니다.")
        logger.info("환경변수 UPBIT_ACCESS_KEY와 UPBIT_SECRET_KEY를 설정해주세요.")
    
    port = int(os.getenv('PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)