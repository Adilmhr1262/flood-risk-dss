import 'package:dio/dio.dart';
import 'package:flood_risk_dss/core/api_client.dart';
import 'package:flood_risk_dss/core/app_error.dart';
import 'package:flood_risk_dss/core/token_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

class _MockTokenStorage extends Mock implements TokenStorage {}

/// API client tests with a stubbed Dio adapter (no network).
void main() {
  late Dio dio;
  late _MockTokenStorage tokens;

  setUp(() {
    dio = Dio();
    tokens = _MockTokenStorage();
    when(() => tokens.readAccessToken()).thenAnswer((_) async => 'abc');
    when(() => tokens.readRefreshToken()).thenAnswer((_) async => 'refresh-abc');
  });

  test('GET attaches bearer token and returns data', () async {
    dio.httpClientAdapter = _StubAdapter(
      handler: (options) async {
        expect(options.headers['Authorization'], 'Bearer abc');
        return ResponseBody.fromString('{"ok":true}', 200,
            headers: {'content-type': ['application/json']});
      },
    );
    final client = ApiClient(dio: dio, tokenStorage: tokens);
    final data = await client.get('/mobile/alerts');
    expect(data, {'ok': true});
  });

  test('401 triggers refresh and retries once', () async {
    var calls = 0;
    // Simulate real token storage: reads reflect the latest rotation.
    var currentAccess = 'abc';
    when(() => tokens.readAccessToken()).thenAnswer((_) async => currentAccess);
    when(() => tokens.updateAccessToken('new', 'new-r'))
        .thenAnswer((_) async => currentAccess = 'new');
    dio.httpClientAdapter = _StubAdapter(
      handler: (options) async {
        calls++;
        if (options.path.endsWith('/auth/refresh')) {
          return ResponseBody.fromString(
              '{"access_token":"new","refresh_token":"new-r"}', 200,
              headers: {'content-type': ['application/json']});
        }
        if (calls == 1) {
          return ResponseBody.fromString('{"detail":"expired"}', 401,
              headers: {'content-type': ['application/json']});
        }
        expect(options.headers['Authorization'], 'Bearer new');
        return ResponseBody.fromString('{"ok":true}', 200,
            headers: {'content-type': ['application/json']});
      },
    );
    final client = ApiClient(dio: dio, tokenStorage: tokens);
    final data = await client.get('/mobile/alerts');
    expect(data, {'ok': true});
    expect(calls, 3); // initial + refresh + retry
  });

  test('404 maps to NotFoundException', () async {
    dio.httpClientAdapter = _StubAdapter(
      handler: (_) async => ResponseBody.fromString('{"detail":"missing"}', 404,
          headers: {'content-type': ['application/json']}),
    );
    final client = ApiClient(dio: dio, tokenStorage: tokens);
    expect(() => client.get('/mobile/my-risk'),
        throwsA(isA<NotFoundException>()));
  });

  test('validation error detail is surfaced', () async {
    dio.httpClientAdapter = _StubAdapter(
      handler: (_) async => ResponseBody.fromString(
          '{"detail":[{"msg":"field required","loc":["body","lat"],"type":"missing"}]}',
          422,
          headers: {'content-type': ['application/json']}),
    );
    final client = ApiClient(dio: dio, tokenStorage: tokens);
    try {
      await client.post('/mobile/report-event', data: {});
      fail('expected ValidationException');
    } on ValidationException catch (e) {
      expect(e.message, contains('field required'));
    }
  });
}

typedef _Handler = Future<ResponseBody> Function(RequestOptions options);

class _StubAdapter implements HttpClientAdapter {
  _StubAdapter({required this.handler});
  final _Handler handler;

  @override
  Future<ResponseBody> fetch(RequestOptions options,
      Stream<List<int>>? requestStream, Future<void>? cancelFuture) {
    return handler(options);
  }

  @override
  void close({bool force = false}) {}
}
