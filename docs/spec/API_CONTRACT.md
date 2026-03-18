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
| `GET` | `/demo/external-cache` | 뉴스 헤드라인 캐싱 데모 | query `topic` | `200`, `400`, `500` |

## 구현 우선순위
- 필수 구현
  - `POST /kv`
  - `GET /kv/{key}`
  - `DELETE /kv/{key}`
  - `POST /kv/{key}/expire`
  - `GET /demo/external-cache`
- 여유가 있으면 추가
  - `GET /kv/{key}/ttl`

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
- `INVALID_TOPIC`
- `KEY_NOT_FOUND`
- `INTERNAL_ERROR`

## 뉴스 헤드라인 캐싱 시나리오
- 엔드포인트:
  - `GET /demo/external-cache?topic={ai|gaming|economy}`
- 입력:
  - `topic`: `ai`, `gaming`, `economy` 중 하나
- 검증:
  - 허용되지 않은 `topic`은 `400`과 `INVALID_TOPIC`으로 처리한다.
- 결과:
  - 첫 요청은 The News API 업스트림을 호출해 결과를 저장하고 `source = origin`으로 반환한다.
  - 같은 토픽 요청은 TTL이 살아 있는 동안 캐시를 우선 반환하고 `source = cache`로 표시한다.
  - TTL 만료 후에는 다시 업스트림을 호출해 결과를 갱신한다.
  - 유효한 토픽인데 결과가 비어 있으면 `200`과 빈 `articles`를 반환하고 캐시에 저장하지 않는다.

요약 표:

| Case | Input | Expected result |
|------|------|------|
| First request | `topic=ai` | `source = origin`, cache write |
| Repeated request | same `topic` within TTL | `source = cache` |
| After TTL expiry | same `topic` after expiry | `source = origin`, refreshed payload |
| Invalid topic | unsupported `topic` | `400`, `INVALID_TOPIC` |
| Empty upstream result | valid `topic`, no articles | `200`, empty `articles` |

응답 필드 의미:
- `topic`
  - 요청에 사용한 토픽 식별자
- `locale`
  - 고정값 `kr`
- `source`
  - `origin` 또는 `cache`
- `cacheKey`
  - 내부 캐시 키. 예: `news:ai:kr`
- `ttlSecondsRemaining`
  - 캐시 hit일 때 남은 TTL 초
- `upstreamFetchedAt`
  - 업스트림을 마지막으로 가져온 시각
- `articles`
  - 최대 3개 기사 배열
- `articles[].title`
  - 기사 제목
- `articles[].source`
  - 기사 출처명
- `articles[].publishedAt`
  - 기사 발행 시각
- `articles[].url`
  - 기사 원문 링크

권장 응답 형태:

```json
{
  "success": true,
  "data": {
    "topic": "ai",
    "locale": "kr",
    "source": "cache",
    "cacheKey": "news:ai:kr",
    "ttlSecondsRemaining": 11,
    "upstreamFetchedAt": "2026-03-17T10:00:00.000Z",
    "articles": [
      {
        "title": "Example headline",
        "source": "Example News",
        "publishedAt": "2026-03-17T09:58:00.000Z",
        "url": "https://example.com/article"
      }
    ]
  },
  "error": null
}
```
