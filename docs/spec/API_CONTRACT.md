# API Contract

이 문서는 공개 API 계약의 단일 원본이다. 엔드포인트, 요청/응답 형식, 상태 코드, validation 규칙은 이 문서를 기준으로 한다.

## 공개 엔드포인트
| Method | Path | Purpose | Required params | Success / Error |
|------|------|------|------|------|
| `POST` | `/kv` | key/value 저장 | `key`, `value`, optional `ttlSeconds` | `200/201`, `400` |
| `GET` | `/kv/{key}` | key 조회 | path `key` | `200`, `404` |
| `DELETE` | `/kv/{key}` | key 삭제 | path `key` | `200`, `404` |
| `POST` | `/kv/{key}/expire` | TTL 설정 | path `key`, body `ttlSeconds` | `200`, `400`, `404` |
| `GET` | `/kv/{key}/ttl` | TTL 조회 | path `key` | `200`, `404` |
| `GET` | `/demo/data-cache` | DB 기반 더미 데이터 캐싱 시나리오 | query `key` | `200`, `400`, `500` |
| `POST` | `/demo/performance/cache-compare` | cold origin vs warm cache 성능 비교 | optional body `key`, `iterations` | `200`, `400`, `404`, `500` |
| `POST` | `/demo/performance/concurrency-burst` | 동시 GET burst 성능 비교 | body `scenario`, optional `count`, `key` | `200`, `400`, `404`, `500` |

## 구현 우선순위
- 필수 구현
  - `POST /kv`
  - `GET /kv/{key}`
  - `DELETE /kv/{key}`
  - `POST /kv/{key}/expire`
  - `GET /kv/{key}/ttl`
- 함께 검증할 데모 API
  - `GET /demo/data-cache`
  - `POST /demo/performance/cache-compare`
  - `POST /demo/performance/concurrency-burst`

## 명령 의미
### `SET`
- 입력:
  - `key`: 비어 있지 않은 문자열
  - `value`: 직렬화 가능한 값
  - `ttlSeconds`: 선택적 양의 정수
- 결과:
  - 새 키를 저장하거나 기존 키를 덮어쓴다.
  - TTL이 주어지면 만료 시각을 갱신한다.
  - TTL 없이 덮어쓰면 기존 만료는 제거한다.

### `GET`
- 입력:
  - `key`: 비어 있지 않은 문자열
- 결과:
  - 값이 있고 만료되지 않았으면 반환한다.
  - 만료되었으면 삭제 후 miss를 반환한다.

### `DELETE`
- 입력:
  - `key`: 비어 있지 않은 문자열
- 결과:
  - 실제 삭제 여부를 반환한다.
  - 없는 키 또는 만료된 키는 miss로 처리한다.
  - v1에서 가장 직접적인 사용자 무효화 수단으로 사용한다.

### `EXPIRE`
- 입력:
  - `key`: 비어 있지 않은 문자열
  - `ttlSeconds`: 양의 정수
- 결과:
  - 존재하는 키에 만료 시간을 설정하거나 갱신한다.

### `TTL`
- 입력:
  - `key`: 비어 있지 않은 문자열
- 결과:
  - 없는 키 / 만료 없음 / 남은 TTL 상태를 구분할 수 있어야 한다.

## 무효화 전략
- v1에서 사용자가 데이터를 무효화하는 방법은 아래 네 가지로 한정한다.
  - `DELETE /kv/{key}`로 즉시 제거
  - `POST /kv/{key}/expire`로 만료 시각 설정 또는 단축
  - TTL 만료에 따른 lazy expiration
  - `POST /kv` 재호출로 같은 key 값을 덮어쓰기
- 별도 `deprecated` 상태, soft delete, background invalidation worker는 도입하지 않는다.

## 입력 규칙
- 빈 문자열 키 금지
- TTL 단위는 모두 초
- 음수 TTL 금지
- `0`초 TTL은 허용하지 않고 `INVALID_TTL`로 처리한다

## 응답 규칙
- 외부 응답은 성공/실패가 분명해야 한다.
- miss 응답과 validation 오류 응답을 구분해야 한다.
- HTTP status는 성공/검증 오류/miss를 구분해야 한다.

권장 HTTP status:
- 정상 조회 / 수정 / 삭제 성공: `200`
- 최초 생성 성격이 분명한 저장: `201` 허용
- 잘못된 입력: `400`
- 존재하지 않거나 만료된 키: `404`
- 내부 오류: `500`

권장 응답 형태:

```json
{
  "success": true,
  "data": {
    "key": "sample",
    "value": "cached-value"
  },
  "error": null
}
```

