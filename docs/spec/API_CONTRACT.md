# API Contract

이 문서는 공개 API 계약의 원본이다.
요청/응답 형식, 상태 코드, validation 규칙은 이 문서를 기준으로 한다.

## Public Endpoints
| Method | Path | Purpose | Required params | Success / Error |
|---|---|---|---|---|
| `POST` | `/kv` | key/value 저장 | `key`, `value`, optional `ttlSeconds` | `200/201`, `400` |
| `GET` | `/kv/{key}` | key 조회 | path `key` | `200`, `404` |
| `DELETE` | `/kv/{key}` | key 삭제 | path `key` | `200`, `404` |
| `POST` | `/kv/{key}/expire` | TTL 설정 | path `key`, body `ttlSeconds` | `200`, `400`, `404` |
| `GET` | `/kv/{key}/ttl` | TTL 조회 | path `key` | `200`, `404` |
| `GET` | `/demo/data-cache` | MongoDB origin 기반 cache-aside 데모 | query `key` | `200`, `400`, `500` |
| `POST` | `/demo/performance/cache-compare` | cold origin vs warm cache 성능 비교 | optional body `key`, `iterations` | `200`, `400`, `404`, `500` |
| `POST` | `/demo/concurrency/seat-reservation` | 좌석 예약 기반 동시성 시연 | optional body `seatLimit`, `requestCount` | `200`, `400`, `500` |

## Validation Rules
- `key`: 비어 있지 않은 문자열
- `ttlSeconds`: 양의 정수, `0` 금지
- `iterations`: `1..100`
- `seatLimit`: `1..100`
- `requestCount`: `1..200`

## Error Codes
- `INVALID_KEY`
- `INVALID_TTL`
- `INVALID_ITERATIONS`
- `INVALID_SEAT_LIMIT`
- `INVALID_REQUEST_COUNT`
- `KEY_NOT_FOUND`
- `BENCHMARK_DATA_NOT_FOUND`
- `INTERNAL_ERROR`

## Response Envelope

성공 응답:

```json
{
  "success": true,
  "data": {},
  "error": null
}
```

실패 응답:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INVALID_KEY",
    "message": "Key must be a non-empty string"
  }
}
```

## Demo Data Cache
### `GET /demo/data-cache`
- query:
  - `key`
- 결과:
  - 첫 요청: `source = origin`
  - 같은 key 재요청: `source = cache`
  - TTL 만료 후: 다시 `source = origin`
  - 빈 origin 결과: `200` + empty `items`, 캐시 미저장

응답 필드:
- `key`
- `source`
- `originType`
- `cacheKey`
- `ttlSecondsRemaining`
- `originFetchedAt`
- `items`

## Performance Compare
### `POST /demo/performance/cache-compare`
- body optional:
  - `key`: default `sample`
  - `iterations`: default `20`
- 목적:
  - 같은 입력에 대해 cold origin path와 warm cache path 평균 시간을 비교한다.
- 결과:
  - `scenario = "cacheCompare"`
  - `key`
  - `iterations`
  - `originType = "mongodb"`
  - `measuredAt`
  - `apiTiming`
  - `serviceTiming`

## Seat Reservation Concurrency Demo
### `POST /demo/concurrency/seat-reservation`
- body optional:
  - `seatLimit`: default `50`
  - `requestCount`: default `100`
- 목적:
  - 동시에 시작된 다수 요청이 서버 내부의 single-thread executor에 의해 순차 처리되는 모습을 시연한다.
- 처리 규칙:
  - 예약 수가 `seatLimit`보다 작으면 성공
  - `seatLimit` 도달 후 나머지 요청은 `soldOut` 실패
  - 모든 요청은 timeline에 기록된다

응답 필드:
- `scenario`
- `seatLimit`
- `requestCount`
- `reservedCount`
- `soldOutCount`
- `serialExecutor`
- `timeline`

`timeline` 항목:
- `requestId`
- `queueOrder`
- `startedOffsetMs`
- `endedOffsetMs`
- `durationMs`
- `result`
- `seatNumber`
- `statusCode`
