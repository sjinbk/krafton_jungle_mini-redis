# UI Demo Page Spec

## Why This Page Exists
- 이 문서는 나중에 만들 발표/시연용 UI의 단일 원본이다.
- 실제 구현 대상은 나중에 만드는 HTML 1파일이며, 이번 단계에서는 설계 문서만 저장한다.
- 목적은 예쁜 제품 화면이 아니라 기존 API를 빠르게 입력하고 결과를 바로 보여주는 데모 페이지를 정의하는 것이다.
- 추후 성능 테스트 버튼과 동시성 테스트 버튼을 추가할 수 있도록 현재 범위와 예약 범위를 분리해 둔다.

## Current Scope
- 페이지는 1페이지로 구성한다.
- 구현 파일은 추후 HTML 1파일만 사용한다.
- 추후 FastAPI 내부 경로에서 제공하는 것을 기본 방향으로 본다.
- 현재 다루는 기능은 아래 여섯 가지다.
  - `SET`
  - `GET`
  - `DELETE`
  - `EXPIRE`
  - `TTL`
  - `demo cache`

## Future Reserved Scope
- 아래 두 영역은 지금 구현하지 않고, 화면 자리와 요구사항만 예약한다.
  - 성능 테스트 영역
  - 동시성 테스트 영역
- 현재 문서는 미래 확장을 막지 않도록 버튼 이름, 출력 항목, 기대 목적만 정의한다.

## Page Layout
- 상단 제목 영역
  - 페이지 이름
  - 짧은 설명 한 줄
- KV 조작 영역
  - 입력값: `key`, `value`, `ttlSeconds`
  - 버튼: `SET`, `GET`, `DELETE`, `EXPIRE`, `TTL`
- Demo Cache 영역
  - 입력값: `demo key`
  - 버튼: `LOAD DEMO CACHE`
- Reserved 영역
  - 버튼 자리: `RUN PERFORMANCE TEST`
  - 버튼 자리: `RUN CONCURRENCY TEST`
- 결과 출력 영역
  - HTTP status 표시
  - 성공/실패 여부 표시
  - 응답 JSON 원문 표시

권장 배치 예시:

```text
[ Title ]
[ Short description ]

[ KV Controls ]
key | value | ttlSeconds
SET | GET | DELETE | EXPIRE | TTL

[ Demo Cache ]
demo key
LOAD DEMO CACHE

[ Reserved: Performance / Concurrency ]
RUN PERFORMANCE TEST
RUN CONCURRENCY TEST

[ Result ]
status
success / failure
raw JSON
```

## Controls And Endpoint Mapping
| UI control | Method | Endpoint | Input source | Expected use |
|---|---|---|---|---|
| `SET` | `POST` | `/kv` | `key`, `value`, optional `ttlSeconds` | 값 저장 또는 overwrite |
| `GET` | `GET` | `/kv/{key}` | `key` | 저장된 값 조회 |
| `DELETE` | `DELETE` | `/kv/{key}` | `key` | 키 삭제 |
| `EXPIRE` | `POST` | `/kv/{key}/expire` | `key`, `ttlSeconds` | TTL 설정 또는 갱신 |
| `TTL` | `GET` | `/kv/{key}/ttl` | `key` | TTL 상태 확인 |
| `LOAD DEMO CACHE` | `GET` | `/demo/data-cache?key={key}` | `demo key` | origin/cache 흐름 시연 |

## Input Rules
| Input field | Meaning | Notes |
|---|---|---|
| `key` | KV API 대상 키 | 빈 문자열 금지 |
| `value` | 저장할 값 | 우선 텍스트 또는 JSON 문자열 입력을 허용하는 방향이 단순하다 |
| `ttlSeconds` | TTL 초 단위 값 | `EXPIRE`와 optional `SET`에서 사용 |
| `demo key` | 캐시 데모 조회 키 | `/demo/data-cache` 전용 입력 |

## Response Display Rules
- 결과 영역은 마지막 요청의 결과만 보여준다.
- 아래 세 가지는 항상 함께 표시한다.
  - HTTP status
  - 성공/실패 여부
  - 응답 JSON 원문
- 성공 응답과 에러 응답은 같은 위치에 표시한다.
- 응답 JSON은 `pre` 형태의 고정폭 텍스트 영역에 표시하는 방향이 가장 단순하다.
- 캐시 데모 응답에서는 `source`, `items`, `ttlSecondsRemaining`가 눈에 잘 띄도록 보여주는 것이 좋다.

## Future Performance Test Area
- 이 영역은 지금 비워 두고 추후 버튼과 출력 칸을 추가한다.
- 예약 버튼 이름은 `RUN PERFORMANCE TEST`로 고정한다.
- 최소 출력 항목은 아래와 같다.
  - `cold_avg_ms`
  - `warm_avg_ms`
  - `speedup_ratio`
- 추후 확장 가능 항목은 아래와 같다.
  - `p95`
  - `cache_hit_ratio`
- 목적은 같은 요청 경로에서 cold origin 경로와 warm cache 경로를 비교해 데모에서 성능 차이를 바로 보여주는 것이다.

## Future Concurrency Test Area
- 이 영역도 지금은 비워 두고 추후 버튼과 출력 칸을 추가한다.
- 예약 버튼 이름은 `RUN CONCURRENCY TEST`로 고정한다.
- 최소 검증 관점은 아래와 같다.
  - same-key 요청 시 응답 일관성
  - different-key 요청 시 독립 처리
  - 응답 형식과 상태 코드 일관성
- 향후 출력은 요청 수, 성공 수, 실패 수, 요약 결과 정도만 먼저 보여줘도 충분하다.

## Non-Goals
- 다중 페이지 UI
- 프론트엔드 프레임워크 도입
- 복잡한 스타일링
- 운영용 대시보드
- 인증, 권한, 사용자 상태 관리
- 실시간 차트나 장기 모니터링 기능

## Acceptance Notes
- 문서만 보고 나중에 HTML 1파일을 구현할 수 있어야 한다.
- 현재 버튼 목록과 연결 API가 모두 명시되어 있어야 한다.
- 성능 테스트와 동시성 테스트는 현재 기능과 분리된 예약 영역으로 보이도록 적혀 있어야 한다.
- 기존 API 계약과 충돌하는 새 엔드포인트를 이 문서에서 요구하지 않는다.
