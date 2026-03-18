# UI Demo Page Spec

이 문서는 발표와 시연을 위한 단일 HTML 페이지의 원본 스펙이다.  
기존 API를 빠르게 호출하고 결과를 즉시 보여주는 데 집중한다.

## 현재 범위
- KV 조작
- demo cache 조회
- cache compare 성능 비교
- 좌석 예약 동시성 시연
- 마지막 API 응답 JSON 확인

## 섹션 구성
- `1. 기본 KV 기능`
- `API 응답`
- `2. 더미 데이터 캐시 확인`
- `3. 성능 비교`
- `4. 좌석 예약 동시성 확인`

## Controls And Endpoint Mapping
| UI Control | Method | Endpoint | Input | Purpose |
|---|---|---|---|---|
| `값 저장 (SET)` | `POST` | `/kv` | `key`, `value`, optional `ttlSeconds` | 값 저장 |
| `값 조회 (GET)` | `GET` | `/kv/{key}` | `key` | 값 조회 |
| `값 삭제 (DELETE)` | `DELETE` | `/kv/{key}` | `key` | 값 삭제 |
| `만료 설정 (EXPIRE)` | `POST` | `/kv/{key}/expire` | `key`, `ttlSeconds` | TTL 설정 |
| `TTL 확인` | `GET` | `/kv/{key}/ttl` | `key` | TTL 조회 |
| `더미 데이터 조회` | `GET` | `/demo/data-cache` | `key` | origin/cache 흐름 시연 |
| `성능 비교 실행` | `POST` | `/demo/performance/cache-compare` | `key`, `iterations` | cold vs warm 비교 |
| `좌석 예약 동시성 실행` | `POST` | `/demo/concurrency/seat-reservation` | `seatLimit`, `requestCount` | 50석/100요청 순차 처리 시연 |

## API 응답 영역
- 마지막 호출 엔드포인트를 표시한다
- HTTP 상태 코드를 표시한다
- 성공 여부를 표시한다
- raw JSON 전체를 그대로 보여준다

## Demo Cache Area
- 입력 필드
  - `key`
- 요약 카드
  - `source`
  - `ttlSecondsRemaining`
  - `items.length`
  - `originFetchedAt`

## Performance Area
- 입력 필드
  - `key`
  - `iterations`
- 결과 카드
  - `apiTiming`
  - `serviceTiming`
- 공통 메트릭
  - `coldAvgMs`
  - `warmAvgMs`
  - `savedMs`
  - `speedupRatio`

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
  - `totalElapsedMs`
- timeline preview table
  - `requestId`
  - `queueOrder`
  - `result`
  - `seatNumber`
  - `statusCode`
  - `durationMs`

## Response Display Rules
- 모든 버튼 결과는 하단 공통 응답 영역에도 raw JSON으로 보여준다.
- 좌석 예약 동시성 영역은 요약 카드 + timeline preview table 조합으로 보여준다.
- preview table은 상위 일부 행만 렌더링하고 전체 결과는 raw JSON에서 확인하게 한다.
- 제거된 구형 동시성 시나리오 문구는 남기지 않는다.
