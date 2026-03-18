# UI Demo Page Spec

## 목적
- 발표와 시연을 위한 단일 HTML 페이지의 원본 스펙이다.
- 기존 API를 빠르게 호출하고 결과를 즉시 보여주는 데 집중한다.

## 현재 범위
- KV 조작
- demo cache 조회
- cache compare 성능 비교
- 좌석 예약 동시성 시연
- 마지막 응답 JSON 확인

## 섹션 구성
- `1. 기본 KV 기능`
- `2. 더미 데이터 캐시 확인`
- `3. 성능 비교`
- `4. 좌석 예약 동시성 확인`
- `5. 마지막 응답`

## Controls And Endpoint Mapping
| UI Control | Method | Endpoint | Input | Purpose |
|---|---|---|---|---|
| `SET` | `POST` | `/kv` | `key`, `value`, optional `ttlSeconds` | 값 저장 |
| `GET` | `GET` | `/kv/{key}` | `key` | 값 조회 |
| `DELETE` | `DELETE` | `/kv/{key}` | `key` | 값 삭제 |
| `EXPIRE` | `POST` | `/kv/{key}/expire` | `key`, `ttlSeconds` | TTL 설정 |
| `TTL` | `GET` | `/kv/{key}/ttl` | `key` | TTL 조회 |
| `LOAD DEMO CACHE` | `GET` | `/demo/data-cache` | `key` | origin/cache 흐름 시연 |
| `RUN PERFORMANCE TEST` | `POST` | `/demo/performance/cache-compare` | `key`, `iterations` | cold vs warm 비교 |
| `RUN SEAT RESERVATION DEMO` | `POST` | `/demo/concurrency/seat-reservation` | `seatLimit`, `requestCount` | 50석/100요청 순차 처리 시연 |

## Seat Reservation Area
- 입력 필드
  - `seatLimit`
  - `requestCount`
- 기본값
  - `seatLimit = 50`
  - `requestCount = 100`
- 결과 요약
  - `reservedCount`
  - `soldOutCount`
  - `serialExecutor`
- preview table
  - `requestId`
  - `queueOrder`
  - `result`
  - `seatNumber`
  - `statusCode`
  - `durationMs`

## Response Display Rules
- 모든 버튼 결과는 하단 마지막 응답 영역에도 raw JSON으로 보여준다.
- 좌석 예약 동시성 영역은 요약 카드 + timeline preview table 조합으로 보여준다.
- preview table은 상위 일부 행만 렌더링하고 전체 결과는 raw JSON에서 확인하게 한다.
