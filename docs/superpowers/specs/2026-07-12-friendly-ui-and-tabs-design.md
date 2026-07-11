# KTOJ — 친근한 밝은 UI + 3탭 + 제출 이력 (설계)

- 작성일: 2026-07-12
- 목표: UI를 "친근하고 밝은 초보 친화" 테마로 전면 교체, 상단 3탭(문제 / 풀이 / 내 제출 이력) 도입, 새 "내 제출 이력" 페이지 추가. 채점 로직·DB 스키마 변경 없음. 승인된 목업 기준.

## 디자인 시스템 (라이트 기본 + 다크 대응)

`base.html` 인라인 CSS를 토큰 기반으로 교체.
- 색: `--bg #eef4f1`(민트빛 밝은 배경), `--surface #fff`, `--ink #17302b`, `--muted #5c716b`, `--primary #0f9d8f`(틸-에메랄드), `--primary-soft #d6f3ee`. 판정: `--ok #16a34a`, `--bad #dc4a44`, `--warn #d98a09`. 난이도: 왕초보=연두(`#dcfce7`/`#15803d`, 🌱), 초보=하늘(`#d3eefb`/`#0e6f96`, 🚀). 다크 테마 토큰도 정의(`prefers-color-scheme` + `data-theme`).
- 타이포: 한글 시스템 스택(Pretendard/Apple SD Gothic/Malgun) + 코드 모노. 위계 있는 크기.
- 형태: 라운드 카드(16px), 부드러운 그림자, 넉넉한 여백, hover 살짝 뜸.

## 네비게이션 (3탭)

`base.html`에 앱바 + 3탭. 활성 탭은 라우트가 넘기는 `active_tab` 값으로 표시.
- `문제` → `GET /` (active_tab="problems")
- `풀이` → `GET /solve` (active_tab="solve")
- `내 제출 이력` → `GET /submissions` (active_tab="history")

## 새 라우트

1. **`GET /submissions`** — 모든 제출을 최신순 목록. 각 행: `#id · 문제명 · 판정 배지 · 실행시간 · 시각`, 클릭 시 `/submissions/{id}`. 세션 내에서 (제출, 문제명) 추출해 컨텍스트로 넘겨 detached 접근 방지. 템플릿 `submissions.html`.
2. **`GET /solve`** — 쿠키 `last_problem`(slug)이 있고 해당 문제가 존재하면 `/problems/{slug}`로 303 리다이렉트. 없으면 빈 상태 페이지 `solve_empty.html`("아직 푼 문제가 없어요. 문제 목록에서 골라보세요").

## 기존 라우트 조정

- `GET /problems/{slug}`: 응답에 쿠키 `last_problem=slug`(30일) 설정. `active_tab="solve"`.
- `GET /`(문제 목록): AC 받은 문제 id 집합을 조회해 `solved`로 전달 → 목록에 "✓ 해결" 표시. `active_tab="problems"`.
- `GET /submissions/{id}`(결과 상세): `active_tab="history"`.
- 모든 라우트 컨텍스트에 `active_tab` 포함(없으면 활성 탭 없음).

## 템플릿

- `base.html`: 테마 CSS + 3탭 앱바.
- `problem_list.html`: 카드형 행 리스트, 난이도 이모지 배지, 해결 표시.
- `problem_detail.html`: 지문 카드, 배지줄, 예제 입출력, 에디터풍 textarea(상단 바 + 다크 모노) + 스타터 프리필 + 힌트 + 큰 제출 버튼.
- `submission_detail.html` + `_submission_status.html`: 큰 판정 카드(AC 초록 ✓ / 그 외 빨강 ✕ / 대기 ⏳), 실행시간·틀린 케이스·메시지 메트릭. **폴링 fragment는 `#status` id·hx 속성·`verdict-{{status}}` 클래스 유지**(동작/기존 테스트 문자열 보존).
- `submissions.html`(신규): 제출 이력 카드 리스트.
- `solve_empty.html`(신규): 풀이 빈 상태.

## 테스트/검증

- 기존 웹 테스트 그대로 통과(문자열/303/400 보존).
- 신규 테스트: `/submissions` 목록에 제출·문제명·판정 노출; `/solve` 쿠키 있으면 303·없으면 200 빈 상태; 문제 상세가 `last_problem` 쿠키를 설정.
- 라이브: 서버 띄워 세 탭 이동, 제출→채점 카드, 이력 목록, 풀이 리다이렉트 확인. 라이트/다크 렌더 확인. 전체 스위트 그린.
```
