# KTOJ — 온라인 저지 (학습용)

Python 코드를 제출하면 Docker 격리 환경에서 채점하는 미니 온라인 저지.

## 요구 사항
- Python 3.11+
- Docker Desktop (실행 중이어야 함)

## 준비
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
docker build -t ktoj-python:latest -f docker/Dockerfile.python docker
python seed.py
```

> venv 활성화가 실행정책(ExecutionPolicy)에 막히거나 `python`이 다른 환경을
> 가리키면, 활성화 없이 프로젝트 venv 파이썬을 직접 부르세요:
> `.\.venv\Scripts\python.exe <스크립트>`

## 실행 (터미널 1개)
```powershell
python run_web.py         # http://127.0.0.1:8000
```
웹 서버와 채점 워커가 한 프로세스에서 함께 돕니다(채점 워커는 데몬 스레드).
`INFO: Uvicorn running on http://127.0.0.1:8000` 이 뜨면 브라우저로 접속하세요.

### (선택) 채점 워커를 별도 프로세스로 분리
실제 온라인 저지처럼 웹과 채점을 분리하고 싶으면, 인프로세스 워커를 끄고
워커를 따로 실행합니다:
```powershell
# 터미널 1 — 웹 (인프로세스 워커 비활성화)
$env:KTOJ_INPROCESS_WORKER = "0"; python run_web.py

# 터미널 2 — 채점 워커
python run_worker.py
```

## 테스트
```powershell
pytest -v
```
Docker가 실행 중이면 채점 통합 테스트까지 전부 돌고, 없으면 해당 테스트는
자동으로 skip 됩니다.

## 라이선스
[MIT](LICENSE)