권장 에러 형태:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "KEY_NOT_FOUND",
    "message": "Requested key does not exist"
  }
}
```

## 에러 코드
- `INVALID_KEY`
- `INVALID_TTL`
- `INVALID_ITERATIONS`
- `INVALID_BURST_COUNT`
- `INVALID_SCENARIO`
- `KEY_NOT_FOUND`
- `BENCHMARK_DATA_NOT_FOUND`
- `INTERNAL_ERROR`

## DB 더미 데이터 캐싱 시나리오
- 엔드포인트:
  - `GET /demo/data-cache?key={key}`
- 입력:
  - `key`: 비어 있지 않은 조회 문자열
- origin 데이터:
  - MongoDB `dummy_items` collection에 사전 적재한 dummy document를 조회한다.
  - 외부 API 연동은 사용하지 않는다.
- 결과:
  - 첫 요청은 MongoDB origin을 조회해 결과를 저장하고 `source = origin`으로 반환한다.
  - 같은 `key` 요청은 TTL이 살아 있는 동안 캐시를 우선 반환하고 `source = cache`로 표시한다.
  - TTL 만료 후에는 MongoDB를 다시 조회해 결과를 갱신한다.
  - 결과가 비어 있으면 `200`과 빈 `items`를 반환하고 캐시에 저장하지 않는다.
  - 이 시나리오는 외부 API 캐싱 요구를 재현 가능한 DB-seeded origin 흐름으로 단순화한 v1 데모 계약이다.

MongoDB 문서 스키마:
- `_id`: `ObjectId`
- `key`: `string`
- `itemId`: `string`
- `value`: `string`
- `createdAt`: `datetime`

요약 표:

| Case | Input | Expected result |
|------|------|------|
| First request | `key=sample` | `source = origin`, MongoDB read, cache write |
| Repeated request | same `key` within TTL | `source = cache` |
| After TTL expiry | same `key` after expiry | `source = origin`, MongoDB reread, refreshed payload |
| Missing key | no `key` query or empty string | `400`, validation error |
| Empty origin result | `key=not-seeded`, no items | `200`, empty `items` |

응답 필드 의미:
- `key`
  - 요청에 사용한 조회 문자열
- `source`
  - `origin` 또는 `cache`
- `originType`
  - 고정값 `mongodb`
- `cacheKey`
  - 내부 캐시 키
- `ttlSecondsRemaining`
  - 캐시 hit일 때 남은 TTL 초
  - origin 응답일 때는 `null` 허용
- `originFetchedAt`
  - MongoDB origin을 마지막으로 읽은 시각
- `items`
  - 캐시된 더미 데이터 배열

권장 응답 형태:

```json
{
  "success": true,
  "data": {
    "key": "sample",
    "source": "cache",
    "originType": "mongodb",
    "cacheKey": "data:sample",
    "ttlSecondsRemaining": 11,
    "originFetchedAt": "2026-03-17T10:00:00.000Z",
    "items": [
      {
        "id": "sample-1",
        "value": "example payload"
      }
    ]
  },
  "error": null
}
```

## 성능 비교 API
### `POST /demo/performance/cache-compare`
- 목적:
  - 동일한 입력에 대해 MongoDB origin 경로와 warm cache 경로의 응답시간을 비교한다.
- 요청:
  - body optional
  - `key`: 기본값 `sample`
  - `iterations`: 기본값 `20`, 범위 `1..100`
- 측정 기준:
  - `apiTiming`: benchmark app의 `/demo/data-cache` HTTP 왕복 시간
  - `serviceTiming`: `DemoCacheService.get_data()` 직접 호출 시간
- 결과:
  - cold 측정은 매 반복 전 cache key를 비운다.
  - warm 측정은 1회 prime 후 측정한다.
  - origin 결과가 비면 `404 BENCHMARK_DATA_NOT_FOUND`

권장 응답 형태:

```json
{
  "success": true,
  "data": {
    "scenario": "cacheCompare",
    "key": "sample",
    "iterations": 20,
    "originType": "mongodb",
    "measuredAt": "2026-03-18T10:00:00.000Z",
    "apiTiming": {
      "coldAvgMs": 3.738,
      "warmAvgMs": 2.396,
      "savedMs": 1.342,
      "speedupRatio": 1.56
    },
    "serviceTiming": {
      "coldAvgMs": 3.101,
      "warmAvgMs": 1.982,
      "savedMs": 1.119,
      "speedupRatio": 1.564
    }
  },
  "error": null
}
```

### `POST /demo/performance/concurrency-burst`
- 목적:
  - n개의 GET을 동시에 보냈을 때 전역 직렬화와 대기 시간을 수치와 타임라인으로 보여준다.
- 요청:
  - `scenario`: 아래 enum 중 하나
    - `sameKeyKvGetBurst`
    - `differentKeyKvGetBurst`
    - `demoCacheGetBurst`
  - `count`: 기본값 `10`, 범위 `1..50`
  - `key`: 기본값 `sample`
- 측정 기준:
  - `apiTiming`: benchmark app HTTP GET burst
  - `serviceTiming`: 서비스 메서드 직접 호출 burst
- 시나리오:
  - `sameKeyKvGetBurst`
    - 같은 key에 대한 `GET /kv/{key}`를 동시에 보낸다.
  - `differentKeyKvGetBurst`
    - 서로 다른 key에 대한 `GET /kv/{key}`를 동시에 보낸다.
  - `demoCacheGetBurst`
    - 1회 prime 후 `GET /demo/data-cache?key={key}`를 동시에 보내고 `source=cache`를 기대한다.

권장 응답 형태:

```json
{
  "success": true,
  "data": {
    "scenario": "sameKeyKvGetBurst",
    "count": 10,
    "measuredAt": "2026-03-18T10:00:00.000Z",
    "apiTiming": {
      "totalElapsedMs": 14.201,
      "avgMs": 5.211,
      "p95Ms": 7.901,
      "maxMs": 7.901,
      "throughputRps": 704.176,
      "successCount": 10,
      "errorCount": 0,
      "timeline": [
        {
          "requestId": "request-1",
          "key": "sample",
          "startedOffsetMs": 0.014,
          "endedOffsetMs": 4.812,
          "durationMs": 4.798,
          "status": "success",
          "statusCode": 200,
          "source": null
        }
      ]
    },
    "serviceTiming": {
      "totalElapsedMs": 9.114,
      "avgMs": 3.221,
      "p95Ms": 4.81,
      "maxMs": 4.81,
      "throughputRps": 1097.957,
      "successCount": 10,
      "errorCount": 0,
      "timeline": []
    }
  },
  "error": null
}
```
