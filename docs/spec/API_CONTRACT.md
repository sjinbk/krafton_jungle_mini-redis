# API Contract

이 문서는 공개 API 계약의 단일 원본이다. 엔드포인트, 요청/응답 형식, 상태 코드, validation 규칙은 이 문서를 기준으로 한다.

## 공개 엔드포인트
- `POST /kv`
  - key/value 저장
- `GET /kv/{key}`
  - key 조회
- `DELETE /kv/{key}`
  - key 삭제
- `POST /kv/{key}/expire`
  - TTL 설정
- `GET /kv/{key}/ttl`
  - TTL 조회
- `GET /demo/external-cache`
  - 외부 API 캐싱 데모

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
- `KEY_NOT_FOUND`
- `INTERNAL_ERROR`

## 외부 API 캐싱 시나리오
- 외부 API를 하나 호출한다.
- 응답을 Mini Redis에 저장한다.
- 같은 요청이 들어오면 TTL이 살아 있는 동안 캐시를 우선 반환한다.
- TTL 만료 후에는 다시 외부 API를 호출해 갱신한다.
- 이 흐름은 `GET /demo/external-cache` 또는 이에 대응되는 단일 엔드포인트로 노출한다.
