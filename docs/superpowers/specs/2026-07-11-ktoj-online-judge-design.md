# KTOJ — 온라인 저지 (설계 문서)

- 작성일: 2026-07-11
- 목적: 학습/포트폴리오. 온라인 저지가 실제로 어떻게 동작하는지 끝까지 만들어보기. 배포·대규모 확장은 이후 고려.
- 개발 환경: Windows 11 + Docker Desktop(WSL2 백엔드)

## 1. 범위 (MVP)

**포함**
- 문제 목록 / 문제 상세 보기 (지문, 제약, 샘플 입출력)
- 코드 제출 (언어 선택 — MVP는 Python 하나)
- Docker 격리 환경에서 채점 → 판정(AC/WA/TLE/MLE/RE/CE/IE) + 실행시간/메모리
- 제출 기록 목록 / 제출 상세(결과) 페이지
- 문제는 파일로 미리 시딩 (관리자 UI 없음)

**제외 (이후 확장)**
- 회원가입/로그인 (MVP는 인증 없는 단일 사용자)
- 문제 등록 관리자 UI (파일/DB 직접 관리로 대체)
- 랭킹, 대회(콘테스트)
- 다중 언어 (어댑터 구조만 잡아두고 Python으로 시작)

**난이도 범위**
- 왕초보 ~ 초보. 약 30줄 내외로 풀 수 있는 수준까지만.
- 순수 stdin → stdout 문제만. 복잡한 알고리즘 문제는 다루지 않음.

## 2. 기술 스택

- 백엔드: Python + FastAPI
- 프론트엔드: 서버 렌더링 (Jinja2 템플릿 + HTMX로 제출 상태 자동 갱신)
- DB: SQLite (SQLAlchemy 사용 — 이후 PostgreSQL 교체 대비)
- 격리/채점: Docker 컨테이너 (제출마다 격리 실행)

## 3. 아키텍처 개요

두 개의 독립 프로세스 + 공유 DB.

```
┌─────────────────┐   write    ┌──────────────┐   poll    ┌─────────────────┐
│  Web (FastAPI)  │──────────▶ │   Database   │ ◀──────── │  Judge Worker   │
│  + Jinja/HTMX   │ submission │  (SQLite)    │  update   │  (별도 프로세스)  │
│  문제/제출 화면   │ = PENDING  │ submissions  │  = 결과   │ Docker로 코드 실행 │
└─────────────────┘            └──────────────┘           └─────────────────┘
        ▲                                                          │
        │ HTMX 폴링으로 상태 갱신 (PENDING→JUDGING→AC/WA…)            │ docker run (격리)
        └──────────────────────────────────────────────────────────┘
```

- **Web 프로세스**: 화면 렌더링 + 제출 접수. 제출을 받으면 DB에 `PENDING`으로 저장만 하고 즉시 응답(비블로킹).
- **Judge Worker 프로세스**: DB에서 `PENDING` 제출을 폴링해 하나씩 채점 → 결과 기록. 워커가 다운돼도 Web은 계속 동작.
- **채점 실행 방식**: 백그라운드 워커 + DB 큐 (선택된 방식 B). 추가 인프라(Redis 등) 없이 DB만으로 큐 구현. 이후 큐 부분만 Celery/Redis로 교체 가능.

## 4. 컴포넌트 (각각 독립적으로 테스트 가능)

| 컴포넌트 | 하는 일 | 의존성 |
|---|---|---|
| `app/web/` | HTTP 라우팅, 템플릿 렌더링, 제출 접수 | DB, problems.loader |
| `app/judge/runner.py` | Docker 컨테이너 실행, stdin 주입, stdout·시간·메모리·종료코드 수집, 리밋 강제 | Docker |
| `app/judge/grader.py` | 실행 결과와 정답 비교 → 판정. **순수 로직(Docker·DB 없음)** | 없음 |
| `app/judge/languages.py` | 언어별 이미지·컴파일·실행 명령 어댑터 (지금은 Python) | 없음 |
| `app/judge/worker.py` | PENDING 폴링 → runner+grader 호출 → 결과 기록 (루프) | DB, runner, grader |
| `app/problems/loader.py` | 파일로 정의된 문제·테스트케이스를 읽어 DB에 시딩/동기화 | 파일시스템, DB |
| `app/db/` | SQLAlchemy 모델, 세션 | 없음 |

설계 원칙: `grader.py`는 입출력만으로 판정하는 순수 함수라 Docker 없이 단위 테스트 가능. Docker 격리(`runner.py`)와 판정 로직(`grader.py`)을 분리해 각각 독립적으로 이해·테스트한다.

## 5. 데이터 모델

