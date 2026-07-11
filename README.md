# KTOJ — 온라인 저지 (학습용)

Python 코드를 제출하면 Docker 격리 환경에서 채점하는 미니 온라인 저지.

## 요구 사항
- Python 3.11+
- Docker Desktop (실행 중이어야 함)

## 준비
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
docker build -t ktoj-python:latest -f docker/Dockerfile.python docker
python seed.py
```

## 실행 (터미널 2개)
```
# 터미널 1 — 웹
python run_web.py         # http://127.0.0.1:8000

# 터미널 2 — 채점 워커
python run_worker.py
```

## 테스트
```
pytest -v
```