```
Problem
  id, slug (고유), title, statement (markdown),
  difficulty ("왕초보" | "초보"),
  time_limit_ms, memory_limit_mb
  # 문제 정의는 파일(problems/<slug>/)로 관리, loader가 DB에 동기화

TestCase
  id, problem_id (FK), input (text), expected_output (text),
  is_sample (bool)   # 샘플은 문제 화면에 노출, 채점엔 전체 사용
  ordinal            # 케이스 순번

Submission
  id, problem_id (FK), language, source_code,
  status: PENDING | JUDGING | AC | WA | TLE | MLE | RE | CE | IE,
  time_ms, memory_kb,
  failed_case_no,    # WA일 때 몇 번째 케이스에서 틀렸는지 (nullable)
  message,           # 에러 메시지/컴파일 에러 출력 (nullable)
  created_at
```

### 문제 파일 포맷 (관리자 UI 대체)

```
problems/
└─ <slug>/
   ├─ problem.md      # 프론트매터(title, difficulty, time_limit_ms, memory_limit_mb) + 지문(markdown)
   └─ tests/
      ├─ 1.in   1.out   # 1번은 샘플로 간주(설정 가능)
      ├─ 2.in   2.out
      └─ ...
```

`loader.py`가 이 폴더를 읽어 Problem/TestCase를 DB에 upsert(slug 기준). 이후 관리자 UI를 붙일 때도 동일 포맷을 재사용.

## 6. 채점 흐름 (데이터 플로우)

1. 사용자가 문제 상세에서 코드 제출.
2. Web: `Submission(status=PENDING)` DB 저장 → 제출 상세 페이지로 리다이렉트.
3. 제출 상세 페이지는 HTMX로 약 2초마다 상태 조각(fragment)을 폴링.
4. Worker: `PENDING` 하나를 집어 `status=JUDGING`으로 변경 (원자적 클레임).
5. Worker: 테스트케이스마다
   1. `runner`가 Docker 컨테이너 실행 (코드 마운트/주입, stdin=input).
      - time limit / memory limit을 `docker run` 옵션으로 강제.
      - `--network none`, 읽기전용 파일시스템, 비특권 사용자.
   2. `grader`가 stdout ↔ expected 비교 (뒤쪽 공백/개행 정규화).
   3. 실패 시 즉시 해당 판정으로 종료 (WA/TLE/MLE/RE), `failed_case_no` 기록.
6. 모든 케이스 통과 → AC. 시간·메모리는 케이스 전체의 최댓값 기록.
7. Worker가 DB에 최종 status·time·memory·message 기록 → HTMX 폴링이 결과 표시하고 폴링 중단.

## 7. 판정과 에러 처리

- **AC** 정답 / **WA** 오답(틀린 케이스 번호) / **TLE** 시간초과 / **MLE** 메모리초과 / **RE** 런타임에러(비정상 종료코드) / **CE** 컴파일에러(Python은 사전 문법 체크, 언어 확장 대비) / **IE** 내부에러(Docker 자체 실패).
- 워커는 어떤 제출에서 예외가 나도 죽지 않는다: 해당 제출만 IE 처리 + 로그 남기고 다음 제출로 진행. 한 제출이 전체 채점을 멈추지 않게 한다.
- 환경 문제(Docker 미실행, 이미지 없음)는 워커 시작 시 pre-flight 점검으로 친절한 에러 메시지.

## 8. 시딩할 문제 세트 (왕초보 ~ 초보, ~30줄)

순수 stdin → stdout 문제만. 초기 세트 예시:

- **왕초보**: Hello World / 두 수의 합(A+B) / 세 수의 평균 / 짝홀 판별
- **초보**: 1부터 N까지 합 / N개 수 중 최댓값 / 문자열 뒤집기 / 구구단 / 약수의 개수 / FizzBuzz

입력이 작으므로 time_limit은 문제별 1~2초, memory 128MB를 기본값으로 잡는다.

## 9. 테스트 전략

- `grader.py`(순수 로직): 판정 규칙 단위 테스트 — Docker 없이.
- `languages.py` 어댑터: 계약 테스트.
- `loader.py`: 파일 → DB 시딩 테스트.
- runner/worker: 실제 Docker로 도는 통합 테스트 1~2개 (예: Hello World가 AC 나오는지, 무한루프가 TLE 나오는지).
- 개발 방식: TDD (테스트 먼저 → 구현).

## 10. 프로젝트 구조

```
KTOJ/
├─ app/
│  ├─ web/          # FastAPI 라우트, Jinja 템플릿, HTMX 조각
│  ├─ judge/        # runner, grader, languages, worker
│  ├─ problems/     # loader
│  └─ db/           # models, session
├─ problems/        # 문제 정의 폴더 (지문 + 테스트케이스)
├─ docker/          # 채점용 언어 이미지 Dockerfile (python)
├─ tests/
└─ docs/superpowers/specs/
```

## 11. 향후 확장 (MVP 이후, 참고용)

- 인증(회원가입/로그인) → Submission을 user별로 귀속
- 문제 등록 관리자 UI (동일 파일 포맷 재사용)
- 다중 언어 (C++, Java) — languages 어댑터 추가 + Docker 이미지 추가
- 랭킹/통계, 대회(콘테스트)
- DB 큐 → Celery/Redis 교체, 워커 수평 확장
